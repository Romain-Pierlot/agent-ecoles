"""
test_router_classification.py — Vérifie que le nœud router classe correctement
un jeu de questions représentatif des 6 catégories définies.

N'appelle QUE le nœud router (pas geo/sql/rag) — test rapide et peu coûteux.
"""

from graph_router import noeud_router

CAS_DE_TEST = [
    ("Quels sont les meilleurs collèges à Lyon ?", "recherche_geo_classement"),
    ("Compare le collège Victor Hugo et le collège Jean Moulin", "comparaison_etablissements_nommes"),
    ("Compare les collèges publics et privés autour de Bordeaux", "recherche_geo_comparaison"),
    ("C'est quoi l'IPS ?", "question_methodologique"),
    ("Quels collèges à Lyon, et est-ce que leur classement est fiable ?", "recherche_geo_methodologique"),
    ("Mon fils a du mal à se concentrer, quel collège lui conviendrait ?", "non_reconnu"),
]

def tester():
    print("=== TEST DE CLASSIFICATION DU ROUTER ===\n")
    resultats = []

    for question, categorie_attendue in CAS_DE_TEST:
        state = {
            "question": question,
            "dc_niveau": "accessible",
            "categorie": None,
            "resultats_geo": None,
            "resultats_sql": None,
            "resultats_rag": None,
            "reponse_finale": None,
            "tours_agent": 0,
        }
        state = noeud_router(state)
        categorie_obtenue = state["categorie"]
        ok = categorie_obtenue == categorie_attendue
        resultats.append(ok)

        symbole = "✓" if ok else "✗"
        print(f"{symbole} \"{question[:60]}\"")
        print(f"   attendu : {categorie_attendue}")
        print(f"   obtenu  : {categorie_obtenue}\n")

    nb_ok = sum(resultats)
    print(f"=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")

if __name__ == "__main__":
    tester()
