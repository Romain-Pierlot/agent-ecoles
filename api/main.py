"""api/main.py — Couche HTTP minimale au-dessus de l'agent LangGraph existant.

Reste volontairement fine : chaque route orchestre des fonctions qui vivent
ailleurs (graphe.py, sessions.py, graph_router.poser_question) et sont
testables séparément. Aucune règle métier ici.
"""
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from graph_router import AgentState, poser_question
from config import API_CORS_ORIGINS
from api.graphe import obtenir_graphe
from api.sessions import obtenir_ou_creer_session, enregistrer_session
from api.schemas import ChatRequest, ChatResponse
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(requete: ChatRequest) -> ChatResponse:
    graphe = obtenir_graphe()
    etat_session = obtenir_ou_creer_session(requete.session_id)

    debut = time.perf_counter()
    nouvel_etat = poser_question(graphe, etat_session, requete.question)
    latence_ms = int((time.perf_counter() - debut) * 1000)

    enregistrer_session(requete.session_id, nouvel_etat)

    journaliser_echange(
        session_id=requete.session_id,
        question=requete.question,
        reponse=nouvel_etat["reponse_finale"],
        categorie=nouvel_etat.get("categorie"),
        outils_appeles=_deduire_outils_appeles(nouvel_etat),
        latence_ms=latence_ms,
    )

    return ChatResponse(reponse=nouvel_etat["reponse_finale"])
