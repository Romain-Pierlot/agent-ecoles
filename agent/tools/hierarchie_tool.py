"""agent/tools/hierarchie_tool.py — Résolution des routes région/département
(page web) et agrégats par sous-division. Requêtes déterministes, AUCUN
appel LLM. Distinct de sql_tool.resoudre_zone_administrative (résolution
d'un nom saisi en langage libre par l'agent conversationnel, tolérante aux
fautes de frappe) : ici on résout un slug d'URL déjà normalisé, selon
l'algorithme décidé en decision_log.md S15.4."""

import sqlite3
import re
import unicodedata

from config import DB_PATH


def _slugifier(texte: str) -> str:
    """
    Miroir Python de web/src/lib/slug.ts::slugifier — DOIT rester identique
    à cette fonction TypeScript (même algorithme : NFD, suppression des
    diacritiques, minuscules, non-alphanumérique -> "-"). Dupliqué faute de
    code partageable entre les deux runtimes ; toute évolution de l'un doit
    être répercutée sur l'autre.
    """
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = texte.lower()
    texte = re.sub(r"[^a-z0-9]+", "-", texte)
    return texte.strip("-")


def resoudre_region_par_slug(slug: str) -> dict | None:
    """Retourne {"libelle_region": str} ou None si aucune région ne slugifie vers `slug`."""
    conn = sqlite3.connect(DB_PATH)
    try:
        regions = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT libelle_region FROM etablissements WHERE libelle_region IS NOT NULL"
            )
        ]
    finally:
        conn.close()
    for libelle in regions:
        if _slugifier(libelle) == slug:
            return {"libelle_region": libelle}
    return None


def resoudre_departement_par_slug(slug: str, libelle_region: str) -> dict | None:
    """
    Extraction directe du code en tête du slug (ex: "01-ain" -> "01",
    "2a-corse-du-sud" -> "2A", "971-guadeloupe" -> "971"), puis requête
    exacte sur code_departement — jamais de comparaison slug par slug ici
    (cf. S15.4). Le nom en fin de slug ne sert qu'à la lisibilité de l'URL,
    il n'est pas revérifié. Alternatives testées dans l'ordre le plus
    spécifique d'abord (3 chiffres avant 2, sinon "971" match comme "97").
    """
    match = re.match(r"^(\d{3}|2[ab]|\d{2})-", slug, re.IGNORECASE)
    if not match:
        return None
    code = match.group(1).upper()

    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT code_departement, libelle_departement FROM etablissements "
            "WHERE code_departement = ? AND libelle_region = ? LIMIT 1",
            (code, libelle_region),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {"code_departement": row[0], "libelle_departement": row[1]}


def agreger_sous_divisions(niveau: str, valeur: str | None = None) -> dict:
    """
    Agrège les collèges par sous-division administrative :
    niveau="national" -> une ligne par région, aucun filtre (`valeur` ignoré) ;
    niveau="region" -> une ligne par département de la région `valeur`
    (libelle_region) ; niveau="departement" -> une ligne par commune du
    département `valeur` (code_departement).

    Pas de notation en lettres ici (cf. decision_log.md) : la notation
    combine résultats + valeur ajoutée d'un établissement précis, une notion
    qui n'a pas de sens transposée à un regroupement géographique — de plus,
    la médiane d'un groupe s'est révélée statistiquement quasi toujours
    classée dans la même lettre (A-, la tranche centrale qui couvre à elle
    seule 50% des établissements), rendant le signal inutilisable pour
    comparer des zones entre elles. Seul le taux de réussite moyen (continu,
    discriminant) sert d'indicateur agrégé.

    Retourne : {"success": bool, "session_utilisee": str | None,
        "global": {"nb_etablissements": int, "taux_reussite_moyen": float | None} | None,
        "sous_divisions": [{"code": str, "libelle": str,
            "nb_etablissements": int, "taux_reussite_moyen": float | None}], "error": str | None}
    "global" porte sur l'ENSEMBLE des établissements du périmètre (toute la
    région, ou tout le département) — sert aux 2 cartes d'agrégat du hero de
    la page hub, distinctes du tableau des sous-divisions.
    """
    if niveau not in ("national", "region", "departement"):
        return {"success": False, "session_utilisee": None, "global": None, "sous_divisions": [], "error": f"niveau invalide : {niveau}"}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
        if session is None:
            return {"success": True, "session_utilisee": None, "global": None, "sous_divisions": [], "error": None}

        if niveau == "national":
            filtre_sql, params = "", (session,)
        else:
            colonne_filtre = "libelle_region" if niveau == "region" else "code_departement"
            filtre_sql, params = f"AND e.{colonne_filtre} = ?", (session, valeur)

        rows = conn.execute(f"""
            SELECT e.libelle_region, e.code_departement, e.libelle_departement, e.commune,
                   v.brevet_taux_reussite_general
            FROM etablissements e
            JOIN scores s ON e.uai = s.uai
            JOIN ivac v ON e.uai = v.uai AND v.session = s.session
            WHERE e.type_etablissement = 'Collège'
              AND s.session = ?
              {filtre_sql}
        """, params).fetchall()

        groupes: dict[str, dict] = {}
        taux_global: list[float] = []
        for row in rows:
            if row["brevet_taux_reussite_general"] is not None:
                taux_global.append(row["brevet_taux_reussite_general"])

            if niveau == "national":
                cle, libelle = row["libelle_region"], row["libelle_region"]
            elif niveau == "region":
                cle, libelle = row["code_departement"], row["libelle_departement"]
            else:
                cle, libelle = row["commune"], row["commune"]
            if cle is None:
                continue
            groupe = groupes.setdefault(cle, {"libelle": libelle, "nb": 0, "taux": []})
            groupe["nb"] += 1
            if row["brevet_taux_reussite_general"] is not None:
                groupe["taux"].append(row["brevet_taux_reussite_general"])

        sous_divisions = [
            {
                "code": code,
                "libelle": g["libelle"],
                "nb_etablissements": g["nb"],
                "taux_reussite_moyen": (sum(g["taux"]) / len(g["taux"])) if g["taux"] else None,
            }
            for code, g in groupes.items()
        ]
        sous_divisions.sort(key=lambda d: d["libelle"] or "")

        global_stats = {
            "nb_etablissements": len(rows),
            "taux_reussite_moyen": (sum(taux_global) / len(taux_global)) if taux_global else None,
        }

        return {"success": True, "session_utilisee": session, "global": global_stats, "sous_divisions": sous_divisions, "error": None}
    except Exception as e:
        return {"success": False, "session_utilisee": None, "global": None, "sous_divisions": [], "error": str(e)}
    finally:
        conn.close()
