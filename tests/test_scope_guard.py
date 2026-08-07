"""
test_scope_guard.py — Vérifie guardrails/scope_guard.py (B2). Fonction pure,
aucun appel LLM/API.
"""

from config import Categorie, OrdreSouhaite
from guardrails.scope_guard import question_hors_sujet

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


def etat(categorie, **kwargs):
    base = {
        "categorie": categorie, "zone_geo": None, "noms_etablissements": [],
        "nuance_methodologique_demandee": False, "ordre_souhaite": OrdreSouhaite.INDIFFERENT,
        "agregation_demandee": False, "evolution_demandee": False,
    }
    base.update(kwargs)
    return base


# --- Catégorie != non_reconnu : jamais hors-sujet, quel que soit le contenu ---
test("recherche_geo_classement -> jamais hors-sujet", not question_hors_sujet(etat(Categorie.RECHERCHE_GEO_CLASSEMENT)))

# --- non_reconnu SANS aucun signal : hors-sujet ---
test("non_reconnu sans signal -> hors-sujet", question_hors_sujet(etat(Categorie.NON_RECONNU)))

# --- non_reconnu AVEC un signal : pas hors-sujet, continue vers l'agent ---
test("non_reconnu + nuance méthodologique -> pas hors-sujet", not question_hors_sujet(
    etat(Categorie.NON_RECONNU, nuance_methodologique_demandee=True)))
test("non_reconnu + zone -> pas hors-sujet", not question_hors_sujet(
    etat(Categorie.NON_RECONNU, zone_geo="Lyon")))
test("non_reconnu + noms -> pas hors-sujet", not question_hors_sujet(
    etat(Categorie.NON_RECONNU, noms_etablissements=["Victor Hugo"])))
test("non_reconnu + ordre_souhaite -> pas hors-sujet", not question_hors_sujet(
    etat(Categorie.NON_RECONNU, ordre_souhaite=OrdreSouhaite.MEILLEUR)))
test("non_reconnu + agregation -> pas hors-sujet", not question_hors_sujet(
    etat(Categorie.NON_RECONNU, agregation_demandee=True)))
test("non_reconnu + evolution -> pas hors-sujet", not question_hors_sujet(
    etat(Categorie.NON_RECONNU, evolution_demandee=True)))


def tester():
    print("=== TEST SCOPE GUARD (B2) ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
