import Link from "next/link";
import type { CommuneRecherche } from "@/lib/types";

// Carte résultat "commune" de la page recherche — même famille visuelle que
// CarteCollege (web/src/components/), mais propre à /recherche : aucune
// autre page n'affiche une liste de communes sous cette forme (la page
// département utilise SousDivisionsTable, pensée pour un tableau à parent
// géo déjà connu, pas des résultats venant de partout en France).
export function CarteCommune({
  commune,
  href,
}: {
  commune: CommuneRecherche;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3.5 rounded-[13px] border-[1.5px] border-filet bg-white p-3.5 hover:border-filet-fonce"
    >
      <span className="flex h-11 w-11 flex-none items-center justify-center rounded-[13px] bg-fond-sable text-[17px] text-texte-doux">
        ⌂
      </span>
      <div className="min-w-0 flex-1">
        <div className="font-baloo text-[15px] font-bold text-texte">{commune.commune}</div>
        <div className="mt-1 text-[11.5px] font-semibold text-texte-doux">
          {commune.libelle_departement} ({commune.code_departement}) · {commune.nb_etablissements}{" "}
          {commune.nb_etablissements > 1 ? "collèges" : "collège"}
        </div>
      </div>
      <span className="flex-none text-[12.5px] font-bold text-action">Voir la commune →</span>
    </Link>
  );
}
