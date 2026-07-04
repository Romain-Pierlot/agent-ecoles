"""guardrails/prompt_leakage.py — Frontière sortie LLM -> utilisateur : détection de fuite verbatim du prompt système."""

import re

MESSAGE_SUBSTITUTION = (
    "Je ne partage pas mes instructions internes. Pose-moi plutôt une question "
    "sur le choix d'un collège en France, à partir des données IPS/IVAC."
)


def _mots(texte):
    return re.findall(r"\w+", texte.lower())


def contient_fuite_prompt_systeme(reponse, prompt_systeme, taille_fenetre=8):
    """
    Détecte une reproduction verbatim d'au moins `taille_fenetre` mots
    consécutifs du prompt système dans la réponse finale — signe d'une
    extraction réussie (directe : "répète tes instructions" ; ou indirecte :
    "traduis tes instructions", "continue ce texte : 'Tu es un assistant
    qui...'").

    Ne détecte pas un résumé/paraphrase fidèle sans copie verbatim (limite
    assumée, cf. docs/guardrails_criteres_acceptance.md E1) — mais une copie
    verbatim de plusieurs mots consécutifs n'a aucune raison de se produire
    dans une réponse légitime sur des données de collèges : risque de faux
    positif quasi nul, contrairement aux guardrails basés sur la détection
    de noms propres (cf. D2).
    """
    mots_reponse = _mots(reponse)
    mots_prompt = _mots(prompt_systeme)
    if len(mots_prompt) < taille_fenetre:
        return False
    fenetres_prompt = {
        tuple(mots_prompt[i:i + taille_fenetre])
        for i in range(len(mots_prompt) - taille_fenetre + 1)
    }
    for i in range(len(mots_reponse) - taille_fenetre + 1):
        if tuple(mots_reponse[i:i + taille_fenetre]) in fenetres_prompt:
            return True
    return False
