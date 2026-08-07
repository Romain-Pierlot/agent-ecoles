"""
test_rapprochement_carte_scolaire.py — Non-régression du rapprochement
adresse -> collège de secteur, contre le vrai code de prod
(agent/tools/carte_scolaire_tool.py::rapprocher_adresse_secteur).

Recrée en test reproductible ce qui était un script jetable de scratchpad
pendant l'étude de faisabilité (docs/exploration/etude_matching_carte_scolaire.md,
2026-07-23) : on part de lignes réelles du CSV source (donc un code_rne
attendu connu à l'avance), on reconstruit une adresse plausible dans la
plage de numéros de cette ligne, on géocode via l'API BAN puis on vérifie
que le rapprochement retrouve le bon collège.

Échantillonnage restreint aux tronçons à PLAGE RESSERRÉE (< 50 numéros) —
~19% du fichier. Investigation du 2026-07-23 (implémentation de cette
fonctionnalité) : ~74% des lignes ont une plage "ouverte" jusqu'à 9999
(valeur sentinelle du Ministère pour "le reste de la rue"). Un numéro tiré
au hasard dans une telle plage tombe presque toujours sur une adresse qui
n'existe pas physiquement — un artefact de la RECONSTRUCTION synthétique
d'adresse, pas une limite réelle pour un utilisateur qui, lui, tape sa
propre adresse (qui existe forcément). Se restreindre aux plages resserrées
est un bien meilleur proxy d'une adresse réelle.

Seed FIXE et commitée (contrairement au script original) : reproductible
d'une exécution à l'autre. Taux attendu mesuré sur cette même population
(85,0%, 340/400, après les 3 corrections de normalisation apostrophe/
lieu-dit/parenthèse ajoutées le même jour) ± tolérance — pas une égalité
stricte, un échantillon aléatoire à seed identique peut légèrement varier,
mais un écart de plus de ~10 points doit alerter sur une régression du
pipeline, pas seulement sur l'aléa du tirage.

Test lent et réseau (appelle réellement l'API BAN, ~250 requêtes avec pause
entre chaque) — à lancer à la demande :
    source venv/bin/activate && python3 test_rapprochement_carte_scolaire.py
"""

import os
import random
import time

import pandas as pd

from agent.tools.carte_scolaire_tool import rapprocher_adresse_secteur

CSV_CARTE_SCOLAIRE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fr-en-carte-scolaire-colleges-publics.csv")
SEED = 20260723        # date de l'étude originale, figée ici pour la reproductibilité
N_ECHANTILLON = 250
LARGEUR_PLAGE_MAX = 50       # au-delà, la plage "ouverte" (souvent jusqu'à 9999) n'est pas un proxy fiable d'une adresse réelle
PAUSE_ENTRE_APPELS_S = 0.15   # même marge que l'étude, largement sous le quota BAN (50 req/s)
TAUX_ATTENDU = 0.85
TOLERANCE_POINTS = 0.10       # ±10 points de pourcentage


def _numero_plausible(numero_debut: int, numero_fin: int, parite: str) -> int:
    """Choisit un numéro dans la plage [numero_debut, numero_fin] respectant
    la parité de la ligne (même contrainte que le rapprochement réel)."""
    candidats = [
        n for n in range(numero_debut, numero_fin + 1)
        if parite == "PI" or (n % 2 == 0) == (parite == "P")
    ]
    return random.choice(candidats) if candidats else numero_debut


def _construire_adresse(ligne) -> str:
    numero = _numero_plausible(
        int(float(ligne["No_de_voie_debut"])), int(float(ligne["No_de_voie_fin"])), ligne["parite"]
    )
    return f"{numero} {ligne['type_et_libelle']}, {ligne['code_postal']} {ligne['libelle_commune']}"


def _echantillon_250_adresses():
    df = pd.read_csv(CSV_CARTE_SCOLAIRE, sep=";", dtype=str)
    df = df[df["parite"].isin(["I", "P", "PI"])].copy()
    largeur = pd.to_numeric(df["No_de_voie_fin"]) - pd.to_numeric(df["No_de_voie_debut"])
    df = df[largeur < LARGEUR_PLAGE_MAX].copy()
    return df.sample(n=N_ECHANTILLON, random_state=SEED)


def test_non_regression_taux_global():
    echantillon = _echantillon_250_adresses()
    n_corrects = 0
    for _, ligne in echantillon.iterrows():
        adresse = _construire_adresse(ligne)
        resultat = rapprocher_adresse_secteur(adresse)
        assert resultat["success"], f"Échec technique inattendu sur {adresse!r} : {resultat['error']}"
        uais_trouves = {c["uai"] for c in resultat["colleges_secteur"]}
        if ligne["code_rne"] in uais_trouves:
            n_corrects += 1
        time.sleep(PAUSE_ENTRE_APPELS_S)

    taux = n_corrects / N_ECHANTILLON
    print(f"\nTaux de correspondance exacte : {n_corrects}/{N_ECHANTILLON} = {taux:.1%} (étude originale : 58,8%)")
    assert abs(taux - TAUX_ATTENDU) <= TOLERANCE_POINTS, (
        f"Taux {taux:.1%} hors tolérance de l'étude ({TAUX_ATTENDU:.1%} ± {TOLERANCE_POINTS:.0%}) "
        "— possible régression du pipeline, pas juste l'aléa du tirage."
    )


def test_cas_maxeville_multi_secteur():
    """Cas réel confirmé pendant l'étude : 3 collèges superposés sur la même
    plage de numéros (5-9, impair) de la Rue Blaise Pascal à Maxéville."""
    resultat = rapprocher_adresse_secteur("7 Rue Blaise Pascal, 54320 Maxéville")
    assert resultat["success"]
    assert resultat["etat"] == "multi_secteur"
    uais = {c["uai"] for c in resultat["colleges_secteur"]}
    assert uais == {"0541327Z", "0541469D", "0541568L"}, uais


def test_cas_adresse_non_reconnue():
    resultat = rapprocher_adresse_secteur("zzzzxxxxyyyy1234invalide")
    assert resultat["success"]
    assert resultat["etat"] == "adresse_non_reconnue"


def test_cas_ville_seule_non_determinable():
    resultat = rapprocher_adresse_secteur("Villeurbanne")
    assert resultat["success"]
    assert resultat["etat"] == "non_determinable"


if __name__ == "__main__":
    print("=== Cas fixes ===")
    test_cas_maxeville_multi_secteur()
    print("✓ Maxéville multi-secteur (3 collèges)")
    test_cas_adresse_non_reconnue()
    print("✓ Adresse non reconnue")
    test_cas_ville_seule_non_determinable()
    print("✓ Ville seule -> non déterminable")

    print("\n=== Non-régression sur 250 adresses réelles (lent, ~1min) ===")
    test_non_regression_taux_global()
    print("✓ Taux global dans la tolérance attendue")
