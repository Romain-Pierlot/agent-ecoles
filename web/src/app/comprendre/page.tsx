import Link from "next/link";
import { CATEGORIES, guidesTriesParCategorie } from "@/lib/comprendre";
import { GUIDES, QUESTIONS_GLOSSAIRE } from "@/lib/comprendreContenu";
import { CarteCategorie } from "@/components/CarteCategorie";
import { RailComprendre } from "@/components/RailComprendre";

export const metadata = {
  title: "Comprendre | agent-ecoles",
  description:
    "Les repères nécessaires pour lire une fiche de collège et pour suivre les étapes de la scolarité.",
};

export default function Page() {
  const comptes = Object.fromEntries(
    CATEGORIES.map((categorie) => [categorie.slug, guidesTriesParCategorie(GUIDES, categorie.slug).length])
  );
  // Catégories sans guide pas encore affichées : une carte à 0 ligne serait
  // trompeuse tant que le contenu de lancement n'est pas complet (cf. plan,
  // phase 10). Le rail, lui, liste toujours les quatre catégories fixes.
  const categoriesAvecGuides = CATEGORIES.filter((categorie) => comptes[categorie.slug] > 0);

  return (
    <div className="min-h-screen bg-fond-creme text-texte">
      <div className="mx-auto w-full max-w-[1280px] px-4.5 pb-16 pt-4.5 md:px-11">
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">Comprendre</span>
        </div>

        <h1 className="font-titre text-[34px] font-semibold leading-[1.08] text-texte md:text-[44px] md:leading-[1.06]">
          Comprendre
        </h1>
        <p className="mt-3 max-w-[720px] font-ui text-[16px] leading-[1.6] text-texte">
          Les repères nécessaires pour lire une fiche de collège et pour suivre les étapes de la
          scolarité. Chaque guide synthétise des sources identifiées.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-8.5 md:grid-cols-[250px_1fr]">
          <RailComprendre mode="navigateur" comptes={comptes} compteGlossaire={QUESTIONS_GLOSSAIRE.length} />

          <div>
            {categoriesAvecGuides.map((categorie) => (
              <CarteCategorie
                key={categorie.slug}
                categorie={categorie}
                guides={guidesTriesParCategorie(GUIDES, categorie.slug)}
                questions={QUESTIONS_GLOSSAIRE.filter((question) => question.categorie === categorie.slug)}
              />
            ))}

            <div className="overflow-hidden rounded-2xl border border-methode-filet bg-methode-pale">
              <div className="border-b border-methode-filet-clair px-6 pt-5 pb-4">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-methode-filet bg-fond-carte px-3 py-1.5 font-ui text-[11px] font-bold tracking-[.05em] text-methode-ink uppercase">
                  <span className="h-1.5 w-1.5 rounded-full bg-methode-accent" />
                  Choix du site
                </span>
                <h2 className="mt-3 font-titre text-[25px] font-semibold text-texte">Méthodologie du site</h2>
                <p className="mt-1.5 max-w-[660px] font-ui text-[14px] text-methode-ink/80">
                  Les guides ci-dessus synthétisent des sources officielles. Ces notes expliquent des
                  décisions prises par le site lui-même.
                </p>
              </div>
              <Link
                href="/comprendre/methodologie"
                className="flex items-center justify-between gap-4 px-6 py-4 font-ui text-[14px] font-bold text-methode-ink"
              >
                Voir les notes de méthode
                <span className="font-ui text-[20px] text-methode-accent">›</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
