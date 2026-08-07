"""
test_input_limits.py — Vérifie guardrails/input_limits.py (B1). Fonction
pure, aucun appel LLM/API.
"""

from guardrails.input_limits import verifier_longueur_question, MAX_CARACTERES_QUESTION

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


autorise_courte, message_courte = verifier_longueur_question("Meilleurs collèges à Lyon ?")
test("question normale -> autorisée", autorise_courte is True and message_courte is None)

question_limite = "a" * MAX_CARACTERES_QUESTION
autorise_limite, message_limite = verifier_longueur_question(question_limite)
test("cas limite : exactement le plafond -> autorisée", autorise_limite is True and message_limite is None)

question_trop_longue = "a" * (MAX_CARACTERES_QUESTION + 1)
autorise_trop_longue, message_trop_longue = verifier_longueur_question(question_trop_longue)
test("un caractère au-delà du plafond -> refusée avec message", autorise_trop_longue is False and message_trop_longue is not None)

question_pave = "Résume-moi ce texte : " + "lorem ipsum " * 100
autorise_pave, _ = verifier_longueur_question(question_pave)
test("pavé de texte à résumer -> refusé", autorise_pave is False)


def tester():
    print("=== TEST INPUT LIMITS (B1) ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
