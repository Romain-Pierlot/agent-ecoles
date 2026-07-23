# ============================================================
# agent-ecoles — Configuration centrale
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
# score_principal (jamais affiché) : sert au tri "meilleur collège" et à
# dériver la notation en lettres (cf. NOTATION_* ci-dessous). 4 indicateurs
# à parts égales — donner autant de poids à la VA (50% du total) qu'aux
# résultats bruts est un choix assumé (cf. decision_log.md S13.4) : valoriser
# les collèges qui font mieux que prévu, pas seulement ceux qui réussissent
# déjà le mieux.
SCORE_PRINCIPAL_POIDS_TAUX = 0.25     # Taux de réussite
SCORE_PRINCIPAL_POIDS_NOTE = 0.25     # Note à l'écrit
SCORE_PRINCIPAL_POIDS_VA_TAUX = 0.25  # VA sur le taux de réussite
SCORE_PRINCIPAL_POIDS_VA_NOTE = 0.25  # VA sur la note à l'écrit

# score_resultats (jamais affiché) : sert au tri quand la question porte
# explicitement sur "les résultats" d'un collège (pas sur "le meilleur
# collège") — résultats bruts seuls, sans valeur ajoutée.
SCORE_RESULTATS_POIDS_TAUX = 0.50
SCORE_RESULTATS_POIDS_NOTE = 0.50

# --- Notation en lettres (dérivée de score_principal uniquement) ---
# Répartition Stanine (standard nine) adaptée à 5 groupes : bande centrale
# large, bandes resserrées aux extrêmes pour réserver les notes les plus
# hautes/basses aux collèges réellement atypiques (cf. decision_log.md
# S13.4). Les deux listes sont alignées : NOTATION_LETTRES[i] correspond au
# pourcentage NOTATION_REPARTITION[i], du groupe le plus faible (index 0) au
# plus élevé (dernier index).
NOTATION_REPARTITION = [10, 15, 50, 15, 10]     # en %, somme = 100
NOTATION_LETTRES = ["B", "B+", "A-", "A", "A+"]  # du plus faible au plus élevé

# Rang de la notation, de la plus forte (0) à la plus faible — dérivé de
# NOTATION_LETTRES plutôt que retapé à chaque endroit qui trie une liste de
# collèges par notation (hierarchie_tool.py, recherche_tool.py).
RANG_NOTATION = {lettre: i for i, lettre in enumerate(reversed(NOTATION_LETTRES))}

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
GEO_RAYON_ENVIRONS_KM = 5      # Rayon pour un élargissement explicite ("et les environs") — testé en
                               # région parisienne : 10 km y ramène des communes trop éloignées.

# --- API backend ---
API_CORS_ORIGINS = ["http://localhost:3000"]  # Origine du frontend Next.js en local


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


class SectionSouhaitee(StrEnum):
    """Section/option demandée comme critère de filtre (extraite par le router)."""
    SPORT = "sport"
    ARTS = "arts"
    CINEMA = "cinema"
    THEATRE = "theatre"
    INTERNATIONALE = "internationale"
    EUROPEENNE = "europeenne"
    AUCUNE = "aucune"


# Correspondance vers le vrai nom de colonne SQL — jamais construit
# dynamiquement à partir du texte utilisateur (cf. agent/tools/sql_tool.py,
# qui revalide en plus contre sa propre liste blanche avant tout usage SQL).
COLONNE_SECTION = {
    SectionSouhaitee.SPORT: "section_sport",
    SectionSouhaitee.ARTS: "section_arts",
    SectionSouhaitee.CINEMA: "section_cinema",
    SectionSouhaitee.THEATRE: "section_theatre",
    SectionSouhaitee.INTERNATIONALE: "section_internationale",
    SectionSouhaitee.EUROPEENNE: "section_europeenne",
}

# Liste blanche des colonnes de section utilisables comme critère de filtre
# dans une requête SQL — dérivée de COLONNE_SECTION (source unique), jamais
# retapée. Partagée par sql_tool.py et recherche_tool.py : centralisée ici
# plutôt qu'importée d'un module à l'autre pour éviter qu'un module sans
# rapport avec le LLM (recherche_tool.py, déterministe) dépende d'un module
# qui instancie un client OpenAI à l'import (sql_tool.py).
COLONNES_SECTION_VALIDES = set(COLONNE_SECTION.values())

# Libellé affiché à l'utilisateur pour chaque section (cf. graph_router.py,
# affichage Oui/Non pour un établissement nommé).
LIBELLE_SECTION = {
    SectionSouhaitee.SPORT: "sportive",
    SectionSouhaitee.ARTS: "arts",
    SectionSouhaitee.CINEMA: "cinéma",
    SectionSouhaitee.THEATRE: "théâtre",
    SectionSouhaitee.INTERNATIONALE: "internationale",
    SectionSouhaitee.EUROPEENNE: "européenne",
}


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


class CritereTriSouhaite(StrEnum):
    """
    Critère de tri demandé par l'utilisateur sur le chemin géo déterministe
    (recherche_geo_classement) — distinct du SENS du tri (OrdreSouhaite).
    GLOBAL (score_principal, notation en lettres) est le tri par défaut
    ("meilleur collège", "classement"). RESULTATS (score_resultats, résultats
    bruts seuls, sans VA) s'applique uniquement quand la question mentionne
    explicitement "les résultats" (cf. decision_log.md S13.4).
    """
    GLOBAL = "global"
    RESULTATS = "resultats"


# --- Synthèse de réponse (graph_router.py) ---
MAX_LIGNES_SYNTHESE = 15        # limite de sécurité — évite d'envoyer des centaines de lignes au LLM de synthèse
SPLIT_SECTEUR_N = 10            # nombre d'établissements par secteur affichés quand le secteur n'est pas précisé
# Requête SQL déterministe (aucun coût LLM) : on récupère ce plafond dès la
# première recherche, mais on n'en affiche que SPLIT_SECTEUR_N — le reste
# attend en cache de session pour le bouton "voir plus" (cf. graph_router.py
# resoudre_choix_voir_plus), sans nouvel appel SQL ni LLM au clic.
SPLIT_SECTEUR_N_MAX = 50
SPLIT_SECTEUR_INCREMENT = 10    # établissements supplémentaires révélés par clic "voir plus"

# --- Mémoire de conversation (graph_router.py) ---
# Nombre de tours passés dans le prompt du routeur pour interpréter une
# relance ("et son adresse ?"). Choix validé avec l'utilisateur : le coût
# réel (mesuré à ~0,0003$/appel pour 5 tours en gpt-4o-mini) est négligeable
# à cette échelle, l'état de session (zone/noms/UAI déjà résolus) couvre par
# ailleurs la continuité au-delà de cette fenêtre — pas de résumé/compaction
# pour l'instant, ajouté plus tard si l'usage réel le justifie.
HISTORIQUE_MAX_TOURS = 5

# --- Agent ReAct : comparaison multi-zones ---
# Au-delà, l'agent devient trop lent/coûteux (timeout observé à 5 zones,
# ~96s avant échec ; 3 zones fonctionne de façon fiable en ~25s, cf. session 8).
# Bloqué en amont plutôt que de laisser l'agent essayer et échouer.
MAX_ZONES_COMPAREES = 3

# --- Résolution de noms d'établissements et de zones géo ambiguës ---
# Seuil commun aux deux entonnoirs de désambiguïsation (noms d'établissements
# et zones géo homonymes/partielles, ex: "Neuilly" -> 5 communes possibles).
# Testé à 10 initialement — à redescendre à 5 si l'affichage de 10 boutons
# s'avère trop chargé à l'usage (cf. décision produit du 2026-07-05).
SEUIL_CANDIDATS_AVANT_PRECISION = 10   # au-delà, on redemande de préciser en texte libre
PREFIXES_INSTITUTIONNELS = [
    "college prive",
    "college",
    "ecole",
    "clg",
]

# --- Carte scolaire / rattachement de secteur ---
# Rayon de repli quand le rattachement officiel n'est pas déterminable
# (~35% des cas mesurés, cf. docs/exploration/etude_matching_carte_scolaire.md) :
# volontairement plus resserré que GEO_RAYON_DEFAUT_KM (10km, pensé pour une
# recherche libre par ville) car ce repli part toujours d'une adresse déjà
# géocodée avec précision, contrairement à une recherche par ville seule —
# 5km privilégie la pertinence locale. Pas de test empirique dédié comme
# GEO_RAYON_ENVIRONS_KM : à ajuster si l'usage réel montre que c'est trop
# étroit ou trop large.
SECTEUR_RAYON_REPLI_KM = 5

# Nombre max de collèges affichés dans la liste "alentours" (états non
# déterminable / multi-secteur de la page dédiée).
SECTEUR_MAX_COLLEGES_ALENTOURS = 4

# Nombre de suggestions d'autocomplétion adresse proposées pendant la
# saisie (cf. agent/tools/geo_tool.py::geocoder_suggestions) — évite de
# résoudre une adresse tapée en partie sur le seul premier résultat BAN
# (limit=1, cf. geocoder()), qui peut être un faux positif plausible mais
# non voulu par l'utilisateur. Choisi après étude comparative (2026-07-23) :
# Google Places Autocomplete plafonne à 5 (retenu ici après essai à 7,
# jugé trop encombrant à l'écran), le site officiel adresse.data.gouv.fr en
# affiche ~7 sans "voir plus", l'API elle-même recommande 10 par défaut
# (max 50) — à ajuster si l'usage réel le justifie. Réutilisé aussi comme
# nombre de candidats vérifiés pour détecter une adresse ambiguë entre
# plusieurs communes à la soumission (cf. carte_scolaire_tool.py).
SECTEUR_NB_SUGGESTIONS_ADRESSE = 5

# --- Zone nationale (geo_tool.py) ---
# Codes département des DOM-TOM tels que stockés en base — fait administratif
# stable, pas recalculé. Sert à distinguer "France" (tout le pays, DOM-TOM
# inclus) de "France métropolitaine" (DOM-TOM exclus) pour une recherche à
# l'échelle nationale.
DEPARTEMENTS_OUTRE_MER = {
    "971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988",
}
