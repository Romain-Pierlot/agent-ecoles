"""guardrails/input_limits.py — Frontière entrée : plafond de longueur avant tout appel LLM."""

MAX_CARACTERES_QUESTION = 400


def verifier_longueur_question(question):
    """
    Refuse une question dépassant MAX_CARACTERES_QUESTION avant tout appel
    LLM — évite qu'un pavé de texte ("résume-moi ce texte : ...") soit
    traité comme une question sur le choix de collège. Seuil calibré sur la
    longueur réelle des questions du golden dataset et des tests existants
    (max observé ~80 caractères), avec une marge large (~5x) pour ne
    jamais rejeter une vraie question composée.

    Retourne (autorise: bool, message_refus: str|None).
    """
    if len(question) > MAX_CARACTERES_QUESTION:
        message = (
            f"Votre question est trop longue ({len(question)} caractères, "
            f"{MAX_CARACTERES_QUESTION} maximum). Pouvez-vous la reformuler en quelques phrases ?"
        )
        return False, message
    return True, None
