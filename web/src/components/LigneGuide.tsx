import Link from "next/link";
import type { Guide } from "@/lib/comprendre";

// Anatomie centrale de la section Comprendre : réutilisée sur l'index, la
// page catégorie et « À lire ensuite » (cf. bundle design_handoff_comprendre).
// Pas de date ni de mention de source sur la ligne : ça n'apparaît que sur
// la page du guide lui-même (décision actée : pas de mécanique de
// vérification affichée en liste, pour ne pas faire ressembler la section
// à un flux chronologique).
export function LigneGuide({ guide }: { guide: Guide }) {
  return (
    <Link
      href={`/comprendre/${guide.slug}`}
      className="grid grid-cols-[1fr_auto] items-center gap-6 px-6 py-4.5 hover:bg-fond-carte-alt"
    >
      <div className="min-w-0">
        <div className="font-titre text-[19px] font-semibold text-texte">{guide.titre}</div>
        <div className="mt-1 line-clamp-2 font-ui text-[14px] text-texte-doux">{guide.resume}</div>
      </div>
      <span className="flex-none font-ui text-[22px] text-filet-fonce">›</span>
    </Link>
  );
}
