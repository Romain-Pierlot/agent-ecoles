"""agent/tools/recherche_tool.py — Recherche libre pour la page /recherche
(web) : matching en sous-chaîne, insensible à la casse et aux accents, sur
le nom des établissements et des communes. Requête déterministe, AUCUN
appel LLM.

Distinct des deux autres résolutions par nom déjà en place dans le
projet :
- sql_tool.rechercher_etablissements_par_nom : résout un nom déjà énoncé
  par l'agent conversationnel, avec un filtrage strict qui élimine les
  faux positifs sur les noms composés (ex: "Saint-Joseph" ne doit pas
  remonter "Saint-Joseph de Cluny").
- hierarchie_tool : résout un slug d'URL déjà normalisé (égalité stricte
  après slugification), pas une saisie libre.
Ici on répond à une saisie libre d'un visiteur qui tape progressivement
dans un champ de recherche : le matching doit au contraire être large
(sous-chaîne, pas égalité), donc une fonction dédiée plutôt que réutiliser
l'une des deux ci-dessus.

Le matching accent/casse-insensible est fait au niveau SQL via une fonction
Python enregistrée dans SQLite (`conn.create_function`) — même pattern que
`haversine` dans geo_tool.py — plutôt que de rapatrier l'ensemble des
~14k établissements/~4300 communes en Python à chaque appel pour les
filtrer ensuite : contrairement aux autres endpoints (scopés à un
département ou une ville, donc naturellement bornés), la recherche est
nationale et doit rester bornée explicitement (cf. LIMITE_RESULTATS).
"""

import re
import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import (
    DB_PATH, NOTATION_LETTRES, RANG_NOTATION,
    Secteur, COLONNE_SECTION, COLONNES_SECTION_VALIDES,
)
from agent.tools.normalisation import normaliser_texte_base

# Borne par catégorie (établissements, communes) — une requête courte et
# fréquente ("e", "college") ne doit pas faire remonter des milliers de
# lignes pour une page qui n'en affiche qu'une quinzaine par défaut.
LIMITE_RESULTATS = 50

# Valeurs de `section` acceptées par `rechercher` -> vraie colonne SQL —
# dérivé de COLONNE_SECTION (config.py, source unique), avec les clés
# SectionSouhaitee traduites en str simples (valeur transmise telle quelle
# par l'API, cf. api/main.py). SectionSouhaitee.AUCUNE volontairement
# absente : "aucune section" n'est pas un filtre de colonne exploitable ici.
SECTIONS_VALIDES = {section.value: colonne for section, colonne in COLONNE_SECTION.items()}

# Valeurs de `dispositif` acceptées par `rechercher` — même univers que
# web/src/lib/dispositifs.ts::deriveDispositifsEducatifs : REP/REP+ (valeur
# de la colonne appartenance_education_prioritaire, vérifiée en base : ce
# sont les 2 seules valeurs non nulles réellement présentes) + ULIS/SEGPA
# (colonnes booléennes dédiées, pas la même colonne).
DISPOSITIFS_VALIDES = {"REP", "REP+", "ULIS", "SEGPA"}


def _construire_filtres_etablissements(
    secteur: str = None, dispositif: str = None, section: str = None, notation_min: str = None,
) -> tuple[str, str, list]:
    """
    Construit la clause SQL (fragment `AND ...` par filtre actif) et la
    liste de paramètres à binder, après validation de chaque valeur contre
    une liste blanche — jamais une valeur non vérifiée interpolée dans le
    SQL. Filtres applicables aux établissements uniquement (pas aux
    communes, agrégats sans secteur/dispositif/section/notation individuels
    — cf. discussion de conception, seul leur tri par nom reste pertinent).

    Retourne (erreur, clause_sql, params) : erreur=None et clause_sql="" si
    aucun filtre n'est demandé ; erreur non-None (clause_sql/params ignorés
    par l'appelant dans ce cas) si une valeur ne correspond à aucune liste
    blanche connue.
    """
    clauses = []
    params = []

    if secteur is not None:
        if secteur not in (Secteur.PUBLIC.value, Secteur.PRIVE.value):
            return f"secteur invalide : {secteur}", "", []
        clauses.append("AND e.secteur = ?")
        params.append(secteur)

    if dispositif is not None:
        if dispositif not in DISPOSITIFS_VALIDES:
            return f"dispositif invalide : {dispositif}", "", []
        if dispositif == "ULIS":
            clauses.append("AND e.ulis = 1")
        elif dispositif == "SEGPA":
            clauses.append("AND e.segpa = 1")
        else:  # "REP" ou "REP+" : valeur de colonne texte, pas un booléen dédié
            clauses.append("AND e.appartenance_education_prioritaire = ?")
            params.append(dispositif)

    if section is not None:
        colonne = SECTIONS_VALIDES.get(section)
        if colonne is None or colonne not in COLONNES_SECTION_VALIDES:
            return f"section invalide : {section}", "", []
        clauses.append(f"AND e.{colonne} = 1")

    if notation_min is not None:
        if notation_min not in RANG_NOTATION:
            return f"notation_min invalide : {notation_min}", "", []
        rang_min = RANG_NOTATION[notation_min]
        lettres_autorisees = [lettre for lettre, rang in RANG_NOTATION.items() if rang <= rang_min]
        placeholders = ",".join("?" for _ in lettres_autorisees)
        clauses.append(f"AND s.notation IN ({placeholders})")
        params.extend(lettres_autorisees)

    return None, " ".join(clauses), params


def _order_by_etablissements(tri: str, direction: str) -> str:
    """
    Construit la clause ORDER BY des établissements selon `tri`/`direction`
    (déjà validés par l'appelant). Les valeurs manquantes (notation ou taux
    de réussite absents) sont toujours classées en dernier, quel que soit
    `direction` — même règle que le tri côté client existant
    (FiltresEtListeColleges.tsx) : une donnée absente n'est ni la meilleure
    ni la pire, inverser le sens ne doit pas la faire remonter.
    """
    if tri == "alphabetique":
        sens = "ASC" if direction == "asc" else "DESC"
        return f"ORDER BY e.nom {sens}"

    if tri == "reussite":
        sens = "DESC" if direction == "desc" else "ASC"
        return (
            "ORDER BY (v.brevet_taux_reussite_general IS NULL) ASC, "
            f"v.brevet_taux_reussite_general {sens}, e.nom ASC"
        )

    # tri == "notation" (défaut). Rang 0 = A+ (meilleure notation) ... 4 = B
    # (pire) -- cf. config.RANG_NOTATION. direction="desc" (défaut) signifie
    # "meilleure notation en premier", donc un ORDER BY ASCENDANT sur ce
    # rang : l'inversion est volontaire (même convention que le tri
    # "notation" du front, pas une erreur de signe à corriger).
    sens = "ASC" if direction == "desc" else "DESC"
    lettres_connues_sql = ",".join(f"'{lettre}'" for lettre in RANG_NOTATION)
    rang_case = "CASE s.notation " + " ".join(
        f"WHEN '{lettre}' THEN {rang}" for lettre, rang in RANG_NOTATION.items()
    ) + f" ELSE {len(NOTATION_LETTRES)} END"
    return (
        f"ORDER BY (CASE WHEN s.notation IN ({lettres_connues_sql}) THEN 0 ELSE 1 END) ASC, "
        f"{rang_case} {sens}, e.nom ASC"
    )


def _order_by_communes(tri_communes: str, direction_communes: str) -> str:
    """
    Construit la clause ORDER BY des communes selon `tri_communes`/
    `direction_communes` (déjà validés par l'appelant). Pas de "notation"
    possible ici (agrégat, cf. rechercher) : seuls le nom, le taux de
    réussite moyen et le nombre d'établissements sont des critères de tri
    pertinents pour une commune.

    Même règle que _order_by_etablissements : une commune sans taux de
    réussite moyen (cas théorique, absence de collège avec donnée brevet)
    reste toujours en dernier, quel que soit `direction_communes`.
    """
    if tri_communes == "nb_etablissements":
        sens = "DESC" if direction_communes == "desc" else "ASC"
        return f"ORDER BY nb_etablissements {sens}, e.commune ASC"

    if tri_communes == "reussite":
        sens = "DESC" if direction_communes == "desc" else "ASC"
        return (
            "ORDER BY (taux_reussite_moyen IS NULL) ASC, "
            f"taux_reussite_moyen {sens}, e.commune ASC"
        )

    # tri_communes == "alphabetique" (défaut) -- direction_communes="asc"
    # (défaut) reproduit le tri actuel (ORDER BY e.commune, sans clause
    # explicite = ascendant), pas d'inversion de signe ici contrairement à
    # la notation des établissements.
    sens = "ASC" if direction_communes == "asc" else "DESC"
    return f"ORDER BY e.commune {sens}"


def _echapper_like(texte: str) -> str:
    """
    Échappe les métacaractères LIKE (%, _) et le caractère d'échappement
    lui-même. Sans ça, une saisie contenant "%" ou "_" élargirait/fausserait
    silencieusement le matching (ce sont des jokers SQL) au lieu d'être
    traitée comme du texte littéral — pas une injection SQL (le paramètre
    reste bindé), mais une corruption silencieuse du résultat.
    """
    return texte.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _normaliser_recherche(texte: str) -> str:
    """
    Normalisation utilisée pour le matching (côté requête ET côté colonnes,
    via la fonction SQL enregistrée dans `rechercher`) : accents/casse (cf.
    normaliser_texte_base) puis tiret et apostrophe (droite et
    typographique) repliés en espace. Sans ce repli, une recherche
    "saint denis" ne retrouvait pas "Saint-Denis", et "isle adam" ne
    retrouvait pas la commune réelle "L'Isle-Adam" — la plupart des
    visiteurs ne tapent pas la ponctuation exacte d'un nom composé.

    Distincte de sql_tool._normaliser_nom/_normaliser_zone_administrative :
    celles-ci comparent un nom à une égalité stricte pour l'agent
    conversationnel, un usage différent qui n'a pas besoin de ce repli
    supplémentaire (et qu'on ne modifie pas ici pour ne rien y régresser).
    """
    texte = normaliser_texte_base(texte)
    texte = re.sub(r"[-'’]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def rechercher(
    query: str,
    limite: int = LIMITE_RESULTATS,
    secteur: str = None,
    dispositif: str = None,
    section: str = None,
    notation_min: str = None,
    tri: str = "notation",
    direction: str = "desc",
    tri_communes: str = "alphabetique",
    direction_communes: str = "asc",
) -> dict:
    """
    Recherche les collèges et communes dont le nom contient `query` (sous-
    chaîne, accent/casse-insensible). Exclut les SEGPA/sections rattachées
    (même exclusion que rechercher_etablissements_par_nom : ce sont des
    sous-structures internes, pas des établissements comparables).

    `limite` : borne par catégorie, paramétrable pour réutiliser la même
    fonction pour la page de résultats (LIMITE_RESULTATS, défaut) et pour
    l'autocomplétion (petite valeur, ex. 4 — même matching, pas de logique
    dupliquée entre les deux usages).

    `secteur`/`dispositif`/`section`/`notation_min` : filtres optionnels,
    établissements uniquement (cf. _construire_filtres_etablissements pour
    le détail des valeurs acceptées et des listes blanches). Le LIMIT
    s'applique après ces filtres, donc etablissements_tronques reste exact
    pour n'importe quelle combinaison — contrairement à un filtrage a
    posteriori sur un lot déjà tronqué (cf. bug d'origine de cette passe).

    `tri`/`direction` : ordre des établissements (cf. _order_by_etablissements
    pour le détail des valeurs et de la règle "donnée manquante toujours en
    dernier"). `tri_communes`/`direction_communes` : même principe pour les
    communes, avec des critères différents (pas de "notation" possible pour
    un agrégat) — cf. _order_by_communes.

    Retourne : {"success": bool, "session_utilisee": str | None,
        "taux_reussite_national": float | None,
        "etablissements": [{"uai", "nom", "secteur", "notation", "badge_va",
            "va_imputee", "appartenance_education_prioritaire", "ulis",
            "segpa", "section_arts", "section_cinema", "section_theatre",
            "section_sport", "section_internationale", "section_europeenne",
            "brevet_taux_reussite_general", "libelle_region",
            "code_departement", "libelle_departement", "commune"}],
        "communes": [{"commune", "code_departement", "libelle_departement",
            "libelle_region", "nb_etablissements", "taux_reussite_moyen"}],
        "etablissements_total": int, "communes_total": int,
        "etablissements_tronques": bool, "communes_tronquees": bool,
        "error": str | None}
    "taux_reussite_national" : taux national de la session utilisée (même
    convention que VilleHub) — récupéré indépendamment du nombre de
    résultats établissements, pour rester correct même si la recherche ne
    remonte que des communes.
    "etablissements_total"/"communes_total" : vrai total filtré (COUNT(*)
    sur le même WHERE, sans LIMIT) — pas juste "au moins limite", le vrai
    chiffre, quel que soit le nombre de résultats réellement matchés.
    "etablissements_tronques"/"communes_tronquees" : True si la liste
    retournée (bornée à `limite`) est plus courte que le total réel —
    dérivé de la comparaison ci-dessus, pas d'une simple égalité à
    LIMITE_RESULTATS (qui ne donnait qu'une borne basse).

    Chaque résultat porte sa lignée géographique complète (contrairement à
    SousDivision, pensé pour un contexte où le parent géo est déjà connu par
    la page hub) — les résultats de recherche viennent potentiellement de
    partout en France. Établissements triés par notation décroissante (même
    convention que la page ville, cf. hierarchie_tool.obtenir_colleges_ville) ;
    communes triées par nom.
    """
    erreur_filtres, clause_filtres, params_filtres = _construire_filtres_etablissements(
        secteur, dispositif, section, notation_min
    )
    if erreur_filtres is None and tri not in ("notation", "reussite", "alphabetique"):
        erreur_filtres = f"tri invalide : {tri}"
    if erreur_filtres is None and direction not in ("asc", "desc"):
        erreur_filtres = f"direction invalide : {direction}"
    if erreur_filtres is None and tri_communes not in ("alphabetique", "reussite", "nb_etablissements"):
        erreur_filtres = f"tri_communes invalide : {tri_communes}"
    if erreur_filtres is None and direction_communes not in ("asc", "desc"):
        erreur_filtres = f"direction_communes invalide : {direction_communes}"
    if erreur_filtres:
        return {
            "success": False, "session_utilisee": None, "taux_reussite_national": None,
            "etablissements": [], "communes": [], "etablissements_total": 0, "communes_total": 0,
            "etablissements_tronques": False, "communes_tronquees": False, "error": erreur_filtres,
        }
    ordre_by_etablissements = _order_by_etablissements(tri, direction)
    ordre_by_communes = _order_by_communes(tri_communes, direction_communes)

    requete_normalisee = _normaliser_recherche(query)
    if not requete_normalisee:
        # Une chaîne vide est une sous-chaîne de n'importe quoi : bug déjà
        # rencontré une fois sur ce projet (cf. decision_log.md,
        # interpreter_precision) — jamais laisser une saisie vide matcher
        # silencieusement tout le monde.
        return {
            "success": True, "session_utilisee": None, "taux_reussite_national": None,
            "etablissements": [], "communes": [], "etablissements_total": 0, "communes_total": 0,
            "etablissements_tronques": False, "communes_tronquees": False, "error": None,
        }

    motif = f"%{_echapper_like(requete_normalisee)}%"

    conn = sqlite3.connect(DB_PATH)
    conn.create_function("normaliser", 1, _normaliser_recherche)
    conn.row_factory = sqlite3.Row
    try:
        session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
        if session is None:
            return {
                "success": True, "session_utilisee": None, "taux_reussite_national": None,
                "etablissements": [], "communes": [], "etablissements_total": 0, "communes_total": 0,
                "etablissements_tronques": False, "communes_tronquees": False, "error": None,
            }

        taux_national_row = conn.execute(
            "SELECT brevet_taux_reussite_national FROM ivac WHERE session = ? LIMIT 1", (session,)
        ).fetchone()
        taux_reussite_national = taux_national_row["brevet_taux_reussite_national"] if taux_national_row else None

        rows_etab = conn.execute(f"""
            SELECT e.uai, e.nom, e.secteur, e.libelle_region, e.code_departement,
                   e.libelle_departement, e.commune,
                   e.appartenance_education_prioritaire, e.ulis, e.segpa,
                   e.section_arts, e.section_cinema, e.section_theatre,
                   e.section_sport, e.section_internationale, e.section_europeenne,
                   v.brevet_taux_reussite_general,
                   s.notation, s.badge_va, s.va_imputee
            FROM etablissements e
            JOIN scores s ON e.uai = s.uai
            JOIN ivac v ON e.uai = v.uai AND v.session = s.session
            WHERE e.type_etablissement = 'Collège'
              AND e.nom NOT LIKE '%Section d%' AND e.nom NOT LIKE '%SEGPA%'
              AND normaliser(e.nom) LIKE ? ESCAPE '\\'
              AND s.session = ?
              {clause_filtres}
            {ordre_by_etablissements}
            LIMIT ?
        """, (motif, session, *params_filtres, limite)).fetchall()

        etablissements = [
            {
                "uai": r["uai"], "nom": r["nom"], "secteur": r["secteur"],
                "notation": r["notation"], "badge_va": r["badge_va"],
                "va_imputee": bool(r["va_imputee"]),
                "appartenance_education_prioritaire": r["appartenance_education_prioritaire"],
                "ulis": bool(r["ulis"]), "segpa": bool(r["segpa"]),
                "section_arts": bool(r["section_arts"]), "section_cinema": bool(r["section_cinema"]),
                "section_theatre": bool(r["section_theatre"]), "section_sport": bool(r["section_sport"]),
                "section_internationale": bool(r["section_internationale"]),
                "section_europeenne": bool(r["section_europeenne"]),
                "brevet_taux_reussite_general": r["brevet_taux_reussite_general"],
                "libelle_region": r["libelle_region"], "code_departement": r["code_departement"],
                "libelle_departement": r["libelle_departement"], "commune": r["commune"],
            }
            for r in rows_etab
        ]
        # Pas de tri Python supplémentaire ici : l'ORDER BY SQL ci-dessus
        # (cf. _order_by_etablissements) fait foi, paramétré par tri/direction
        # — un second tri fixe sur la notation serait faux dès que
        # tri="reussite"/"alphabetique" est demandé.

        # Total réel (même WHERE, sans LIMIT) -- un simple "== limite" ne
        # donne qu'une borne basse ("au moins 50"), pas le vrai chiffre
        # (cf. retour utilisateur : "50+" partout n'est pas assez informatif
        # pour un vrai produit). Réutilise motif/session/clause_filtres/
        # params_filtres déjà construits : même filtre, jamais retapé.
        etablissements_total = conn.execute(f"""
            SELECT COUNT(*) AS total
            FROM etablissements e
            JOIN scores s ON e.uai = s.uai
            JOIN ivac v ON e.uai = v.uai AND v.session = s.session
            WHERE e.type_etablissement = 'Collège'
              AND e.nom NOT LIKE '%Section d%' AND e.nom NOT LIKE '%SEGPA%'
              AND normaliser(e.nom) LIKE ? ESCAPE '\\'
              AND s.session = ?
              {clause_filtres}
        """, (motif, session, *params_filtres)).fetchone()["total"]
        etablissements_tronques = len(etablissements) < etablissements_total

        rows_commune = conn.execute(f"""
            SELECT e.commune, e.code_departement, e.libelle_departement, e.libelle_region,
                   COUNT(*) AS nb_etablissements,
                   AVG(v.brevet_taux_reussite_general) AS taux_reussite_moyen
            FROM etablissements e
            JOIN scores s ON e.uai = s.uai
            JOIN ivac v ON e.uai = v.uai AND v.session = s.session
            WHERE e.type_etablissement = 'Collège'
              AND normaliser(e.commune) LIKE ? ESCAPE '\\'
              AND s.session = ?
            GROUP BY e.commune, e.code_departement
            {ordre_by_communes}
            LIMIT ?
        """, (motif, session, limite)).fetchall()

        communes = [
            {
                "commune": r["commune"], "code_departement": r["code_departement"],
                "libelle_departement": r["libelle_departement"], "libelle_region": r["libelle_region"],
                "nb_etablissements": r["nb_etablissements"],
                "taux_reussite_moyen": r["taux_reussite_moyen"],
            }
            for r in rows_commune
        ]

        # Même principe que pour les établissements : total réel via COUNT(*)
        # sur le même regroupement (commune, code_departement), sans LIMIT.
        communes_total = conn.execute(f"""
            SELECT COUNT(*) AS total FROM (
                SELECT 1
                FROM etablissements e
                JOIN scores s ON e.uai = s.uai
                JOIN ivac v ON e.uai = v.uai AND v.session = s.session
                WHERE e.type_etablissement = 'Collège'
                  AND normaliser(e.commune) LIKE ? ESCAPE '\\'
                  AND s.session = ?
                GROUP BY e.commune, e.code_departement
            )
        """, (motif, session)).fetchone()["total"]
        communes_tronquees = len(communes) < communes_total

        return {
            "success": True, "session_utilisee": session, "taux_reussite_national": taux_reussite_national,
            "etablissements": etablissements, "communes": communes,
            "etablissements_total": etablissements_total, "communes_total": communes_total,
            "etablissements_tronques": etablissements_tronques, "communes_tronquees": communes_tronquees,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False, "session_utilisee": None, "taux_reussite_national": None,
            "etablissements": [], "communes": [], "etablissements_total": 0, "communes_total": 0,
            "etablissements_tronques": False, "communes_tronquees": False, "error": str(e),
        }
    finally:
        conn.close()
