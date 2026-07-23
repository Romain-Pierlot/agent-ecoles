"""
test_route_secteur.py — Test de la route GET /secteur (FastAPI TestClient),
couvrant les 5 états + le respect des constantes de repli (config.py).

Réseau (appelle réellement l'API BAN pour chaque cas) — à lancer à la demande :
    source venv/bin/activate && python3 test_route_secteur.py
"""

from fastapi.testclient import TestClient

from api.main import app
from config import SECTEUR_MAX_COLLEGES_ALENTOURS, SECTEUR_RAYON_REPLI_KM, SECTEUR_NB_SUGGESTIONS_ADRESSE

client = TestClient(app)


def test_etat_trouve():
    # La liste "alentours" est aussi affichée en état "trouve" (repli commun
    # aux 3 états géocodés, cf. maquette : bloc "autres collèges autour de
    # chez vous" présent dès l'état 1) — mais ne doit jamais réafficher le
    # collège de secteur déjà mis en avant.
    r = client.get("/secteur", params={"adresse": "1 Rue Pasteur, 06400 Cannes"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["etat"] == "trouve"
    assert len(corps["colleges_secteur"]) == 1
    assert corps["colleges_secteur"][0]["uai"] == "0061342B"
    assert len(corps["colleges_alentours"]) <= SECTEUR_MAX_COLLEGES_ALENTOURS
    assert all(c["uai"] != "0061342B" for c in corps["colleges_alentours"])


def test_etat_multi_secteur():
    r = client.get("/secteur", params={"adresse": "7 Rue Blaise Pascal, 54320 Maxéville"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["etat"] == "multi_secteur"
    uais = {c["uai"] for c in corps["colleges_secteur"]}
    assert uais == {"0541327Z", "0541469D", "0541568L"}
    assert len(corps["colleges_alentours"]) <= SECTEUR_MAX_COLLEGES_ALENTOURS
    assert all(c["distance_km"] <= SECTEUR_RAYON_REPLI_KM for c in corps["colleges_alentours"])


def test_etat_non_determinable():
    # Ville seule, sans numéro -> BAN ne peut pas résoudre de tronçon précis.
    r = client.get("/secteur", params={"adresse": "Villeurbanne"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["etat"] == "non_determinable"
    assert corps["colleges_secteur"] == []
    assert len(corps["colleges_alentours"]) <= SECTEUR_MAX_COLLEGES_ALENTOURS


def test_etat_adresse_non_reconnue():
    r = client.get("/secteur", params={"adresse": "zzzzxxxxyyyy1234invalide"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["etat"] == "adresse_non_reconnue"
    assert corps["colleges_secteur"] == []
    assert corps["colleges_alentours"] == []


def test_etat_adresse_ambigue():
    # Cas réel qui a motivé cet état (2026-07-23) : une adresse soumise sans
    # passer par le menu d'autocomplétion peut matcher plusieurs communes
    # avec des scores de confiance BAN quasi identiques (le score ne suffit
    # pas à distinguer une adresse précise d'une adresse ambiguë).
    r = client.get("/secteur", params={"adresse": "3 rue jean"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["etat"] == "adresse_ambigue"
    assert corps["colleges_secteur"] == []
    assert corps["colleges_alentours"] == []
    assert 1 < len(corps["suggestions_ambigues"]) <= SECTEUR_NB_SUGGESTIONS_ADRESSE
    villes = {s["label"].split(" ")[-1] for s in corps["suggestions_ambigues"]}
    assert len(villes) > 1


def test_adresse_deja_precise_pas_signalee_ambigue():
    # Non-régression : une adresse déjà complète (avec code postal/ville) ne
    # doit jamais être signalée ambiguë même si BAN retourne plusieurs
    # suggestions (mêmes rues voisines de la même commune).
    r = client.get("/secteur", params={"adresse": "3 Rue Jean 34000 Montpellier"})
    assert r.status_code == 200
    assert r.json()["etat"] != "adresse_ambigue"


if __name__ == "__main__":
    test_etat_trouve()
    print("✓ État trouvé (Cannes)")
    test_etat_multi_secteur()
    print("✓ État multi-secteur (Maxéville) + repli alentours dans les bornes")
    test_etat_non_determinable()
    print("✓ État non déterminable (ville seule) + repli alentours")
    test_etat_adresse_non_reconnue()
    print("✓ État adresse non reconnue (200 OK, pas 500)")
    test_etat_adresse_ambigue()
    print("✓ État adresse ambiguë (plusieurs communes distinctes)")
    test_adresse_deja_precise_pas_signalee_ambigue()
    print("✓ Adresse déjà précise -> jamais signalée ambiguë (non-régression)")
