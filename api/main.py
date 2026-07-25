"""api/main.py — Couche HTTP minimale au-dessus de l'agent LangGraph existant.

Reste volontairement fine : chaque route orchestre des fonctions qui vivent
ailleurs (graphe.py, sessions.py, graph_router.poser_question) et sont
testables séparément. Aucune règle métier ici.
"""
import time
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from graph_router import AgentState, poser_question, poser_resolution_choix
from config import API_CORS_ORIGINS, SEUIL_CANDIDATS_AVANT_PRECISION, SPLIT_SECTEUR_INCREMENT
from api.graphe import obtenir_graphe
from api.sessions import obtenir_ou_creer_session, enregistrer_session
from api.schemas import (
    ChatRequest, ChatResponse, Choix, FicheEtablissement,
    NationalHub, RegionHub, DepartementHub, VilleHub, RechercheResultats,
    SecteurResultats, SuggestionsAdresseResultats, RechercheLogRequest,
)
from api.journalisation import journaliser_echange, journaliser_recherche
from agent.tools.etablissement_tool import obtenir_fiche_etablissement
from agent.tools.hierarchie_tool import (
    resoudre_region_par_slug,
    resoudre_departement_par_slug,
    resoudre_ville_par_slug,
    agreger_sous_divisions,
    obtenir_colleges_ville,
    obtenir_top_etablissements_zone,
)
from agent.tools.recherche_tool import rechercher, LIMITE_RESULTATS
from agent.tools.carte_scolaire_tool import resoudre_secteur
from agent.tools.geo_tool import geocoder_suggestions

app = FastAPI(title="agent-ecoles API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _deduire_outils_appeles(etat: AgentState) -> list[str]:
    """Outils dont l'appel a produit un résultat non vide sur ce tour."""
    correspondance = {
        "geo_tool": etat.get("resultats_geo"),
        "sql_tool": etat.get("resultats_sql"),
        "rag_tool": etat.get("resultats_rag"),
    }
    return [nom for nom, resultat in correspondance.items() if resultat]


def _construire_choix(etat: AgentState) -> Choix | None:
    """
    Traduit une clarification ambiguë en attente (zone géo ou noms
    d'établissements, cf. graph_router S11.2) en choix structurés
    cliquables. None si aucune clarification n'est en attente, ou si le
    nombre de candidats dépasse le seuil (dans ce cas, le texte de
    reponse_finale demande déjà de préciser en texte libre plutôt que
    d'afficher une liste trop longue de boutons).
    """
    resultats_sql = etat.get("resultats_sql") or {}
    if resultats_sql.get("split_secteur"):
        options = []
        for secteur, libelle in (("public", "publics"), ("prive", "privés")):
            cache = etat.get(f"cache_secteur_{secteur}") or []
            n_affiches = etat.get(f"n_affiches_{secteur}") or 0
            if n_affiches < len(cache):
                nb_de_plus = min(SPLIT_SECTEUR_INCREMENT, len(cache) - n_affiches)
                options.append({
                    "label": f"Voir {nb_de_plus} établissements {libelle} de plus",
                    "valeur": {"secteur": secteur},
                })
        if options:
            return Choix(type="voir_plus", groupes=[{"titre": "Voir plus", "options": options}])

    candidats_zone = etat.get("candidats_zone_geo")
    if candidats_zone:
        if len(candidats_zone) > SEUIL_CANDIDATS_AVANT_PRECISION:
            return None
        return Choix(
            type="zone",
            groupes=[{
                "titre": etat.get("zone_geo") or "",
                "options": [
                    {
                        "label": f"{c['commune']} ({c['code_departement']})",
                        "valeur": {"commune": c["commune"], "code_departement": c["code_departement"]},
                    }
                    for c in candidats_zone
                ],
            }],
        )

    candidats_par_nom = (etat.get("resolution_noms") or {}).get("resultats", {})
    groupes = [
        {
            "titre": nom,
            "options": [
                {
                    "label": f"{c['nom']} — {c['commune']} ({c['secteur']})",
                    "valeur": {"nom": nom, "uai": c["uai"]},
                }
                for c in candidats
            ],
        }
        for nom, candidats in candidats_par_nom.items()
        if 1 < len(candidats) <= SEUIL_CANDIDATS_AVANT_PRECISION
    ]
    return Choix(type="noms", groupes=groupes) if groupes else None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/etablissement/{uai}", response_model=FicheEtablissement)
def obtenir_etablissement(uai: str):
    resultat = obtenir_fiche_etablissement(uai)
    if not resultat["success"]:
        raise HTTPException(status_code=500, detail=resultat["error"])
    if resultat["fiche"] is None:
        raise HTTPException(status_code=404, detail=f"Établissement {uai} introuvable")
    return resultat["fiche"]


@app.get("/region", response_model=NationalHub)
def obtenir_national():
    agregat = agreger_sous_divisions("national")
    if not agregat["success"]:
        raise HTTPException(status_code=500, detail=agregat["error"])

    return NationalHub(
        session_utilisee=agregat["session_utilisee"],
        global_=agregat["global"],
        regions=agregat["sous_divisions"],
    )


@app.get("/region/{region_slug}", response_model=RegionHub)
def obtenir_region(region_slug: str):
    region = resoudre_region_par_slug(region_slug)
    if region is None:
        raise HTTPException(status_code=404, detail=f"Région introuvable : {region_slug}")

    agregat = agreger_sous_divisions("region", region["libelle_region"])
    if not agregat["success"]:
        raise HTTPException(status_code=500, detail=agregat["error"])

    top = obtenir_top_etablissements_zone("region", region["libelle_region"])
    if not top["success"]:
        raise HTTPException(status_code=500, detail=top["error"])

    return RegionHub(
        libelle_region=region["libelle_region"],
        session_utilisee=agregat["session_utilisee"],
        global_=agregat["global"],
        departements=agregat["sous_divisions"],
        top_notation=top["top_notation"],
        top_va=top["top_va"],
    )


@app.get("/region/{region_slug}/departement/{dept_slug}", response_model=DepartementHub)
def obtenir_departement(region_slug: str, dept_slug: str):
    region = resoudre_region_par_slug(region_slug)
    if region is None:
        raise HTTPException(status_code=404, detail=f"Région introuvable : {region_slug}")

    departement = resoudre_departement_par_slug(dept_slug, region["libelle_region"])
    if departement is None:
        raise HTTPException(status_code=404, detail=f"Département introuvable : {dept_slug}")

    agregat = agreger_sous_divisions("departement", departement["code_departement"])
    if not agregat["success"]:
        raise HTTPException(status_code=500, detail=agregat["error"])

    top = obtenir_top_etablissements_zone("departement", departement["code_departement"])
    if not top["success"]:
        raise HTTPException(status_code=500, detail=top["error"])

    return DepartementHub(
        libelle_region=region["libelle_region"],
        code_departement=departement["code_departement"],
        libelle_departement=departement["libelle_departement"],
        session_utilisee=agregat["session_utilisee"],
        global_=agregat["global"],
        communes=agregat["sous_divisions"],
        top_notation=top["top_notation"],
        top_va=top["top_va"],
    )


@app.get("/region/{region_slug}/departement/{dept_slug}/ville/{ville_slug}", response_model=VilleHub)
def obtenir_ville(region_slug: str, dept_slug: str, ville_slug: str):
    region = resoudre_region_par_slug(region_slug)
    if region is None:
        raise HTTPException(status_code=404, detail=f"Région introuvable : {region_slug}")

    departement = resoudre_departement_par_slug(dept_slug, region["libelle_region"])
    if departement is None:
        raise HTTPException(status_code=404, detail=f"Département introuvable : {dept_slug}")

    ville = resoudre_ville_par_slug(ville_slug, departement["code_departement"])
    if ville is None:
        raise HTTPException(status_code=404, detail=f"Ville introuvable : {ville_slug}")

    resultat = obtenir_colleges_ville(ville["commune"], departement["code_departement"])
    if not resultat["success"]:
        raise HTTPException(status_code=500, detail=resultat["error"])

    return VilleHub(
        libelle_region=region["libelle_region"],
        code_departement=departement["code_departement"],
        libelle_departement=departement["libelle_departement"],
        commune=ville["commune"],
        session_utilisee=resultat["session_utilisee"],
        global_=resultat["global"],
        nb_publics=resultat["nb_publics"],
        nb_prives=resultat["nb_prives"],
        taux_reussite_national=resultat["taux_reussite_national"],
        colleges=resultat["colleges"],
    )


@app.get("/recherche", response_model=RechercheResultats)
def obtenir_recherche(
    q: str = "",
    limite: int = Query(LIMITE_RESULTATS, ge=1, le=LIMITE_RESULTATS),
    # Filtres et tri : établissements uniquement (les communes sont des
    # agrégats sans secteur/dispositif/section/notation individuels, cf.
    # agent/tools/recherche_tool.py::rechercher). Literal ici pour un 422
    # automatique sur une valeur hors liste — recherche_tool.py revalide
    # quand même contre les mêmes listes blanches (config.py), cette
    # fonction restant appelable en dehors de l'API.
    secteur: Optional[Literal["Public", "Privé"]] = None,
    dispositif: Optional[Literal["REP", "REP+", "ULIS", "SEGPA"]] = None,
    section: Optional[Literal["sport", "arts", "cinema", "theatre", "internationale", "europeenne"]] = None,
    notation_min: Optional[Literal["A+", "A", "A-", "B+", "B"]] = None,
    tri: Literal["notation", "reussite", "alphabetique"] = "alphabetique",
    direction: Literal["asc", "desc"] = "asc",
    tri_communes: Literal["alphabetique", "reussite", "nb_etablissements"] = "alphabetique",
    direction_communes: Literal["asc", "desc"] = "asc",
):
    resultat = rechercher(
        q, limite=limite, secteur=secteur, dispositif=dispositif,
        section=section, notation_min=notation_min, tri=tri, direction=direction,
        tri_communes=tri_communes, direction_communes=direction_communes,
    )
    if not resultat["success"]:
        raise HTTPException(status_code=500, detail=resultat["error"])

    return RechercheResultats(
        query=q,
        session_utilisee=resultat["session_utilisee"],
        taux_reussite_national=resultat["taux_reussite_national"],
        etablissements=resultat["etablissements"],
        communes=resultat["communes"],
        etablissements_total=resultat["etablissements_total"],
        communes_total=resultat["communes_total"],
        etablissements_tronques=resultat["etablissements_tronques"],
        communes_tronquees=resultat["communes_tronquees"],
    )


@app.post("/recherche/log", status_code=204)
def journaliser_recherche_route(requete: RechercheLogRequest) -> None:
    journaliser_recherche(
        page_origine="recherche",
        terme=requete.terme,
        nb_etablissements=requete.nb_etablissements,
        nb_communes=requete.nb_communes,
    )


@app.get("/secteur/adresses", response_model=SuggestionsAdresseResultats)
def obtenir_suggestions_adresse(q: str = ""):
    resultat = geocoder_suggestions(q)
    if not resultat["success"]:
        raise HTTPException(status_code=500, detail=resultat["error"])
    return SuggestionsAdresseResultats(suggestions=resultat["suggestions"])


@app.get("/secteur", response_model=SecteurResultats)
def obtenir_secteur(adresse: str = Query(..., min_length=1)):
    resultat = resoudre_secteur(adresse)
    # "adresse_non_reconnue" est un résultat normal et attendu (échec du
    # géocodage BAN, ~pas rare), pas une panne — 200 OK avec cet état,
    # jamais une HTTPException. success=False est réservé aux vraies pannes
    # techniques (ex: base SQLite inaccessible), cf. carte_scolaire_tool.py.
    if not resultat["success"]:
        raise HTTPException(status_code=500, detail=resultat["error"])

    # Une seule résolution par navigation réelle sur /carte-scolaire (page
    # serveur Next.js, pas de re-fetch client comme sur /recherche) — bon
    # point pour journaliser sans compter plusieurs fois la même recherche.
    journaliser_recherche(
        page_origine="carte_scolaire",
        commune=resultat.get("commune"),
        code_departement=resultat.get("code_departement"),
        etat_carte_scolaire=resultat["etat"],
    )

    return SecteurResultats(
        adresse_recherchee=adresse,
        etat=resultat["etat"],
        adresse_normalisee=resultat["adresse_normalisee"],
        latitude=resultat["latitude"],
        longitude=resultat["longitude"],
        academie=resultat.get("academie"),
        colleges_secteur=resultat["colleges_secteur"],
        colleges_alentours=resultat["colleges_alentours"],
        suggestions_ambigues=resultat.get("suggestions_ambigues", []),
    )


@app.post("/chat", response_model=ChatResponse)
def chat(requete: ChatRequest) -> ChatResponse:
    graphe = obtenir_graphe()
    etat_session = obtenir_ou_creer_session(requete.session_id)

    debut = time.perf_counter()
    if requete.resolution is not None:
        # Choix cliqué sur une clarification précédente (S11.2) : aucune
        # interprétation de texte libre à faire, ne passe jamais par le
        # graphe LangGraph/noeud_router (cf. poser_resolution_choix).
        nouvel_etat = poser_resolution_choix(etat_session, requete.resolution)
        question_journalisee = requete.question or str(requete.resolution)
    else:
        nouvel_etat = poser_question(graphe, etat_session, requete.question)
        question_journalisee = requete.question
    latence_ms = int((time.perf_counter() - debut) * 1000)

    enregistrer_session(requete.session_id, nouvel_etat)

    journaliser_echange(
        session_id=requete.session_id,
        question=question_journalisee,
        reponse=nouvel_etat["reponse_finale"],
        categorie=nouvel_etat.get("categorie"),
        outils_appeles=_deduire_outils_appeles(nouvel_etat),
        latence_ms=latence_ms,
    )

    return ChatResponse(reponse=nouvel_etat["reponse_finale"], choix=_construire_choix(nouvel_etat))
