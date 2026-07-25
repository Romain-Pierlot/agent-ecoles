import { CarteCollegeSecteur } from "@/components/CarteCollegeSecteur";
import type { SecteurResultats } from "@/lib/types";
import { ListeAlentours } from "./ListeAlentours";

const URL_RECTORATS =
  "https://www.education.gouv.fr/les-regions-academiques-academies-et-services-departementaux-de-l-education-nationale-6557";

export function BlocTrouve({ resultats }: { resultats: SecteurResultats }) {
  const college = resultats.colleges_secteur[0];

  return (
    <div>
      <CarteCollegeSecteur college={college} />

      <div className="mt-3 flex gap-2 px-1">
        <span className="flex-none text-[13px] text-texte-doux">ⓘ</span>
        <p className="text-[12px] leading-relaxed text-texte-doux">
          Ce résultat correspond à l&apos;adresse que vous avez saisie{" "}
          <b className="text-texte-doux">dans la carte scolaire 2025 du Ministère</b> — c&apos;est la donnée sur
          laquelle nous nous appuyons. En principe c&apos;est le bon collège, mais ces fichiers peuvent comporter des
          erreurs et le rattachement dépend parfois du niveau ou de la langue vivante. Avant toute inscription,{" "}
          <a href={URL_RECTORATS} target="_blank" rel="noopener" className="font-bold text-action-dark hover:text-action">
            vérifiez auprès de votre rectorat
          </a>
          , qui reste seul à faire foi.
        </p>
      </div>

      <ListeAlentours
        colleges={resultats.colleges_alentours}
        titre={`Autres collèges autour de chez vous · ${resultats.colleges_alentours.length}`}
      />
    </div>
  );
}
