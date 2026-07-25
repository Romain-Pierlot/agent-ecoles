"""guardrails/output_vocabulary.py — Frontière sortie -> utilisateur : vocabulaire d'implémentation interdit."""

import re
import unicodedata

# Même liste que l'instruction déjà posée dans SYNTHESE_SYSTEM_PROMPT
# (graph_router.py) — ce guardrail la vérifie enfin en code, plutôt que de
# ne dépendre que du LLM pour la respecter.
MOTS_INTERDITS = ["sql", "base de donnees", "requete", "outil", "backend"]

MESSAGE_SUBSTITUTION = (
    "Je ne peux pas formuler cette partie de la réponse correctement. "
    "Précisez votre question si vous voulez une explication méthodologique."
)


def _normaliser(texte):
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return texte.lower()


def contient_vocabulaire_interdit(texte):
    """
    Détecte un mot de vocabulaire d'implémentation (SQL, base de données,
    requête, outil, backend...) dans un texte destiné à l'utilisateur
    final — filet dur en plus de l'instruction déjà posée dans
    SYNTHESE_SYSTEM_PROMPT, jamais vérifiée en code jusqu'ici.

    Limite structurelle assumée (cf. docs/guardrails_criteres_acceptance.md
    E2) : une liste de mots interdits se contourne toujours (synonymes,
    autre langue, espacement) — sert de filet contre l'oubli du LLM, pas
    une garantie absolue face à un contournement délibéré.
    """
    texte_normalise = _normaliser(texte)
    return any(re.search(rf"\b{re.escape(mot)}\b", texte_normalise) for mot in MOTS_INTERDITS)
