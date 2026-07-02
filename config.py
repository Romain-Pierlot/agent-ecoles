# ============================================================
# EduScope — Configuration centrale
# La vérité est dans le code. Toutes les constantes ici.
# ============================================================
import os
from enum import StrEnum

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


# --- Router : catégories de question (ensemble fermé -> enum, pas des chaînes libres) ---
class Categorie(StrEnum):
    RECHERCHE_GEO_CLASSEMENT = "recherche_geo_classement"
    COMPARAISON_ETABLISSEMENTS_NOMMES = "comparaison_etablissements_nommes"
    QUESTION_METHODOLOGIQUE = "question_methodologique"
    NON_RECONNU = "non_reconnu"


class SecteurSouhaite(StrEnum):
    """Secteur demandé par l'utilisateur dans sa question (extrait par le router)."""
    PUBLIC = "public"
    PRIVE = "prive"
    INDIFFERENT = "indifferent"


class Secteur(StrEnum):
    """Valeurs du secteur telles que stockées dans la table etablissements — distinct de SecteurSouhaite."""
    PUBLIC = "Public"
    PRIVE = "Privé"


class OrdreSouhaite(StrEnum):
    """
    Sens de tri demandé par l'utilisateur (extrait par le router, en LLM,
    pas par mots-clés en dur) — remplace les regex _MOTS_SUPERLATIFS/_MOTS_PIRE
    (S8.13/S8.20), qui ne couvraient que "meilleur"/"pire" littéralement et
    ratent les synonymes ("le plus mauvais", "en difficulté", "moins bon"...).
    """
    MEILLEUR = "meilleur"
    PIRE = "pire"
    INDIFFERENT = "indifferent"


# --- Synthèse de réponse (graph_router.py) ---
MAX_LIGNES_SYNTHESE = 15        # limite de sécurité — évite d'envoyer des centaines de lignes au LLM de synthèse
SPLIT_SECTEUR_N = 10            # nombre d'établissements par secteur affichés quand le secteur n'est pas précisé

# --- Agent ReAct : comparaison multi-zones ---
# Au-delà, l'agent devient trop lent/coûteux (timeout observé à 5 zones,
# ~96s avant échec ; 3 zones fonctionne de façon fiable en ~25s, cf. session 8).
# Bloqué en amont plutôt que de laisser l'agent essayer et échouer.
MAX_ZONES_COMPAREES = 3

# --- Résolution de noms d'établissements (sql_tool.py) ---
SEUIL_CANDIDATS_AVANT_PRECISION = 5   # au-delà, l'entonnoir de désambiguïsation demande une précision géo
PREFIXES_INSTITUTIONNELS = [
    "college prive",
    "college",
    "ecole",
    "clg",
]
