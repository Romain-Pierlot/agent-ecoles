// Première implémentation réelle de la fonction sentiment() documentée dans
// docs/Design_system/fiche_etablissement/DESIGN_SYSTEM.md
// (jusqu'ici du pseudo-code JS dans la doc, jamais implémenté). Un gabarit
// n'écrit jamais une couleur en dur sur une donnée : il appelle une de ces
// fonctions et reçoit le nom du token sémantique à utiliser.

export type TokenSemantique = "action" | "positif" | "descriptif" | "attention";

export function sentimentNote(notation: string): TokenSemantique {
  return /^A/.test(notation) ? "positif" : "attention";
}

// Le badge_va est déjà calculé et catégorisé côté backend (config.VA_SEUIL_*)
// — on mappe la catégorie existante, on ne recalcule jamais un seuil ici.
export function sentimentBadgeVa(badgeVa: string | null): TokenSemantique {
  if (badgeVa === "positif") return "positif";
  if (badgeVa === "negatif") return "attention";
  return "descriptif";
}

// Écart volontaire par rapport au seuil générique codé en dur (>= 89) de
// DESIGN_SYSTEM.md : on compare à la vraie moyenne nationale de la session
// affichée (désormais disponible via l'API), pour ne jamais devenir obsolète
// au fil des années.
export function sentimentReussite(taux: number, tauxNational: number): TokenSemantique {
  return taux >= tauxNational ? "positif" : "attention";
}

// IPS et mixité sociale : toujours descriptif, jamais un jugement — règle 3
// du design system ("on situe, on ne juge pas").
export function sentimentDescriptif(): TokenSemantique {
  return "descriptif";
}
