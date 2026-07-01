"""graph_router.py — V3 : load_dotenv() explicite en premier (fix LangSmith EU)"""

from dotenv import load_dotenv
load_dotenv()  # DOIT être appelé avant tout import LangGraph/LangSmith, pour
                # que LANGSMITH_ENDPOINT soit lu correctement dès le départ.

import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from openai import OpenAI
from langsmith.wrappers import wrap_openai

from agent.tools.rag_tool import search_rag
from agent.tools.sql_tool import recherche_sql
from agent.tools.geo_tool import recherche_geo

from config import LLM_MODEL, AGENT_MAX_TOURS, LLM_TIMEOUT_SECONDS
from prompts.router_system_prompt import ROUTER_SYSTEM_PROMPT

client = wrap_openai(OpenAI())  # rend chaque appel visible dans LangSmith (tokens, latence par appel)


class AgentState(TypedDict):
    question: str
    dc_niveau: str
    categorie: Optional[str]
    zone_geo: Optional[str]
    resultats_geo: Optional[dict]
    resultats_sql: Optional[dict]
    resultats_rag: Optional[dict]
    reponse_finale: Optional[str]
    tours_agent: int


CATEGORIES = [
    "recherche_geo_classement", "comparaison_etablissements_nommes",
    "recherche_geo_comparaison", "question_methodologique",
    "recherche_geo_methodologique", "non_reconnu",
]

ROUTER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "classifier_question",
        "description": "Classifie la question utilisateur et extrait sa zone géographique en un seul passage.",
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {"type": "string", "enum": CATEGORIES},
                "zone_detectee": {
                    "type": "boolean",
                    "description": "true si la question mentionne une zone géographique géocodable (ville, adresse, code postal, département). Un nom de région touristique informel (ex: Côte d'Opale) compte comme false.",
                },
                "zone": {
                    "type": "string",
                    "description": "La zone géographique extraite si zone_detectee=true, sinon chaîne vide.",
                },
            },
            "required": ["categorie", "zone_detectee", "zone"],
        },
    },
}


def noeud_router(state: AgentState) -> AgentState:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": state["question"]},
        ],
        tools=[ROUTER_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "classifier_question"}},
        timeout=LLM_TIMEOUT_SECONDS,
    )
    args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    state["categorie"] = args["categorie"]
    # Zone géographique extraite en même temps que la classification —
    # évite un second appel LLM séparé (gain de latence).
    state["zone_geo"] = args["zone"] if args.get("zone_detectee") else None
    return state


EXTRACTION_ZONE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extraire_zone",
        "description": "Extrait la zone géographique géocodable d'une question.",
        "parameters": {
            "type": "object",
            "properties": {
                "zone_detectee": {
                    "type": "boolean",
                    "description": "true si une zone géocodable (ville, adresse, code postal, département) est identifiable",
                },
                "zone": {
                    "type": "string",
                    "description": "La zone extraite (vide si zone_detectee=false)",
                },
            },
            "required": ["zone_detectee", "zone"],
        },
    },
}


def extraire_zone_geo(question: str) -> str | None:
    """
    Isole la zone géographique (ville, adresse, code postal) d'une question
    complète. Utilise le function calling (sortie structurée) plutôt qu'une
    comparaison de texte libre — évite toute fragilité liée à la ponctuation
    ou au format exact de la réponse du LLM.

    Retourne la zone extraite (str), ou None si aucune zone géocodable.
    """
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": (
                "Extrais la zone géographique géocodable mentionnée dans la "
                "question (ville, adresse, code postal, département). "
                "Un nom de région touristique informel (ex: 'Côte d'Opale') "
                "n'est pas géocodable : zone_detectee=false dans ce cas."
            )},
            {"role": "user", "content": question},
        ],
        tools=[EXTRACTION_ZONE_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "extraire_zone"}},
        temperature=0,
    )
    import json as _json
    args = _json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    if not args.get("zone_detectee"):
        return None
    return args["zone"]


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


def noeud_sql(state: AgentState) -> AgentState:
    uai_filtre = None
    if state.get("resultats_geo") and state["resultats_geo"].get("success"):
        uai_filtre = [e["uai"] for e in state["resultats_geo"]["etablissements"]]
        if not uai_filtre:
            state["resultats_sql"] = {"success": True, "resultats": [], "nb_resultats": 0, "error": None}
            return state
    state["resultats_sql"] = recherche_sql(state["question"], uai_filtre=uai_filtre)
    return state


def noeud_rag(state: AgentState) -> AgentState:
    state["resultats_rag"] = search_rag(state["question"])
    return state


def noeud_agent_react(state: AgentState) -> AgentState:
    state["tours_agent"] = 0
    while state["tours_agent"] < AGENT_MAX_TOURS:
        state["tours_agent"] += 1
        break  # TODO : vraie boucle de décision, session dédiée
    return state


def _formater_badge_va(badge_va):
    """Traduit le badge_va en libellé lisible, gère le cas None."""
    if badge_va is None:
        return "non disponible"
    return badge_va


def _generer_tableau_etablissements(resultats_sql):
    """
    Génère le tableau markdown directement depuis les données SQL —
    aucune génération LLM ici. Ces données sont déjà connues et fiables,
    les faire "recopier" par un LLM ne fait qu'ajouter latence et risque
    d'erreur de recopie, sans aucune valeur ajoutée.
    """
    if not resultats_sql or not resultats_sql.get("success"):
        return None
    lignes = resultats_sql.get("resultats", [])
    if not lignes:
        return None

    entete = "| Nom | Secteur | Score | Taux de réussite | VA | Note écrit |\n"
    separateur = "|---|---|---|---|---|---|\n"
    corps = ""
    for r in lignes:
        nom = r.get("nom", "?")
        secteur = r.get("secteur", "?")
        score = r.get("score_principal")
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "?"
        taux = r.get("brevet_taux_reussite_general")
        taux_str = f"{taux:.1f}" if isinstance(taux, (int, float)) else "?"
        va = _formater_badge_va(r.get("badge_va"))
        note = r.get("brevet_note_ecrit_general")
        note_str = f"{note:.1f}" if isinstance(note, (int, float)) else "?"
        corps += f"| {nom} | {secteur} | {score_str} | {taux_str} | {va} | {note_str} |\n"

    return entete + separateur + corps


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


MAX_LIGNES_SYNTHESE = 15  # limite de sécurité — évite d'envoyer des centaines de lignes au LLM de synthèse


def _tronquer_resultats_sql(resultats_sql):
    """Limite le nombre de lignes envoyées en synthèse, avec mention du total réel."""
    if not resultats_sql or not resultats_sql.get("success"):
        return resultats_sql
    lignes = resultats_sql.get("resultats", [])
    if len(lignes) <= MAX_LIGNES_SYNTHESE:
        return resultats_sql
    copie = dict(resultats_sql)
    copie["resultats"] = lignes[:MAX_LIGNES_SYNTHESE]
    copie["nb_resultats_total_reel"] = len(lignes)
    copie["note"] = f"Affichage limité à {MAX_LIGNES_SYNTHESE} résultats sur {len(lignes)} trouvés."
    return copie


def _tronquer_resultats_geo(resultats_geo):
    """
    resultats_geo sert uniquement à donner un chiffre de contexte (nombre total
    dans la zone) — on ne garde AUCUN détail d'établissement individuel, pour
    éviter tout risque de citation hors-contexte par le LLM de synthèse (cf.
    hallucination "Collège Raoul Follereau" détectée en test).
    """
    if not resultats_geo or not resultats_geo.get("success"):
        return resultats_geo
    return {
        "success": True,
        "adresse_normalisee": resultats_geo.get("adresse_normalisee"),
        "rayon_km": resultats_geo.get("rayon_km"),
        "nb_etablissements": resultats_geo.get("nb_etablissements"),
        # Volontairement : pas de clé "etablissements" — le détail individuel
        # n'a rien à faire dans la synthèse, seul le chiffre total est utile.
    }


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


def _generer_intro_template(resultats_geo, nb_affiches):
    """Intro 100% template — insertion de chiffres, aucune génération LLM."""
    if resultats_geo and resultats_geo.get("success"):
        total = resultats_geo.get("nb_etablissements", 0)
        zone = resultats_geo.get("adresse_normalisee", "la zone recherchée")
        if nb_affiches < total:
            return f"Dans la zone recherchée autour de {zone}, {total} établissements ont été identifiés. Voici les {nb_affiches} présentant les meilleurs résultats :"
        return f"Voici les établissements trouvés autour de {zone} :"
    return "Voici les résultats trouvés :"


def _generer_explication_va_template(tableau_contient_va):
    """Explication VA 100% template — texte fixe, condition simple."""
    if not tableau_contient_va:
        return ""
    return ("\n\nLa VA (valeur ajoutée) compare les résultats réels de l'établissement "
            "à ceux attendus compte tenu du profil de ses élèves — un badge positif "
            "signifie que l'établissement fait mieux que prévu.")


def noeud_synthese(state: AgentState) -> AgentState:
    resultats_sql_tronques = _tronquer_resultats_sql(state.get("resultats_sql"))
    resultats_rag = state.get("resultats_rag")

    tableau = _generer_tableau_etablissements(resultats_sql_tronques)
    nb_affiches = len(resultats_sql_tronques.get("resultats", [])) if resultats_sql_tronques else 0
    tableau_contient_va = tableau is not None and "badge_va" in json.dumps(resultats_sql_tronques or {})

    # Y a-t-il vraiment du contenu RAG à interpréter ? Seul cas où un LLM
    # a une tâche légitime — nuancer du texte non structuré. Sinon, tout
    # est template : pas d'appel LLM du tout (latence ~0, coût ~0, pas
    # de risque d'hallucination sur cette partie de la réponse).
    chunks_rag = (resultats_rag or {}).get("chunks", []) if resultats_rag else []

    if chunks_rag:
        # Cas avec RAG : le LLM ne fait QUE la nuance méthodologique,
        # jamais l'intro ni le tableau (déjà générés en template).
        contexte = {
            "question": state["question"],
            "resultats_rag": resultats_rag,
        }
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYNTHESE_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(contexte, ensure_ascii=False, default=str)},
            ],
            timeout=LLM_TIMEOUT_SECONDS,
        )
        texte_nuance_rag = "\n\n" + response.choices[0].message.content
    else:
        texte_nuance_rag = ""

    intro = _generer_intro_template(state.get("resultats_geo"), nb_affiches)
    explication_va = _generer_explication_va_template(tableau_contient_va)

    reponse = intro
    if tableau:
        reponse += "\n\n" + tableau
    reponse += texte_nuance_rag + explication_va

    # Garde-fou en code (pas seulement en prompt) : si au moins un établissement
    # privé figure dans les résultats SQL, la nuance est ajoutée systématiquement,
    # que le LLM l'ait fait ou non.
    resultats_bruts = state.get("resultats_sql") or {}
    lignes = resultats_bruts.get("resultats", [])
    au_moins_un_prive = any(row.get("secteur") == "Privé" for row in lignes)

    NUANCE_PRIVE = (
        "\n\n⚠️ Précision importante : ce n'est pas un classement officiel. "
        "Les établissements privés peuvent pratiquer une sélection à l'entrée, "
        "ce qui peut influencer leurs résultats indépendamment de la qualité "
        "pédagogique."
    )
    if au_moins_un_prive and NUANCE_PRIVE.strip() not in reponse:
        reponse += NUANCE_PRIVE

    state["reponse_finale"] = reponse
    return state


def router_vers_chemin(state: AgentState) -> str:
    return state["categorie"]

def router_apres_geo(state: AgentState) -> str:
    """Après geo_tool : succès -> sql_tool, échec -> clarification directe (jamais sql_tool en silence)."""
    if state.get("resultats_geo") and state["resultats_geo"].get("success"):
        return "sql_tool"
    return "clarification_geo"


def construire_graphe():
    graph = StateGraph(AgentState)
    graph.add_node("router", noeud_router)
    graph.add_node("geo_tool", noeud_geo)
    graph.add_node("sql_tool", noeud_sql)
    graph.add_node("rag_tool", noeud_rag)
    graph.add_node("agent_react", noeud_agent_react)
    graph.add_node("clarification_geo", noeud_clarification_geo)
    graph.add_node("synthese", noeud_synthese)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", router_vers_chemin, {
        "recherche_geo_classement": "geo_tool",
        "comparaison_etablissements_nommes": "sql_tool",
        "recherche_geo_comparaison": "geo_tool",
        "question_methodologique": "rag_tool",
        "recherche_geo_methodologique": "geo_tool",
        "non_reconnu": "agent_react",
    })
    graph.add_conditional_edges("geo_tool", router_apres_geo, {
        "sql_tool": "sql_tool",
        "clarification_geo": "clarification_geo",
    })
    graph.add_edge("sql_tool", "synthese")
    graph.add_edge("clarification_geo", END)
    graph.add_edge("rag_tool", "synthese")
    graph.add_edge("agent_react", "synthese")
    graph.add_edge("synthese", END)
    return graph.compile()


if __name__ == "__main__":
    app = construire_graphe()
    resultat = app.invoke({
        "question": "C'est quoi l'IPS ?", "dc_niveau": "accessible",
        "categorie": None, "resultats_geo": None, "resultats_sql": None,
        "resultats_rag": None, "reponse_finale": None, "tours_agent": 0,
    })
    print("Catégorie :", resultat["categorie"])
    print("Réponse :", resultat["reponse_finale"])
