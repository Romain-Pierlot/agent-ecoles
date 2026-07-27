import Link from "next/link";
import { NOTES_METHODE } from "@/lib/comprendreContenu";

export const metadata = {
  title: "Méthodologie du site | Comprendre | agent-ecoles",
  description:
    "Les décisions prises par le site lui-même : comment la notation est construite, et comment les graphiques sont cadrés.",
};

export default function Page() {
  return (
    <div className="min-h-screen bg-fond-creme text-texte">
      <div className="mx-auto w-full max-w-[820px] px-4.5 pb-16 pt-4.5 md:px-11">
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <Link href="/comprendre" className="hover:text-texte-doux">Comprendre</Link>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">Méthodologie du site</span>
        </div>

        <span className="inline-flex items-center gap-1.5 rounded-full border border-methode-filet bg-fond-carte px-3 py-1.5 font-ui text-[11px] font-bold tracking-[.05em] text-methode-ink uppercase">
          <span className="h-1.5 w-1.5 rounded-full bg-methode-accent" />
          Choix du site
        </span>
        <h1 className="mt-3 font-titre text-[34px] font-semibold leading-[1.08] text-texte md:text-[40px]">
          Méthodologie du site
        </h1>
        <p className="mt-3 font-ui text-[16px] leading-[1.6] text-texte">
          Les guides de Comprendre synthétisent des sources officielles. Ces notes expliquent, elles, des décisions
          prises par le site lui-même.
        </p>

        <div className="mt-6 overflow-hidden rounded-2xl border border-methode-filet bg-methode-fond">
          {NOTES_METHODE.length === 0 ? (
            <p className="px-6 py-6 font-ui text-[14.5px] leading-[1.6] text-methode-ink/80">
              Aucune note de méthode publiée pour le moment.
            </p>
          ) : (
            NOTES_METHODE.map((note, i) => (
              <Link
                key={note.slug}
                href={`/comprendre/methodologie/${note.slug}`}
                className={`flex items-center justify-between gap-5 px-6 py-4.5 ${
                  i > 0 ? "border-t border-methode-filet-clair" : ""
                }`}
              >
                <span className="font-titre text-[19px] font-semibold text-texte">{note.titre}</span>
                <span className="font-ui text-[20px] text-methode-accent">›</span>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
