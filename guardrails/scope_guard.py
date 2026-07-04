"""guardrails/scope_guard.py — Frontière entrée -> agent : refus dur du hors-sujet, sans signal exploitable."""

from config import Categorie, OrdreSouhaite

MESSAGE_HORS_SUJET = (
    "Je réponds uniquement aux questions sur le choix d'un collège en France, à "
    "partir des données IPS/IVAC officielles (recherche par zone géographique, "
    "comparaison d'établissements nommés, questions méthodologiques). Peux-tu "
    "reformuler ta question dans ce cadre ?"
)


def question_hors_sujet(state: dict) -> bool:
    """
    Vrai si la catégorie est non_reconnu ET qu'aucun signal exploitable n'a
    été extrait par le router (zone, noms d'établissements, nuance
    méthodologique, tri souhaité, agrégation, évolution).

    Distingue une question vraiment hors-sujet (conseil personnalisé, hors
    périmètre géographique, tentative d'injection...) d'une question
    complexe mais légitime (ex: comparaison multi-zones combinée à une
    question méthodologique) — cette dernière garde au moins un signal, et
    doit continuer vers l'agent ReAct comme avant, pas être refusée.
    """
    if state.get("categorie") != Categorie.NON_RECONNU:
        return False
    return not any([
        state.get("zone_geo"),
        state.get("noms_etablissements"),
        state.get("nuance_methodologique_demandee"),
        state.get("ordre_souhaite") not in (None, OrdreSouhaite.INDIFFERENT),
        state.get("agregation_demandee"),
        state.get("evolution_demandee"),
    ])
