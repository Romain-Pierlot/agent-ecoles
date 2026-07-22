import { recupererNational } from "@/lib/geographie";
import { construireSlugRegion } from "@/lib/slug";
import { ZoneHub } from "@/components/ZoneHub";

export default async function Page() {
  const national = await recupererNational();

  return (
    <ZoneHub
      filAriane={[{ label: "Accueil", href: "/" }, { label: "France" }]}
      eyebrow="France"
      titre="Toutes les régions"
      sousTitre={`${national.regions.length} régions`}
      global={national.global}
      labelColonneSousDivision="Région"
      sousDivisions={national.regions.map((r) => ({
        ...r,
        href: `/region/${construireSlugRegion(r.libelle)}`,
      }))}
      exempleAgent="Un bon collège public près de chez moi…"
    />
  );
}
