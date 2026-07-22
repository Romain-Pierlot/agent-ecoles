import Link from "next/link";
import type { AgregatEtablissements, SousDivision } from "@/lib/types";
import { AgentBlock } from "@/components/AgentBlock";
import { RechercheBloc } from "@/components/RechercheBloc";
import { SousDivisionsTable } from "@/components/SousDivisionsTable";

export type LigneSousDivision = SousDivision & { href: string };

export function ZoneHub({
  filAriane,
  eyebrow,
  titre,
  sousTitre,
  global,
  labelColonneSousDivision,
  sousDivisions,
  exempleAgent,
}: {
  filAriane: { label: string; href?: string }[];
  eyebrow: string;
  titre: string;
  sousTitre: string;
  global: AgregatEtablissements;
  labelColonneSousDivision: string;
  sousDivisions: LigneSousDivision[];
  exempleAgent: string;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-4.5 md:px-8">
      {/* ===== FIL D'ARIANE ===== */}
      <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
        {filAriane.map((item, index) => (
          <span key={item.label} className="flex items-center gap-1.5">
            {index > 0 && <span className="text-filet-fonce">›</span>}
            {item.href ? (
              <Link href={item.href} className="hover:text-texte-doux">
                {item.label}
              </Link>
            ) : (
              <span className="text-texte">{item.label}</span>
            )}
          </span>
        ))}
      </div>

      {/* ===== HERO ===== */}
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">{eyebrow}</span>
          <h1 className="mt-1 font-baloo text-[30px] font-extrabold leading-tight text-texte">{titre}</h1>
          <p className="mt-1.5 text-[12.5px] text-texte-doux">{sousTitre}</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-baloo text-[22px] font-extrabold text-texte">{global.nb_etablissements}</div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Collèges</div>
          </div>
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-baloo text-[22px] font-extrabold text-positif">
              {global.taux_reussite_moyen !== null ? `${global.taux_reussite_moyen.toFixed(0)} %` : "—"}
            </div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Réussite moyenne</div>
          </div>
        </div>
      </div>

      <RechercheBloc />

      {/* ===== LISTE SOUS-DIVISIONS ===== */}
      <div className="mt-7">
        <h2 className="font-baloo text-[15px] font-extrabold text-texte">{labelColonneSousDivision}s</h2>
        <SousDivisionsTable labelColonne={labelColonneSousDivision} sousDivisions={sousDivisions} />
      </div>

      <AgentBlock exemple={exempleAgent} />
    </div>
  );
}
