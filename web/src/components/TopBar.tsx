import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";
import { GaletCamille } from "@/components/GaletCamille";

// Remplacement de src/components/TopBar.tsx
// Changements refonte :
//  - logo : coin net (rounded-[9px]) sans rotation « bancale » (-rotate-6 retiré)
//  - marque « écoles » en font-titre (Newsreader) au lieu de font-baloo
//  - nav en font-ui
//  - CTA Camille : IDENTITÉ APRICOT dédiée (pilule bg-camille-pale + point
//    apricot), distincte du terracotta d'action — on repère l'agent sans
//    qu'il prenne le pas sur les actions produit.
export function TopBar() {
  return (
    <div className="sticky top-0 z-40 h-16 flex-none border-b border-filet bg-fond-creme">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between px-4 md:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="h-[26px] w-[26px] rounded-[9px] bg-action" />
          <span className="font-titre text-[22px] font-semibold text-texte">écoles</span>
        </Link>
        <div className="flex items-center gap-5.5">
          <div className="hidden items-center gap-5.5 font-ui text-[13px] font-semibold text-texte-doux md:flex">
            <Link href="/recherche" className="hover:text-texte">Rechercher</Link>
            <Link href="/carte-scolaire" className="hover:text-texte">Carte scolaire</Link>
            <Link href="/explorer" className="hover:text-texte">Explorer</Link>
            <Link href="/comprendre/ips" className="hover:text-texte">Comprendre</Link>
          </div>
          <Link
            href="/assistant"
            className="flex items-center gap-2 rounded-full border border-camille bg-camille-pale py-2 pl-[7px] pr-[15px] font-ui text-[12.5px] font-bold text-camille-ink"
          >
            <GaletCamille taille="mini" />
            Demander à {NOM_ASSISTANT}
          </Link>
        </div>
      </div>
    </div>
  );
}
