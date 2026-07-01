"""geo_tool.py — Outil de géolocalisation pour EduScope (V2 — clés harmonisées)"""

import sqlite3
import requests
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH, BAN_API_TIMEOUT_SECONDS, GEO_RAYON_DEFAUT_KM

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
                    "label": None, "type": None, "error": f"Adresse non trouvée : {adresse_ou_ville}"}
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]
        return {
            "success": True, "latitude": coords[1], "longitude": coords[0],
            "label": feature["properties"].get("label", adresse_ou_ville),
            "type": feature["properties"].get("type", "inconnu"), "error": None
        }
    except requests.Timeout:
        return {"success": False, "latitude": None, "longitude": None,
                "label": None, "type": None, "error": f"Timeout API BAN après {BAN_API_TIMEOUT_SECONDS}s"}
    except Exception as e:
        return {"success": False, "latitude": None, "longitude": None,
                "label": None, "type": None, "error": str(e)}


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


def recherche_geo(adresse_ou_ville: str, rayon_km: float = None, type_etablissement: str = "Collège") -> dict:
    """Retourne : {success, adresse_recherchee, adresse_normalisee, latitude, longitude,
    rayon_km, etablissements, nb_etablissements, error}"""
    if rayon_km is None:
        rayon_km = GEO_RAYON_DEFAUT_KM
    geo = geocoder(adresse_ou_ville)
    if not geo["success"]:
        return {
            "success": False, "adresse_recherchee": adresse_ou_ville, "adresse_normalisee": None,
            "latitude": None, "longitude": None, "rayon_km": rayon_km,
            "etablissements": [], "nb_etablissements": 0, "error": geo["error"]
        }
    etablissements = trouver_etablissements_dans_rayon(geo["latitude"], geo["longitude"], rayon_km, type_etablissement)
    return {
        "success": True, "adresse_recherchee": adresse_ou_ville,
        "adresse_normalisee": geo["label"], "latitude": geo["latitude"], "longitude": geo["longitude"],
        "rayon_km": rayon_km, "etablissements": etablissements,
        "nb_etablissements": len(etablissements), "error": None
    }


if __name__ == "__main__":
    resultat = recherche_geo("Lyon", 10)
    print(f"success={resultat['success']} | {resultat.get('nb_etablissements', 0)} établissements")
