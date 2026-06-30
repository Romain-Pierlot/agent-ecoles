"""
ingest_rag.py — Pipeline d'ingestion des documents DEPP dans ChromaDB
Version 8 — ajout chunk Cour des comptes + version du header corrigée

Corrections v8 :
- Ajout chunk ccomptes_2023_prive_000 dans CHUNKS_MANUELS
- Correction placement chunk (était hors liste en v7)
"""

import os
import re
import sys
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL

SOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources")

CHUNK_MAX_CHARACTERS = 1500
CHUNK_NEW_AFTER_N_CHARS = 1000
CHUNK_COMBINE_UNDER_N_CHARS = 500

CHUNKS_ARTEFACTS = {
    "ivac_2025_003",
    "ivac_2025_004",
    "ivac_2025_005",
    "ips_2016_000",
    "ips_2016_004",
    "ips_2016_015",
    "ips_2016_018",
    "ips_2016_020",
    "ips_2016_035",
    "ips_2023_000",
}

KEYWORDS_EXCLUSION = [
    "SOMMAIRE", "BIBLIOGRAPHIE", "ANNEXES", "Table des matières",
    "Pour aller plus loin", "Retrouvez les travaux", "Calcul pratique", "FIGURE 2",
]



import json

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chunks_manuels.json"), "r", encoding="utf-8") as f:
    CHUNKS_MANUELS = json.load(f)


SOURCES = [
    {
        "fichier": "Depp_Guide_méthodologique_IVAC_2025.pdf-515492.pdf",
        "pages_exclure": [1, 2, 4, 7, 9, 10, 11],
        "dc_title":      "Guide méthodologique IVAC 2025",
        "dc_creator":    "Franck Evain, Violette Marmion — DEPP B3",
        "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
        "dc_date":       "2025",
        "dc_type":       "methodologie",
        "dc_source":     "https://www.education.gouv.fr/depp/les-indicateurs-de-resultats-des-colleges-et-des-lycees-377729",
        "chunk_domaine": "ivac",
        "dc_niveau":     "avancé",
    },
    {
        "fichier": "EF-90-chap-01-construction-d-un-indice-de-position-sociale-des-eleves-pdfa.pdf",
        "pages_exclure": [10, 19, 20, 21, 22, 23, 24],
        "dc_title":      "Construction d'un Indice de Position Sociale des élèves",
        "dc_creator":    "Thierry Rocher — MENESR-DEPP",
        "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
        "dc_date":       "2016",
        "dc_type":       "article_methodologique",
        "dc_source":     "https://www.education.gouv.fr/education-formations-n-90-avril-2016-5959",
        "chunk_domaine": "ips",
        "dc_niveau":     "avancé",
    },
    {
        "fichier": "Indice de position sociale (IPS) _ actualisation 2022-476864.pdf",
        "pages_exclure": [1, 2, 3, 4, 5, 16, 17, 18, 19, 20, 21, 22],
        "dc_title":      "Indice de position sociale (IPS) — Actualisation 2022",
        "dc_creator":    "Thierry Rocher — DEPP",
        "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
        "dc_date":       "2023",
        "dc_type":       "document_travail",
        "dc_source":     "https://www.education.gouv.fr/indice-de-position-sociale-ips-actualisation-2022-476864",
        "chunk_domaine": "ips",
        "dc_niveau":     "avancé",
    },
    {
        "fichier": "NI 23.16-364089_IPS.pdf",
        "pages_exclure": [1, 2, 3, 4],
        "dc_title":      "Note d'information — L'IPS, un outil pour décrire les inégalités sociales entre établissements",
        "dc_creator":    "Fannie Dauphant, Franck Evain, Marine Guillerm, Catherine Simon, Thierry Rocher — DEPP B3",
        "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
        "dc_date":       "2023",
        "dc_type":       "note_information",
        "dc_source":     "https://www.education.gouv.fr/ni-23-16-l-indice-de-position-sociale-ips-364089",
        "chunk_domaine": "ips",
        "dc_niveau":     "avancé",
    },
]


def est_chunk_fragmente(texte: str) -> bool:
    lignes = [l.strip() for l in texte.split("\n") if l.strip()]
    if len(lignes) < 4:
        return False
    lignes_courtes = sum(1 for l in lignes if len(l) < 40)
    return (lignes_courtes / len(lignes)) > 0.5


def extraire_chunks(chemin: str, pages_exclure: list) -> list:
    elements = partition_pdf(chemin)
    elements = [e for e in elements if type(e).__name__ != "Footer"]
    if pages_exclure:
        elements_filtres = []
        for e in elements:
            page = None
            try:
                page = e.metadata.page_number
            except AttributeError:
                pass
            if page not in pages_exclure:
                elements_filtres.append(e)
        elements = elements_filtres
    chunks_raw = chunk_by_title(
        elements,
        max_characters=CHUNK_MAX_CHARACTERS,
        new_after_n_chars=CHUNK_NEW_AFTER_N_CHARS,
        combine_text_under_n_chars=CHUNK_COMBINE_UNDER_N_CHARS,
    )
    chunks_valides = []
    for chunk in chunks_raw:
        texte = chunk.text.strip()
        if any(kw.lower() in texte.lower() for kw in KEYWORDS_EXCLUSION):
            continue
        premier_mot = texte.split()[0] if texte.split() else ""
        if premier_mot and premier_mot[0].islower():
            continue
        if re.match(r'^[A-Z] [a-z]', texte):
            continue
        if texte.startswith("(cid:"):
            continue
        if len(texte) < 100:
            continue
        chars_alpha = sum(1 for c in texte if c.isalpha())
        ratio_alpha = chars_alpha / len(texte) if texte else 0
        if ratio_alpha < 0.60:
            continue
        if re.search(r'[a-zàâéèêëîïôùûü][A-ZÀÂÉÈÊËÎÏÔÙÛÜ]', texte) and \
           len(re.findall(r'[a-zàâéèêëîïôùûü][A-ZÀÂÉÈÊËÎÏÔÙÛÜ]', texte)) > 3:
            continue
        if est_chunk_fragmente(texte):
            continue
        chunks_valides.append(chunk)
    return chunks_valides


def construire_metadata(chunk, source: dict) -> dict:
    page = "N/A"
    try:
        page = str(chunk.metadata.page_number)
    except AttributeError:
        pass
    titre_section = ""
    try:
        titre_section = chunk.metadata.section or ""
    except AttributeError:
        pass
    return {
        "dc_title":            source["dc_title"],
        "dc_creator":          source["dc_creator"],
        "dc_publisher":        source["dc_publisher"],
        "dc_date":             source["dc_date"],
        "dc_type":             source["dc_type"],
        "dc_source":           source["dc_source"],
        "chunk_domaine":       source["chunk_domaine"],
        "dc_niveau":           source["dc_niveau"],
        "chunk_page":          page,
        "chunk_titre_section": titre_section,
    }


def main():
    print("=== INGESTION RAG AGENT-ECOLES v8 ===")
    print("=== Unstructured + chunks manuels + sources accessibles ===\n")

    chroma_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        CHROMA_PATH
    )
    os.makedirs(chroma_path, exist_ok=True)

    client = chromadb.PersistentClient(path=chroma_path)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL,
    )

    try:
        client.delete_collection(CHROMA_COLLECTION)
        print("Collection existante supprimée\n")
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = 0

    print(f"-> Chunks manuels ({len(CHUNKS_MANUELS)} chunks)")
    collection.upsert(
        ids=[c["id"] for c in CHUNKS_MANUELS],
        documents=[c["contenu"] for c in CHUNKS_MANUELS],
        metadatas=[c["metadata"] for c in CHUNKS_MANUELS],
    )
    total_chunks += len(CHUNKS_MANUELS)
    print(f"  OK {len(CHUNKS_MANUELS)} chunks manuels ingérés\n")

    for source in SOURCES:
        chemin = os.path.join(SOURCES_DIR, source["fichier"])
        if not os.path.exists(chemin):
            print(f"MANQUANT : {source['fichier'][:60]}")
            continue

        print(f"-> {source['dc_title'][:55]}")
        print(f"  Niveau : {source['dc_niveau']} | Pages exclues : {source['pages_exclure']}")

        chunks_bruts = extraire_chunks(chemin, source["pages_exclure"])
        prefix = f"{source['chunk_domaine']}_{source['dc_date']}"
        chunks_avec_ids = [(f"{prefix}_{i:03d}", c) for i, c in enumerate(chunks_bruts)]
        chunks_filtres = [(id_, c) for id_, c in chunks_avec_ids if id_ not in CHUNKS_ARTEFACTS]

        if not chunks_filtres:
            print(f"  VIDE apres filtrage\n")
            continue

        ids_filtres = [x[0] for x in chunks_filtres]
        chunks_ok = [x[1] for x in chunks_filtres]
        documents = [c.text.strip() for c in chunks_ok]
        metadatas = [construire_metadata(c, source) for c in chunks_ok]

        collection.upsert(ids=ids_filtres, documents=documents, metadatas=metadatas)
        total_chunks += len(chunks_filtres)
        print(f"  OK {len(chunks_filtres)} chunks ingérés")
        for i, (doc, meta) in enumerate(zip(documents[:2], metadatas[:2])):
            print(f"    [{i}] p.{meta['chunk_page']} — {doc[:100]}...")
        print()

    print(f"Total : {total_chunks} chunks dans ChromaDB\n")

    print("=== TEST DE RECHERCHE ===\n")
    questions = [
        "qu'est-ce que la valeur ajoutée d'un collège",
        "quels sont les quatre indicateurs IVAC",
        "est-ce qu'un collège privé avec un bon taux de réussite est forcément meilleur",
        "comment est calculé l'IPS",
        "différence IPS public privé",
        "taux d'accès sixième troisième",
        "météo Paris demain",
    ]

    for question in questions:
        results = collection.query(query_texts=[question], n_results=2)
        print(f"Q : '{question}'")
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            print(f"  [{i+1}] [{meta.get('dc_niveau','?')}] {meta['dc_title'][:45]} — p.{meta['chunk_page']}")
            print(f"       {doc[:110]}...")
        print()


if __name__ == "__main__":
    main()
