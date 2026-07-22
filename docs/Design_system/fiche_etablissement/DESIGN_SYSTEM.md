# Design System « écoles »

> Principe fondateur : **une couleur = un rôle, jamais une décoration.**
> On ne code jamais un hex « en dur » sur une donnée — on lui applique le token qui porte son sens.

## 1. Les 3 couches
1. **Palette brute** — les hex physiques. Jamais nommés dans le code produit.
2. **Tokens sémantiques** — le rôle donné à chaque teinte. C'est ce qu'on manipule.
3. **Règle par indicateur** — la logique « valeur → sens » qui choisit le token.

## 2. Tokens sémantiques

| Token | Hex (foncé) | Rôle | Interdit |
|---|---|---|---|
| `action` | `#D9457A` (`#A82C58`) | Produit & action : logo, CTA, assistant, liens, intitulés de section | Ne qualifie jamais une donnée |
| `positif` | `#2E8F5E` (→ `#9BCBAF`) | Résultat favorable : réussite, valeur ajoutée +, note A | — |
| `descriptif` | `#3A5A8C` | Indicateur positionnel : IPS, mixité (« on situe, on ne juge pas ») | Pas de connotation bon/mauvais |
| `attention` | `#F0A02E` (`#B0741A`) | Point de vigilance sur une donnée : résultat sous la moyenne, note B | Jamais un bouton |
| `accent` | `#C15A3C` | Accent rare + notes manuscrites (Caveat) | À doser |
| neutres | `#F1E7D6` `#FCF4E9` `#fff` / `#8A7B64` / `#223B30` | Fonds / repères / texte | — |

## 3. Tableau des seuils (choix éditorial, modifiable)

| Indicateur | Règle | Token |
|---|---|---|
| IPS | toujours → `descriptif` (positionnel) | `descriptif` |
| Mixité sociale | toujours → `descriptif` (choix assumé : on ne hiérarchise pas les profils sociaux) | `descriptif` |
| Réussite brevet | `>= 89` → `positif` · sinon `attention` | `positif` |
| Valeur ajoutée | `> 0` → `positif` · `= 0` → `descriptif` · `< 0` → `attention` | `positif` |
| Note écoles | `A+/A/A-` → `positif` · `B+/B` → `attention` | `positif` |

## 4. La fonction (point d'entrée unique)

```js
function sentiment(indicator, value) {
  const rules = {
    ips:       v => 'descriptif',      // positionnel, jamais un jugement
    mixite:    v => 'descriptif',      // choix éditorial assumé
    reussite:  v => v >= 89 ? 'positif' : 'attention',
    valeurAj:  v => v > 0 ? 'positif' : v < 0 ? 'attention' : 'descriptif',
    note:      v => /^A/.test(v) ? 'positif' : 'attention',
  };
  const level = rules[indicator](value);
  return {
    action:     '#D9457A',   // produit & CTA
    positif:    '#2E8F5E',   // résultat favorable
    descriptif: '#3A5A8C',   // indicateur positionnel
    attention:  '#F0A02E',   // point de vigilance
  }[level];
}
```

Le gabarit n'écrit jamais une couleur : il appelle `sentiment('ips', 112)` et reçoit le bon token. Ajouter un indicateur = ajouter une ligne dans `rules`.

En cible, exposer plutôt les tokens en variables CSS (`--color-positif`, etc.) et faire renvoyer à `sentiment()` le **nom du token**, pas le hex, pour rester thémable.

## 5. Typographie
- **Baloo 2** — titres & chiffres (700-800). Rondeur chaleureuse.
- **Figtree** — texte courant (400 pour lire, 600-700 pour souligner).
- **Caveat** — notes manuscrites, en terracotta. Aide de lecture, jamais info critique.
- **JetBrains Mono** — valeurs techniques / URL.

Repères d'échelle : grands chiffres 34-40px, titres de section 25-26px, corps 12.5-14px, libellés secondaires 10-11px.

## 6. Formes
- Cartes : rayon 18-26px, souvent **asymétrique** (`26px 22px 26px 24px`) pour le côté fait-main.
- Bordures : `2px solid #EFE1CE`. Filets internes `1px dashed #EAD9BF`.
- Légères rotations (`rotate(-1deg)`) sur badges/pastilles pour le grain humain.

## 7. Cinq règles anti-« sapin de Noël »
1. **Une couleur = un rôle.** Si tu hésites sur la teinte, le sens n'est pas clair — règle le sens d'abord.
2. **Jamais de hex en dur sur une donnée.** Toujours passer par `sentiment()`.
3. **Descriptif ≠ jugement.** IPS et mixité en bleu : on situe, on ne note pas.
4. **L'action ne qualifie pas, la donnée ne clique pas.** Framboise pour agir ; vert/bleu/ambre pour informer.
5. **Nuancer par l'intensité, pas par la teinte.** Trois bons résultats = trois verts, pas vert/orange/rouge.
