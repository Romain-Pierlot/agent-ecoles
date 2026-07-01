"""
test_comparaison_noms.py — Test interactif du chemin comparaison_etablissements_nommes

Entonnoir de désambiguïsation, avec prise en compte d'une zone déjà donnée
dans la question elle-même (ex: "Saint-Joseph dans le 44" ou "Victor Hugo à
Nantes") — cette zone est pré-filtrée en amont par noeud_resolution_noms
(zone_geo). Le niveau de départ de l'entonnoir tient compte de ce qui a déjà
été consommé :
  - zone_geo de type département déjà appliquée -> l'entonnoir démarre
    directement au niveau "ville" (pas la peine de redemander le département)
  - zone_geo de type ville déjà appliquée -> pas de niveau de précision
    supplémentaire disponible dans cette V0 ; si (cas rare, jamais rencontré
    à plus de 2 dans les données réelles) il reste encore >5 candidats après
    filtrage ville, on affiche la liste complète malgré le seuil
  - aucune zone_geo -> l'entonnoir démarre normalement au niveau "département"

3 tentatives max de saisie non reconnue avant d'abandonner le sous-parcours.

Limitation V0 assumée : gère un seul nom ambigu à la fois.

Dette technique connue (pas corrigée ici) : la recherche par nom (LIKE) est
trop permissive sur les noms composés (ex: "Saint-Joseph" remonte aussi
"Saint-Joseph de Cluny", "Saint-Joseph La Salle", etc.) — à traiter séparément.
"""

from graph_router import construire_graphe, noeud_sql, noeud_synthese, AgentState
from agent.tools.sql_tool import filtrer_candidats_par_precision, interpreter_precision

app = construire_graphe()

SEUIL_CANDIDATS_AVANT_PRECISION = 5
MAX_TENTATIVES = 3


def afficher_candidats(candidats):
    for i, c in enumerate(candidats):
        print(f"  {i + 1}. {c['nom']} — {c['commune']} ({c['secteur']})")


def resoudre_ambiguite(nom, candidats, niveau_initial="departement"):
    """
    Fait tourner l'entonnoir de clarification pour un seul nom ambigu.

    niveau_initial : "departement" (défaut, rien n'a encore été précisé),
    "ville" (le département a déjà été consommé via zone_geo, on saute
    directement à la ville), ou "epuise" (la ville a déjà été consommée via
    zone_geo, plus aucun niveau de précision supplémentaire disponible).

    Retourne l'UAI choisi, ou None si abandon après 3 tentatives infructueuses.
    """
    niveau = niveau_initial

    while True:
        if len(candidats) == 1:
            c = candidats[0]
            print(f"\nÉtablissement retenu pour « {nom} » : {c['nom']} — {c['commune']} ({c['secteur']})")
            return c["uai"]

        if len(candidats) <= SEUIL_CANDIDATS_AVANT_PRECISION or niveau == "epuise":
            if niveau == "epuise" and len(candidats) > SEUIL_CANDIDATS_AVANT_PRECISION:
                print(f"\n« {nom} » correspond encore à {len(candidats)} établissements "
                      f"même après la précision déjà donnée — aucun niveau de précision "
                      f"supplémentaire disponible, voici la liste complète :")
            else:
                print(f"\nPlusieurs établissements correspondent à « {nom} » :")
            afficher_candidats(candidats)
            choix = input("Ton choix (numéro) > ").strip()
            if choix.isdigit() and 1 <= int(choix) <= len(candidats):
                return candidats[int(choix) - 1]["uai"]
            print("Choix invalide.\n")
            continue

        label = "le département (2 chiffres)" if niveau == "departement" else "la ville"
        print(f"\n« {nom} » correspond à {len(candidats)} établissements — "
              f"précise {label} pour réduire la liste.")

        for tentative in range(1, MAX_TENTATIVES + 1):
            saisie = input(f"Précision ({label}) > ").strip()
            filtres = filtrer_candidats_par_precision(candidats, saisie)

            if filtres:
                candidats = filtres
                break

            label_attendu = ("les 2 premiers chiffres du département"
                             if niveau == "departement" else "le nom de la ville")
            print(f"Aucune correspondance pour « {saisie} » parmi les {len(candidats)} "
                  f"établissements restants. Précise {label_attendu}. "
                  f"(tentative {tentative}/{MAX_TENTATIVES})")

            if tentative == MAX_TENTATIVES:
                print("Trop de tentatives infructueuses — reformule ta question "
                      "complète si tu veux réessayer.")
                return None
        else:
            return None

        if niveau == "departement":
            niveau = "ville"
        elif niveau == "ville":
            niveau = "epuise"


print("Test du chemin comparaison_etablissements_nommes — tape 'quit' pour sortir.\n")
print("Exemple : Compare le collège Victor Hugo et le collège Jean Moulin\n")

while True:
    question = input("Question > ").strip()
    if question.lower() in ("quit", "exit"):
        break

    state: AgentState = {
        "question": question, "dc_niveau": "accessible", "categorie": None,
        "zone_geo": None, "resultats_geo": None, "resultats_sql": None,
        "resultats_rag": None, "reponse_finale": None, "tours_agent": 0,
        "noms_etablissements": [], "resolution_noms": None, "uai_resolus": None,
    }
    resultat = app.invoke(state)

    print(f"[catégorie: {resultat.get('categorie')}]")

    resolution = resultat.get("resolution_noms") or {}
    candidats_par_nom = resolution.get("resultats", {})
    zones_sans_resultat = resolution.get("zones_sans_resultat", {})
    noms_ambigus = [n for n, c in candidats_par_nom.items() if len(c) != 1]

    if zones_sans_resultat:
        print("\n" + resultat["reponse_finale"] + "\n")
        continue

    if not noms_ambigus:
        print("\n" + resultat["reponse_finale"] + "\n")
        continue

    if len(noms_ambigus) > 1:
        print("\nPlusieurs noms ambigus simultanément — non géré en V0, "
              "reformule avec un seul nom à la fois si besoin.\n")
        continue

    nom = noms_ambigus[0]
    candidats = candidats_par_nom[nom]

    if len(candidats) == 0:
        print(f"\nAucun établissement nommé « {nom} » n'a été trouvé dans les données.\n")
        continue

    # Détermine si une zone était déjà présente dans la question, et à quel
    # niveau de précision elle correspond, pour ne pas la redemander.
    zone_geo = resultat.get("zone_geo")
    niveau_initial = "departement"
    if zone_geo:
        type_zone = interpreter_precision(zone_geo)["type"]
        if type_zone == "departement":
            print(f"\n(Département « {zone_geo} » déjà pris en compte depuis ta question — "
                  f"il reste {len(candidats)} établissements pour « {nom} ».)")
            niveau_initial = "ville"
        else:
            print(f"\n(Ville « {zone_geo} » déjà prise en compte depuis ta question — "
                  f"il reste {len(candidats)} établissements pour « {nom} ».)")
            niveau_initial = "epuise"

    uai_choisi = resoudre_ambiguite(nom, candidats, niveau_initial=niveau_initial)
    if uai_choisi is None:
        continue

    state_reprise: AgentState = {
        "question": question, "dc_niveau": "accessible",
        "categorie": "comparaison_etablissements_nommes",
        "zone_geo": None, "resultats_geo": None, "resultats_sql": None,
        "resultats_rag": None, "reponse_finale": None, "tours_agent": 0,
        "noms_etablissements": [], "resolution_noms": None,
        "uai_resolus": [uai_choisi],
    }
    state_reprise = noeud_sql(state_reprise)
    state_reprise = noeud_synthese(state_reprise)
    print("\n" + state_reprise["reponse_finale"] + "\n")
