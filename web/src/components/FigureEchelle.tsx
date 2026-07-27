import type { FigureEchelle as FigureEchelleType } from "@/lib/comprendre";

// Figure de repère positionnel (ex. échelle IPS) — au plus une par guide,
// cf. gabarit de lecture du bundle design_handoff_comprendre.
export function FigureEchelle({ figure }: { figure: FigureEchelleType }) {
  const { min, max, graduations, moitieCentrale, reperes } = figure;
  const total = max - min;
  const pct = (valeur: number) => ((valeur - min) / total) * 100;

  return (
    <div className="mb-6.5 rounded-[14px] border border-filet-fonce bg-fond-carte px-5.5 pt-5 pb-4.5">
      <div className="flex justify-between font-ui text-[12px] font-semibold text-texte-doux">
        {graduations.map((graduation) => (
          <span key={graduation}>{graduation}</span>
        ))}
      </div>

      <div className="relative mt-2.5 h-3.5 rounded-[7px] border border-filet bg-fond-encart">
        <div
          className="absolute top-0 bottom-0 rounded-[7px] bg-figure-plage"
          style={{
            left: `${pct(moitieCentrale[0])}%`,
            width: `${pct(moitieCentrale[1]) - pct(moitieCentrale[0])}%`,
          }}
        />
        {reperes.map((repere) => (
          <div
            key={repere.label}
            className={`absolute -top-1.5 -bottom-1.5 w-[3px] rounded-sm ${repere.accent ? "bg-texte" : "bg-figure-repere"}`}
            style={{ left: `${pct(repere.valeur)}%` }}
          />
        ))}
      </div>

      <div className="mt-3.5 flex flex-wrap gap-6.5">
        {reperes.map((repere) => (
          <div key={repere.label} className="flex items-center gap-2">
            <span className={`h-3.5 w-[3px] flex-none rounded-sm ${repere.accent ? "bg-texte" : "bg-figure-repere"}`} />
            <span className="font-ui text-[12.5px] font-semibold text-texte">
              {repere.label} : {repere.valeur}
            </span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-4 flex-none border border-filet bg-figure-plage" />
          <span className="font-ui text-[12.5px] font-medium text-texte-doux">Moitié centrale des collèges publics</span>
        </div>
      </div>
    </div>
  );
}
