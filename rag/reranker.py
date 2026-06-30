# ============================================================
# Re-ranker — agent-ecoles
# Reclasse les chunks retournés par ChromaDB avec un cross-encoder
# Architecture modulaire : le provider est configurable (local / cohere)
# ============================================================

from config import RERANKER_PROVIDER, RERANKER_MODEL_LOCAL

# --- Provider local : cross-encoder sentence-transformers ---

_model_local = None  # Chargé une seule fois (lazy loading)


def _get_model_local():
    """Charge le modèle local une seule fois, au premier appel."""
    global _model_local
    if _model_local is None:
        from sentence_transformers import CrossEncoder
        _model_local = CrossEncoder(RERANKER_MODEL_LOCAL)
    return _model_local


def _reranker_local(question, chunks_ids, chunks_docs):
    """
    Reclasse les chunks avec un cross-encoder local.
    chunks_ids : liste des IDs dans l'ordre ChromaDB
    chunks_docs : liste des contenus textuels correspondants
    Retourne : (ids_reclasses, docs_reclasses) triés par pertinence décroissante
    """
    model = _get_model_local()
    paires = [[question, doc] for doc in chunks_docs]
    scores = model.predict(paires)

    # Tri décroissant par score
    indices_tries = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    ids_reclasses = [chunks_ids[i] for i in indices_tries]
    docs_reclasses = [chunks_docs[i] for i in indices_tries]
    scores_tries = [float(scores[i]) for i in indices_tries]

    return ids_reclasses, docs_reclasses, scores_tries


# --- Provider Cohere (placeholder — à implémenter si besoin) ---

def _reranker_cohere(question, chunks_ids, chunks_docs):
    """
    Reclasse les chunks via l'API Cohere Rerank.
    Nécessite COHERE_API_KEY dans .env et le package cohere installé.
    """
    raise NotImplementedError(
        "Provider Cohere non implémenté. "
        "Pour l'activer : pip install cohere, ajouter COHERE_API_KEY au .env, "
        "et implémenter cette fonction."
    )


# --- Interface publique stable ---

def reranker(question, chunks_ids, chunks_docs, provider=None):
    """
    Reclasse une liste de chunks selon leur pertinence réelle par rapport à la question.

    Args:
        question (str): la question utilisateur
        chunks_ids (list[str]): IDs des chunks dans l'ordre retourné par ChromaDB
        chunks_docs (list[str]): contenus textuels correspondants
        provider (str, optionnel): "local" ou "cohere". Si None, utilise RERANKER_PROVIDER de config.py

    Returns:
        tuple (ids_reclasses, docs_reclasses, scores) — tous triés par pertinence décroissante
    """
    provider = provider or RERANKER_PROVIDER

    if provider == "local":
        return _reranker_local(question, chunks_ids, chunks_docs)
    elif provider == "cohere":
        return _reranker_cohere(question, chunks_ids, chunks_docs)
    else:
        raise ValueError(f"Provider de re-ranking inconnu : {provider}")
