"use client";

import { useState } from "react";
import Link from "next/link";
import type { CollegeSecteurItem } from "@/lib/types";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { construireSlugCollege } from "@/lib/slug";
import { hrefBaseVille } from "@/lib/hrefsGeo";
import { NOTATION_GRADIENTS } from "@/components/CarteCollege";
import { classeStatutSecteur, classeBadgeDispositif } from "@/lib/tokens";

// Carte "collège de secteur" — même anatomie que CarteCollege (ligne
// entièrement cliquable : infos à gauche, distance, tuile de notation,
// chevron), seul l'habillage la distingue : fond dégradé pêche, bordure,
// badge ★ au-dessus du nom (cf. maquette de référence, tour 12 : "même
// anatomie que les voisines" — pas de bouton CTA séparé, pas de légende
// "notation" sous la pastille).
const MAX_TAGS_VISIBLES = 2;

export function CarteCollegeSecteur({
  college,
  rang,
  totalRang,
}: {
  college: CollegeSecteurItem;
  // Présents seulement en multi-secteur ("Rattachement possible · 1 sur 2")
  rang?: number;
  totalRang?: number;
}) {
  const [deplie, setDeplie] = useState(false);
  const badgesDispositifs = deriveBadgesDispositifs(college);
  const visibles = deplie ? badgesDispositifs : badgesDispositifs.slice(0, MAX_TAGS_VISIBLES);
  const reste = badgesDispositifs.length - MAX_TAGS_VISIBLES;
  const gradient = college.notation ? NOTATION_GRADIENTS[college.notation] : null;
  const hrefBase = hrefBaseVille(college);

  const classeStatut = classeStatutSecteur(college.secteur);

  return (
    <Link
      href={`${hrefBase}/college/${construireSlugCollege(college.nom, college.uai)}`}
      className="flex items-center gap-3.5 rounded-[14px] border-[1.5px] p-3.5 transition-colors"
      /* eslint-disable no-restricted-syntax -- fond dégradé pêche propre à
         cette carte, registre de référence (docs/Design_system/REFERENCE.md
         section 2), nécessairement en hex brut pour le dégradé */
      style={{
        background: "linear-gradient(150deg,#FCEBD8,#F9DEE4)",
        borderColor: "#E7B0A0",
        boxShadow: "0 12px 28px rgba(191,74,42,.16)",
      }}
      /* eslint-enable no-restricted-syntax */
    >
      <div className="min-w-0 flex-1">
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 rounded-full bg-action px-3 py-1 text-[10px] font-extrabold text-white"
            style={{ boxShadow: "0 3px 9px rgba(191,74,42,.26)" }}
          >
            ★ Collège de secteur
          </span>
          {rang !== undefined && totalRang !== undefined && (
            <span className="text-[12px] font-bold text-texte-doux">
              Rattachement possible · {rang} sur {totalRang}
            </span>
          )}
        </div>
        <div className="font-titre text-[17px] font-semibold text-texte">{college.nom}</div>
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          <span className="font-ui text-[12px] font-semibold text-texte-doux">
            {college.commune} · {college.libelle_departement} ({college.code_departement})
          </span>
          <span className={`rounded-[6px] px-2 py-0.5 font-ui text-[10.5px] font-bold ${classeStatut}`}>
            {college.secteur}
          </span>
          {visibles.map((b) => (
            <span key={b} className={`rounded-[6px] px-2 py-0.5 font-ui text-[10.5px] font-bold ${classeBadgeDispositif(b)}`}>
              {b}
            </span>
          ))}
          {reste > 0 && (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setDeplie((v) => !v);
              }}
              className="rounded-[6px] bg-fond-sable px-2 py-0.5 font-ui text-[10.5px] font-bold text-texte-doux hover:bg-filet-fonce"
            >
              {deplie ? "− réduire" : `+${reste}`}
            </button>
          )}
        </div>
      </div>

      <span className="flex flex-none items-center gap-1 rounded-[9px] bg-distance-pale px-2.5 py-1.5 font-ui text-[11.5px] font-bold text-distance">
        📍 {college.distance_km.toFixed(1).replace(".", ",")} km
      </span>

      <span
        className="flex h-11 w-11 flex-none items-center justify-center rounded-[13px] font-notation text-[20px] font-bold text-white"
        style={
          gradient
            ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre }
            : { backgroundColor: "var(--color-descriptif)" }
        }
      >
        {college.notation ?? "—"}
      </span>

      <span className="flex-none text-[15px] text-filet-fonce">›</span>
    </Link>
  );
}
