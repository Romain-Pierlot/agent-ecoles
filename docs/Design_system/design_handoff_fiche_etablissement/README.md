# Handoff — Fiche établissement & Design System « écoles »

## Overview
Ce paquet documente la **page “Fiche établissement”** (page collège) du produit *écoles* et le **design system** qui la gouverne. Objectif produit : donner à un parent une lecture claire, honnête et non anxiogène des données officielles d'un collège (identité, secteur/carte scolaire, résultats au brevet, valeur ajoutée, positionnement social, dispositifs, voisins), avec un assistant IA (« Camille ») qui explique et nuance les indicateurs à partir de sources officielles de l'Éducation nationale (RAG).

## À propos des fichiers de design
Les fichiers `.dc.html` de ce paquet sont des **références de design réalisées en HTML** — des prototypes qui montrent l'intention visuelle et le comportement, **pas du code de production à copier tel quel**. La tâche est de **recréer ces designs dans l'environnement existant du repo** (`web/`, framework front en place) en suivant ses patterns. Ils s'ouvrent directement dans un navigateur pour référence visuelle.

## Fidélité
**Haute fidélité (hifi).** Couleurs, typographie, espacements et hiérarchie sont définitifs. À reproduire fidèlement avec les composants/libs du repo. Les **données affichées sont illustratives** (Collège Jean Moulin, IPS 112, etc.) — à brancher sur les vraies données par UAI.

## Le principe fondateur
**Une couleur = un rôle, jamais une décoration.** On ne code jamais un hex « en dur » sur une donnée : on lui applique le token sémantique qui porte son sens. Voir `DESIGN_SYSTEM.md` pour la règle complète et la fonction `sentiment()`.

## Écrans / vues

### Fiche établissement (`Fiche établissement.dc.html`)
Page unique scrollable, largeur de contenu **1120px** centrée, fond crème `#FCF4E9`.

Sections dans l'ordre :
1. **Top bar** (sticky) — logo « écoles », nav (Chercher / Explorer / Comprendre), CTA « Demander à Camille ».
2. **Fil d'Ariane + URL** — région › département › commune › établissement.
3. **Fiche identité** (grille 2 colonnes `1fr 340px`) :
   - Carte identité : statut, nom (Baloo 2 800/34px), adresse, **pastille de notation maison** (A+/A/A-/B+/B), badges dispositifs, coordonnées (UAI, tél, courriel, site, académie, zone), langues & options intégrées, bandeau vacances.
   - Rail droit : vignette carte de secteur, CTA « Suis-je dans le secteur ? », carte assistant Camille (compacte).
4. **Barre d'ancres** (sticky) — Identité / Localisation / Résultats & public / Dispositifs / Voisins.
5. **Résultats au brevet** (`#brevet`) : 3 cartes stats (libellé au-dessus, chiffre 40px vedette, repères National/Rhône), donut des mentions, histogramme d'évolution (vert uni), bloc **valeur ajoutée** (2 cartes), et bloc **positionnement social** rattaché (IPS + mixité en bleu descriptif).
6. **Dispositifs expliqués** — REP+, ULIS, SEGPA en clair (sans jargon).
7. **Synthèse IA** — résumé « par Camille » + CTA.
8. **Voisins** — collèges à proximité (IPS + VA).

## Tokens & règles
Voir **`DESIGN_SYSTEM.md`** — palette, 6 tokens sémantiques, tableau de seuils par indicateur, fonction `sentiment()`, typographie, principes.

## Design tokens (résumé)
- **Framboise `#D9457A`** (foncé `#A82C58`) — produit & action : logo, CTA, assistant, liens, intitulés de section.
- **Vert `#2E8F5E`** (intensités jusqu'à `#9BCBAF`) — résultat favorable.
- **Bleu encre `#3A5A8C`** — indicateur descriptif/positionnel (IPS, mixité) : on situe, on ne juge pas.
- **Ambre `#F0A02E`** (texte `#B0741A`) — point de vigilance sur donnée. Jamais un bouton.
- **Terracotta `#C15A3C`** — accent rare + notes manuscrites (Caveat).
- **Neutres** — fonds `#F1E7D6` / `#FCF4E9` / `#fff`, repères/taupe `#8A7B64`, texte `#223B30`, filets `#EFE1CE`.
- **Typo** — Baloo 2 (titres/chiffres, 700-800), Figtree (courant, 400-700), Caveat (notes manuscrites), JetBrains Mono (valeurs/technique).
- **Rayons** — cartes 18-26px, souvent asymétriques (ex. `26px 22px 26px 24px`) pour le côté fait-main.
- **Bordures** — `2px solid #EFE1CE` sur cartes ; filets internes `1px dashed #EAD9BF`.

## Interactions & comportement
- Top bar + barre d'ancres **sticky**.
- Assistant Camille : ouvre un chat qui **n'explique que les indicateurs affichés**, nuancés via RAG sur sources officielles (Éducation nationale). Ne répond pas sur le subjectif (ambiance, « bon pour enfant timide »).
- CTA carte scolaire → page dédiée « vérifier mon secteur à partir de mon adresse » (à la rue près).
- Liens : soulignés (jamais de flèche ↗ qui suggère une progression).
- Animation `camPulse` (halo pulsé) sur l'avatar Camille.

## State / props (prototype)
- `rating` (enum A+/A/A-/B+/B) → pilote couleur + libellé de la pastille de notation.
- `assistantName` (défaut « Camille »).
- `showNotes` (bool) → affiche/masque les annotations manuscrites Caveat.
- `secteurConfirmed` (bool) → état « adresse vérifiée dans le secteur ».

## Fichiers de ce paquet
- `Fiche établissement.dc.html` — la page complète (référence hifi).
- `Design System.dc.html` — la doc visuelle du design system.
- `DESIGN_SYSTEM.md` — la version texte, lisible par un dev, à garder en source de vérité.

## Assets
Aucune image externe : cartes/pictos sont des formes CSS. Polices via Google Fonts (Baloo 2, Figtree, Caveat, JetBrains Mono). Les vraies données proviennent des jeux officiels (IPS collèges, valeur ajoutée DNB, ségrégation sociale, registre cantines) déjà présents dans `data/`.
