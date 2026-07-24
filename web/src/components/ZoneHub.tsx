import Link from "next/link";
import type { AgregatEtablissements, SousDivision, TopEtablissement } from "@/lib/types";
import { AgentBlock } from "@/components/AgentBlock";
import { RechercheBloc } from "@/components/RechercheBloc";
import { SousDivisionsTable } from "@/components/SousDivisionsTable";
import { BlocTopEtablissements } from "@/components/BlocTopEtablissements";

export type LigneSousDivision = SousDivision & { href: string };

export function ZoneHub({
  filAriane,
  eyebrow,
  titre,
  sousTitre,
  global,
  labelColonneSousDivision,
  sousDivisions,
  afficherCodeSousDivisions,
  topNotation,
  topVa,
  regionSlug,
  exempleAgent,
}: {
  filAriane: { label: string; href?: string }[];
  eyebrow: string;
  titre: string;
  sousTitre: string;
  global: AgregatEtablissements;
  labelColonneSousDivision: string;
  sousDivisions: LigneSousDivision[];
  // Relayé tel quel à SousDivisionsTable — cf. commentaire là-bas.
  afficherCodeSousDivisions?: boolean;
  // Absents sur /region (liste des régions) — ce niveau n'a pas ce bloc
  // (mesuré non pertinent, cf. hierarchie_tool.py::obtenir_top_etablissements_zone).
  topNotation?: TopEtablissement[];
  topVa?: TopEtablissement[];
  // Nécessaire pour reconstruire l'URL de chaque établissement du top
  // (peut appartenir à n'importe quel département de la région affichée).
  regionSlug?: string;
  exempleAgent: string;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-4.5 md:px-8">
      {/* ===== FIL D'ARIANE ===== */}
      <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
        {filAriane.map((item, index) => (
          <span key={item.label} className="flex items-center gap-1.5">
            {index > 0 && <span className="text-filet-fonce">›</span>}
            {item.href ? (
              <Link href={item.href} className="hover:text-texte-doux">
                {item.label}
              </Link>
            ) : (
              <span className="text-texte">{item.label}</span>
            )}
          </span>
        ))}
      </div>

      {/* ===== HERO ===== */}
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">{eyebrow}</span>
          <h1 className="mt-1 font-baloo text-[30px] font-extrabold leading-tight text-texte">{titre}</h1>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-baloo text-[22px] font-extrabold text-texte">{global.nb_etablissements}</div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Collèges</div>
          </div>
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-baloo text-[22px] font-extrabold text-positif">
              {global.taux_reussite_moyen !== null ? `${global.taux_reussite_moyen.toFixed(0)} %` : "—"}
            </div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Réussite moyenne</div>
          </div>
        </div>
      </div>

      {regionSlug && topNotation && topVa && (topNotation.length > 0 || topVa.length > 0) && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <BlocTopEtablissements
            titre="Meilleure notation"
            aide="La notation (de A+ à B) combine les résultats au brevet (taux de réussite et note à l'écrit) et leur valeur ajoutée par rapport au niveau attendu compte tenu du profil des élèves."
            pastilleClasse="bg-notation-a-plus"
            etablissements={topNotation}
            critere="notation"
            regionSlug={regionSlug}
          />
          <BlocTopEtablissements
            titre="Meilleure valeur ajoutée"
            aide="On compare les résultats obtenus à ceux attendus compte tenu du profil des élèves. Un écart positif = le collège fait progresser ses élèves au-delà des prévisions."
            pastilleClasse="bg-positif"
            etablissements={topVa}
            critere="va"
            regionSlug={regionSlug}
          />
        </div>
      )}

      <RechercheBloc />

      {/* ===== LISTE SOUS-DIVISIONS =====
          Le H2 porte le compteur ("N départements") plutôt que de le dupliquer
          avec un sous-titre séparé sous le H1 — une seule mention, avec le
          poids visuel d'un vrai titre de section (H1 région → H2 liste,
          hiérarchie de titres correcte pour le SEO/l'accessibilité). L'en-tête
          de colonne du tableau ("Département") reste : son rôle est de nommer
          une colonne, pas d'annoncer la section. */}
      <div className="mt-7">
        <h2 className="font-baloo text-[19px] font-extrabold text-texte">{sousTitre}</h2>
        <SousDivisionsTable
          labelColonne={labelColonneSousDivision}
          sousDivisions={sousDivisions}
          afficherCode={afficherCodeSousDivisions}
        />
      </div>

      <AgentBlock exemple={exempleAgent} />
    </div>
  );
}
