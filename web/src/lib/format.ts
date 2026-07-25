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
