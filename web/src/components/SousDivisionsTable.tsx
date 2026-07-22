"use client";

import Link from "next/link";
import { useState } from "react";
import type { LigneSousDivision } from "@/components/ZoneHub";
import { BoutonAide } from "@/components/BoutonAide";

const NB_AFFICHEES_INITIALEMENT = 15;

function ChipNotation({ notation }: { notation: string | null }) {
  if (!notation) {
    return (
      <span className="inline-flex items-center text-[11px] font-semibold text-texte-doux/50">
        n/d
        <BoutonAide texte="La notation combine le taux de réussite, la note à l'écrit et la valeur ajoutée du collège. Sans valeur ajoutée publiée par le Ministère pour ce collège cette session, la notation ne peut pas être calculée — même si le collège a de bons résultats bruts (visibles dans la colonne Réussite)." />
      </span>
    );
  }
  const estPositif = notation.startsWith("A");
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-[11.5px] font-bold ${
        estPositif ? "bg-positif-pale text-positif" : "bg-attention-pale text-attention-dark"
      }`}
    >
      {notation}
    </span>
  );
}

function formaterTaux(taux: number | null): string {
  return taux === null ? "—" : `${taux.toFixed(0)} %`;
}

export function SousDivisionsTable({
  labelColonne,
  sousDivisions,
}: {
  labelColonne: string;
  sousDivisions: LigneSousDivision[];
}) {
  const [toutAfficher, setToutAfficher] = useState(false);
  const affichees = toutAfficher ? sousDivisions : sousDivisions.slice(0, NB_AFFICHEES_INITIALEMENT);
  const nbRestantes = sousDivisions.length - affichees.length;

  return (
    <div className="mt-2.5 overflow-hidden rounded-xl border-[1.5px] border-filet">
      <div className="grid grid-cols-[1fr_70px_92px_66px_18px] gap-2 bg-fond-carte px-4 py-2 text-[9.5px] font-bold uppercase tracking-wide text-texte-doux">
        <span>{labelColonne}</span>
        <span className="text-right">Collèges</span>
        <span className="text-center">Notation médiane</span>
        <span className="text-right">Réussite</span>
        <span />
      </div>
      {affichees.map((sd) => (
        <Link
          key={sd.code}
          href={sd.href}
          className="grid grid-cols-[1fr_70px_92px_66px_18px] items-center gap-2 border-t border-[#F0E6D2] px-4 py-2.5 hover:bg-fond-carte/60"
        >
          <span className="truncate text-[13px] font-bold text-texte">{sd.libelle}</span>
          <span className="text-right font-baloo text-[13px] font-bold text-texte">
            {sd.nb_etablissements}
          </span>
          <span className="text-center">
            <ChipNotation notation={sd.notation_mediane} />
          </span>
          <span className="text-right text-[12.5px] font-semibold text-texte-doux">
            {formaterTaux(sd.taux_reussite_moyen)}
          </span>
          <span className="text-right text-[14px] text-filet-fonce">›</span>
        </Link>
      ))}
      {nbRestantes > 0 && (
        <button
          type="button"
          onClick={() => setToutAfficher(true)}
          className="w-full border-t border-[#F0E6D2] py-2.5 text-center text-[12.5px] font-bold text-action hover:bg-fond-carte/60"
        >
          Voir les {nbRestantes} {labelColonne.toLowerCase()}s restant{nbRestantes > 1 ? "e" : ""}s
        </button>
      )}
    </div>
  );
}
