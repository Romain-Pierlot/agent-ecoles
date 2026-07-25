// Remplacement de src/lib/tokens.ts
// Les fonctions sentiment*() et classeStatutSecteur() sont INCHANGÉES
// (mêmes noms de tokens sémantiques renvoyés — seules leurs valeurs bougent
// dans globals.css). AJOUT : classeBadgeDispositif(), qui colore chaque
// badge dispositif/section par famille au lieu du gris uniforme d'avant.

export type TokenSemantique = "action" | "positif" | "descriptif" | "attention";

export function sentimentNote(notation: string): TokenSemantique {
  return /^A/.test(notation) ? "positif" : "attention";
}

export function sentimentBadgeVa(badgeVa: string | null): TokenSemantique {
  if (badgeVa === "positif") return "positif";
  if (badgeVa === "negatif") return "attention";
  return "descriptif";
}

export function sentimentReussite(taux: number, tauxNational: number): TokenSemantique {
  return taux >= tauxNational ? "positif" : "attention";
}

export function sentimentDescriptif(): TokenSemantique {
  return "descriptif";
}

export function classeStatutSecteur(secteur: string): string {
  return secteur === "Public"
    ? "bg-statut-public-pale text-statut-public"
    : "bg-statut-prive-pale text-statut-prive";
}

// NOUVEAU — couleur de badge par famille de dispositif/section.
// Entrée = libellé produit par deriveBadgesDispositifs() (lib/dispositifs.ts) :
//   "Public"/"Privé" ne passent PAS ici (rendus via classeStatutSecteur),
//   "REP"/"REP+", "ULIS", "SEGPA", "Section sportive", "Section arts",
//   "Section cinéma", "Section théâtre", "Section internationale",
//   "Section européenne".
// Classes Tailwind écrites en toutes lettres (littéraux scannés à la
// compilation — jamais interpolées). « une couleur = un rôle ».
const CLASSE_BADGE_INCLUSION = "bg-badge-inclusion-pale text-badge-inclusion";
const CLASSE_BADGE_PRIORITAIRE = "bg-badge-prioritaire-pale text-badge-prioritaire";
const CLASSE_BADGE_LANGUE = "bg-badge-langue-pale text-badge-langue";
const CLASSE_BADGE_OPTION = "bg-badge-option-pale text-badge-option";

export function classeBadgeDispositif(label: string): string {
  if (label === "ULIS" || label === "SEGPA") return CLASSE_BADGE_INCLUSION;
  if (/^REP/.test(label)) return CLASSE_BADGE_PRIORITAIRE;
  if (label === "Section internationale" || label === "Section européenne") return CLASSE_BADGE_LANGUE;
  if (label.startsWith("Section")) return CLASSE_BADGE_OPTION;
  return CLASSE_BADGE_OPTION; // repli
}
