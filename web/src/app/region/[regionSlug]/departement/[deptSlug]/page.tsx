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

  return (
    <ZoneHub
      filAriane={[
        { label: "Accueil", href: "/" },
        { label: departement.libelle_region, href: `/region/${regionSlug}` },
        { label: departement.libelle_departement },
      ]}
      eyebrow="Département"
      titre={departement.libelle_departement}
      sousTitre={`${departement.communes.length} communes`}
      global={departement.global}
      labelColonneSousDivision="Commune"
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
