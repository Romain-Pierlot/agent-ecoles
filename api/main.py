"""api/main.py — Couche HTTP minimale au-dessus de l'agent LangGraph existant.

Reste volontairement fine : chaque route orchestre des fonctions qui vivent
ailleurs (graphe.py, sessions.py, graph_router.poser_question) et sont
testables séparément. Aucune règle métier ici.
"""
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from graph_router import AgentState, poser_question, poser_resolution_choix
from config import API_CORS_ORIGINS, SEUIL_CANDIDATS_AVANT_PRECISION, SPLIT_SECTEUR_INCREMENT
from api.graphe import obtenir_graphe
from api.sessions import obtenir_ou_creer_session, enregistrer_session
from api.schemas import ChatRequest, ChatResponse, Choix
from api.journalisation import journaliser_echange

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
