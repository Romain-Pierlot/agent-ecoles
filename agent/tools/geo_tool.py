"""
geo_tool.py — Outil de géolocalisation pour EduScope
Convertit une adresse ou ville en coordonnées GPS via l'API BAN,
puis trouve les établissements dans un rayon donné via formule haversine.

Flux :
1. Appel API BAN → coordonnées GPS du point de référence
2. Calcul distance haversine sur SQLite via fonction Python custom
3. Retour des UAI dans le rayon avec leur distance

Limites :
- 1 appel API BAN par question (guardrail anti-abus)
- Rayon par défaut : GEO_RAYON_DEFAUT_KM (config.py)
- Timeout API BAN : BAN_API_TIMEOUT_SECONDS (config.py)
"""

import sqlite3
import requests
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import DB_PATH, BAN_API_TIMEOUT_SECONDS, GEO_RAYON_DEFAUT_KM

# URL de l'API BAN (Base Adresse Nationale) — gratuite, sans clé
BAN_API_URL = "https://api-adresse.data.gouv.fr/search/"


# ================================================================
# FORMULE HAVERSINE
# Calcule la distance en km entre deux points GPS
# ================================================================

def haversine(lat1, lon1, lat2, lon2):
    """Distance en km entre deux points GPS (formule haversine)."""
    R = 6371  # Rayon de la Terre en km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# ================================================================
# GÉOCODAGE — Adresse/ville → GPS
# ================================================================

def geocoder(adresse_ou_ville: str) -> dict:
    """
    Appelle l'API BAN pour convertir une adresse ou ville en GPS.
    
    Retourne :
    {
        "succes": bool,
        "latitude": float,
        "longitude": float,
        "label": str,       # adresse normalisée retournée par BAN
        "type": str,        # "housenumber", "street", "municipality"...
        "erreur": str | None
    }
    """
    try:
        response = requests.get(
            BAN_API_URL,
            params={"q": adresse_ou_ville, "limit": 1},
            timeout=BAN_API_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("features"):
            return {
                "succes": False,
                "latitude": None,
                "longitude": None,
                "label": None,
                "type": None,
                "erreur": f"Adresse non trouvée : {adresse_ou_ville}"
            }
        
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]  # [longitude, latitude]
        
        return {
            "succes": True,
            "latitude": coords[1],
            "longitude": coords[0],
            "label": feature["properties"].get("label", adresse_ou_ville),
            "type": feature["properties"].get("type", "inconnu"),
            "erreur": None
        }
        
    except requests.Timeout:
        return {
            "succes": False,
            "latitude": None,
            "longitude": None,
            "label": None,
            "type": None,
            "erreur": f"Timeout API BAN après {BAN_API_TIMEOUT_SECONDS}s"
        }
    except Exception as e:
        return {
            "succes": False,
            "latitude": None,
            "longitude": None,
            "label": None,
            "type": None,
            "erreur": str(e)
        }


# ================================================================
# RECHERCHE DANS LE RAYON
# ================================================================

def trouver_etablissements_dans_rayon(
    latitude: float,
    longitude: float,
    rayon_km: float = None,
    type_etablissement: str = "Collège"
) -> list[dict]:
    """
    Trouve les établissements dans un rayon autour d'un point GPS.
    Utilise la formule haversine injectée comme fonction SQLite.
    
    Retourne une liste de dicts avec uai, nom, commune, distance_km.
    """
    if rayon_km is None:
        rayon_km = GEO_RAYON_DEFAUT_KM
    
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        DB_PATH
    )
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Injection de la fonction haversine dans SQLite
    conn.create_function("haversine", 4, haversine)
    
    try:
        rows = conn.execute("""
            SELECT 
                e.uai,
                e.nom,
                e.commune,
                e.secteur,
                e.type_etablissement,
                e.latitude,
                e.longitude,
                ROUND(haversine(?, ?, e.latitude, e.longitude), 2) as distance_km
            FROM etablissements e
            WHERE e.latitude IS NOT NULL
              AND e.longitude IS NOT NULL
              AND e.type_etablissement = ?
              AND haversine(?, ?, e.latitude, e.longitude) <= ?
            ORDER BY distance_km ASC
        """, (
            latitude, longitude,
            type_etablissement,
            latitude, longitude, rayon_km
        )).fetchall()
        
        return [dict(row) for row in rows]
    
    finally:
        conn.close()


# ================================================================
# FONCTION PRINCIPALE
# ================================================================

def recherche_geo(
    adresse_ou_ville: str,
    rayon_km: float = None,
    type_etablissement: str = "Collège"
) -> dict:
    """
    Fonction principale — géolocalise une adresse et trouve
    les établissements dans le rayon.
    
    Retourne :
    {
        "succes": bool,
        "adresse_recherchee": str,
        "adresse_normalisee": str,
        "latitude": float,
        "longitude": float,
        "rayon_km": float,
        "etablissements": list[dict],
        "nb_etablissements": int,
        "erreur": str | None
    }
    """
    if rayon_km is None:
        rayon_km = GEO_RAYON_DEFAUT_KM
    
    # Étape 1 — Géocodage
    geo = geocoder(adresse_ou_ville)
    
    if not geo["succes"]:
        return {
            "succes": False,
            "adresse_recherchee": adresse_ou_ville,
            "adresse_normalisee": None,
            "latitude": None,
            "longitude": None,
            "rayon_km": rayon_km,
            "etablissements": [],
            "nb_etablissements": 0,
            "erreur": geo["erreur"]
        }
    
    # Étape 2 — Recherche dans le rayon
    etablissements = trouver_etablissements_dans_rayon(
        geo["latitude"],
        geo["longitude"],
        rayon_km,
        type_etablissement
    )
    
    return {
        "succes": True,
        "adresse_recherchee": adresse_ou_ville,
        "adresse_normalisee": geo["label"],
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "rayon_km": rayon_km,
        "etablissements": etablissements,
        "nb_etablissements": len(etablissements),
        "erreur": None
    }


# ================================================================
# TEST RAPIDE EN LIGNE DE COMMANDE
# ================================================================

if __name__ == "__main__":
    tests = [
        ("12 rue de Rivoli Paris", 5),
        ("Lyon", 10),
        ("Bordeaux", 10),
        ("adresse qui nexiste vraiment pas du tout", 10),
    ]
    
    print("=== TEST GEO TOOL ===\n")
    
    for adresse, rayon in tests:
        print(f"Adresse : {adresse} | Rayon : {rayon}km")
        resultat = recherche_geo(adresse, rayon)
        
        if resultat["succes"]:
            print(f"✓ Normalisée : {resultat['adresse_normalisee']}")
            print(f"  GPS : {resultat['latitude']:.4f}, {resultat['longitude']:.4f}")
            print(f"  Établissements trouvés : {resultat['nb_etablissements']}")
            if resultat["etablissements"]:
                for e in resultat["etablissements"][:3]:
                    print(f"    {e['nom'][:40]:<40} {e['commune']:<20} {e['distance_km']}km")
                if resultat["nb_etablissements"] > 3:
                    print(f"    ... et {resultat['nb_etablissements'] - 3} autres")
        else:
            print(f"✗ Erreur : {resultat['erreur']}")
        print()
