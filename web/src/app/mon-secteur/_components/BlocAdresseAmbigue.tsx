import Link from "next/link";
import type { SuggestionAdresse } from "@/lib/types";

// État "adresse ambiguë" : la saisie soumise sans passer par le menu
// d'autocomplétion (Entrée directe, ou "Trouver mon secteur" sans cliquer
// une suggestion) correspond à plusieurs communes distinctes — on demande
// explicitement de choisir plutôt que de résoudre sur le premier résultat
// BAN (cf. étude du 2026-07-23 : le score de confiance ne distingue pas une
// adresse précise d'une adresse ambiguë entre communes).
export function BlocAdresseAmbigue({ suggestions }: { suggestions: SuggestionAdresse[] }) {
  return (
    <div className="rounded-[20px] border-[1.5px] border-[#F0D9A8] bg-white p-5.5">
      <div className="flex items-start gap-3.5">
        <span className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-attention font-baloo text-xl font-extrabold text-white shadow-[0_5px_13px_rgba(176,116,26,.28)]">
          ?
        </span>
        <div className="flex-1">
          <div className="font-baloo text-xl font-extrabold text-texte">
            Votre adresse correspond à plusieurs endroits différents
          </div>
          <p className="mt-1.5 text-[13.5px] leading-relaxed text-[#6A5A3E]">
            Plutôt que de deviner, laquelle est la vôtre ?
          </p>
          <div className="mt-3.5 flex flex-col gap-2">
            {suggestions.map((s) => (
              <Link
                key={s.label}
                href={`/mon-secteur?adresse=${encodeURIComponent(s.label)}`}
                className="flex items-center gap-2.5 rounded-xl border-[1.5px] border-filet bg-white px-4 py-2.5 text-[13px] font-semibold text-texte hover:border-action hover:bg-action-pale"
              >
                <span className="flex-none text-[13px] text-texte-doux">📍</span>
                {s.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
