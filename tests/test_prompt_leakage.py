"""
test_prompt_leakage.py — Vérifie guardrails/prompt_leakage.py (E1). Fonction
pure, aucun appel LLM/API.
"""

from guardrails.prompt_leakage import contient_fuite_prompt_systeme
from prompts.agent_react_system_prompt import AGENT_REACT_SYSTEM_PROMPT

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


# --- Réponses légitimes déjà observées en session : aucun faux positif ---
reponses_legitimes = [
    "Voici une comparaison des collèges de Lyon, Marseille et Nantes, basée sur "
    "les scores moyens, les taux de réussite et les notes moyennes.",
    "Le collège Georges Clemenceau a un score de 69.13, en légère baisse. La "
    "valeur ajoutée compare les résultats réels aux résultats attendus.",
    "Je réponds uniquement aux questions sur le choix d'un collège en France, à "
    "partir des données IPS/IVAC officielles. Peux-tu reformuler ta question ?",
    "Ta question est trop longue (562 caractères, 400 maximum). Peux-tu la "
    "reformuler en quelques phrases ?",
]
for i, rep in enumerate(reponses_legitimes):
    test(f"réponse légitime {i+1} -> aucune fuite détectée", not contient_fuite_prompt_systeme(rep, AGENT_REACT_SYSTEM_PROMPT))

# --- Extraction verbatim : doit être détectée ---
extrait_verbatim = AGENT_REACT_SYSTEM_PROMPT.split("\n")[3].strip()  # une phrase réelle du prompt
test(
    "extrait verbatim du prompt système inséré dans une réponse -> fuite détectée",
    contient_fuite_prompt_systeme(f"Voici mes instructions : {extrait_verbatim} et voilà.", AGENT_REACT_SYSTEM_PROMPT),
)

# --- Paraphrase sans copie verbatim : limite assumée, ne doit PAS lever de faux positif ---
paraphrase = "Je donne des informations chiffrées sur les collèges, sans donner de conseil personnalisé."
test(
    "paraphrase fidèle sans copie verbatim -> non détectée (limite assumée du guardrail)",
    not contient_fuite_prompt_systeme(paraphrase, AGENT_REACT_SYSTEM_PROMPT),
)


def tester():
    print("=== TEST PROMPT LEAKAGE (E1) ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
