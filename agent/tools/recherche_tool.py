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
from config import DB_PATH, NOTATION_LETTRES, RANG_NOTATION
from agent.tools.normalisation import normaliser_texte_base

# Borne par catégorie (établissements, communes) — une requête courte et
# fréquente ("e", "college") ne doit pas faire remonter des milliers de
# lignes pour une page qui n'en affiche qu'une quinzaine par défaut.
LIMITE_RESULTATS = 50


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


def rechercher(query: str, limite: int = LIMITE_RESULTATS) -> dict:
    """
    Recherche les collèges et communes dont le nom contient `query` (sous-
    chaîne, accent/casse-insensible). Exclut les SEGPA/sections rattachées
    (même exclusion que rechercher_etablissements_par_nom : ce sont des
    sous-structures internes, pas des établissements comparables).

    `limite` : borne par catégorie, paramétrable pour réutiliser la même
    fonction pour la page de résultats (LIMITE_RESULTATS, défaut) et pour
    l'autocomplétion (petite valeur, ex. 4 — même matching, pas de logique
    dupliquée entre les deux usages).

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
        "etablissements_tronques": bool, "communes_tronquees": bool,
        "error": str | None}
    "taux_reussite_national" : taux national de la session utilisée (même
    convention que VilleHub) — récupéré indépendamment du nombre de
    résultats établissements, pour rester correct même si la recherche ne
    remonte que des communes.
    "etablissements_tronques"/"communes_tronquees" : True si la liste
    correspondante a atteint LIMITE_RESULTATS — le compte affiché n'est
    alors pas le total réel, seulement une borne basse.

    Chaque résultat porte sa lignée géographique complète (contrairement à
    SousDivision, pensé pour un contexte où le parent géo est déjà connu par
    la page hub) — les résultats de recherche viennent potentiellement de
    partout en France. Établissements triés par notation décroissante (même
    convention que la page ville, cf. hierarchie_tool.obtenir_colleges_ville) ;
    communes triées par nom.
    """
    requete_normalisee = _normaliser_recherche(query)
    if not requete_normalisee:
        # Une chaîne vide est une sous-chaîne de n'importe quoi : bug déjà
        # rencontré une fois sur ce projet (cf. decision_log.md,
        # interpreter_precision) — jamais laisser une saisie vide matcher
        # silencieusement tout le monde.
        return {
            "success": True, "session_utilisee": None, "taux_reussite_national": None,
            "etablissements": [], "communes": [], "etablissements_tronques": False,
            "communes_tronquees": False, "error": None,
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
                "etablissements": [], "communes": [], "etablissements_tronques": False,
                "communes_tronquees": False, "error": None,
            }

        taux_national_row = conn.execute(
            "SELECT brevet_taux_reussite_national FROM ivac WHERE session = ? LIMIT 1", (session,)
        ).fetchone()
        taux_reussite_national = taux_national_row["brevet_taux_reussite_national"] if taux_national_row else None

        rows_etab = conn.execute("""
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
            ORDER BY e.nom
            LIMIT ?
        """, (motif, session, limite)).fetchall()

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
        etablissements.sort(key=lambda e: (RANG_NOTATION.get(e["notation"], len(NOTATION_LETTRES)), e["nom"]))
        # Un résultat exactement égal à la limite ne prouve pas qu'il n'y en
        # a pas plus (LIMIT coupe avant de savoir) — signalé au front pour
        # ne pas afficher un total comme s'il était exact (cf. test "e" :
        # 50/50 affichés comme si c'était le compte réel).
        etablissements_tronques = len(etablissements) == limite

        rows_commune = conn.execute("""
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
            ORDER BY e.commune
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
        communes_tronquees = len(communes) == limite

        return {
            "success": True, "session_utilisee": session, "taux_reussite_national": taux_reussite_national,
            "etablissements": etablissements, "communes": communes,
            "etablissements_tronques": etablissements_tronques, "communes_tronquees": communes_tronquees,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False, "session_utilisee": None, "taux_reussite_national": None,
            "etablissements": [], "communes": [], "etablissements_tronques": False,
            "communes_tronquees": False, "error": str(e),
        }
    finally:
        conn.close()
