"""
test_e2e_complet.py — Cahier de test end-to-end consolidé (session 8, partie C).

Couvre l'ensemble des chemins et variantes construits pendant la session :
classement/split, comparaison de noms (standard/évolution/nuance),
agrégation géo (secteur précisé/indifférent), question méthodologique pure,
agent ReAct (hors-sujet, multi-zones 2/3/5, hors-périmètre, zone introuvable),
une série de cas limites/questions bancales, l'affichage conditionnel des
mentions TB/B (session 2026-07-06, sur les deux chemins qui y sont sensibles :
déterministe et agent ReAct) et le bouton "voir plus" (cache + pagination).

Chaque cas de CAS peut porter une fonction de vérification optionnelle
(3e élément du tuple) qui contrôle le contenu réel de la réponse, pas
seulement l'absence d'exception — sans ça, une régression d'affichage
(colonne en trop ou manquante) passerait inaperçue.

Coûteux dans son ensemble (beaucoup de cas passent par l'agent ou plusieurs
appels LLM) — lancé volontairement, pas en CI à chaque commit.
"""

import time
from graph_router import construire_graphe, nouvelle_session, poser_question, poser_resolution_choix

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

    # --- Mentions TB/B : affichage conditionnel (session 2026-07-06) ---
    # 3e élément optionnel : fonction de vérification du contenu de la
    # réponse (au-delà du simple "pas d'exception") — sinon les régressions
    # d'affichage (colonnes en trop ou manquantes) passeraient inaperçues.
    ("Classement géo, mentions demandées explicitement",
     "Quels sont les collèges à Toulouse avec leurs mentions TB et B ?",
     lambda r: "Mentions B" in r["reponse_finale"] and "Mentions TB" in r["reponse_finale"]),
    ("Classement géo, sans mention (non-régression affichage par défaut)",
     "Quels sont les meilleurs collèges à Toulouse ?",
     lambda r: "Mentions B" not in r["reponse_finale"] and "Mentions TB" not in r["reponse_finale"]),
    ("Agent ReAct, taux de mention TB demandé (chemin non_reconnu, bug régression S12)",
     "Quel est le taux de mention TB moyen des collèges publics à Levallois-Perret ?",
     lambda r: "mention" in r["reponse_finale"].lower()),
    ("Agent ReAct, moyenne sans mention (non-régression, même chemin non_reconnu)",
     "Quelle est la moyenne des collèges publics à Levallois-Perret ?",
     lambda r: "mention" not in r["reponse_finale"].lower()),
]


def tester_bouton_voir_plus(resultats):
    """
    Cas multi-tours (bouton "voir plus", session 2026-07-06) : nécessite un
    état de session persistant (poser_question/poser_resolution_choix),
    incompatible avec le format à une question de CAS (un simple app.invoke
    isolé). Vérifie : le cache est bien rempli au-delà de ce qui est
    affiché, le clic augmente n_affiches sans dépasser le cache, et un
    second clic jusqu'à épuisement du cache ne plante pas (plafonne).
    """
    nom_cas = "Bouton 'voir plus' : incrémente depuis le cache, sans nouvel appel SQL/LLM"
    print(f"--- {nom_cas} ---")
    debut = time.time()
    try:
        etat_session = nouvelle_session()
        etat_session = poser_question(app, etat_session, "Quels sont les collèges à Toulouse ?")
        cache_public = etat_session["cache_secteur_public"]
        n_avant = etat_session["n_affiches_public"]

        etat_session = poser_resolution_choix(etat_session, {"type": "voir_plus", "secteur": "public"})
        n_apres_1_clic = etat_session["n_affiches_public"]

        # Clics répétés jusqu'à dépasser la taille du cache — doit plafonner,
        # jamais planter ni dépasser len(cache_public).
        for _ in range(5):
            etat_session = poser_resolution_choix(etat_session, {"type": "voir_plus", "secteur": "public"})
        n_final = etat_session["n_affiches_public"]

        ok = (
            len(cache_public) > n_avant
            and n_apres_1_clic > n_avant
            and n_apres_1_clic <= len(cache_public)
            and n_final == len(cache_public)
            and len(etat_session["resultats_sql"]["public"]) == n_final
        )
        duree = time.time() - debut
        print(
            f"cache={len(cache_public)} | n_affiches avant={n_avant}, après 1 clic={n_apres_1_clic}, "
            f"après 6 clics={n_final} -> {'✓' if ok else '✗'}"
        )
        resultats.append((nom_cas, ok, duree))
    except Exception as e:
        duree = time.time() - debut
        print(f"✗ ERREUR après {duree:.1f}s : {type(e).__name__} : {e}")
        resultats.append((nom_cas, False, duree))
    print("=" * 70 + "\n")


def tester():
    print("=== CAHIER DE TEST END-TO-END CONSOLIDÉ ===\n")
    resultats = []

    for cas in CAS:
        nom_cas, question = cas[0], cas[1]
        verification = cas[2] if len(cas) > 2 else None
        print(f"--- {nom_cas} ---")
        print(f"Question : \"{question}\"")
        debut = time.time()
        try:
            r = app.invoke(etat(question))
            duree = time.time() - debut
            print(f"Catégorie : {r['categorie']} | Tours agent : {r['tours_agent']} | Durée : {duree:.1f}s")
            print(f"\n{r['reponse_finale']}\n")
            if verification is not None:
                ok = bool(verification(r))
                if not ok:
                    print(f"✗ VÉRIFICATION DE CONTENU ÉCHOUÉE pour : {nom_cas}\n")
                resultats.append((nom_cas, ok, duree))
            else:
                resultats.append((nom_cas, True, duree))
        except Exception as e:
            duree = time.time() - debut
            print(f"✗ ERREUR après {duree:.1f}s : {type(e).__name__} : {e}\n")
            resultats.append((nom_cas, False, duree))
        print("=" * 70 + "\n")

    tester_bouton_voir_plus(resultats)

    print("=== RÉCAPITULATIF ===")
    for nom_cas, ok, duree in resultats:
        symbole = "✓" if ok else "✗"
        print(f"{symbole} {nom_cas} ({duree:.1f}s)")
    nb_ok = sum(1 for _, ok, _ in resultats if ok)
    print(f"\n{nb_ok}/{len(resultats)} corrects (pas d'exception + vérification de contenu quand présente).")
    return nb_ok == len(resultats)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)


if __name__ == "__main__":
    tester()
