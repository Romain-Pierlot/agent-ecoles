// Miroir TypeScript des modèles Pydantic de api/schemas.py (FicheEtablissement
// et sous-types) — GET /etablissement/{uai}.

export type EtablissementIdentite = {
  uai: string;
  nom: string;
  type_etablissement: string;
  secteur: string;
  adresse: string | null;
  code_postal: string | null;
  commune: string;
  code_departement: string | null;
  libelle_departement: string | null;
  code_academie: string | null;
  libelle_academie: string | null;
  libelle_region: string | null;
  telephone: string | null;
  mail: string | null;
  web: string | null;
  date_ouverture: string | null;
  notation: string | null;
  badge_va: string | null;
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

export type MentionDetail = {
  libelle: string;
  nb_eleves: number | null;
  taux_pct: number | null;
};

export type BrevetResultats = {
  session: string;
  brevet_nb_candidats_general: number | null;
  brevet_taux_reussite_general: number | null;
  brevet_note_ecrit_general: number | null;
  taux_acces_6eme_3eme: number | null;
  taux_reussite_national: number | null;
  taux_reussite_departemental: number | null;
  note_ecrit_national: number | null;
  note_ecrit_departemental: number | null;
  mentions: MentionDetail[];
};

export type ValeurAjouteeDetail = {
  va_taux: number | null;
  taux_observe: number | null;
  taux_attendu: number | null;
  va_note: number | null;
  note_observee: number | null;
  note_attendue: number | null;
};

export type EvolutionPoint = {
  session: string;
  brevet_taux_reussite_general: number | null;
  brevet_note_ecrit_general: number | null;
  notation: string | null;
  badge_va: string | null;
};

export type PositionnementSocial = {
  annee_scolaire: string;
  ips_moyen: number | null;
  ecart_type_ips: number | null;
  ips_national: number | null;
  ips_academique: number | null;
  ips_departemental: number | null;
  ecart_type_ips_national: number | null;
  ecart_type_ips_departemental: number | null;
};

export type LanguesOffertes = {
  lv1: string[];
  lv2: string[];
  lca: string[];
};

export type ProchainesVacances = {
  zone: string;
  periode: string;
  date_debut: string;
  date_fin: string | null;
};

export type FicheEtablissement = {
  identite: EtablissementIdentite;
  brevet: BrevetResultats | null;
  valeur_ajoutee: ValeurAjouteeDetail | null;
  evolution: EvolutionPoint[];
  positionnement_social: PositionnementSocial | null;
  langues: LanguesOffertes | null;
  sections_sportives: string[];
  zone_vacances: string | null;
  prochaines_vacances: ProchainesVacances | null;
};
