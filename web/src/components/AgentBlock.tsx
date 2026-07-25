import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";
import { GaletAgent } from "@/components/GaletAgent";

// Composant transverse unique (hub région, hub département, page ville,
// carte scolaire, fiche établissement). Seul `exemple` (et `titre`/
// `sousTitre`) change d'un écran à l'autre. Identité visuelle : accents
// apricot dédiés à l'agent (icône, bouton, bordures), jamais --color-action
// (cf. docs/Design_system/REFERENCE.md), jamais de fond plein sur toute la
// carte, champ de saisie toujours blanc.
export function AgentBlock({
  exemple,
  titre = `Demander à ${NOM_ASSISTANT}`,
  sousTitre = "Posez votre situation en une phrase",
}: {
  exemple: string;
  // Optionnels : la page carte scolaire fait varier le titre/sous-titre
  // selon l'état (trouvé/multi-secteur/non déterminable/adresse ambiguë) —
  // la règle "seul le prop exemple change" ne vaut donc que pour les autres
  // usages (recherche, page ville, ZoneHub, fiche établissement).
  titre?: string;
  sousTitre?: string;
}) {
  return (
    <div className="mt-4 rounded-2xl border border-agent bg-gradient-to-br from-agent-pale to-fond-carte p-4">
      <div className="flex items-center gap-2.5">
        <GaletAgent taille="carte" />
        <div>
          <div className="font-titre text-sm font-semibold text-texte">{titre}</div>
          <div className="text-[11px] font-semibold text-texte-doux">{sousTitre}</div>
        </div>
      </div>

      <Link
        href="/assistant"
        className="mt-3 flex items-center gap-2.5 rounded-[11px] border border-agent bg-white px-3.5 py-2.5 text-[12px] font-medium text-texte-doux hover:border-agent-dark"
      >
        <span className="flex-1">{exemple}</span>
        <span className="flex-none rounded-lg bg-agent-dark px-3 py-1.5 text-[11px] font-extrabold text-white">
          Demander →
        </span>
      </Link>
    </div>
  );
}
