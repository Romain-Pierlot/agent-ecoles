"""
test_agent_react.py — Batterie de tests du chemin agent ReAct (catégorie non_reconnu).

Contrairement aux autres chemins (déterministes, séquence d'outils fixe),
l'agent décide dynamiquement quels outils appeler — moins de contrôle,
donc besoin d'une couverture de cas plus large : hors-sujet, multi-zones,
hors-périmètre géographique, échec d'outil, combinaison de dimensions.

Coûteux (plusieurs appels LLM par cas, jusqu'à 30-45s) — à lancer
volontairement, pas dans une CI à chaque commit.

Vérifications automatiques limitées (catégorie, présence de mots-clés
attendus) — la qualité de la réponse elle-même reste à relire manuellement,
affichée en clair pour chaque cas.
"""

import time
from graph_router import construire_graphe

app = construire_graphe()


def etat_initial(question):
    return {
        "question": question, "dc_niveau": "accessible", "categorie": None, "zone_geo": None,
        "resultats_geo": None, "resultats_sql": None, "resultats_rag": None,
        "reponse_finale": None, "tours_agent": 0,
        "noms_etablissements": [], "resolution_noms": None, "uai_resolus": None,
    }


CAS_DE_TEST = [
    {
        "nom": "Hors-sujet (conseil personnalisé)",
        "question": "Mon fils a du mal à se concentrer, quel collège lui conviendrait ?",
        "verifie": lambda r: r["categorie"] == "non_reconnu" and r["tours_agent"] <= 1,
        "attendu": "Refus honnête, sans appel d'outil inutile (0 ou 1 tour max).",
    },
    {
        "nom": "Comparaison multi-zones",
        "question": "Compare le meilleur collège de Lyon et le meilleur collège de Marseille, en tenant compte de la valeur ajoutée",
        "verifie": lambda r: r["categorie"] == "non_reconnu" and "Neutre" in r["reponse_finale"] or "positif" in r["reponse_finale"] or "negatif" in r["reponse_finale"],
        "attendu": "Badge VA en clair (pas de chiffre brut type 1.0/0.7), tableau des deux collèges.",
    },
    {
        "nom": "Hors-périmètre géographique (monde)",
        "question": "Quel est le meilleur collège du monde ?",
        "verifie": lambda r: r["categorie"] == "non_reconnu",
        "attendu": "Doit clarifier que le périmètre est la France, pas halluciner un collège étranger.",
    },
    {
        "nom": "Zone introuvable",
        "question": "Compare les collèges de Trifouillisville, une ville qui n'existe pas",
        "verifie": lambda r: r["categorie"] == "non_reconnu",
        "attendu": "Doit gérer l'échec de recherche_geo proprement (le dire), pas planter ni inventer un résultat.",
    },
    {
        "nom": "Combiné 3 dimensions (multi-zones + méthodologie)",
        "question": "Compare 3 collèges dans des villes différentes et explique-moi comment leur VA est calculée",
        "verifie": lambda r: r["categorie"] == "non_reconnu" and r["tours_agent"] <= 5,
        "attendu": "Doit enchaîner geo/sql plusieurs fois ET rag, sans dépasser le plafond de 5 tours.",
    },
]


def tester():
    print("=== BATTERIE DE TESTS : AGENT REACT (non_reconnu) ===\n")
    resultats = []

    for cas in CAS_DE_TEST:
        print(f"--- {cas['nom']} ---")
        print(f"Question : \"{cas['question']}\"")
        print(f"Attendu  : {cas['attendu']}\n")

        debut = time.time()
        resultat = app.invoke(etat_initial(cas["question"]))
        duree = time.time() - debut

        try:
            ok = cas["verifie"](resultat)
        except Exception as e:
            ok = False
            print(f"  (vérification automatique en échec : {e})")
        resultats.append(ok)

        symbole = "✓" if ok else "✗"
        print(f"{symbole} Catégorie : {resultat['categorie']} | Tours : {resultat['tours_agent']} | Durée : {duree:.1f}s")
        print(f"\nRéponse :\n{resultat['reponse_finale']}\n")
        print("=" * 70 + "\n")

    nb_ok = sum(resultats)
    print(f"=== RÉSULTAT AUTOMATIQUE : {nb_ok}/{len(CAS_DE_TEST)} — relire les réponses ci-dessus pour la qualité ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
