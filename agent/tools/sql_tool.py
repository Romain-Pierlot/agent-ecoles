"""sql_tool.py — Outil Text-to-SQL pour agent-ecoles (V7 — précision limitée à ville/département, code postal retiré)"""

import sqlite3
import os
import sys
import re
import unicodedata
from difflib import get_close_matches
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import (
    DB_PATH, LLM_MODEL, LLM_MAX_RETRIES, SQL_TIMEOUT_SECONDS,
    Secteur, SecteurSouhaite, SEUIL_CANDIDATS_AVANT_PRECISION, PREFIXES_INSTITUTIONNELS,
    COLONNE_SECTION,
)
from guardrails.sql_safety import valider_sql
from agent.tools.normalisation import normaliser_texte_base

client = OpenAI()

# Liste blanche des colonnes de section utilisables comme critère de filtre
# dans les requêtes déterministes ci-dessous — dérivée de COLONNE_SECTION
# (config.py, source unique) plutôt que retapée ici : ajouter une section
# ne demande de toucher qu'un seul endroit, jamais deux listes à resynchroniser
# à la main. Jamais un nom de colonne construit dynamiquement à partir d'un
# texte utilisateur non vérifié.
COLONNES_SECTION_VALIDES = set(COLONNE_SECTION.values())


def _filtre_section_sql(colonne_section_filtre: str = None) -> tuple[str, str]:
    """
    Construit la clause SQL de filtre `AND e.{colonne} = 1` après validation
    contre la liste blanche — factorisé une seule fois, utilisé par les 3
    fonctions déterministes ci-dessous (rechercher_top_par_secteur,
    rechercher_etablissements_par_uai, calculer_moyenne_etablissements), qui
    dupliquaient chacune la même validation et la même construction de
    chaîne. Un nouveau critère de filtre binaire (ex: futur "restauration",
    "hebergement") s'ajoute en étendant COLONNE_SECTION/COLONNES_SECTION_VALIDES,
    pas en recopiant cette logique dans une 4e fonction.

    Retourne (clause_sql, erreur) : clause_sql vide et erreur=None si
    colonne_section_filtre est None (aucun filtre demandé) ; erreur non-None
    si la colonne demandée n'appartient pas à la liste blanche (jamais de
    clause construite sur une valeur non vérifiée).
    """
    if colonne_section_filtre is None:
        return "", None
    if colonne_section_filtre not in COLONNES_SECTION_VALIDES:
        return "", f"colonne de section invalide : {colonne_section_filtre}"
    return f" AND e.{colonne_section_filtre} = 1", None

SCHEMA_PROMPT = """
Tu as accès à une base SQLite avec 9 tables sur les établissements scolaires français.

TABLE etablissements — 1 ligne par établissement
  uai TEXT PRIMARY KEY
  nom TEXT
  type_etablissement TEXT
  secteur TEXT
  commune TEXT
  code_departement TEXT
  libelle_departement TEXT
  libelle_academie TEXT
  libelle_region TEXT
  latitude REAL
  longitude REAL
  segpa INTEGER
  ulis INTEGER
  section_sport INTEGER
  section_arts INTEGER
  section_cinema INTEGER
  section_theatre INTEGER
  section_internationale INTEGER
  section_europeenne INTEGER
  appartenance_education_prioritaire TEXT

TABLE ips
  uai TEXT FK
  annee_scolaire TEXT
  ips_moyen REAL
  ecart_type_ips REAL
  ips_national REAL
  ips_national_public REAL
  ips_academique REAL
  ips_departemental REAL
  ecart_type_ips_national REAL       -- comparatif mixité, calculé à l'ingestion
  ecart_type_ips_departemental REAL

TABLE ivac
  uai TEXT FK
  session TEXT
  brevet_nb_candidats_general INTEGER
  brevet_taux_reussite_general REAL
  brevet_va_taux_reussite_general REAL
  brevet_note_ecrit_general REAL
  brevet_va_note_ecrit_general REAL
  taux_acces_6eme_3eme REAL
  nb_mentions_ab INTEGER
  nb_mentions_b INTEGER
  nb_mentions_tb INTEGER
  nb_mentions_total INTEGER
  brevet_taux_reussite_national REAL       -- moyenne nationale de la session, calculée à l'ingestion
  brevet_note_ecrit_national REAL
  brevet_taux_reussite_departemental REAL  -- moyenne du département de l'établissement, même session
  brevet_note_ecrit_departemental REAL

TABLE scores
  uai TEXT FK
  session TEXT
  score_principal REAL   -- jamais affiché : sert au tri "meilleur(s) collège(s)"
  score_resultats REAL   -- jamais affiché : sert au tri "meilleurs résultats" (résultats bruts seuls)
  notation TEXT           -- A+/A/A-/B+/B : c'est ÇA qui s'affiche, jamais score_principal ni score_resultats
  badge_va TEXT

TABLE referentiel_temporel
  session_ivac TEXT PRIMARY KEY
  annee_scolaire_ips TEXT
  libelle_affichage TEXT

TABLE zones_academiques — 1 ligne par académie (rattachement via etablissements.code_academie)
  code_academie TEXT PRIMARY KEY
  libelle_academie TEXT
  zone TEXT  -- 'A'/'B'/'C', NULL pour la Corse et les académies d'outre-mer

TABLE langues_offertes — 0 à N lignes par établissement (uniquement collèges, ~78% de couverture)
  uai TEXT FK
  type_enseignement TEXT  -- 'LV1'/'LV2'/'LCA' — pas de niveau (6e/5e) ni de bilangue dans cette donnée
  langue TEXT

TABLE sections_sportives — 0 à N lignes par établissement (uniquement collèges, ~25% de couverture)
  uai TEXT FK
  sport TEXT  -- ex: 'Football', 'Escalade', 'Karate' — sport précis de la section sportive

TABLE vacances_scolaires — calendrier des vacances par zone et par année scolaire
  annee_scolaire TEXT
  zone TEXT           -- 'A'/'B'/'C', ou 'TOUTES' pour une période commune aux 3 zones
  periode TEXT         -- 'Toussaint'/'Noël'/'Hiver'/'Printemps'/'Prérentrée'/'Rentrée'/'Fin d'année scolaire'
  type_periode TEXT    -- 'vacances' (date_fin renseignée) ou 'jalon' (date ponctuelle, date_fin NULL)
  date_debut TEXT       -- ISO 'YYYY-MM-DD'
  date_fin TEXT         -- ISO, NULL pour un jalon

RÈGLES IMPORTANTES :
- Toujours filtrer WHERE type_etablissement = 'Collège' sauf demande explicite sur les lycées
- Session : TOUJOURS filtrer sur une session, même si la question ne précise
  aucune année — ne JAMAIS laisser une requête sans filtre de session
  (mélangerait plusieurs années incomparables entre elles, notamment pour
  une moyenne). Par défaut, une seule session, la plus récente :
  s.session = (SELECT MAX(session) FROM scores) — n'écris JAMAIS une année
  en dur (elle se périmera). Seule exception : si la question demande
  explicitement plusieurs années ou une évolution historique, utilise
  s.session IN (...) sur les sessions concernées.
- La commune est en MAJUSCULES — utiliser UPPER() ou LIKE '%LYON%'
- Pour filtrer par nom d'établissement, utilise TOUJOURS LIKE '%...%' sur le
  nom distinctif (sans le préfixe institutionnel "Collège"/"Collège privé"),
  JAMAIS une égalité exacte (=) ni IN — les noms en base incluent ce préfixe,
  qu'une correspondance exacte manquerait. Pour plusieurs noms, combine
  plusieurs conditions LIKE avec OR.
  Exemple correct   : WHERE (e.nom LIKE '%Chevreul%' OR e.nom LIKE '%Louise Michel%')
  Exemple incorrect : WHERE e.nom IN ('Chevreul', 'Louise Michel')
- La VA peut être NULL — toujours IS NOT NULL si filtrée
- segpa/ulis/section_* sont des colonnes binaires (1 = oui, 0 = non, jamais
  NULL) — pour filtrer sur leur présence, teste TOUJOURS `= 1`, jamais
  `IS NOT NULL` (qui vaut vrai pour toutes les lignes, y compris celles à 0,
  et ne filtre donc rien du tout)
- La notation (colonne notation, ex: A+/A/A-/B+/B) est ce qui s'affiche à
  l'utilisateur — TOUJOURS l'inclure dans le SELECT dès que la table scores
  est jointe, à côté du badge_va. Ne JAMAIS afficher score_principal ni
  score_resultats tels quels (ce sont des chiffres internes jamais montrés,
  ils ne servent qu'au tri) — inclus dans le SELECT uniquement s'ils sont
  nécessaires au tri demandé, jamais pour être lus par l'utilisateur.
- TOUJOURS inclure e.uai dans le SELECT (nécessaire pour la traçabilité en aval)
- TOUJOURS inclure e.secteur dans le SELECT dès que la requête retourne des
  lignes d'établissement (pas une agrégation) — nécessaire à l'avertissement
  sur la sélection à l'entrée du privé, affiché en aval à partir de ce champ
- Synonymes : école/établissement/collège → etablissements, résultats/notes → ivac,
  social/milieu → ips_moyen, section arts/option arts → section_arts, section
  cinéma/option cinéma/audiovisuel → section_cinema, section théâtre/option
  théâtre/art dramatique → section_theatre, langues/LV1/LV2/latin/grec →
  langues_offertes, quel sport/section sport précise → sections_sportives,
  zone de vacances/quand sont les vacances → zones_academiques JOIN
  vacances_scolaires
- Pour "quand sont les prochaines vacances d'un établissement" : joindre
  etablissements → zones_academiques ON code_academie, puis filtrer
  vacances_scolaires WHERE type_periode = 'vacances' AND zone IN (za.zone,
  'TOUTES') AND date_debut >= date('now') ORDER BY date_debut LIMIT 1. Si
  za.zone est NULL (Corse, outre-mer), dire que cette académie fixe son
  calendrier indépendamment plutôt que de deviner une zone.
- DEUX critères de tri distincts selon la formulation exacte de la question —
  ne jamais les confondre :
  1. "quels sont les meilleurs/pires collèges", "classe les collèges",
     "meilleur collège" (sans qualificatif) → ORDER BY s.score_principal
     DESC (ou ASC pour "pires"/"moins bons"). C'est le tri par défaut, y
     compris quand la question mentionne la VA comme critère ("le meilleur
     collège en tenant compte de la valeur ajoutée") — la VA fait déjà
     partie du calcul de score_principal, elle n'est jamais un second
     critère de tri ajouté par-dessus.
  2. "quels collèges ont les meilleurs/moins bons résultats", "les meilleurs
     résultats" (le mot "résultats" est explicitement présent) → ORDER BY
     s.score_resultats DESC (ou ASC). Ce tri ignore la valeur ajoutée,
     uniquement taux de réussite + note écrite.
  Correct   : "meilleurs collèges à Lyon" → ORDER BY s.score_principal DESC
  Correct   : "collèges avec les meilleurs résultats à Lyon" → ORDER BY s.score_resultats DESC
  Incorrect : utiliser score_resultats pour "meilleurs collèges" (sans le mot
              "résultats"), ou score_principal pour "meilleurs résultats"
  Incorrect : ORDER BY v.brevet_va_taux_reussite_general DESC (la VA n'est
              jamais un critère de tri direct, seulement une composante de
              score_principal)

EXEMPLES :
Question: "Meilleurs collèges publics à Lyon"
SQL: SELECT e.uai, e.nom, e.commune, e.secteur, s.notation, s.badge_va,
            v.brevet_taux_reussite_general, v.brevet_note_ecrit_general,
            v.brevet_va_taux_reussite_general, v.brevet_va_note_ecrit_general
     FROM etablissements e
     JOIN scores s ON e.uai = s.uai
     JOIN ivac v ON e.uai = v.uai AND v.session = s.session
     WHERE e.commune LIKE '%LYON%' AND e.secteur = 'Public'
       AND e.type_etablissement = 'Collège' AND s.session = (SELECT MAX(session) FROM scores)
     ORDER BY s.score_principal DESC LIMIT 10;

Question: "Quels collèges de Lyon ont les meilleurs résultats ?"
SQL: SELECT e.uai, e.nom, e.commune, e.secteur, s.notation, s.badge_va,
            v.brevet_taux_reussite_general, v.brevet_note_ecrit_general,
            v.brevet_va_taux_reussite_general, v.brevet_va_note_ecrit_general
     FROM etablissements e
     JOIN scores s ON e.uai = s.uai
     JOIN ivac v ON e.uai = v.uai AND v.session = s.session
     WHERE e.commune LIKE '%LYON%'
       AND e.type_etablissement = 'Collège' AND s.session = (SELECT MAX(session) FROM scores)
     ORDER BY s.score_resultats DESC LIMIT 10;

TOUJOURS inclure notation, badge_va, brevet_va_taux_reussite_general et
brevet_va_note_ecrit_general dans le SELECT quand la table scores/ivac est
jointe — la valeur ajoutée est une information clé pour l'utilisateur final.
"""


def generer_sql(question: str, historique_erreurs: list = None, uai_filtre: list = None) -> str:
    contrainte_uai = ""
    if uai_filtre:
        # IMPORTANT : le LLM ne recopie JAMAIS la liste d'UAI lui-même — risque
        # de troncature (max_tokens) ou d'erreur de recopie sur de longues listes.
        # Il écrit un placeholder littéral, remplacé en Python après coup.
        contrainte_uai = """
CONTRAINTE OBLIGATOIRE : la requête doit systématiquement inclure
WHERE e.uai IN ({UAI_LIST})
Écris EXACTEMENT le texte {UAI_LIST} tel quel (avec les accolades) — ne
remplace pas ce texte par une liste d'UAI, ce sera fait automatiquement après.
Ces établissements ont déjà été présélectionnés — ne refais pas de filtre
par commune ou par nom."""

    messages = [
        {"role": "system", "content": f"""Tu es un expert SQL spécialisé dans les données éducatives françaises.

{SCHEMA_PROMPT}
{contrainte_uai}

INSTRUCTIONS :
- Génère UNIQUEMENT la requête SQL, sans explication ni markdown
- La requête doit être valide pour SQLite
- Termine toujours par un point-virgule
- Maximum 50 résultats sauf si explicitement demandé"""},
        {"role": "user", "content": question}
    ]

    if historique_erreurs:
        for erreur in historique_erreurs:
            messages.append({"role": "assistant", "content": erreur["sql_tente"]})
            messages.append({"role": "user", "content": f"Cette requête a échoué avec l'erreur : {erreur['erreur']}. Corrige-la."})

    response = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=0,
        max_tokens=800, timeout=SQL_TIMEOUT_SECONDS
    )
    sql = response.choices[0].message.content.strip()
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    sql = sql.strip()

    # Substitution du placeholder par la vraie liste d'UAI — fait par le code,
    # jamais par le LLM (évite toute recopie fragile de longues listes)
    if uai_filtre and "{UAI_LIST}" in sql:
        liste_uai_sql = ", ".join(f"'{uai}'" for uai in uai_filtre)
        sql = sql.replace("{UAI_LIST}", liste_uai_sql)

    return sql


def executer_sql(sql: str) -> list[dict]:
    """
    Connexion en LECTURE SEULE (mode URI SQLite `?mode=ro`) : garantit
    qu'aucune écriture ne passe, quoi que la requête générée par le LLM
    contienne — indépendamment du validateur (guardrails/sql_safety.py),
    qui reste la protection principale mais ne doit pas être le seul filet.
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def _sessions_disponibles() -> list[str]:
    """
    Sessions réellement présentes en base, triées par ordre croissant —
    calculé en Python (déterministe), pas par le LLM Text-to-SQL. Permet à
    l'appelant (agent, synthèse) de signaler explicitement un écart entre
    une demande ("les 10 dernières années") et ce qui existe vraiment (ex:
    seulement 4 sessions), plutôt que de présenter silencieusement une
    moyenne calculée sur moins d'années que demandé.
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT DISTINCT session FROM scores ORDER BY session").fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def recherche_sql(question: str, uai_filtre: list = None) -> dict:
    """
    Retourne : {success, question, sql_genere, resultats, nb_resultats,
    sessions_disponibles, session_utilisee, error, tentatives}

    session_utilisee : calculé déterministiquement (MAX des sessions_disponibles),
    PAS extrait du SQL généré par le LLM. Testé en pratique (S8.23) : demander
    au Text-to-SQL d'inclure s.session dans son SELECT (règle de prompt) n'est
    pas suivi de façon fiable (0/4 essais) — contrairement à d'autres règles
    de ce prompt. Plutôt que de dépendre de cette fiabilité, ce champ est
    calculé à côté, indépendamment de ce que le SQL généré sélectionne
    réellement, pour donner à l'appelant (agent ReAct notamment) une donnée
    fiable sur laquelle fonder une affirmation de méthodologie — évite qu'il
    en invente une (ex: "basé sur les 3 dernières années") faute d'information.
    """
    historique_erreurs = []
    for tentative in range(1, LLM_MAX_RETRIES + 2):
        sql = generer_sql(question, historique_erreurs if historique_erreurs else None, uai_filtre)
        # Guardrail (cf. guardrails/sql_safety.py) : validation AVANT exécution
        # — une requête rejetée est réinjectée dans la boucle de retry
        # existante, exactement comme une erreur SQLite classique.
        valide, erreur_validation = valider_sql(sql)
        if not valide:
            historique_erreurs.append({"sql_tente": sql, "erreur": erreur_validation})
            if tentative > LLM_MAX_RETRIES:
                return {
                    "success": False, "question": question, "sql_genere": sql,
                    "resultats": [], "nb_resultats": 0,
                    "error": erreur_validation, "tentatives": tentative
                }
            continue
        try:
            resultats = executer_sql(sql)
            sessions = _sessions_disponibles()
            return {
                "success": True, "question": question, "sql_genere": sql,
                "resultats": resultats, "nb_resultats": len(resultats),
                "sessions_disponibles": sessions,
                "session_utilisee": max(sessions) if sessions else None,
                "error": None, "tentatives": tentative
            }
        except Exception as e:
            erreur_msg = str(e)
            historique_erreurs.append({"sql_tente": sql, "erreur": erreur_msg})
            if tentative > LLM_MAX_RETRIES:
                return {
                    "success": False, "question": question, "sql_genere": sql,
                    "resultats": [], "nb_resultats": 0,
                    "error": erreur_msg, "tentatives": tentative
                }
    return {
        "success": False, "question": question, "sql_genere": "",
        "resultats": [], "nb_resultats": 0,
        "error": "Nombre maximum de tentatives atteint", "tentatives": LLM_MAX_RETRIES + 1
    }


def rechercher_top_par_secteur(uai_filtre: list[str], n: int = 10, type_etablissement: str = "Collège", ordre: str = "DESC", inclure_mentions: bool = False, colonne_section_filtre: str = None, critere_tri: str = "global") -> dict:
    """
    Retourne séparément les n meilleurs (ou pires, cf. ordre) établissements
    publics et privés parmi une liste d'UAI déjà présélectionnée (ex: par
    geo_tool), triés par score_principal ou score_resultats (cf. critere_tri).

    critere_tri="global" (défaut) : tri sur score_principal — "meilleurs
    collèges", classement général (résultats bruts + valeur ajoutée).
    critere_tri="resultats" : tri sur score_resultats — uniquement quand la
    question mentionne explicitement "les résultats" (résultats bruts seuls,
    sans VA). Valeur dérivée de state["critere_tri_souhaite"] (extrait par le
    router, cf. config.CritereTriSouhaite), jamais construite depuis un texte
    utilisateur non vérifié — validée ci-dessous contre les 2 seules valeurs
    possibles avant toute interpolation dans le SQL.

    Requête SQL déterministe, AUCUN appel LLM : une fois qu'on sait que
    l'utilisateur n'a précisé aucun secteur (cf. state["secteur_souhaite"]
    extrait par le router), "prendre le top n de chaque secteur" est une
    règle fixe, pas une tâche d'interprétation de texte libre — le Text-to-SQL
    général (recherche_sql) n'a pas sa place ici.

    ordre="DESC" (défaut, meilleurs) ou "ASC" (pires) — jamais interpolé
    depuis une chaîne fournie par l'appelant sans validation, pour éviter
    toute injection SQL sur cette clause (cf. validation stricte ci-dessous).

    colonne_section_filtre=None (défaut) : si fourni (ex: "section_theatre"),
    ajoute un filtre `= 1` sur cette colonne — utilisé quand state["section_souhaitee"]
    (extrait par le router) demande un critère de section en plus de la zone.
    Doit appartenir à COLONNES_SECTION_VALIDES (jamais un nom de colonne
    construit depuis un texte utilisateur non vérifié).

    inclure_mentions=False (défaut) : colonnes de mention absentes des lignes
    retournées, donc absentes de l'affichage (cf. _generer_tableau_depuis_lignes,
    conditionné à leur présence — même principe que la colonne Session).
    True seulement quand state["mentions_demandees"] (extrait par le router)
    l'indique — évite d'encombrer l'affichage normal d'une donnée non demandée.

    La session utilisée est la plus récente disponible dans la table scores,
    déterminée dynamiquement (jamais codée en dur, pour ne pas se périmer
    quand une nouvelle session de données arrive).

    Retourne : {
        "success": bool,
        "session_utilisee": str | None,
        "public": [ {uai, nom, commune, secteur, notation, badge_va,
                     brevet_taux_reussite_general, brevet_note_ecrit_general,
                     brevet_va_taux_reussite_general, brevet_va_note_ecrit_general,
                     [+ brevet_nb_candidats_general, nb_mentions_b, nb_mentions_tb si inclure_mentions]}, ... ],
        "prive": [ ... même structure ... ],
        "error": str | None
    }
    """
    if not uai_filtre:
        return {"success": True, "session_utilisee": None, "public": [], "prive": [], "error": None}
    if ordre not in ("DESC", "ASC"):
        return {"success": False, "session_utilisee": None, "public": [], "prive": [], "error": f"ordre invalide : {ordre}"}
    if critere_tri not in ("global", "resultats"):
        return {"success": False, "session_utilisee": None, "public": [], "prive": [], "error": f"critere_tri invalide : {critere_tri}"}
    colonne_tri = "score_principal" if critere_tri == "global" else "score_resultats"
    filtre_section_sql, erreur_section = _filtre_section_sql(colonne_section_filtre)
    if erreur_section:
        return {"success": False, "session_utilisee": None, "public": [], "prive": [], "error": erreur_section}

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    colonnes_mentions = ", v.brevet_nb_candidats_general, v.nb_mentions_b, v.nb_mentions_tb" if inclure_mentions else ""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
            if session is None:
                return {"success": True, "session_utilisee": None, "public": [], "prive": [], "error": None}

            placeholders = ",".join("?" for _ in uai_filtre)
            resultats_par_secteur = {}
            for secteur_db, cle in ((Secteur.PUBLIC, SecteurSouhaite.PUBLIC), (Secteur.PRIVE, SecteurSouhaite.PRIVE)):
                rows = conn.execute(f"""
                    SELECT e.uai, e.nom, e.commune, e.secteur, s.notation, s.badge_va,
                           v.brevet_taux_reussite_general, v.brevet_note_ecrit_general,
                           v.brevet_va_taux_reussite_general, v.brevet_va_note_ecrit_general
                           {colonnes_mentions}
                    FROM etablissements e
                    JOIN scores s ON e.uai = s.uai
                    JOIN ivac v ON e.uai = v.uai AND v.session = s.session
                    WHERE e.uai IN ({placeholders})
                      AND e.secteur = ?
                      AND e.type_etablissement = ?
                      AND s.session = ?
                      {filtre_section_sql}
                    ORDER BY s.{colonne_tri} {ordre}
                    LIMIT ?
                """, (*uai_filtre, secteur_db.value, type_etablissement, session, n)).fetchall()
                resultats_par_secteur[cle.value] = [dict(row) for row in rows]
        finally:
            conn.close()
        return {"success": True, "session_utilisee": session, "error": None, **resultats_par_secteur}
    except Exception as e:
        return {"success": False, "session_utilisee": None, "public": [], "prive": [], "error": str(e)}


def rechercher_etablissements_par_uai(uai_filtre: list[str], type_etablissement: str = "Collège", inclure_mentions: bool = False, colonne_section_filtre: str = None) -> dict:
    """
    Retourne le tableau standard (score, VA, taux de réussite, note écrit —
    valeurs brutes) pour une liste d'établissements déjà résolue par nom
    (cf. rechercher_etablissements_par_nom). Requête SQL déterministe,
    AUCUN appel LLM.

    Remplace l'usage de recherche_sql() (Text-to-SQL général) pour ce cas :
    piloté par le texte brut de la question, il régénère un jeu de colonnes
    différent selon le phrasé exact du tour courant (ex: "leur valeur
    ajoutée est-elle fiable ?" faisait ressortir les colonnes delta VA au
    lieu des valeurs brutes attendues par le gabarit d'affichage) — cassant
    le tableau dès qu'une relance ne répète pas les mots de la question
    initiale (mémoire de conversation générale).

    Les 6 colonnes de section (section_sport, section_arts, section_cinema,
    section_theatre, section_internationale, section_europeenne) sont
    TOUJOURS incluses dans le SELECT, coût négligeable pour le petit nombre
    de lignes concerné ici (établissement(s) déjà résolu(s) par nom, ou
    ville d'une zone). Ça permet de répondre à une question de suivi sur
    n'importe laquelle de ces sections sans nouvel appel SQL ciblé — cf.
    discussion produit sur l'entonnoir zone -> établissement nommé.

    colonne_section_filtre=None (défaut) : aucun filtre, TOUS les
    établissements de uai_filtre sont retournés (avec leurs colonnes de
    section pour affichage) — comportement voulu pour un établissement
    nommé : "Ampère a-t-il une section théâtre ?" doit répondre Oui/Non,
    jamais faire disparaître Ampère du résultat s'il ne l'a pas. Si fourni
    (cas zone, ex: "ville" d'un split ville+environs), ajoute un filtre
    `= 1` sur cette colonne — doit appartenir à COLONNES_SECTION_VALIDES.

    inclure_mentions=False (défaut) : colonnes de mention absentes des lignes
    retournées, donc absentes de l'affichage (cf. _generer_tableau_depuis_lignes,
    conditionné à leur présence). True seulement quand state["mentions_demandees"]
    (extrait par le router) l'indique.

    Retourne : {
        "success": bool,
        "session_utilisee": str | None,
        "resultats": [ {uai, nom, commune, secteur, notation, badge_va,
                         brevet_taux_reussite_general, brevet_note_ecrit_general,
                         section_sport, section_arts, section_cinema, section_theatre,
                         section_internationale, section_europeenne,
                         [+ brevet_nb_candidats_general, nb_mentions_b, nb_mentions_tb si inclure_mentions]}, ... ],
        "error": str | None
    }
    """
    if not uai_filtre:
        return {"success": True, "session_utilisee": None, "resultats": [], "error": None}
    filtre_section_sql, erreur_section = _filtre_section_sql(colonne_section_filtre)
    if erreur_section:
        return {"success": False, "session_utilisee": None, "resultats": [], "error": erreur_section}

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    colonnes_mentions = ", v.brevet_nb_candidats_general, v.nb_mentions_b, v.nb_mentions_tb" if inclure_mentions else ""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
            if session is None:
                return {"success": True, "session_utilisee": None, "resultats": [], "error": None}

            placeholders = ",".join("?" for _ in uai_filtre)
            rows = conn.execute(f"""
                SELECT e.uai, e.nom, e.commune, e.secteur, s.notation, s.badge_va,
                       v.brevet_taux_reussite_general, v.brevet_note_ecrit_general,
                       e.section_sport, e.section_arts, e.section_cinema, e.section_theatre,
                       e.section_internationale, e.section_europeenne
                       {colonnes_mentions}
                FROM etablissements e
                JOIN scores s ON e.uai = s.uai
                JOIN ivac v ON e.uai = v.uai AND v.session = s.session
                WHERE e.uai IN ({placeholders})
                  AND e.type_etablissement = ?
                  AND s.session = ?
                  {filtre_section_sql}
                ORDER BY s.score_principal DESC
            """, (*uai_filtre, type_etablissement, session)).fetchall()
        finally:
            conn.close()
        return {"success": True, "session_utilisee": session, "resultats": [dict(row) for row in rows], "error": None}
    except Exception as e:
        return {"success": False, "session_utilisee": None, "resultats": [], "error": str(e)}


def calculer_moyenne_etablissements(uai_filtre: list[str], type_etablissement: str = "Collège", inclure_mentions: bool = False, colonne_section_filtre: str = None, critere_tri: str = "global") -> dict:
    """
    Calcule la moyenne du score/taux/note pour un ensemble d'établissements
    déjà présélectionné (ex: par geo_tool) — moyenne globale (tous secteurs
    confondus) ET détail par secteur (public/privé), calculées dans tous les
    cas pour laisser l'affichage choisir quoi montrer selon que le secteur
    est précisé ou non dans la question (pas de tableau détaillé par
    établissement ici : c'est une agrégation statistique, pas une liste).

    Requête SQL déterministe, AUCUN appel LLM. Session la plus récente
    disponible, déterminée dynamiquement (jamais codée en dur).

    colonne_section_filtre=None (défaut) : si fourni (ex: "section_theatre"),
    restreint la moyenne aux établissements ayant cette section — utilisé
    quand state["section_souhaitee"] (extrait par le router) demande un
    critère de section en plus de la zone (ex: "la moyenne des collèges
    avec section sport à Lyon"). Doit appartenir à COLONNES_SECTION_VALIDES.

    inclure_mentions=False (défaut) : taux_b_moyen/taux_tb_moyen absents du
    résultat, donc absents de l'affichage (cf. _formater_stats_moyenne,
    conditionné à leur présence). True seulement quand state["mentions_demandees"]
    (extrait par le router) l'indique.

    critere_tri="global" (défaut) : la moyenne "score_moyen" porte sur
    score_principal. critere_tri="resultats" : porte sur score_resultats —
    quand la question demande explicitement "la moyenne des résultats" (cf.
    config.CritereTriSouhaite). Le nom de la clé retournée reste "score_moyen"
    dans les deux cas, le libellé affiché est choisi en aval selon ce qui a
    été demandé.

    Retourne : {
        "success": bool,
        "session_utilisee": str | None,
        "global": {"nb_etablissements": int, "score_moyen": float, "taux_moyen": float, "note_moyenne": float,
                   [+ "taux_b_moyen": float, "taux_tb_moyen": float si inclure_mentions]} | None,
        "public": { ... même structure ... } | None,
        "prive": { ... même structure ... } | None,
        "error": str | None
    }
    """
    if not uai_filtre:
        return {"success": True, "session_utilisee": None, "global": None, "public": None, "prive": None, "error": None}
    if critere_tri not in ("global", "resultats"):
        return {"success": False, "session_utilisee": None, "global": None, "public": None, "prive": None, "error": f"critere_tri invalide : {critere_tri}"}
    colonne_tri = "score_principal" if critere_tri == "global" else "score_resultats"
    filtre_section_sql, erreur_section = _filtre_section_sql(colonne_section_filtre)
    if erreur_section:
        return {"success": False, "session_utilisee": None, "global": None, "public": None, "prive": None, "error": erreur_section}

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    colonnes_mentions = (
        ", AVG(1.0 * v.nb_mentions_b / v.brevet_nb_candidats_general) AS taux_b_moyen,"
        " AVG(1.0 * v.nb_mentions_tb / v.brevet_nb_candidats_general) AS taux_tb_moyen"
    ) if inclure_mentions else ""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
            if session is None:
                return {"success": True, "session_utilisee": None, "global": None, "public": None, "prive": None, "error": None}

            placeholders = ",".join("?" for _ in uai_filtre)

            def _moyenne(secteur_filtre: str = None):
                filtre_secteur_sql = "AND e.secteur = ?" if secteur_filtre else ""
                params = [*uai_filtre, type_etablissement, session]
                if secteur_filtre:
                    params.append(secteur_filtre)
                row = conn.execute(f"""
                    SELECT COUNT(*) AS nb_etablissements, AVG(s.{colonne_tri}) AS score_moyen,
                           AVG(v.brevet_taux_reussite_general) AS taux_moyen,
                           AVG(v.brevet_note_ecrit_general) AS note_moyenne
                           {colonnes_mentions}
                    FROM etablissements e
                    JOIN scores s ON e.uai = s.uai
                    JOIN ivac v ON e.uai = v.uai AND v.session = s.session
                    WHERE e.uai IN ({placeholders})
                      AND e.type_etablissement = ?
                      AND s.session = ?
                      {filtre_secteur_sql}
                      {filtre_section_sql}
                """, params).fetchone()
                if not row or not row["nb_etablissements"]:
                    return None
                return dict(row)

            resultats = {
                "global": _moyenne(),
                "public": _moyenne(Secteur.PUBLIC.value),
                "prive": _moyenne(Secteur.PRIVE.value),
            }
        finally:
            conn.close()
        return {"success": True, "session_utilisee": session, "error": None, **resultats}
    except Exception as e:
        return {"success": False, "session_utilisee": None, "global": None, "public": None, "prive": None, "error": str(e)}


def calculer_evolution_moyenne_zone(uai_filtre: list[str], n_sessions: int = None, type_etablissement: str = "Collège") -> dict:
    """
    Calcule, pour chaque session disponible (ou les n_sessions les plus
    récentes), la moyenne du score/taux/note pour un ensemble d'établissements
    déjà présélectionné (ex: par geo_tool) — moyenne globale ET détail par
    secteur, PAR SESSION.

    Utilisé pour une demande d'évolution/tendance sur une ZONE GÉOGRAPHIQUE
    entière (pas un établissement nommé, cf. obtenir_evolution_etablissements
    pour ce cas précis) : afficher une ligne par établissement par session
    serait illisible sur une zone (ex: 104 établissements x 4 sessions = 416
    lignes). On affiche l'évolution de la MOYENNE, peu importe le nombre
    d'établissements dans la zone — même principe que calculer_moyenne_etablissements
    (S8.18), répété par session au lieu de la seule session la plus récente.

    Requête SQL déterministe, AUCUN appel LLM.

    Retourne : {
        "success": bool,
        "sessions_disponibles": [str, ...],
        "evolution": [ {"session": str, "global": {...}|None, "public": {...}|None, "prive": {...}|None}, ... ],
        "error": str | None
    }
    (chaque bloc global/public/prive a la même structure que dans calculer_moyenne_etablissements)
    """
    if not uai_filtre:
        return {"success": True, "sessions_disponibles": [], "evolution": [], "error": None}

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            toutes_sessions = [
                row["session"] for row in conn.execute("SELECT DISTINCT session FROM scores ORDER BY session")
            ]
            sessions_ciblees = toutes_sessions[-n_sessions:] if n_sessions else toutes_sessions
            placeholders = ",".join("?" for _ in uai_filtre)

            def _moyenne(session, secteur_filtre: str = None):
                filtre_secteur_sql = "AND e.secteur = ?" if secteur_filtre else ""
                params = [*uai_filtre, type_etablissement, session]
                if secteur_filtre:
                    params.append(secteur_filtre)
                row = conn.execute(f"""
                    SELECT COUNT(*) AS nb_etablissements, AVG(s.score_principal) AS score_moyen,
                           AVG(v.brevet_taux_reussite_general) AS taux_moyen,
                           AVG(v.brevet_note_ecrit_general) AS note_moyenne
                    FROM etablissements e
                    JOIN scores s ON e.uai = s.uai
                    JOIN ivac v ON e.uai = v.uai AND v.session = s.session
                    WHERE e.uai IN ({placeholders})
                      AND e.type_etablissement = ?
                      AND s.session = ?
                      {filtre_secteur_sql}
                """, params).fetchone()
                if not row or not row["nb_etablissements"]:
                    return None
                return dict(row)

            evolution = [
                {
                    "session": session,
                    "global": _moyenne(session),
                    "public": _moyenne(session, Secteur.PUBLIC.value),
                    "prive": _moyenne(session, Secteur.PRIVE.value),
                }
                for session in reversed(sessions_ciblees)
            ]
        finally:
            conn.close()
        return {"success": True, "sessions_disponibles": toutes_sessions, "evolution": evolution, "error": None}
    except Exception as e:
        return {"success": False, "sessions_disponibles": [], "evolution": [], "error": str(e)}


def obtenir_evolution_etablissements(uai_filtre: list[str], n_sessions: int = None, type_etablissement: str = "Collège") -> dict:
    """
    Retourne les données chiffrées (score, taux, note, VA) d'une liste
    d'établissements déjà résolue (par nom, cf. rechercher_etablissements_par_nom),
    une ligne par (établissement, session) — utilisé pour une évolution ou
    une moyenne sur plusieurs années.

    Requête SQL déterministe, AUCUN appel LLM : une fois les établissements
    identifiés (state["uai_resolus"]) et le besoin d'évolution détecté
    (state["evolution_demandee"], extrait par le router), récupérer leur
    historique par session est une règle fixe — le Text-to-SQL général
    (recherche_sql) a montré une fragilité réelle sur cette combinaison
    (nom + zone + plusieurs années en une seule requête libre, cf. session 8).

    n_sessions=None -> toutes les sessions disponibles. Sinon, les
    n_sessions les plus récentes.

    Ne calcule pas de moyenne lui-même : retourne les données brutes par
    session, une moyenne se calcule trivialement en Python à partir de ça
    si besoin — pas la peine d'un deuxième chemin SQL pour ça.

    Retourne : {
        "success": bool,
        "sessions_disponibles": [str, ...],
        "resultats": [ {uai, nom, commune, secteur, session, notation,
                         badge_va, brevet_taux_reussite_general,
                         brevet_note_ecrit_general}, ... ],
        "error": str | None
    }
    """
    if not uai_filtre:
        return {"success": True, "sessions_disponibles": [], "resultats": [], "error": None}

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            toutes_sessions = [
                row["session"] for row in conn.execute("SELECT DISTINCT session FROM scores ORDER BY session")
            ]
            sessions_ciblees = toutes_sessions[-n_sessions:] if n_sessions else toutes_sessions

            placeholders_uai = ",".join("?" for _ in uai_filtre)
            placeholders_sessions = ",".join("?" for _ in sessions_ciblees)
            rows = conn.execute(f"""
                SELECT e.uai, e.nom, e.commune, e.secteur, s.session, s.notation, s.badge_va,
                       v.brevet_taux_reussite_general, v.brevet_note_ecrit_general
                FROM etablissements e
                JOIN scores s ON e.uai = s.uai
                JOIN ivac v ON e.uai = v.uai AND v.session = s.session
                WHERE e.uai IN ({placeholders_uai})
                  AND e.type_etablissement = ?
                  AND s.session IN ({placeholders_sessions})
                ORDER BY e.nom, s.session DESC
            """, (*uai_filtre, type_etablissement, *sessions_ciblees)).fetchall()
            resultats = [dict(row) for row in rows]
        finally:
            conn.close()
        return {"success": True, "sessions_disponibles": toutes_sessions, "resultats": resultats, "error": None}
    except Exception as e:
        return {"success": False, "sessions_disponibles": [], "resultats": [], "error": str(e)}


def _normaliser_nom(nom: str) -> str:
    """
    Nettoie un nom d'établissement pour comparaison stricte : minuscules,
    sans accents, sans préfixe institutionnel générique (Collège, Collège
    privé, École, CLG), espaces multiples réduits.

    Objectif : distinguer un vrai homonyme ("Collège Saint-Joseph" ==
    "Collège privé Saint-Joseph" une fois nettoyés) d'un nom composé qui
    contient juste la même chaîne ("Collège Saint-Joseph de Cluny" reste
    différent après nettoyage).
    """
    nom = normaliser_texte_base(nom).strip()
    for prefixe in PREFIXES_INSTITUTIONNELS:
        if nom.startswith(prefixe + " "):
            nom = nom[len(prefixe):].strip()
            break
    return re.sub(r"\s+", " ", nom)


def _normaliser_zone_administrative(nom: str) -> str:
    """
    Normalise un nom de région/département pour comparaison robuste aux
    variantes (tirets/espaces, accents, casse) — "Nord-Pas-de-Calais",
    "nord pas de calais" et "NORD PAS DE CALAIS" doivent être équivalents.
    Différent de _normaliser_nom (établissements) : pas de préfixe
    institutionnel à retirer ici, mais les tirets doivent être traités
    comme des séparateurs de mots, pas conservés tels quels.
    """
    nom = normaliser_texte_base(nom).replace("-", " ").strip()
    return re.sub(r"\s+", " ", nom)


# Zone nationale : "France" (tout le pays, DOM-TOM inclus, aucune condition
# géographique dans la requête) et "France métropolitaine" (DOM-TOM exclus,
# cf. DEPARTEMENTS_OUTRE_MER dans config.py) sont deux zones distinctes,
# pas une seule — une demande explicite de métropole ne doit pas inclure
# les DOM-TOM, et inversement "France" doit tous les inclure.
ZONES_NATIONALES = {
    "france": "national",
    "france metropolitaine": "national_metropole",
    "metropole": "national_metropole",
}

# Noms de régions françaises d'avant la réforme territoriale de 2016,
# encore courants dans le langage courant — mappés vers le nom de la
# région actuelle telle que stockée en base. Fait historique stable (pas
# de nouvelle fusion prévue), donc figé en dur plutôt que recalculé.
REGIONS_HERITEES = {
    "midi pyrenees": "Occitanie",
    "languedoc roussillon": "Occitanie",
    "nord pas de calais": "Hauts-de-France",
    "picardie": "Hauts-de-France",
    "champagne ardenne": "Grand Est",
    "lorraine": "Grand Est",
    "alsace": "Grand Est",
    "aquitaine": "Nouvelle-Aquitaine",
    "limousin": "Nouvelle-Aquitaine",
    "poitou charentes": "Nouvelle-Aquitaine",
    "basse normandie": "Normandie",
    "haute normandie": "Normandie",
    "bourgogne": "Bourgogne-Franche-Comté",
    "franche comte": "Bourgogne-Franche-Comté",
    "rhone alpes": "Auvergne-Rhône-Alpes",
    "auvergne": "Auvergne-Rhône-Alpes",
}


def resoudre_zone_administrative(nom_zone: str) -> dict:
    """
    Détermine si nom_zone désigne une région, un département, ou la France
    entière (nom actuel, nom d'avant la réforme de 2016, ou faute de frappe
    légère) plutôt qu'une ville/adresse — évite de laisser l'API de
    géocodage externe mal interpréter un nom de région (ex: "Bretagne"
    résolu à tort vers une rue à Denain, cf. S8.26) en la contournant
    complètement pour ce cas, au profit d'une requête directe sur nos
    propres données.

    Ensemble de comparaison volontairement petit (~30 noms au total,
    régions + départements) : les noms de régions/départements changent
    extrêmement rarement, contrairement aux noms d'établissements — permet
    une tolérance aux fautes de frappe fiable (plus proche voisin) sans le
    risque de faux positifs qu'aurait la même approche sur un ensemble de
    plusieurs milliers de noms.

    Retourne : {"type": "region"|"departement"|"national"|"national_metropole"|None, "valeur": str|None}
    "valeur" est toujours le nom/code officiel tel que stocké en base
    (libelle_region ou code_departement), jamais le texte brut saisi — sauf
    pour "national"/"national_metropole", où aucune valeur unique n'a de
    sens (valeur=None, cf. ZONES_NATIONALES).
    """
    nom_normalise = _normaliser_zone_administrative(nom_zone)

    if nom_normalise in ZONES_NATIONALES:
        type_national = ZONES_NATIONALES[nom_normalise]
        libelle = "France métropolitaine" if type_national == "national_metropole" else "France"
        return {"type": type_national, "valeur": None, "libelle": libelle}

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    try:
        regions = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT libelle_region FROM etablissements WHERE libelle_region IS NOT NULL"
            )
        ]
        departements = conn.execute(
            "SELECT DISTINCT code_departement, libelle_departement FROM etablissements "
            "WHERE code_departement IS NOT NULL AND libelle_departement IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()

    regions_norm = {_normaliser_zone_administrative(r): r for r in regions}
    departements_norm_par_libelle = {_normaliser_zone_administrative(lib): code for code, lib in departements}
    departements_norm_par_code = {code.lower(): code for code, _ in departements}
    code_vers_libelle = {code: lib for code, lib in departements}

    def _resultat_departement(code):
        return {"type": "departement", "valeur": code, "libelle": code_vers_libelle.get(code, code)}

    if nom_normalise in regions_norm:
        return {"type": "region", "valeur": regions_norm[nom_normalise], "libelle": regions_norm[nom_normalise]}
    if nom_normalise in departements_norm_par_libelle:
        return _resultat_departement(departements_norm_par_libelle[nom_normalise])
    if nom_normalise in departements_norm_par_code:
        return _resultat_departement(departements_norm_par_code[nom_normalise])
    if nom_normalise in REGIONS_HERITEES:
        region = REGIONS_HERITEES[nom_normalise]
        return {"type": "region", "valeur": region, "libelle": region}

    tous_les_noms_connus = (
        list(regions_norm.keys()) + list(departements_norm_par_libelle.keys()) + list(REGIONS_HERITEES.keys())
    )
    proches = get_close_matches(nom_normalise, tous_les_noms_connus, n=1, cutoff=0.8)
    if proches:
        trouve = proches[0]
        if trouve in regions_norm:
            return {"type": "region", "valeur": regions_norm[trouve], "libelle": regions_norm[trouve]}
        if trouve in departements_norm_par_libelle:
            return _resultat_departement(departements_norm_par_libelle[trouve])
        if trouve in REGIONS_HERITEES:
            region = REGIONS_HERITEES[trouve]
            return {"type": "region", "valeur": region, "libelle": region}

    return {"type": None, "valeur": None, "libelle": None}


def _retirer_prefixe_recherche(nom: str) -> str:
    """
    Retire un préfixe institutionnel générique (Collège, Collège privé,
    École, CLG) en tête du nom recherché, sans toucher aux accents ni à la
    casse du reste du texte — la recherche SQL (LIKE) doit rester capable
    de retrouver les noms réels en base, qui gardent leurs accents.

    Corrige un cas réel observé : le LLM du router extrait parfois le nom
    en gardant le mot "collège" (ex: "collège Saint-Joseph" au lieu de
    "Saint-Joseph"), ce qui empêchait la recherche LIKE de retrouver les
    établissements "Collège privé X" (le mot "privé" casse la continuité
    de la sous-chaîne recherchée).
    """
    nom = nom.strip()
    nom_comparable = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode("ascii").lower()
    for prefixe in PREFIXES_INSTITUTIONNELS:
        if nom_comparable.startswith(prefixe + " "):
            return nom[len(prefixe):].strip()
    return nom


def rechercher_etablissements_par_nom(noms: list[str], type_etablissement: str = "Collège") -> dict:
    """
    Résout une liste de noms d'établissements en candidats potentiels.

    Lookup SQL direct (LIKE), AUCUN appel LLM : trouver les établissements
    correspondant à un nom donné est une recherche déterministe, pas une
    tâche d'interprétation de texte libre (cf. principe templating vs LLM).

    Exclut les SEGPA/sections rattachées (nom contient "Section d'enseignement"
    ou "SEGPA") — ce sont des sous-structures internes à un collège, pas des
    établissements comparables entre eux pour un parent qui compare deux
    collèges.

    Le préfixe institutionnel du nom recherché (Collège/Collège privé/École/
    CLG) est retiré avant la recherche (cf. _retirer_prefixe_recherche) —
    évite que la recherche dépende de si le LLM a gardé ou non ce mot en
    l'extrayant de la question.

    Le LIKE SQL sert de filtre large (recall) ; un filtrage Python en sortie
    ne garde que les candidats dont le nom nettoyé (cf. _normaliser_nom)
    correspond exactement au nom recherché nettoyé — élimine les noms
    composés qui contiennent la chaîne recherchée sans être un homonyme réel
    (ex: recherche "Saint-Joseph" ne doit pas remonter "Saint-Joseph de Cluny").

    Retourne : {
        "success": bool,
        "resultats": { nom_recherche: [ {uai, nom, commune, code_departement, secteur}, ... ] },
        "error": str | None
    }
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    resultats = {}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            for nom in noms:
                nom_recherche = _retirer_prefixe_recherche(nom)
                rows = conn.execute("""
                    SELECT uai, nom, commune, code_departement, secteur
                    FROM etablissements
                    WHERE nom LIKE ?
                      AND type_etablissement = ?
                      AND nom NOT LIKE '%Section d%'
                      AND nom NOT LIKE '%SEGPA%'
                    ORDER BY nom
                """, (f"%{nom_recherche}%", type_etablissement)).fetchall()
                nom_cherche_normalise = _normaliser_nom(nom)
                resultats[nom] = [
                    dict(row) for row in rows
                    if _normaliser_nom(row["nom"]) == nom_cherche_normalise
                ]
        finally:
            conn.close()
        return {"success": True, "resultats": resultats, "error": None}
    except Exception as e:
        return {"success": False, "resultats": {}, "error": str(e)}


def interpreter_precision(saisie: str) -> dict:
    """
    Détermine le type de précision saisie par l'utilisateur, sans appel LLM —
    simple règle de format. Seulement 2 formats acceptés (V0, décision
    volontairement restreinte, pas de code postal) :
    - vide (ou uniquement des espaces) -> invalide
    - 2 chiffres -> département
    - sinon      -> recherche par nom de ville

    Une saisie vide doit être rejetée explicitement (type "invalide") plutôt
    que de tomber dans le cas "ville" avec une valeur vide : une chaîne vide
    est une sous-chaîne de n'importe quel nom de commune, donc un filtrage
    par ville avec valeur vide matcherait silencieusement tous les candidats
    au lieu de signaler une saisie non reconnue (bug réel observé en test :
    appuyer sur Entrée sans rien taper faisait croire au filtrage qu'il avait
    réussi, jusqu'à afficher la liste complète des 146 candidats).

    Retourne : {"type": "departement"|"ville"|"invalide", "valeur": str}
    """
    s = saisie.strip()
    if not s:
        return {"type": "invalide", "valeur": s}
    if s.isdigit() and len(s) == 2:
        return {"type": "departement", "valeur": s}
    return {"type": "ville", "valeur": s}


def filtrer_candidats_par_precision(candidats: list[dict], saisie: str) -> list[dict]:
    """
    Filtre une liste de candidats déjà résolus (via rechercher_etablissements_par_nom)
    selon une précision saisie par l'utilisateur (département ou ville).
    Filtrage en mémoire sur les candidats déjà obtenus — pas une nouvelle requête
    de recherche par nom, pas d'appel LLM.

    Une saisie invalide (vide) retourne une liste vide plutôt que la liste
    complète — laisse le mécanisme de nouvelle tentative (déjà prévu côté
    appelant) se déclencher correctement au lieu d'avancer silencieusement.
    """
    precision = interpreter_precision(saisie)
    if precision["type"] == "invalide":
        return []
    if precision["type"] == "departement":
        return [c for c in candidats if c.get("code_departement") == precision["valeur"]]
    # Recherche par ville : comparaison insensible à la casse, sous-chaîne
    valeur_normalisee = precision["valeur"].strip().lower()
    return [c for c in candidats if valeur_normalisee in (c.get("commune") or "").lower()]


if __name__ == "__main__":
    r1 = recherche_sql("Quels sont les meilleurs collèges publics à Lyon ?")
    print(f"success={r1['success']} | {r1['nb_resultats']} résultats")

    r2 = rechercher_etablissements_par_nom(["Victor Hugo"])
    candidats = r2["resultats"].get("Victor Hugo", [])
    print(f"success={r2['success']} | {len(candidats)} candidats pour 'Victor Hugo' (SEGPA exclues)")

    filtres = filtrer_candidats_par_precision(candidats, "31")
    print(f"Après filtrage département 31 : {len(filtres)} candidats")

    filtres_ville = filtrer_candidats_par_precision(candidats, "Nantes")
    print(f"Après filtrage ville 'Nantes' : {len(filtres_ville)} candidats")
