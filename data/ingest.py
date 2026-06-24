"""
ingest.py — Script d'ingestion CSV → SQLite
EduScope / agent-ecoles

Décisions d'architecture documentées :
- On stocke TOUS les établissements (collèges + lycées) — filtre par type dans les requêtes
- On stocke TOUS les états (ouvert + fermé) — filtre WHERE etat='OUVERT' dans l'agent
- Coordonnées GPS : on utilise celles de l'annuaire (latitude/longitude séparées)
- Colonnes binaires : INTEGER 0/1 (convention SQLite — pas de type BOOLEAN natif)
- VA calculée uniquement pour la série générale du brevet (pas la série pro)
- Score absent (NULL) si taux_reussite ou note_ecrit manquants
"""

import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    SCORE_POIDS_TAUX, SCORE_POIDS_NOTE,
    VA_SEUIL_POSITIF, VA_SEUIL_NEGATIF
)

DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ANNUAIRE = os.path.join(DIR, "frenannuaireeducation_col_lycees.csv")
CSV_IPS      = os.path.join(DIR, "frenipscollegesap2023.csv")
CSV_IVAC     = os.path.join(DIR, "frenindicateursvaleurajouteecolleges.csv")


def creer_connexion():
    db_path = os.path.join(os.path.dirname(DIR), DB_PATH)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    print(f"✓ Base SQLite : {db_path}")
    return conn


def creer_tables(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS scores;
        DROP TABLE IF EXISTS ips;
        DROP TABLE IF EXISTS ivac;
        DROP TABLE IF EXISTS etablissements;
        DROP TABLE IF EXISTS referentiel_temporel;

        CREATE TABLE etablissements (
            uai                                 TEXT PRIMARY KEY,
            nom                                 TEXT,
            type_etablissement                  TEXT,
            secteur                             TEXT,
            adresse                             TEXT,
            code_postal                         TEXT,
            commune                             TEXT,
            code_departement                    TEXT,
            libelle_departement                 TEXT,
            code_academie                       TEXT,
            libelle_academie                    TEXT,
            libelle_region                      TEXT,
            latitude                            REAL,
            longitude                           REAL,
            telephone                           TEXT,
            mail                                TEXT,
            web                                 TEXT,
            fiche_onisep                        TEXT,
            date_ouverture                      TEXT,
            etat                                TEXT,
            -- Services (0/1)
            restauration                        INTEGER,
            hebergement                         INTEGER,
            -- Dispositifs inclusifs (0/1)
            ulis                                INTEGER,
            apprentissage                       INTEGER,
            segpa                               INTEGER,
            -- Sections (0/1)
            section_arts                        INTEGER,
            section_cinema                      INTEGER,
            section_theatre                     INTEGER,
            section_sport                       INTEGER,
            section_internationale              INTEGER,
            section_europeenne                  INTEGER,
            -- Spécifiques lycées (0/1) — NULL ou 0 pour les collèges
            voie_generale                       INTEGER,
            voie_technologique                  INTEGER,
            voie_professionnelle                INTEGER,
            lycee_agricole                      INTEGER,
            lycee_militaire                     INTEGER,
            lycee_des_metiers                   INTEGER,
            post_bac                            INTEGER,
            -- Éducation prioritaire
            appartenance_education_prioritaire  TEXT
        );

        CREATE TABLE ips (
            uai                         TEXT,
            annee_scolaire              TEXT,
            ips_moyen                   REAL,
            ecart_type_ips              REAL,
            ips_national_public         REAL,
            ips_national_prive          REAL,
            ips_national                REAL,
            ips_academique_public       REAL,
            ips_academique_prive        REAL,
            ips_academique              REAL,
            ips_departemental_public    REAL,
            ips_departemental_prive     REAL,
            ips_departemental           REAL,
            PRIMARY KEY (uai, annee_scolaire),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE ivac (
            uai                             TEXT,
            session                         TEXT,
            brevet_nb_candidats_general     INTEGER,
            brevet_taux_reussite_general    REAL,
            brevet_va_taux_reussite_general REAL,
            brevet_note_ecrit_general       REAL,
            brevet_va_note_ecrit_general    REAL,
            brevet_nb_candidats_pro         INTEGER,
            brevet_taux_reussite_pro        REAL,
            brevet_note_ecrit_pro           REAL,
            taux_acces_6eme_3eme            REAL,
            part_3eme_ordinaire             REAL,
            part_3eme_segpa                 REAL,
            nb_mentions_ab                  INTEGER,
            nb_mentions_b                   INTEGER,
            nb_mentions_tb                  INTEGER,
            nb_mentions_total               INTEGER,
            PRIMARY KEY (uai, session),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE scores (
            uai             TEXT,
            session         TEXT,
            score_principal REAL,
            badge_va        TEXT,
            PRIMARY KEY (uai, session),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE referentiel_temporel (
            session_ivac        TEXT PRIMARY KEY,
            annee_scolaire_ips  TEXT,
            libelle_affichage   TEXT
        );
    """)
    print("✓ Tables créées")


def ingerer_annuaire(conn):
    print("→ Chargement annuaire...")
    df = pd.read_csv(CSV_ANNUAIRE, sep=',', dtype=str, low_memory=False)

    colonnes = {
        'Identifiant_de_l_etablissement':       'uai',
        'Nom_etablissement':                    'nom',
        'Type_etablissement':                   'type_etablissement',
        'Statut_public_prive':                  'secteur',
        'Adresse_1':                            'adresse',
        'Code_postal':                          'code_postal',
        'Nom_commune':                          'commune',
        'Code_departement':                     'code_departement',
        'Libelle_departement':                  'libelle_departement',
        'Code_academie':                        'code_academie',
        'Libelle_academie':                     'libelle_academie',
        'Libelle_region':                       'libelle_region',
        'latitude':                             'latitude',
        'longitude':                            'longitude',
        'Telephone':                            'telephone',
        'Mail':                                 'mail',
        'Web':                                  'web',
        'Fiche_onisep':                         'fiche_onisep',
        'date_ouverture':                       'date_ouverture',
        'etat':                                 'etat',
        'Restauration':                         'restauration',
        'Hebergement':                          'hebergement',
        'ULIS':                                 'ulis',
        'Apprentissage':                        'apprentissage',
        'Segpa':                                'segpa',
        'Section_arts':                         'section_arts',
        'Section_cinema':                       'section_cinema',
        'Section_theatre':                      'section_theatre',
        'Section_sport':                        'section_sport',
        'Section_internationale':               'section_internationale',
        'Section_europeenne':                   'section_europeenne',
        'Voie_generale':                        'voie_generale',
        'Voie_technologique':                   'voie_technologique',
        'Voie_professionnelle':                 'voie_professionnelle',
        'Lycee_Agricole':                       'lycee_agricole',
        'Lycee_militaire':                      'lycee_militaire',
        'Lycee_des_metiers':                    'lycee_des_metiers',
        'Post_BAC':                             'post_bac',
        'Appartenance_Education_Prioritaire':   'appartenance_education_prioritaire',
    }

    cols_dispo = {k: v for k, v in colonnes.items() if k in df.columns}
    df = df[list(cols_dispo.keys())].rename(columns=cols_dispo)

    # GPS
    for col in ['latitude', 'longitude']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Binaires 0/1
    cols_bin = [
        'restauration', 'hebergement', 'ulis', 'apprentissage', 'segpa',
        'section_arts', 'section_cinema', 'section_theatre', 'section_sport',
        'section_internationale', 'section_europeenne', 'voie_generale',
        'voie_technologique', 'voie_professionnelle', 'lycee_agricole',
        'lycee_militaire', 'lycee_des_metiers', 'post_bac'
    ]
    for col in cols_bin:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df = df[df['etat'] == 'OUVERT'].copy()
    # Multi-sites : on garde le site principal (première occurrence par UAI)
    df = df.drop_duplicates(subset='uai', keep='first')
    df['secteur'] = df['secteur'].str.strip()

    df.to_sql('etablissements', conn, if_exists='append', index=False)

    # Stats
    if 'type_etablissement' in df.columns:
        for t, n in df['type_etablissement'].value_counts().items():
            print(f"  ✓ {n:>5} {t}")
    if 'etat' in df.columns:
        for e, n in df['etat'].value_counts().items():
            print(f"         état {e} : {n}")


def ingerer_ips(conn):
    print("→ Chargement IPS...")
    df = pd.read_csv(CSV_IPS, sep=';', dtype=str, low_memory=False)

    colonnes = {
        'UAI':                          'uai',
        'Année scolaire':               'annee_scolaire',
        'IPS':                          'ips_moyen',
        "Ecart type de l'IPS":          'ecart_type_ips',
        'IPS national privé':           'ips_national_prive',
        'IPS national public':          'ips_national_public',
        'IPS national':                 'ips_national',
        'IPS académique privé':         'ips_academique_prive',
        'IPS académique public':        'ips_academique_public',
        'IPS académique':               'ips_academique',
        'IPS départemental privé':      'ips_departemental_prive',
        'IPS départemental public':     'ips_departemental_public',
        'IPS départemental':            'ips_departemental',
    }

    # Noms alternatifs selon les versions du fichier
    colonnes_alt = {
        "Ecart-type de l'IPS":          'ecart_type_ips',
        'IPS national prive':           'ips_national_prive',
        'IPS academique prive':         'ips_academique_prive',
        'IPS academique public':        'ips_academique_public',
        'IPS academique':               'ips_academique',
        'IPS departemental prive':      'ips_departemental_prive',
        'IPS departemental public':     'ips_departemental_public',
        'IPS departemental':            'ips_departemental',
    }
    colonnes.update({k: v for k, v in colonnes_alt.items() if k in df.columns})

    cols_dispo = {k: v for k, v in colonnes.items() if k in df.columns}
    df = df[list(cols_dispo.keys())].rename(columns=cols_dispo)

    # Dédoublonner si une colonne apparaît deux fois
    df = df.loc[:, ~df.columns.duplicated()]

    for col in df.columns:
        if col not in ['uai', 'annee_scolaire']:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '.'), errors='coerce'
            )

    df.to_sql('ips', conn, if_exists='append', index=False)
    print(f"  ✓ {len(df)} lignes IPS")


def ingerer_ivac(conn):
    print("→ Chargement IVAC...")
    df = pd.read_csv(CSV_IVAC, sep=';', dtype=str, low_memory=False)

    colonnes = {
        'UAI':                          'uai',
        'Session':                      'session',
        'Nb candidats G':               'brevet_nb_candidats_general',
        'Taux de réussite G':           'brevet_taux_reussite_general',
        'VA du taux de réussite G':     'brevet_va_taux_reussite_general',
        "Note à l'écrit G":             'brevet_note_ecrit_general',
        'VA de la note G':              'brevet_va_note_ecrit_general',
        'Nb candidats P':               'brevet_nb_candidats_pro',
        'Taux de réussite P':           'brevet_taux_reussite_pro',
        "Note à l'écrit P":             'brevet_note_ecrit_pro',
        "Taux d'accès 6eme 3eme":       'taux_acces_6eme_3eme',
        'Part présents 3eme ordinaire total': 'part_3eme_ordinaire',
        'Part présents 3eme segpa total':     'part_3eme_segpa',
        'Nb mentions AB G':             'nb_mentions_ab',
        'Nb mentions B G':              'nb_mentions_b',
        'Nb mentions TB G':             'nb_mentions_tb',
        'Nb mentions global G':         'nb_mentions_total',
    }

    cols_dispo = {k: v for k, v in colonnes.items() if k in df.columns}
    df = df[list(cols_dispo.keys())].rename(columns=cols_dispo)

    for col in df.columns:
        if col not in ['uai', 'session']:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '.'), errors='coerce'
            )

    df.to_sql('ivac', conn, if_exists='append', index=False)
    print(f"  ✓ {len(df)} lignes IVAC")


def calculer_scores(conn):
    print("→ Calcul des scores...")
    df = pd.read_sql("""
        SELECT uai, session,
               brevet_taux_reussite_general,
               brevet_note_ecrit_general,
               brevet_va_taux_reussite_general
        FROM ivac
        WHERE brevet_taux_reussite_general IS NOT NULL
          AND brevet_note_ecrit_general IS NOT NULL
    """, conn)

    df['score_principal'] = None

    for session in df['session'].unique():
        mask = df['session'] == session
        s = df[mask]

        t_min, t_max = s['brevet_taux_reussite_general'].min(), s['brevet_taux_reussite_general'].max()
        n_min, n_max = s['brevet_note_ecrit_general'].min(), s['brevet_note_ecrit_general'].max()

        if t_max > t_min and n_max > n_min:
            t_norm = (df.loc[mask, 'brevet_taux_reussite_general'] - t_min) / (t_max - t_min)
            n_norm = (df.loc[mask, 'brevet_note_ecrit_general'] - n_min) / (n_max - n_min)
            df.loc[mask, 'score_principal'] = (
                t_norm * SCORE_POIDS_TAUX + n_norm * SCORE_POIDS_NOTE
            ) * 100

    def badge(row):
        va = row['brevet_va_taux_reussite_general']
        if pd.isna(va):
            return None
        if va > VA_SEUIL_POSITIF:
            return 'positif'
        if va < VA_SEUIL_NEGATIF:
            return 'negatif'
        return 'neutre'

    df['badge_va'] = df.apply(badge, axis=1)

    scores = df[['uai', 'session', 'score_principal', 'badge_va']]
    scores.to_sql('scores', conn, if_exists='append', index=False)
    print(f"  ✓ {len(scores)} scores calculés")


def inserer_referentiel(conn):
    print("→ Référentiel temporel...")
    conn.executemany(
        "INSERT INTO referentiel_temporel VALUES (?, ?, ?)",
        [
            ('2022', None,        'Session 2022 (pas de données IPS disponibles)'),
            ('2023', '2023-2024', 'Année 2023-2024'),
            ('2024', '2024-2025', 'Année 2024-2025'),
            ('2025', '2025-2026', 'Année 2025-2026'),
        ]
    )
    conn.commit()
    print("  ✓ 4 lignes insérées")


def creer_index(conn):
    print("→ Index...")
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_etab_type
            ON etablissements(type_etablissement);
        CREATE INDEX IF NOT EXISTS idx_etab_dept
            ON etablissements(code_departement);
        CREATE INDEX IF NOT EXISTS idx_etab_secteur
            ON etablissements(secteur);
        CREATE INDEX IF NOT EXISTS idx_etab_etat
            ON etablissements(etat);
        CREATE INDEX IF NOT EXISTS idx_etab_geo
            ON etablissements(latitude, longitude);
        CREATE INDEX IF NOT EXISTS idx_ips_uai
            ON ips(uai);
        CREATE INDEX IF NOT EXISTS idx_ips_annee
            ON ips(annee_scolaire);
        CREATE INDEX IF NOT EXISTS idx_ivac_uai
            ON ivac(uai);
        CREATE INDEX IF NOT EXISTS idx_ivac_session
            ON ivac(session);
        CREATE INDEX IF NOT EXISTS idx_scores_uai
            ON scores(uai);
        CREATE INDEX IF NOT EXISTS idx_scores_session
            ON scores(session);
    """)
    print("  ✓ 11 index créés")


def verifier(conn):
    print("\n=== VÉRIFICATION ===")
    for table in ['etablissements', 'ips', 'ivac', 'scores', 'referentiel_temporel']:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<30} : {n:>6} lignes")

    print("\n  Types établissements :")
    for row in conn.execute("""
        SELECT type_etablissement, etat, COUNT(*) n
        FROM etablissements
        GROUP BY type_etablissement, etat
        ORDER BY n DESC
    """):
        print(f"    {row[0]:<35} {row[1]:<10} : {row[2]:>5}")

    communs = conn.execute("""
        SELECT COUNT(DISTINCT e.uai)
        FROM etablissements e
        JOIN ivac i ON e.uai = i.uai
        JOIN ips p  ON e.uai = p.uai
    """).fetchone()[0]
    print(f"\n  UAI communs aux 3 sources : {communs}")

    scores_non_null = conn.execute(
        "SELECT COUNT(*) FROM scores WHERE score_principal IS NOT NULL"
    ).fetchone()[0]
    print(f"  Scores calculés (non NULL) : {scores_non_null}")
    print("====================\n")


def main():
    print("=== INGESTION AGENT-ECOLES ===\n")
    conn = creer_connexion()
    creer_tables(conn)
    ingerer_annuaire(conn)
    ingerer_ips(conn)
    ingerer_ivac(conn)
    calculer_scores(conn)
    inserer_referentiel(conn)
    creer_index(conn)
    verifier(conn)
    conn.close()
    print("✓ Ingestion terminée\n")


if __name__ == "__main__":
    main()
