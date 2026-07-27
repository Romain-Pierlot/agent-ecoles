import type { Source } from "@/lib/comprendre";
import { formaterDateJourMoisAnnee } from "@/lib/formatDateLongue";

// Liste de sources façon bibliographie, en bas de page (colonne de droite
// du gabarit de lecture) : pas de mécanique de vérification, juste "voici
// ce qui a servi à écrire ce guide" (décision actée).
export function ListeSources({ sources }: { sources: Source[] }) {
  return (
    <div className="rounded-[14px] border border-filet-fonce bg-fond-carte px-4.5 py-4">
      <div className="mb-3.5 font-ui text-[11px] font-bold tracking-[.08em] text-texte-doux uppercase">Sources</div>
      <div className="flex flex-col">
        {sources.map((source, i) => (
          <div key={`${source.producteur}-${source.titre}`} className={i > 0 ? "mt-3.5 border-t border-fond-encart pt-3.5" : undefined}>
            <div className="font-ui text-[13px] font-bold text-texte">
              {source.producteur} — {source.titre}
            </div>
            <div className="mt-0.5 font-ui text-[12.5px] text-texte-doux">
              {source.millesime && `${source.millesime} · `}relevé le {formaterDateJourMoisAnnee(source.dateReleve)}
            </div>
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-ui text-[12px] font-semibold text-action-dark"
            >
              {new URL(source.url).hostname} ↗
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
