"""
test_output_vocabulary.py — Vérifie guardrails/output_vocabulary.py (E2).
Fonction pure, aucun appel LLM/API.
"""

from guardrails.output_vocabulary import contient_vocabulaire_interdit

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


test(
    "mention de la base de données -> détecté",
    contient_vocabulaire_interdit("D'après la base de données, ce collège..."),
)
test(
    "mention de SQL -> détecté",
    contient_vocabulaire_interdit("La requête SQL retourne 3 résultats."),
)
test(
    "mention de backend -> détecté",
    contient_vocabulaire_interdit("Le backend a calculé ce score."),
)
test(
    "réponse normale sur les données disponibles -> pas détecté",
    not contient_vocabulaire_interdit("D'après les données disponibles, ce collège a un bon score."),
)
test(
    "réponse légitime déjà générée ce soir (Lyon/Marseille/Nantes) -> pas détecté",
    not contient_vocabulaire_interdit(
        "Voici une comparaison des collèges de Lyon, Marseille et Nantes, basée sur les scores moyens."
    ),
)
test(
    "explication méthodologique légitime (VA) -> pas détecté",
    not contient_vocabulaire_interdit(
        "La valeur ajoutée compare les résultats réels de l'établissement à ceux attendus."
    ),
)


def tester():
    print("=== TEST OUTPUT VOCABULARY (E2) ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
