# ============================================================
# Harness d'évaluation RAG — agent-ecoles
# Métriques retrieval : Recall@K, Precision@K, MRR (K=3,5,10)
# Métriques génération : Faithfulness, Answer Relevance, Answer Correctness
# Runtime : latence, coût tokens
# ============================================================

import os
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI

load_dotenv()

# --- Config ---
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL, LLM_MODEL, RERANKER_TOP_K_INITIAL
from rag.reranker import reranker as appliquer_reranker

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTATS_DIR = Path(__file__).parent / "resultats"
HISTORY_PATH = Path(__file__).parent / "resultats_harness_history.json"

K_VALUES = [3, 5, 10]
K_PRODUCTION = 5
TESTER_RERANKER = False  # Mettre à True pour comparer avec/sans re-ranker (ralentit le run)

# Coût GPT-4o-mini en dollars par token (mai 2025)
COUT_INPUT_PER_TOKEN = 0.00000015   # $0.15 / 1M tokens
COUT_OUTPUT_PER_TOKEN = 0.00000060  # $0.60 / 1M tokens


# ============================================================
# INITIALISATION
# ============================================================

def init_clients():
    client_chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL
    )
    collection = client_chroma.get_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn
    )
    client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return collection, client_openai


# ============================================================
# MÉTRIQUES RETRIEVAL
# ============================================================

def retrieval_pour_k(collection, question, k):
    """Retourne les IDs des chunks dans l'ordre retourné par ChromaDB pour un K donné."""
    debut = time.time()
    results = collection.query(
        query_texts=[question],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    latence_ms = int((time.time() - debut) * 1000)
    ids = results["ids"][0]
    docs = results["documents"][0]
    return ids, docs, latence_ms


def calcul_recall(chunks_retournes, chunks_attendus):
    """Recall = chunks attendus trouvés / total chunks attendus"""
    if not chunks_attendus:
        return 1.0
    trouves = sum(1 for c in chunks_attendus if c in chunks_retournes)
    return round(trouves / len(chunks_attendus), 4)


def calcul_precision(chunks_retournes, chunks_attendus):
    """Precision@K = chunks attendus trouvés / K"""
    if not chunks_retournes:
        return 0.0
    trouves = sum(1 for c in chunks_retournes if c in chunks_attendus)
    return round(trouves / len(chunks_retournes), 4)


def calcul_mrr(chunks_retournes, chunks_attendus):
    """MRR = 1 / position du premier chunk pertinent (0 si aucun trouvé)"""
    for i, chunk_id in enumerate(chunks_retournes):
        if chunk_id in chunks_attendus:
            return round(1 / (i + 1), 4)
    return 0.0


def evaluer_retrieval(collection, question, chunks_attendus, avec_reranker=False):
    """
    Évalue le retrieval à K=3, 5, 10. Retourne métriques + chunks retournés.
    Si avec_reranker=True : récupère RERANKER_TOP_K_INITIAL chunks, les reclasse,
    puis mesure Recall/Precision/MRR sur les K premiers du résultat reclassé.
    """
    resultats = {}
    latence_ms = 0
    latence_reranking_ms = 0

    if avec_reranker:
        # On récupère un net large, on reclasse, puis on tronque à chaque K
        ids_larges, docs_larges, lat_retrieval = retrieval_pour_k(
            collection, question, RERANKER_TOP_K_INITIAL
        )
        debut_rerank = time.time()
        ids_reclasses, docs_reclasses, scores_rerank = appliquer_reranker(
            question, ids_larges, docs_larges
        )
        latence_reranking_ms = int((time.time() - debut_rerank) * 1000)
        latence_ms = lat_retrieval + latence_reranking_ms

        for k in K_VALUES:
            ids_k = ids_reclasses[:k]
            resultats[f"k{k}"] = {
                "chunks_retournes": ids_k,
                "recall": calcul_recall(ids_k, chunks_attendus),
                "precision": calcul_precision(ids_k, chunks_attendus),
                "mrr": calcul_mrr(ids_k, chunks_attendus)
            }
        docs_production = docs_reclasses[:K_PRODUCTION]

    else:
        for k in K_VALUES:
            ids, docs, lat = retrieval_pour_k(collection, question, k)
            if k == K_PRODUCTION:
                latence_ms = lat
                docs_production = docs

            resultats[f"k{k}"] = {
                "chunks_retournes": ids,
                "recall": calcul_recall(ids, chunks_attendus),
                "precision": calcul_precision(ids, chunks_attendus),
                "mrr": calcul_mrr(ids, chunks_attendus)
            }

    return resultats, docs_production, latence_ms, latence_reranking_ms


# ============================================================
# GÉNÉRATION
# ============================================================

def generer_reponse(client_openai, question, docs_contexte):
    """Génère une réponse RAG à partir des chunks récupérés."""
    contexte = "\n\n---\n\n".join(docs_contexte)

    prompt_system = """Tu es un assistant qui aide les parents à choisir un collège.
Tu réponds uniquement à partir du contexte fourni.
Si le contexte ne contient pas l'information, dis-le clairement."""

    prompt_user = f"""Contexte :
{contexte}

Question : {question}"""

    debut = time.time()
    response = client_openai.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ],
        temperature=0
    )
    latence_ms = int((time.time() - debut) * 1000)

    reponse = response.choices[0].message.content
    tokens_prompt = response.usage.prompt_tokens
    tokens_completion = response.usage.completion_tokens
    cout = (tokens_prompt * COUT_INPUT_PER_TOKEN) + (tokens_completion * COUT_OUTPUT_PER_TOKEN)

    return reponse, latence_ms, tokens_prompt, tokens_completion, cout


# ============================================================
# LLM-AS-JUDGE
# ============================================================

def judge_faithfulness(client_openai, reponse, docs_contexte):
    """Le LLM juge si chaque affirmation de la réponse est ancrée dans le contexte."""
    contexte = "\n\n---\n\n".join(docs_contexte)

    prompt = f"""Tu es un évaluateur expert en qualité de systèmes RAG.

CONTEXTE FOURNI AU SYSTÈME :
{contexte}

RÉPONSE GÉNÉRÉE :
{reponse}

TÂCHE : Évalue si chaque affirmation de la réponse est ancrée dans le contexte fourni.
Une réponse est fidèle si elle ne contient aucune information absente du contexte.

Réponds UNIQUEMENT avec ce JSON (sans markdown) :
{{"score": 0.0, "justification": "..."}}

Score : entre 0.0 (aucune affirmation ancrée) et 1.0 (toutes les affirmations ancrées).
Justification : 1-2 phrases expliquant le score."""

    response = client_openai.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    tokens_prompt = response.usage.prompt_tokens
    tokens_completion = response.usage.completion_tokens
    cout = (tokens_prompt * COUT_INPUT_PER_TOKEN) + (tokens_completion * COUT_OUTPUT_PER_TOKEN)

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"score": 0.0, "justification": "Erreur parsing JSON judge"}

    return result, cout


def judge_answer_relevance(client_openai, question, reponse):
    """Le LLM juge si la réponse répond bien à la question posée."""
    prompt = f"""Tu es un évaluateur expert en qualité de systèmes RAG.

QUESTION POSÉE :
{question}

RÉPONSE GÉNÉRÉE :
{reponse}

TÂCHE : Évalue si la réponse répond directement et complètement à la question posée.

Réponds UNIQUEMENT avec ce JSON (sans markdown) :
{{"score": 0.0, "justification": "..."}}

Score : entre 0.0 (hors sujet) et 1.0 (répond parfaitement à la question).
Justification : 1-2 phrases expliquant le score."""

    response = client_openai.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    tokens_prompt = response.usage.prompt_tokens
    tokens_completion = response.usage.completion_tokens
    cout = (tokens_prompt * COUT_INPUT_PER_TOKEN) + (tokens_completion * COUT_OUTPUT_PER_TOKEN)

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"score": 0.0, "justification": "Erreur parsing JSON judge"}

    return result, cout


def judge_answer_correctness(client_openai, question, reponse, reponse_reference):
    """Le LLM juge si la réponse correspond à la réponse de référence du golden dataset."""
    prompt = f"""Tu es un évaluateur expert en qualité de systèmes RAG.

QUESTION POSÉE :
{question}

RÉPONSE DE RÉFÉRENCE (vérité terrain) :
{reponse_reference}

RÉPONSE GÉNÉRÉE :
{reponse}

TÂCHE : Évalue si la réponse générée est factuellement correcte et complète par rapport à la réponse de référence.
Les formulations peuvent être différentes — juge le fond, pas la forme.

Réponds UNIQUEMENT avec ce JSON (sans markdown) :
{{"score": 0.0, "justification": "..."}}

Score : entre 0.0 (incorrecte ou incomplète) et 1.0 (correcte et complète).
Justification : 1-2 phrases expliquant le score."""

    response = client_openai.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    tokens_prompt = response.usage.prompt_tokens
    tokens_completion = response.usage.completion_tokens
    cout = (tokens_prompt * COUT_INPUT_PER_TOKEN) + (tokens_completion * COUT_OUTPUT_PER_TOKEN)

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"score": 0.0, "justification": "Erreur parsing JSON judge"}

    return result, cout


# ============================================================
# ORCHESTRATION PRINCIPALE
# ============================================================

def evaluer_question(collection, client_openai, question_data, avec_reranker=False):
    """Évalue une question complète — retrieval + génération + judge."""
    question = question_data["question"]
    chunks_attendus = question_data["chunks_attendus"]
    reponse_reference = question_data["reponse_reference"]

    print(f"\n  → Retrieval{' + re-ranking' if avec_reranker else ''}...")
    retrieval, docs_production, latence_retrieval, latence_reranking = evaluer_retrieval(
        collection, question, chunks_attendus, avec_reranker=avec_reranker
    )

    print(f"  → Génération...")
    reponse, latence_generation, tokens_prompt, tokens_completion, cout_generation = generer_reponse(
        client_openai, question, docs_production
    )

    print(f"  → Judge Faithfulness...")
    faith, cout_faith = judge_faithfulness(client_openai, reponse, docs_production)

    print(f"  → Judge Answer Relevance...")
    relevance, cout_relevance = judge_answer_relevance(client_openai, question, reponse)

    print(f"  → Judge Answer Correctness...")
    correctness, cout_correctness = judge_answer_correctness(
        client_openai, question, reponse, reponse_reference
    )

    cout_total = cout_generation + cout_faith + cout_relevance + cout_correctness

    return {
        "id": question_data["id"],
        "question": question,
        "chunks_attendus": chunks_attendus,
        "retrieval": retrieval,
        "generation": {
            "reponse_produite": reponse,
            "faithfulness": faith,
            "answer_relevance": relevance,
            "answer_correctness": correctness
        },
        "runtime": {
            "latence_retrieval_ms": latence_retrieval,
            "latence_reranking_ms": latence_reranking,
            "latence_generation_ms": latence_generation,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "cout_dollars": round(cout_total, 6)
        }
    }


def calculer_agregats(resultats_questions):
    """Calcule les moyennes globales sur toutes les questions."""
    n = len(resultats_questions)
    if n == 0:
        return {}

    def moyenne(key_path):
        vals = []
        for q in resultats_questions:
            obj = q
            for k in key_path:
                obj = obj[k]
            vals.append(obj)
        return round(sum(vals) / len(vals), 4)

    return {
        "recall_k3": moyenne(["retrieval", "k3", "recall"]),
        "recall_k5": moyenne(["retrieval", "k5", "recall"]),
        "recall_k10": moyenne(["retrieval", "k10", "recall"]),
        "precision_k3": moyenne(["retrieval", "k3", "precision"]),
        "precision_k5": moyenne(["retrieval", "k5", "precision"]),
        "precision_k10": moyenne(["retrieval", "k10", "precision"]),
        "mrr_k3": moyenne(["retrieval", "k3", "mrr"]),
        "mrr_k5": moyenne(["retrieval", "k5", "mrr"]),
        "mrr_k10": moyenne(["retrieval", "k10", "mrr"]),
        "faithfulness": moyenne(["generation", "faithfulness", "score"]),
        "answer_relevance": moyenne(["generation", "answer_relevance", "score"]),
        "answer_correctness": moyenne(["generation", "answer_correctness", "score"]),
        "latence_retrieval_moy_ms": round(
            sum(q["runtime"]["latence_retrieval_ms"] for q in resultats_questions) / n
        ),
        "latence_generation_moy_ms": round(
            sum(q["runtime"]["latence_generation_ms"] for q in resultats_questions) / n
        ),
        "cout_total_dollars": round(
            sum(q["runtime"]["cout_dollars"] for q in resultats_questions), 6
        )
    }


def sauvegarder_resultats(run_id, agregats, resultats_questions):
    """Sauvegarde le détail du run + met à jour l'historique."""
    RESULTATS_DIR.mkdir(exist_ok=True)

    # Fichier détail horodaté
    rapport = {
        "metadata": {
            "run_id": run_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nb_questions": len(resultats_questions),
            "golden_dataset": str(GOLDEN_DATASET_PATH),
            "k_production": K_PRODUCTION,
            "k_tests": K_VALUES,
            "modele_llm": LLM_MODEL,
            "modele_embedding": EMBEDDING_MODEL
        },
        "agregats": agregats,
        "questions": resultats_questions
    }

    fichier_detail = RESULTATS_DIR / f"resultats_harness_{run_id}.json"
    with open(fichier_detail, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    # Fichier latest
    fichier_latest = RESULTATS_DIR / "resultats_harness_latest.json"
    with open(fichier_latest, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    # Historique synthétique
    historique = []
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            historique = json.load(f)

    historique.append({
        "run_id": run_id,
        "date": rapport["metadata"]["date"],
        "nb_questions": len(resultats_questions),
        "modele_llm": LLM_MODEL,
        "modele_embedding": EMBEDDING_MODEL,
        "k_production": K_PRODUCTION,
        **agregats,
        "fichier_detail": str(fichier_detail)
    })

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(historique, f, ensure_ascii=False, indent=2)

    return fichier_detail


# ============================================================
# POINT D'ENTRÉE
# ============================================================

def lancer_run(collection, client_openai, golden_dataset, avec_reranker, label):
    """Lance un run complet du harness avec ou sans re-ranker."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + ("_rerank" if avec_reranker else "_baseline")
    print(f"\n=== HARNESS RAG — {label} — run {run_id} ===")

    resultats_questions = []
    for i, question_data in enumerate(golden_dataset):
        print(f"\n[{i+1}/{len(golden_dataset)}] {question_data['id']} — {question_data['question'][:60]}...")
        resultat = evaluer_question(collection, client_openai, question_data, avec_reranker=avec_reranker)
        resultats_questions.append(resultat)

    print("\nCalcul des agrégats...")
    agregats = calculer_agregats(resultats_questions)
    agregats["avec_reranker"] = avec_reranker

    print("\nSauvegarde des résultats...")
    fichier = sauvegarder_resultats(run_id, agregats, resultats_questions)

    print(f"\n--- RÉSULTATS {label} ---")
    print(f"Recall@3      : {agregats['recall_k3']}")
    print(f"Recall@5      : {agregats['recall_k5']}")
    print(f"Recall@10     : {agregats['recall_k10']}")
    print(f"Precision@K{K_PRODUCTION} (prod) : {agregats[f'precision_k{K_PRODUCTION}']}")
    print(f"MRR@K{K_PRODUCTION} (prod)       : {agregats[f'mrr_k{K_PRODUCTION}']}")
    print(f"Faithfulness       : {agregats['faithfulness']}")
    print(f"Answer Relevance   : {agregats['answer_relevance']}")
    print(f"Answer Correctness : {agregats['answer_correctness']}")
    print(f"Coût total         : ${agregats['cout_total_dollars']}")
    print(f"Détail sauvegardé : {fichier}")

    return agregats


def main():
    print("\nInitialisation des clients...")
    collection, client_openai = init_clients()

    print("Chargement du golden dataset...")
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        golden_dataset = json.load(f)
    print(f"  {len(golden_dataset)} questions chargées")

    agregats_baseline = lancer_run(collection, client_openai, golden_dataset, avec_reranker=False, label="BASELINE (sans re-ranker)")

    if TESTER_RERANKER:
        agregats_rerank = lancer_run(collection, client_openai, golden_dataset, avec_reranker=True, label="AVEC RE-RANKER")

        print(f"\n\n=== COMPARATIF ===")
        print(f"{'Métrique':<20} {'Baseline':<12} {'Re-ranker':<12} {'Delta':<10}")
        for cle, nom in [
            (f"recall_k{K_PRODUCTION}", f"Recall@K{K_PRODUCTION}"),
            (f"precision_k{K_PRODUCTION}", f"Precision@K{K_PRODUCTION}"),
            (f"mrr_k{K_PRODUCTION}", f"MRR@K{K_PRODUCTION}"),
            ("faithfulness", "Faithfulness"), ("answer_relevance", "Answer Relevance"),
            ("answer_correctness", "Answer Correctness")
        ]:
            b, r = agregats_baseline[cle], agregats_rerank[cle]
            delta = round(r - b, 4)
            print(f"{nom:<20} {b:<12} {r:<12} {delta:+.4f}")

    print(f"\nHistorique mis à jour : {HISTORY_PATH}")


if __name__ == "__main__":
    main()
