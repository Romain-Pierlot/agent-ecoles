"use client";

export type DirectionTri = "asc" | "desc";

// Bouton ↓/↑ qui inverse le sens du tri — partagé entre la page ville et les
// tableaux hub, à côté d'un SelectFiltre qui choisit le critère.
export function BoutonDirectionTri({
  direction,
  onToggle,
}: {
  direction: DirectionTri;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex h-[26px] w-[26px] flex-none cursor-pointer items-center justify-center rounded-[9px] border-[1.5px] border-filet bg-white text-[12px] text-texte-doux hover:border-filet-fonce"
      title={
        direction === "desc"
          ? "Ordre décroissant — cliquer pour inverser"
          : "Ordre croissant — cliquer pour inverser"
      }
    >
      {direction === "desc" ? "↓" : "↑"}
    </button>
  );
}
