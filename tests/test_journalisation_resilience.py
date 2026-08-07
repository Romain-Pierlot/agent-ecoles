"""
tests/test_journalisation_resilience.py — Vérifie la garantie documentée dans
api/journalisation.py : une panne d'écriture (base injoignable) ne doit
jamais faire échouer ni ralentir la réponse à l'utilisateur (décision
S19.1 du decision_log).

Point important : api.journalisation lit _DB_URL une seule fois au niveau
module, à l'import (`_DB_URL = os.environ.get("SUPABASE_DB_URL")`). Comme
tests/test_route_secteur.py et tests/test_suggestions_adresse.py importent
déjà api.main (qui importe api.journalisation), ce module est déjà chargé
dans le process pytest avant que ce fichier ne s'exécute — positionner la
variable d'environnement SUPABASE_DB_URL ici n'aurait donc aucun effet.
Il faut monkeypatcher l'attribut _DB_URL du module directement.
"""
import api.journalisation as journalisation_module

_URL_INJOIGNABLE = "postgresql://x:x@127.0.0.1:1/inexistant"


def test_journaliser_echange_ne_leve_pas_si_base_injoignable(monkeypatch):
    monkeypatch.setattr(journalisation_module, "_DB_URL", _URL_INJOIGNABLE)
    journalisation_module.journaliser_echange(
        session_id="test",
        question="Une question",
        reponse="Une réponse",
        categorie="recherche_sql",
        outils_appeles=["sql_tool"],
        latence_ms=42,
    )  # ne doit lever aucune exception


def test_journaliser_recherche_ne_leve_pas_si_base_injoignable(monkeypatch):
    monkeypatch.setattr(journalisation_module, "_DB_URL", _URL_INJOIGNABLE)
    journalisation_module.journaliser_recherche(
        page_origine="recherche",
        terme="college lyon",
        nb_etablissements=3,
        nb_communes=1,
    )  # ne doit lever aucune exception


def test_journaliser_echange_ne_leve_pas_si_url_absente(monkeypatch):
    monkeypatch.setattr(journalisation_module, "_DB_URL", None)
    journalisation_module.journaliser_echange(
        session_id="test", question="Q", reponse="R",
    )  # chemin de repli (aucune tentative de connexion) : doit rester sûr aussi
