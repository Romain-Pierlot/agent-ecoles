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
