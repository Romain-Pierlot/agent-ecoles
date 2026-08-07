"""
test_suggestions_adresse.py — Test de la route GET /secteur/adresses
(autocomplétion adresse), qui corrige le fait que geocoder() (limit=1)
résolvait silencieusement une adresse incomplète sur un seul résultat
arbitraire (ex: "30 rue jean" -> Marseille, alors que 5 villes différentes
matchent). Réseau (appelle réellement l'API BAN) — à lancer à la demande.
"""

from fastapi.testclient import TestClient

from api.main import app
from config import SECTEUR_NB_SUGGESTIONS_ADRESSE

client = TestClient(app)


def test_adresse_ambigue_plusieurs_suggestions():
    # Cas réel qui a motivé cette fonctionnalité : une seule ville ne
    # suffirait pas à représenter "30 rue jean" (plusieurs villes/rues).
    r = client.get("/secteur/adresses", params={"q": "30 rue jean"})
    assert r.status_code == 200
    suggestions = r.json()["suggestions"]
    assert len(suggestions) > 1
    assert len(suggestions) <= SECTEUR_NB_SUGGESTIONS_ADRESSE
    villes = {s["label"].split(" ")[-1] for s in suggestions}
    assert len(villes) > 1, "les suggestions doivent couvrir plusieurs villes distinctes sur ce cas réel"


def test_adresse_precise_une_suggestion_pertinente():
    r = client.get("/secteur/adresses", params={"q": "1 Rue Pasteur, 06400 Cannes"})
    assert r.status_code == 200
    suggestions = r.json()["suggestions"]
    assert len(suggestions) >= 1
    assert "Cannes" in suggestions[0]["label"]


def test_requete_vide():
    r = client.get("/secteur/adresses", params={"q": ""})
    assert r.status_code == 200
    assert r.json()["suggestions"] == []


if __name__ == "__main__":
    test_adresse_ambigue_plusieurs_suggestions()
    print("✓ Adresse ambiguë -> plusieurs suggestions distinctes")
    test_adresse_precise_une_suggestion_pertinente()
    print("✓ Adresse précise -> suggestion pertinente en tête")
    test_requete_vide()
    print("✓ Requête vide -> liste vide, pas d'appel BAN inutile")
