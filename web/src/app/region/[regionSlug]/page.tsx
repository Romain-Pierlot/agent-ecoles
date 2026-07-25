import { notFound } from "next/navigation";
import { recupererRegion } from "@/lib/geographie";
import { construireSlugDepartement } from "@/lib/slug";
import { accorder } from "@/lib/format";
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
      sousTitre={`${region.departements.length} ${accorder(region.departements.length, "département")}`}
      global={region.global}
      labelColonneSousDivision="Département"
      afficherCodeSousDivisions
      topNotation={region.top_notation}
      topVa={region.top_va}
      regionSlug={regionSlug}
      sousDivisions={region.departements.map((d) => ({
        ...d,
        href: `/region/${regionSlug}/departement/${construireSlugDepartement(d.code, d.libelle)}`,
      }))}
      exempleAgent="Un bon collège public près de chez moi…"
    />
  );
}
