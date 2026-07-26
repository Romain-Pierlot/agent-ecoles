"""agent/tools/calendrier_tool.py — Calendrier des vacances scolaires
(page /calendrier-scolaire) : dates par zone (métropole + Corse) et par
territoire (outre-mer), à partir des tables zones_academiques et
vacances_scolaires déjà peuplées pour la fiche établissement (cf.
etablissement_tool.py::_obtenir_zone_et_vacances). Requête déterministe,
aucun appel LLM.
"""

import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH

# Valeurs de la colonne "zone" de vacances_scolaires qui relèvent de la
# métropole/Corse — tout le reste (Guadeloupe, Martinique, ...) est un
# territoire d'outre-mer. "TOUTES" désigne une période commune aux trois
# zones métropolitaines (la Corse a ses propres lignes quand elle diverge,
# cf. data/vacances_scolaires_2026_2027.csv).
ZONES_METROPOLE = {"A", "B", "C", "Corse", "TOUTES"}


def _lignes_recentes(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Pour chaque zone/territoire de vacances_scolaires, uniquement les
    lignes de son année scolaire la plus récente. Un simple
    MAX(annee_scolaire) global exclurait la Nouvelle-Calédonie et
    Wallis-et-Futuna, qui suivent l'année civile australe et sont donc
    étiquetées "2026" pendant que le reste du fichier est étiqueté
    "2026-2027" — un MAX par zone fonctionne pour les deux conventions
    sans cas particulier (comparaison de chaînes : "2026-2027" > "2026")."""
    return conn.execute("""
        SELECT v.zone, v.annee_scolaire, v.periode, v.type_periode, v.date_debut, v.date_fin
        FROM vacances_scolaires v
        INNER JOIN (
            SELECT zone, MAX(annee_scolaire) AS annee_scolaire
            FROM vacances_scolaires GROUP BY zone
        ) recent ON recent.zone = v.zone AND recent.annee_scolaire = v.annee_scolaire
        ORDER BY v.date_debut ASC
    """).fetchall()


def obtenir_calendrier_scolaire() -> dict:
    """
    Retourne :
    {
        "success": bool,
        "metropole": list[dict],   # zones A/B/C/Corse/TOUTES
        "outre_mer": list[dict],   # un territoire par valeur de "zone"
        "academies": list[dict],   # code_academie, libelle_academie, zone
        "error": str | None,
    }
    Chaque ligne de metropole/outre_mer :
    {zone, annee_scolaire, periode, type_periode, date_debut, date_fin}.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            lignes = [dict(row) for row in _lignes_recentes(conn)]
            academies = [
                dict(row) for row in conn.execute(
                    "SELECT code_academie, libelle_academie, zone FROM zones_academiques ORDER BY libelle_academie"
                ).fetchall()
            ]
        finally:
            conn.close()

        metropole = [ligne for ligne in lignes if ligne["zone"] in ZONES_METROPOLE]
        outre_mer = [ligne for ligne in lignes if ligne["zone"] not in ZONES_METROPOLE]

        return {
            "success": True, "metropole": metropole, "outre_mer": outre_mer,
            "academies": academies, "error": None,
        }
    except Exception as e:
        return {"success": False, "metropole": [], "outre_mer": [], "academies": [], "error": str(e)}
