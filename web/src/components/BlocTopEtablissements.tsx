import Link from "next/link";
import type { TopEtablissement } from "@/lib/types";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { construireSlugDepartement, construireSlugCollege, slugifier } from "@/lib/slug";
import { NOTATION_GRADIENTS } from "@/components/CarteCollege";
import { classeStatutSecteur } from "@/lib/tokens";
import { BoutonAide } from "@/components/BoutonAide";

// Blocs "Meilleure notation" / "Meilleure valeur ajoutée" des pages
// région/département (cf. docs/Design_system/Sitemap.dc.html, maquette
// validée sur le Rhône). Volontairement compact — nom + un seul chiffre par
// ligne, badge à droite (pas à gauche : plusieurs badges de même couleur
// empilés à gauche faisaient "pâté" visuel, cf. retour sur le mockup) — pas
// la carte complète (CarteCollege), pour ne pas pousser le tableau des
// sous-divisions trop bas sur la page.

function hrefEtablissement(e: TopEtablissement, regionSlug: string): string {
  const deptSlug = construireSlugDepartement(e.code_departement, e.libelle_departement);
  return `/region/${regionSlug}/departement/${deptSlug}/ville/${slugifier(e.commune)}/college/${construireSlugCollege(e.nom, e.uai)}`;
}

function BadgeNotation({ notation }: { notation: string | null }) {
  const gradient = notation ? NOTATION_GRADIENTS[notation] : null;
  return (
    <span
      className="flex h-7 w-7 flex-none items-center justify-center rounded-[9px] font-notation text-[11.5px] font-extrabold text-white"
      style={gradient ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre } : { backgroundColor: "var(--color-descriptif)" }}
    >
      {notation ?? "—"}
    </span>
  );
}

function BadgeVa({ valeur }: { valeur: number }) {
  const positif = valeur >= 0;
  return (
    <span
      className={`flex h-7 w-7 flex-none items-center justify-center rounded-[9px] font-ui text-[10.5px] font-extrabold text-white ${
        positif ? "bg-positif" : "bg-attention"
      }`}
    >
      {positif ? "+" : ""}
      {Math.round(valeur)}
    </span>
  );
}

export function BlocTopEtablissements({
  titre,
  aide,
  pastilleClasse,
  etablissements,
  critere,
  regionSlug,
}: {
  titre: string;
  // Texte de la bulle d'aide contextuelle affichée à côté du titre (cf.
  // BoutonAide, même pattern que sur la fiche établissement).
  aide?: string;
  // Couleur de la pastille à côté du titre — Tailwind ne peut pas résoudre
  // une classe construite dynamiquement, donc la classe complète est passée
  // telle quelle par l'appelant plutôt que composée ici (cf. ZoneHub.tsx).
  pastilleClasse: string;
  etablissements: TopEtablissement[];
  critere: "notation" | "va";
  regionSlug: string;
}) {
  if (etablissements.length === 0) return null;

  return (
    <div className="rounded-[14px] border-[1.5px] border-filet bg-white p-3.5 pb-1.5">
      <h3 className="mb-2 flex items-center gap-1.5 text-[12.5px] font-bold text-texte">
        <span className={`h-[7px] w-[7px] rounded-full ${pastilleClasse}`} />
        {titre}
        {aide && <BoutonAide texte={aide} />}
      </h3>
      {etablissements.map((e) => {
        const tag = deriveBadgesDispositifs(e)[0];
        return (
          <Link
            key={e.uai}
            href={hrefEtablissement(e, regionSlug)}
            className="flex items-center gap-2.5 border-b border-fond-sable py-2 last:border-none hover:bg-fond-carte/50"
          >
            <span className="min-w-0 flex-1">
              <div className="truncate text-[12.5px] font-bold text-texte">{e.nom}</div>
              <div className="flex items-center gap-1.5">
                <span className="truncate text-[10.5px] text-texte-doux">
                  {e.commune} · {e.libelle_departement} ({e.code_departement})
                </span>
                <span className={`flex-none rounded-md px-1.5 py-px text-[9.5px] font-bold ${classeStatutSecteur(e.secteur)}`}>
                  {e.secteur}
                </span>
                {tag && (
                  <span className="flex-none rounded-md bg-attention-pale px-1.5 py-px text-[9.5px] font-bold text-attention-dark">
                    {tag}
                  </span>
                )}
              </div>
            </span>
            {critere === "notation" ? (
              <BadgeNotation notation={e.notation} />
            ) : (
              <BadgeVa valeur={e.brevet_va_taux_reussite_general ?? 0} />
            )}
          </Link>
        );
      })}
    </div>
  );
}
