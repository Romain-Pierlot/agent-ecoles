"""api/sessions.py — Mémoire de conversation en mémoire process, par session_id.

Réutilise nouvelle_session()/poser_question() de graph_router.py (S9.1) —
pas de logique de session réécrite ici, juste le rangement par session_id.
Volatile (perdu au redémarrage du processus) : accepté pour un usage local
mono-utilisateur, à revoir si l'API tourne un jour sur plusieurs instances.
"""
from graph_router import AgentState, nouvelle_session

_sessions: dict[str, AgentState] = {}


def obtenir_ou_creer_session(session_id: str) -> AgentState:
    if session_id not in _sessions:
        _sessions[session_id] = nouvelle_session()
    return _sessions[session_id]


def enregistrer_session(session_id: str, etat: AgentState) -> None:
    _sessions[session_id] = etat
