"use client";

import { useState } from "react";
import type { CollegeVille } from "@/lib/types";
import { CarteCollege } from "./CarteCollege";

const NB_AFFICHES_INITIALEMENT = 15;

export function ListeColleges({
  colleges,
  tauxReussiteNational,
  critereTriActif,
}: {
  // hrefBase porté par chaque collège (pas un seul partagé) : la page ville
  // a tous ses collèges sous le même hrefBase, mais la page recherche
  // affiche des collèges venant potentiellement de villes différentes,
  // chacun avec son propre chemin.
  colleges: (CollegeVille & { hrefBase: string })[];
  tauxReussiteNational: number | null;
  critereTriActif?: "notation" | "reussite";
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
          hrefBase={c.hrefBase}
          tauxReussiteNational={tauxReussiteNational}
          critereTriActif={critereTriActif}
        />
      ))}
      {nbRestants > 0 && (
        <button
          type="button"
          onClick={() => setToutAfficher(true)}
          className="cursor-pointer rounded-[13px] border-[1.5px] border-filet bg-white py-2.5 text-center text-[12.5px] font-bold text-action hover:bg-fond-carte/60"
        >
          Voir les {nbRestants} collèges restants
        </button>
      )}
    </div>
  );
}
