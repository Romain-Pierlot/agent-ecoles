// Dérive la liste des badges dispositifs/sections à partir des colonnes
// booléennes communes à EtablissementIdentite (fiche établissement) et
// CollegeVille (carte résultat de la page ville) — factorisé ici pour
// n'avoir qu'un seul endroit à mettre à jour si un nouveau dispositif doit
// être reconnu (cf. principe de factorisation, CLAUDE.md).

export type EntiteAvecDispositifs = {
  appartenance_education_prioritaire: string | null;
  ulis: boolean;
  segpa: boolean;
  section_arts: boolean;
  section_cinema: boolean;
  section_theatre: boolean;
  section_sport: boolean;
  section_internationale: boolean;
  section_europeenne: boolean;
};

const SECTIONS: { cle: keyof EntiteAvecDispositifs; label: string }[] = [
  { cle: "section_sport", label: "Section sportive" },
  { cle: "section_arts", label: "Section arts" },
  { cle: "section_cinema", label: "Section cinéma" },
  { cle: "section_theatre", label: "Section théâtre" },
  { cle: "section_internationale", label: "Section internationale" },
  { cle: "section_europeenne", label: "Section européenne" },
];

// Dispositifs éducatifs (REP/REP+, ULIS, SEGPA) — distincts des sections pour
// le filtre "Dispositifs" de la page ville, séparé du filtre "Sections".
export function deriveDispositifsEducatifs(entite: EntiteAvecDispositifs): string[] {
  const dispositifs: string[] = [];
  if (entite.appartenance_education_prioritaire) dispositifs.push(entite.appartenance_education_prioritaire);
  if (entite.ulis) dispositifs.push("ULIS");
  if (entite.segpa) dispositifs.push("SEGPA");
  return dispositifs;
}

export function deriveSections(entite: EntiteAvecDispositifs): string[] {
  return SECTIONS.filter((s) => entite[s.cle]).map((s) => s.label);
}

export function deriveBadgesDispositifs(entite: EntiteAvecDispositifs): string[] {
  return [...deriveDispositifsEducatifs(entite), ...deriveSections(entite)];
}

// Clé attendue par GET /recherche (config.SectionSouhaitee côté back) pour
// chaque section — distincte de `cle` ci-dessus (nom de colonne). Dérivée de
// SECTIONS (même source que les libellés) : ajouter une section ne demande
// toujours qu'un seul endroit à mettre à jour. Utilisé uniquement par
// FiltresEtListeColleges en mode serveur (page /recherche) pour traduire le
// libellé sélectionné dans le menu vers le paramètre attendu par l'API.
const CLE_COLONNE_VERS_CLE_API: Record<string, string> = {
  section_sport: "sport",
  section_arts: "arts",
  section_cinema: "cinema",
  section_theatre: "theatre",
  section_internationale: "internationale",
  section_europeenne: "europeenne",
};

export const SECTION_VERS_CLE_API: Record<string, string> = Object.fromEntries(
  SECTIONS.map((s) => [s.label, CLE_COLONNE_VERS_CLE_API[s.cle]])
);

export const CLE_API_VERS_SECTION: Record<string, string> = Object.fromEntries(
  Object.entries(SECTION_VERS_CLE_API).map(([label, cle]) => [cle, label])
);
