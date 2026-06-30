"""
rag_tool.py — Outil RAG pour l'agent EduScope
Retrieval dans ChromaDB et retour des chunks bruts au router LangGraph.

Rôle dans l'architecture :
- Reçoit une requête optimisée du router LangGraph
- Cherche les chunks pertinents dans ChromaDB
- Retourne les chunks bruts avec scores et métadonnées Dublin Core
- Ne génère pas de réponse finale — c'est le rôle du router

Configuration (RAG_TOP_K, SIMILARITY_THRESHOLD) centralisée dans config.py,
pour rester cohérente avec les valeurs validées via le harness (rag/harness.py).
"""

import os
import sys
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL, RAG_TOP_K, SIMILARITY_THRESHOLD


def get_collection():
    """Initialise et retourne la collection ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL,
    )
    return client.get_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
    )


def search_rag(query: str, n_results: int = None) -> dict:
    """
    Recherche les chunks pertinents dans ChromaDB.

    Args:
        query     : requête optimisée générée par le router LangGraph
        n_results : nombre de chunks à retourner (défaut : RAG_TOP_K de config.py)

    Returns:
        dict avec :
        - success      : bool
        - query        : la requête utilisée
        - chunks       : liste de chunks avec contenu, score et métadonnées
        - error        : message d'erreur si success=False
    """
    n_results = n_results or RAG_TOP_K

    try:
        collection = get_collection()

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # ChromaDB retourne des distances cosinus. text-embedding-3-small produit
        # des vecteurs normalisés, donc distance cosinus ∈ [0, 1] → score = 1 - distance
        chunks = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            score = round(1 - dist, 4)

            # On écarte les chunks sous le seuil de pertinence
            if score < SIMILARITY_THRESHOLD:
                continue

            chunks.append({
                "contenu":  doc,
                "score":    score,
                "source":   meta.get("dc_title", ""),
                "page":     meta.get("chunk_page", ""),
                "section":  meta.get("chunk_titre_section", ""),
                "domaine":  meta.get("chunk_domaine", ""),
                "url":      meta.get("dc_source", ""),
                "auteur":   meta.get("dc_creator", ""),
                "date":     meta.get("dc_date", ""),
            })

        return {
            "success": True,
            "query":   query,
            "chunks":  chunks,
        }

    except Exception as e:
        return {
            "success": False,
            "query":   query,
            "chunks":  [],
            "error":   str(e),
        }


if __name__ == "__main__":
    """Test rapide de l'outil."""
    questions = [
        "qu'est-ce que la valeur ajoutée d'un collège",
        "comment est calculé l'IPS",
        "différence IPS public privé",
        "taux d'accès sixième troisième",
        "météo à Paris demain",  # hors domaine — doit retourner 0 chunks
    ]

    for q in questions:
        print(f"\nQ : '{q}'")
        result = search_rag(q)

        if not result["success"]:
            print(f"  Erreur : {result['error']}")
            continue

        if not result["chunks"]:
            print(f"  Aucun chunk pertinent (score < {SIMILARITY_THRESHOLD})")
            continue

        for i, chunk in enumerate(result["chunks"]):
            print(f"  [{i+1}] score={chunk['score']} — {chunk['source'][:45]} p.{chunk['page']}")
            print(f"       {chunk['contenu'][:120]}...")
