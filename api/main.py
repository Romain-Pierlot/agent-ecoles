"""api/main.py — Couche HTTP minimale au-dessus de l'agent LangGraph existant.

Reste volontairement fine : chaque route orchestre des fonctions qui vivent
ailleurs (graphe.py, sessions.py, graph_router.poser_question) et sont
testables séparément. Aucune règle métier ici.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from graph_router import poser_question
from config import API_CORS_ORIGINS
from api.graphe import obtenir_graphe
from api.sessions import obtenir_ou_creer_session, enregistrer_session
from api.schemas import ChatRequest, ChatResponse

app = FastAPI(title="agent-ecoles API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(requete: ChatRequest) -> ChatResponse:
    graphe = obtenir_graphe()
    etat_session = obtenir_ou_creer_session(requete.session_id)
    nouvel_etat = poser_question(graphe, etat_session, requete.question)
    enregistrer_session(requete.session_id, nouvel_etat)
    return ChatResponse(reponse=nouvel_etat["reponse_finale"])
