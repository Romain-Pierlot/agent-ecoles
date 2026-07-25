"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { LigneSousDivision } from "@/components/ZoneHub";
import { SelectFiltre } from "@/components/SelectFiltre";
import { BoutonDirectionTri, type DirectionTri } from "@/components/BoutonDirectionTri";

// Assez haut pour que régions (19) et départements (≤13 par région) s'affichent
// toujours en entier sans pagination — seule une liste de communes très
// dense (page département) peut dépasser ce seuil et déclencher "voir plus".
const NB_AFFICHEES_INITIALEMENT = 25;

type CritereTri = "alphabetique" | "nb_etablissements" | "reussite";

function formaterTaux(taux: number | null): string {
  return taux === null ? "—" : `${taux.toFixed(0)} %`;
}

export function SousDivisionsTable({
  labelColonne,
  sousDivisions,
  afficherCode = false,
}: {
  labelColonne: string;
  sousDivisions: LigneSousDivision[];
  // Désactivé par défaut : seul le listing des départements d'une région
  // affiche le code entre parenthèses (convention alignée sur RechercheBloc,
  // "Rhône (69)") — région et commune n'ont pas cette convention.
  afficherCode?: boolean;
}) {
  const [toutAfficher, setToutAfficher] = useState(false);
  const [critereTri, setCritereTri] = useState<CritereTri>("alphabetique");
  const [directionTri, setDirectionTri] = useState<DirectionTri>("asc");

  // Alphabétique par défaut, dans les deux sens — identique au tri déjà
  // effectué côté back (agreger_sous_divisions), donc l'ordre initial ne
  // change pas. Les valeurs manquantes (taux de réussite) restent en
  // dernier, quel que soit le sens, comme sur la page ville.
  const trie = useMemo(() => {
    return [...sousDivisions].sort((a, b) => {
      if (critereTri === "nb_etablissements") {
        const diff = b.nb_etablissements - a.nb_etablissements;
        return directionTri === "asc" ? -diff : diff;
      }
      if (critereTri === "reussite") {
        const ta = a.taux_reussite_moyen;
        const tb = b.taux_reussite_moyen;
        if (ta === null && tb === null) return 0;
        if (ta === null) return 1;
        if (tb === null) return -1;
        const diff = tb - ta;
        return directionTri === "asc" ? -diff : diff;
      }
      const diff = (a.libelle || "").localeCompare(b.libelle || "");
      return directionTri === "asc" ? diff : -diff;
    });
  }, [sousDivisions, critereTri, directionTri]);

  const affichees = toutAfficher ? trie : trie.slice(0, NB_AFFICHEES_INITIALEMENT);
  const nbRestantes = trie.length - affichees.length;

  return (
    <div className="mt-2.5">
      <div className="flex items-center justify-end gap-1.5 pb-1.5 text-[11px] font-semibold text-texte-doux">
        <span>Trier :</span>
        <SelectFiltre value={critereTri} onChange={(v) => setCritereTri(v as CritereTri)} actif={false}>
          <option value="alphabetique">Alphabétique</option>
          <option value="nb_etablissements">Collèges</option>
          <option value="reussite">Réussite</option>
        </SelectFiltre>
        <BoutonDirectionTri
          direction={directionTri}
          onToggle={() => setDirectionTri((d) => (d === "desc" ? "asc" : "desc"))}
        />
      </div>

      <div className="overflow-hidden rounded-xl border-[1.5px] border-filet">
        <div className="grid grid-cols-[1fr_70px_84px_18px] gap-2 bg-fond-carte px-4 py-2 text-[9.5px] font-bold uppercase tracking-wide text-texte-doux">
          <span>{labelColonne}</span>
          <span className="text-right">Collèges</span>
          <span className="text-right">Réussite moy.</span>
          <span />
        </div>
        {affichees.map((sd) => (
          <Link
            key={sd.code}
            href={sd.href}
            className="grid grid-cols-[1fr_70px_84px_18px] items-center gap-2 border-t border-[#F0E6D2] px-4 py-2.5 hover:bg-fond-carte/60"
          >
            <span className="min-w-0 truncate text-[13px] font-bold text-texte">
              {sd.libelle}
              {afficherCode ? ` (${sd.code})` : ""}
            </span>
            <span className="text-right font-ui text-[13px] font-bold text-texte">
              {sd.nb_etablissements}
            </span>
            <span className="text-right font-ui text-[14px] font-bold text-texte">
              {formaterTaux(sd.taux_reussite_moyen)}
            </span>
            <span className="text-right text-[14px] text-filet-fonce">›</span>
          </Link>
        ))}
        {nbRestantes > 0 && (
          <button
            type="button"
            onClick={() => setToutAfficher(true)}
            className="w-full cursor-pointer border-t border-[#F0E6D2] py-2.5 text-center text-[12.5px] font-bold text-action hover:bg-fond-carte/60"
          >
            Voir les {nbRestantes} {labelColonne.toLowerCase()}s restant{nbRestantes > 1 ? "e" : ""}s
          </button>
        )}
      </div>
    </div>
  );
}
