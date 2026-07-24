"use client";

import { useState } from "react";
import Link from "next/link";
import type { CollegeSecteurItem } from "@/lib/types";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { construireSlugCollege } from "@/lib/slug";
import { hrefBaseVille } from "@/lib/hrefsGeo";
import { NOTATION_GRADIENTS } from "@/components/CarteCollege";
import { classeStatutSecteur } from "@/lib/tokens";

// Carte "collège de secteur" — visuellement distincte de CarteCollege
// (fond dégradé framboise, bordure 2px, badge ★), utilisée pour le collège
// de rattachement mis en avant sur la page dédiée. Contrairement à
// CarteCollege (liste "alentours" et /recherche), applique la règle des
// tags harmonisés avec troncature "+N" (documentée dans
// docs/Design_system/recherche/README.md, jamais implémentée jusqu'ici) —
// nouvelle sur cette page uniquement, /recherche non touché (cf. décision
// produit : gain marginal à rattraper là-bas, risque de régression visuelle
// non justifié pour cette tâche).
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
    <div
      className="rounded-[20px] border-2 p-4"
      style={{
        background: "linear-gradient(160deg,#FFFFFF 55%,#FDEFF4)",
        borderColor: "#E9A9C0",
        boxShadow: "0 12px 30px rgba(168,44,88,.13)",
      }}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2.5">
        <span
          className="inline-flex items-center gap-1.5 rounded-full bg-action px-3 py-1 text-[11.5px] font-extrabold text-white"
          style={{ boxShadow: "0 4px 11px rgba(168,44,88,.28)" }}
        >
          ★ Collège de secteur
        </span>
        {rang !== undefined && totalRang !== undefined && (
          <span className="text-[12px] font-bold text-texte-doux">
            Rattachement possible · {rang} sur {totalRang}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <div className="min-w-[170px] flex-1">
          <div className="font-baloo text-xl font-bold text-texte">{college.nom}</div>
          <div className="mt-0.5 text-[12.5px] font-semibold text-texte-doux">
            {college.secteur} · {college.commune} · {college.libelle_departement} ({college.code_departement})
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className={`rounded-[7px] px-2 py-0.5 text-[10.5px] font-bold ${classeStatut}`}>
              {college.secteur}
            </span>
            {visibles.map((b) => (
              <span key={b} className="rounded-[7px] bg-fond-sable px-2 py-0.5 text-[10.5px] font-bold text-texte-doux">
                {b}
              </span>
            ))}
            {reste > 0 && (
              <button
                type="button"
                onClick={() => setDeplie((v) => !v)}
                className="rounded-[7px] bg-fond-sable px-2 py-0.5 text-[10.5px] font-bold text-texte-doux hover:bg-filet-fonce"
              >
                {deplie ? "− réduire" : `+${reste}`}
              </button>
            )}
          </div>
        </div>

        <span className="flex flex-none items-center gap-1 rounded-[9px] bg-distance-pale px-2.5 py-1.5 text-[11.5px] font-bold text-distance">
          📍 {college.distance_km.toFixed(1).replace(".", ",")} km
        </span>

        <div className="flex-none text-center">
          <div
            className="inline-flex min-w-[40px] items-center justify-center rounded-[11px] px-3 py-1.5 font-baloo text-[17px] font-extrabold text-white"
            style={
              gradient
                ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre }
                : { backgroundColor: "var(--color-descriptif)" }
            }
          >
            {college.notation ?? "—"}
          </div>
          <div className="mt-1 text-[9px] font-semibold text-texte-doux">notation</div>
        </div>

        <Link
          href={`${hrefBase}/college/${construireSlugCollege(college.nom, college.uai)}`}
          className="flex-none rounded-xl bg-action px-4 py-2.5 text-[12.5px] font-bold text-white hover:bg-action-dark"
          style={{ boxShadow: "0 4px 12px rgba(217,69,122,.28)" }}
        >
          Voir le collège →
        </Link>
      </div>
    </div>
  );
}
