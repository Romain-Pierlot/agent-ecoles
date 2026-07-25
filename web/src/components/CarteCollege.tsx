import Link from "next/link";
import { classeStatutSecteur, classeBadgeDispositif } from "@/lib/tokens";
import { formaterDecimale, formaterPourcentage, formaterEcart } from "@/lib/format";
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
  // Optionnels : absents sur CollegeSecteurItem (bandeau "établissements
  // proches"/carte scolaire), qui affiche toujours une distance à la place
  // de ce bloc (cf. le rendu conditionné par `distanceKm` plus bas) — la
  // ligne d'écart n'est donc jamais lue dans ce contexte-là.
  brevet_va_taux_reussite_general?: number | null;
  va_imputee?: boolean;
  commune?: string;
  libelle_departement?: string;
  code_departement?: string;
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
  distanceKm,
}: {
  college: CarteCollegeDonnees;
  hrefBase: string;
  distanceKm?: number;
}) {
  const badgesDispositifs = deriveBadgesDispositifs(college);
  const gradient = college.notation ? NOTATION_GRADIENTS[college.notation] : null;

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

      {distanceKm !== undefined ? (
        <span className="flex flex-none items-center gap-1 rounded-[9px] bg-distance-pale px-2.5 py-1.5 font-ui text-[11.5px] font-bold text-distance">
          📍 {formaterDecimale(distanceKm, 1)} km
        </span>
      ) : (
        college.brevet_taux_reussite_general != null && (
          <div className="w-[150px] flex-none rounded-lg px-2 py-1 text-center">
            <div className="font-ui text-[20px] font-extrabold text-texte">
              {formaterPourcentage(college.brevet_taux_reussite_general, 0)}
            </div>
            {/* Libellé visible seul en dessous du point de rupture sm : au-delà,
                l'en-tête partagé (ListeColleges) le remplace visuellement — mais
                le texte reste dans le DOM (sr-only) pour les lecteurs d'écran,
                qui parcourent les cartes indépendamment de l'en-tête. */}
            <div className="mt-0.5 font-ui text-[12px] leading-tight font-semibold text-texte-doux sm:sr-only">
              Réussite au brevet
            </div>
            {!college.va_imputee && college.brevet_va_taux_reussite_general != null && (
              <div
                className={`font-ui text-[12px] leading-tight font-semibold ${
                  college.brevet_va_taux_reussite_general >= 0 ? "text-positif" : "text-attention"
                }`}
              >
                {`${formaterEcart(college.brevet_va_taux_reussite_general, 1)} vs attendu`}
              </div>
            )}
            {college.va_imputee && (
              <div className="font-ui text-[12px] leading-tight font-normal text-texte-doux">non publiée</div>
            )}
          </div>
        )
      )}

      <span
        className="flex h-11 w-11 flex-none items-center justify-center rounded-[12px] font-notation text-[19px] font-bold text-white"
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
