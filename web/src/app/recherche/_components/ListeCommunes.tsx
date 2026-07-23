"use client";

import { useState } from "react";
import type { CommuneRecherche } from "@/lib/types";
import { hrefCommune } from "@/lib/hrefsGeo";
import { CarteCommune } from "./CarteCommune";
import { SelectFiltre } from "@/components/SelectFiltre";
import { BoutonDirectionTri, type DirectionTri } from "@/components/BoutonDirectionTri";
import type { TriCommunes } from "@/lib/rechercheParams";

// Nombre de communes affichées avant dépliage — à ajuster ici si besoin.
// Plafonné pour qu'une recherche à beaucoup de communes homonymes (ex:
// "saint") ne force pas à scroller une longue liste avant d'atteindre les
// établissements, qui précèdent cette section sur /recherche.
const APERCU_COMMUNES = 5;

export function ListeCommunes({
  communes,
  tri,
  direction,
  onTriChange,
}: {
  communes: CommuneRecherche[];
  tri: TriCommunes;
  direction: DirectionTri;
  // Le tri est calculé côté API (cf. agent/tools/recherche_tool.py::
  // _order_by_communes) : un tri purement client sur ce lot déjà tronqué à
  // 50 masquerait les vraies communes en tête pour un critère différent de
  // celui utilisé par le LIMIT — même raison que pour les établissements
  // (Phase 6). `onTriChange` relance donc l'appel /recherche.
  onTriChange: (tri: TriCommunes, direction: DirectionTri) => void;
}) {
  const [depliee, setDepliee] = useState(false);
  const communesAffichees = depliee ? communes : communes.slice(0, APERCU_COMMUNES);
  const nbMasquees = communes.length - communesAffichees.length;

  return (
    <div className="mt-2.5">
      <div className="mb-2.5 flex items-center justify-end gap-1.5 text-[11px] font-semibold text-texte-doux">
        <span>Trier :</span>
        <SelectFiltre value={tri} onChange={(v) => onTriChange(v as TriCommunes, direction)} actif={false}>
          <option value="alphabetique">Alphabétique</option>
          <option value="reussite">Réussite</option>
          <option value="nb_etablissements">Nb. collèges</option>
        </SelectFiltre>
        <BoutonDirectionTri
          direction={direction}
          onToggle={() => onTriChange(tri, direction === "desc" ? "asc" : "desc")}
        />
      </div>

      <div className="flex flex-col gap-2.5">
        {communesAffichees.map((c) => (
          <CarteCommune key={`${c.commune}-${c.code_departement}`} commune={c} href={hrefCommune(c)} />
        ))}
        {!depliee && nbMasquees > 0 && (
          <button
            type="button"
            onClick={() => setDepliee(true)}
            className="cursor-pointer rounded-[13px] border-[1.5px] border-dashed border-filet-fonce py-2.5 text-center text-[12.5px] font-semibold text-texte-doux hover:border-action hover:text-action"
          >
            Voir {nbMasquees} commune{nbMasquees > 1 ? "s" : ""} de plus
          </button>
        )}
      </div>
    </div>
  );
}
