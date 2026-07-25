"use client";

// Menu déroulant natif stylé pour ressembler à une puce de filtre/tri — pas
// de popover personnalisé (accessibilité clavier/mobile gratuite). Partagé
// entre les filtres et le tri de la page ville et des tableaux hub.
export function classesFiltre(actif: boolean): string {
  return actif
    ? "border-[1.5px] border-action bg-action-pale text-action-dark"
    : "border-[1.5px] border-filet bg-white text-texte-doux";
}

export function SelectFiltre({
  value,
  onChange,
  actif,
  children,
}: {
  value: string;
  onChange: (v: string) => void;
  actif: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={`relative rounded-[9px] ${classesFiltre(actif)}`}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-transparent py-1.5 pl-2.5 pr-6 text-[11px] font-bold outline-none"
      >
        {children}
      </select>
      <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[9px]">▾</span>
    </div>
  );
}
