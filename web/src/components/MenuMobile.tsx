"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NOM_ASSISTANT } from "@/lib/constants";
import { LIENS_NAV } from "@/lib/navigation";
import { GaletAgent } from "@/components/GaletAgent";

// Menu de navigation mobile : sous md, le header ne montre que logo + loupe
// (RechercheMobile) — la nav (Mon collège de secteur / Explorer /
// Comprendre) et le CTA Camille, visibles en permanence sur desktop,
// n'avaient plus aucun point d'entrée sur mobile. Même pattern d'overlay
// plein écran que RechercheMobile.tsx, pour rester cohérent.

export function MenuMobile() {
  const pathname = usePathname();
  const [ouvert, setOuvert] = useState(false);

  useEffect(() => {
    if (!ouvert) return;
    const precedent = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = precedent;
    };
  }, [ouvert]);

  // Ferme automatiquement le menu après une navigation (clic sur un lien).
  useEffect(() => {
    setOuvert(false);
  }, [pathname]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOuvert(true)}
        aria-label="Ouvrir le menu"
        aria-expanded={ouvert}
        className="flex h-9 w-9 flex-none items-center justify-center rounded-[9px] border border-filet bg-white text-[15px] text-texte-doux outline-none focus-visible:ring-2 focus-visible:ring-action focus-visible:ring-offset-2 md:hidden"
      >
        ☰
      </button>

      {ouvert && (
        <div className="fixed inset-0 z-50 flex flex-col bg-fond-creme md:hidden">
          <div className="flex flex-none items-center justify-between border-b border-filet px-4 py-3">
            <Link href="/" className="flex items-center gap-2.5" onClick={() => setOuvert(false)}>
              <div className="h-6 w-6 rounded-[7px] bg-action" />
              <span className="font-titre text-[21px] font-semibold text-texte">écoles</span>
            </Link>
            <button
              type="button"
              onClick={() => setOuvert(false)}
              aria-label="Fermer le menu"
              className="flex-none font-ui text-[13px] font-bold text-texte-doux"
            >
              Fermer
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4">
            <nav className="flex flex-col gap-1">
              {LIENS_NAV.map((lien) => {
                const base = lien.match ?? lien.href;
                const actif = pathname === base || pathname.startsWith(`${base}/`);

                return (
                  <Link
                    key={lien.href}
                    href={lien.href}
                    aria-current={actif ? "page" : undefined}
                    className={`rounded-xl px-3 py-3 font-ui text-[16px] font-semibold ${
                      actif ? "bg-action-pale text-action-dark" : "text-texte hover:bg-fond-carte"
                    }`}
                  >
                    {lien.label}
                  </Link>
                );
              })}
            </nav>

            <Link
              href="/assistant"
              className="mt-4 flex items-center gap-2.5 rounded-full border border-agent bg-agent-pale px-4 py-3 font-ui text-[14px] font-bold text-agent-ink"
            >
              <GaletAgent taille="mini" />
              Demander à {NOM_ASSISTANT}
            </Link>
          </div>
        </div>
      )}
    </>
  );
}
