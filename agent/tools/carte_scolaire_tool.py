"""
carte_scolaire_tool.py — Rapprochement adresse -> collège de secteur

Rattachement officiel (carte scolaire du Ministère, collèges publics
uniquement) à partir d'une adresse. Cf. docs/exploration/
etude_matching_carte_scolaire.md pour la méthode validée empiriquement
(58,8% de correspondance exacte sur 250 adresses réelles) et
docs/journal_de_bord.md pour la décision de conception (3 états + sous-cas
multi-secteur).

Même pattern que geo_tool.py : connexion SQLite via DB_PATH, retour dict
{success, ..., error}, aucune dépendance à FastAPI ici (orchestrateur pur,
testable isolément).
"""

import re
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH, SECTEUR_RAYON_REPLI_KM, SECTEUR_MAX_COLLEGES_ALENTOURS, SECTEUR_NB_SUGGESTIONS_ADRESSE
from agent.tools.geo_tool import (
    geocoder_suggestions, _normaliser_nom_commune, trouver_etablissements_dans_rayon, haversine,
)

_DB_ABS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
)


def _parite_numero(numero: int) -> str:
    return "P" if numero % 2 == 0 else "I"


def _ligne_vers_college(row: sqlite3.Row) -> dict:
    """Forme commune à trouver_college_secteur (jointure carte_scolaire_troncons)
    et à l'enrichissement de trouver_etablissements_dans_rayon (repli
    alentours) — mêmes clés attendues par api/schemas.py::CollegeSecteurItem/
    CollegeAlentourItem et par web/src/lib/dispositifs.ts::deriveBadgesDispositifs
    côté front (mêmes noms de colonnes que EntiteAvecDispositifs)."""
    return {
        "uai": row["code_rne"] if "code_rne" in row.keys() else row["uai"],
        "nom": row["nom"],
        "commune": row["commune"],
        "secteur": row["secteur"],
        "libelle_region": row["libelle_region"],
        "code_departement": row["code_departement"],
        "libelle_departement": row["libelle_departement"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "notation": row["notation"],
        "badge_va": row["badge_va"],
        "appartenance_education_prioritaire": row["appartenance_education_prioritaire"],
        "ulis": bool(row["ulis"]),
        "segpa": bool(row["segpa"]),
        "section_arts": bool(row["section_arts"]),
        "section_cinema": bool(row["section_cinema"]),
        "section_theatre": bool(row["section_theatre"]),
        "section_sport": bool(row["section_sport"]),
        "section_internationale": bool(row["section_internationale"]),
        "section_europeenne": bool(row["section_europeenne"]),
    }


def _academie_pour_departement(code_departement: str | None) -> str | None:
    """Libellé de l'académie du département géocodé — nécessaire pour le
    message "contactez le rectorat de l'académie de {academie}" de l'état
    non déterminable. Dérivé de la table etablissements (chaque département
    n'a qu'une seule académie, cf. code_academie/libelle_academie déjà
    présents sur chaque établissement) plutôt qu'un nouveau jeu de données —
    aucune ligne garantie si le département n'a aucun établissement en base
    (cas non rencontré en pratique pour un département métropolitain)."""
    if not code_departement:
        return None
    try:
        conn = sqlite3.connect(_DB_ABS_PATH)
        try:
            row = conn.execute(
                "SELECT libelle_academie FROM etablissements WHERE code_departement = ? AND libelle_academie IS NOT NULL LIMIT 1",
                (code_departement,),
            ).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    except Exception:
        return None


def trouver_college_secteur(code_insee: str, numero: int, voie: str) -> dict:
    """
    Cherche en base les tronçons de carte_scolaire_troncons correspondant à
    (code_insee, voie normalisée) dont la plage [numero_debut, numero_fin]
    contient `numero`, avec une parité compatible ('PI' ou parité exacte).

    Un même code_rne peut apparaître sur plusieurs tronçons qui matchent
    (ex: parité et plage se recoupant) -> dédoublonné par code_rne, pas par
    ligne. Retourne :
    {
        "success": bool,
        "colleges_secteur": list[dict],  # 0, 1 ou N (multi-secteur), enrichis via JOIN etablissements
        "multi_secteur": bool,
        "error": str | None
    }
    """
    voie_normalisee = _normaliser_nom_commune(voie) if voie else None
    parite = _parite_numero(numero)
    try:
        conn = sqlite3.connect(_DB_ABS_PATH)
        conn.row_factory = sqlite3.Row
        try:
            session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
            rows = conn.execute(
                """
                SELECT DISTINCT
                    c.code_rne, e.nom, e.commune, e.secteur,
                    e.libelle_region, e.code_departement, e.libelle_departement,
                    e.latitude, e.longitude,
                    e.appartenance_education_prioritaire, e.ulis, e.segpa,
                    e.section_arts, e.section_cinema, e.section_theatre,
                    e.section_sport, e.section_internationale, e.section_europeenne,
                    s.notation, s.badge_va
                FROM carte_scolaire_troncons c
                JOIN etablissements e ON e.uai = c.code_rne
                LEFT JOIN scores s ON e.uai = s.uai AND s.session = ?
                WHERE c.code_insee = ?
                  AND c.voie_normalisee = ?
                  AND ? BETWEEN c.numero_debut AND c.numero_fin
                  AND (c.parite = 'PI' OR c.parite = ?)
                """,
                (session, code_insee, voie_normalisee, numero, parite),
            ).fetchall()
        finally:
            conn.close()

        colleges = [_ligne_vers_college(row) for row in rows]
        return {"success": True, "colleges_secteur": colleges, "multi_secteur": len(colleges) > 1, "error": None}
    except Exception as e:
        return {"success": False, "colleges_secteur": [], "multi_secteur": False, "error": str(e)}


def rapprocher_adresse_secteur(adresse: str) -> dict:
    """
    Orchestrateur pur du rapprochement (pas de repli "alentours" ici, cf.
    resoudre_secteur qui l'ajoute par-dessus). Détermine un état parmi :
    - "trouve"            : exactement 1 collège de secteur identifié
    - "multi_secteur"     : plusieurs collèges de secteur légitimes
    - "non_determinable"  : adresse reconnue mais numéro non résolu par BAN,
                            ou reconnue seulement au niveau ville, ou numéro
                            hors couverture du CSV
    - "adresse_ambigue"   : la saisie correspond à plusieurs communes
                            distinctes (adresse incomplète soumise sans
                            passer par le menu d'autocomplétion)
    - "adresse_non_reconnue" : échec du géocodage BAN lui-même

    `success` reflète le bon déroulement du PIPELINE, pas la reconnaissance
    de l'adresse : "adresse_non_reconnue"/"adresse_ambigue" sont des résultats
    normaux et attendus, retournés avec success=True. success=False est
    réservé aux pannes techniques réelles (ex: base SQLite inaccessible).

    Utilise geocoder_suggestions (jusqu'à SECTEUR_NB_SUGGESTIONS_ADRESSE
    candidats) plutôt que geocoder() (limit=1) : une saisie incomplète
    soumise directement (Entrée sans choisir dans le menu d'autocomplétion)
    peut matcher plusieurs communes différentes avec des scores de
    confiance BAN quasi identiques (vérifié empiriquement le 2026-07-23 : le
    score ne distingue PAS une adresse précise d'une adresse ambiguë) — le
    signal fiable est le nombre de citycodes distincts parmi les candidats,
    pas le score. Si un seul citycode ressort, on résout directement sur le
    premier candidat (déjà celui que BAN juge le plus probable).
    """
    resultat_suggestions = geocoder_suggestions(adresse, limite=SECTEUR_NB_SUGGESTIONS_ADRESSE)
    if not resultat_suggestions["success"]:
        return {
            "success": False, "etat": "adresse_non_reconnue",
            "adresse_normalisee": None, "latitude": None, "longitude": None,
            "academie": None, "colleges_secteur": [], "suggestions_ambigues": [],
            "commune": None, "code_departement": None,
            "error": resultat_suggestions["error"],
        }

    suggestions = resultat_suggestions["suggestions"]
    if not suggestions:
        return {
            "success": True, "etat": "adresse_non_reconnue",
            "adresse_normalisee": None, "latitude": None, "longitude": None,
            "academie": None, "colleges_secteur": [], "suggestions_ambigues": [],
            "commune": None, "code_departement": None, "error": None,
        }

    citycodes_distincts = {s["citycode"] for s in suggestions if s["citycode"]}
    if len(citycodes_distincts) > 1:
        return {
            "success": True, "etat": "adresse_ambigue",
            "adresse_normalisee": None, "latitude": None, "longitude": None,
            "academie": None, "colleges_secteur": [],
            "suggestions_ambigues": [{"label": s["label"], "type": s["type"]} for s in suggestions],
            # Plusieurs communes candidates distinctes à ce stade, aucune ne
            # peut être journalisée seule sans arbitraire.
            "commune": None, "code_departement": None, "error": None,
        }

    geo = suggestions[0]
    resultat_de_base = {
        "success": True, "adresse_normalisee": geo["label"],
        "latitude": geo["latitude"], "longitude": geo["longitude"],
        "academie": _academie_pour_departement(geo["depcode"]),
        "suggestions_ambigues": [],
        # Commune résolue par géocodage, pour l'analytics de recherche
        # (recherches_log) — jamais l'adresse brute tapée (donnée
        # personnelle), cf. journal_de_bord.md.
        "commune": geo["city"], "code_departement": geo["depcode"],
    }

    # Ville seule (pas d'adresse précise) : aucun numéro de rue à chercher,
    # inutile de tenter le rapprochement.
    if geo["type"] == "municipality" or not geo["housenumber"]:
        return {**resultat_de_base, "etat": "non_determinable", "colleges_secteur": [], "error": None}

    match_numero = re.match(r"^\d+", geo["housenumber"])
    if not match_numero:
        return {**resultat_de_base, "etat": "non_determinable", "colleges_secteur": [], "error": None}
    numero = int(match_numero.group())

    resultat = trouver_college_secteur(geo["citycode"], numero, geo["street"])
    if not resultat["success"]:
        return {**resultat_de_base, "success": False, "etat": "non_determinable",
                "colleges_secteur": [], "error": resultat["error"]}

    # Distance user <-> collège de secteur (la maquette l'affiche aussi sur
    # cette carte, pas seulement sur les alentours) — mêmes coordonnées déjà
    # géocodées, pas d'appel supplémentaire.
    colleges = [
        {**c, "distance_km": round(haversine(geo["latitude"], geo["longitude"], c["latitude"], c["longitude"]), 2)}
        for c in resultat["colleges_secteur"]
    ]
    if len(colleges) == 0:
        etat = "non_determinable"
    elif len(colleges) == 1:
        etat = "trouve"
    else:
        etat = "multi_secteur"

    return {**resultat_de_base, "etat": etat, "colleges_secteur": colleges, "error": None}


def resoudre_secteur(adresse: str) -> dict:
    """
    Orchestrateur de la route GET /secteur : combine rapprocher_adresse_secteur
    (rattachement officiel) et trouver_etablissements_dans_rayon (repli
    "alentours", geo_tool.py) selon l'état obtenu. Le repli ne s'applique que
    pour les 3 états qui ont des coordonnées géocodées (trouve/multi_secteur/
    non_determinable) — ni "adresse_non_reconnue" ni "adresse_ambigue" n'en
    ont (dans ce dernier cas, on ne sait pas encore laquelle des communes
    candidates choisir).

    Retourne :
    {
        "success": bool,
        "etat": "trouve" | "multi_secteur" | "non_determinable" | "adresse_ambigue" | "adresse_non_reconnue",
        "adresse_normalisee": str | None,
        "latitude": float | None, "longitude": float | None,
        "colleges_secteur": list[dict],
        "colleges_alentours": list[dict],  # rempli pour les 3 états avec coordonnées
        "suggestions_ambigues": list[dict],  # rempli seulement pour "adresse_ambigue"
        "error": str | None,
    }
    """
    resultat = rapprocher_adresse_secteur(adresse)
    if not resultat["success"] or resultat["etat"] in ("adresse_non_reconnue", "adresse_ambigue"):
        return {**resultat, "colleges_alentours": []}

    uais_deja_affiches = {c["uai"] for c in resultat["colleges_secteur"]}
    rows = trouver_etablissements_dans_rayon(
        resultat["latitude"], resultat["longitude"],
        rayon_km=SECTEUR_RAYON_REPLI_KM, type_etablissement="Collège",
    )
    alentours = [
        {**_ligne_vers_college(row), "distance_km": row["distance_km"]}
        for row in rows
        if row["uai"] not in uais_deja_affiches
    ][:SECTEUR_MAX_COLLEGES_ALENTOURS]

    return {**resultat, "colleges_alentours": alentours}
