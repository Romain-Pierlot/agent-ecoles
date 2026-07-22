import { notFound } from "next/navigation";
import { recupererRegion } from "@/lib/geographie";
import { construireSlugDepartement } from "@/lib/slug";
import { ZoneHub } from "@/components/ZoneHub";

export default async function Page({
  params,
}: {
  params: Promise<{ regionSlug: string }>;
}) {
  const { regionSlug } = await params;

  const region = await recupererRegion(regionSlug);
  if (!region) notFound();

  return (
    <ZoneHub
      filAriane={[
        { label: "Accueil", href: "/" },
        { label: "France", href: "/region" },
        { label: region.libelle_region },
      ]}
      eyebrow="Région"
      titre={region.libelle_region}
      sousTitre={`${region.departements.length} départements`}
      global={region.global}
      labelColonneSousDivision="Département"
      sousDivisions={region.departements.map((d) => ({
        ...d,
        href: `/region/${regionSlug}/departement/${construireSlugDepartement(d.code, d.libelle)}`,
      }))}
      exempleAgent="Un bon collège public près de chez moi…"
    />
  );
}
