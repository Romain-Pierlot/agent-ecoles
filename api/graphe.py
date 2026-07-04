"""api/graphe.py — Construction du graphe LangGraph compilé, en singleton.

Séparé du reste de l'API : la couche HTTP (main.py) ne connaît pas les
détails de construction du graphe, elle appelle juste obtenir_graphe().
"""
from graph_router import construire_graphe

_graphe_compile = None


def obtenir_graphe():
    """Retourne le graphe compilé, construit une seule fois par processus."""
    global _graphe_compile
    if _graphe_compile is None:
        _graphe_compile = construire_graphe()
    return _graphe_compile
