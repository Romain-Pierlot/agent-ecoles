import Link from "next/link";
import { classeStatutSecteur, sentimentReussite } from "@/lib/tokens";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { construireSlugCollege } from "@/lib/slug";

// Sous-ensemble commun à CollegeVille (page ville, /recherche) et
// CollegeSecteurItem (page collège de secteur, cf. lib/types.ts) — seuls
// les champs réellement lus par ce composant, pour rester compatible avec
// les deux sans dépendre de champs que l'un des deux ne porte pas (ex.
// va_imputee, brevet_taux_reussite_general).
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
  // Optionnels sur CollegeVille, toujours présents sur EtablissementRecherche
  // (/recherche). La page ville les fournit désormais explicitement (cf.
  // ville/page.tsx, convention "chaque carte porte nom + ville + département") —
  // la ligne de localisation s'affiche donc sur les deux pages dès qu'ils sont
  // fournis.
  commune?: string;
  libelle_departement?: string;
  code_departement?: string;
};

// Classes Tailwind statiques — jamais interpolées dans un template string
// (Tailwind ne peut détecter que des noms de classe littéraux à la compilation).
const CLASSE_TEXTE_SENTIMENT: Record<string, string> = {
  positif: "text-positif",
  attention: "text-attention",
};

// Dégradés de badge notation (carte résultat page ville / comparateur) —
// distincts du badge solide de la fiche établissement (cf. README du bundle
// hub_departement_comparateur, section "Badges notation solides"). "B" n'a
// pas d'exemple dans la maquette : teinte dérivée en cohérence avec
// --color-attention-dark, déjà utilisé pour la même famille ambre que B+.
export const NOTATION_GRADIENTS: Record<string, { fond: string; ombre: string }> = {
  "A+": { fond: "linear-gradient(155deg,#2E8F5E,#1F6B44)", ombre: "0 5px 13px rgba(46,143,94,.3)" },
  "A": { fond: "linear-gradient(155deg,#4FA772,#2E8F5E)", ombre: "0 5px 13px rgba(79,167,114,.3)" },
  "A-": { fond: "linear-gradient(155deg,#7FB65E,#5E9642)", ombre: "0 5px 13px rgba(122,163,74,.3)" },
  "B+": { fond: "linear-gradient(155deg,#F0A02E,#CE821A)", ombre: "0 5px 13px rgba(240,160,46,.28)" },
  "B": { fond: "linear-gradient(155deg,#E58A3C,#B0741A)", ombre: "0 5px 13px rgba(229,138,60,.3)" },
};

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
  // Optionnel : seule la page ville trie (et donc met en évidence le
  // critère actif) pour l'instant — /recherche peut réutiliser cette carte
  // sans tri, auquel cas rien n'est mis en évidence.
  critereTriActif?: "notation" | "reussite";
  // Optionnel : liste "alentours" de la page collège de secteur — remplace
  // l'affichage % réussite brevet par un badge distance (la maquette de
  // cette page n'affiche pas le taux de réussite sur cette carte).
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
      className="flex items-center gap-3.5 rounded-[13px] border-[1.5px] border-filet bg-white p-3.5 hover:border-filet-fonce"
    >
      <div className="min-w-0 flex-1">
        <div className="font-baloo text-[15px] font-bold text-texte">{college.nom}</div>
        {/* Ligne unique : ville/département (si présents, /recherche uniquement)
            puis les tags à sa droite sur la même ligne — au lieu d'une ligne
            dédiée à la localisation, pour limiter la hauteur de la carte. */}
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          {college.commune && (
            <span className="text-[12px] font-semibold text-texte-doux">
              {college.commune} · {college.libelle_departement} ({college.code_departement})
            </span>
          )}
          <span className={`rounded-[7px] px-2 py-0.5 text-[10px] font-bold ${classeStatut}`}>
            {college.secteur}
          </span>
          {badgesDispositifs.map((b) => (
            <span key={b} className="rounded-[7px] bg-fond-sable px-2 py-0.5 text-[10px] font-bold text-texte-doux">
              {b}
            </span>
          ))}
        </div>
      </div>

      {/* Indicateurs groupés à droite, comme sur les tableaux hub (libellé à
          gauche, indicateurs à droite) — badge notation et taux de réussite
          côte à côte, près du contrôle de tri qu'ils alimentent. Celui qui
          correspond au critère de tri actif est mis en évidence, pour relier
          visuellement le contrôle de tri à la bonne donnée. */}
      <span
        className={`flex h-11 w-11 flex-none items-center justify-center rounded-[13px] font-baloo text-[19px] font-extrabold text-white ${
          critereTriActif === "notation" ? "ring-2 ring-action ring-offset-2" : ""
        }`}
        style={gradient ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre } : { backgroundColor: "var(--color-descriptif)" }}
      >
        {college.notation ?? "—"}
      </span>

      {distanceKm !== undefined ? (
        <span className="flex flex-none items-center gap-1 rounded-[9px] bg-distance-pale px-2.5 py-1.5 text-[11.5px] font-bold text-distance">
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
              className={`font-baloo text-[17px] font-extrabold ${
                sentimentTaux ? CLASSE_TEXTE_SENTIMENT[sentimentTaux] : "text-texte"
              }`}
            >
              {college.brevet_taux_reussite_general.toFixed(0)} %
            </div>
            <div className="text-[9px] font-semibold text-texte-doux">réussite brevet</div>
          </div>
        )
      )}

      <span className="flex-none text-[15px] text-filet-fonce">›</span>
    </Link>
  );
}
