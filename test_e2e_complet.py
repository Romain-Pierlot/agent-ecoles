"""
test_e2e_complet.py — Cahier de test end-to-end consolidé (session 8, partie C).

Couvre l'ensemble des chemins et variantes construits pendant la session :
classement/split, comparaison de noms (standard/évolution/nuance),
agrégation géo (secteur précisé/indifférent), question méthodologique pure,
agent ReAct (hors-sujet, multi-zones 2/3/5, hors-périmètre, zone introuvable),
et une série de cas limites/questions bancales pour chercher des trous non
encore trouvés.

Coûteux dans son ensemble (beaucoup de cas passent par l'agent ou plusieurs
appels LLM) — lancé volontairement, pas en CI à chaque commit.
"""

import time
from graph_router import construire_graphe

app = construire_graphe()


def etat(question):
    return {
        "question": question, "dc_niveau": "accessible", "categorie": None, "zone_geo": None,
        "resultats_geo": None, "resultats_sql": None, "resultats_rag": None,
        "reponse_finale": None, "tours_agent": 0,
        "noms_etablissements": [], "resolution_noms": None, "uai_resolus": None,
    }


CAS = [
    # --- Chemins déterministes déjà validés isolément : re-confirmation groupée ---
    ("Classement géo, secteur indifférent (split)",
     "Quels sont les meilleurs collèges à Lyon ?"),
    ("Classement géo, secteur précisé",
     "Quels sont les meilleurs collèges publics à Lyon ?"),
    ("Classement géo + nuance méthodologique",
     "Quels collèges à Lyon, et est-ce que leur classement est fiable ?"),
    ("Comparaison de noms standard",
     "Compare le collège Victor Hugo et le collège Jean Moulin à Nantes"),
    ("Comparaison de noms + évolution multi-années",
     "Compare les résultats du collège Chevreul à Lyon sur les trois dernières années"),
    ("Comparaison de noms + nuance méthodologique",
     "Compare le collège Saint-Joseph et Victor Hugo à Nantes, et est-ce que leur VA est fiable ?"),
    ("Agrégation géo, secteur indifférent",
     "Quelle est la moyenne du score des collèges à Lyon ?"),
    ("Agrégation géo, secteur précisé",
     "Quelle est la moyenne du score des collèges publics à Lyon ?"),
    ("Question méthodologique pure",
     "C'est quoi l'IPS ?"),

    # --- Agent : cas déjà validés isolément ---
    ("Agent : hors-sujet",
     "Mon fils a du mal à se concentrer, quel collège lui conviendrait ?"),
    ("Agent : 2 zones",
     "Compare le meilleur collège de Lyon et le meilleur collège de Marseille"),
    ("Agent : 3 zones (limite haute autorisée)",
     "Quelle est la moyenne des scores des collèges à Lyon, Perpignan et Poitiers ?"),
    ("Agent : 5 zones (doit être bloqué)",
     "Compare la moyenne des collèges de Lyon, Marseille, Nantes, Bordeaux et Lille"),
    ("Agent : hors-périmètre géographique",
     "Quel est le meilleur collège du monde ?"),
    ("Agent : zone introuvable",
     "Compare les collèges de Trifouillisville, une ville qui n'existe pas"),

    # --- Nouveaux cas limites / questions bancales ---
    ("Edge : 'pire' doit inverser le tri (jamais vérifié)",
     "Quels sont les pires collèges publics à Lyon ?"),
    ("Edge : géo + évolution SANS nom (combinaison non construite)",
     "Comment ont évolué les résultats des collèges de Lyon sur les 3 dernières années ?"),
    ("Edge : question vague sans zone ni nom ni concept",
     "Un collège c'est bien ou pas ?"),
    ("Edge : ville avec faute de frappe",
     "Quels sont les meilleurs collèges à Lyeon ?"),
    ("Edge : nom + zone contradictoires (2 zones pour 1 nom)",
     "Compare le collège Victor Hugo à Paris et à Lyon"),
    ("Edge : question quasi vide",
     "collège"),
    ("Edge : secteur privé seul + agrégation",
     "Quelle est la moyenne du score des collèges privés à Bordeaux ?"),
]


def tester():
    print("=== CAHIER DE TEST END-TO-END CONSOLIDÉ ===\n")
    resultats = []

    for nom_cas, question in CAS:
        print(f"--- {nom_cas} ---")
        print(f"Question : \"{question}\"")
        debut = time.time()
        try:
            r = app.invoke(etat(question))
            duree = time.time() - debut
            print(f"Catégorie : {r['categorie']} | Tours agent : {r['tours_agent']} | Durée : {duree:.1f}s")
            print(f"\n{r['reponse_finale']}\n")
            resultats.append((nom_cas, True, duree))
        except Exception as e:
            duree = time.time() - debut
            print(f"✗ ERREUR après {duree:.1f}s : {type(e).__name__} : {e}\n")
            resultats.append((nom_cas, False, duree))
        print("=" * 70 + "\n")

    print("=== RÉCAPITULATIF ===")
    for nom_cas, ok, duree in resultats:
        symbole = "✓" if ok else "✗"
        print(f"{symbole} {nom_cas} ({duree:.1f}s)")
    nb_ok = sum(1 for _, ok, _ in resultats if ok)
    print(f"\n{nb_ok}/{len(resultats)} sans exception levée — la qualité des réponses reste à relire ci-dessus.")


if __name__ == "__main__":
    tester()
