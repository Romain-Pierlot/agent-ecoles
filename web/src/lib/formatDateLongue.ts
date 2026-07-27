const JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
const MOIS = [
  "janvier", "février", "mars", "avril", "mai", "juin",
  "juillet", "août", "septembre", "octobre", "novembre", "décembre",
];

export type DateDecomposee = { jourSemaine: string; jour: number; mois: string; annee: number };

// Décompose une date ISO (YYYY-MM-DD) pour un format long type "samedi 17
// octobre 2026" — cf. web/src/app/calendrier-scolaire/_components/DateLongue.tsx
// pour la mise en forme (capitalisation, "1ᵉʳ" en exposant), qui dépend du
// contexte d'affichage (jalon isolé vs "Du ... au ...").
export function decomposerDate(iso: string): DateDecomposee {
  const [anneeStr, moisStr, jourStr] = iso.split("-");
  const date = new Date(Number(anneeStr), Number(moisStr) - 1, Number(jourStr));
  return {
    jourSemaine: JOURS[date.getDay()],
    jour: Number(jourStr),
    mois: MOIS[Number(moisStr) - 1],
    annee: Number(anneeStr),
  };
}

// Format court "17 oct." pour le tableau outre-mer (une cellule liste
// jusqu'à 6 périodes, le format long "Du samedi ... au lundi ..." y serait
// illisible). Même logique que formaterDate() dans FicheIdentite.tsx —
// dupliquée ici plutôt que factorisée : ce fichier est en cours de
// modification indépendante au moment où cette page est écrite.
export function formaterDateCourte(iso: string): string {
  const [annee, mois, jour] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" }).format(new Date(annee, mois - 1, jour));
}

// Format "18 juin 2026" (jour + mois en toutes lettres + année, sans jour de
// semaine) — utilisé par la section Comprendre ("Publié le ...", dates de
// relevé des sources), plus sobre que le format long à jour de semaine.
export function formaterDateJourMoisAnnee(iso: string): string {
  const [annee, mois, jour] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric" }).format(
    new Date(annee, mois - 1, jour)
  );
}
