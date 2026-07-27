import Link from "next/link";
import type { Categorie, Guide, QuestionGlossaire } from "@/lib/comprendre";
import { LigneGuide } from "@/components/LigneGuide";

// Plafond de l'index (règle C du bundle) : au-delà, la catégorie renvoie
// vers sa page dédiée plutôt que d'allonger l'index indéfiniment.
const PLAFOND_INDEX = 8;

export function CarteCategorie({
  categorie,
  guides,
  questions = [],
}: {
  categorie: Categorie;
  guides: Guide[];
  questions?: QuestionGlossaire[];
}) {
  const affiches = guides.slice(0, PLAFOND_INDEX);
  const reste = guides.length - affiches.length;

  return (
    <div className="mb-5 overflow-hidden rounded-2xl border border-filet-fonce bg-fond-carte">
      <div className="border-b border-filet bg-fond-entete-carte px-6 pt-5 pb-4">
        <div className="flex items-baseline gap-3">
          <h2 className="font-titre text-[25px] font-semibold text-texte">{categorie.label}</h2>
          <span className="font-ui text-[12.5px] font-semibold text-texte-doux">
            {guides.length} guide{guides.length > 1 ? "s" : ""}
          </span>
        </div>
        <p className="mt-1.5 max-w-[640px] font-ui text-[14px] text-texte-doux">{categorie.role}</p>
      </div>

      {affiches.map((guide, i) => (
        <div key={guide.slug} className={i > 0 ? "border-t border-filet" : undefined}>
          <LigneGuide guide={guide} />
        </div>
      ))}

      {reste > 0 && (
        <Link
          href={`/comprendre/${categorie.slug}`}
          className="flex items-center justify-between gap-4 border-t border-filet bg-fond-entete-carte px-6 py-3.5"
        >
          <span className="font-ui text-[14px] font-bold text-action-dark">
            Voir les {guides.length} guides de cette catégorie
          </span>
          <span className="font-ui text-[12.5px] font-medium text-texte-doux">
            {reste} guide{reste > 1 ? "s" : ""} de plus ›
          </span>
        </Link>
      )}

      {questions.length > 0 && (
        <div className="flex flex-wrap items-center gap-3.5 border-t border-filet bg-fond-encart px-6 py-3.5">
          <span className="flex-none font-ui text-[11px] font-bold tracking-[.08em] text-texte-doux uppercase">
            Réponses courtes
          </span>
          {questions.slice(0, 2).map((q) => (
            <Link
              key={q.question}
              href="/comprendre/glossaire"
              className="border-b border-filet-fonce font-ui text-[13.5px] font-medium text-texte"
            >
              {q.question}
            </Link>
          ))}
          <Link
            href="/comprendre/glossaire"
            className="ml-auto flex-none font-ui text-[13px] font-bold text-action-dark"
          >
            Voir le glossaire ›
          </Link>
        </div>
      )}
    </div>
  );
}
