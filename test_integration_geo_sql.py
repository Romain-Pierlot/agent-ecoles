"""
test_integration_geo_sql.py — Vérifie que le chaînage geo_tool -> sql_tool
fonctionne : le filtre UAI trouvé par geo est bien transmis et respecté par SQL.

Fait de vrais appels (API BAN + SQLite + LLM pour la génération SQL) —
plus lent qu'un test unitaire, c'est normal.
"""

from agent.tools.geo_tool import recherche_geo
from agent.tools.sql_tool import recherche_sql

def tester():
    print("=== TEST D'INTÉGRATION geo_tool -> sql_tool ===\n")

    # Étape 1 : geo_tool seul
    print("1. Appel recherche_geo('Lyon', 10)...")
    resultat_geo = recherche_geo("Lyon", 10)

    if not resultat_geo["success"]:
        print(f"✗ ÉCHEC geo_tool : {resultat_geo['error']}")
        return

    uai_geo = [e["uai"] for e in resultat_geo["etablissements"]]
    print(f"✓ geo_tool OK — {len(uai_geo)} établissements trouvés dans le rayon")
    print(f"  Exemples d'UAI : {uai_geo[:3]}\n")

    if not uai_geo:
        print("⚠ Aucun établissement trouvé — impossible de tester le chaînage plus loin.")
        return

    # Étape 2 : sql_tool avec le filtre UAI
    print("2. Appel recherche_sql avec uai_filtre=<UAI trouvés par geo>...")
    resultat_sql = recherche_sql(
        "Quels sont les scores de ces collèges ?",
        uai_filtre=uai_geo
    )

    if not resultat_sql["success"]:
        print(f"✗ ÉCHEC sql_tool : {resultat_sql['error']}")
        return

    print(f"✓ sql_tool OK — {resultat_sql['nb_resultats']} résultats")
    print(f"  SQL généré : {resultat_sql['sql_genere']}\n")

    # Étape 3 : vérification — les UAI retournés par SQL sont-ils bien
    # un sous-ensemble de ceux trouvés par geo ?
    uai_retournes_sql = {row.get("uai") for row in resultat_sql["resultats"] if "uai" in row}

    if not uai_retournes_sql:
        print("⚠ La requête SQL générée ne retourne pas la colonne 'uai' — impossible de vérifier le filtre.")
        print("  (Le SQL généré doit inclure e.uai dans le SELECT pour que ce test soit concluant.)")
        return

    uai_geo_set = set(uai_geo)
    hors_perimetre = uai_retournes_sql - uai_geo_set

    if hors_perimetre:
        print(f"✗ ÉCHEC : {len(hors_perimetre)} établissement(s) retourné(s) par SQL hors du périmètre géo !")
        print(f"  UAI problématiques : {hors_perimetre}")
    else:
        print(f"✓ SUCCÈS : tous les établissements retournés par SQL sont bien dans le périmètre geo.")

if __name__ == "__main__":
    tester()
