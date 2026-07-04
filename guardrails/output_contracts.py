"""guardrails/output_contracts.py — Contrats internes outil -> couche d'affichage."""


def verifier_transparence_temporelle(resultats_sql):
    """
    Tout résultat SQL réussi doit indiquer sur quelle période il porte
    (session_utilisee ou sessions_disponibles, même à None/vide) — sinon
    l'utilisateur ne peut pas savoir de quand datent les données affichées.
    Échec bruyant et immédiat (AssertionError) plutôt qu'un trou de
    transparence silencieux (cf. S8.25).
    """
    assert "session_utilisee" in resultats_sql or "sessions_disponibles" in resultats_sql, (
        "resultats_sql (success=True) ne contient ni session_utilisee ni "
        "sessions_disponibles — l'utilisateur ne pourrait pas savoir de "
        "quand datent les données affichées. Toute fonction de recherche "
        "doit inclure l'un des deux, même à None/vide (cf. S8.25)."
    )
