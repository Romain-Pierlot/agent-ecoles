"""guardrails/resource_limits.py — Limites de ressources avant tout appel LLM coûteux."""

from config import MAX_ZONES_COMPAREES


def verifier_limite_zones(zone_geo):
    """
    Refuse une comparaison portant sur plus de MAX_ZONES_COMPAREES zones
    géographiques avant de lancer l'agent ReAct — au-delà, l'agent devient
    trop lent/coûteux (timeout mesuré à 5 zones, ~96s avant échec, cf.
    session 8). Bloqué en amont plutôt que de laisser l'agent essayer et
    échouer après une longue attente.

    Retourne (autorise: bool, message_refus: str|None).
    """
    nb_zones = len(zone_geo.split(",")) if zone_geo else 0
    if nb_zones > MAX_ZONES_COMPAREES:
        message = (
            f"Je peux comparer jusqu'à {MAX_ZONES_COMPAREES} zones géographiques à la fois "
            f"(villes, départements...). Peux-tu reformuler ta question avec "
            f"{MAX_ZONES_COMPAREES} zones maximum ?"
        )
        return False, message
    return True, None
