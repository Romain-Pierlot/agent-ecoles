"""guardrails/sql_safety.py — Frontière texte/LLM -> SQL exécuté : validation avant exécution."""

import sqlglot
from sqlglot import exp

TABLES_AUTORISEES = {"etablissements", "ips", "ivac", "scores", "referentiel_temporel"}


def valider_sql(sql: str):
    """
    Valide une requête SQL générée par un LLM avant exécution : doit être un
    unique SELECT, portant uniquement sur les tables du schéma connu, sans
    chaînage multi-instructions. Utilise un vrai parseur (sqlglot), pas une
    regex — une regex se contourne par des commentaires SQL, de la casse
    alternée ou des sous-requêtes, un parseur non.

    Retourne (valide: bool, erreur: str|None). En cas d'erreur, le message
    est formulé pour être réinjecté tel quel dans la boucle de retry
    existante de recherche_sql, comme une erreur SQLite classique — le LLM
    a une chance de se corriger dans le même budget de tentatives.
    """
    try:
        statements = [s for s in sqlglot.parse(sql, read="sqlite") if s is not None]
    except Exception as e:
        return False, f"Requête SQL invalide : {e}"

    if len(statements) != 1:
        return False, "Une seule instruction SQL est autorisée par requête (pas de chaînage)."

    statement = statements[0]
    if not isinstance(statement, exp.Select):
        return False, "Seules les requêtes SELECT sont autorisées."

    tables = {t.name.lower() for t in statement.find_all(exp.Table)}
    tables_interdites = tables - TABLES_AUTORISEES
    if tables_interdites:
        mot = "Table" if len(tables_interdites) <= 1 else "Tables"
        accord = "non autorisée" if len(tables_interdites) <= 1 else "non autorisées"
        return False, f"{mot} {accord} : {', '.join(sorted(tables_interdites))}."

    return True, None
