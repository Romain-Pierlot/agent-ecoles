import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";

// Composant transverse unique (hub région, hub département, page ville —
// cf. docs/Design_system/hub_departement_comparateur/README.md). Seul
// `exemple` change d'un écran à l'autre. Identité visuelle : accents
// framboise (avatar, bouton, bordures), jamais de fond framboise plein sur
// toute la carte, champ de saisie toujours blanc (cf. règle "à ne pas
// faire" du README).
export function AgentBlock({ exemple }: { exemple: string }) {
  return (
    <div className="mt-4 rounded-2xl border border-[#F0C9D8] bg-gradient-to-br from-[#FCEDF2] to-fond-carte p-4">
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-action font-baloo text-[17px] font-extrabold text-white shadow-[0_3px_9px_rgba(168,44,88,0.28)]">
          {NOM_ASSISTANT.charAt(0)}
        </div>
        <div>
          <div className="font-baloo text-sm font-bold text-texte">Demander à {NOM_ASSISTANT}</div>
          <div className="text-[11px] font-semibold text-texte-doux">Posez votre situation en une phrase</div>
        </div>
      </div>

      <Link
        href="/assistant"
        className="mt-3 flex items-center gap-2.5 rounded-[11px] border border-[#F0C9D8] bg-white px-3.5 py-2.5 text-[12px] font-medium text-texte-doux hover:border-action"
      >
        <span className="flex-1">{exemple}</span>
        <span className="flex-none rounded-lg bg-action px-3 py-1.5 font-baloo text-[11px] font-extrabold text-white">
          Demander →
        </span>
      </Link>
    </div>
  );
}
