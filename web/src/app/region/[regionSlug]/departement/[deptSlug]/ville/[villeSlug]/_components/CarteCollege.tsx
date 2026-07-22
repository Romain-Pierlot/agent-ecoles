import Link from "next/link";
import type { CollegeVille } from "@/lib/types";
import { sentimentReussite } from "@/lib/tokens";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { construireSlugCollege } from "@/lib/slug";

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
const NOTATION_GRADIENTS: Record<string, { fond: string; ombre: string }> = {
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
}: {
  college: CollegeVille;
  hrefBase: string;
  tauxReussiteNational: number | null;
}) {
  const badgesDispositifs = deriveBadgesDispositifs(college);
  const gradient = college.notation ? NOTATION_GRADIENTS[college.notation] : null;

  const sentimentTaux =
    college.brevet_taux_reussite_general !== null && tauxReussiteNational !== null
      ? sentimentReussite(college.brevet_taux_reussite_general, tauxReussiteNational)
      : null;

  const classeStatut =
    college.secteur === "Public"
      ? "bg-statut-public-pale text-statut-public"
      : "bg-statut-prive-pale text-statut-prive";

  return (
    <Link
      href={`${hrefBase}/college/${construireSlugCollege(college.nom, college.uai)}`}
      className="flex items-center gap-3.5 rounded-[13px] border-[1.5px] border-filet bg-white p-3.5 hover:border-filet-fonce"
    >
      <div className="min-w-0 flex-1">
        <div className="font-baloo text-[15px] font-bold text-texte">{college.nom}</div>
        <div className="mt-1.5 flex flex-wrap gap-1.5">
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
          côte à côte, près du contrôle de tri qu'ils alimentent. */}
      <span
        className="flex h-11 w-11 flex-none items-center justify-center rounded-[13px] font-baloo text-[19px] font-extrabold text-white"
        style={gradient ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre } : { backgroundColor: "var(--color-descriptif)" }}
      >
        {college.notation ?? "—"}
      </span>

      {college.brevet_taux_reussite_general !== null && (
        <div className="flex-none text-center">
          <div
            className={`font-baloo text-[17px] font-extrabold ${
              sentimentTaux ? CLASSE_TEXTE_SENTIMENT[sentimentTaux] : "text-texte"
            }`}
          >
            {college.brevet_taux_reussite_general.toFixed(0)} %
          </div>
          <div className="text-[9px] font-semibold text-texte-doux">réussite brevet</div>
        </div>
      )}

      <span className="flex-none text-[15px] text-filet-fonce">›</span>
    </Link>
  );
}
