"use client";

import { useState } from "react";
import type { CollegeVille } from "@/lib/types";
import { accorder } from "@/lib/format";
import { CarteCollege } from "./CarteCollege";

const NB_AFFICHES_INITIALEMENT = 15;

export function ListeColleges({
  colleges,
}: {
  // hrefBase porté par chaque collège (pas un seul partagé) : la page ville
  // a tous ses collèges sous le même hrefBase, mais la page recherche
  // affiche des collèges venant potentiellement de villes différentes,
  // chacun avec son propre chemin.
  // commune/libelle_departement/code_departement optionnels sur CollegeVille,
  // toujours présents sur EtablissementRecherche (/recherche) — la page ville
  // les fournit désormais explicitement (cf. ville/page.tsx) ; CarteCollege
  // affiche la ligne de localisation sur les deux pages dès qu'ils sont fournis.
  colleges: (CollegeVille & {
    hrefBase: string;
    commune?: string;
    libelle_departement?: string;
    code_departement?: string;
  })[];
}) {
  const [toutAfficher, setToutAfficher] = useState(false);
  const affiches = toutAfficher ? colleges : colleges.slice(0, NB_AFFICHES_INITIALEMENT);
  const nbRestants = colleges.length - affiches.length;

  return (
    <div className="mt-2.5 flex flex-col gap-2.5">
      {/* En-tête partagé des colonnes "chiffres" des cartes, dès le point de
          rupture sm : largeurs verrouillées sur celles de CarteCollege
          (150px/44px) pour rester aligné. Purement visuel (aria-hidden) —
          chaque carte porte déjà son propre libellé accessible (sr-only à
          partir de sm dans CarteCollege), donc un lecteur d'écran l'entend
          une fois par carte plutôt que de dépendre d'un en-tête lu une seule
          fois en haut de liste. Repli mobile : le libellé redevient visible
          directement dans la carte (CarteCollege), cet en-tête disparaît. */}
      <div className="mb-1 hidden items-center gap-3.5 px-3.5 sm:flex" aria-hidden="true">
        <div className="min-w-0 flex-1" />
        <div className="w-[150px] flex-none text-center text-[10px] font-bold uppercase tracking-wide text-texte-doux">
          Réussite au brevet
        </div>
        <div className="w-11 flex-none text-center text-[10px] font-bold uppercase tracking-wide text-texte-doux">
          Notation
        </div>
        <span className="invisible flex-none text-[15px]">›</span>
      </div>
      {affiches.map((c) => (
        <CarteCollege key={c.uai} college={c} hrefBase={c.hrefBase} />
      ))}
      {nbRestants > 0 && (
        <button
          type="button"
          onClick={() => setToutAfficher(true)}
          className="cursor-pointer rounded-[13px] border-[1.5px] border-filet bg-white py-2.5 text-center text-[12.5px] font-bold text-action hover:bg-fond-carte/60"
        >
          Voir les {nbRestants} {accorder(nbRestants, "collège")} {accorder(nbRestants, "restant")}
        </button>
      )}
    </div>
  );
}
