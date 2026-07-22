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

export function deriveBadgesDispositifs(entite: EntiteAvecDispositifs): string[] {
  const badges: string[] = [];
  if (entite.appartenance_education_prioritaire) badges.push(entite.appartenance_education_prioritaire);
  if (entite.ulis) badges.push("ULIS");
  if (entite.segpa) badges.push("SEGPA");
  for (const s of SECTIONS) {
    if (entite[s.cle]) badges.push(s.label);
  }
  return badges;
}
