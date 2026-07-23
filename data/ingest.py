"""
ingest.py — Script d'ingestion CSV → SQLite
agent-ecoles

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
import numpy as np
import re
import sys
import os
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    SCORE_PRINCIPAL_POIDS_TAUX, SCORE_PRINCIPAL_POIDS_NOTE,
    SCORE_PRINCIPAL_POIDS_VA_TAUX, SCORE_PRINCIPAL_POIDS_VA_NOTE,
    SCORE_RESULTATS_POIDS_TAUX, SCORE_RESULTATS_POIDS_NOTE,
    NOTATION_REPARTITION, NOTATION_LETTRES,
    VA_SEUIL_POSITIF, VA_SEUIL_NEGATIF
)
# Réutilise la même normalisation de nom de voie que le futur rapprochement
# adresse -> secteur (agent/tools/carte_scolaire_tool.py) : les deux côtés
# doivent produire exactement la même clé, sinon aucune jointure ne matche
# jamais. Première dépendance de data/ingest.py vers le package agent/
# (jusqu'ici limité à config.py) — accepté ici plutôt que dupliquer la
# logique d'accent-fold/tirets à deux endroits.
from agent.tools.geo_tool import _normaliser_nom_commune

DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ANNUAIRE = os.path.join(DIR, "frenannuaireeducation_col_lycees.csv")
CSV_IPS      = os.path.join(DIR, "frenipscollegesap2023.csv")
CSV_IVAC     = os.path.join(DIR, "frenindicateursvaleurajouteecolleges.csv")
CSV_LANGUES  = os.path.join(DIR, "fr-en-offre-langues-2d.csv")
CSV_SECTIONS_SPORTIVES = os.path.join(DIR, "fr-en-sections-sportives-scolaires.csv")
CSV_ZONES_ACADEMIQUES = os.path.join(DIR, "zones_academiques.csv")
CSV_CARTE_SCOLAIRE = os.path.join(DIR, "fr-en-carte-scolaire-colleges-publics.csv")


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
        DROP TABLE IF EXISTS langues_offertes;
        DROP TABLE IF EXISTS vacances_scolaires;
        DROP TABLE IF EXISTS zones_academiques;
        DROP TABLE IF EXISTS sections_sportives;
        DROP TABLE IF EXISTS carte_scolaire_troncons;

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
            -- Comparatifs mixité sociale (calculés à l'ingestion, cf.
            -- _ajouter_comparatifs_ips — la source ne fournit de comparatifs
            -- que pour ips_moyen, pas pour ecart_type_ips)
            ecart_type_ips_national       REAL,
            ecart_type_ips_departemental  REAL,
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
            -- Comparatifs brevet (calculés à l'ingestion, cf. _ajouter_comparatifs_ivac
            -- — contrairement à ips.*, non fournis par le fichier source)
            brevet_taux_reussite_national       REAL,
            brevet_note_ecrit_national          REAL,
            brevet_taux_reussite_departemental  REAL,
            brevet_note_ecrit_departemental     REAL,
            taux_acces_6eme_3eme_national       REAL,
            taux_acces_6eme_3eme_departemental  REAL,
            PRIMARY KEY (uai, session),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE scores (
            uai             TEXT,
            session         TEXT,
            score_principal REAL,
            score_resultats REAL,
            notation        TEXT,
            badge_va        TEXT,
            -- VA absente -> substituée par 0 (neutre) dans score_principal,
            -- cf. calculer_scores. va_imputee=1 signale que la notation de
            -- cet établissement ne s'appuie pas sur une VA réelle.
            va_imputee      INTEGER,
            PRIMARY KEY (uai, session),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE referentiel_temporel (
            session_ivac        TEXT PRIMARY KEY,
            annee_scolaire_ips  TEXT,
            libelle_affichage   TEXT
        );

        CREATE TABLE zones_academiques (
            code_academie     TEXT PRIMARY KEY,
            libelle_academie  TEXT,
            zone              TEXT  -- 'A' | 'B' | 'C' | NULL (Corse, outre-mer)
        );

        CREATE TABLE langues_offertes (
            uai                TEXT,
            type_enseignement  TEXT,  -- 'LV1' | 'LV2' | 'LCA'
            langue             TEXT,
            PRIMARY KEY (uai, type_enseignement, langue),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE sections_sportives (
            uai    TEXT,
            sport  TEXT,
            PRIMARY KEY (uai, sport),
            FOREIGN KEY (uai) REFERENCES etablissements(uai)
        );

        CREATE TABLE vacances_scolaires (
            annee_scolaire  TEXT,
            zone            TEXT,  -- 'A' | 'B' | 'C' | 'TOUTES'
            periode         TEXT,  -- 'Prérentrée' | 'Rentrée' | 'Toussaint' | 'Noël' | 'Hiver' | 'Printemps' | 'Fin d''année scolaire'
            type_periode    TEXT,  -- 'vacances' | 'jalon'
            date_debut      TEXT,  -- ISO 'YYYY-MM-DD'
            date_fin        TEXT,  -- ISO, NULL pour un jalon ponctuel
            PRIMARY KEY (annee_scolaire, zone, periode)
        );

        -- Sectorisation des collèges PUBLICS uniquement (carte scolaire du
        -- Ministère ne couvre pas le privé). Une ligne = un tronçon de rue
        -- (commune + voie + plage de numéros + parité) -> un collège de
        -- secteur (code_rne = uai). Plusieurs tronçons PEUVENT se superposer
        -- sur la même plage avec des code_rne différents : plusieurs
        -- collèges légitimes pour la même adresse (cas réel confirmé à
        -- Maxéville/RUE BLAISE PASCAL, cf. docs/exploration/
        -- etude_matching_carte_scolaire.md). Ce multi-secteur se détecte en
        -- comptant les code_rne distincts retournés par le rapprochement
        -- (étape suivante), PAS via secteur_unique ci-dessous : cette
        -- colonne vaut 'N' pour l'écrasante majorité des lignes (486618/
        -- 520678, vérifié) et ne semble donc pas signaler une ambiguïté par
        -- tronçon — sémantique exacte non éclaircie, stockée telle quelle
        -- (traçabilité/débogage) mais non utilisée dans la logique métier.
        CREATE TABLE carte_scolaire_troncons (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            code_insee       TEXT,
            libelle_commune  TEXT,
            voie_normalisee  TEXT,
            numero_debut     INTEGER,
            numero_fin       INTEGER,
            parite           TEXT,  -- 'I' | 'P' | 'PI'
            code_rne         TEXT,  -- = uai du collège de secteur
            secteur_unique   TEXT   -- 'O' | 'N', tel que fourni par le Ministère
        );
    """)
    print("✓ Tables créées")


# Communes à arrondissements où le fichier source du ministère étiquette la
# grande majorité des établissements génériquement ("Paris", "Lyon",
# "Marseille") plutôt que par arrondissement précis ("Paris 13e
# Arrondissement") — ex: 179 des ~200 collèges parisiens sont dans ce cas.
# Une recherche géo par arrondissement (comparaison exacte sur commune,
# cf. geo_tool.trouver_etablissements_par_commune) ratait donc la quasi-
# totalité des établissements. Le code postal complet encode fiablement
# l'arrondissement pour ces 3 villes (750XX, 690XX, 130XX) — regex validée
# manuellement contre les codes postaux réellement présents en base.
ARRONDISSEMENTS_PAR_CODE_POSTAL = {
    "Paris": (re.compile(r'^750(\d{2})$'), 1, 20),
    "Lyon": (re.compile(r'^690(\d{2})$'), 1, 9),
    "Marseille": (re.compile(r'^130(\d{2})$'), 1, 16),
}


def _deriver_arrondissement(commune: str, code_postal) -> str:
    """
    Reconstruit le libellé d'arrondissement (ex: "Paris 16e Arrondissement")
    depuis le code postal quand la commune est étiquetée génériquement.
    Ne touche jamais les communes déjà précises (ex: déjà "Paris 16e
    Arrondissement") ni les codes postaux hors du motif attendu (quelques
    codes CEDEX/administratifs isolés, ex: 69289, 13232 — laissés tels
    quels plutôt que de risquer un rattachement erroné).
    """
    motif = ARRONDISSEMENTS_PAR_CODE_POSTAL.get(commune)
    if motif is None or not isinstance(code_postal, str):
        return commune
    regex, arr_min, arr_max = motif
    match = regex.match(code_postal)
    if not match:
        return commune
    numero = int(match.group(1))
    if not (arr_min <= numero <= arr_max):
        return commune
    suffixe = "1er" if numero == 1 else f"{numero}e"
    return f"{commune} {suffixe} Arrondissement"


def _normaliser_code_departement(code):
    """
    Corrige le code département brut de la source (cf. appel dans
    ingerer_annuaire) : zero-pad les codes 1-9 ("1" -> "01"), retire le zéro
    parasite de la Corse ("02A"/"02B" -> "2A"/"2B", le code officiel INSEE).
    Les codes DOM-TOM (971-978) et les autres départements métropolitains
    (10-95) sont déjà corrects, laissés inchangés.
    """
    if pd.isna(code):
        return code
    if code in ('02A', '02B'):
        return code[1:]
    if code.isdigit() and len(code) == 1:
        return code.zfill(2)
    return code


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
    # Espaces multiples normalisés en un seul (ex: "Paris 16e  Arrondissement"
    # -> "Paris 16e Arrondissement") — anomalie du fichier source du ministère
    # présente sur les arrondissements de Paris, Lyon ET Marseille (espacement
    # incohérent selon les lignes). Sans ça, une égalité stricte sur commune
    # (cf. geo_tool.trouver_etablissements_par_commune) ne matche jamais la
    # valeur renvoyée par le géocodeur (BAN), qui utilise toujours un seul
    # espace -> "collèges à Paris/Lyon/Marseille Xe" retournait 0 résultat.
    if 'commune' in df.columns:
        df['commune'] = df['commune'].str.strip().str.replace(r'\s+', ' ', regex=True)
    # Arrondissement reconstruit depuis le code postal quand la commune est
    # étiquetée génériquement (cf. _deriver_arrondissement) — Paris, Lyon,
    # Marseille seulement, sans effet sur les autres communes.
    if 'commune' in df.columns and 'code_postal' in df.columns:
        df['commune'] = df.apply(lambda r: _deriver_arrondissement(r['commune'], r['code_postal']), axis=1)
    # Anomalie de la source (Code_departement du fichier annuaire) : les
    # départements 1 à 9 sont fournis sans zéro ("1" pour l'Ain), la Corse
    # avec un zéro parasite ("02A"/"02B" au lieu du code officiel "2A"/"2B").
    # Corrigé une fois ici plutôt que dans chaque consommateur (même logique
    # que le nettoyage de commune ci-dessus) — nécessaire pour que le slug
    # département affiche le repère à 2 chiffres attendu (decision_log.md
    # S15.4).
    if 'code_departement' in df.columns:
        df['code_departement'] = df['code_departement'].apply(_normaliser_code_departement)

    df.to_sql('etablissements', conn, if_exists='append', index=False)

    # Stats
    if 'type_etablissement' in df.columns:
        for t, n in df['type_etablissement'].value_counts().items():
            print(f"  ✓ {n:>5} {t}")
    if 'etat' in df.columns:
        for e, n in df['etat'].value_counts().items():
            print(f"         état {e} : {n}")


def ingerer_carte_scolaire(conn):
    """
    Ingère data/fr-en-carte-scolaire-colleges-publics.csv (sectorisation des
    collèges PUBLICS uniquement — cf. docs/exploration/
    etude_matching_carte_scolaire.md). Chaque ligne = un tronçon de rue
    (commune + voie + plage de numéros + parité) -> un collège de secteur
    (code_rne = uai).

    ~6,5% des lignes (34191/520678, vérifié) ont un décalage de colonnes :
    la colonne "parite" contient un UAI ou une valeur vide au lieu de
    I/P/PI. Rejetées ici (pas de tentative de réparation du décalage, sa
    régularité n'étant pas établie — cf. décision n°2 du plan) plutôt que
    de risquer un rattachement erroné.
    """
    print("→ Chargement carte scolaire (sectorisation collèges publics)...")
    df = pd.read_csv(CSV_CARTE_SCOLAIRE, sep=';', dtype=str)

    n_total = len(df)
    df = df[df['parite'].isin(['I', 'P', 'PI'])].copy()
    n_rejetees_parite = n_total - len(df)

    # Même normalisation que côté rapprochement (agent/tools/geo_tool.py) :
    # accents supprimés, minuscules, tirets/apostrophes -> espaces —
    # indispensable pour que "RUE BLAISE PASCAL" (CSV) et "Rue Blaise
    # Pascal" (label BAN) produisent la même clé.
    #
    # Deux nettoyages supplémentaires propres au CSV carte scolaire (absents
    # côté BAN, donc à retirer avant de normaliser sous peine de ne jamais
    # matcher) — patterns mesurés sur le fichier entier, cf. investigation
    # du 2026-07-23 :
    # - préfixe "LIEU DIT " (1,44% des lignes) : BAN renvoie le nom du lieu-dit
    #   seul, sans ce préfixe administratif.
    # - suffixe parenthèse "(NOM DE COMMUNE)" (0,46% des lignes) : sert à
    #   désambiguïser une rue au sein d'une commune nouvelle issue d'une
    #   fusion (ex: "RUE LOUIS SIMON (BRIEY)" à Val-de-Briey) — BAN ne le
    #   reprend jamais dans son nom de rue.
    voie_nettoyee = (
        df['type_et_libelle']
        .str.replace(r'^LIEU.?DIT\s+', '', regex=True, case=False)
        .str.replace(r'\s*\([^)]+\)\s*$', '', regex=True)
    )
    df['voie_normalisee'] = voie_nettoyee.apply(_normaliser_nom_commune)
    df['numero_debut'] = pd.to_numeric(df['No_de_voie_debut'], errors='coerce')
    df['numero_fin'] = pd.to_numeric(df['No_de_voie_fin'], errors='coerce')

    # Filet de sécurité supplémentaire : une plage non numérique (NaN) ne
    # peut de toute façon jamais matcher une recherche par numéro.
    avant_filtre_numero = len(df)
    df = df[df['numero_debut'].notna() & df['numero_fin'].notna()].copy()
    n_rejetees_numero = avant_filtre_numero - len(df)
    df['numero_debut'] = df['numero_debut'].astype(int)
    df['numero_fin'] = df['numero_fin'].astype(int)

    a_inserer = df[[
        'code_insee', 'libelle_commune', 'voie_normalisee',
        'numero_debut', 'numero_fin', 'parite', 'code_rne', 'secteur_unique',
    ]]
    a_inserer.to_sql('carte_scolaire_troncons', conn, if_exists='append', index=False)
    print(
        f"  ✓ {len(a_inserer)} tronçons ingérés "
        f"({n_rejetees_parite} lignes rejetées — colonne parité incohérente"
        + (f", {n_rejetees_numero} rejetées en plus — plage numérique invalide" if n_rejetees_numero else "")
        + ")"
    )


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

    df = _ajouter_comparatifs_ips(df, conn)

    df.to_sql('ips', conn, if_exists='append', index=False)
    print(f"  ✓ {len(df)} lignes IPS")


def _ajouter_comparatifs_ips(df, conn):
    """
    Ajoute les comparatifs national/départemental de la mixité sociale
    (ecart_type_ips) — la source ne fournit des comparatifs que pour
    ips_moyen (ips_national/ips_departemental...), pas pour ecart_type_ips.
    Même principe que _ajouter_comparatifs_ivac pour le brevet.
    """
    dept_par_uai = pd.read_sql(
        "SELECT uai, code_departement FROM etablissements", conn
    ).set_index('uai')['code_departement']
    df = df.copy()
    df['code_departement'] = df['uai'].map(dept_par_uai)

    df['ecart_type_ips_national'] = df.groupby('annee_scolaire')['ecart_type_ips'].transform('mean')
    df['ecart_type_ips_departemental'] = df.groupby(['annee_scolaire', 'code_departement'])['ecart_type_ips'].transform('mean')

    return df.drop(columns=['code_departement'])


def _ajouter_comparatifs_ivac(df, conn):
    """
    Ajoute les 6 colonnes de comparaison national/départemental — calculées
    ICI par simple moyenne, contrairement à ips.* qui les reçoit déjà toutes
    faites de sa source. Département de chaque UAI lu depuis
    `etablissements` (déjà ingérée à ce stade, cf. ordre d'appel dans
    main()). transform('mean') inclut la propre valeur de l'établissement
    dans sa moyenne de comparaison (biais négligeable au nombre
    d'établissements par session/département, pas un souci en pratique).
    """
    dept_par_uai = pd.read_sql(
        "SELECT uai, code_departement FROM etablissements", conn
    ).set_index('uai')['code_departement']
    df = df.copy()
    df['code_departement'] = df['uai'].map(dept_par_uai)

    df['brevet_taux_reussite_national'] = df.groupby('session')['brevet_taux_reussite_general'].transform('mean')
    df['brevet_note_ecrit_national'] = df.groupby('session')['brevet_note_ecrit_general'].transform('mean')
    df['brevet_taux_reussite_departemental'] = df.groupby(['session', 'code_departement'])['brevet_taux_reussite_general'].transform('mean')
    df['brevet_note_ecrit_departemental'] = df.groupby(['session', 'code_departement'])['brevet_note_ecrit_general'].transform('mean')
    df['taux_acces_6eme_3eme_national'] = df.groupby('session')['taux_acces_6eme_3eme'].transform('mean')
    df['taux_acces_6eme_3eme_departemental'] = df.groupby(['session', 'code_departement'])['taux_acces_6eme_3eme'].transform('mean')

    return df.drop(columns=['code_departement'])


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

    df = _ajouter_comparatifs_ivac(df, conn)

    df.to_sql('ivac', conn, if_exists='append', index=False)
    print(f"  ✓ {len(df)} lignes IVAC")


def ingerer_langues(conn):
    print("→ Chargement langues & options...")
    df = pd.read_csv(CSV_LANGUES, sep=';', encoding='utf-8-sig', dtype=str)

    # Le fichier source couvre aussi les lycées — hors périmètre ici (V1
    # limitée aux collèges, cf. decision_log.md S1.2).
    df = df[df["Type d'établissement"] == 'Collège']

    colonnes = {'UAI': 'uai', 'Enseignements': 'type_enseignement', 'Langues': 'langue'}
    df = df[list(colonnes.keys())].rename(columns=colonnes).dropna()
    df = df.drop_duplicates(subset=['uai', 'type_enseignement', 'langue'])

    uai_valides = set(pd.read_sql("SELECT uai FROM etablissements", conn)['uai'])
    df = df[df['uai'].isin(uai_valides)]

    df.to_sql('langues_offertes', conn, if_exists='append', index=False)
    print(f"  ✓ {len(df)} lignes langues/options ({df['uai'].nunique()} établissements)")


def ingerer_sections_sportives(conn):
    print("→ Chargement sections sportives...")
    df = pd.read_csv(CSV_SECTIONS_SPORTIVES, sep=';', encoding='utf-8-sig', dtype=str)
    df = df[df["Type d'établissement"] == 'Collège']

    df = df[['UAI', 'Sections scolaires']].rename(columns={'UAI': 'uai', 'Sections scolaires': 'sports'}).dropna()
    # Une ligne source peut lister plusieurs sports séparés par une virgule
    # (ex: "FOOTBALL EN SALLE (FUTSAL),KARATE") — une ligne par sport en base.
    df['sport'] = df['sports'].str.split(',')
    df = df.explode('sport')
    df['sport'] = df['sport'].str.strip().str.title()
    df = df[['uai', 'sport']].drop_duplicates()

    uai_valides = set(pd.read_sql("SELECT uai FROM etablissements", conn)['uai'])
    df = df[df['uai'].isin(uai_valides)]

    df.to_sql('sections_sportives', conn, if_exists='append', index=False)
    print(f"  ✓ {len(df)} lignes sections sportives ({df['uai'].nunique()} établissements)")


def ingerer_zones_academiques(conn):
    print("→ Chargement zones académiques (vacances scolaires)...")
    df = pd.read_csv(CSV_ZONES_ACADEMIQUES, sep=';', dtype=str)
    df['zone'] = df['zone'].replace('', None)
    df.to_sql('zones_academiques', conn, if_exists='append', index=False)
    n_avec_zone = df['zone'].notna().sum()
    print(f"  ✓ {len(df)} académies ({n_avec_zone} en zone A/B/C)")


def ingerer_vacances(conn):
    print("→ Chargement calendrier vacances scolaires...")
    fichiers = sorted(glob.glob(os.path.join(DIR, "vacances_scolaires_*.csv")))
    if not fichiers:
        print("  ⚠ aucun fichier vacances_scolaires_*.csv trouvé")
        return
    df = pd.concat([pd.read_csv(f, sep=';', dtype=str) for f in fichiers], ignore_index=True)
    df = df.drop_duplicates(subset=['annee_scolaire', 'zone', 'periode'])
    df.to_sql('vacances_scolaires', conn, if_exists='append', index=False)
    annees = ', '.join(sorted(df['annee_scolaire'].unique()))
    print(f"  ✓ {len(df)} lignes vacances scolaires ({df['annee_scolaire'].nunique()} année(s) : {annees})")


def _bornes_repartition(valeurs, repartition_pct):
    """
    Bornes de score correspondant à une répartition en % cumulés (ex: la
    répartition Stanine [10, 15, 50, 15, 10] de NOTATION_REPARTITION), sur
    une série de valeurs donnée. np.unique gère le cas de doublons aux
    bornes (valeurs très concentrées) en fusionnant les tranches concernées.
    """
    cumules = np.cumsum([0] + list(repartition_pct)) / 100.0
    return np.unique(valeurs.quantile(cumules).values)


def calculer_scores(conn):
    """
    Calcule 2 scores distincts (jamais affichés, cf. decision_log.md S13.4) :
    - score_resultats : taux de réussite + note écrite seuls (50/50) — sert
      au tri quand la question porte explicitement sur "les résultats".
    - score_principal : les 2 précédents + VA taux + VA note (25% chacun) —
      sert au tri "meilleur collège" et à dériver la notation en lettres.
    Chaque indicateur est normalisé min-max par session (comparable entre
    établissements de la même année uniquement, jamais d'une année à
    l'autre).

    VA absente (~25% des établissements, VA non publiée par le Ministère
    pour ces établissements cette session-là, cf. decision_log.md) ->
    substituée par 0 dans score_principal. La VA est une mesure d'écart à
    un résultat attendu, centrée sur 0 par construction (vérifié
    empiriquement : moyenne entre -0.94 et -0.73 selon la session pour le
    taux, quasi 0 pour la note) — 0 revient donc à supposer "résultat
    conforme à l'attendu" en l'absence de preuve du contraire, sans
    avantager ni pénaliser l'établissement. Les bornes de normalisation
    (vt_min/vt_max/vn_min/vn_max) restent calculées sur les VRAIES valeurs
    de VA uniquement, jamais faussées par les zéros substitués. Résultat :
    score_principal et notation sont désormais calculables pour le même
    périmètre que score_resultats (tout établissement ayant taux + note).
    va_imputee (colonne scores) garde la trace de cette substitution,
    établissement par établissement, pour que l'interface puisse continuer
    à signaler une notation sans VA réelle derrière.
    """
    print("→ Calcul des scores...")
    df = pd.read_sql("""
        SELECT uai, session,
               brevet_taux_reussite_general,
               brevet_note_ecrit_general,
               brevet_va_taux_reussite_general,
               brevet_va_note_ecrit_general
        FROM ivac
        WHERE brevet_taux_reussite_general IS NOT NULL
          AND brevet_note_ecrit_general IS NOT NULL
    """, conn)

    df['score_resultats'] = None
    df['score_principal'] = None
    df['notation'] = None
    df['va_imputee'] = None

    for session in df['session'].unique():
        mask = df['session'] == session

        t_min = df.loc[mask, 'brevet_taux_reussite_general'].min()
        t_max = df.loc[mask, 'brevet_taux_reussite_general'].max()
        n_min = df.loc[mask, 'brevet_note_ecrit_general'].min()
        n_max = df.loc[mask, 'brevet_note_ecrit_general'].max()
        if t_max <= t_min or n_max <= n_min:
            continue  # session dégénérée (une seule valeur distincte) : pas de score calculable

        df.loc[mask, 'score_resultats'] = (
            (df.loc[mask, 'brevet_taux_reussite_general'] - t_min) / (t_max - t_min) * SCORE_RESULTATS_POIDS_TAUX +
            (df.loc[mask, 'brevet_note_ecrit_general'] - n_min) / (n_max - n_min) * SCORE_RESULTATS_POIDS_NOTE
        ) * 100

        # Bornes de normalisation VA : calculées sur les vraies valeurs
        # uniquement (mask_va), jamais sur les zéros substitués ci-dessous.
        mask_va = mask & df['brevet_va_taux_reussite_general'].notna() & df['brevet_va_note_ecrit_general'].notna()
        if not mask_va.any():
            continue

        vt_min = df.loc[mask_va, 'brevet_va_taux_reussite_general'].min()
        vt_max = df.loc[mask_va, 'brevet_va_taux_reussite_general'].max()
        vn_min = df.loc[mask_va, 'brevet_va_note_ecrit_general'].min()
        vn_max = df.loc[mask_va, 'brevet_va_note_ecrit_general'].max()
        if vt_max <= vt_min or vn_max <= vn_min:
            continue

        # score_principal calculé sur tout `mask` (même périmètre que
        # score_resultats), pas seulement mask_va : VA manquante -> 0.
        va_taux_utilise = df.loc[mask, 'brevet_va_taux_reussite_general'].fillna(0)
        va_note_utilise = df.loc[mask, 'brevet_va_note_ecrit_general'].fillna(0)

        df.loc[mask, 'score_principal'] = (
            (df.loc[mask, 'brevet_taux_reussite_general'] - t_min) / (t_max - t_min) * SCORE_PRINCIPAL_POIDS_TAUX +
            (df.loc[mask, 'brevet_note_ecrit_general'] - n_min) / (n_max - n_min) * SCORE_PRINCIPAL_POIDS_NOTE +
            (va_taux_utilise - vt_min) / (vt_max - vt_min) * SCORE_PRINCIPAL_POIDS_VA_TAUX +
            (va_note_utilise - vn_min) / (vn_max - vn_min) * SCORE_PRINCIPAL_POIDS_VA_NOTE
        ) * 100
        df.loc[mask, 'va_imputee'] = df.loc[mask, 'brevet_va_taux_reussite_general'].isna()

        scores_session = df.loc[mask, 'score_principal']
        bornes = _bornes_repartition(scores_session, NOTATION_REPARTITION)
        if len(bornes) < 2:
            continue
        labels = NOTATION_LETTRES[:len(bornes) - 1]
        df.loc[mask, 'notation'] = pd.cut(
            scores_session, bins=bornes, labels=labels, include_lowest=True
        ).astype(str)

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

    scores = df[['uai', 'session', 'score_principal', 'score_resultats', 'notation', 'badge_va', 'va_imputee']]
    scores.to_sql('scores', conn, if_exists='append', index=False)
    n_avec_notation = scores['notation'].notna().sum()
    n_va_imputee = scores['va_imputee'].fillna(False).astype(bool).sum()
    print(f"  ✓ {len(scores)} scores calculés ({n_avec_notation} avec notation complète, dont {n_va_imputee} avec VA imputée à 0)")


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
        CREATE INDEX IF NOT EXISTS idx_langues_uai
            ON langues_offertes(uai);
        CREATE INDEX IF NOT EXISTS idx_vacances_zone
            ON vacances_scolaires(zone, date_debut);
        CREATE INDEX IF NOT EXISTS idx_sections_sportives_uai
            ON sections_sportives(uai);
        CREATE INDEX IF NOT EXISTS idx_carte_scolaire_lookup
            ON carte_scolaire_troncons(code_insee, voie_normalisee);
    """)
    print("  ✓ 15 index créés")


def verifier(conn):
    print("\n=== VÉRIFICATION ===")
    for table in ['etablissements', 'ips', 'ivac', 'scores', 'referentiel_temporel',
                  'langues_offertes', 'vacances_scolaires', 'zones_academiques', 'sections_sportives',
                  'carte_scolaire_troncons']:
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

    resultats_non_null = conn.execute(
        "SELECT COUNT(*) FROM scores WHERE score_resultats IS NOT NULL"
    ).fetchone()[0]
    principal_non_null = conn.execute(
        "SELECT COUNT(*) FROM scores WHERE score_principal IS NOT NULL"
    ).fetchone()[0]
    notation_non_null = conn.execute(
        "SELECT COUNT(*) FROM scores WHERE notation IS NOT NULL"
    ).fetchone()[0]
    print(f"  score_resultats calculés (non NULL) : {resultats_non_null}")
    print(f"  score_principal calculés (non NULL) : {principal_non_null}")
    print(f"  notation calculées (non NULL) : {notation_non_null}")
    print("====================\n")


def main():
    print("=== INGESTION AGENT-ECOLES ===\n")
    conn = creer_connexion()
    creer_tables(conn)
    ingerer_annuaire(conn)
    ingerer_carte_scolaire(conn)
    ingerer_ips(conn)
    ingerer_ivac(conn)
    ingerer_langues(conn)
    ingerer_sections_sportives(conn)
    ingerer_zones_academiques(conn)
    ingerer_vacances(conn)
    calculer_scores(conn)
    inserer_referentiel(conn)
    creer_index(conn)
    verifier(conn)
    conn.close()
    print("✓ Ingestion terminée\n")


if __name__ == "__main__":
    main()
