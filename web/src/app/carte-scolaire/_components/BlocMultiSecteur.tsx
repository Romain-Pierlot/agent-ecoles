import { CarteCollegeSecteur } from "@/components/CarteCollegeSecteur";
import type { SecteurResultats } from "@/lib/types";
import { ListeAlentours } from "./ListeAlentours";

const URL_RECTORATS =
  "https://www.education.gouv.fr/les-regions-academiques-academies-et-services-departementaux-de-l-education-nationale-6557";

export function BlocMultiSecteur({ resultats }: { resultats: SecteurResultats }) {
  const total = resultats.colleges_secteur.length;

  return (
    <div>
      <div className="mb-3.5 flex gap-2.5 rounded-2xl border-[1.5px] border-attention/35 bg-attention-pale p-3.5">
        <span className="flex h-7.5 w-7.5 flex-none items-center justify-center rounded-lg bg-attention font-bold text-white">
          !
        </span>
        <p className="text-[13px] leading-relaxed text-attention-dark">
          <b className="font-extrabold text-attention-dark">Votre adresse peut relever de plusieurs secteurs.</b> Selon le
          côté de la rue ou la langue vivante choisie, plusieurs collèges sont légitimes pour votre domicile. Confirmez
          le vôtre auprès de votre rectorat.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {resultats.colleges_secteur.map((college, i) => (
          <CarteCollegeSecteur key={college.uai} college={college} rang={i + 1} totalRang={total} />
        ))}
      </div>

      <div className="mt-3 flex gap-2 px-1">
        <span className="flex-none text-[13px] text-texte-doux">ⓘ</span>
        <p className="text-[12px] leading-relaxed text-texte-doux">
          Ces résultats correspondent à l&apos;adresse que vous avez saisie{" "}
          <b className="text-texte-doux">dans la carte scolaire 2025 du Ministère</b> — c&apos;est la donnée sur
          laquelle nous nous appuyons. Avant toute inscription,{" "}
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
