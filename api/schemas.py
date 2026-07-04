"""api/schemas.py — Contrats de données de l'API (requêtes/réponses HTTP)."""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    reponse: str
