import Link from "next/link";
import { CATEGORIES, guidesTriesParCategorie, type CategorieSlug } from "@/lib/comprendre";
import { GUIDES, QUESTIONS_GLOSSAIRE } from "@/lib/comprendreContenu";
import { formaterDateJourMoisAnnee } from "@/lib/formatDateLongue";
import { slugifier } from "@/lib/slug";
import { RailComprendre } from "@/components/RailComprendre";
import { ListeGuidesCategorie } from "@/components/ListeGuidesCategorie";
import { LigneGuide } from "@/components/LigneGuide";
import { FigureEchelle } from "@/components/FigureEchelle";
import { ListeSources } from "@/components/ListeSources";
import { AgentBlock } from "@/components/AgentBlock";
import { PagePlaceholder } from "@/components/PagePlaceholder";

// Un seul dossier dynamique pour catégories ET guides : Next.js interdit
// deux segments dynamiques de noms différents ([categorieSlug] et [slug])
// au même niveau /comprendre/*, alors que le bundle de référence les place
// bien côte à côte dans l'arborescence (/comprendre/[categorieSlug] et
// /comprendre/[slug]). On tranche ici sur le contenu du slug plutôt que sur
// l'URL, pour ne pas dévier des routes prévues par le bundle.

export function generateStaticParams() {
  return [...CATEGORIES.map((c) => ({ slug: c.slug })), ...GUIDES.map((g) => ({ slug: g.slug }))];
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const categorie = CATEGORIES.find((c) => c.slug === slug);
  if (categorie) return { title: `${categorie.label} | Comprendre | agent-ecoles`, description: categorie.role };
  const guide = GUIDES.find((g) => g.slug === slug);
  if (guide) return { title: `${guide.titre} | Comprendre | agent-ecoles`, description: guide.resume };
  return {};
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  const categorie = CATEGORIES.find((c) => c.slug === slug);
  if (categorie) return <PageCategorie categorieSlug={categorie.slug} />;

  const guide = GUIDES.find((g) => g.slug === slug);
  if (guide) return <PageGuide slug={guide.slug} />;

  // Ni catégorie ni guide connu : contenu pas encore écrit (arrive au fil
  // de la phase 10 du plan). Squelette temporaire, comme avant la création
  // de cette route.
  return <PagePlaceholder titre="Guide — Comprendre" chemin="/comprendre/[slug]" params={{ slug }} />;
}

function PageCategorie({ categorieSlug }: { categorieSlug: CategorieSlug }) {
  const categorie = CATEGORIES.find((c) => c.slug === categorieSlug)!;
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

function PageGuide({ slug }: { slug: string }) {
  const guide = GUIDES.find((g) => g.slug === slug)!;
  const categorie = CATEGORIES.find((c) => c.slug === guide.categorie)!;
  const questionsGuide = QUESTIONS_GLOSSAIRE.filter((q) => q.guideSlug === guide.slug);
  const autresGuides = guidesTriesParCategorie(GUIDES, guide.categorie)
    .filter((g) => g.slug !== guide.slug)
    .slice(0, 2);

  return (
    <div className="min-h-screen bg-fond-creme text-texte">
      <div className="mx-auto w-full max-w-[1280px] px-4.5 pb-16 pt-4.5 md:px-11">
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <Link href="/comprendre" className="hover:text-texte-doux">Comprendre</Link>
          <span className="text-filet-fonce">›</span>
          <Link href={`/comprendre/${categorie.slug}`} className="hover:text-texte-doux">{categorie.label}</Link>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">{guide.titre}</span>
        </div>

        <div className="max-w-[820px]">
          <h1 className="font-titre text-[36px] font-semibold leading-[1.1] text-texte md:text-[42px]">
            {guide.titre}
          </h1>
          <p className="mt-3.5 font-ui text-[17px] leading-[1.62] text-texte-corps">{guide.chapeau}</p>
          <div className="mt-4 flex flex-wrap items-center gap-2.5 font-ui text-[12.5px] font-medium text-texte-doux">
            <span>Publié le {formaterDateJourMoisAnnee(guide.publieLe)}</span>
            <span>·</span>
            <span>{guide.sources.length} source{guide.sources.length > 1 ? "s" : ""} officielle{guide.sources.length > 1 ? "s" : ""}</span>
          </div>
        </div>

        <div className="mt-7 grid grid-cols-1 gap-8.5 md:grid-cols-[228px_660px_1fr]">
          <RailComprendre
            mode="sommaire"
            retour={{ label: categorie.label, href: `/comprendre/${categorie.slug}` }}
            sections={guide.corps.map((section) => ({ titre: section.titre, ancre: slugifier(section.titre) }))}
          />

          <div>
            <div className="mb-7.5 rounded-[14px] border border-filet-fonce bg-fond-carte px-5.5 pt-4.5 pb-5">
              <div className="mb-2.5 font-ui text-[11px] font-bold tracking-[.08em] text-texte-doux uppercase">
                En résumé
              </div>
              <div className="flex flex-col gap-2.5">
                {guide.resumeCourt.map((puce) => (
                  <div key={puce} className="grid grid-cols-[auto_1fr] items-start gap-2.5">
                    <span className="mt-2 h-[5px] w-[5px] flex-none rounded-full bg-action" />
                    <span className="font-ui text-[14.5px] leading-[1.55] text-texte-corps">{puce}</span>
                  </div>
                ))}
              </div>
            </div>

            {guide.corps.map((section) => (
              <div key={section.titre}>
                <h2
                  id={slugifier(section.titre)}
                  className="scroll-mt-24 font-titre text-[27px] font-semibold text-texte"
                >
                  {section.titre}
                </h2>
                {section.paragraphes.map((paragraphe) => (
                  <p key={paragraphe} className="mt-3 font-ui text-[16.5px] leading-[1.72] text-texte-corps">
                    {paragraphe}
                  </p>
                ))}
                {section.encadre && (
                  <div className="mt-1 mb-6 rounded-xl border border-filet-fonce bg-fond-encart px-4.5 py-4">
                    <div className="mb-1 font-ui text-[12.5px] font-bold text-texte-corps">{section.encadre.titre}</div>
                    <div className="font-ui text-[14px] leading-[1.6] text-texte-corps">{section.encadre.texte}</div>
                  </div>
                )}
              </div>
            ))}

            {guide.figure && <FigureEchelle figure={guide.figure} />}

            {guide.apparaitSur && guide.apparaitSur.length > 0 && (
              <>
                <h2 className="font-titre text-[27px] font-semibold text-texte">Où il apparaît sur le site</h2>
                <div className="mt-3 mb-8.5 overflow-hidden rounded-[14px] border border-filet-fonce bg-fond-carte">
                  {guide.apparaitSur.map((occurrence, i) => {
                    const contenu = (
                      <>
                        <div className="font-ui text-[14.5px] font-bold text-texte">{occurrence.label}</div>
                        <div className="mt-0.5 font-ui text-[13.5px] leading-[1.5] text-texte-doux">
                          {occurrence.description}
                        </div>
                      </>
                    );
                    const classe = `grid grid-cols-[1fr_auto] items-center gap-5 px-5 py-4 ${i > 0 ? "border-t border-filet" : ""}`;
                    return occurrence.href ? (
                      <Link key={occurrence.label} href={occurrence.href} className={classe}>
                        <div>{contenu}</div>
                        <span className="font-ui text-[21px] text-filet-fonce">›</span>
                      </Link>
                    ) : (
                      <div key={occurrence.label} className={classe}>
                        <div>{contenu}</div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}

            {questionsGuide.length > 0 && (
              <>
                <div className="mb-3 font-ui text-[11px] font-bold tracking-[.08em] text-texte-doux uppercase">
                  Questions courtes sur ce sujet
                </div>
                <div className="mb-6.5 overflow-hidden rounded-xl border border-filet-fonce bg-fond-encart">
                  {questionsGuide.map((question, i) => (
                    <Link
                      key={question.question}
                      href="/comprendre/glossaire"
                      className={`grid grid-cols-[1fr_auto] items-center gap-4 px-4.5 py-3.5 font-ui text-[14.5px] font-medium text-texte-corps ${
                        i > 0 ? "border-t border-filet-fonce" : ""
                      }`}
                    >
                      {question.question}
                      <span className="text-filet-fonce">›</span>
                    </Link>
                  ))}
                </div>
              </>
            )}

            {autresGuides.length > 0 && (
              <>
                <div className="mb-3 font-ui text-[11px] font-bold tracking-[.08em] text-texte-doux uppercase">
                  À lire ensuite
                </div>
                <div className="mb-6.5 overflow-hidden rounded-xl border border-filet-fonce bg-fond-carte">
                  {autresGuides.map((autreGuide, i) => (
                    <div key={autreGuide.slug} className={i > 0 ? "border-t border-filet" : undefined}>
                      <LigneGuide guide={autreGuide} />
                    </div>
                  ))}
                </div>
              </>
            )}

            <AgentBlock exemple={`Une question sur « ${guide.titre.split(":")[0].trim()} » pour un collège précis ?`} />
          </div>

          <ListeSources sources={guide.sources} />
        </div>
      </div>
    </div>
  );
}
