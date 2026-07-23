// Filtres/tri de la page /recherche — codec partagé entre le rendu serveur
// (page.tsx, lit l'URL au premier chargement) et le fetch client
// (ResultatsRecherche, réécrit l'URL et rappelle l'API à chaque changement
// de filtre). Une seule définition des valeurs valides des deux côtés,
// miroir des Literal de api/main.py.

export type SecteurFiltre = "Public" | "Privé";
export type DispositifFiltre = "REP" | "REP+" | "ULIS" | "SEGPA";
export type SectionFiltre = "sport" | "arts" | "cinema" | "theatre" | "internationale" | "europeenne";
export type NotationFiltre = "A+" | "A" | "A-" | "B+" | "B";
export type TriEtablissements = "notation" | "reussite" | "alphabetique";
export type TriCommunes = "alphabetique" | "reussite" | "nb_etablissements";
export type Direction = "asc" | "desc";

export type FiltresEtablissements = {
  secteur: SecteurFiltre | null;
  dispositif: DispositifFiltre | null;
  section: SectionFiltre | null;
  notationMin: NotationFiltre | null;
  tri: TriEtablissements;
  direction: Direction;
};

export type FiltresCommunes = {
  triCommunes: TriCommunes;
  directionCommunes: Direction;
};

export type FiltresRecherche = FiltresEtablissements & FiltresCommunes;

export const FILTRES_PAR_DEFAUT: FiltresRecherche = {
  secteur: null,
  dispositif: null,
  section: null,
  notationMin: null,
  tri: "notation",
  direction: "desc",
  triCommunes: "alphabetique",
  directionCommunes: "asc",
};

const SECTEURS_VALIDES: readonly SecteurFiltre[] = ["Public", "Privé"];
const DISPOSITIFS_VALIDES: readonly DispositifFiltre[] = ["REP", "REP+", "ULIS", "SEGPA"];
const SECTIONS_VALIDES: readonly SectionFiltre[] = [
  "sport", "arts", "cinema", "theatre", "internationale", "europeenne",
];
const NOTATIONS_VALIDES: readonly NotationFiltre[] = ["A+", "A", "A-", "B+", "B"];
const TRIS_ETABLISSEMENTS_VALIDES: readonly TriEtablissements[] = ["notation", "reussite", "alphabetique"];
const TRIS_COMMUNES_VALIDES: readonly TriCommunes[] = ["alphabetique", "reussite", "nb_etablissements"];
const DIRECTIONS_VALIDES: readonly Direction[] = ["asc", "desc"];

function valeurOuNull<T extends string>(valides: readonly T[], brut: string | undefined): T | null {
  return (valides as readonly string[]).includes(brut ?? "") ? (brut as T) : null;
}

function valeurOuDefaut<T extends string>(valides: readonly T[], brut: string | undefined, defaut: T): T {
  return (valides as readonly string[]).includes(brut ?? "") ? (brut as T) : defaut;
}

// `get` abstrait la source (searchParams serveur Next.js déjà résolu en
// Record<string,string>, ou URLSearchParams côté client) — une valeur
// absente ou hors liste blanche retombe silencieusement sur son défaut,
// jamais une valeur non vérifiée transmise telle quelle à l'API.
export function lireFiltres(get: (cle: string) => string | undefined): FiltresRecherche {
  return {
    secteur: valeurOuNull(SECTEURS_VALIDES, get("secteur")),
    dispositif: valeurOuNull(DISPOSITIFS_VALIDES, get("dispositif")),
    section: valeurOuNull(SECTIONS_VALIDES, get("section")),
    notationMin: valeurOuNull(NOTATIONS_VALIDES, get("notation_min")),
    tri: valeurOuDefaut(TRIS_ETABLISSEMENTS_VALIDES, get("tri"), FILTRES_PAR_DEFAUT.tri),
    direction: valeurOuDefaut(DIRECTIONS_VALIDES, get("direction"), FILTRES_PAR_DEFAUT.direction),
    triCommunes: valeurOuDefaut(TRIS_COMMUNES_VALIDES, get("tri_communes"), FILTRES_PAR_DEFAUT.triCommunes),
    directionCommunes: valeurOuDefaut(
      DIRECTIONS_VALIDES, get("direction_communes"), FILTRES_PAR_DEFAUT.directionCommunes
    ),
  };
}

// Construit les query params HTTP (mêmes noms que GET /recherche, cf.
// api/main.py) à partir des filtres — omet les valeurs par défaut pour
// garder les URL courtes et rester compatible avec les liens ?q=... déjà
// existants (partagés avant l'introduction des filtres).
export function construireParams(query: string, filtres: FiltresRecherche): URLSearchParams {
  const params = new URLSearchParams();
  params.set("q", query);
  if (filtres.secteur) params.set("secteur", filtres.secteur);
  if (filtres.dispositif) params.set("dispositif", filtres.dispositif);
  if (filtres.section) params.set("section", filtres.section);
  if (filtres.notationMin) params.set("notation_min", filtres.notationMin);
  if (filtres.tri !== FILTRES_PAR_DEFAUT.tri) params.set("tri", filtres.tri);
  if (filtres.direction !== FILTRES_PAR_DEFAUT.direction) params.set("direction", filtres.direction);
  if (filtres.triCommunes !== FILTRES_PAR_DEFAUT.triCommunes) params.set("tri_communes", filtres.triCommunes);
  if (filtres.directionCommunes !== FILTRES_PAR_DEFAUT.directionCommunes) {
    params.set("direction_communes", filtres.directionCommunes);
  }
  return params;
}

// Un filtre établissement actif (secteur/dispositif/section/notation_min)
// peut réduire le compte à 0 : utilisé pour garder la barre de filtres
// visible (avec son propre message "aucun résultat") même quand le lot
// filtré est vide — le tri seul (tri/direction) ne réduit jamais le
// compte, pas besoin de le vérifier ici.
export function filtresEtablissementsActifs(filtres: FiltresRecherche): boolean {
  return (
    filtres.secteur !== null ||
    filtres.dispositif !== null ||
    filtres.section !== null ||
    filtres.notationMin !== null
  );
}

export function filtresActifs(filtres: FiltresRecherche): boolean {
  return JSON.stringify(filtres) !== JSON.stringify(FILTRES_PAR_DEFAUT);
}
