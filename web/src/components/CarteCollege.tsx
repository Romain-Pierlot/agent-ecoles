import Link from "next/link";
import { classeStatutSecteur, classeBadgeDispositif, sentimentReussite } from "@/lib/tokens";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { construireSlugCollege } from "@/lib/slug";

// Remplacement de src/components/CarteCollege.tsx (refonte terracotta).
// Structure & données IDENTIQUES à l'original (mêmes champs lus, même href,
// même logique tri/distance) — seul l'habillage change :
//   - carte : coins nets rounded-[14px], surface bg-fond-carte
//   - nom du collège + commune : font-titre (Newsreader)
//   - badges dispositifs/sections : COULEUR PAR FAMILLE via
//     classeBadgeDispositif() (au lieu du gris uniforme bg-fond-sable)
//   - lettre de notation : font-notation (Schibsted), coin net rounded-[12px]
//   - taux de réussite : font-ui (grotesque lisible, ex font-baloo)
//   - la mise en évidence du critère de tri actif est CONSERVÉE (ring sur la
//     notation OU fond pâle sur la réussite — jamais les deux)

type CarteCollegeDonnees = {
  uai: string;
  nom: string;
  secteur: string;
  notation: string | null;
  appartenance_education_prioritaire: string | null;
  ulis: boolean;
  segpa: boolean;
  section_arts: boolean;
  section_cinema: boolean;
  section_theatre: boolean;
  section_sport: boolean;
  section_internationale: boolean;
  section_europeenne: boolean;
  brevet_taux_reussite_general?: number | null;
  commune?: string;
  libelle_departement?: string;
  code_departement?: string;
};

const CLASSE_TEXTE_SENTIMENT: Record<string, string> = {
  positif: "text-positif",
  attention: "text-attention",
};

// Registre de référence légitime (cf. docs/Design_system/REFERENCE.md,
// section 2) : dégradés de la pastille notation, nécessairement en hex brut
// (injectés dans un style inline `backgroundImage`, pas une classe Tailwind
// statique possible pour un dégradé à 2 couleurs). Valeurs inchangées
// depuis avant la refonte — déjà cohérentes avec le sable. Seule la POLICE
// de la lettre change (Schibsted, cf. className).
/* eslint-disable no-restricted-syntax -- registre de référence, voir commentaire ci-dessus */
export const NOTATION_GRADIENTS: Record<string, { fond: string; ombre: string }> = {
  "A+": { fond: "linear-gradient(155deg,#2E8F5E,#1F6B44)", ombre: "0 5px 13px rgba(46,143,94,.3)" },
  "A": { fond: "linear-gradient(155deg,#4FA772,#2E8F5E)", ombre: "0 5px 13px rgba(79,167,114,.3)" },
  "A-": { fond: "linear-gradient(155deg,#7FB65E,#5E9642)", ombre: "0 5px 13px rgba(122,163,74,.3)" },
  "B+": { fond: "linear-gradient(155deg,#F0A02E,#CE821A)", ombre: "0 5px 13px rgba(240,160,46,.28)" },
  "B": { fond: "linear-gradient(155deg,#E58A3C,#B0741A)", ombre: "0 5px 13px rgba(229,138,60,.3)" },
};
/* eslint-enable no-restricted-syntax */

export function CarteCollege({
  college,
  hrefBase,
  tauxReussiteNational,
  critereTriActif,
  distanceKm,
}: {
  college: CarteCollegeDonnees;
  hrefBase: string;
  tauxReussiteNational: number | null;
  critereTriActif?: "notation" | "reussite";
  distanceKm?: number;
}) {
  const badgesDispositifs = deriveBadgesDispositifs(college);
  const gradient = college.notation ? NOTATION_GRADIENTS[college.notation] : null;

  const sentimentTaux =
    college.brevet_taux_reussite_general != null && tauxReussiteNational !== null
      ? sentimentReussite(college.brevet_taux_reussite_general, tauxReussiteNational)
      : null;

  const classeStatut = classeStatutSecteur(college.secteur);

  return (
    <Link
      href={`${hrefBase}/college/${construireSlugCollege(college.nom, college.uai)}`}
      className="flex items-center gap-3.5 rounded-[14px] border border-filet bg-fond-carte p-3.5 transition-colors hover:border-filet-fonce"
    >
      <div className="min-w-0 flex-1">
        <div className="font-titre text-[17px] font-semibold text-texte">{college.nom}</div>
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          {college.commune && (
            <span className="font-ui text-[12px] font-semibold text-texte-doux">
              {college.commune} · {college.libelle_departement} ({college.code_departement})
            </span>
          )}
          <span className={`rounded-[6px] px-2 py-0.5 font-ui text-[10.5px] font-bold ${classeStatut}`}>
            {college.secteur}
          </span>
          {badgesDispositifs.map((b) => (
            <span
              key={b}
              className={`rounded-[6px] px-2 py-0.5 font-ui text-[10.5px] font-bold ${classeBadgeDispositif(b)}`}
            >
              {b}
            </span>
          ))}
        </div>
      </div>

      <span
        className={`flex h-11 w-11 flex-none items-center justify-center rounded-[12px] font-notation text-[19px] font-bold text-white ${
          critereTriActif === "notation" ? "ring-2 ring-action ring-offset-2 ring-offset-fond-carte" : ""
        }`}
        style={
          gradient
            ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre }
            : { backgroundColor: "var(--color-descriptif)" }
        }
      >
        {college.notation ?? "—"}
      </span>

      {distanceKm !== undefined ? (
        <span className="flex flex-none items-center gap-1 rounded-[9px] bg-distance-pale px-2.5 py-1.5 font-ui text-[11.5px] font-bold text-distance">
          📍 {distanceKm.toFixed(1).replace(".", ",")} km
        </span>
      ) : (
        college.brevet_taux_reussite_general != null && (
          <div
            className={`flex-none rounded-lg px-2 py-1 text-center ${
              critereTriActif === "reussite" ? "bg-action-pale" : ""
            }`}
          >
            <div
              className={`font-ui text-[17px] font-extrabold ${
                sentimentTaux ? CLASSE_TEXTE_SENTIMENT[sentimentTaux] : "text-texte"
              }`}
            >
              {college.brevet_taux_reussite_general.toFixed(0)} %
            </div>
            <div className="font-ui text-[9px] font-semibold text-texte-doux">réussite brevet</div>
          </div>
        )
      )}

      <span className="flex-none text-[15px] text-filet-fonce">›</span>
    </Link>
  );
}
