import Link from "next/link";
import { CATEGORIES, guidesTriesParCategorie, type CategorieSlug } from "@/lib/comprendre";
import { GUIDES, QUESTIONS_GLOSSAIRE } from "@/lib/comprendreContenu";
import { RailComprendre } from "@/components/RailComprendre";
import { ListeQuestionsGlossaire } from "@/components/ListeQuestionsGlossaire";

export const metadata = {
  title: "Glossaire | Comprendre | agent-ecoles",
  description: "Réponses courtes aux questions qui reviennent, rangées par catégorie.",
};

export default function Page() {
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
          <span className="text-texte">Glossaire</span>
        </div>

        <h1 className="font-titre text-[34px] font-semibold leading-[1.08] text-texte md:text-[40px]">Glossaire</h1>
        <p className="mt-3 max-w-[700px] font-ui text-[16px] leading-[1.6] text-texte">
          {QUESTIONS_GLOSSAIRE.length} réponse{QUESTIONS_GLOSSAIRE.length > 1 ? "s" : ""} courte
          {QUESTIONS_GLOSSAIRE.length > 1 ? "s" : ""} aux questions qui reviennent, rangées par catégorie. Chaque
          réponse tient en quelques lignes et renvoie vers un guide lorsqu&apos;il existe.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-8.5 md:grid-cols-[236px_1fr]">
          <RailComprendre mode="navigateur" retour={{ label: "Comprendre", href: "/comprendre" }} comptes={comptes} />

          <div>
            {CATEGORIES.map((categorie) => {
              const questions = QUESTIONS_GLOSSAIRE.filter((q) => q.categorie === categorie.slug);
              if (questions.length === 0) return null;
              return (
                <div
                  key={categorie.slug}
                  className="mb-5 overflow-hidden rounded-2xl border border-filet-fonce bg-fond-carte"
                >
                  <div className="flex items-baseline gap-3 border-b border-filet bg-fond-entete-carte px-6 pt-4.5 pb-3.5">
                    <h2 className="font-titre text-[23px] font-semibold text-texte">{categorie.label}</h2>
                    <span className="font-ui text-[12.5px] font-semibold text-texte-doux">
                      {questions.length} question{questions.length > 1 ? "s" : ""}
                    </span>
                  </div>
                  <ListeQuestionsGlossaire questions={questions} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
