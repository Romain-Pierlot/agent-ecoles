# Sources de données

Les fichiers CSV ne sont pas versionnés (trop lourds, données publiques).
Télécharge-les depuis data.education.gouv.fr et place-les dans ce dossier.

## Fichiers requis

| Fichier | Source |
|---|---|
| `frenipscollegesap2023.csv` | [IPS collèges](https://data.education.gouv.fr/explore/dataset/fr-en-ips-colleges-ap2023/) |
| `frenindicateursvaleurajouteecolleges.csv` | [IVAC collèges](https://data.education.gouv.fr/explore/dataset/fr-en-colleges-valeur-ajoutee-dnb/) |
| `frenannuaireeducation_col_lycees.csv` | [Annuaire éducation](https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/) — filtrer collèges + lycées |

## Ingestion

Une fois les CSV en place :
```bash
python3 data/ingest.py
```
