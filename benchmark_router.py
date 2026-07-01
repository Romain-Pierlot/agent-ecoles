"""
benchmark_router.py — Compare la latence de gpt-4o-mini, claude-haiku-4-5
et gemini-2.5-flash sur l'appel de classification + extraction de zone
du nœud router, avec le prompt système réduit (post-optimisation).
"""

import os
import time
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from openai import OpenAI
import anthropic
from google import genai

NB_ESSAIS = 5
QUESTION_TEST = "Quels sont les meilleurs collèges à Lyon ?"

CATEGORIES = [
    "recherche_geo_classement", "comparaison_etablissements_nommes",
    "recherche_geo_comparaison", "question_methodologique",
    "recherche_geo_methodologique", "non_reconnu",
]

ROUTER_SYSTEM_PROMPT = """
Tu classifies une question sur le choix de collège en France dans UNE des
catégories suivantes, et extrais sa zone géographique si présente.

- recherche_geo_classement : recherche géo avec tri par indicateur.
- comparaison_etablissements_nommes : comparaison d'établissements nommés.
- recherche_geo_comparaison : recherche géo + comparaison.
- question_methodologique : question sur un concept/indicateur, sans donnée
  chiffrée sur un établissement précis.
- recherche_geo_methodologique : recherche géo + question méthodologique.
- non_reconnu : aucune catégorie ci-dessus ne correspond clairement.
"""

ROUTER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "classifier_question",
        "description": "Classifie la question et extrait sa zone géographique.",
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {"type": "string", "enum": CATEGORIES},
                "zone_detectee": {"type": "boolean"},
                "zone": {"type": "string"},
            },
            "required": ["categorie", "zone_detectee", "zone"],
        },
    },
}


def appel_openai():
    client = OpenAI()
    debut = time.time()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": QUESTION_TEST},
        ],
        tools=[ROUTER_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "classifier_question"}},
        timeout=30,
    )
    duree = time.time() - debut
    tokens = response.usage.completion_tokens
    return duree, tokens


def appel_anthropic():
    client = anthropic.Anthropic()
    tool_anthropic = {
        "name": "classifier_question",
        "description": "Classifie la question et extrait sa zone géographique.",
        "input_schema": ROUTER_TOOL_SCHEMA["function"]["parameters"],
    }
    debut = time.time()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        system=ROUTER_SYSTEM_PROMPT,
        tools=[tool_anthropic],
        tool_choice={"type": "tool", "name": "classifier_question"},
        messages=[{"role": "user", "content": QUESTION_TEST}],
    )
    duree = time.time() - debut
    tokens = response.usage.output_tokens
    return duree, tokens


def appel_gemini():
    client = genai.Client()
    debut = time.time()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=QUESTION_TEST,
        config={
            "system_instruction": ROUTER_SYSTEM_PROMPT,
            "tools": [{"function_declarations": [ROUTER_TOOL_SCHEMA["function"]]}],
        },
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

    print("\n=== RÉCAPITULATIF ROUTER (prompt réduit) ===")
    for nom, durees in resultats.items():
        if durees:
            print(f"{nom:20s} : moyenne {sum(durees)/len(durees):.2f}s sur {len(durees)} essais")
        else:
            print(f"{nom:20s} : aucun essai réussi")
