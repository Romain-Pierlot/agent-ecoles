"use client";

import { useState } from "react";
import { LigneGuide } from "@/components/LigneGuide";
import type { Guide } from "@/lib/comprendre";

// Corps de la page catégorie : pastilles "Filtrer" à partir de 6 guides
// (règle B du bundle), groupage par sous-thème en intertitres si la
// catégorie en a. Composant client isolé : le filtre réduit la liste sans
// rechargement, le reste de la page (page.tsx) reste un composant serveur.
export function ListeGuidesCategorie({ guides, sousThemes }: { guides: Guide[]; sousThemes?: string[] }) {
  const [filtre, setFiltre] = useState<string | null>(null);

  const guidesAffiches = filtre ? guides.filter((g) => g.sousTheme === filtre) : guides;

  const groupes: { sousTheme: string | undefined; guides: Guide[] }[] = sousThemes
    ? sousThemes
        .map((sousTheme) => ({ sousTheme, guides: guidesAffiches.filter((g) => g.sousTheme === sousTheme) }))
        .filter((groupe) => groupe.guides.length > 0)
    : [{ sousTheme: undefined, guides: guidesAffiches }];

  return (
    <div className="overflow-hidden rounded-2xl border border-filet-fonce bg-fond-carte">
      {sousThemes && guides.length >= 6 && (
        <div className="flex flex-wrap items-center gap-2 border-b border-filet bg-fond-entete-carte px-6 pt-4 pb-3.5">
          <span className="mr-0.5 flex-none font-ui text-[10px] font-bold tracking-[.09em] text-texte-doux uppercase">
            Filtrer
          </span>
          <button
            type="button"
            onClick={() => setFiltre(null)}
            className={`rounded-full px-3.5 py-1.5 font-ui text-[12.5px] font-bold ${
              filtre === null ? "bg-action text-white" : "border border-filet-fonce bg-fond-carte text-texte"
            }`}
          >
            Tout ({guides.length})
          </button>
          {sousThemes.map((sousTheme) => {
            const compte = guides.filter((g) => g.sousTheme === sousTheme).length;
            if (compte === 0) return null;
            return (
              <button
                key={sousTheme}
                type="button"
                onClick={() => setFiltre(sousTheme)}
                className={`rounded-full px-3.5 py-1.5 font-ui text-[12.5px] font-semibold ${
                  filtre === sousTheme ? "bg-action text-white" : "border border-filet-fonce bg-fond-carte text-texte"
                }`}
              >
                {sousTheme} ({compte})
              </button>
            );
          })}
        </div>
      )}

      {groupes.map((groupe, indexGroupe) => (
        <div key={groupe.sousTheme ?? "sans-sous-theme"}>
          {groupe.sousTheme && (
            <div className={`px-6 pt-4.5 pb-1.5 ${indexGroupe > 0 ? "border-t border-filet" : ""}`}>
              <div className="font-ui text-[11px] font-bold tracking-[.09em] text-texte-doux uppercase">
                {groupe.sousTheme}
              </div>
            </div>
          )}
          {groupe.guides.map((guide, i) => (
            <div key={guide.slug} className={i > 0 ? "border-t border-filet" : undefined}>
              <LigneGuide guide={guide} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
