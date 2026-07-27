"use client";

import { useState } from "react";
import Link from "next/link";
import type { QuestionGlossaire } from "@/lib/comprendre";
import { GUIDES } from "@/lib/comprendreContenu";

// Une question = une ligne dépliable sur place (cf. bundle, §5). "Approfondir"
// n'apparaît que si le guide visé existe déjà dans GUIDES (pas de lien mort
// vers un guide pas encore écrit).
export function ListeQuestionsGlossaire({ questions }: { questions: QuestionGlossaire[] }) {
  const [ouverte, setOuverte] = useState<string | null>(null);

  return (
    <div>
      {questions.map((question, i) => {
        const ouvert = ouverte === question.question;
        const guide = question.guideSlug ? GUIDES.find((g) => g.slug === question.guideSlug) : undefined;

        return (
          <div key={question.question} className={i > 0 ? "border-t border-filet" : undefined}>
            <button
              type="button"
              onClick={() => setOuverte(ouvert ? null : question.question)}
              aria-expanded={ouvert}
              className="flex w-full items-center justify-between gap-5 px-6 py-4 text-left"
            >
              <span className="font-titre text-[18px] font-semibold leading-[1.35] text-texte">
                {question.question}
              </span>
              <span className="flex-none font-ui text-[18px] text-texte-doux">{ouvert ? "▴" : "▾"}</span>
            </button>
            {ouvert && (
              <div className="px-6 pb-4.5">
                <p className="max-w-[640px] font-ui text-[15.5px] leading-[1.65] text-texte-corps">
                  {question.reponse}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-3.5">
                  {guide && (
                    <Link
                      href={`/comprendre/${guide.slug}`}
                      className="font-ui text-[13px] font-bold text-action-dark"
                    >
                      Approfondir : {guide.titre} ›
                    </Link>
                  )}
                  {question.source && (
                    <span className="font-ui text-[12px] font-medium text-texte-doux">
                      {question.source.producteur} · {question.source.titre}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
