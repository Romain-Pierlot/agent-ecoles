"""
sql_tool.py — Outil Text-to-SQL pour EduScope
Convertit une question en langage naturel en requête SQL,
l'exécute sur SQLite, et retourne les résultats.

Flux :
1. Construction du prompt avec schéma + dictionnaire de données
2. Appel LLM → génération SQL
3. Validation + exécution sur SQLite
4. Retry automatique si erreur SQL (max LLM_MAX_RETRIES)
"""

import sqlite3
import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH, LLM_MODEL, LLM_MAX_RETRIES, SQL_TIMEOUT_SECONDS

client = OpenAI()

# ================================================================
# SCHÉMA COMPACT POUR LE PROMPT
# Descriptions issues du dictionnaire de données
# ================================================================

SCHEMA_PROMPT = """
Tu as accès à une base SQLite avec 5 tables sur les établissements scolaires français.

TABLE etablissements — 1 ligne par établissement
  uai TEXT PRIMARY KEY          -- identifiant unique officiel
  nom TEXT                      -- nom de l'établissement
  type_etablissement TEXT       -- 'Collège' ou 'Lycée'
  secteur TEXT                  -- 'Public' ou 'Privé'
  commune TEXT                  -- ville (en majuscules dans la base)
  code_departement TEXT         -- ex: '69' pour le Rhône, '75' pour Paris
  libelle_departement TEXT      -- ex: 'Rhône', 'Paris'
  libelle_academie TEXT         -- ex: 'Lyon', 'Paris', 'Versailles'
  libelle_region TEXT           -- ex: 'Auvergne-Rhône-Alpes', 'Île-de-France'
  latitude REAL                 -- coordonnée GPS
  longitude REAL                -- coordonnée GPS
  segpa INTEGER                 -- 1 si section SEGPA, 0 sinon
  ulis INTEGER                  -- 1 si dispositif ULIS, 0 sinon
  section_sport INTEGER         -- 1 si section sportive, 0 sinon
  section_internationale INTEGER -- 1 si section internationale, 0 sinon
  section_europeenne INTEGER    -- 1 si section européenne, 0 sinon
  appartenance_education_prioritaire TEXT -- 'REP', 'REP+', ou NULL

TABLE ips — 1 ligne par établissement par année scolaire
  uai TEXT FK
  annee_scolaire TEXT           -- ex: '2024-2025', '2023-2024'
  ips_moyen REAL                -- IPS moyen (~50=défavorisé, ~180=favorisé, ~100=moyenne nationale)
  ecart_type_ips REAL           -- hétérogénéité sociale (élevé = bonne mixité)
  ips_national REAL             -- référence nationale tous secteurs
  ips_national_public REAL      -- référence nationale secteur public
  ips_academique REAL           -- référence académique tous secteurs
  ips_departemental REAL        -- référence départementale tous secteurs

TABLE ivac — 1 ligne par établissement par session brevet
  uai TEXT FK
  session TEXT                  -- année brevet: '2022', '2023', '2024', '2025'
  brevet_nb_candidats_general INTEGER    -- nombre de candidats série générale
  brevet_taux_reussite_general REAL      -- taux de réussite brevet général (%)
  brevet_va_taux_reussite_general REAL   -- valeur ajoutée du taux (NULL si effectif < 40)
  brevet_note_ecrit_general REAL         -- note moyenne à l'écrit /20
  brevet_va_note_ecrit_general REAL      -- valeur ajoutée de la note (NULL si effectif < 40)
  taux_acces_6eme_3eme REAL             -- % élèves de 6ème atteignant la 3ème dans le collège
  nb_mentions_tb INTEGER                 -- nombre de mentions Très Bien
  nb_mentions_total INTEGER              -- total des mentions (AB + B + TB)

TABLE scores — 1 ligne par établissement par session (calculé par EduScope)
  uai TEXT FK
  session TEXT
  score_principal REAL          -- score EduScope /100 (60% taux réussite + 40% note écrit, normalisé)
  badge_va TEXT                 -- 'positif', 'neutre', 'negatif', ou NULL si VA indisponible

TABLE referentiel_temporel — correspondance session IVAC ↔ année scolaire IPS
  session_ivac TEXT PRIMARY KEY -- '2022', '2023', '2024', '2025'
  annee_scolaire_ips TEXT       -- '2023-2024', '2024-2025', '2025-2026', ou NULL pour 2022
  libelle_affichage TEXT        -- ex: 'Année 2023-2024'

RÈGLES IMPORTANTES :
- Toujours filtrer WHERE type_etablissement = 'Collège' sauf demande explicite sur les lycées
- Session la plus récente disponible : '2025'. Utiliser '2024' si '2025' manque pour un établissement
- La commune est en MAJUSCULES — utiliser UPPER() ou LIKE '%LYON%' pour les recherches
- La VA (valeur ajoutée) peut être NULL — toujours utiliser IS NOT NULL si on la filtre
- Le score EduScope mesure la performance brute — toujours afficher le badge_va à côté
- Synonymes importants : école/établissement/collège → etablissements, résultats/notes → ivac,
  classement/meilleur → ORDER BY score_principal DESC, social/milieu → ips_moyen

EXEMPLES :
Question: "Meilleurs collèges publics à Lyon"
SQL: SELECT e.nom, e.commune, e.secteur, s.score_principal, s.badge_va,
            v.brevet_taux_reussite_general, v.brevet_note_ecrit_general
     FROM etablissements e
     JOIN scores s ON e.uai = s.uai
     JOIN ivac v ON e.uai = v.uai AND v.session = s.session
     WHERE e.commune LIKE '%LYON%'
       AND e.secteur = 'Public'
       AND e.type_etablissement = 'Collège'
       AND s.session = '2024'
     ORDER BY s.score_principal DESC
     LIMIT 10;

Question: "IPS du collège Henri IV à Paris"
SQL: SELECT e.nom, e.commune, i.ips_moyen, i.annee_scolaire,
            i.ips_national, i.ips_departemental
     FROM etablissements e
     JOIN ips i ON e.uai = i.uai
     WHERE e.nom LIKE '%HENRI IV%'
       AND e.commune LIKE '%PARIS%'
       AND e.type_etablissement = 'Collège'
       AND i.annee_scolaire = '2024-2025';

Question: "Collèges avec section sportive dans le 69"
SQL: SELECT e.nom, e.commune, e.secteur, s.score_principal
     FROM etablissements e
     LEFT JOIN scores s ON e.uai = s.uai AND s.session = '2024'
     WHERE e.code_departement = '69'
       AND e.type_etablissement = 'Collège'
       AND e.section_sport = 1
     ORDER BY s.score_principal DESC;
"""

# ================================================================
# FONCTIONS PRINCIPALES
# ================================================================

def generer_sql(question: str, historique_erreurs: list = None) -> str:
    """Appelle le LLM pour générer une requête SQL depuis une question."""
    
    messages = [
        {
            "role": "system",
            "content": f"""Tu es un expert SQL spécialisé dans les données éducatives françaises.
            
{SCHEMA_PROMPT}

INSTRUCTIONS :
- Génère UNIQUEMENT la requête SQL, sans explication ni markdown
- La requête doit être valide pour SQLite
- Termine toujours par un point-virgule
- Maximum 50 résultats sauf si explicitement demandé"""
        },
        {
            "role": "user", 
            "content": question
        }
    ]
    
    # Si on a des erreurs précédentes, on les ajoute au contexte
    if historique_erreurs:
        for erreur in historique_erreurs:
            messages.append({"role": "assistant", "content": erreur["sql_tente"]})
            messages.append({"role": "user", "content": f"Cette requête a échoué avec l'erreur : {erreur['erreur']}. Corrige-la."})
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0,       # Déterministe — on veut du SQL précis
        max_tokens=500,
        timeout=SQL_TIMEOUT_SECONDS
    )
    
    sql = response.choices[0].message.content.strip()
    
    # Nettoyer si le LLM a quand même mis du markdown
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    sql = sql.strip()
    
    return sql


def executer_sql(sql: str) -> list[dict]:
    """Exécute la requête SQL sur SQLite et retourne les résultats."""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        DB_PATH
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Résultats sous forme de dict
    
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def recherche_sql(question: str) -> dict:
    """
    Fonction principale — convertit une question en résultats SQL.
    
    Retourne :
    {
        "succes": bool,
        "question": str,
        "sql_genere": str,
        "resultats": list[dict],
        "nb_resultats": int,
        "erreur": str | None,
        "tentatives": int
    }
    """
    historique_erreurs = []
    
    for tentative in range(1, LLM_MAX_RETRIES + 2):  # +2 car range est exclusif
        
        # Génération SQL
        sql = generer_sql(question, historique_erreurs if historique_erreurs else None)
        
        # Exécution
        try:
            resultats = executer_sql(sql)
            return {
                "succes": True,
                "question": question,
                "sql_genere": sql,
                "resultats": resultats,
                "nb_resultats": len(resultats),
                "erreur": None,
                "tentatives": tentative
            }
            
        except Exception as e:
            erreur_msg = str(e)
            historique_erreurs.append({
                "sql_tente": sql,
                "erreur": erreur_msg
            })
            
            if tentative > LLM_MAX_RETRIES:
                return {
                    "succes": False,
                    "question": question,
                    "sql_genere": sql,
                    "resultats": [],
                    "nb_resultats": 0,
                    "erreur": erreur_msg,
                    "tentatives": tentative
                }
    
    # Ne devrait jamais arriver mais sécurité
    return {
        "succes": False,
        "question": question,
        "sql_genere": "",
        "resultats": [],
        "nb_resultats": 0,
        "erreur": "Nombre maximum de tentatives atteint",
        "tentatives": LLM_MAX_RETRIES + 1
    }


# ================================================================
# TEST RAPIDE EN LIGNE DE COMMANDE
# ================================================================

if __name__ == "__main__":
    questions_test = [
        "Quels sont les meilleurs collèges publics à Lyon ?",
        "Quel est l'IPS du collège Henri IV à Paris ?",
        "Collèges avec section sportive dans le département 69",
        "Compare la valeur ajoutée des collèges de Bordeaux",
    ]
    
    print("=== TEST SQL TOOL ===\n")
    
    for question in questions_test:
        print(f"Question : {question}")
        resultat = recherche_sql(question)
        
        if resultat["succes"]:
            print(f"✓ SQL généré en {resultat['tentatives']} tentative(s)")
            print(f"  Requête : {resultat['sql_genere'][:100]}...")
            print(f"  Résultats : {resultat['nb_resultats']} lignes")
            if resultat["resultats"]:
                print(f"  Premier résultat : {list(resultat['resultats'][0].items())[:3]}")
        else:
            print(f"✗ Échec après {resultat['tentatives']} tentative(s)")
            print(f"  Erreur : {resultat['erreur']}")
        print()
