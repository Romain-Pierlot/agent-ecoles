import type { AcademieZone, PeriodeVacances } from "@/lib/types";
import { PeriodePlage } from "./DateLongue";
import {
  ZONES, LABEL_ZONE, TEINTE_ZONE, SUFFIXE_TOKEN_ZONE, LIGNES_METROPOLE,
  resoudreZone, grouperZonesParDate, academiesParZone, type Zone,
} from "./zones";

function fondGroupe(zones: Zone[]): { className?: string; style?: React.CSSProperties } {
  if (zones.length === 1) return { className: TEINTE_ZONE[zones[0]].pale };
  const pas = 100 / zones.length;
  const bandes = zones
    .map((z, i) => `var(--color-zone-${SUFFIXE_TOKEN_ZONE[z]}-pale) ${i * pas}% ${(i + 1) * pas}%`)
    .join(", ");
  return { style: { background: `linear-gradient(120deg, ${bandes})` } };
}

export function CartesMetropoleMobile({
  metropole, academies,
}: {
  metropole: PeriodeVacances[];
  academies: AcademieZone[];
}) {
  const groupes = academiesParZone(academies);

  return (
    <div className="md:hidden">
      {/* Clé des zones */}
      <ul className="flex flex-col gap-[7px]">
        {ZONES.map((zone) => {
          const teinte = TEINTE_ZONE[zone];
          return (
            <li
              key={zone}
              className={`rounded-[4px_12px_12px_4px] border border-filet border-l-[3px] ${teinte.bordurePleine} bg-fond-carte px-[13px] py-[11px]`}
            >
              <span className={`inline-block rounded-[6px] ${teinte.pleine} px-2.5 py-[3px] font-ui text-[11.5px] font-extrabold text-fond-carte`}>
                {LABEL_ZONE[zone]}
              </span>
              <span className="ml-2 font-ui text-[12px] leading-[1.55] text-texte">
                {zone === "Corse" ? "Académie de Corse, hors découpage A / B / C" : groupes[zone].join(" · ")}
              </span>
            </li>
          );
        })}
      </ul>

      {/* Cartes de périodes */}
      <div className="mt-4 overflow-hidden rounded-2xl border border-filet-fonce bg-fond-carte">
        {LIGNES_METROPOLE.map((ligne) => {
          const resolutions = ZONES.map((zone) => ({ zone, resolution: resoudreZone(ligne.periodeSource, zone, metropole) }));
          const commune = resolutions.every((r) => r.resolution?.deToutes);

          if (commune && resolutions[0].resolution) {
            const { ligne: donnee } = resolutions[0].resolution;
            return (
              <div key={ligne.libelle} className="border-t border-filet px-[13px] py-[11px] first:border-t-0">
                <div className="flex items-center justify-between">
                  <span className="font-ui text-[14px] font-bold text-texte">{ligne.libelle}</span>
                  <span className="rounded-full border border-filet-fonce bg-fond-sable px-[9px] py-[2px] font-ui text-[9.5px] font-bold text-texte-doux">
                    toutes les zones
                  </span>
                </div>
                <div className="mt-[7px] font-ui text-[16px] font-bold leading-[1.4] text-texte">
                  <PeriodePlage dateDebut={donnee.date_debut} dateFin={donnee.date_fin} />
                </div>
              </div>
            );
          }

          const groupesDate = grouperZonesParDate(resolutions);
          return (
            <div key={ligne.libelle} className="border-t border-filet px-[13px] py-[11px] first:border-t-0">
              <span className="font-ui text-[14px] font-bold text-texte">{ligne.libelle}</span>
              <div className="mt-2 flex flex-col gap-2">
                {groupesDate.map((groupe) => {
                  const fond = fondGroupe(groupe.zones);
                  return (
                    <div
                      key={groupe.zones.join("-")}
                      className={`rounded-[10px] border border-filet px-[11px] py-[9px] ${fond.className ?? ""}`}
                      style={fond.style}
                    >
                      <div className="flex flex-wrap gap-[5px]">
                        {groupe.zones.map((zone) => (
                          <span
                            key={zone}
                            className={`inline-block rounded-[6px] ${TEINTE_ZONE[zone].pleine} px-2.5 py-[3px] font-ui text-[11.5px] font-extrabold text-fond-carte`}
                          >
                            {LABEL_ZONE[zone]}
                          </span>
                        ))}
                      </div>
                      <div className="mt-[6px] font-ui text-[14px] font-bold leading-[1.4] text-texte">
                        <PeriodePlage dateDebut={groupe.dateDebut} dateFin={groupe.dateFin} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
