import Link from "next/link";
import { CATEGORIES, guidesTriesParCategorie, type CategorieSlug } from "@/lib/comprendre";
import { GUIDES, QUESTIONS_GLOSSAIRE } from "@/lib/comprendreContenu";
import { RailComprendre } from "@/components/RailComprendre";
import { ListeGuidesCategorie } from "@/components/ListeGuidesCategorie";
import { PagePlaceholder } from "@/components/PagePlaceholder";

// Un seul dossier dynamique pour catégories ET guides : Next.js interdit
// deux segments dynamiques de noms différents ([categorieSlug] et [slug])
// au même niveau /comprendre/*, alors que le bundle de référence les place
// bien côte à côte dans l'arborescence (/comprendre/[categorieSlug] et
// /comprendre/[slug]). On tranche ici sur le contenu du slug plutôt que sur
// l'URL, pour ne pas dévier des routes prévues par le bundle.

export function generateStaticParams() {
  return CATEGORIES.map((categorie) => ({ slug: categorie.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const categorie = CATEGORIES.find((c) => c.slug === slug);
  if (!categorie) return {};
  return { title: `${categorie.label} | Comprendre | agent-ecoles`, description: categorie.role };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const categorie = CATEGORIES.find((c) => c.slug === slug);

  if (!categorie) {
    // Pas encore une vraie route de guide (arrive en phase 6 du plan) :
    // squelette temporaire, comme avant la création de cette route.
    return <PagePlaceholder titre="Guide — Comprendre" chemin="/comprendre/[slug]" params={{ slug }} />;
  }

  const guides = guidesTriesParCategorie(GUIDES, categorie.slug);
  const comptes = Object.fromEntries(
    CATEGORIES.map((c) => [c.slug, guidesTriesParCategorie(GUIDES, c.slug as CategorieSlug).length])
  );

  return (
    <div className="min-h-screen bg-fond-creme text-texte">
      <div className="mx-auto w-full max-w-[1280px] px-4.5 pb-16 pt-4.5 md:px-11">
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <Link href="/comprendre" className="hover:text-texte-doux">Comprendre</Link>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">{categorie.label}</span>
        </div>

        <h1 className="font-titre text-[32px] font-semibold leading-[1.08] text-texte md:text-[40px] md:leading-[1.08]">
          {categorie.label}
        </h1>
        <p className="mt-3 max-w-[700px] font-ui text-[16px] leading-[1.6] text-texte">{categorie.role}</p>

        <div className="mt-6 grid grid-cols-1 gap-8.5 md:grid-cols-[236px_1fr]">
          <RailComprendre
            mode="navigateur"
            categorieActive={categorie}
            comptes={comptes}
            glossaire={{
              label: "Glossaire de la catégorie",
              href: "/comprendre/glossaire",
              compte: QUESTIONS_GLOSSAIRE.filter((q) => q.categorie === categorie.slug).length,
            }}
          />

          <ListeGuidesCategorie guides={guides} sousThemes={categorie.sousThemes} />
        </div>
      </div>
    </div>
  );
}
