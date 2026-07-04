"""guardrails/llm_output_safety.py — Frontière sortie LLM (JSON) -> code : le LLM produit du texte, pas une donnée de confiance."""


def enum_securise(cls, valeur, defaut):
    """
    Conversion défensive : le LLM renvoie du JSON, pas une donnée de
    confiance. Repli sur `defaut` plutôt que de laisser planter le
    programme si le modèle renvoie une valeur incohérente (observé sur un
    cas limite volontairement difficile — 5 zones géographiques dans une
    seule question — où le LLM a renvoyé le NOM d'un autre champ du schéma
    comme valeur de "categorie").
    """
    try:
        return cls(valeur)
    except ValueError:
        return defaut
