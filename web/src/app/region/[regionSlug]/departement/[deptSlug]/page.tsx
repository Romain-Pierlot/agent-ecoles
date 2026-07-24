import { notFound } from "next/navigation";
import { recupererDepartement } from "@/lib/geographie";
import { slugifier } from "@/lib/slug";
import { ZoneHub } from "@/components/ZoneHub";

export default async function Page({
  params,
}: {
  params: Promise<{ regionSlug: string; deptSlug: string }>;
}) {
  const { regionSlug, deptSlug } = await params;

  const departement = await recupererDepartement(regionSlug, deptSlug);
  if (!departement) notFound();

  // Convention alignée sur RechercheBloc : nom d'abord, code entre
  // parenthèses (cf. decision_log.md, recherche de convention du 2026-07-23).
  const libelleDepartementAvecCode = `${departement.libelle_departement} (${departement.code_departement})`;

  return (
    <ZoneHub
      filAriane={[
        { label: "Accueil", href: "/" },
        { label: departement.libelle_region, href: `/region/${regionSlug}` },
        { label: libelleDepartementAvecCode },
      ]}
      eyebrow="Département"
      titre={libelleDepartementAvecCode}
      sousTitre={`${departement.communes.length} communes`}
      global={departement.global}
      labelColonneSousDivision="Commune"
      topNotation={departement.top_notation}
      topVa={departement.top_va}
      regionSlug={regionSlug}
      sousDivisions={departement.communes.map((c) => ({
        ...c,
        // La page ville (Phase 4) n'existe pas encore : lien posé sur la
        // bonne route (imbrication S15.4), résoudra une fois construite.
        href: `/region/${regionSlug}/departement/${deptSlug}/ville/${slugifier(c.libelle)}`,
      }))}
      exempleAgent="Entre deux collèges du secteur, lequel fait le plus progresser ses élèves ?"
    />
  );
}
