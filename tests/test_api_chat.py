"""
tests/test_api_chat.py — Teste la vraie route HTTP POST /chat (FastAPI
TestClient) : c'est le seul chemin qui exerce ensemble la sérialisation
Pydantic (ChatRequest/ChatResponse), le rangement par session_id
(api/sessions.py) et l'appel à la journalisation. Les tests réseau/LLM
existants appellent le graphe LangGraph directement (graph_router.py),
en court-circuitant toute cette couche API.

poser_question/poser_resolution_choix sont mockés au point où api/main.py
les importe (monkeypatch.setattr(main_module, ...)) — aucun appel LLM réel.
Invoqué via pytest (monkeypatch est une fixture pytest, pas d'exécution en
script direct comme les autres fichiers de tests/).
"""
from fastapi.testclient import TestClient

import api.main as main_module
from api.main import app

client = TestClient(app)


def _etat_factice(reponse="Réponse de test.", **overrides):
    etat = {
        "reponse_finale": reponse,
        "categorie": "recherche_sql",
        "resultats_geo": None,
        "resultats_sql": None,
        "resultats_rag": None,
        "candidats_zone_geo": None,
        "resolution_noms": None,
        "tours_agent": 1,
    }
    etat.update(overrides)
    return etat


def test_chat_question_libre_retourne_200_et_le_bon_schema(monkeypatch):
    monkeypatch.setattr(
        main_module, "poser_question",
        lambda graphe, etat, question: _etat_factice("Voici la réponse."),
    )
    r = client.post("/chat", json={"session_id": "test-1", "question": "Quel est le meilleur collège à Lyon ?"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["reponse"] == "Voici la réponse."
    assert corps["choix"] is None


def test_chat_resolution_appelle_poser_resolution_choix_pas_poser_question(monkeypatch):
    appels = {"poser_question": 0, "poser_resolution_choix": 0}

    def fausse_poser_question(graphe, etat, question):
        appels["poser_question"] += 1
        return _etat_factice()

    def fausse_poser_resolution_choix(etat, resolution):
        appels["poser_resolution_choix"] += 1
        return _etat_factice("Réponse suite au choix cliqué.")

    monkeypatch.setattr(main_module, "poser_question", fausse_poser_question)
    monkeypatch.setattr(main_module, "poser_resolution_choix", fausse_poser_resolution_choix)

    r = client.post(
        "/chat",
        json={"session_id": "test-2", "resolution": {"commune": "Nantes", "code_departement": "44"}},
    )
    assert r.status_code == 200
    assert r.json()["reponse"] == "Réponse suite au choix cliqué."
    assert appels["poser_resolution_choix"] == 1
    assert appels["poser_question"] == 0


def test_chat_session_reutilisee_entre_deux_appels(monkeypatch):
    etats_recus = []
    etats_retournes = []

    def fausse_poser_question(graphe, etat, question):
        etats_recus.append(etat)
        nouvel_etat = _etat_factice(f"Réponse à : {question}")
        etats_retournes.append(nouvel_etat)
        return nouvel_etat

    monkeypatch.setattr(main_module, "poser_question", fausse_poser_question)

    session_id = "test-session-continue"
    client.post("/chat", json={"session_id": session_id, "question": "Première question"})
    client.post("/chat", json={"session_id": session_id, "question": "Deuxième question"})

    # L'état REÇU par le 2e appel doit être exactement l'objet RETOURNÉ par
    # le 1er (enregistrer_session l'a bien stocké, obtenir_ou_creer_session
    # l'a bien retrouvé) — pas une nouvelle session recréée à chaque appel.
    assert len(etats_recus) == 2
    assert etats_recus[1] is etats_retournes[0]


def test_chat_requete_malformee_retourne_422():
    r = client.post("/chat", json={"question": "Sans session_id"})
    assert r.status_code == 422


def test_chat_construit_choix_zone_quand_candidats_zone_geo_present(monkeypatch):
    etat = _etat_factice(
        candidats_zone_geo=[
            {"commune": "Nantes", "code_departement": "44"},
            {"commune": "Rennes", "code_departement": "35"},
        ],
        zone_geo="Pays de la Loire",
    )
    monkeypatch.setattr(main_module, "poser_question", lambda graphe, e, q: etat)
    r = client.post("/chat", json={"session_id": "test-3", "question": "Collèges dans la région ?"})
    assert r.status_code == 200
    choix = r.json()["choix"]
    assert choix is not None
    assert choix["type"] == "zone"
    assert len(choix["groupes"][0]["options"]) == 2
