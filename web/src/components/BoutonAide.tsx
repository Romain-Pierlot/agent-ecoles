"use client";

import { useState } from "react";

// Bouton d'aide contextuelle : l'explication n'est affichée nulle part par
// défaut, révélée au clic — popover accessible (aria-expanded, focusable),
// pas un simple `title` (survol seul, inaccessible au clavier).
export function BoutonAide({ texte }: { texte: string }) {
  const [ouvert, setOuvert] = useState(false);
  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setOuvert((v) => !v)}
        aria-expanded={ouvert}
        aria-label="Qu'est-ce que ça veut dire ?"
        className="ml-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full border border-filet-fonce text-[10px] font-bold leading-none text-texte-doux"
      >
        ?
      </button>
      {ouvert && (
        <span className="absolute left-0 top-6 z-10 w-60 rounded-xl border border-filet bg-white p-2.5 text-[11px] font-normal leading-relaxed text-texte-doux shadow-lg">
          {texte}
        </span>
      )}
    </span>
  );
}
