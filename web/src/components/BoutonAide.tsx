"use client";

import { useState, type ReactNode } from "react";

// Bouton d'aide contextuelle : l'explication n'est affichée nulle part par
// défaut, révélée au clic — popover accessible (aria-expanded, focusable),
// pas un simple `title` (survol seul, inaccessible au clavier).
export function BoutonAide({
  texte,
  alignementDroite = false,
  decalageHaut = "top-6",
}: {
  texte: ReactNode;
  // Aligne la popup sur le bord droit du bouton plutôt que le gauche —
  // utile quand le bouton est proche du bord droit de son conteneur
  // (ex: surimpression sur un coin de badge) pour éviter le débordement.
  alignementDroite?: boolean;
  // Classe Tailwind de décalage vertical de la popup. Par défaut elle
  // s'ouvre juste sous le bouton — mais quand le bouton est en
  // surimpression sur un élément plus grand que lui (coin d'un badge),
  // ce décalage doit être augmenté pour que la popup s'ouvre sous cet
  // élément entier, pas seulement sous le bouton, sans quoi elle le
  // recouvre pendant qu'elle est ouverte.
  decalageHaut?: string;
}) {
  const [ouvert, setOuvert] = useState(false);
  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setOuvert((v) => !v)}
        aria-expanded={ouvert}
        aria-label="Qu'est-ce que ça veut dire ?"
        className="inline-flex h-4 w-4 cursor-pointer items-center justify-center rounded-full border border-filet-fonce bg-white text-[10px] font-bold leading-none text-texte-doux"
      >
        ?
      </button>
      {ouvert && (
        <span
          className={`absolute ${decalageHaut} z-[1100] w-60 rounded-xl border border-filet bg-white p-2.5 text-[11px] font-normal leading-relaxed text-texte-doux shadow-lg ${
            alignementDroite ? "right-0" : "left-0"
          }`}
        >
          {texte}
        </span>
      )}
    </span>
  );
}
