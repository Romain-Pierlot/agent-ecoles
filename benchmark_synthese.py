"""
benchmark_synthese.py — Compare la latence de gpt-4o-mini, claude-haiku-4-5
et gemini-2.5-flash sur le même prompt de synthèse et les mêmes données réelles
(cas Lyon déjà testé), 5 essais par modèle.
"""

import os
import time
import json
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from openai import OpenAI
import anthropic
from google import genai

NB_ESSAIS = 5

SYNTHESE_SYSTEM_PROMPT = """
Tu rédiges la réponse finale à partir des résultats des outils déjà exécutés.

Règles impératives :
- Les données SQL sont la source de vérité pour tout chiffre. Ne jamais laisser
  une nuance RAG contredire un chiffre SQL.
- Les chunks RAG servent à contextualiser/nuancer, jamais à corriger un chiffre.
  Cite les deux sources séparément.
- Si aucun résultat pertinent n'est disponible, explique-le plutôt que d'inventer.
- Un classement, si présenté, doit être nuancé : pas un classement officiel,
  sélection possible à l'entrée dans le privé.
- Adapte le niveau de langage à dc_niveau.

Règles anti-hallucination (strictes) :
- N'ajoute JAMAIS de conseil, recommandation ou généralité qui ne provient pas
  directement des données fournies.
- Ne dis jamais "scores scolaires" : nomme précisément les critères utilisés.
- Ne confonds jamais les nombres d'établissements de resultats_geo et resultats_sql.

Règles de structure et de langage (strictes) :
- N'utilise JAMAIS de termes techniques d'implémentation (SQL, base de données, requête).
- Ne crée JAMAIS de section séparée listant des établissements géolocalisés à part.
- Une seule liste classée, issue de resultats_sql.

Règles de format :
- Utilise TOUJOURS un tableau markdown compact. Colonnes : Nom, Secteur, Score,
  Taux de réussite, VA (badge), Note écrit.
- Si VA présente, termine par une explication courte de ce qu'elle représente.
"""

# Contexte réel du test Lyon, tronqué à 15 lignes SQL + geo résumé (même volume qu'en prod)
with open("contexte_benchmark_lyon.json", "r") as f:
    CONTEXTE_USER = f.read()


def appel_openai():
    client = OpenAI()
    debut = time.time()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYNTHESE_SYSTEM_PROMPT},
            {"role": "user", "content": CONTEXTE_USER},
        ],
        timeout=30,
    )
    duree = time.time() - debut
    tokens = response.usage.completion_tokens
    return duree, tokens


def appel_anthropic():
    client = anthropic.Anthropic()
    debut = time.time()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        system=SYNTHESE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": CONTEXTE_USER}],
    )
    duree = time.time() - debut
    tokens = response.usage.output_tokens
    return duree, tokens


def appel_gemini():
    client = genai.Client()
    debut = time.time()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=CONTEXTE_USER,
        config={"system_instruction": SYNTHESE_SYSTEM_PROMPT},
    )
    duree = time.time() - debut
    tokens = response.usage_metadata.candidates_token_count
    return duree, tokens


def benchmark(nom, fonction_appel):
    print(f"\n=== {nom} ===")
    durees = []
    for i in range(1, NB_ESSAIS + 1):
        try:
            duree, tokens = fonction_appel()
            durees.append(duree)
            print(f"  Essai {i}: {duree:.2f}s ({tokens} tokens de sortie)")
        except Exception as e:
            print(f"  Essai {i}: ÉCHEC — {e}")
    if durees:
        print(f"  → Moyenne: {sum(durees)/len(durees):.2f}s | Min: {min(durees):.2f}s | Max: {max(durees):.2f}s")
    return durees


if __name__ == "__main__":
    resultats = {}
    resultats["gpt-4o-mini"] = benchmark("OpenAI gpt-4o-mini", appel_openai)
    resultats["claude-haiku-4-5"] = benchmark("Anthropic claude-haiku-4-5", appel_anthropic)
    resultats["gemini-2.5-flash"] = benchmark("Google gemini-2.5-flash", appel_gemini)

    print("\n=== RÉCAPITULATIF ===")
    for nom, durees in resultats.items():
        if durees:
            print(f"{nom:20s} : moyenne {sum(durees)/len(durees):.2f}s sur {len(durees)} essais")
        else:
            print(f"{nom:20s} : aucun essai réussi")
