"""graph_router.py — Router LangGraph : classification de la question, orchestration des outils (geo/sql/rag), synthèse de la réponse finale."""

from dotenv import load_dotenv
load_dotenv()  # DOIT être appelé avant tout import LangGraph/LangSmith, pour
                # que LANGSMITH_ENDPOINT soit lu correctement dès le départ.

import json
import re
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from openai import OpenAI
from langsmith.wrappers import wrap_openai

from agent.tools.rag_tool import search_rag
from agent.tools.sql_tool import (
    recherche_sql, rechercher_etablissements_par_nom, filtrer_candidats_par_precision,
    rechercher_top_par_secteur, obtenir_evolution_etablissements, calculer_moyenne_etablissements,
)
from agent.tools.geo_tool import recherche_geo

from config import (
    LLM_MODEL, AGENT_MAX_TOURS, LLM_TIMEOUT_SECONDS, MAX_LIGNES_SYNTHESE, SPLIT_SECTEUR_N,
    MAX_ZONES_COMPAREES, Categorie, SecteurSouhaite, Secteur,
)
from prompts.router_system_prompt import ROUTER_SYSTEM_PROMPT
from prompts.agent_react_system_prompt import AGENT_REACT_SYSTEM_PROMPT

client = wrap_openai(OpenAI())  # rend chaque appel visible dans LangSmith (tokens, latence par appel)


class AgentState(TypedDict):
    question: str
    dc_niveau: str
    categorie: Optional[Categorie]
    zone_geo: Optional[str]
    secteur_souhaite: Optional[SecteurSouhaite]
    nuance_methodologique_demandee: bool
    evolution_demandee: bool
    resultats_geo: Optional[dict]
    resultats_sql: Optional[dict]
    resultats_rag: Optional[dict]
    reponse_finale: Optional[str]
    tours_agent: int
    noms_etablissements: Optional[list]
    resolution_noms: Optional[dict]
    uai_resolus: Optional[list]


ROUTER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "classifier_question",
        "description": (
            "Classifie la question utilisateur et extrait sa zone géographique, ses noms "
            "d'établissements, le secteur souhaité et le besoin de nuance méthodologique, "
            "en un seul passage."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {"type": "string", "enum": [c.value for c in Categorie]},
                "zone_detectee": {
                    "type": "boolean",
                    "description": "true si la question mentionne une zone géographique géocodable (ville, adresse, code postal, département). Un nom de région touristique informel (ex: Côte d'Opale) compte comme false.",
                },
                "zone": {
                    "type": "string",
                    "description": "La zone géographique extraite si zone_detectee=true, sinon chaîne vide.",
                },
                "noms_etablissements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Noms propres d'établissements explicitement cités dans la question (ex: 'Victor Hugo', 'Jean Moulin', 'Chevreul'), quelle que soit la catégorie choisie — même une question sur un seul établissement nommé (pas une comparaison entre plusieurs) doit remplir ce champ. Liste vide seulement si aucun nom propre d'établissement n'est cité.",
                },
                "secteur_souhaite": {
                    "type": "string",
                    "enum": [s.value for s in SecteurSouhaite],
                    "description": "Secteur souhaité si mentionné explicitement dans la question (\"collèges publics\", \"écoles privées\"...). \"indifferent\" si non précisé, ou si public ET privé sont explicitement demandés ensemble.",
                },
                "nuance_methodologique_demandee": {
                    "type": "boolean",
                    "description": "true si la question demande aussi, en plus d'une recherche géo ou d'une comparaison nommée, une nuance ou explication méthodologique (ex: \"est-ce fiable ?\", \"comment c'est calculé ?\"). false si la question ne porte que sur les données brutes.",
                },
                "evolution_demandee": {
                    "type": "boolean",
                    "description": "true si la question porte sur une évolution, une tendance ou une moyenne sur PLUSIEURS années/sessions (ex: \"sur les 3 dernières années\", \"évolution\", \"en moyenne depuis 2 ans\"). false si la question ne porte que sur la session la plus récente.",
                },
            },
            "required": [
                "categorie", "zone_detectee", "zone", "noms_etablissements",
                "secteur_souhaite", "nuance_methodologique_demandee", "evolution_demandee",
            ],
        },
    },
}


# Mots signalant une demande de classement concret ("le meilleur X") plutôt
# qu'une question de concept — volontairement restreint aux superlatifs sans
# ambiguïté ("classement" est exclu : peut aussi désigner le concept lui-même,
# ex: "est-ce que le classement des collèges est fiable ?", légitimement méthodologique).
_MOTS_SUPERLATIFS = re.compile(r"\b(meilleurs?|meilleures?|pires?)\b", re.IGNORECASE)

# Détection déterministe d'une demande de moyenne/agrégation sur une zone
# géographique — même principe que _MOTS_SUPERLATIFS, un mot-clé simple sur
# la question plutôt qu'un champ de plus extrait par le LLM du router.
_MOTS_AGREGATION = re.compile(r"\b(moyennes?)\b", re.IGNORECASE)

# Sous-ensemble de _MOTS_SUPERLATIFS spécifique à "pire" — utilisé pour
# adapter le sens du tri (ASC) et le texte d'intro en conséquence. Bug réel
# trouvé en test (S8.20) : "pires collèges" affichait bien les pires
# résultats via le Text-to-SQL général, mais l'intro disait quand même
# "meilleurs résultats" (texte figé) ; et le chemin split (rechercher_top_par_secteur)
# n'avait carrément pas d'option de tri ascendant, donc affichait les
# meilleurs même quand les pires étaient demandés.
_MOTS_PIRE = re.compile(r"\bpires?\b", re.IGNORECASE)


def noeud_router(state: AgentState) -> AgentState:
    response = client.chat.completions.create(
        model=LLM_MODEL, temperature=0,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": state["question"]},
        ],
        tools=[ROUTER_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "classifier_question"}},
        timeout=LLM_TIMEOUT_SECONDS,
    )
    args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    # Catégorie, zone géographique, noms d'établissements, secteur et nuance
    # méthodologique extraits en un seul appel LLM fusionné — évite des
    # appels séparés (gain de latence).
    state["categorie"] = Categorie(args["categorie"])
    state["zone_geo"] = args["zone"] if args.get("zone_detectee") else None
    state["noms_etablissements"] = args.get("noms_etablissements") or []
    state["secteur_souhaite"] = SecteurSouhaite(args.get("secteur_souhaite") or SecteurSouhaite.INDIFFERENT)
    state["nuance_methodologique_demandee"] = bool(args.get("nuance_methodologique_demandee"))
    state["evolution_demandee"] = bool(args.get("evolution_demandee"))

    # Garde-fou déterministe (pas un patch de prompt) : comparaison_etablissements_nommes
    # exige par définition au moins un nom propre cité. Si le LLM choisit cette
    # catégorie sans avoir extrait de nom (incohérence interne observée en test,
    # ex: "compare le meilleur collège de Lyon et de Marseille" — pas de nom
    # propre, juste des zones), on bascule vers non_reconnu -> agent ReAct,
    # seul chemin capable de gérer une comparaison multi-zones non prévue.
    if state["categorie"] == Categorie.COMPARAISON_ETABLISSEMENTS_NOMMES and not state["noms_etablissements"]:
        state["categorie"] = Categorie.NON_RECONNU

    # Garde-fou déterministe symétrique au précédent : si un ou plusieurs
    # noms propres d'établissements ont été extraits mais que la catégorie
    # choisie n'est pas comparaison_etablissements_nommes (ex: une question
    # sur UN SEUL établissement nommé, comme une évolution multi-années,
    # n'est pas perçue comme une "comparaison" par le LLM), on bascule quand
    # même vers cette catégorie -> passe par la résolution de nom fiable
    # (rechercher_etablissements_par_nom) plutôt que de laisser le nom
    # inexploité dans une autre catégorie qui ne sait pas le résoudre.
    if state["noms_etablissements"] and state["categorie"] != Categorie.COMPARAISON_ETABLISSEMENTS_NOMMES:
        state["categorie"] = Categorie.COMPARAISON_ETABLISSEMENTS_NOMMES

    # Garde-fou déterministe : question_methodologique sert de catégorie
    # "par défaut" un peu trop attractive pour le LLM du router dès qu'aucune
    # zone/nom n'est détecté (déjà observé une première fois avec la
    # classification non_reconnu, cf. S8.9). Si aucune zone n'est détectée ET
    # que la question contient un mot superlatif ("meilleur", "pire"...), ce
    # n'est pas une question de concept/méthodologie mais une demande de
    # classement à une échelle non gérée (ex: "le meilleur collège de
    # France") -> non_reconnu, laisse l'agent ReAct clarifier le périmètre.
    if (
        state["categorie"] == Categorie.QUESTION_METHODOLOGIQUE
        and state["zone_geo"] is None
        and _MOTS_SUPERLATIFS.search(state["question"])
    ):
        state["categorie"] = Categorie.NON_RECONNU

    # Garde-fou déterministe : même phénomène que ci-dessus, mais avec une
    # zone détectée cette fois. "Moyenne des collèges publics à Lyon"
    # ("zone" trouvée) tombait quand même dans question_methodologique au
    # lieu de recherche_geo_classement, qui sait désormais calculer une
    # moyenne déterministe sur une zone (cf. calculer_moyenne_etablissements,
    # S8.18) — pas une question de concept.
    if (
        state["categorie"] == Categorie.QUESTION_METHODOLOGIQUE
        and state["zone_geo"] is not None
        and _MOTS_AGREGATION.search(state["question"])
    ):
        state["categorie"] = Categorie.RECHERCHE_GEO_CLASSEMENT

    # Garde-fou déterministe : plusieurs zones combinées dans une seule
    # chaîne (ex: "Lyon, Perpignan, Poitiers" extrait comme une seule zone)
    # échouent systématiquement au géocodage — geo_tool attend une seule
    # adresse. Plutôt qu'un échec silencieux vers clarification_geo qui
    # n'aide pas l'utilisateur, bascule vers non_reconnu -> agent ReAct,
    # capable d'appeler recherche_geo séparément par zone. Volontairement
    # pas de support déterministe multi-zones pour l'instant (cas plus rare
    # et plus ouvert que les cas déjà sécurisés, cf. journal S8.19) — à
    # réévaluer si l'agent se montre fragile ou trop lent sur ces cas.
    if state["zone_geo"] and "," in state["zone_geo"]:
        state["categorie"] = Categorie.NON_RECONNU

    return state


def noeud_geo(state: AgentState) -> AgentState:
    # Zone déjà extraite par noeud_router (appel LLM fusionné, cf. plus haut) —
    # plus besoin d'un second appel LLM séparé ici.
    zone = state.get("zone_geo")

    if zone is None:
        state["resultats_geo"] = {
            "success": False,
            "adresse_recherchee": state["question"],
            "error": "Aucune zone géographique reconnaissable dans la question.",
        }
        return state

    state["resultats_geo"] = recherche_geo(zone)
    return state


def noeud_resolution_noms(state: AgentState) -> AgentState:
    """
    Résout les noms d'établissements en UAI. Lookup SQL déterministe (pas de
    LLM). Ne choisit JAMAIS un candidat par défaut en cas d'ambiguïté —
    route systématiquement vers clarification_noms dans ce cas.

    Si une zone géographique a déjà été extraite par le router (ex: "le
    collège Victor Hugo à Nantes"), on l'applique comme pré-filtre AVANT
    l'entonnoir interactif département/ville — pas besoin de redemander une
    info déjà donnée dans la question.

    Si ce pré-filtre par zone ne retourne AUCUN candidat, on ne se rabat
    JAMAIS silencieusement sur la liste complète (ce serait ignorer une
    contrainte explicite de l'utilisateur) : on marque explicitement le nom
    comme "zone_sans_resultat" pour que clarification_noms formule le bon
    message ("aucun Jean Moulin à Perpignan, précise une autre zone").
    """
    noms = state.get("noms_etablissements") or []
    if not noms:
        state["resolution_noms"] = {
            "success": False, "resultats": {}, "zones_sans_resultat": {},
            "error": "Aucun nom d'établissement identifié dans la question.",
        }
        state["uai_resolus"] = None
        return state

    resolution = rechercher_etablissements_par_nom(noms)

    if not resolution.get("success"):
        state["resolution_noms"] = resolution
        state["uai_resolus"] = None
        return state

    zone_geo = state.get("zone_geo")
    zones_sans_resultat = {}

    if zone_geo:
        for nom, candidats in resolution["resultats"].items():
            if len(candidats) <= 1:
                continue  # déjà résolu ou introuvable, la zone n'a rien à filtrer
            filtres = filtrer_candidats_par_precision(candidats, zone_geo)
            if not filtres:
                # La zone donnée ne correspond à aucun candidat pour ce nom —
                # on le signale explicitement, on ne l'ignore pas en silence.
                zones_sans_resultat[nom] = zone_geo
            else:
                resolution["resultats"][nom] = filtres

    resolution["zones_sans_resultat"] = zones_sans_resultat
    state["resolution_noms"] = resolution

    if zones_sans_resultat:
        state["uai_resolus"] = None
        return state

    uai_resolus = []
    for nom, candidats in resolution["resultats"].items():
        if len(candidats) != 1:
            # 0 ou 2+ candidats : ambigu ou introuvable, jamais de choix par défaut
            state["uai_resolus"] = None
            return state
        uai_resolus.append(candidats[0]["uai"])

    state["uai_resolus"] = uai_resolus
    return state


def noeud_sql(state: AgentState) -> AgentState:
    uai_filtre = None
    if state.get("resultats_geo") and state["resultats_geo"].get("success"):
        uai_filtre = [e["uai"] for e in state["resultats_geo"]["etablissements"]]
        if not uai_filtre:
            state["resultats_sql"] = {"success": True, "resultats": [], "nb_resultats": 0, "error": None}
            return state
        if _MOTS_AGREGATION.search(state["question"]):
            # Moyenne/agrégation demandée sur une zone : requête déterministe
            # (cf. calculer_moyenne_etablissements) plutôt que Text-to-SQL
            # général — pas de tableau détaillé par établissement ici, c'est
            # une agrégation statistique, pas une liste à afficher.
            resultat_moyenne = calculer_moyenne_etablissements(uai_filtre)
            state["resultats_sql"] = {
                "success": resultat_moyenne["success"],
                "agregation_geo": True,
                "global": resultat_moyenne["global"],
                "public": resultat_moyenne["public"],
                "prive": resultat_moyenne["prive"],
                "session_utilisee": resultat_moyenne["session_utilisee"],
                "error": resultat_moyenne["error"],
            }
            return state
        if state.get("secteur_souhaite") == SecteurSouhaite.INDIFFERENT:
            # Secteur non précisé sur un chemin géo : split déterministe top N
            # public / top N privé (cf. rechercher_top_par_secteur) plutôt que
            # de laisser le Text-to-SQL général produire un classement global
            # où le privé écrase mécaniquement le public (score plus élevé en
            # moyenne, lié au biais de sélection à l'entrée).
            ordre = "ASC" if _MOTS_PIRE.search(state["question"]) else "DESC"
            resultat_split = rechercher_top_par_secteur(uai_filtre, n=SPLIT_SECTEUR_N, ordre=ordre)
            state["resultats_sql"] = {
                "success": resultat_split["success"],
                "split_secteur": True,
                "ordre_pire": ordre == "ASC",
                "public": resultat_split["public"],
                "prive": resultat_split["prive"],
                "session_utilisee": resultat_split["session_utilisee"],
                "error": resultat_split["error"],
            }
            return state
    elif state.get("uai_resolus"):
        uai_filtre = state["uai_resolus"]
        if state.get("evolution_demandee"):
            # Établissement(s) nommé(s) déjà résolus + question portant sur
            # plusieurs années : requête déterministe (cf. obtenir_evolution_etablissements)
            # plutôt que Text-to-SQL général — fragilité réelle observée sur
            # cette combinaison précise (nom + zone + plusieurs années en une
            # seule requête libre, cf. session 8).
            resultat_evolution = obtenir_evolution_etablissements(uai_filtre)
            state["resultats_sql"] = {
                "success": resultat_evolution["success"],
                "resultats": resultat_evolution["resultats"],
                "nb_resultats": len(resultat_evolution["resultats"]),
                "sessions_disponibles": resultat_evolution["sessions_disponibles"],
                "error": resultat_evolution["error"],
            }
            return state
    state["resultats_sql"] = recherche_sql(state["question"], uai_filtre=uai_filtre)
    return state


def noeud_rag(state: AgentState) -> AgentState:
    state["resultats_rag"] = search_rag(state["question"])
    return state


AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "recherche_geo",
            "description": "Trouve les collèges dans un rayon autour d'une ville ou adresse.",
            "parameters": {
                "type": "object",
                "properties": {
                    "adresse_ou_ville": {"type": "string", "description": "Ville, adresse ou code postal."},
                },
                "required": ["adresse_ou_ville"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rechercher_etablissement_par_nom",
            "description": "Résout un ou plusieurs noms d'établissements en identifiants uniques (UAI) fiables. À utiliser EN PREMIER dès qu'un ou plusieurs établissements sont désignés par leur nom, avant recherche_sql — plus fiable que de laisser recherche_sql deviner un nom depuis du texte libre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "noms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Noms distinctifs à résoudre, sans le mot générique 'Collège' devant (ex: 'Chevreul', pas 'Collège Chevreul').",
                    },
                },
                "required": ["noms"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recherche_sql",
            "description": "Interroge les données chiffrées des collèges (résultats, scores, VA) à partir d'une question en langage naturel. Si un ou plusieurs UAI ont déjà été résolus (via rechercher_etablissement_par_nom ou recherche_geo), passe-les dans uai_filtre pour un filtrage fiable plutôt que de redécrire le nom ou la zone dans la question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "La question, reformulée si besoin pour cibler précisément la donnée recherchée (ex: la nuance temporelle : 'sur les 3 dernières années', 'en moyenne')."},
                    "uai_filtre": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "UAI déjà résolus à utiliser comme filtre exact. Laisser vide si aucune résolution préalable.",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculer_moyenne",
            "description": "Calcule la moyenne du score/taux/note pour un ensemble d'établissements déjà identifiés (via recherche_geo ou rechercher_etablissement_par_nom) — moyenne globale, plus détail public/privé. À utiliser DE PRÉFÉRENCE à recherche_sql dès que la question porte sur une moyenne/agrégation sur une zone — plus rapide et plus fiable qu'une requête libre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uais": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste des UAI (obtenue via recherche_geo ou rechercher_etablissement_par_nom) sur laquelle calculer la moyenne.",
                    },
                },
                "required": ["uais"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recherche_rag",
            "description": "Cherche une explication méthodologique dans les documents de référence (définition d'un indicateur, méthode de calcul, précautions d'interprétation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "requete": {"type": "string", "description": "La question ou le concept à rechercher."},
                },
                "required": ["requete"],
            },
        },
    },
]


def _resultat_geo_pour_agent(resultat_geo: dict) -> dict:
    """
    Version allégée du résultat de recherche_geo pour l'agent — seulement
    les UAI (nécessaires pour filtrer recherche_sql/calculer_moyenne
    ensuite) et un résumé, jamais le détail complet de chaque établissement
    (nom, commune, coordonnées...). Même principe que _tronquer_resultats_geo
    déjà appliqué au chemin déterministe (S1-S2) : évite un contexte de
    conversation surchargé — mesuré à 36 Ko pour une seule zone (Lyon)
    avant ce fix, ce qui ralentissait chaque tour suivant et risquait un
    timeout au-delà de 2-3 zones dans une même question (cf. session 8).
    """
    if not resultat_geo or not resultat_geo.get("success"):
        return resultat_geo
    return {
        "success": True,
        "adresse_normalisee": resultat_geo.get("adresse_normalisee"),
        "rayon_km": resultat_geo.get("rayon_km"),
        "nb_etablissements": resultat_geo.get("nb_etablissements"),
        "uais": [e["uai"] for e in resultat_geo.get("etablissements", [])],
        "error": None,
    }


def _executer_outil_agent(nom_outil: str, arguments: dict) -> dict:
    """
    Dispatch vers la fonction Python réelle correspondant à l'outil choisi
    par l'agent. Appelle directement les fonctions des outils (pas les
    nœuds noeud_geo/noeud_sql/noeud_rag) : ces nœuds écrivent dans le state
    partagé du graphe, conçu pour les chemins déterministes à un seul appel
    — l'agent, lui, peut appeler plusieurs outils dans un ordre libre, ses
    résultats vivent dans l'historique de conversation local à la boucle,
    pas dans le state partagé.
    """
    if nom_outil == "recherche_geo":
        return _resultat_geo_pour_agent(recherche_geo(arguments["adresse_ou_ville"]))
    if nom_outil == "rechercher_etablissement_par_nom":
        return rechercher_etablissements_par_nom(arguments["noms"])
    if nom_outil == "calculer_moyenne":
        return calculer_moyenne_etablissements(arguments["uais"])
    if nom_outil == "recherche_sql":
        resultat = recherche_sql(arguments["question"], uai_filtre=arguments.get("uai_filtre") or None)
        # Enrichit avec un tableau déjà formaté (même fonction de templating
        # que les chemins déterministes) — l'agent ne doit jamais recalculer
        # lui-même un score ou une VA, ni improviser sa propre mise en forme
        # d'un badge : cohérent avec le principe templating vs LLM du projet.
        lignes = resultat.get("resultats", []) if resultat.get("success") else []
        tableau = _generer_tableau_depuis_lignes(lignes)
        if tableau:
            contient_va = "badge_va" in json.dumps(lignes, default=str)
            bloc = (
                tableau
                + _generer_explication_score_template(True)
                + _generer_explication_va_template(contient_va)
            )
            resultat["tableau_formate"] = _ajouter_nuance_privee_si_besoin(bloc, resultat)
        return resultat
    if nom_outil == "recherche_rag":
        return search_rag(arguments["requete"])
    return {"success": False, "error": f"Outil inconnu : {nom_outil}"}


def noeud_agent_react(state: AgentState) -> AgentState:
    """
    Boucle ReAct : à chaque tour, le LLM décide d'appeler un outil de plus
    ou de répondre directement. Pas de chemin fixe — c'est précisément le
    rôle de ce nœud (cf. S1.5/S2.15 : agent à décision dynamique pour les
    questions trop complexes/combinées pour un workflow codé, ou hors du
    périmètre des 3 autres catégories).

    Génère sa propre réponse finale directement (state["reponse_finale"]),
    sans repasser par noeud_synthese : ce nœud suppose une forme fixe de
    resultats_sql produite par un seul appel déterministe, incompatible
    avec des appels multiples dans un ordre libre.

    Garde-fou déterministe en premier, avant tout appel LLM : au-delà de
    MAX_ZONES_COMPAREES zones dans la même question, l'agent devient trop
    lent/coûteux (timeout mesuré à 5 zones, ~96s avant échec — cf. session
    8). Plutôt que de laisser l'agent essayer et échouer après une longue
    attente, on bloque immédiatement avec un message explicite, sans coût
    ni latence.
    """
    nb_zones = len((state.get("zone_geo") or "").split(",")) if state.get("zone_geo") else 0
    if nb_zones > MAX_ZONES_COMPAREES:
        state["tours_agent"] = 0
        state["reponse_finale"] = (
            f"Je peux comparer jusqu'à {MAX_ZONES_COMPAREES} zones géographiques à la fois "
            f"(villes, départements...). Peux-tu reformuler ta question avec "
            f"{MAX_ZONES_COMPAREES} zones maximum ?"
        )
        return state

    messages = [
        {"role": "system", "content": AGENT_REACT_SYSTEM_PROMPT},
        {"role": "user", "content": state["question"]},
    ]

    for tour in range(AGENT_MAX_TOURS):
        state["tours_agent"] = tour + 1
        response = client.chat.completions.create(
            model=LLM_MODEL, temperature=0,
            messages=messages,
            tools=AGENT_TOOLS_SCHEMA,
            tool_choice="auto",
            timeout=LLM_TIMEOUT_SECONDS,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            # Pas d'appel d'outil : le LLM a choisi de répondre directement.
            state["reponse_finale"] = message.content
            return state

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ],
        })
        for tool_call in message.tool_calls:
            nom_outil = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            resultat = _executer_outil_agent(nom_outil, arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(resultat, ensure_ascii=False, default=str),
            })

    # Plafond de tours atteint sans réponse finale — dernier appel forcé,
    # sans outil disponible, pour obtenir une réponse avec ce qui a déjà
    # été trouvé plutôt que de laisser la boucle sans réponse.
    messages.append({
        "role": "user",
        "content": "Réponds maintenant avec les informations déjà obtenues, sans appeler d'autre outil.",
    })
    response = client.chat.completions.create(
        model=LLM_MODEL, temperature=0,
        messages=messages,
        timeout=LLM_TIMEOUT_SECONDS,
    )
    state["reponse_finale"] = response.choices[0].message.content
    return state


def _formater_badge_va(badge_va):
    """Traduit le badge_va en libellé lisible, gère le cas None."""
    if badge_va is None:
        return "non disponible"
    return badge_va


def _generer_tableau_generique(lignes, sessions_disponibles=None):
    """
    Rendu générique quand les lignes SQL n'ont pas la forme standard
    "établissement" (nom/secteur/score_principal...) — cas d'une requête
    d'agrégation (AVG, COUNT...) qui ne retourne qu'une ou quelques valeurs
    calculées. Affiche les colonnes réellement présentes plutôt que des "?"
    pour des colonnes qui n'existent pas dans ce résultat.

    Ajoute une note sur les sessions réellement couvertes par la base —
    une agrégation (moyenne, total...) implique souvent une période, et le
    nombre d'années disponibles peut être inférieur à ce qui a été demandé
    (ex: "10 dernières années" alors que seules 4 sessions existent) sans
    que ce soit signalé autrement.
    """
    if not lignes:
        return None
    colonnes = list(lignes[0].keys())
    entete = "| " + " | ".join(colonnes) + " |\n"
    separateur = "|" + "|".join(["---"] * len(colonnes)) + "|\n"
    corps = ""
    for r in lignes:
        valeurs = []
        for c in colonnes:
            v = r.get(c)
            if isinstance(v, float):
                v = f"{v:.2f}"
            valeurs.append(str(v) if v is not None else "?")
        corps += "| " + " | ".join(valeurs) + " |\n"
    tableau = entete + separateur + corps
    if sessions_disponibles:
        tableau += f"\n*Calculé sur les {len(sessions_disponibles)} années disponibles en base : {', '.join(sessions_disponibles)}.*\n"
    return tableau


def _generer_moyennes_par_etablissement(lignes):
    """
    Calcule la moyenne du score (et taux/note quand disponibles) par
    établissement, à partir de lignes couvrant plusieurs sessions — calcul
    déterministe en Python, pas de LLM. Groupé par nom d'établissement pour
    ne jamais mélanger les moyennes de deux établissements différents
    (ex: comparaison de l'évolution de 2 collèges nommés en même temps).
    """
    par_etablissement = {}
    for r in lignes:
        par_etablissement.setdefault(r.get("nom", "?"), []).append(r)

    blocs = []
    for nom_etab, rows_etab in par_etablissement.items():
        scores = [r["score_principal"] for r in rows_etab if isinstance(r.get("score_principal"), (int, float))]
        if not scores:
            continue
        ligne = f"**{nom_etab}** — score moyen : {sum(scores) / len(scores):.2f} (sur {len(scores)} année(s))"
        taux = [r["brevet_taux_reussite_general"] for r in rows_etab if isinstance(r.get("brevet_taux_reussite_general"), (int, float))]
        if taux:
            ligne += f", taux de réussite moyen : {sum(taux) / len(taux):.1f}%"
        note = [r["brevet_note_ecrit_general"] for r in rows_etab if isinstance(r.get("brevet_note_ecrit_general"), (int, float))]
        if note:
            ligne += f", note écrit moyenne : {sum(note) / len(note):.1f}"
        blocs.append(ligne)
    return "\n\n".join(blocs)


def _generer_tableau_depuis_lignes(lignes, sessions_disponibles=None):
    """Génère le tableau markdown depuis une liste de lignes déjà résolues — aucune génération LLM."""
    if not lignes:
        return None
    if "nom" not in lignes[0]:
        # Forme non standard (ex: résultat d'agrégation type moyenne) —
        # le template à colonnes fixes ne s'applique pas ici.
        return _generer_tableau_generique(lignes, sessions_disponibles)

    # Colonne Session ajoutée seulement si présente (ex: évolution sur
    # plusieurs années) — absente sur le tableau standard un-seul-an.
    contient_session = "session" in lignes[0]
    if contient_session:
        entete = "| Session | Nom | Secteur | Score | VA | Taux de réussite | Note écrit |\n"
        separateur = "|---|---|---|---|---|---|---|\n"
    else:
        entete = "| Nom | Secteur | Score | VA | Taux de réussite | Note écrit |\n"
        separateur = "|---|---|---|---|---|---|\n"
    corps = ""
    for r in lignes:
        nom = r.get("nom", "?")
        secteur = r.get("secteur", "?")
        score = r.get("score_principal")
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "?"
        va = _formater_badge_va(r.get("badge_va"))
        taux = r.get("brevet_taux_reussite_general")
        taux_str = f"{taux:.1f}" if isinstance(taux, (int, float)) else "?"
        note = r.get("brevet_note_ecrit_general")
        note_str = f"{note:.1f}" if isinstance(note, (int, float)) else "?"
        if contient_session:
            corps += f"| {r.get('session', '?')} | {nom} | {secteur} | {score_str} | {va} | {taux_str} | {note_str} |\n"
        else:
            corps += f"| {nom} | {secteur} | {score_str} | {va} | {taux_str} | {note_str} |\n"

    tableau = entete + separateur + corps
    if contient_session:
        # Si la question demande une moyenne, il faut afficher une vraie
        # moyenne chiffrée, pas seulement le détail par année — affichée
        # avant le tableau de détail.
        moyennes = _generer_moyennes_par_etablissement(lignes)
        if moyennes:
            tableau = moyennes + "\n\n" + tableau
    if sessions_disponibles and contient_session:
        tableau += f"\n*Sur les {len(sessions_disponibles)} années disponibles en base : {', '.join(sessions_disponibles)}.*\n"
    return tableau


def _generer_tableau_etablissements(resultats_sql):
    """
    Génère le tableau markdown directement depuis les données SQL —
    aucune génération LLM ici. Ces données sont déjà connues et fiables,
    les faire "recopier" par un LLM ne fait qu'ajouter latence et risque
    d'erreur de recopie, sans aucune valeur ajoutée.
    """
    if not resultats_sql or not resultats_sql.get("success"):
        return None
    return _generer_tableau_depuis_lignes(
        resultats_sql.get("resultats", []), resultats_sql.get("sessions_disponibles")
    )


def _generer_tableaux_split_secteur(resultats_sql):
    """
    Génère deux tableaux markdown distincts (public / privé) plutôt qu'un
    classement global — évite qu'un secteur soit mécaniquement absent de
    l'affichage quand ses scores sont structurellement plus bas (cf. biais
    de sélection à l'entrée du privé).
    """
    if not resultats_sql or not resultats_sql.get("success"):
        return None
    public = resultats_sql.get("public", [])
    prive = resultats_sql.get("prive", [])
    if not public and not prive:
        return None

    bloc_public = _generer_tableau_depuis_lignes(public) or "Aucun établissement public trouvé dans cette zone."
    bloc_prive = _generer_tableau_depuis_lignes(prive) or "Aucun établissement privé trouvé dans cette zone."
    return f"**Établissements publics**\n\n{bloc_public}\n\n**Établissements privés**\n\n{bloc_prive}"


def _formater_stats_moyenne(stats, label):
    """Une ligne de statistiques agrégées formatée pour un secteur ou une moyenne globale."""
    if not stats:
        return f"**{label}** : aucune donnée disponible dans cette zone."
    nb = stats.get("nb_etablissements", 0)
    score = stats.get("score_moyen")
    taux = stats.get("taux_moyen")
    note = stats.get("note_moyenne")
    score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "?"
    taux_str = f"{taux:.1f}%" if isinstance(taux, (int, float)) else "?"
    note_str = f"{note:.1f}" if isinstance(note, (int, float)) else "?"
    return (
        f"**{label}** (sur {nb} établissement(s)) : score moyen {score_str}, "
        f"taux de réussite moyen {taux_str}, note écrit moyenne {note_str}"
    )


def _generer_moyennes_geo_template(resultats_sql, secteur_souhaite):
    """
    Génère le texte des moyennes agrégées sur une zone géographique — pas
    de tableau détaillé par établissement, c'est une agrégation statistique.
    Si le secteur est précisé, affiche uniquement ce secteur. Sinon, la
    moyenne globale (tous secteurs confondus) en premier, puis le détail
    public/privé en complément — la moyenne globale seule masquerait
    l'écart réel entre secteurs (vérifié empiriquement, cf. journal S8.17).
    """
    if not resultats_sql or not resultats_sql.get("success"):
        return None
    if secteur_souhaite == SecteurSouhaite.PUBLIC:
        return _formater_stats_moyenne(resultats_sql.get("public"), "Établissements publics")
    if secteur_souhaite == SecteurSouhaite.PRIVE:
        return _formater_stats_moyenne(resultats_sql.get("prive"), "Établissements privés")
    blocs = [_formater_stats_moyenne(resultats_sql.get("global"), "Moyenne globale (tous secteurs confondus)")]
    if resultats_sql.get("public") or resultats_sql.get("prive"):
        blocs.append(_formater_stats_moyenne(resultats_sql.get("public"), "Établissements publics"))
        blocs.append(_formater_stats_moyenne(resultats_sql.get("prive"), "Établissements privés"))
    return "\n\n".join(blocs)


def _zone_affichage(resultats_geo):
    """Nom de zone à afficher dans l'intro — factorisé, utilisé par les deux variantes d'intro."""
    if resultats_geo and resultats_geo.get("success"):
        return resultats_geo.get("adresse_normalisee", "la zone recherchée")
    return "la zone recherchée"


def _generer_intro_template(resultats_geo, nb_affiches, question=""):
    """
    Intro 100% template — insertion de chiffres, aucune génération LLM.
    Le qualificatif ("meilleurs" vs "moins bons") reflète le tri réellement
    demandé — bug réel corrigé (S8.20) : ce texte disait toujours "meilleurs
    résultats", même en affichant les pires établissements demandés.
    """
    qualificatif = "présentant les moins bons résultats" if _MOTS_PIRE.search(question) else "présentant les meilleurs résultats"
    if resultats_geo and resultats_geo.get("success"):
        total = resultats_geo.get("nb_etablissements", 0)
        zone = _zone_affichage(resultats_geo)
        if nb_affiches < total:
            return f"Dans la zone recherchée autour de {zone}, {total} établissements ont été identifiés. Voici les {nb_affiches} {qualificatif} :"
        return f"Voici les établissements trouvés autour de {zone} :"
    if nb_affiches == 1:
        return "Voici les informations pour l'établissement demandé :"
    return "Voici les résultats trouvés :"


def _generer_intro_split_template(resultats_geo, nb_public, nb_prive, ordre_pire=False):
    """Intro 100% template pour le cas split public/privé — aucune génération LLM."""
    zone = _zone_affichage(resultats_geo)
    qualificatif = "moins bons" if ordre_pire else "meilleurs"
    return (
        f"Voici les {nb_public} {qualificatif} établissements publics et les {nb_prive} "
        f"{qualificatif} établissements privés trouvés autour de {zone}, affichés séparément "
        f"pour représenter les deux secteurs équitablement :"
    )


def _generer_intro_agregation_template(resultats_geo):
    """Intro 100% template pour le cas moyenne/agrégation sur une zone — aucune génération LLM."""
    zone = _zone_affichage(resultats_geo)
    return f"Voici les moyennes calculées pour les établissements trouvés autour de {zone} :"


def _preparer_affichage_resultats(resultats_sql, resultats_geo, secteur_souhaite=None, question=""):
    """
    Prépare le tableau et l'intro à partir des résultats SQL déjà tronqués,
    en gérant les trois formats possibles (classement normal, split
    public/privé, ou moyenne/agrégation sur zone). Centralise ce branchement
    à un seul endroit plutôt que de le répéter à chaque étape de noeud_synthese.

    Retourne (tableau: str|None, intro: str).
    """
    if resultats_sql and resultats_sql.get("agregation_geo"):
        tableau = _generer_moyennes_geo_template(resultats_sql, secteur_souhaite)
        intro = _generer_intro_agregation_template(resultats_geo)
        return tableau, intro

    if resultats_sql and resultats_sql.get("split_secteur"):
        tableau = _generer_tableaux_split_secteur(resultats_sql)
        nb_public = len(resultats_sql.get("public", []))
        nb_prive = len(resultats_sql.get("prive", []))
        intro = _generer_intro_split_template(resultats_geo, nb_public, nb_prive, resultats_sql.get("ordre_pire", False))
        return tableau, intro

    tableau = _generer_tableau_etablissements(resultats_sql)
    nb_affiches = len(resultats_sql.get("resultats", [])) if resultats_sql else 0
    intro = _generer_intro_template(resultats_geo, nb_affiches, question)
    return tableau, intro


def _generer_explication_score_template(tableau_contient_score):
    """Explication du score 100% template — texte fixe, condition simple."""
    if not tableau_contient_score:
        return ""
    return ("\n\nLe score combine le taux de réussite (60%) et la note à l'écrit (40%), "
            "comparés aux autres établissements de la même année — ce n'est pas une "
            "note absolue.")


def _generer_explication_va_template(tableau_contient_va):
    """Explication VA 100% template — texte fixe, condition simple."""
    if not tableau_contient_va:
        return ""
    return ("\n\nLa VA (valeur ajoutée) compare les résultats réels de l'établissement "
            "à ceux attendus compte tenu du profil de ses élèves — un badge positif "
            "signifie que l'établissement fait mieux que prévu.")


SYNTHESE_SYSTEM_PROMPT = """
Ton unique rôle : synthétiser en 1-2 phrases les chunks RAG fournis, pour
apporter une nuance méthodologique à la réponse. Tu n'es appelé QUE quand
du contenu RAG existe — l'intro, le tableau et les autres explications sont
déjà générés séparément, ne les reproduis jamais.

Règles strictes :
- Cite la nuance en te basant uniquement sur les chunks RAG fournis.
- N'utilise JAMAIS de termes techniques d'implémentation (SQL, base de
  données, requête, outil, backend).
- N'ajoute JAMAIS de conseil non issu des données fournies.
- Reste bref.
"""


def _generer_nuance_rag(question, resultats_rag):
    """
    Appelle le LLM pour synthétiser une nuance méthodologique à partir des
    chunks RAG fournis — seule tâche légitime pour un LLM dans la synthèse
    (interprétation de texte non structuré). Chaîne vide si aucun chunk
    pertinent n'a été trouvé (pas d'appel LLM dans ce cas : latence ~0,
    coût ~0, pas de risque d'hallucination sur cette partie de la réponse).
    """
    chunks_rag = (resultats_rag or {}).get("chunks", []) if resultats_rag else []
    if not chunks_rag:
        return ""

    contexte = {"question": question, "resultats_rag": resultats_rag}
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYNTHESE_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(contexte, ensure_ascii=False, default=str)},
        ],
        timeout=LLM_TIMEOUT_SECONDS,
    )
    return "\n\n" + response.choices[0].message.content


NUANCE_PRIVE = (
    "\n\n⚠️ Précision importante : ce n'est pas un classement officiel. "
    "Les établissements privés peuvent pratiquer une sélection à l'entrée, "
    "ce qui peut influencer leurs résultats indépendamment de la qualité "
    "pédagogique."
)


def _etablissement_prive_present(resultats_sql, secteur_souhaite=None):
    """
    Détecte un établissement privé RÉELLEMENT AFFICHÉ dans les résultats,
    quel que soit le format (normal, split, ou moyenne/agrégation sur zone).
    Défensif : une ligne d'établissement (qui a un "nom") sans champ
    "secteur" du tout (ex: Text-to-SQL ayant omis la colonne malgré la
    règle du prompt) est traitée comme potentiellement privée plutôt
    qu'ignorée — mieux vaut un avertissement affiché à tort qu'un
    avertissement de sécurité manquant à tort sur un vrai établissement
    privé. Les lignes d'agrégation générique (sans "nom", ex: une moyenne
    calculée par le Text-to-SQL général) n'ont jamais de secteur par nature
    et ne déclenchent rien.

    Cas "moyenne/agrégation sur zone" (agregation_geo) : les stats "public"
    et "prive" sont TOUJOURS calculées en interne (cf. calculer_moyenne_etablissements),
    même quand secteur_souhaite=public ne fait afficher que le secteur
    public — sans secteur_souhaite ici, l'avertissement apparaîtrait à tort
    sur une réponse qui ne montre aucune donnée privée.
    """
    if not resultats_sql:
        return False
    if resultats_sql.get("split_secteur"):
        return len(resultats_sql.get("prive", [])) > 0
    if resultats_sql.get("agregation_geo"):
        if secteur_souhaite == SecteurSouhaite.PUBLIC:
            return False
        prive = resultats_sql.get("prive")
        return bool(prive and prive.get("nb_etablissements", 0) > 0)
    lignes = resultats_sql.get("resultats", [])
    return any(
        "nom" in row and row.get("secteur", Secteur.PRIVE) == Secteur.PRIVE
        for row in lignes
    )


def _ajouter_nuance_privee_si_besoin(reponse, resultats_sql, secteur_souhaite=None):
    """
    Garde-fou en code (pas seulement en prompt) : si au moins un établissement
    privé figure RÉELLEMENT dans ce qui est affiché (non tronqué — le biais
    de sélection reste valable même si l'établissement privé n'est pas dans
    les lignes affichées, sauf cas agregation_geo où le secteur peut être
    explicitement filtré), la nuance est ajoutée systématiquement, que le
    LLM l'ait fait ou non.
    """
    if _etablissement_prive_present(resultats_sql, secteur_souhaite) and NUANCE_PRIVE.strip() not in reponse:
        return reponse + NUANCE_PRIVE
    return reponse


def _tronquer_resultats_sql(resultats_sql):
    """Limite le nombre de lignes envoyées en synthèse, avec mention du total réel."""
    if not resultats_sql or not resultats_sql.get("success"):
        return resultats_sql
    if resultats_sql.get("split_secteur"):
        return resultats_sql  # déjà plafonné à la source (top n par secteur)
    lignes = resultats_sql.get("resultats", [])
    if len(lignes) <= MAX_LIGNES_SYNTHESE:
        return resultats_sql
    copie = dict(resultats_sql)
    copie["resultats"] = lignes[:MAX_LIGNES_SYNTHESE]
    copie["nb_resultats_total_reel"] = len(lignes)
    copie["note"] = f"Affichage limité à {MAX_LIGNES_SYNTHESE} résultats sur {len(lignes)} trouvés."
    return copie


def noeud_clarification_geo(state: AgentState) -> AgentState:
    """
    Appelé quand geo_tool échoue sur un chemin qui en dépend. Ne tente
    jamais de laisser sql_tool deviner une zone géographique en silence.
    """
    state["reponse_finale"] = (
        "Je n'ai pas réussi à identifier la zone géographique de ta question. "
        "Peux-tu préciser une adresse, une ville ou un code postal ?"
    )
    return state


def noeud_clarification_noms(state: AgentState) -> AgentState:
    """
    Appelé quand un nom d'établissement est ambigu (plusieurs candidats),
    introuvable (zéro candidat), ou quand la zone donnée dans la question ne
    correspond à aucun candidat. Ne choisit jamais un résultat par défaut,
    et ne substitue jamais silencieusement une zone différente de celle
    demandée — le message distingue explicitement ces 3 cas.
    """
    resolution = state.get("resolution_noms") or {}
    candidats_par_nom = resolution.get("resultats", {})
    zones_sans_resultat = resolution.get("zones_sans_resultat", {})

    if not candidats_par_nom:
        state["reponse_finale"] = (
            "Je n'ai pas identifié d'établissement nommé dans ta question. "
            "Peux-tu préciser le nom du ou des établissements à comparer ?"
        )
        return state

    morceaux = []
    for nom, candidats in candidats_par_nom.items():
        if nom in zones_sans_resultat:
            zone = zones_sans_resultat[nom]
            morceaux.append(
                f"Aucun établissement nommé « {nom} » n'a été trouvé pour « {zone} ». "
                f"Précise une autre ville ou un autre département."
            )
        elif len(candidats) == 0:
            morceaux.append(f"Aucun établissement nommé « {nom} » n'a été trouvé dans les données.")
        elif len(candidats) > 1:
            lignes = "\n".join(
                f"  {i + 1}. {c['nom']} — {c['commune']} ({c['secteur']})"
                for i, c in enumerate(candidats)
            )
            morceaux.append(f"Plusieurs établissements correspondent à « {nom} » :\n{lignes}")

    state["reponse_finale"] = (
        "\n\n".join(morceaux)
        + "\n\nPeux-tu préciser lequel tu veux (numéro, ville ou département) ?"
    )
    return state


def _lignes_contiennent(resultats_sql, cle):
    """
    Vérifie si les LIGNES de résultat (pas tout l'objet resultats_sql)
    contiennent une colonne donnée — contrairement à une recherche sur le
    JSON entier, insensible au fait que le texte de la requête SQL
    elle-même (sql_genere) puisse mentionner ce nom sans que la colonne
    soit réellement présente dans les lignes retournées (ex: AVG(score_principal)
    renommé en "moyenne_score" ne contient plus la clé "score_principal").
    """
    if not resultats_sql:
        return False
    if resultats_sql.get("split_secteur"):
        lignes = (resultats_sql.get("public") or []) + (resultats_sql.get("prive") or [])
    else:
        lignes = resultats_sql.get("resultats") or []
    return bool(lignes) and cle in lignes[0]


def noeud_synthese(state: AgentState) -> AgentState:
    resultats_sql_tronques = _tronquer_resultats_sql(state.get("resultats_sql"))

    tableau, intro = _preparer_affichage_resultats(
        resultats_sql_tronques, state.get("resultats_geo"), state.get("secteur_souhaite"), state["question"]
    )
    # Forme "moyenne/agrégation" : la clé du score n'est pas "score_principal"
    # (c'est "score_moyen", agrégé) — _lignes_contiennent ne la détecterait
    # pas, donc court-circuit explicite : le score moyen est toujours
    # affiché dès que ce type de tableau existe.
    est_agregation_geo = bool(resultats_sql_tronques and resultats_sql_tronques.get("agregation_geo"))
    tableau_contient_va = _lignes_contiennent(resultats_sql_tronques, "badge_va")
    tableau_contient_score = est_agregation_geo or _lignes_contiennent(resultats_sql_tronques, "score_principal")

    texte_nuance_rag = _generer_nuance_rag(state["question"], state.get("resultats_rag"))

    explication_score = _generer_explication_score_template(tableau_contient_score)
    explication_va = _generer_explication_va_template(tableau_contient_va)

    reponse = intro
    if tableau:
        reponse += "\n\n" + tableau
    reponse += texte_nuance_rag + explication_score + explication_va

    reponse = _ajouter_nuance_privee_si_besoin(reponse, state.get("resultats_sql"), state.get("secteur_souhaite"))

    state["reponse_finale"] = reponse
    return state


def router_vers_chemin(state: AgentState) -> str:
    return state["categorie"]


def router_apres_geo(state: AgentState) -> str:
    """Après geo_tool : succès -> sql_tool, échec -> clarification directe (jamais sql_tool en silence)."""
    if state.get("resultats_geo") and state["resultats_geo"].get("success"):
        return "sql_tool"
    return "clarification_geo"


def router_apres_resolution_noms(state: AgentState) -> str:
    """Après resolution_noms : tout résolu sans ambiguïté -> sql_tool, sinon -> clarification."""
    if state.get("uai_resolus"):
        return "sql_tool"
    return "clarification_noms"


def router_apres_sql(state: AgentState) -> str:
    """
    Après sql_tool : si la question demande aussi une nuance méthodologique
    (signal indépendant de la catégorie de base — géo ou noms), passer par
    rag_tool avant la synthèse. Sinon, synthèse directe.
    """
    if state.get("nuance_methodologique_demandee"):
        return "rag_tool"
    return "synthese"


def construire_graphe():
    graph = StateGraph(AgentState)
    graph.add_node("router", noeud_router)
    graph.add_node("geo_tool", noeud_geo)
    graph.add_node("resolution_noms", noeud_resolution_noms)
    graph.add_node("sql_tool", noeud_sql)
    graph.add_node("rag_tool", noeud_rag)
    graph.add_node("agent_react", noeud_agent_react)
    graph.add_node("clarification_geo", noeud_clarification_geo)
    graph.add_node("clarification_noms", noeud_clarification_noms)
    graph.add_node("synthese", noeud_synthese)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", router_vers_chemin, {
        Categorie.RECHERCHE_GEO_CLASSEMENT: "geo_tool",
        Categorie.COMPARAISON_ETABLISSEMENTS_NOMMES: "resolution_noms",
        Categorie.QUESTION_METHODOLOGIQUE: "rag_tool",
        Categorie.NON_RECONNU: "agent_react",
    })
    graph.add_conditional_edges("geo_tool", router_apres_geo, {
        "sql_tool": "sql_tool",
        "clarification_geo": "clarification_geo",
    })
    graph.add_conditional_edges("resolution_noms", router_apres_resolution_noms, {
        "sql_tool": "sql_tool",
        "clarification_noms": "clarification_noms",
    })
    graph.add_conditional_edges("sql_tool", router_apres_sql, {
        "rag_tool": "rag_tool",
        "synthese": "synthese",
    })
    graph.add_edge("clarification_geo", END)
    graph.add_edge("clarification_noms", END)
    graph.add_edge("rag_tool", "synthese")
    graph.add_edge("agent_react", END)  # réponse générée directement par l'agent, pas de re-templating
    graph.add_edge("synthese", END)
    return graph.compile()


if __name__ == "__main__":
    app = construire_graphe()
    resultat = app.invoke({
        "question": "C'est quoi l'IPS ?", "dc_niveau": "accessible",
        "categorie": None, "zone_geo": None, "resultats_geo": None, "resultats_sql": None,
        "resultats_rag": None, "reponse_finale": None, "tours_agent": 0,
        "noms_etablissements": [], "resolution_noms": None, "uai_resolus": None,
    })
    print("Catégorie :", resultat["categorie"])
    print("Réponse :", resultat["reponse_finale"])
