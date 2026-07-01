"""sql_tool.py — Outil Text-to-SQL pour EduScope (V7 — précision limitée à ville/département, code postal retiré)"""

import sqlite3
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH, LLM_MODEL, LLM_MAX_RETRIES, SQL_TIMEOUT_SECONDS

client = OpenAI()

SCHEMA_PROMPT = """
Tu as accès à une base SQLite avec 5 tables sur les établissements scolaires français.

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

TABLE ivac
  uai TEXT FK
  session TEXT
  brevet_nb_candidats_general INTEGER
  brevet_taux_reussite_general REAL
  brevet_va_taux_reussite_general REAL
  brevet_note_ecrit_general REAL
  brevet_va_note_ecrit_general REAL
  taux_acces_6eme_3eme REAL
  nb_mentions_tb INTEGER
  nb_mentions_total INTEGER

TABLE scores
  uai TEXT FK
  session TEXT
  score_principal REAL
  badge_va TEXT

TABLE referentiel_temporel
  session_ivac TEXT PRIMARY KEY
  annee_scolaire_ips TEXT
  libelle_affichage TEXT

RÈGLES IMPORTANTES :
- Toujours filtrer WHERE type_etablissement = 'Collège' sauf demande explicite sur les lycées
- Session la plus récente disponible : '2025'. Utiliser '2024' si '2025' manque
- La commune est en MAJUSCULES — utiliser UPPER() ou LIKE '%LYON%'
- La VA peut être NULL — toujours IS NOT NULL si filtrée
- Toujours afficher le badge_va à côté du score
- TOUJOURS inclure e.uai dans le SELECT (nécessaire pour la traçabilité en aval)
- Synonymes : école/établissement/collège → etablissements, résultats/notes → ivac,
  classement/meilleur → ORDER BY score_principal DESC, social/milieu → ips_moyen

EXEMPLES :
Question: "Meilleurs collèges publics à Lyon"
SQL: SELECT e.uai, e.nom, e.commune, e.secteur, s.score_principal, s.badge_va,
            v.brevet_taux_reussite_general, v.brevet_note_ecrit_general,
            v.brevet_va_taux_reussite_general, v.brevet_va_note_ecrit_general
     FROM etablissements e
     JOIN scores s ON e.uai = s.uai
     JOIN ivac v ON e.uai = v.uai AND v.session = s.session
     WHERE e.commune LIKE '%LYON%' AND e.secteur = 'Public'
       AND e.type_etablissement = 'Collège' AND s.session = '2024'
     ORDER BY s.score_principal DESC LIMIT 10;

TOUJOURS inclure badge_va, brevet_va_taux_reussite_general et
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
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def recherche_sql(question: str, uai_filtre: list = None) -> dict:
    """Retourne : {success, question, sql_genere, resultats, nb_resultats, error, tentatives}"""
    historique_erreurs = []
    for tentative in range(1, LLM_MAX_RETRIES + 2):
        sql = generer_sql(question, historique_erreurs if historique_erreurs else None, uai_filtre)
        try:
            resultats = executer_sql(sql)
            return {
                "success": True, "question": question, "sql_genere": sql,
                "resultats": resultats, "nb_resultats": len(resultats),
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


# Seuil au-delà duquel on ne liste plus les candidats mais on demande une
# précision géographique (département ou ville). Au-delà de 5 options, une
# liste numérotée devient inexploitable pour l'utilisateur.
SEUIL_CANDIDATS_AVANT_PRECISION = 5


def rechercher_etablissements_par_nom(noms: list[str], type_etablissement: str = "Collège") -> dict:
    """
    Résout une liste de noms d'établissements en candidats potentiels.

    Lookup SQL direct (LIKE), AUCUN appel LLM : trouver les établissements
    correspondant à un nom donné est une recherche déterministe, pas une
    tâche d'interprétation de texte libre (cf. principe templating vs LLM).

    Exclut les SEGPA/sections rattachées (nom contient "Section d'enseignement")
    — ce sont des sous-structures internes à un collège, pas des établissements
    comparables entre eux pour un parent qui compare deux collèges.

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
                rows = conn.execute("""
                    SELECT uai, nom, commune, code_departement, secteur
                    FROM etablissements
                    WHERE nom LIKE ?
                      AND type_etablissement = ?
                      AND nom NOT LIKE '%Section d%'
                    ORDER BY nom
                """, (f"%{nom}%", type_etablissement)).fetchall()
                resultats[nom] = [dict(row) for row in rows]
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
    - 2 chiffres -> département
    - sinon      -> recherche par nom de ville

    Retourne : {"type": "departement"|"ville", "valeur": str}
    """
    s = saisie.strip()
    if s.isdigit() and len(s) == 2:
        return {"type": "departement", "valeur": s}
    return {"type": "ville", "valeur": s}


def filtrer_candidats_par_precision(candidats: list[dict], saisie: str) -> list[dict]:
    """
    Filtre une liste de candidats déjà résolus (via rechercher_etablissements_par_nom)
    selon une précision saisie par l'utilisateur (département ou ville).
    Filtrage en mémoire sur les candidats déjà obtenus — pas une nouvelle requête
    de recherche par nom, pas d'appel LLM.
    """
    precision = interpreter_precision(saisie)
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
