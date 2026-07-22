"use client";

import { useState } from "react";
import type { CollegeVille } from "@/lib/types";
import { CarteCollege } from "./CarteCollege";

const NB_AFFICHES_INITIALEMENT = 15;

export function ListeColleges({
  colleges,
  hrefBase,
  tauxReussiteNational,
}: {
  colleges: CollegeVille[];
  hrefBase: string;
  tauxReussiteNational: number | null;
}) {
  const [toutAfficher, setToutAfficher] = useState(false);
  const affiches = toutAfficher ? colleges : colleges.slice(0, NB_AFFICHES_INITIALEMENT);
  const nbRestants = colleges.length - affiches.length;

  return (
    <div className="mt-2.5 flex flex-col gap-2.5">
      {affiches.map((c) => (
        <CarteCollege
          key={c.uai}
          college={c}
          hrefBase={hrefBase}
          tauxReussiteNational={tauxReussiteNational}
        />
      ))}
      {nbRestants > 0 && (
        <button
          type="button"
          onClick={() => setToutAfficher(true)}
          className="rounded-[13px] border-[1.5px] border-filet bg-white py-2.5 text-center text-[12.5px] font-bold text-action hover:bg-fond-carte/60"
        >
          Voir les {nbRestants} collèges restants
        </button>
      )}
    </div>
  );
}
