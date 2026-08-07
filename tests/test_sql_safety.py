"""
test_sql_safety.py — Vérifie guardrails/sql_safety.py (D3) : validateur de
requête + connexion en lecture seule. Deux filets testés indépendamment.
"""

import sqlite3
from guardrails.sql_safety import valider_sql
from agent.tools.sql_tool import executer_sql
from config import DB_PATH

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


# --- Validateur : requêtes légitimes ---
valide, erreur = valider_sql("SELECT nom, commune FROM etablissements WHERE commune = 'Lyon'")
test("SELECT simple légitime -> valide", valide is True and erreur is None)

valide, erreur = valider_sql(
    "SELECT e.nom, s.score FROM etablissements e JOIN scores s ON e.uai = s.uai WHERE e.commune = 'Nantes'"
)
test("SELECT avec JOIN sur tables autorisées -> valide", valide is True and erreur is None)

# --- Validateur : tentatives d'attaque ---
valide, erreur = valider_sql("DROP TABLE etablissements;")
test("DROP TABLE -> rejeté (pas un SELECT)", valide is False)

valide, erreur = valider_sql("DELETE FROM etablissements WHERE 1=1;")
test("DELETE -> rejeté (pas un SELECT)", valide is False)

valide, erreur = valider_sql("SELECT * FROM etablissements; DELETE FROM etablissements;")
test("SELECT puis DELETE (chaînage) -> rejeté", valide is False)

valide, erreur = valider_sql("SELECT * FROM sqlite_master")
test("Table hors périmètre (sqlite_master) -> rejeté", valide is False)

valide, erreur = valider_sql("SELECT * FROM etablissements /* commentaire */; DROP TABLE etablissements;")
test("Chaînage caché par un commentaire SQL -> toujours rejeté (vrai parseur, pas une regex)", valide is False)

valide, erreur = valider_sql("ceci n'est pas du SQL du tout")
test("texte non-SQL -> rejeté proprement (pas d'exception qui remonte)", valide is False)

# --- Connexion en lecture seule : filet indépendant du validateur ---
# On appelle executer_sql() DIRECTEMENT (en contournant le validateur) pour
# vérifier que le filet tient même si le validateur avait un trou.
try:
    executer_sql("DELETE FROM etablissements WHERE uai = 'INEXISTANT'")
    ecriture_bloquee = False
except sqlite3.OperationalError:
    ecriture_bloquee = True
test("Connexion en lecture seule : DELETE direct (validateur contourné) -> bloqué par SQLite", ecriture_bloquee)

# Vérifie que la lecture, elle, fonctionne toujours normalement
resultats = executer_sql("SELECT COUNT(*) as n FROM etablissements")
test("Lecture toujours fonctionnelle malgré le mode lecture seule", resultats[0]["n"] > 0)


def tester():
    print("=== TEST SQL SAFETY (D3) ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
