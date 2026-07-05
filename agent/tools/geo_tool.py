"""geo_tool.py — Outil de géolocalisation pour agent-ecoles (V2 — clés harmonisées)"""

import sqlite3
import requests
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH, BAN_API_TIMEOUT_SECONDS, GEO_RAYON_DEFAUT_KM, GEO_RAYON_ENVIRONS_KM, DEPARTEMENTS_OUTRE_MER

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def geocoder(adresse_ou_ville: str) -> dict:
    try:
        response = requests.get(
            BAN_API_URL, params={"q": adresse_ou_ville, "limit": 1},
            timeout=BAN_API_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("features"):
            return {"success": False, "latitude": None, "longitude": None,
                    "label": None, "type": None, "city": None, "depcode": None,
                    "error": f"Adresse non trouvée : {adresse_ou_ville}"}
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]
        proprietes = feature["properties"]
        return {
            "success": True, "latitude": coords[1], "longitude": coords[0],
            "label": proprietes.get("label", adresse_ou_ville),
            "type": proprietes.get("type", "inconnu"),
            "city": proprietes.get("city"), "depcode": proprietes.get("depcode"),
            "error": None
        }
    except requests.Timeout:
        return {"success": False, "latitude": None, "longitude": None,
                "label": None, "type": None, "city": None, "depcode": None,
                "error": f"Timeout API BAN après {BAN_API_TIMEOUT_SECONDS}s"}
    except Exception as e:
        return {"success": False, "latitude": None, "longitude": None,
                "label": None, "type": None, "city": None, "depcode": None, "error": str(e)}


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
        rows = conn.execute("""
            SELECT e.uai, e.nom, e.commune, e.secteur, e.type_etablissement,
                   e.latitude, e.longitude,
                   ROUND(haversine(?, ?, e.latitude, e.longitude), 2) as distance_km
            FROM etablissements e
            WHERE e.latitude IS NOT NULL AND e.longitude IS NOT NULL
              AND e.type_etablissement = ?
              AND haversine(?, ?, e.latitude, e.longitude) <= ?
            ORDER BY distance_km ASC
        """, (latitude, longitude, type_etablissement, latitude, longitude, rayon_km)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


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
