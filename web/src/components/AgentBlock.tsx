import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";
import { GaletCamille } from "@/components/GaletCamille";

// Composant transverse unique (hub région, hub département, page ville —
// cf. docs/Design_system/hub_departement_comparateur/README.md). Seul
// `exemple` change d'un écran à l'autre. Identité visuelle : accents
// apricot dédiés à Camille (avatar, bouton, bordures), jamais --color-action
// (cf. refonte terracotta), jamais de fond plein sur toute la carte, champ
// de saisie toujours blanc (cf. règle "à ne pas faire" du README).
export function AgentBlock({
  exemple,
  titre = `Demander à ${NOM_ASSISTANT}`,
  sousTitre = "Posez votre situation en une phrase",
}: {
  exemple: string;
  // Optionnels : la page collège de secteur fait varier le titre/sous-titre
  // selon l'état (trouvé/multi-secteur/non déterminable) — cf.
  // docs/Design_system/recherche/README.md, à mettre à jour (la règle "seul
  // le prop example change" n'est plus exacte). Défauts = valeurs
  // historiques, aucun des 3 usages existants (recherche, page ville,
  // ZoneHub) n'a besoin de changer.
  titre?: string;
  sousTitre?: string;
}) {
  return (
    <div className="mt-4 rounded-2xl border border-camille bg-gradient-to-br from-camille-pale to-fond-carte p-4">
      <div className="flex items-center gap-2.5">
        <GaletCamille taille="carte" />
        <div>
          <div className="font-titre text-sm font-semibold text-texte">{titre}</div>
          <div className="text-[11px] font-semibold text-texte-doux">{sousTitre}</div>
        </div>
      </div>

      <Link
        href="/assistant"
        className="mt-3 flex items-center gap-2.5 rounded-[11px] border border-camille bg-white px-3.5 py-2.5 text-[12px] font-medium text-texte-doux hover:border-camille-dark"
      >
        <span className="flex-1">{exemple}</span>
        <span className="flex-none rounded-lg bg-camille-dark px-3 py-1.5 text-[11px] font-extrabold text-white">
          Demander →
        </span>
      </Link>
    </div>
  );
}
