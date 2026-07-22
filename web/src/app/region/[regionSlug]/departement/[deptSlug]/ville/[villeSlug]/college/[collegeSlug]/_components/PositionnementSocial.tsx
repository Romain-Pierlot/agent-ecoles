"use client";

import type { PositionnementSocial as PositionnementSocialType } from "@/lib/types";
import { BoutonAide } from "@/components/BoutonAide";

// Jauge en barre de progression + marqueur circulaire — le curseur est
// centré via `top-1/2 -translate-y-1/2` (transform CSS), pas via un calcul
// manuel de pixels : robuste par construction, ne peut pas désaligner comme
// la version précédente (top-0.5 estimé à la main).
function Jauge({
  valeur,
  national,
  plancher,
  plafond,
  labelGauche,
  labelDroite,
}: {
  valeur: number;
  national: number | null;
  plancher: number;
  plafond: number;
  labelGauche: string;
  labelDroite: string;
}) {
  const echelle = plafond - plancher || 1;
  const position = (v: number) => Math.min(100, Math.max(0, ((v - plancher) / echelle) * 100));
  const pctValeur = position(valeur);

  return (
    <div className="mt-4">
      <div className="relative h-2.5 rounded-full bg-descriptif-pale shadow-[inset_0_1px_2px_rgba(58,90,140,0.12)]">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-descriptif/45 to-descriptif"
          style={{ width: `${pctValeur}%` }}
        />
        {/* Repère national : couleur pleine et contrastée (le blanc
            précédent était invisible sur le fond clair de la jauge) —
            dépasse légèrement de la piste pour rester lisible même quand
            le remplissage passe dessous. */}
        {national != null && (
          <div
            className="absolute top-1/2 h-6 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-texte"
            style={{ left: `${position(national)}%` }}
          />
        )}
        <div
          className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-white bg-descriptif shadow-[0_2px_6px_rgba(58,90,140,0.55),0_0_0_4px_rgba(58,90,140,0.14)]"
          style={{ left: `${pctValeur}%` }}
        />
      </div>
      {/* Bornes de l'échelle uniquement — pas de catégorie ni de seuil
          jugé : aucune source officielle DEPP ne définit de découpage
          "favorisé/défavorisé", donc on affiche juste les deux extrémités
          de l'axe et on laisse chacun situer l'établissement. */}
      <div className="mt-1.5 flex items-baseline justify-between text-[9.5px] font-semibold text-texte-doux/60">
        <span>{labelGauche}</span>
        <span>{labelDroite}</span>
      </div>
      {national != null && (
        <div className="relative mt-1 h-3.5">
          <span
            className="absolute -translate-x-1/2 whitespace-nowrap text-[10px] font-semibold text-texte-doux"
            style={{ left: `${position(national)}%` }}
          >
            Moyenne nationale : {national.toFixed(0)}
          </span>
        </div>
      )}
    </div>
  );
}

export function PositionnementSocial({ positionnementSocial }: { positionnementSocial: PositionnementSocialType | null }) {
  if (!positionnementSocial) return null;
  const { ips_moyen, ecart_type_ips, ips_national, ecart_type_ips_national } = positionnementSocial;

  return (
    <div id="social" className="mt-4 scroll-mt-28">
      <div className="font-baloo text-[25px] font-extrabold text-texte">Le milieu social des élèves</div>

      <div className="mt-4 grid gap-3.5 sm:grid-cols-2">
        {ips_moyen != null && (
          <div className="rounded-[18px] border-2 border-filet bg-white p-[18px_20px]">
            <div className="flex items-center text-[13px] font-bold text-texte">
              Indice de position sociale (IPS)
              <BoutonAide texte="L'IPS résume les conditions socio-économiques et culturelles moyennes des familles des élèves, déterminées à partir de la profession des parents : plus il est élevé, plus ces conditions sont en moyenne favorables à la scolarité." />
            </div>
            <div className="mt-1 font-baloo text-[34px] font-extrabold leading-none text-descriptif">
              {ips_moyen.toFixed(0)}
            </div>
            <Jauge
              valeur={ips_moyen}
              national={ips_national}
              plancher={50}
              plafond={180}
              labelGauche="Très défavorisé"
              labelDroite="Très favorisé"
            />
          </div>
        )}

        {ecart_type_ips != null && (
          <div className="rounded-[18px] border-2 border-filet bg-white p-[18px_20px]">
            <div className="flex items-center text-[13px] font-bold text-texte">
              Mixité sociale
              <BoutonAide texte="L'écart-type mesure la diversité des profils sociaux au sein du collège : plus il est élevé, plus les familles des élèves sont différentes socialement (grande mixité) ; plus il est bas, plus elles se ressemblent (population homogène)." />
            </div>
            <div className="mt-1 font-baloo text-[34px] font-extrabold leading-none text-descriptif">
              {ecart_type_ips.toFixed(1)}
            </div>
            <Jauge
              valeur={ecart_type_ips}
              national={ecart_type_ips_national}
              plancher={10}
              plafond={45}
              labelGauche="Peu mixte"
              labelDroite="Très mixte"
            />
          </div>
        )}
      </div>
    </div>
  );
}
