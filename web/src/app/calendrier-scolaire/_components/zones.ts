import type { AcademieZone, PeriodeVacances } from "@/lib/types";

export type Zone = "A" | "B" | "C" | "Corse";
export const ZONES: Zone[] = ["A", "B", "C", "Corse"];

export const LABEL_ZONE: Record<Zone, string> = { A: "Zone A", B: "Zone B", C: "Zone C", Corse: "Corse" };

// Teintes Tailwind par zone. "Pleine" pour A/B/Corse réutilise des tokens
// déjà existants dans le thème (mêmes valeurs hex que la maquette) — seule
// Zone C est une teinte inédite. En-tête/pâle : tokens ajoutés à
// globals.css, aucun équivalent existant (cf. conception validée).
export const TEINTE_ZONE: Record<Zone, { pleine: string; pleineTexte: string; entete: string; pale: string; bordurePleine: string }> = {
  A: { pleine: "bg-action", pleineTexte: "text-action", entete: "bg-zone-a-entete", pale: "bg-zone-a-pale", bordurePleine: "border-action" },
  B: { pleine: "bg-descriptif", pleineTexte: "text-descriptif", entete: "bg-zone-b-entete", pale: "bg-zone-b-pale", bordurePleine: "border-descriptif" },
  C: { pleine: "bg-zone-c", pleineTexte: "text-zone-c", entete: "bg-zone-c-entete", pale: "bg-zone-c-pale", bordurePleine: "border-zone-c" },
  Corse: { pleine: "bg-statut-public", pleineTexte: "text-statut-public", entete: "bg-zone-corse-entete", pale: "bg-zone-corse-pale", bordurePleine: "border-statut-public" },
};

// Les 6 lignes affichées dans le tableau métropole — periodeSource est le
// libellé brut stocké en base (data/vacances_scolaires_2026_2027.csv), le
// mapping vers le libellé affiché n'est pas 1:1 : "Fin d'année scolaire"
// (jalon technique) devient "Vacances d'été" à l'affichage (c'est la date à
// laquelle les vacances d'été commencent), et "Prérentrée" n'apparaît pas
// dans le tableau (non demandée par la maquette).
export const LIGNES_METROPOLE: { libelle: string; periodeSource: string }[] = [
  { libelle: "Rentrée des élèves", periodeSource: "Rentrée" },
  { libelle: "Vacances de la Toussaint", periodeSource: "Toussaint" },
  { libelle: "Vacances de Noël", periodeSource: "Noël" },
  { libelle: "Vacances d'hiver", periodeSource: "Hiver" },
  { libelle: "Vacances de printemps", periodeSource: "Printemps" },
  { libelle: "Vacances d'été", periodeSource: "Fin d'année scolaire" },
];

export type ResolutionZone = { ligne: PeriodeVacances; deToutes: boolean };

// Pour une période donnée, la date d'une zone est soit une ligne spécifique
// à cette zone, soit (à défaut) la ligne commune "TOUTES". `deToutes`
// indique laquelle des deux, ce qui sert ensuite à décider la fusion visuelle
// des cellules (cf. FUSION_METROPOLE ci-dessous) : la fusion suit la source
// des données, pas une comparaison de dates qui se prêterait à des
// coïncidences (Zone A et Corse ont les mêmes dates en hiver/printemps sans
// que la maquette les fusionne, cf. README).
export function resoudreZone(periodeSource: string, zone: Zone, metropole: PeriodeVacances[]): ResolutionZone | null {
  const specifique = metropole.find((l) => l.periode === periodeSource && l.zone === zone);
  if (specifique) return { ligne: specifique, deToutes: false };
  const commune = metropole.find((l) => l.periode === periodeSource && l.zone === "TOUTES");
  return commune ? { ligne: commune, deToutes: true } : null;
}

export const SUFFIXE_TOKEN_ZONE: Record<Zone, string> = { A: "a", B: "b", C: "c", Corse: "corse" };

// Regroupe les zones dont la date (debut+fin) est strictement identique —
// utilisé côté mobile (cf. CartesMetropoleMobile.tsx) où le regroupement se
// fait par valeur (contrairement au tableau desktop, où la fusion suit la
// source des données à cause de la contrainte d'adjacence des colonnes).
export function grouperZonesParDate(
  resolutions: { zone: Zone; resolution: ResolutionZone | null }[]
): { zones: Zone[]; dateDebut: string; dateFin: string | null }[] {
  const groupes: { zones: Zone[]; dateDebut: string; dateFin: string | null }[] = [];
  for (const { zone, resolution } of resolutions) {
    if (!resolution) continue;
    const { date_debut, date_fin } = resolution.ligne;
    const existant = groupes.find((g) => g.dateDebut === date_debut && g.dateFin === date_fin);
    if (existant) existant.zones.push(zone);
    else groupes.push({ zones: [zone], dateDebut: date_debut, dateFin: date_fin });
  }
  return groupes;
}

export function academiesParZone(academies: AcademieZone[]): Record<Zone, string[]> {
  const groupes: Record<Zone, string[]> = { A: [], B: [], C: [], Corse: [] };
  for (const a of academies) {
    if (a.zone === "A" || a.zone === "B" || a.zone === "C" || a.zone === "Corse") {
      groupes[a.zone].push(a.libelle_academie);
    }
  }
  return groupes;
}
