import Link from "next/link";
import { notFound } from "next/navigation";
import { NOTES_METHODE } from "@/lib/comprendreContenu";
import { formaterDateJourMoisAnnee } from "@/lib/formatDateLongue";
import { slugifier } from "@/lib/slug";
import { RailComprendre } from "@/components/RailComprendre";
import { AgentBlock } from "@/components/AgentBlock";

export function generateStaticParams() {
  return NOTES_METHODE.map((note) => ({ slug: note.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const note = NOTES_METHODE.find((n) => n.slug === slug);
  if (!note) return {};
  return { title: `${note.titre} | Méthodologie | agent-ecoles` };
}

// Même gabarit de lecture que la page guide, mais avec la famille de
// couleurs "méthode" (fond, bordures, pastille) et une colonne de droite
// différente : historique des révisions plutôt que sources externes — un
// guide reconfirme un fait externe stable, une note de méthode documente
// un changement de choix du site (cf. bundle, §4).
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const note = NOTES_METHODE.find((n) => n.slug === slug);
  if (!note) notFound();

  return (
    <div className="min-h-screen bg-methode-fond text-texte">
      <div className="mx-auto w-full max-w-[1280px] px-4.5 pb-16 pt-4.5 md:px-11">
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <Link href="/comprendre" className="hover:text-texte-doux">Comprendre</Link>
          <span className="text-filet-fonce">›</span>
          <Link href="/comprendre/methodologie" className="hover:text-texte-doux">Méthodologie du site</Link>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">{note.titre}</span>
        </div>

        <div className="max-w-[820px]">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-methode-filet bg-fond-carte px-3 py-1.5 font-ui text-[11px] font-bold tracking-[.05em] text-methode-ink uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-methode-accent" />
            Choix du site
          </span>
          <h1 className="mt-3 font-titre text-[36px] font-semibold leading-[1.1] text-texte md:text-[42px]">
            {note.titre}
          </h1>
          <p className="mt-3 font-ui text-[12.5px] font-medium text-texte-doux">
            Version {note.version} · en vigueur depuis le {formaterDateJourMoisAnnee(note.enVigueurDepuis)}
          </p>
        </div>

        <div className="mt-7 grid grid-cols-1 gap-8.5 md:grid-cols-[228px_660px_1fr]">
          <RailComprendre
            mode="sommaire"
            retour={{ label: "Méthodologie du site", href: "/comprendre/methodologie" }}
            sections={note.corps.map((section) => ({ titre: section.titre, ancre: slugifier(section.titre) }))}
          />

          <div>
            {note.corps.map((section) => (
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
              </div>
            ))}

            <AgentBlock exemple={`Une question sur « ${note.titre.split(":")[0].trim()} » ?`} />
          </div>

          <div className="rounded-[14px] border border-methode-filet bg-fond-carte px-4.5 py-4">
            <div className="mb-3.5 font-ui text-[11px] font-bold tracking-[.08em] text-texte-doux uppercase">
              Historique des révisions
            </div>
            <div className="flex flex-col">
              {note.revisions.map((revision, i) => (
                <div
                  key={revision.version}
                  className={i > 0 ? "mt-3.5 border-t border-methode-filet-clair pt-3.5" : undefined}
                >
                  <div className="font-ui text-[13px] font-bold text-texte">
                    Version {revision.version} · {formaterDateJourMoisAnnee(revision.date)}
                  </div>
                  <div className="mt-0.5 font-ui text-[12.5px] leading-[1.5] text-texte-doux">
                    {revision.changement}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
