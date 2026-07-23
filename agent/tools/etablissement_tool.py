"""agent/tools/etablissement_tool.py — Assemblage de la fiche établissement
complète (page web college/[uai]) : identité, résultats brevet, valeur
ajoutée, évolution multi-année, positionnement social, langues & options,
zone de vacances. Requête déterministe, AUCUN appel LLM."""

import sqlite3
import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH
from agent.tools.sql_tool import obtenir_evolution_etablissements


COLONNES_IDENTITE = """
    uai, nom, type_etablissement, secteur, adresse, code_postal, commune,
    code_departement, libelle_departement, code_academie, libelle_academie,
    libelle_region, telephone, mail, web, date_ouverture,
    appartenance_education_prioritaire, ulis, segpa,
    section_arts, section_cinema, section_theatre, section_sport,
    section_internationale, section_europeenne
"""

COLONNES_SECTION_BOOL = [
    "ulis", "segpa", "section_arts", "section_cinema", "section_theatre",
    "section_sport", "section_internationale", "section_europeenne",
]


def obtenir_fiche_etablissement(uai: str) -> dict:
    """
    Assemble toutes les données réelles nécessaires à la fiche établissement
    pour un UAI donné.

    Retourne : {"success": bool, "fiche": dict | None, "error": str | None}
    fiche est None si l'UAI est inconnu ou n'est pas un collège (pas une
    erreur — cas normal d'un UAI absent ou d'un lycée demandé par erreur).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            base_row = conn.execute(
                f"SELECT {COLONNES_IDENTITE} FROM etablissements "
                "WHERE uai = ? AND type_etablissement = 'Collège'",
                (uai,),
            ).fetchone()
            if base_row is None:
                return {"success": True, "fiche": None, "error": None}
            base = dict(base_row)

            # Session la plus récente POUR CET ÉTABLISSEMENT — pas la plus
            # récente du réseau entier (sql_tool.rechercher_etablissements_par_uai
            # fait ça, volontairement, pour son propre cas d'usage) : un
            # établissement absent de la toute dernière session doit quand
            # même afficher ses derniers résultats connus, pas disparaître.
            session = conn.execute(
                "SELECT MAX(session) AS s FROM ivac WHERE uai = ?", (uai,)
            ).fetchone()["s"]

            ivac_row = _obtenir_ivac_row(conn, uai, session) if session else None
            notation_row = conn.execute(
                "SELECT notation, badge_va, va_imputee FROM scores WHERE uai = ? AND session = ?",
                (uai, session),
            ).fetchone() if session else None

            identite = _construire_identite(base, notation_row)
            fiche = {
                "identite": identite,
                "brevet": _construire_brevet(ivac_row) if ivac_row else None,
                "valeur_ajoutee": _construire_valeur_ajoutee(ivac_row) if ivac_row else None,
                "evolution": _obtenir_evolution(uai),
                "positionnement_social": _obtenir_positionnement_social(conn, uai),
                "langues": _obtenir_langues(conn, uai),
                "sections_sportives": _obtenir_sections_sportives(conn, uai),
            }
            zone, prochaines_vacances = _obtenir_zone_et_vacances(conn, base["code_academie"])
            fiche["zone_vacances"] = zone
            fiche["prochaines_vacances"] = prochaines_vacances

            return {"success": True, "fiche": fiche, "error": None}
        finally:
            conn.close()
    except Exception as e:
        return {"success": False, "fiche": None, "error": str(e)}


def _construire_identite(base: dict, notation_row) -> dict:
    identite = dict(base)
    for col in COLONNES_SECTION_BOOL:
        identite[col] = bool(identite[col])
    identite["notation"] = notation_row["notation"] if notation_row else None
    identite["badge_va"] = notation_row["badge_va"] if notation_row else None
    identite["va_imputee"] = bool(notation_row["va_imputee"]) if notation_row else False
    return identite


def _obtenir_ivac_row(conn, uai: str, session: str) -> dict | None:
    row = conn.execute("""
        SELECT session, brevet_nb_candidats_general, brevet_taux_reussite_general,
               brevet_va_taux_reussite_general, brevet_note_ecrit_general,
               brevet_va_note_ecrit_general, taux_acces_6eme_3eme,
               nb_mentions_ab, nb_mentions_b, nb_mentions_tb, nb_mentions_total,
               brevet_taux_reussite_national, brevet_note_ecrit_national,
               brevet_taux_reussite_departemental, brevet_note_ecrit_departemental,
               taux_acces_6eme_3eme_national, taux_acces_6eme_3eme_departemental
        FROM ivac WHERE uai = ? AND session = ?
    """, (uai, session)).fetchone()
    return dict(row) if row else None


def _taux(nb, total):
    return round(100 * nb / total, 1) if nb is not None and total else None


def _construire_brevet(r: dict) -> dict:
    nb_candidats = r["brevet_nb_candidats_general"]
    mentions = [
        {"libelle": "Très bien", "nb_eleves": r["nb_mentions_tb"], "taux_pct": _taux(r["nb_mentions_tb"], nb_candidats)},
        {"libelle": "Bien", "nb_eleves": r["nb_mentions_b"], "taux_pct": _taux(r["nb_mentions_b"], nb_candidats)},
        {"libelle": "Assez bien", "nb_eleves": r["nb_mentions_ab"], "taux_pct": _taux(r["nb_mentions_ab"], nb_candidats)},
    ]
    sans_mention = None
    if nb_candidats is not None and r["nb_mentions_total"] is not None:
        sans_mention = nb_candidats - r["nb_mentions_total"]
    mentions.append({"libelle": "Sans mention", "nb_eleves": sans_mention, "taux_pct": _taux(sans_mention, nb_candidats)})

    return {
        "session": r["session"],
        "brevet_nb_candidats_general": nb_candidats,
        "brevet_taux_reussite_general": r["brevet_taux_reussite_general"],
        "brevet_note_ecrit_general": r["brevet_note_ecrit_general"],
        "taux_acces_6eme_3eme": r["taux_acces_6eme_3eme"],
        "taux_reussite_national": r["brevet_taux_reussite_national"],
        "taux_reussite_departemental": r["brevet_taux_reussite_departemental"],
        "note_ecrit_national": r["brevet_note_ecrit_national"],
        "note_ecrit_departemental": r["brevet_note_ecrit_departemental"],
        "taux_acces_6eme_3eme_national": r["taux_acces_6eme_3eme_national"],
        "taux_acces_6eme_3eme_departemental": r["taux_acces_6eme_3eme_departemental"],
        "mentions": mentions,
    }


def _construire_valeur_ajoutee(r: dict) -> dict | None:
    va_taux = r["brevet_va_taux_reussite_general"]
    va_note = r["brevet_va_note_ecrit_general"]
    if va_taux is None and va_note is None:
        return None
    taux_observe = r["brevet_taux_reussite_general"]
    note_observee = r["brevet_note_ecrit_general"]
    return {
        "va_taux": va_taux,
        "taux_observe": taux_observe,
        "taux_attendu": (taux_observe - va_taux) if (va_taux is not None and taux_observe is not None) else None,
        "va_note": va_note,
        "note_observee": note_observee,
        "note_attendue": (note_observee - va_note) if (va_note is not None and note_observee is not None) else None,
    }


def _obtenir_evolution(uai: str) -> list[dict]:
    resultat = obtenir_evolution_etablissements(uai_filtre=[uai], n_sessions=4, type_etablissement="Collège")
    if not resultat["success"]:
        return []
    return [
        {
            "session": r["session"],
            "brevet_taux_reussite_general": r["brevet_taux_reussite_general"],
            "brevet_note_ecrit_general": r["brevet_note_ecrit_general"],
            "notation": r["notation"],
            "badge_va": r["badge_va"],
        }
        for r in resultat["resultats"]
    ]


def _obtenir_positionnement_social(conn, uai: str) -> dict | None:
    # Décision actée : toujours l'IPS le plus récent disponible, sans lien
    # avec la session brevet affichée (pas de mise en correspondance de
    # période — clarifié explicitement pendant la conception).
    row = conn.execute("""
        SELECT annee_scolaire, ips_moyen, ecart_type_ips,
               ips_national, ips_academique, ips_departemental,
               ecart_type_ips_national, ecart_type_ips_departemental
        FROM ips WHERE uai = ? ORDER BY annee_scolaire DESC LIMIT 1
    """, (uai,)).fetchone()
    return dict(row) if row else None


def _obtenir_sections_sportives(conn, uai: str) -> list[str]:
    rows = conn.execute(
        "SELECT sport FROM sections_sportives WHERE uai = ? ORDER BY sport", (uai,)
    ).fetchall()
    return [row["sport"] for row in rows]


def _obtenir_langues(conn, uai: str) -> dict | None:
    rows = conn.execute(
        "SELECT type_enseignement, langue FROM langues_offertes WHERE uai = ?", (uai,)
    ).fetchall()
    if not rows:
        return None
    langues = {"lv1": [], "lv2": [], "lca": []}
    cle_par_type = {"LV1": "lv1", "LV2": "lv2", "LCA": "lca"}
    for row in rows:
        cle = cle_par_type.get(row["type_enseignement"])
        if cle:
            langues[cle].append(row["langue"])
    for cle in langues:
        langues[cle].sort()
    return langues


def _obtenir_zone_et_vacances(conn, code_academie: str) -> tuple[str | None, dict | None]:
    row = conn.execute(
        "SELECT zone FROM zones_academiques WHERE code_academie = ?", (code_academie,)
    ).fetchone()
    zone = row["zone"] if row else None
    if not zone:
        return None, None

    vac = conn.execute("""
        SELECT periode, date_debut, date_fin FROM vacances_scolaires
        WHERE type_periode = 'vacances' AND zone IN (?, 'TOUTES') AND date_debut >= ?
        ORDER BY date_debut ASC LIMIT 1
    """, (zone, date.today().isoformat())).fetchone()
    prochaines_vacances = {"zone": zone, **dict(vac)} if vac else None
    return zone, prochaines_vacances
