"use client";

import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { useXAxisScale, useYAxisScale } from "recharts";
import type { EvolutionPoint } from "@/lib/types";
import { formaterPourcentage } from "@/lib/format";

// Échelle verticale volontairement fixe (70-100, pas de 10) plutôt que
// calée sur le min/max de l'établissement affiché : sur les données
// réelles, 96,6% des couples collège-session sont ≥ 70%, donc ce cadre
// suffit à l'immense majorité des fiches sans jamais les tronquer. Pour
// les 9,5% de collèges dont au moins une session descend sous 70%
// (vérifié empiriquement), le plancher descend d'un palier de 10 à la
// fois (60, 50...) — jamais le plafond, toujours fixé à 100. Un plancher
// unique et bas pour tout le monde écraserait la variation normale des
// 90% de fiches qui n'en ont pas besoin ; un plancher toujours strict à
// 70 tronquerait silencieusement les cas réellement en difficulté, ce
// qui serait plus grave qu'un écart mineur exagéré à l'œil.
const PLANCHER_MINIMUM = 30;
const PAS_PALIER = 10;
const PLAFOND = 100;

function calculerPlancher(valeurs: number[]): number {
  const min = Math.min(...valeurs);
  let plancher = 70;
  while (min < plancher && plancher > PLANCHER_MINIMUM) {
    plancher -= PAS_PALIER;
  }
  return plancher;
}

type PointGraphe = { session: string; taux: number; national: number | null };

// Rendu à part (plutôt qu'un `label` sur la barre) : il faut la vraie
// échelle du graphique pour savoir à quelle hauteur pixel se place le
// point national, sinon deux barres de valeur identique (ex. deux fois
// "90%") peuvent afficher leur libellé à des hauteurs différentes selon
// la seule comparaison des valeurs brutes — c'est ce qui produisait le
// rendu incohérent observé. `useXAxisScale`/`useYAxisScale` donnent accès
// à cette échelle depuis n'importe quel enfant du graphique.
function EtiquettesValeurs({ donnees }: { donnees: PointGraphe[] }) {
  const xScale = useXAxisScale();
  const yScale = useYAxisScale();
  if (!xScale || !yScale) return null;

  return (
    <>
      {donnees.map((d) => {
        const xCentre = xScale(d.session, { position: "middle" });
        const yBarre = yScale(d.taux);
        if (xCentre == null || yBarre == null) return null;
        const yNational = d.national != null ? yScale(d.national) : undefined;
        const yPlusHaut = yNational != null ? Math.min(yBarre, yNational) : yBarre;
        return (
          <text
            key={d.session}
            x={xCentre}
            y={yPlusHaut - 10}
            textAnchor="middle"
            className="fill-positif text-[11px] font-bold"
          >
            {formaterPourcentage(d.taux, 0)}
          </text>
        );
      })}
    </>
  );
}

export function GraphiqueEvolutionTaux({ evolution }: { evolution: EvolutionPoint[] }) {
  const points = [...evolution].reverse().filter((p) => p.brevet_taux_reussite_general != null);
  if (points.length === 0) return null;

  const valeursEtab = points.map((p) => p.brevet_taux_reussite_general as number);
  const valeursNational = points
    .map((p) => p.brevet_taux_reussite_national)
    .filter((v): v is number => v != null);
  const plancher = calculerPlancher([...valeursEtab, ...valeursNational]);

  const graduations: number[] = [];
  for (let g = plancher; g <= PLAFOND; g += PAS_PALIER) graduations.push(g);

  const donnees: PointGraphe[] = points.map((p) => ({
    session: p.session,
    taux: p.brevet_taux_reussite_general as number,
    national: p.brevet_taux_reussite_national,
  }));
  const auMoinsUnNational = donnees.some((d) => d.national != null);

  return (
    <div className="rounded-[22px] border-2 border-filet bg-white p-[22px_24px]">
      <div className="mb-2 flex items-baseline justify-between">
        <div className="font-titre text-[15px] font-semibold text-texte">Évolution du taux de réussite</div>
        {auMoinsUnNational && (
          <div className="flex items-center gap-1.5 text-[10.5px] font-semibold text-texte-doux">
            <span className="inline-block h-0 w-3 border-t-[1.5px] border-dashed border-texte-doux" />
            National
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <ComposedChart data={donnees} margin={{ top: 24, right: 10, bottom: 0, left: 0 }} barCategoryGap="20%">
          <defs>
            <linearGradient id="gradientBarreEvolution" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="var(--color-mention-b)" />
              <stop offset="100%" stopColor="var(--color-positif)" />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--color-filet)" />
          <XAxis
            dataKey="session"
            tickLine={false}
            axisLine={false}
            tickMargin={10}
            tick={{ fontSize: 11, fontWeight: 600, fill: "var(--color-texte-doux)" }}
          />
          <YAxis
            domain={[plancher, PLAFOND]}
            ticks={graduations}
            tickLine={false}
            axisLine={false}
            width={34}
            tick={{ fontSize: 10.5, fontWeight: 600, fill: "var(--color-texte-doux)" }}
          />
          <Bar dataKey="taux" fill="url(#gradientBarreEvolution)" radius={[8, 8, 0, 0]} maxBarSize={96} isAnimationActive={false} />
          {auMoinsUnNational && (
            <Line
              type="linear"
              dataKey="national"
              stroke="var(--color-texte-doux)"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              dot={{ r: 3, fill: "var(--color-texte-doux)", strokeWidth: 0 }}
              connectNulls
              isAnimationActive={false}
            />
          )}
          <EtiquettesValeurs donnees={donnees} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
