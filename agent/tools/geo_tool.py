"""geo_tool.py — Outil de géolocalisation pour agent-ecoles (V2 — clés harmonisées)"""

import sqlite3
import requests
import math
import os
import re
import sys
import unicodedata

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import (
    DB_PATH, BAN_API_TIMEOUT_SECONDS, GEO_RAYON_DEFAUT_KM, GEO_RAYON_ENVIRONS_KM,
    DEPARTEMENTS_OUTRE_MER, SECTEUR_NB_SUGGESTIONS_ADRESSE,
)

# Migré le 2026-07-23 depuis https://api-adresse.data.gouv.fr/search/ :
# cette dernière renvoie des en-têtes HTTP "deprecation"/"sunset" (échéance
# 2026-01-31, déjà passée) et redirige en coulisses vers cette même URL
# (x-infra: gpf) — vérifié : réponses identiques au format près, migration
# à coût nul. Cf. doc officielle : https://data.geopf.fr/geocodage/openapi.yaml
BAN_API_URL = "https://data.geopf.fr/geocodage/search/"

# Nombre d'arrondissements par ville — borne la plage valide pour éviter de
# réécrire un numéro qui n'a rien à voir avec un arrondissement.
VILLES_ARRONDISSEMENT = {"paris": 20, "lyon": 9, "marseille": 16}


def _normaliser_arrondissement_sans_suffixe(adresse: str) -> str:
    """
    Ajoute le suffixe ordinal ("8e", "1er") à une ville + numéro
    d'arrondissement sans suffixe (ex: "Marseille 8" -> "Marseille 8e")
    avant l'appel à l'API BAN.

    Nécessaire car l'API interprète parfois un numéro nu après "Marseille"
    comme un numéro de rue plutôt qu'un arrondissement : "marseille 8" seul
    renvoyait "Route de Marseilles, Précy" (Cher, sans rapport), alors que
    "marseille 8e" résout correctement "Marseille 8e Arrondissement". Bug
    non reproduit sur Paris/Lyon dans les cas testés, mais corrigé de façon
    uniforme sur les 3 villes par prudence — un suffixe déjà présent
    (e/eme/ème) n'est jamais dupliqué, la chaîne ne matche simplement pas.
    """
    match = re.match(r'^\s*(paris|lyon|marseille)\s+(\d{1,2})\s*$', adresse, re.IGNORECASE)
    if not match:
        return adresse
    ville, numero_str = match.group(1), match.group(2)
    numero = int(numero_str)
    if not (1 <= numero <= VILLES_ARRONDISSEMENT[ville.lower()]):
        return adresse
    suffixe = "1er" if numero == 1 else f"{numero}e"
    return f"{ville} {suffixe}"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def geocoder(adresse_ou_ville: str) -> dict:
    adresse_ou_ville = _normaliser_arrondissement_sans_suffixe(adresse_ou_ville)
    champs_vides = {
        "latitude": None, "longitude": None, "label": None, "type": None,
        "city": None, "depcode": None,
        # housenumber/street/citycode : ajoutés pour le rapprochement
        # adresse -> collège de secteur (agent/tools/carte_scolaire_tool.py),
        # qui a besoin du numéro de rue exact et du code INSEE précis (y
        # compris par arrondissement Paris/Lyon/Marseille, citycode les
        # distingue déjà) plutôt que de re-parser `label` par regex. Purement
        # additif : aucun appelant existant (ex. recherche_geo) ne dépendait
        # de l'absence de ces clés.
        "housenumber": None, "street": None, "citycode": None,
    }
    try:
        response = requests.get(
            BAN_API_URL, params={"q": adresse_ou_ville, "limit": 1},
            timeout=BAN_API_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("features"):
            return {**champs_vides, "success": False,
                    "error": f"Adresse non trouvée : {adresse_ou_ville}"}
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]
        proprietes = feature["properties"]
        return {
            "success": True, "latitude": coords[1], "longitude": coords[0],
            "label": proprietes.get("label", adresse_ou_ville),
            "type": proprietes.get("type", "inconnu"),
            "city": proprietes.get("city"), "depcode": proprietes.get("depcode"),
            "housenumber": proprietes.get("housenumber"),
            "street": proprietes.get("street"),
            "citycode": proprietes.get("citycode"),
            "error": None
        }
    except requests.Timeout:
        return {**champs_vides, "success": False,
                "error": f"Timeout API BAN après {BAN_API_TIMEOUT_SECONDS}s"}
    except Exception as e:
        return {**champs_vides, "success": False, "error": str(e)}


def geocoder_suggestions(q: str, limite: int = SECTEUR_NB_SUGGESTIONS_ADRESSE) -> dict:
    """
    Autocomplétion adresse — contrairement à geocoder() (limit=1, prend le
    premier résultat BAN sans confirmation), retourne plusieurs candidats
    pour que l'utilisateur choisisse explicitement le sien avant validation.
    Nécessaire car une adresse tapée en partie (ex: "30 rue Jean") peut
    matcher plusieurs rues "Jean ..." dans des villes différentes — prendre
    le seul premier résultat BAN silencieusement donnerait un rattachement
    de secteur basé sur une adresse jamais réellement choisie par
    l'utilisateur (cf. retour utilisateur du 2026-07-23).

    Chaque suggestion porte les mêmes clés que geocoder() (label, type,
    latitude, longitude, city, depcode, housenumber, street, citycode) — pas
    seulement label/type — pour que carte_scolaire_tool.py puisse détecter
    une ambiguïté ENTRE COMMUNES (citycodes distincts parmi les candidats,
    cf. étude du 2026-07-23 : le score BAN ne distingue pas une adresse
    précise d'une adresse ambiguë, les deux ont des scores quasi identiques)
    et, si non ambigu, résoudre directement sur le premier candidat sans
    second appel réseau à geocoder(). La route API (/secteur/adresses)
    n'expose que label/type au front (SuggestionAdresse), les clés en plus
    sont ignorées silencieusement par Pydantic.
    """
    if not q or not q.strip():
        return {"success": True, "suggestions": [], "error": None}
    q = _normaliser_arrondissement_sans_suffixe(q)
    try:
        response = requests.get(
            BAN_API_URL, params={"q": q, "limit": limite},
            timeout=BAN_API_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        suggestions = []
        for f in data.get("features", []):
            proprietes = f["properties"]
            if not proprietes.get("label"):
                continue
            coords = f["geometry"]["coordinates"]
            suggestions.append({
                "label": proprietes.get("label"), "type": proprietes.get("type"),
                "latitude": coords[1], "longitude": coords[0],
                "city": proprietes.get("city"), "depcode": proprietes.get("depcode"),
                "housenumber": proprietes.get("housenumber"),
                "street": proprietes.get("street"),
                "citycode": proprietes.get("citycode"),
            })
        return {"success": True, "suggestions": suggestions, "error": None}
    except requests.Timeout:
        return {"success": False, "suggestions": [], "error": f"Timeout API BAN après {BAN_API_TIMEOUT_SECONDS}s"}
    except Exception as e:
        return {"success": False, "suggestions": [], "error": str(e)}


def trouver_etablissements_dans_rayon(latitude, longitude, rayon_km=None, type_etablissement="Collège"):
    if rayon_km is None:
        rayon_km = GEO_RAYON_DEFAUT_KM
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.create_function("haversine", 4, haversine)
    try:
        session = conn.execute("SELECT MAX(session) AS s FROM scores").fetchone()["s"]
        rows = conn.execute("""
            SELECT e.uai, e.nom, e.commune, e.secteur, e.type_etablissement,
                   e.latitude, e.longitude,
                   e.libelle_region, e.code_departement, e.libelle_departement,
                   e.appartenance_education_prioritaire, e.ulis, e.segpa,
                   e.section_arts, e.section_cinema, e.section_theatre,
                   e.section_sport, e.section_internationale, e.section_europeenne,
                   s.notation, s.badge_va,
                   ROUND(haversine(?, ?, e.latitude, e.longitude), 2) as distance_km
            FROM etablissements e
            LEFT JOIN scores s ON e.uai = s.uai AND s.session = ?
            WHERE e.latitude IS NOT NULL AND e.longitude IS NOT NULL
              AND e.type_etablissement = ?
              AND haversine(?, ?, e.latitude, e.longitude) <= ?
            ORDER BY distance_km ASC
        """, (latitude, longitude, session, type_etablissement, latitude, longitude, rayon_km)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def ligne_vers_college(row) -> dict:
    """Forme commune à carte_scolaire_tool.py::trouver_college_secteur
    (jointure carte_scolaire_troncons), à l'enrichissement de
    trouver_etablissements_dans_rayon ci-dessus (repli "alentours" de la
    carte scolaire, et établissements à proximité de la fiche établissement,
    cf. etablissement_tool.py) — mêmes clés attendues par api/schemas.py::
    CollegeSecteurItem et par web/src/lib/dispositifs.ts::deriveBadgesDispositifs
    côté front (mêmes noms de colonnes que EntiteAvecDispositifs). Accepte
    aussi bien un sqlite3.Row qu'un dict (les deux supportent .keys()/[])."""
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


def _normaliser_nom_commune(nom: str) -> str:
    """
    Minuscules, sans accents, tirets ET apostrophes traités comme des
    séparateurs de mots. L'apostrophe est repliée pour la même raison que le
    tiret : BAN retourne parfois "Rue de l'Arquebuse" quand une source
    administrative (carte scolaire) l'écrit "RUE DE L ARQUEBUSE" (déjà sans
    apostrophe) — sans ce repli les deux ne matchent jamais alors qu'elles
    désignent la même voie (cf. docs/exploration/etude_matching_carte_scolaire.md).
    """
    nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode("ascii")
    nom = nom.lower().replace("-", " ").replace("'", " ").strip()
    return re.sub(r"\s+", " ", nom)


def _racine_commune(nom: str) -> str:
    """
    Premier segment avant un vrai tiret dans le nom D'ORIGINE (pas après
    normalisation) — ex: "Neuilly-sur-Seine" -> "neuilly". Ne segmente PAS
    sur un simple espace : "Lyon 3e Arrondissement" doit rester entier,
    sinon il serait confondu à tort avec "Lyon" (bug trouvé en testant :
    les arrondissements de Lyon/Paris/Marseille sont des communes distinctes
    dans notre base, séparées par un espace, pas un tiret).
    """
    return _normaliser_nom_commune(nom.split("-")[0])


def candidats_zone_ambigue(nom_zone: str, type_etablissement: str = "Collège") -> list:
    """
    Détecte, dans notre PROPRE base (pas d'appel réseau), si un nom de zone
    correspond à plusieurs communes distinctes — deux formes d'ambiguïté :
    - homonyme exact : "Saint-Denis" existe dans 2 départements différents.
    - nom partiel : "Neuilly" correspond au premier mot de 5 communes
      distinctes (Neuilly-sur-Seine, Neuilly-Plaisance...) sans être
      lui-même un nom de commune complet dans notre périmètre.

    Retourne la liste des communes candidates ({commune, code_departement}),
    dédupliquée, triée par nom. Liste vide ou à 1 élément = pas d'ambiguïté
    détectable ici (comportement de géocodage inchangé dans ce cas) — ne
    déclenche une clarification qu'à partir de 2 candidats distincts.
    """
    cible = _normaliser_nom_commune(nom_zone)
    if not cible:
        return []

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT DISTINCT commune, code_departement
            FROM etablissements
            WHERE type_etablissement = ?
        """, (type_etablissement,)).fetchall()
    finally:
        conn.close()

    candidats = {}
    for row in rows:
        commune, depcode = row["commune"], row["code_departement"]
        normalise = _normaliser_nom_commune(commune)
        racine = _racine_commune(commune)
        if normalise == cible or racine == cible:
            candidats[(commune, depcode)] = {"commune": commune, "code_departement": depcode}

    return sorted(candidats.values(), key=lambda c: c["commune"])


def trouver_etablissements_par_commune(commune: str, code_departement: str, type_etablissement: str = "Collège") -> list:
    """
    Recherche exacte par commune — AUCUN rayon (S8.27) : quand la question
    ne mentionne qu'un nom de ville (pas une adresse précise), un rayon
    arbitraire n'a pas de sens — soit il déborde sur les communes voisines
    (ex: Toulouse en rayon 10km inclut Blagnac, Colomiers... 78 résultats
    contre 50 pour la seule commune de Toulouse), soit il pourrait couper
    une partie de la ville sur une commune très étendue. Le nom de commune
    seul, désambiguïsé par code_departement (des communes homonymes
    existent en France), est la correspondance la plus fidèle à "collèges
    à Toulouse" au sens strict.
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT uai, nom, commune, secteur, type_etablissement, latitude, longitude
            FROM etablissements
            WHERE commune = ? AND code_departement = ? AND type_etablissement = ?
        """, (commune, code_departement, type_etablissement)).fetchall()
        return [{**dict(row), "distance_km": None} for row in rows]
    finally:
        conn.close()


def recherche_geo(
    adresse_ou_ville: str, rayon_km: float = None, type_etablissement: str = "Collège",
    elargir_environs: bool = False,
) -> dict:
    """Retourne : {success, adresse_recherchee, adresse_normalisee, latitude, longitude,
    rayon_km, etablissements, nb_etablissements, error, commune_principale}"""
    geo = geocoder(adresse_ou_ville)
    if not geo["success"]:
        return {
            "success": False, "adresse_recherchee": adresse_ou_ville, "adresse_normalisee": None,
            "latitude": None, "longitude": None, "rayon_km": rayon_km,
            "etablissements": [], "nb_etablissements": 0, "error": geo["error"]
        }

    # "type": "municipality" = l'utilisateur n'a donné qu'un nom de ville
    # (pas une adresse précise) -> correspondance exacte sur la commune,
    # pas de rayon (S8.27). Adresse précise -> comportement inchangé
    # (rayon autour du point géocodé, pertinent dans ce cas).
    # elargir_environs=True (demande explicite type "et les environs")
    # bypasse cette règle : l'utilisateur a explicitement demandé un rayon
    # élargi, ce que S8.27 ne visait qu'à éviter par défaut.
    if geo["type"] == "municipality" and geo.get("city") and geo.get("depcode") and not elargir_environs:
        etablissements = trouver_etablissements_par_commune(geo["city"], geo["depcode"], type_etablissement)
        return {
            "success": True, "adresse_recherchee": adresse_ou_ville,
            "adresse_normalisee": geo["label"], "latitude": geo["latitude"], "longitude": geo["longitude"],
            "rayon_km": None, "etablissements": etablissements,
            "nb_etablissements": len(etablissements), "error": None,
            "commune_principale": geo.get("city"),
        }

    if rayon_km is None:
        # Élargissement explicite ("et les environs") : rayon volontairement
        # plus resserré que le rayon par défaut (GEO_RAYON_DEFAUT_KM, pensé
        # pour une adresse précise) — un rayon de 10 km ramène des communes
        # trop éloignées en zone dense (testé en région parisienne).
        rayon_km = GEO_RAYON_ENVIRONS_KM if elargir_environs else GEO_RAYON_DEFAUT_KM
    etablissements = trouver_etablissements_dans_rayon(geo["latitude"], geo["longitude"], rayon_km, type_etablissement)
    return {
        "success": True, "adresse_recherchee": adresse_ou_ville,
        "adresse_normalisee": geo["label"], "latitude": geo["latitude"], "longitude": geo["longitude"],
        "rayon_km": rayon_km, "etablissements": etablissements,
        "nb_etablissements": len(etablissements), "error": None,
        "commune_principale": geo.get("city"),
    }


def rechercher_etablissements_region_departement(type_zone: str, valeur: str, libelle: str = None, type_etablissement: str = "Collège") -> dict:
    """
    Recherche déterministe par région, département, ou France entière —
    AUCUN appel à l'API de géocodage (S8.26) : contourne la mauvaise
    interprétation d'un nom de région par l'API BAN (ex: "Bretagne" résolu
    à tort vers une rue à Denain, dans le 59), en filtrant directement sur
    les colonnes libelle_region/code_departement déjà présentes dans notre
    propre base (cf. resoudre_zone_administrative dans sql_tool.py pour la
    résolution du nom/type de zone saisi).

    "national" (France entière, DOM-TOM inclus) et "national_metropole"
    (DOM-TOM exclus, cf. DEPARTEMENTS_OUTRE_MER) ne filtrent sur aucune
    valeur précise — valeur/libelle ne servent alors qu'à l'affichage.

    Retourne la même forme que recherche_geo (compatibilité avec le reste
    du pipeline — agrégation, split, classement fonctionnent sans
    modification), sauf latitude/longitude/rayon_km/distance_km qui n'ont
    pas de sens pour une zone administrative entière (mis à None : pas de
    point central ni de rayon, contrairement à une recherche par adresse).
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_PATH
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        colonnes = "uai, nom, commune, secteur, type_etablissement, latitude, longitude"
        if type_zone == "national":
            rows = conn.execute(
                f"SELECT {colonnes} FROM etablissements WHERE type_etablissement = ?",
                (type_etablissement,),
            ).fetchall()
        elif type_zone == "national_metropole":
            placeholders = ", ".join("?" for _ in DEPARTEMENTS_OUTRE_MER)
            rows = conn.execute(
                f"SELECT {colonnes} FROM etablissements "
                f"WHERE type_etablissement = ? AND code_departement NOT IN ({placeholders})",
                (type_etablissement, *DEPARTEMENTS_OUTRE_MER),
            ).fetchall()
        else:
            colonne_zone = "libelle_region" if type_zone == "region" else "code_departement"
            rows = conn.execute(
                f"SELECT {colonnes} FROM etablissements WHERE {colonne_zone} = ? AND type_etablissement = ?",
                (valeur, type_etablissement),
            ).fetchall()
    finally:
        conn.close()
    etablissements = [{**dict(row), "distance_km": None} for row in rows]
    defaut_national = "France métropolitaine" if type_zone == "national_metropole" else "France"
    nom_affiche = libelle or valeur or defaut_national
    if type_zone == "region":
        label = f"{nom_affiche} (région)"
    elif type_zone == "departement":
        label = f"{nom_affiche} ({valeur})"
    else:
        label = nom_affiche
    return {
        "success": True, "adresse_recherchee": nom_affiche, "adresse_normalisee": label,
        "latitude": None, "longitude": None, "rayon_km": None,
        "etablissements": etablissements, "nb_etablissements": len(etablissements), "error": None
    }


if __name__ == "__main__":
    resultat = recherche_geo("Lyon", 10)
    print(f"success={resultat['success']} | {resultat.get('nb_etablissements', 0)} établissements")
