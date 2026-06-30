# ============================================================
# EduScope — Configuration centrale
# La vérité est dans le code. Toutes les constantes ici.
# ============================================================
import os

# Racine du projet — ancré sur ce fichier, jamais sur le répertoire courant
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Timeouts (secondes) ---
LLM_TIMEOUT_SECONDS = 30        # Au-delà l'utilisateur abandonne
BAN_API_TIMEOUT_SECONDS = 5     # API BAN publique, parfois lente
SQL_TIMEOUT_SECONDS = 10        # Requête SQLite locale

# --- Retries ---
LLM_MAX_RETRIES = 2             # Erreurs transitoires OpenAI

# --- Agent ---
AGENT_MAX_TOURS = 5             # Garde-fou boucle infinie LangGraph

# --- Scoring ---
SCORE_POIDS_TAUX = 0.60         # Poids taux de réussite dans le score
SCORE_POIDS_NOTE = 0.40         # Poids note à l'écrit dans le score

# --- Badge Valeur Ajoutée ---
VA_SEUIL_POSITIF = 2.0          # VA taux > +2 → badge vert
VA_SEUIL_NEGATIF = -2.0         # VA taux < -2 → badge rouge

# --- Base de données ---
DB_PATH = os.path.join(_PROJECT_ROOT, "data", "agent_ecoles.db")

# --- ChromaDB ---
CHROMA_PATH = os.path.join(_PROJECT_ROOT, "chroma_db")
CHROMA_COLLECTION = "depp_methodology"

# --- Re-ranking ---
RERANKER_PROVIDER = "local"  # "local" (cross-encoder gratuit) ou "cohere" (API payante)
RERANKER_MODEL_LOCAL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"  # multilingue, adapté au français
RERANKER_TOP_K_INITIAL = 10  # Nombre de chunks récupérés par ChromaDB avant re-ranking


# --- RAG ---
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 5                   # Nombre de chunks retournés par recherche (K=3 testé : Recall trop faible, 0.64)
SIMILARITY_THRESHOLD = 0.50      # Seuil de score sous lequel un chunk est écarté (formule : 1 - distance cosinus)

# --- LLM ---
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# --- LangSmith ---
LANGSMITH_PROJECT = "agent-ecoles"

# --- Géolocalisation ---
GEO_RAYON_DEFAUT_KM = 10       # Rayon par défaut si non précisé par l'utilisateur
