# ============================================================
# EduScope — Configuration centrale
# La vérité est dans le code. Toutes les constantes ici.
# ============================================================

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
DB_PATH = "data/agent_ecoles.db"

# --- ChromaDB ---
CHROMA_PATH = "chroma_db"
CHROMA_COLLECTION = "depp_methodology"

# --- RAG ---
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 3                   # Nombre de chunks retournés par recherche

# --- LLM ---
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# --- LangSmith ---
LANGSMITH_PROJECT = "agent-ecoles"

# --- Géolocalisation ---
GEO_RAYON_DEFAUT_KM = 10       # Rayon par défaut si non précisé par l'utilisateur
