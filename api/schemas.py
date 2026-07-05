"""api/schemas.py — Contrats de données de l'API (requêtes/réponses HTTP)."""
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    question: str = ""
    # Choix cliqué en réponse à une clarification structurée précédente
    # (cf. graph_router.poser_resolution_choix) — présent seulement quand
    # l'utilisateur clique un bouton plutôt que de taper une question.
    # {"type": "zone", "commune": str, "code_departement": str}
    # {"type": "noms", "choix": {nom: uai, ...}}
    resolution: Optional[dict] = None


class OptionChoix(BaseModel):
    label: str
    valeur: dict


class GroupeChoix(BaseModel):
    titre: str
    options: list[OptionChoix]


class Choix(BaseModel):
    type: str  # "zone" ou "noms"
    groupes: list[GroupeChoix]


class ChatResponse(BaseModel):
    reponse: str
    # Présent seulement quand une clarification ambiguë (zone ou noms
    # d'établissements) attend un choix cliquable — cf. docs/fiches/
    # (désambiguïsation par boutons, S11.2). Absent sinon.
    choix: Optional[Choix] = None
