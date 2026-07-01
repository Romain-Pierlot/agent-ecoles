"""
test_e2e_geo_classement.py — Test bout en bout du chemin recherche_geo_classement.
Passe par le graphe complet : router -> geo_tool -> sql_tool -> synthese.
"""

import time
from graph_router import construire_graphe

def tester():
    print("=== TEST BOUT EN BOUT : recherche_geo_classement ===\n")

    app = construire_graphe()

    question = "Quels sont les meilleurs collèges à Lyon ?"
    print(f"Question : \"{question}\"\n")

    debut = time.time()
    resultat = app.invoke({
        "question": question,
        "dc_niveau": "accessible",
        "categorie": None,
        "zone_geo": None,
        "resultats_geo": None,
        "resultats_sql": None,
        "resultats_rag": None,
        "reponse_finale": None,
        "tours_agent": 0,
    })

    categorie_attendue = "recherche_geo_classement"
    categorie_obtenue = resultat["categorie"]
    print(f"Catégorie attendue : {categorie_attendue}")
    print(f"Catégorie obtenue  : {categorie_obtenue}")
    print("✓ Classification correcte" if categorie_obtenue == categorie_attendue else "✗ MAUVAISE CLASSIFICATION\n")

    geo = resultat.get("resultats_geo") or {}
    sql = resultat.get("resultats_sql") or {}
    print(f"\ngeo_tool  : success={geo.get('success')} | {geo.get('nb_etablissements', 0)} établissements trouvés")
    print(f"sql_tool  : success={sql.get('success')} | {sql.get('nb_resultats', 0)} résultats")

    duree = time.time() - debut
    print(f"\n--- Réponse finale ---\n{resultat['reponse_finale']}")
    print(f"\n⏱ Durée totale : {duree:.1f}s")

if __name__ == "__main__":
    tester()
