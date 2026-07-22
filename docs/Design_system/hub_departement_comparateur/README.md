# Handoff : Hub multi-niveaux, page terminale ville & comparateur de collèges

## Overview
Cet ensemble couvre trois briques du parcours « écoles » (recherche de collèges) :

1. **Pages hub** (`/region`, `/…/[region]`, `/…/departement/[dept]`) — un **gabarit unique paramétré** qui liste les sous-divisions d'un territoire et met en avant la recherche ville/adresse.
2. **Page terminale ville** — la vraie page de résultats : la liste des collèges d'une commune, filtrable/triable, avec sélection pour comparaison.
3. **Comparateur** — 2 à 3 collèges côte à côte, alimenté par la sélection de la page ville.

Objectif produit : permettre à un parent de descendre région → département → ville, puis de comparer des collèges sur des critères **honnêtes** (la valeur ajoutée plutôt que le taux brut), sans classement trompeur des territoires.

## À propos des fichiers de design
Les fichiers de ce bundle sont des **références de design réalisées en HTML** (des prototypes qui montrent l'apparence et le comportement attendus), **pas du code de production à copier tel quel**. Ils sont écrits dans un format « Design Component » maison (`.dc.html` + `support.js`) qui n'a pas vocation à être porté.

La tâche est de **recréer ces maquettes dans l'environnement du codebase cible** en utilisant ses patterns établis. Le repo fourni (`agent-ecoles/web`) est un projet **Next.js + TypeScript + Tailwind** : implémenter les écrans en composants React/Tailwind, en réutilisant les composants et tokens déjà présents. Le back-office data (API Python + Supabase) expose déjà la plupart des indicateurs par établissement.

## Fidélité
**Haute-fidélité (hi-fi).** Couleurs, typographies, espacements et états sont définitifs et doivent être reproduits fidèlement, en s'appuyant sur le design system « écoles » (voir `Fiche établissement.dc.html` pour la référence de style la plus aboutie, et les tokens ci-dessous). Les maquettes utilisent des **données d'exemple** (Lyon 5ᵉ, Jean Moulin, etc.) — à remplacer par les données réelles.

---

## Écrans / vues

### 1. Hub — gabarit unique paramétré (`zoneLevel`)
Un seul composant rend les trois niveaux. Un prop `zoneLevel: 'region' | 'departement' | 'ville'` (ou déduit de la route) pilote le contenu ; **la structure ne change pas**.

| Zone | Région | Département | (Ville → voir écran 2) |
|---|---|---|---|
| Fil d'Ariane | Accueil › France › [Région] | Accueil › [Région] › [Dépt] | — |
| Eyebrow + titre | « Région » + nom | « Département » + nom | — |
| Sous-titre | « 12 départements · Académies… » | « 78 communes · Académie… » | — |
| Agrégats (2 cartes) | nb collèges · notation médiane | idem | idem |
| Liste | départements | communes (Lyon groupé, arrondissements dépliables) | — |
| En-têtes de liste | Département / Collèges / Notation / Réussite | Commune / Collèges / Note méd. / Réussite | — |

**Layout** (largeur de contenu ~ 776 px utile, cadre max ~ 1120 px comme la fiche) :
- **Top bar** (sticky, `h ≈ 48 px`) : logo (carré framboise `#D9457A` en rotation `-4deg` + wordmark « écoles » Baloo 2 800/18px `#223B30`), nav « Chercher · Explorer · Comprendre » (Figtree 600/12 `#5C6A60`), pilule framboise « Demander à Camille » avec pastille « C ».
- **Fil d'Ariane** : Figtree 600/11.5, `#8A7B64`, séparateurs `›` en `#C9B79A`.
- **Hero** : `flex` espace-entre. À gauche : eyebrow (Figtree 700/11, uppercase, `letter-spacing .06em`, **framboise `#D9457A`**) + titre (Baloo 2 800/30 `#223B30`) + contexte (Figtree 400/12.5 `#5C6A60`). À droite : 2 cartes agrégats (grille 2 col, largeur ~246 px) — carte blanche, bordure `1.5px #EFE1CE`, radius 12, chiffre Baloo 2 800/22 (notation médiane en vert `#227049`), libellé Figtree 600/10 `#8A7B64`.
- **Bloc « Trouver un collège »** (chemin principal) : carte blanche, radius 14. Champ de recherche = inset `#FBF6EC` bordure `#EFE1CE`, placeholder `#B6A488`, bouton framboise « Rechercher ». En dessous, ligne « Accès rapide » + chips de villes/territoires (fond `#FBF6EC`, bordure `#EAD9BF`, radius 20, Figtree 700/11.5 `#3A4842`).
- **Liste sous-divisions** (chemin secondaire) : titre Baloo 2 800/15 + contrôle de tri à droite. Tableau : bordure `1.5px #EFE1CE`, radius 12 ; ligne d'en-tête fond `#FBF6EC` (Figtree 700/9.5 uppercase `#8A7B64`) ; lignes en grille `1fr 70px 92px 66px 18px`, séparateur `1px #F0E6D2`. Cellules : nom (Figtree 700/13 `#223B30`) + code (500/10 `#8A7B64`) ; nb collèges (Baloo 2 700/13, aligné droite) ; **chip notation** ; **taux de réussite** ; chevron `›` `#C9B79A`.
- **Bloc Camille** (identique sur tous les niveaux) : carte dégradé crème `linear-gradient(155deg,#FBF6EC,#F6FBF7)`, bordure `#E7DECB`, radius 16 ; avatar framboise « C », prompt d'exemple, chips d'exemples.

**Cas particulier Lyon (niveau département)** : ligne « groupée » (fond `#FBF7F1`), notation remplacée par « au détail », chevron `▾`, sous-texte « Déplier pour choisir l'arrondissement ».

### 2. Page terminale ville
Même top bar + fil d'Ariane complet (Accueil › Région › Dépt › Ville).
- **Hero** : eyebrow « Ville » + titre « Collèges à [ville] » + compteur « 7 collèges · 5 publics, 2 privés ». À droite : 2 mini-cartes stats (réussite moyenne, notation médiane).
- **Recherche** : champ pleine largeur (rechercher une autre ville / saisir une adresse pour trouver son secteur).
- **Barre de filtres** : chip actif framboise « Public / Privé » (`#FDEBE4`/`#A82C58`, bordure `#E9A9C0`) + chips neutres « Dispositifs / Sections / Notation min. » (blanc, bordure `#EFE1CE`).
- **Tri + résultats** : « N résultats » + tri (Notation ↓ par défaut).
- **Cartes résultat** : carte blanche radius 13, `flex` align-center gap 14. Badge notation **carré dégradé 44px** (radius 13, dégradé selon la note, ombre teintée) + nom (Baloo 2 700/15) + chips (Public/Privé + dispositifs) + taux de réussite (Baloo 2 800/17, vert si ≥89 sinon ambre) + case « Comparer » + chevron. Résultats au-delà des 2-3 premiers : `opacity` réduite + « + N autres résultats ».
- **Barre de comparaison** (apparaît dès 2 collèges cochés) : barre sombre `#223B30` radius 12, texte blanc « N collèges sélectionnés — … » + bouton framboise « Comparer → » qui route vers le comparateur.

### 3. Comparateur de collèges (`#2a` dans le fichier)
2 à 3 collèges en colonnes, un critère par ligne, **regroupés par rubriques**.

**Layout** : carte **blanche** (`#fff`, bordure `1.5px #EFE1CE`, radius 18, ombre douce). Fil d'Ariane + titre « Comparer 3 collèges ». Grille unique `176px 1fr 1fr 1fr` (colonne libellé + une colonne par collège).
- **En-tête** (non encadré, pensé **sticky**) : par collège, badge notation **solide 50px** (radius 15, couleur unie selon la note, `#2E8F5E`/`#7FB65E`/`#4FA772`) + nom (Baloo 2 800/17 `#223B30`) + « type · ville » (600/10.5 `#8A7B64`). Bouton `×` pour retirer une colonne. Séparateur bas `2px #E7DECB`.
- **Rubriques** (toutes traitées **identiquement**, aucune n'est survalorisée) : label eyebrow framboise (Figtree 700/10 uppercase `letter-spacing .1em` `#D9457A`), puis lignes en grille séparées par `1px #F0E6D2`. Libellé Figtree 600/11.5 `#8A7B64` ; valeurs centrées.
  - **Description** : Langues · Dispositifs · Sections & options (chips DS colorés).
  - **Résultats au brevet** : Taux de réussite (Baloo 2 800/19, vert ≥89 sinon ambre) · Note moy. à l'écrit (Baloo 2 800/19 `#3A4842`).
  - **Valeur ajoutée** : Réussite vs attendu · Note écrit vs attendu (Baloo 2 800/19 vert `#2E8F5E`).
  - **Milieu social** (« on situe, on ne juge pas ») : Public accueilli (IPS) · Mixité sociale — **bleu descriptif `#3A5A8C`**, pas de gagnant.
- **Icônes `?`** : cercle 15px `#F4EFE6`/`#8A7B64`, `cursor:help`, définition dans l'attribut `title` (tooltip natif). Présentes sur : Notation, Dispositifs, Taux de réussite, Valeur ajoutée, Public accueilli (IPS), Mixité sociale. **À porter en tooltip/popover accessible** (pas un simple `title`) dans le codebase.
- Pied : bouton « + Ajouter un collège (max 3) ».

**Décisions de design importantes**
- **Uniformité** : une seule grammaire visuelle (surface blanche, un seul type de filet, en-têtes non encadrés). Pas de traitement spécial pour une rubrique.
- **Pas de marqueur « le + élevé »** : jugé trop lourd — retiré volontairement.
- **Ligne « dans mon secteur » retirée** : elle exige l'adresse de l'élève (donnée non disponible à ce stade). À réintroduire uniquement après saisie d'adresse.
- **La valeur ajoutée est l'indicateur mis en avant éditorialement** (dans la copie / Camille), mais **pas** par un traitement visuel différent.

---

## Composant transverse — Bloc « Demander à Camille »
Camille est l'assistant conversationnel du produit. Le **même composant** apparaît en bas de chaque écran (hub région, hub département, page terminale ville) et doit être **un composant réutilisable unique** (`<CamilleBlock example="…" />`), pas une copie par écran. Seul le prop `example` (la question d'exemple mise en avant) change ; le reste est identique.

**Identité visuelle (règle)** : Camille se distingue des barres de recherche par des **accents framboise** (avatar plein, bouton, teinte de carte, bordures rosées) — **jamais** par un fond framboise plein (illisible), et **le champ de saisie reste blanc** pour rester utilisable. Ne pas confondre avec le champ de recherche, qui est en inset crème neutre.

**Anatomie & tokens**
- **Conteneur** : `background: linear-gradient(155deg,#FCEDF2,#FBF6EC)` (léger lavis framboise), bordure `1.5px #F0C9D8`, radius 16, padding 15–17px, `margin-top:16px`.
- **En-tête** : avatar rond 36px **framboise plein** `#D9457A`, initiale « C » blanche Baloo 2 800/17, ombre `0 3px 9px rgba(168,44,88,.28)` ; titre « Demander à Camille » Baloo 2 800/14 `#223B30` ; sous-titre Figtree 600/11 `#8A7B64`.
- **Champ de saisie** : **fond blanc `#fff`** (zone où l'on tape), bordure framboise claire `1.5px #F0C9D8`, radius 11, padding 11×13. Texte/placeholder de la question d'exemple Figtree 500/12 `#8A7B64` ; bouton « Demander → » **framboise plein** `#D9457A`, texte blanc Baloo 2 800/11, radius 9.
- **Exemples** : libellé « Exemples » Figtree 700/9.5 uppercase `#B0708C` ; chips blancs, bordure `1px #F0C9D8`, texte framboise `#A82C58`, radius 16.

**Comportement** : le champ est un vrai input (saisie libre) ; les chips d'exemples pré-remplissent la question ; « Demander → » ouvre la conversation Camille avec le contexte de la page courante (zone / filtres / sélection). Le prop `example` doit être contextuel : sur le hub « Un bon collège public près de chez moi… », sur la page ville « Entre [A] et [B], lequel fait le plus progresser ses élèves ? ».

**À NE PAS faire** : fond framboise plein sur toute la carte ; champ de saisie translucide ou coloré ; réutiliser le style de la barre de recherche (inset crème) pour Camille.

---

## Interactions & comportement
- **Navigation hub** : clic sur une ligne de sous-division → hub niveau inférieur ; au niveau ville → page terminale (écran 2).
- **Recherche ville/adresse** : chemin principal, présent à tous les niveaux (y compris page terminale). Une adresse précise permet de calculer le secteur (carte scolaire).
- **Lyon groupé** : ligne dépliable révélant les 9 arrondissements.
- **Sélection comparaison** : cases « Comparer » sur les cartes résultat → barre de comparaison sticky en bas → route `/comparer?colleges=uai1,uai2,uai3` → écran 3.
- **Retrait de colonne** : `×` dans l'en-tête du comparateur.
- **Tooltips `?`** : au survol/focus, définition de l'indicateur (accessibles clavier).
- **Tri** : hub = alphabétique par défaut (tri notation / nb collèges en option) ; page ville = notation décroissante par défaut.

## State management
- `zoneLevel` + identifiants de zone (déduits de la route Next.js).
- Liste des sous-divisions / collèges (fetch selon la zone).
- Filtres actifs (public/privé, dispositifs, sections, notation min.) — page ville.
- Tri courant.
- **Sélection de comparaison** (jusqu'à 3 UAI) — à persister entre page ville et comparateur (query string ou store).
- Adresse saisie (optionnelle) → secteur.

## Design tokens
Voir aussi `DESIGN_SYSTEM.md` du repo (`agent-ecoles/docs/Design_system/…`). Principe : **une couleur = un rôle, jamais une décoration**.

**Couleurs sémantiques**
- `action` (produit / CTA / liens / eyebrows de section) : `#D9457A`, foncé `#A82C58`.
- `positif` (réussite, VA+, notes A) : `#2E8F5E` → dégradés `#4FA772`, `#7FB65E`, `#5AAE7E`, `#3E9A6B`.
- `descriptif` (IPS, mixité — positionnel, pas de jugement) : `#3A5A8C`.
- `attention` (résultat sous la moyenne, note B) : `#F0A02E`, foncé `#B0741A`.
- `accent` (rare, notes manuscrites) : `#C15A3C`.

**Chips dispositifs (couleurs fixes, cohérentes partout)**
- REP/REP+ : fond `#E7F1E9`, texte `#227049` (ou en page ville : bleu selon usage) ; ULIS : `#EAF2FA` / `#2C6FA6` ; SEGPA : `#FFF3DE` / `#B0741A` ; Section sportive : `#FDEBE4` / `#C15A3C` ; Section euro./privé : `#EAF2FA` / `#2C6FA6`.

**Chips notation** : A+/A/A- → `#E7F1E9`/`#227049` ; B+/B → `#FBF4E4`/`#B0741A`.
**Badges notation solides** (comparateur / cartes ville) : A+ `#2E8F5E→#1F6B44` · A `#4FA772→#2E8F5E` · A- `#7FB65E→#5E9642` · B+ `#F0A02E→#CE821A`.

**Neutres** : fonds `#F1E7D6` / `#FCF4E9` / `#FBF6EC` / `#fff` ; texte `#223B30` (titres), `#3A4842` / `#5C6A60`, muted `#8A7B64` / `#B6A488` ; bordures `1.5px #EFE1CE`, filets `1px #F0E6D2`, filet interne pointillé `#EAD9BF`.

**Seuils** : réussite brevet ≥ 89 → positif, sinon attention. VA > 0 → positif, < 0 → attention. Note A* → positif, B* → attention. IPS & mixité → toujours descriptif.

**Typographie**
- **Baloo 2** (600–800) : titres & chiffres. Titres de zone 28–30px, chiffres agrégats 22px, valeurs comparateur 19px, wordmark 18px.
- **Figtree** (400–800) : texte courant. Corps 12.5–13px, libellés 10–11.5px, eyebrows 10–11px uppercase.
- **JetBrains Mono** : valeurs techniques / URL (classe `.mono`).
- **Caveat** : réservé aux notes manuscrites de wireframe — **à ne pas reprendre** en production.

**Formes** : cartes radius 12–18 (parfois asymétrique côté « fait-main » sur la fiche) ; rotations légères `-4deg` sur le logo ; ombres douces `0 4–6px 18–22px rgba(34,59,48,.06)`.

## Assets
- Aucun asset bitmap requis. Le logo est une forme CSS (carré framboise arrondi en rotation) — à remplacer par le vrai logo si disponible.
- Icônes : les glyphes `› ▾ ⇅ → ×` et `🔍` sont des placeholders — utiliser le set d'icônes du codebase (ex. lucide) en production.
- La carte de secteur (sur la fiche établissement) est un placeholder CSS → intégrer la vraie carte (carte scolaire) côté produit.

## Files
- `Wireframes hub & terminal.dc.html` — les 3 écrans hi-fi : comparateur (`#2a`) puis hub région (`#1a`), hub département (`#1d`), page terminale ville (`#1c`). Ouvrir dans un navigateur pour voir le rendu.
- `Fiche établissement.dc.html` — la page établissement (référence de style la plus complète : notation, brevet, valeur ajoutée, positionnement social, dispositifs expliqués, synthèse IA). À traiter comme la source de vérité visuelle du design system.
- `support.js`, `image-slot.js` — runtime des prototypes (non porté ; nécessaire seulement pour ouvrir les `.dc.html`).

> Repo cible : `agent-ecoles/web` (Next.js + TS + Tailwind). Données par établissement déjà disponibles côté API/Supabase (réussite brevet, VA, IPS, mixité, langues, dispositifs). Dépendance à créer côté back : **agrégats par sous-division** (notation médiane / réussite d'une région ou d'un département) — non encore exposés.
