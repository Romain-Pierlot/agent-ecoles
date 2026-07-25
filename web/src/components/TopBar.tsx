"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NOM_ASSISTANT } from "@/lib/constants";
import { GaletAgent } from "@/components/GaletAgent";
import { RechercheChamp } from "@/components/RechercheChamp";
import { RechercheMobile } from "@/components/RechercheMobile";

// Remplacement de src/components/TopBar.tsx
// Changements refonte :
//  - logo : coin net (rounded-[9px]) sans rotation « bancale » (-rotate-6 retiré)
//  - marque « écoles » en font-titre (Newsreader) au lieu de font-baloo
//  - nav en font-ui
//  - CTA agent : IDENTITÉ APRICOT dédiée (pilule bg-agent-pale + galet
//    apricot), distincte du terracotta d'action — on repère l'agent sans
//    qu'il prenne le pas sur les actions produit.
//
// Ajout état actif/hover/focus :
//  - "match" distinct de "href" pour Comprendre, dont la destination réelle
//    est /comprendre/ips mais dont toutes les sous-pages /comprendre/[slug]
//    doivent allumer l'item.
//  - Composant passé en client : usePathname n'existe pas côté serveur.
//
// Refonte recherche : le lien nav "Rechercher" disparaît, remplacé par un
// champ permanent (RechercheChamp, desktop) et une icône plein écran
// (RechercheMobile, <md) — c'est le champ qui mène à /recherche, plus le
// lien. Voir lib/rechercheMenu.ts pour la logique partagée.

type LienNav = { href: string; label: string; match?: string };

const LIENS_NAV: LienNav[] = [
  { href: "/carte-scolaire", label: "Carte scolaire" },
  { href: "/explorer", label: "Explorer" },
  { href: "/comprendre/ips", label: "Comprendre", match: "/comprendre" },
];

const CLASSES_COMMUNES =
  "font-ui text-[13px] font-semibold rounded-sm underline-offset-[6px] outline-none " +
  "focus-visible:ring-2 focus-visible:ring-action focus-visible:ring-offset-[3px] focus-visible:ring-offset-fond-creme";

export function TopBar() {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-40 h-16 flex-none border-b border-filet bg-fond-creme">
      <div className="mx-auto flex h-full max-w-6xl items-center gap-5 px-4 md:px-8">
        <Link href="/" className="flex flex-none items-center gap-2.5">
          <div className="h-[26px] w-[26px] rounded-[9px] bg-action" />
          <span className="font-titre text-[22px] font-semibold text-texte">écoles</span>
        </Link>

        {/* Masqué sous md : RechercheMobile prend le relais (recherche
            plein écran) côté mobile. */}
        <div className="hidden flex-1 md:flex">
          <RechercheChamp />
        </div>

        <div className="ml-auto flex flex-none items-center gap-5.5">
          <div className="hidden items-center gap-5.5 font-ui text-[13px] font-semibold text-texte-doux md:flex">
            {LIENS_NAV.map((lien) => {
              const base = lien.match ?? lien.href;
              const actif = pathname === base || pathname.startsWith(`${base}/`);

              return (
                <Link
                  key={lien.href}
                  href={lien.href}
                  aria-current={actif ? "page" : undefined}
                  className={
                    actif
                      ? `${CLASSES_COMMUNES} text-texte font-bold underline decoration-2 decoration-action`
                      : `${CLASSES_COMMUNES} text-texte-doux hover:text-texte hover:underline hover:decoration-2 hover:decoration-action/35`
                  }
                >
                  {lien.label}
                </Link>
              );
            })}
          </div>
          <RechercheMobile />
          <Link
            href="/assistant"
            className="flex items-center gap-2 rounded-full border border-agent bg-agent-pale py-2 pl-[7px] pr-[15px] font-ui text-[12.5px] font-bold text-agent-ink outline-none hover:border-agent-dark focus-visible:ring-2 focus-visible:ring-action focus-visible:ring-offset-[3px] focus-visible:ring-offset-fond-creme"
          >
            <GaletAgent taille="mini" />
            Demander à {NOM_ASSISTANT}
          </Link>
        </div>
      </div>
    </div>
  );
}
