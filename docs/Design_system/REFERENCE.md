# Référence design — identité terracotta

Ce document décrit les règles du design actuel du site (`web/`), pour que
toute nouvelle page ou tout nouveau composant reste cohérent sans avoir à
redécouvrir ces règles à chaque fois. Mis à jour le 2026-07-25, à la fin de
la refonte terracotta.

## 0. Principe transverse — le nom de l'agent est provisoire

L'agent conversationnel du site n'a pas de nom définitif : le nom actuel
est une donnée de configuration (`NOM_ASSISTANT`, `web/src/lib/constants.ts`),
pas une identité figée. **Ne jamais coder en dur le nom actuel de l'agent**
— ni dans un identifiant de code (composant, variable, token CSS), ni dans
un texte affiché en dehors de `NOM_ASSISTANT`, ni dans cette documentation.
Utiliser un terme générique (« l'agent », « l'assistant ») partout ailleurs.
Les tokens `agent*` (section 2) et le composant `GaletAgent.tsx` respectent
déjà cette règle — si un nouvel élément visuel dédié à l'agent est ajouté,
le nommer sur ce même principe, jamais d'après le nom courant.

## 1. Source de vérité

La référence visuelle de travail (maquette interactive, tours de décision
sur les couleurs, l'identité de l'agent, la recherche, la fiche
établissement, la carte scolaire, l'accueil) est conservée en dehors du
dépôt.

**Règle** : avant de se fier à une maquette ou un ancien document de
référence, vérifier que ses couleurs/polices correspondent aux tokens
actuels (section 2). Une référence dont les couleurs ne matchent pas
`globals.css` est périmée — ne pas s'y fier même si son nom semble à jour.
C'est exactement l'erreur commise pendant cette refonte avec un ancien
bundle jamais mis à jour (archivé depuis dans `docs/Design_system/archive/`).

## 2. Tokens couleur

Les valeurs vivent dans `web/src/app/globals.css` (bloc `@theme inline`) —
ce tableau documente le *rôle* de chaque token, pas sa valeur hex (qui
peut changer à la prochaine refonte de palette sans que ce document ait
besoin d'être réécrit).

| Token | Rôle |
|---|---|
| `action` / `action-dark` / `action-pale` | Produit & action : CTA, liens, logo. Ne qualifie jamais une donnée. |
| `positif` / `positif-pale` | Résultat favorable (réussite au-dessus du national, VA positive, note A). |
| `descriptif` / `descriptif-pale` | Indicateur positionnel (IPS, mixité sociale) — on situe, on ne juge pas. |
| `attention` / `attention-dark` / `attention-pale` | Point de vigilance sur une donnée. Jamais un bouton. |
| `statut-public` / `-pale`, `statut-prive` / `-pale` | Statut Public/Privé d'un établissement — décrit un type, pas un jugement. |
| `badge-prioritaire` / `-pale` | REP / REP+. |
| `badge-inclusion` / `-pale` | ULIS / SEGPA. |
| `badge-langue` / `-pale` | Section internationale / européenne. |
| `badge-option` / `-pale` | Sections sport / arts / cinéma / théâtre. Repli par défaut de `classeBadgeDispositif()`. |
| `distance` / `-pale` | Distance depuis une adresse (carte scolaire). Neutre — ne doit jamais se confondre avec un statut. |
| `agent` / `-dark` / `-pale` / `-ink` | Identité dédiée à l'agent conversationnel. N'apparaît nulle part ailleurs — jamais `action` pour un élément qui représente l'agent. |
| `notation-a-plus` … `notation-b`, `mention-tb` … `mention-sans` | Pastille de notation (via `NOTATION_GRADIENTS`, `CarteCollege.tsx`) et donut des mentions au brevet. Valeurs volontairement inchangées depuis avant la refonte. |
| `fond-creme` / `fond-sable` / `fond-carte`, `texte` / `texte-doux`, `filet` / `filet-fonce` | Fonds, texte, bordures génériques. |

**Fonctions à utiliser plutôt que du hex en dur** (`web/src/lib/tokens.ts`) :
`sentimentNote()`, `sentimentBadgeVa()`, `sentimentReussite()`,
`sentimentDescriptif()`, `classeStatutSecteur()`, `classeBadgeDispositif()`.

**Règle absolue : jamais de couleur hex codée en dur dans un composant**
(ni dans une `className`, ni dans un `style` inline, ni dans un SVG). Cette
refonte a buté trois fois sur le même défaut : une ombre CSS
(`shadow-[...rgba(217,69,122,...)]`) contenant l'ancienne couleur en dur,
invisible tant qu'on ne cherche pas spécifiquement une couleur — jamais
détecté en relisant le composant, seulement en `grep`-ant tout le code.

**Garde-fou en place depuis le 2026-07-25** : `web/eslint.config.mjs`
bloque toute couleur hex en dur dans `src/**/*.{ts,tsx}` (`no-restricted-syntax`,
niveau `error`). Les rares registres légitimes qui ont besoin de hex brut
pour un dégradé dynamique (`NOTATION_GRADIENTS`, `COULEURS_MENTIONS`, les
couleurs propres au `GaletAgent`) sont désactivés ligne par ligne avec un
commentaire de justification — jamais un fichier entier exempté en bloc.

## 3. Typographie

Trois rôles, jamais un nom de police directement :

| Classe | Police | Usage |
|---|---|---|
| `font-titre` | Newsreader (sérif éditorial) | Titres, noms de collège/commune, titres de section |
| `font-ui` | Hanken Grotesk | Corps, UI, **tous les chiffres** (taux, VA, IPS, compteurs...) |
| `font-notation` | Schibsted Grotesk | La lettre de notation (A+ → B) **uniquement** |
| `font-mono` | Monospace système (Tailwind, pas de police chargée) | Identifiants type UAI |

Aucun texte ne doit rester sans rôle explicite quand il s'écarte du corps
de page par défaut (`font-ui`, hérité de `body`).

## 4. Anatomie des composants récurrents

### Carte résultat (`CarteCollege.tsx`, `CarteCollegeSecteur.tsx`)
Toute carte qui représente un établissement dans une liste suit le même
patron :
- **Toute la carte est un seul `<Link>` cliquable** — jamais de bouton CTA
  séparé à l'intérieur.
- Bloc de gauche (`flex-1 min-w-0`) : nom en `font-titre`, puis **une seule
  ligne** qui regroupe commune/département, badge statut Public/Privé, et
  badges dispositifs — jamais deux lignes séparées (texte à gauche, tout le
  reste empilé à droite).
- Bloc de droite, **dans cet ordre fixe, jamais l'inverse** : badge distance
  (si applicable) ou taux de réussite, *puis* pastille de notation carrée
  (dégradé `NOTATION_GRADIENTS`, `font-notation`, sans légende "notation"
  en dessous), *puis* chevron `›`. Défaut trouvé dans `CarteCollege.tsx` le
  2026-07-25 (notation placée avant la distance, contrairement à
  `CarteCollegeSecteur.tsx` qui suivait déjà le bon ordre) : invisible à la
  relecture du code, seule la comparaison avec `CarteCollegeSecteur.tsx`
  l'a révélé. Corrigé dans la même session.
- `CarteCollegeSecteur` reprend exactement cette anatomie ; seuls le fond
  dégradé, la bordure et le badge ★ au-dessus du nom la distinguent.

### Bloc agent (`AgentBlock.tsx`)
- Toujours les tokens `agent*`, jamais `action`.
- Icône = `GaletAgent` (composant partagé), jamais un rond avec une
  lettre.
- Carte bordée à fond pâle (`border-agent bg-gradient-to-br
  from-agent-pale to-fond-carte`), jamais de fond plein.
- Un seul composant pour tout le site — si un écran a besoin d'un bloc pour
  l'agent, réutiliser `AgentBlock`, ne pas en dupliquer un nouveau à la main
  (c'est cette duplication qui avait fait dériver la fiche établissement).

### Ligne de tableau (`SousDivisionsTable.tsx`)
Texte aligné à gauche, indicateurs chiffrés (`font-ui`) alignés à droite,
chevron en bout de ligne.

## 5. Checklist — nouvelle page ou nouveau composant

Avant de considérer une page conforme au thème :
1. Aucune couleur hex en dur — le lint (section 2) doit passer sans
   exception nouvelle non justifiée.
2. Chaque texte a le bon rôle de police (section 3).
3. Si la page affiche des cartes résultat, un bloc agent ou un tableau,
   son anatomie suit un patron existant (section 4) plutôt que d'en
   improviser un nouveau.
4. Si une maquette de référence existe pour cette page, comparer une
   capture d'écran réelle à la maquette — pas seulement relire le code.
   C'est la seule méthode qui a permis de détecter l'écart structurel sur
   `CarteCollegeSecteur` : le code semblait correct à la lecture, la
   structure entière du composant divergeait pourtant de la référence.

## 6. Dette connue (au 2026-07-25)

Non vérifié ou non aligné, pour ne pas supposer à tort qu'une zone est
conforme :
- `FiltresEtListeColleges` (page `/recherche`) : structure non comparée à
  la maquette (le composant lui-même ne contient ni carte ni couleur ni
  police propre — il délègue entièrement l'affichage à `ListeColleges` →
  `CarteCollege`, déjà conforme — donc risque faible, mais pas vérifié
  formellement).

**Vérifié pendant cette session, pas de la dette** : `/explorer` réutilise
directement `region/page.tsx` (déjà couvert par la refonte) — ce n'est pas
une page distincte. `/comprendre/*`, `/academie/*`, `/calendrier`,
`/a-propos`, `/methodologie`, `/mentions-legales`, `/sources` sont des
squelettes de route (`PagePlaceholder.tsx`, non conçus visuellement, hors
sujet pour cette refonte tant qu'ils ne le sont pas). `/assistant` ne
contenait déjà aucun résidu de police ni de couleur en dur. Les tokens
`agent*` et `GaletAgent.tsx` (section 0) ne dérogent plus au principe du
nom provisoire — renommés le 2026-07-25.
