"""
test_guardrails_phase_a.py — Tests unitaires des guardrails migrés en Phase A
(cf. docs/guardrails_criteres_acceptance.md, A1/A2/A3). Aucun appel LLM/API :
ce sont des fonctions pures, testables isolément.
"""

from config import Categorie
from guardrails.llm_output_safety import enum_securise
from guardrails.resource_limits import verifier_limite_zones
from guardrails.output_contracts import verifier_transparence_temporelle

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


# --- A1 : enum_securise ---
test(
    "A1 valeur incohérente -> repli sur le défaut, pas d'exception",
    enum_securise(Categorie, "je_ne_sais_pas", Categorie.NON_RECONNU) == Categorie.NON_RECONNU,
)
test(
    "A1 cas limite : valeur valide -> jamais altérée",
    enum_securise(Categorie, "question_methodologique", Categorie.NON_RECONNU) == Categorie.QUESTION_METHODOLOGIQUE,
)

# --- A2 : verifier_limite_zones ---
autorise_4, message_4 = verifier_limite_zones("Lyon,Marseille,Nantes,Bordeaux")
test("A2 4 zones -> refusé avec message", autorise_4 is False and message_4 is not None)

autorise_3, message_3 = verifier_limite_zones("Lyon,Marseille,Nantes")
test("A2 cas limite : exactement 3 zones (la limite) -> autorisé", autorise_3 is True and message_3 is None)

autorise_none, message_none = verifier_limite_zones(None)
test("A2 pas de zone -> autorisé", autorise_none is True and message_none is None)

# --- A3 : verifier_transparence_temporelle ---
leve_exception = False
try:
    verifier_transparence_temporelle({"success": True, "resultats": []})
except AssertionError:
    leve_exception = True
test("A3 champ manquant -> AssertionError levée", leve_exception)

ne_leve_pas = True
try:
    verifier_transparence_temporelle({"success": True, "session_utilisee": "2025"})
except AssertionError:
    ne_leve_pas = False
test("A3 cas limite : champ présent -> ne lève rien", ne_leve_pas)


def tester():
    print("=== TEST GUARDRAILS PHASE A ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
