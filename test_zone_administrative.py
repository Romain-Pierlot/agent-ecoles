"""
test_zone_administrative.py — Vérifie resoudre_zone_administrative + la
recherche région/département/nationale associée. Aucun appel API/LLM (tout
est déterministe, SQLite pur) — test rapide et peu coûteux.

Ajouté lors de la conception des guardrails (cf. docs/decision_log.md) :
support de "France" (nationale, DOM-TOM inclus) et "France métropolitaine"
(DOM-TOM exclus), en plus de région/département déjà existants.
"""

from agent.tools.sql_tool import resoudre_zone_administrative
from agent.tools.geo_tool import rechercher_etablissements_region_departement

CAS_DE_TEST = []


def test(nom, condition):
    CAS_DE_TEST.append((nom, condition))


# --- resoudre_zone_administrative : reconnaissance du type de zone ---
test("région reconnue (Bretagne)", resoudre_zone_administrative("Bretagne")["type"] == "region")
test("département reconnu (44)", resoudre_zone_administrative("44")["type"] == "departement")
test("France -> national", resoudre_zone_administrative("France")["type"] == "national")
test("France métropolitaine -> national_metropole", resoudre_zone_administrative("France métropolitaine")["type"] == "national_metropole")
test("métropole (seul) -> national_metropole", resoudre_zone_administrative("métropole")["type"] == "national_metropole")
test("zone inconnue -> type None", resoudre_zone_administrative("Atlantide")["type"] is None)

# --- rechercher_etablissements_region_departement : comptages réels ---
resultat_national = rechercher_etablissements_region_departement("national", None, "France")
resultat_metropole = rechercher_etablissements_region_departement("national_metropole", None, "France métropolitaine")
resultat_martinique = rechercher_etablissements_region_departement("region", "Martinique", "Martinique")

test("national : succès", resultat_national["success"] is True)
test("national : au moins autant d'établissements que métropole seule", resultat_national["nb_etablissements"] >= resultat_metropole["nb_etablissements"])
test("national_metropole : strictement moins que national (DOM-TOM exclus)", resultat_metropole["nb_etablissements"] < resultat_national["nb_etablissements"])
test("national_metropole : différence = établissements DOM-TOM du national", resultat_national["nb_etablissements"] - resultat_metropole["nb_etablissements"] == 502)
test("Martinique : toujours géré normalement (région), non affecté par les nouveaux cas", resultat_martinique["success"] is True and resultat_martinique["nb_etablissements"] == 77)


def tester():
    print("=== TEST ZONE ADMINISTRATIVE (région / département / nationale) ===\n")
    for nom, condition in CAS_DE_TEST:
        symbole = "✓" if condition else "✗"
        print(f"{symbole} {nom}")
    nb_ok = sum(1 for _, c in CAS_DE_TEST if c)
    print(f"\n=== RÉSULTAT : {nb_ok}/{len(CAS_DE_TEST)} corrects ===")
    return nb_ok == len(CAS_DE_TEST)


if __name__ == "__main__":
    import sys
    sys.exit(0 if tester() else 1)
