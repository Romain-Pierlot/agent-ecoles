"""
audit_chunks.py
Audit qualité des chunks ChromaDB — agent-ecoles
Usage : python audit_chunks.py
Produit : audit_chunks_rapport.csv + résumé console
"""

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
import re
import csv
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL

client = chromadb.PersistentClient(path=CHROMA_PATH)
ef = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name=EMBEDDING_MODEL
)
collection = client.get_collection(CHROMA_COLLECTION, embedding_function=ef)
results = collection.get(include=["documents", "metadatas"])

SEUIL_TROP_COURT = 200
SEUIL_TROP_LONG  = 2000
MIN_MOTS         = 30

PATTERN_TITRE_SECTION = re.compile(r"(➢|►|•|\n#{1,3} |\*\*[A-Z])")
PATTERN_ARTEFACT = re.compile(r"[^\x00-\x7FéàâäéèêëîïôùûüçÉÀÂÄÈÊËÎÏÔÙÛÜÇ\u2019\n\r\t «»°€%().,;:!?\-–—/\\'\"\[\]{}@#&*+=<>]")

rapport = []

for id_, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
    problemes = []
    niveau_risque = "OK"
    longueur = len(doc)
    nb_mots = len(doc.split())
    est_manuel = "_manual_" in id_

    if longueur < SEUIL_TROP_COURT:
        problemes.append(f"TROP_COURT ({longueur} chars)")
        niveau_risque = "CRITIQUE"

    if longueur > SEUIL_TROP_LONG:
        problemes.append(f"TROP_LONG ({longueur} chars)")
        if niveau_risque == "OK":
            niveau_risque = "ATTENTION"

    if nb_mots < MIN_MOTS:
        problemes.append(f"PEU_DE_MOTS ({nb_mots} mots)")
        if niveau_risque == "OK":
            niveau_risque = "ATTENTION"

    titres_trouves = PATTERN_TITRE_SECTION.findall(doc)
    if len(titres_trouves) >= 3:
        problemes.append(f"MULTI_SECTIONS ({len(titres_trouves)} marqueurs)")
        niveau_risque = "CRITIQUE"

    artefacts = PATTERN_ARTEFACT.findall(doc)
    if len(artefacts) > 5:
        problemes.append(f"ARTEFACTS ({len(artefacts)} caractères suspects)")
        if niveau_risque == "OK":
            niveau_risque = "ATTENTION"

    dernier_char = doc.strip()[-1] if doc.strip() else ""
    if dernier_char not in [".", ")", "»", "%", ":", ";", "?", "!"]:
        problemes.append("COUPURE_POSSIBLE")
        if niveau_risque == "OK":
            niveau_risque = "VERIFIER"

    if est_manuel and niveau_risque == "OK":
        niveau_risque = "MANUEL"

    rapport.append({
        "id": id_,
        "niveau_risque": niveau_risque,
        "problemes": " | ".join(problemes) if problemes else "—",
        "domaine": meta.get("chunk_domaine", "?"),
        "dc_niveau": meta.get("dc_niveau", "?"),
        "page": meta.get("chunk_page", "?"),
        "section": meta.get("chunk_titre_section", "")[:60],
        "longueur": longueur,
        "nb_mots": nb_mots,
        "extrait": doc[:120].replace("\n", " "),
    })

ORDRE_RISQUE = {"CRITIQUE": 0, "ATTENTION": 1, "VERIFIER": 2, "MANUEL": 3, "OK": 4}
rapport.sort(key=lambda x: ORDRE_RISQUE.get(x["niveau_risque"], 99))

output_path = "audit_chunks_rapport.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rapport[0].keys())
    writer.writeheader()
    writer.writerows(rapport)

compteur = Counter(r["niveau_risque"] for r in rapport)

print("\n" + "="*60)
print("AUDIT QUALITÉ CHUNKS — RÉSUMÉ")
print("="*60)
print(f"Total chunks analysés : {len(rapport)}")
print()
for niveau in ["CRITIQUE", "ATTENTION", "VERIFIER", "MANUEL", "OK"]:
    n = compteur.get(niveau, 0)
    print(f"  {niveau:<12} {n:>3}  {'█' * n}")

print()
print("── CHUNKS CRITIQUES ──────────────────────────────────────")
critiques = [r for r in rapport if r["niveau_risque"] == "CRITIQUE"]
if critiques:
    for r in critiques:
        print(f"  [{r['id']}] page {r['page']} | {r['problemes']}")
        print(f"    Extrait : {r['extrait'][:80]}")
        print()
else:
    print("  Aucun chunk critique détecté.")

print()
print("── CHUNKS ATTENTION ──────────────────────────────────────")
attentions = [r for r in rapport if r["niveau_risque"] == "ATTENTION"]
if attentions:
    for r in attentions:
        print(f"  [{r['id']}] page {r['page']} | {r['problemes']}")
else:
    print("  Aucun.")

print()
print(f"Rapport complet : {output_path}")
print("="*60 + "\n")
