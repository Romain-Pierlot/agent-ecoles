"""agent/tools/hierarchie_tool.py — Résolution des routes région/département
(page web) et agrégats par sous-division. Requêtes déterministes, AUCUN
appel LLM. Distinct de sql_tool.resoudre_zone_administrative (résolution
d'un nom saisi en langage libre par l'agent conversationnel, tolérante aux
fautes de frappe) : ici on résout un slug d'URL déjà normalisé, selon
l'algorithme décidé en decision_log.md S15.4."""

import sqlite3
import re
import unicodedata

from config import DB_PATH, NOTATION_LETTRES, RANG_NOTATION


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


def resoudre_ville_par_slug(slug: str, code_departement: str) -> dict | None:
    """
    Retourne {"commune": str} ou None. Contrairement aux départements, les
    communes n'ont pas de code stable en base : on ne peut pas extraire un
    code en tête du slug (cf. resoudre_departement_par_slug). On itère donc
    les communes du département et on compare leur slug, comme
    resoudre_region_par_slug le fait pour les régions.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        communes = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT commune FROM etablissements "
                "WHERE code_departement = ? AND commune IS NOT NULL",
                (code_departement,),
            )
        ]
    finally:
        conn.close()
    for commune in communes:
        if _slugifier(commune) == slug:
            return {"commune": commune}
    return None


def obtenir_colleges_ville(commune: str, code_departement: str) -> dict:
    """
    Liste les collèges d'une commune avec les champs nécessaires aux cartes
    de la page ville (identité, secteur, dispositifs, notation, réussite
    brevet) — contrairement à agreger_sous_divisions, qui ne renvoie que des
    compteurs par sous-division. Même jointure (etablissements/scores/ivac
    sur la session la plus récente) que agreger_sous_divisions, pour que le
    nombre de collèges affiché ici corresponde exactement à celui déjà
    affiché sur la ligne de cette commune dans le tableau département.

    Retourne : {"success": bool, "session_utilisee": str | None,
        "global": {"nb_etablissements": int, "taux_reussite_moyen": float | None} | None,
        "nb_publics": int, "nb_prives": int,
        "taux_reussite_national": float | None,
        "colleges": [{"uai", "nom", "secteur", "notation", "badge_va",
            "va_imputee", "appartenance_education_prioritaire", "ulis",
            "segpa", "section_arts", "section_cinema", "section_theatre",
            "section_sport", "section_internationale", "section_europeenne",
            "brevet_taux_reussite_general"}], "error": str | None}
    Triée par notation décroissante par défaut (A+ -> B), conforme à la
    maquette ; le tri interactif (phase front à venir) part de cette liste
    déjà chargée, sans nouvel appel réseau.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
        if session is None:
            return {
                "success": True, "session_utilisee": None, "global": None,
                "nb_publics": 0, "nb_prives": 0, "taux_reussite_national": None,
                "colleges": [], "error": None,
            }

        rows = conn.execute("""
            SELECT e.uai, e.nom, e.secteur, e.appartenance_education_prioritaire,
                   e.ulis, e.segpa, e.section_arts, e.section_cinema, e.section_theatre,
                   e.section_sport, e.section_internationale, e.section_europeenne,
                   v.brevet_taux_reussite_general, v.brevet_taux_reussite_national,
                   s.notation, s.badge_va, s.va_imputee
            FROM etablissements e
            JOIN scores s ON e.uai = s.uai
            JOIN ivac v ON e.uai = v.uai AND v.session = s.session
            WHERE e.type_etablissement = 'Collège'
              AND e.commune = ? AND e.code_departement = ?
              AND s.session = ?
        """, (commune, code_departement, session)).fetchall()

        colleges = []
        taux_liste: list[float] = []
        taux_national = None
        nb_publics = nb_prives = 0
        for row in rows:
            r = dict(row)
            if r["brevet_taux_reussite_general"] is not None:
                taux_liste.append(r["brevet_taux_reussite_general"])
            if r["brevet_taux_reussite_national"] is not None:
                taux_national = r["brevet_taux_reussite_national"]
            if r["secteur"] == "Public":
                nb_publics += 1
            elif r["secteur"] == "Privé":
                nb_prives += 1
            colleges.append({
                "uai": r["uai"],
                "nom": r["nom"],
                "secteur": r["secteur"],
                "notation": r["notation"],
                "badge_va": r["badge_va"],
                "va_imputee": bool(r["va_imputee"]),
                "appartenance_education_prioritaire": r["appartenance_education_prioritaire"],
                "ulis": bool(r["ulis"]),
                "segpa": bool(r["segpa"]),
                "section_arts": bool(r["section_arts"]),
                "section_cinema": bool(r["section_cinema"]),
                "section_theatre": bool(r["section_theatre"]),
                "section_sport": bool(r["section_sport"]),
                "section_internationale": bool(r["section_internationale"]),
                "section_europeenne": bool(r["section_europeenne"]),
                "brevet_taux_reussite_general": r["brevet_taux_reussite_general"],
            })

        colleges.sort(key=lambda c: (RANG_NOTATION.get(c["notation"], len(NOTATION_LETTRES)), c["nom"]))

        global_stats = {
            "nb_etablissements": len(rows),
            "taux_reussite_moyen": (sum(taux_liste) / len(taux_liste)) if taux_liste else None,
        }

        return {
            "success": True, "session_utilisee": session, "global": global_stats,
            "nb_publics": nb_publics, "nb_prives": nb_prives,
            "taux_reussite_national": taux_national,
            "colleges": colleges, "error": None,
        }
    except Exception as e:
        return {
            "success": False, "session_utilisee": None, "global": None,
            "nb_publics": 0, "nb_prives": 0, "taux_reussite_national": None,
            "colleges": [], "error": str(e),
        }
    finally:
        conn.close()


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
