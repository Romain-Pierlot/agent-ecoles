// Formatage des nombres en français (virgule décimale) — centralisé ici pour
// éviter que chaque composant refasse son propre toFixed().replace(".", ",")
// (cf. web/src/components/SousDivisionsTable.tsx et page.tsx qui dupliquaient
// exactement la même fonction avant factorisation).

export function formaterDecimale(valeur: number, decimales = 1): string {
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(valeur);
}

// Espace insécable avant le % (typographie française), pas un espace normal
// qui pourrait laisser le "%" seul en fin de ligne.
export function formaterPourcentage(valeur: number, decimales = 0): string {
  return `${formaterDecimale(valeur, decimales)} %`;
}

export function formaterTaux(taux: number | null): string {
  return taux === null ? "—" : formaterPourcentage(taux, 0);
}

// Écart signé (valeur ajoutée vs attendu) : signe toujours affiché, vrai
// signe moins (U+2212, pas le trait d'union U+002D que produit
// Intl.NumberFormat par défaut) — convention typographique distincte d'un
// simple nombre, cf. docs/Design_system (colonne "Écart à l'attendu").
export function formaterEcart(valeur: number, decimales = 1): string {
  const signe = valeur < 0 ? "−" : "+";
  return `${signe}${formaterDecimale(Math.abs(valeur), decimales)}`;
}

// Accord singulier/pluriel d'un compteur : seul 1 prend le singulier (0
// compris, comme en français) — centralisé pour éviter qu'un ternaire
// `n > 1 ? "s" : ""` soit recopié à chaque affichage d'un compteur
// (collèges, communes, départements, candidats...).
export function accorder(n: number, singulier: string, pluriel: string = `${singulier}s`): string {
  return n === 1 ? singulier : pluriel;
}
