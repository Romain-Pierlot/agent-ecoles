# Handoff : Recherche — barre transverse, autocomplétion & page de résultats

## Overview
Cet ensemble couvre la **porte 2 « Chercher »** du parcours « écoles » :

1. **Barre de recherche transverse** — un **composant unique**, une seule densité, présent sur l'accueil, le hub Explorer, l'en-tête des pages internes et en haut de la page de résultats.
2. **Autocomplétion** — panneau de suggestions groupées (établissements → communes → maillage) qui s'ouvre au focus/à la frappe.
3. **Page de résultats** (`/recherche`) — résultats **mixtes** (communes + établissements), avec filtres, tris et cartes établissement.

Objectif produit : un accès **direct et rapide** à une destination connue (un collège, un lieu). La recherche route vers un **LIEU** ou une **FICHE** ; elle ne fait pas de recommandation par critères — ça, c'est le rôle de Camille (l'assistant conversationnel). Le filtrage fin (options, langues, dispositifs, notation) se fait **sur la page de résultats**, pas dans la barre.

## À propos des fichiers de design
Les fichiers de ce bundle sont des **références de design réalisées en HTML** (des prototypes qui montrent l'apparence et le comportement attendus), **pas du code de production à copier tel quel**. Ils sont écrits dans un format « Design Component » maison (`.dc.html` + `support.js`) qui n'a pas vocation à être porté.

La tâche est de **recréer ces maquettes dans l'environnement du codebase cible** (`agent-ecoles/web`, Next.js + TypeScript + Tailwind), en réutilisant ses composants et tokens. Le back-office data (API Python + Supabase) expose déjà la plupart des indicateurs par établissement.

## Fidélité
**Haute-fidélité (hi-fi).** Couleurs, typographies, espacements et états sont définitifs. S'appuyer sur le design system « écoles » (voir `Fiche établissement.dc.html` pour la référence de style, et les tokens ci-dessous). Les maquettes utilisent des **données d'exemple** (requête « moulin », Jean Moulin, Moulins…) — à remplacer par les données réelles.

---

## Le parti pris (règle produit)
- **Recherche = OÙ / QUEL** : accès direct à une destination qu'on connaît (nom, UAI, ville, CP, département, région, adresse).
- **Camille = LEQUEL, POUR MOI** : le choix par critères et arbitrages, en conversation.
- La barre **ne traite pas** les critères en langage naturel. Les critères (chorale, allemand, ULIS, notation…) sont des **filtres sur la page de résultats**.

---

## Écran 1 — Barre de recherche transverse

**Une seule densité, partout** (pas de version compacte). Le même composant sur : accueil (bande sous le héros Camille), hub Explorer (héros), en-tête des pages internes (région / département / ville) et haut de la page de résultats.

**Ce qu'on peut saisir → où ça route** (détection par heuristiques simples : regex CP/UAI, correspondance base villes/établissements) :

| Type détecté | Exemple | Destination |
|---|---|---|
| Nom d'établissement | `Jean Moulin` | Fiche (ou liste si plusieurs) — `/…/college/{nom-uai}` |
| **Code UAI** | `0690123B` | Fiche établissement (direct) — `/…/college/{uai}` |
| Ville / commune | `Lyon 5ᵉ` | Page Ville — `/ville/{slug}` |
| Code postal | `69005` | Page Ville de ce CP — `/ville/{slug}` |
| Département | `Rhône · 69` | Maillage département — `/departement/{slug}` |
| Région | `Auvergne-Rhône-Alpes` | Maillage région — `/region/{slug}` |
| **Adresse complète** | `12 rue des Farges, 69005 Lyon` | Collèges les plus proches, **tri par distance** — `/recherche?près=…` |

**Anatomie (densité pleine)** : carte/bande blanche ; titre « Chercher un collège ou un lieu » (Baloo 2 800/30 `#223B30`) + sous-titre (Figtree 400/14.5 `#5C6A60`). Champ = **vrai input** dans un conteneur blanc, bordure `2px #EFE1CE` (→ **framboise `#D9457A` au focus**), radius 18, ombre `0 10px 30px rgba(34,59,48,.10)` ; icône `⌕` `#C9A98A` ; bouton framboise plein « Chercher ». Sous le champ : ligne « Fréquent : » + chips de villes (blanc, bordure `#EBD9BF`, radius 16).

**Recherche par adresse (démontré dans le prototype)** : une adresse saisie reste tapée **dans le même champ** que le reste (aucun changement de nature). Quand la saisie est reconnue comme une adresse (heuristique : n° + mot de voie), l'autocomplétion propose en tête une ligne de confirmation framboise « 📍 Chercher les collèges les plus proches ». Sur `/recherche`, ce mode : masque le groupe Communes, affiche un bandeau « 📍 Autour de {adresse} — triés par distance · Modifier », bascule le tri par défaut sur **Distance ↑**, et ajoute sur chaque carte établissement un **badge distance** (`📍 1,2 km`, famille bleue `#EAF2FA`/`#2C6FA6`) à côté du % brevet. Un raccourci de démo (chip framboise « 📍 12 rue des Farges, Lyon » sous le champ) permet de visualiser ce mode sans taper.

---

## Écran 2 — Autocomplétion

S'ouvre dès **1 caractère** au focus ; se ferme au blur (délai ~130 ms pour laisser le clic passer).

- **Panneau** : blanc, bordure `1.5px #EFE1CE`, radius 18, ombre `0 18px 44px rgba(34,59,48,.16)`, en overlay absolu sous le champ (ne pousse pas la page).
- **Groupes, dans cet ordre** : `Établissements` → `Communes` → `Départements / Régions`. En-tête de groupe Figtree 700/9.5 uppercase `#B6A488`. Un groupe vide est masqué. **Max 4 items par groupe** — au-delà, on renvoie vers « voir tous les résultats ». Les 3 groupes sont démontrés dans le prototype sur la requête « moulin » (Établissements Jean Moulin / Moulin des Prés · Communes Moulins / Moulins-lès-Metz · Départements/Régions « Allier — préfecture : Moulins »).
- **Item établissement** : **badge notation** (carré dégradé 32px, radius 10, dégradé selon la note) + nom (Figtree 700/14) + méta « ville · dépt · public » (500/11.5) + chevron `→`. **La notation est le repère affiché ici** (pas la valeur ajoutée).
- **Item commune** : icône `⌂` (carré crème `#F1E7D6`) + nom + « dépt · N collèges ».
- **Pied persistant** : « Voir tous les résultats pour « … » → » (framboise). Si aucune correspondance : message « Aucune correspondance directe » + ce même lien.
- **Clavier** : `↑ ↓` naviguent, `Entrée` = 1ᵉ résultat (ou page de résultats si rien de survolé), `Échap` ferme.

---

## Écran 3 — Page de résultats (`/recherche`)

Un nom unique route direct vers la fiche. Sinon on arrive ici. Les résultats peuvent **mêler communes et établissements** → on les **groupe** (communes d'abord, puis établissements). La barre de recherche (écran 1) est **reprise en haut** de la page.

### Groupe Communes
- En-tête « Communes · N » (eyebrow framboise) + **tri** (« Trier : A→Z ⇅ »).
- Ligne commune : icône `⌂` + nom (Baloo 2 700/14.5) + « dépt (code) · N collèges » + affordance **« Voir la commune → »** (framboise). Toute la ligne est cliquable (hover framboise `#FDEFF4`).
- **Requête courte** (ex : « mou ») → beaucoup de communes : **pagination 20/page** + « voir toutes les communes ».

### Groupe Établissements
- En-tête « Établissements · N » + **tri cliquable** « Trier : {label} ⇅ ».
- **Barre de filtres** : label « FILTRER » + chips (« Public / Privé ▾ », « Dispositifs ▾ », « Sections & langues ▾ », « Notation min. ▾ »). Chaque chip **ouvre un menu de valeurs** (popover : liste des valeurs individuelles avec case à cocher) ; sélection **multiple** possible ; une valeur choisie devient une **puce détachable** framboise `#FDEBE4`/`#A82C58` bordure `#E9A9C0` avec `✕`, affichée au-dessus de la liste. Les **valeurs menant à 0 résultat sont grisées** et non cliquables, avec la mention « 0 résultat » (démontré : `UPE2A` sous Dispositifs, `Section inter.` sous Sections & langues). Lien « Réinitialiser » quand au moins un filtre est actif. *(Le prototype ne recalcule pas dynamiquement quelles valeurs sont à 0 — l'état grisé est montré sur un cas d'exemple ; à câbler côté produit à partir des facettes réelles.)*
- **Carte résultat** : blanche, radius 14, `flex` align-center gap 14. Badge notation **carré dégradé 46px** (selon la note, ombre teintée) + nom (Baloo 2 700/15.5) + **tags harmonisés** (voir règle ci-dessous) + % réussite brevet (Baloo 2 800/17, vert `#227049` si ≥ moyenne nationale de la session sinon ambre `#B0741A`) + affordance **« Voir le collège → »**.
- **Pagination** : ligne pointillée « + N autres établissements · pagination ».
- **Bloc Camille** en pied (composant réutilisable — voir plus bas).

### Règle des tags harmonisés (important)
On ne montre **jamais tout**. Par carte :
1. **Statut d'abord** : `Public` (vert) ou `Privé` (bleu).
2. Puis **2 tags max**, dans un **ordre de priorité fixe** : éduc. prioritaire (REP+/REP) > dispositif (ULIS, SEGPA) > section / langue (Section euro, internationale, Allemand…) > option (Chorale, Latin…).
3. Le reste se replie en une puce **« +N » cliquable** : au clic, elle **déplie les tags restants dans la carte** (libellé « − réduire ») ; tooltip au survol. **Jamais** une nouvelle page.
4. **Couleurs par famille, limitées au statut** : statut public = vert, statut privé = bleu. Dispositifs, sections et langues (REP/REP+, ULIS, SEGPA, sections euro/sport/arts/…, Allemand, Chorale…) restent en **neutre** — convention de couleur non tranchée pour ces badges factuels, voir `journal_de_bord.md` (S15.1) ; on ne code pas une couleur en dur tant que ce n'est pas décidé. « +N » = même neutre.

### Tris (deux listes, deux tris)
- **Établissements** : `Notation ↓` (défaut) · `Notation ↑` · `Réussite brevet` · `Distance` (si adresse saisie) · `Nom A→Z`.
- **Communes** : `Nom A→Z` (défaut) · `Nombre de collèges` · `Proximité` (si adresse).
- Le tri **A→Z** est le repli sûr quand aucune métrique ne s'impose (indispensable sur une requête courte).

### Filtres exhaustifs (comportement)
- Les filtres se **cumulent (ET)** ; un **compteur live** suit chaque changement.
- Pour éviter les impasses : **griser (ou masquer) les valeurs qui mèneraient à 0** résultat compte tenu des filtres déjà posés.
- Si 0 résultat malgré tout → état vide clair : « aucun collège ne coche tout ça » + **retirer le dernier filtre** / **tout réinitialiser**.
- Les filtres actifs apparaissent en **puces détachables** au-dessus de la liste.

---

## Composant transverse — Bloc « Demander à Camille »
Camille est l'assistant conversationnel du produit. Le **même composant** apparaît en pied de la page de résultats (et ailleurs) — un **composant réutilisable unique** (`<CamilleBlock example="…" />`), pas une copie par écran. Seul le prop `example` change.

**Identité visuelle (règle)** : Camille se distingue de la barre de recherche par des **accents framboise** (avatar plein, bouton, teinte de carte, bordures rosées) — **jamais** un fond framboise plein, et **le champ reste blanc**. Ne pas confondre avec le champ de recherche (inset crème neutre).

**Anatomie & tokens**
- **Conteneur** : `background: linear-gradient(155deg,#FCEDF2,#FBF6EC)`, bordure `1.5px #F0C9D8`, radius 16.
- **En-tête** : avatar rond 36–38px **framboise plein** `#D9457A`, initiale blanche Baloo 2 800/17, ombre `0 3px 9px rgba(168,44,88,.28)` ; titre Baloo 2 800/14 `#223B30` ; sous-titre Figtree 600/11 `#8A7B64`.
- **CTA** : « Demander à {assistantName} → » framboise plein, texte blanc, radius 11.
- Sur la page de résultats, `example` doit être contextuel : « Entre [A] et [B], lequel fait le plus progresser ses élèves ? ».

---

## Interactions & comportement (récap)
- **Focus champ** → dropdown ouvert ; **frappe** → suggestions filtrées (substring sur nom + clés) ; **blur** → fermeture différée ~130 ms.
- **Clic suggestion** → remplit le champ et route (utiliser `onMouseDown` pour devancer le blur).
- **Submit / « Voir tous les résultats »** → page `/recherche?q=…` (routeur : nom→fiche, ville/CP→ville, dépt/région→maillage, adresse→proches).
- **Tri** : cliquable, cycle documenté ci-dessus (le prototype cycle au clic ; en prod, un menu déroulant est acceptable).
- **Filtres** : chip → menu de valeurs → puce détachable ✕ ; compteur live ; griser les valeurs à 0.
- **« +N »** : clic → déplie/replie les tags dans la carte.
- **« Voir le collège / la commune »** → fiche / page ville.

## State management
- `query` (contrôlé) + `focused` (ouverture dropdown).
- Suggestions (fetch débouncé selon `query` ; grouper par type).
- `estSort` / `commSort` (tri courant par liste).
- `filters` actifs (public/privé, dispositifs, sections, notation min.) + compteur live.
- `expanded` par carte (état du « +N »).
- Pagination (communes & établissements).
- Adresse saisie (optionnelle) → tri par distance.

## Design tokens
Voir aussi `DESIGN_SYSTEM.md` du repo. Principe : **une couleur = un rôle**.

**Couleurs sémantiques**
- `action` (CTA / liens / eyebrows / focus champ) : `#D9457A`, foncé `#A82C58`.
- `positif` (réussite, notes A) : `#2E8F5E` → `#3E9A6B`, `#4FA772`, `#7FB65E`.
- `descriptif` (IPS, mixité) : `#3A5A8C`.
- `attention` (sous la moyenne, note B) : `#F0A02E`, foncé `#B0741A`.

**Tags** : statut public `#E7F1E9`/`#227049` ; statut privé `#EAF2FA`/`#2C6FA6` ; dispositifs/sections/langues (REP/REP+, ULIS, SEGPA, sections, langues) en **neutre** `#F1E7D6`/`#8A7B64` — convention couleur non tranchée, voir `journal_de_bord.md` (S15.1) ; « +N » même neutre `#F1E7D6`/`#8A7B64`.

**Badges notation solides (dégradés)** : A+ `#2E8F5E→#1F6B44` · A `#3E9A6B→#2E8F5E` · A- `#7FB65E→#5E9642` · B+ `#F0A02E→#CE821A` · B `#EBAE4A→#C98A1E`.

**Neutres** : fonds `#FCF4E9` / `#FBF6EC` / `#F1E7D6` / `#fff` ; texte `#223B30` (titres), `#3A4842` / `#5C6A60`, muted `#8A7B64` / `#B6A488` / `#A8987F` ; bordures `1.5px #EFE1CE`, filets `1px #F0E6D2`.

**Seuils** : réussite brevet ≥ moyenne nationale de la session (comparaison relative, pas un seuil fixe — voir `web/src/lib/tokens.ts`) → positif, sinon attention. Note A* → positif, B* → attention.

**Typographie**
- **Baloo 2** (600–800) : titres & chiffres (titre 26–30px, badge notation, % brevet, nom collège 15–15.5px, wordmark).
- **Figtree** (400–800) : texte courant, méta, chips, eyebrows uppercase.
- **Caveat** : réservé aux notes de wireframe — **à ne pas reprendre** en production.

## Assets
- Aucun bitmap requis. Logo = forme CSS (carré framboise arrondi, rotation `-4deg`) → remplacer par le vrai logo.
- Icônes : `⌕ ⌂ ⇅ → ✕ ▾` sont des placeholders → utiliser le set du codebase (ex. lucide).

## Files
- `Recherche.dc.html` — **la référence hi-fi principale** : barre + autocomplétion (3 groupes) + page de résultats, interactive (tri dont Distance, menu de filtres par valeur avec grisage à 0 résultat, expand « +N », mode adresse via la chip de démo « 📍 12 rue des Farges, Lyon »). Tweak `openSuggestions` : ouvre le dropdown par défaut pour visualiser l'autocomplétion. Ouvrir dans un navigateur.
- `Recherche - réflexion.dc.html` — le **document de conception** (parti pris, table des types de requête, anatomie de la barre, autocomplétion, page de résultats, décisions tranchées). Contexte du « pourquoi ».
- `Fiche établissement.dc.html` — référence de style la plus complète du design system (source de vérité visuelle : notation, brevet, valeur ajoutée, dispositifs, IPS/mixité).
- `support.js`, `image-slot.js` — runtime des prototypes (non porté ; nécessaire seulement pour ouvrir les `.dc.html`).

> Repo cible : `agent-ecoles/web` (Next.js + TS + Tailwind). Indicateurs par établissement déjà dispo (notation, réussite brevet, dispositifs, langues). Dépendances back à prévoir : **index de recherche** (établissements + communes + UAI + CP) avec correspondance floue ; **géocodage d'adresse** → collèges les plus proches (tri distance).
