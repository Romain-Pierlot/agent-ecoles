import type { AcademieZone, PeriodeVacances } from "@/lib/types";
import { PeriodePlage } from "./DateLongue";
import {
  ZONES, LABEL_ZONE, TEINTE_ZONE, LIGNES_METROPOLE, resoudreZone, academiesParZone, type Zone,
} from "./zones";

const ZONES_ABC: Zone[] = ["A", "B", "C"];

// Étiquette explicite au-dessus de la date d'une cellule fusionnée — un
// dégradé de couleur seul (essayé d'abord, cf. maquette) donnait l'impression
// que le texte centré appartenait à la colonne du milieu. Même principe que
// l'accessibilité des en-têtes de colonnes : la couleur ne porte jamais
// seule l'information (retenu après retour d'usage réel, cf. décision_log).
function EtiquetteZones({ zones }: { zones: Zone[] }) {
  if (zones.length === ZONES.length) {
    return (
      <span className="inline-block rounded-full border border-filet-fonce bg-fond-carte px-[10px] py-[3px] font-ui text-[10.5px] font-bold text-texte-doux">
        Toutes les zones
      </span>
    );
  }
  return (
    <div className="flex flex-wrap justify-center gap-1.5">
      {zones.map((zone) => (
        <span
          key={zone}
          className={`inline-block rounded-[6px] ${TEINTE_ZONE[zone].pleine} px-2 py-[2px] font-ui text-[10.5px] font-extrabold text-fond-carte`}
        >
          {LABEL_ZONE[zone]}
        </span>
      ))}
    </div>
  );
}

export function TableauMetropole({
  metropole, academies,
}: {
  metropole: PeriodeVacances[];
  academies: AcademieZone[];
}) {
  const groupes = academiesParZone(academies);

  return (
    <div className="hidden overflow-hidden rounded-2xl border border-filet-fonce bg-fond-carte md:block">
      <table className="w-full table-fixed border-collapse">
        <caption className="sr-only">
          Dates des vacances scolaires par zone (métropole et Corse)
        </caption>
        <colgroup>
          <col className="w-[196px]" />
          {/* table-fixed répartit les colonnes sans largeur explicite à
              parts égales sur l'espace restant — sans ça, la colonne dont
              la liste d'académies est la plus longue (Zone B, 11 académies)
              s'étirait au détriment des autres, et les dégradés de fusion
              (colSpan) désalignaient avec les vraies frontières de colonne. */}
          <col />
          <col />
          <col />
          <col />
        </colgroup>
        <thead>
          <tr>
            <th scope="col" className="border-b border-filet bg-fond-carte" />
            {ZONES.map((zone) => {
              const teinte = TEINTE_ZONE[zone];
              return (
                <th
                  key={zone}
                  scope="col"
                  className={`border-b-4 ${teinte.bordurePleine} ${teinte.entete} px-[15px] pb-[14px] pt-[13px] text-center align-top`}
                >
                  <span className={`inline-block rounded-[7px] ${teinte.pleine} px-3.5 py-[5px] font-ui text-[13px] font-extrabold text-fond-carte`}>
                    {LABEL_ZONE[zone]}
                  </span>
                  <div className="mt-2 font-ui text-[11.5px] leading-[1.55] text-texte">
                    {zone === "Corse"
                      ? "Académie de Corse, hors découpage A / B / C"
                      : groupes[zone].join(", ")}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {LIGNES_METROPOLE.map((ligne) => {
            const resolutions = ZONES.map((zone) => ({ zone, resolution: resoudreZone(ligne.periodeSource, zone, metropole) }));
            const [a, b, c, corse] = resolutions;
            const abcCommunes = a.resolution?.deToutes && b.resolution?.deToutes && c.resolution?.deToutes;
            const toutesCommunes = abcCommunes && corse.resolution?.deToutes;

            return (
              <tr key={ligne.libelle} className="border-t border-filet first:border-t-0">
                <th
                  scope="row"
                  className="px-[18px] py-4 text-left align-middle font-ui text-[15px] font-bold leading-tight text-texte"
                >
                  {ligne.libelle}
                </th>
                {toutesCommunes && a.resolution ? (
                  <td
                    colSpan={4}
                    className="bg-fond-sable px-[18px] py-[15px] text-center"
                  >
                    <EtiquetteZones zones={ZONES} />
                    <div className="mt-1.5 font-ui text-[16px] font-bold leading-[1.4] text-texte">
                      <PeriodePlage dateDebut={a.resolution.ligne.date_debut} dateFin={a.resolution.ligne.date_fin} />
                    </div>
                  </td>
                ) : abcCommunes && a.resolution && corse.resolution ? (
                  <>
                    <td colSpan={3} className="bg-fond-sable px-[18px] py-[15px] text-center">
                      <EtiquetteZones zones={ZONES_ABC} />
                      <div className="mt-1.5 font-ui text-[16px] font-bold leading-[1.4] text-texte">
                        <PeriodePlage dateDebut={a.resolution.ligne.date_debut} dateFin={a.resolution.ligne.date_fin} />
                      </div>
                    </td>
                    <td className={`border-l border-filet ${TEINTE_ZONE.Corse.pale} px-3.5 py-[15px] text-center font-ui text-[14.5px] font-bold leading-[1.4] text-texte`}>
                      <PeriodePlage dateDebut={corse.resolution.ligne.date_debut} dateFin={corse.resolution.ligne.date_fin} />
                    </td>
                  </>
                ) : (
                  resolutions.map(({ zone, resolution }) =>
                    resolution ? (
                      <td
                        key={zone}
                        className={`border-l border-filet ${TEINTE_ZONE[zone].pale} px-3.5 py-[15px] text-center font-ui text-[14.5px] font-bold leading-[1.4] text-texte`}
                      >
                        <PeriodePlage dateDebut={resolution.ligne.date_debut} dateFin={resolution.ligne.date_fin} />
                      </td>
                    ) : (
                      <td key={zone} className="border-l border-filet px-3.5 py-[15px] text-center text-texte-doux" />

                    )
                  )
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
