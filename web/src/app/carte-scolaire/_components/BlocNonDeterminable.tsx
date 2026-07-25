import type { SecteurResultats } from "@/lib/types";
import { ListeAlentours } from "./ListeAlentours";

const URL_RECTORATS =
  "https://www.education.gouv.fr/les-regions-academiques-academies-et-services-departementaux-de-l-education-nationale-6557";
const URL_SERVICE_PUBLIC = "https://www.service-public.gouv.fr/particuliers/vosdroits/F2322";

export function BlocNonDeterminable({ resultats }: { resultats: SecteurResultats }) {
  const academie = resultats.academie ?? "votre académie";

  return (
    <div>
      <div className="rounded-[20px] border-[1.5px] border-attention/35 bg-attention-pale p-5.5">
        <div className="flex items-start gap-3.5">
          <span className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-attention font-titre text-xl font-semibold text-white shadow-[0_5px_13px_rgba(176,116,26,.28)]">
            ?
          </span>
          <div className="flex-1">
            <div className="font-titre text-xl font-semibold text-texte">
              Nous n&apos;avons pas pu déterminer votre collège de secteur
            </div>
            <p className="mt-1.5 text-[13.5px] leading-relaxed text-texte-doux">
              Nous avons bien reconnu votre adresse, mais pas au numéro près — et le rattachement à la carte scolaire
              dépend précisément de ce niveau de détail. Plutôt que de vous indiquer un collège qui pourrait être faux,
              nous préférons vous le dire franchement.
            </p>
            <p className="mt-2 text-[13.5px] leading-relaxed text-texte-doux">
              Pour connaître votre établissement de rattachement, le mieux est de contacter le{" "}
              <b className="font-extrabold text-texte">rectorat de l&apos;académie de {academie}</b> (les services
              départementaux de l&apos;Éducation nationale). Le portail Service-Public détaille aussi la démarche
              d&apos;inscription au collège.
            </p>
            <div className="mt-3.5 flex flex-wrap gap-2.5">
              <a
                href={URL_RECTORATS}
                target="_blank"
                rel="noopener"
                className="inline-flex items-center gap-1.5 rounded-xl bg-action px-4 py-2.5 text-[12.5px] font-bold text-white shadow-[0_4px_12px_rgba(158,58,31,.28)] hover:bg-action-dark"
              >
                Contacter le rectorat de {academie} →
              </a>
              <a
                href={URL_SERVICE_PUBLIC}
                target="_blank"
                rel="noopener"
                className="inline-flex items-center gap-1.5 rounded-xl border-[1.5px] border-filet bg-white px-4 py-2.5 text-[12.5px] font-bold text-action-dark hover:border-action hover:bg-action-pale"
              >
                La démarche sur Service-Public.fr →
              </a>
            </div>
          </div>
        </div>
      </div>

      <ListeAlentours
        colleges={resultats.colleges_alentours}
        titre={`En attendant · les collèges autour de cette adresse · ${resultats.colleges_alentours.length}`}
        sousTitre="Triés par distance. L'un d'eux est probablement votre collège de secteur — la vérification officielle ci-dessus le confirmera."
      />
    </div>
  );
}
