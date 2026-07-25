import type { BrevetResultats, EvolutionPoint } from "@/lib/types";
import { sentimentReussite } from "@/lib/tokens";
import { BoutonAide } from "@/components/BoutonAide";

// Classes Tailwind statiques — jamais interpolées dans un template string
// (Tailwind ne peut détecter que des noms de classe littéraux à la compilation).
const CLASSE_TEXTE_SENTIMENT: Record<string, string> = {
  positif: "text-positif",
  attention: "text-attention",
  descriptif: "text-descriptif",
};

// Registre de référence légitime (cf. docs/Design_system/REFERENCE.md,
// section 2) : couleurs du donut des mentions, nécessairement en hex brut
// car injectées dans un `conic-gradient()` dynamique — pas une classe
// Tailwind statique possible ici. Valeurs = mêmes tokens que
// --color-mention-* dans globals.css, gardées synchronisées à la main.
const COULEURS_MENTIONS: Record<string, string> = {
  // eslint-disable-next-line no-restricted-syntax -- registre de référence, voir commentaire ci-dessus
  "Très bien": "#2E8F5E",
  // eslint-disable-next-line no-restricted-syntax -- registre de référence, voir commentaire ci-dessus
  "Bien": "#5DB98B",
  // eslint-disable-next-line no-restricted-syntax -- registre de référence, voir commentaire ci-dessus
  "Assez bien": "#9BCBAF",
  // eslint-disable-next-line no-restricted-syntax -- registre de référence, voir commentaire ci-dessus
  "Sans mention": "#D8CBB4",
};

function DonutMentions({ brevet }: { brevet: BrevetResultats }) {
  const total = brevet.brevet_nb_candidats_general;
  if (!total) return null;

  const bornes = brevet.mentions.reduce<number[]>(
    (acc, m) => [...acc, acc[acc.length - 1] + (m.taux_pct ?? 0)],
    [0]
  );
  const segments = brevet.mentions.map(
    // eslint-disable-next-line no-restricted-syntax -- repli du registre COULEURS_MENTIONS ci-dessus
    (m, i) => `${COULEURS_MENTIONS[m.libelle] ?? "#D8CBB4"} ${bornes[i]}% ${bornes[i + 1]}%`
  );

  return (
    <div className="rounded-[22px] border-2 border-filet bg-white p-[22px_24px]">
      <div className="mb-3.5 font-titre text-[15px] font-semibold text-texte">Répartition des mentions</div>
      <div className="flex items-center gap-[22px]">
        <div
          className="relative h-[132px] w-[132px] flex-none rounded-full"
          style={{ background: `conic-gradient(${segments.join(", ")})` }}
        >
          <div className="absolute inset-[26px] flex flex-col items-center justify-center rounded-full bg-white">
            <div className="font-ui text-[22px] font-extrabold text-texte">{total}</div>
            <div className="text-[9.5px] font-semibold text-texte-doux">candidats</div>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          {brevet.mentions.map((m) => (
            <div key={m.libelle} className="flex items-center gap-2 text-[12.5px] font-semibold text-texte">
              <span
                className="h-3 w-3 rounded"
                // eslint-disable-next-line no-restricted-syntax -- repli du registre COULEURS_MENTIONS ci-dessus
                style={{ backgroundColor: COULEURS_MENTIONS[m.libelle] ?? "#D8CBB4" }}
              />
              {m.libelle} — <b>{m.taux_pct ?? "—"}%</b>{" "}
              <span className="text-texte-doux">· {m.nb_eleves ?? "—"} él.</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EvolutionTaux({ evolution }: { evolution: EvolutionPoint[] }) {
  const points = [...evolution].reverse().filter((p) => p.brevet_taux_reussite_general != null);
  if (points.length === 0) return null;

  const valeurs = points.map((p) => p.brevet_taux_reussite_general as number);
  const plancher = Math.max(0, Math.min(...valeurs) - 8);
  const plafond = Math.min(100, Math.max(...valeurs) + 4);
  const echelle = plafond - plancher || 1;

  return (
    <div className="rounded-[22px] border-2 border-filet bg-white p-[22px_24px]">
      <div className="mb-2 flex items-baseline justify-between">
        <div className="font-titre text-[15px] font-semibold text-texte">Évolution du taux de réussite</div>
        <div className="text-[11px] font-semibold text-texte-doux">
          {points[0].session} → {points[points.length - 1].session}
        </div>
      </div>
      <div className="flex h-40 items-end justify-between gap-3 border-b-2 border-filet px-1">
        {points.map((p) => {
          const valeur = p.brevet_taux_reussite_general as number;
          const pct = ((valeur - plancher) / echelle) * 100;
          // Hauteur calculée en pixels, pas en % : un `height: X%` sur cette
          // barre se résoudrait contre son parent flex-col, qui n'a pas de
          // hauteur définie (sizing par contenu) — un % de hauteur contre un
          // ancêtre en "auto" ne produit aucun effet visible (piège CSS classique).
          const hauteurPx = Math.max((pct / 100) * 96, 6);
          return (
            <div key={p.session} className="flex flex-1 flex-col items-center justify-end gap-1.5">
              <div className="text-[11px] font-bold text-positif">{valeur}%</div>
              <div
                className="w-[70%] rounded-t-lg bg-gradient-to-t from-mention-b to-positif"
                style={{ height: `${hauteurPx}px` }}
              />
              <div className="text-[11px] font-semibold text-texte-doux">{p.session}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ResultatsBrevet({ brevet, evolution }: { brevet: BrevetResultats | null; evolution: EvolutionPoint[] }) {
  if (!brevet) {
    return (
      <div id="brevet" className="scroll-mt-28">
        <p className="text-[13px] text-texte-doux">Aucun résultat au brevet disponible pour cet établissement.</p>
      </div>
    );
  }

  const sentimentTaux =
    brevet.brevet_taux_reussite_general != null && brevet.taux_reussite_national != null
      ? sentimentReussite(brevet.brevet_taux_reussite_general, brevet.taux_reussite_national)
      : "descriptif";

  const sentimentNoteEcrit =
    brevet.brevet_note_ecrit_general != null && brevet.note_ecrit_national != null
      ? sentimentReussite(brevet.brevet_note_ecrit_general, brevet.note_ecrit_national)
      : "descriptif";

  const sentimentAcces =
    brevet.taux_acces_6eme_3eme != null && brevet.taux_acces_6eme_3eme_national != null
      ? sentimentReussite(brevet.taux_acces_6eme_3eme, brevet.taux_acces_6eme_3eme_national)
      : "descriptif";

  return (
    <div id="brevet" className="scroll-mt-28">
      <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-action">
        Diplôme national du brevet · session {brevet.session}
      </div>
      <h2 className="font-titre text-[25px] font-semibold text-texte">Les résultats au brevet</h2>

      <div className="mt-4 grid gap-3.5 sm:grid-cols-3">
        <div className="rounded-[18px] border-2 border-filet bg-white p-[18px_20px]">
          <div className="text-[13.5px] font-bold text-texte">Taux de réussite au brevet</div>
          <div
            className={`mt-1.5 font-ui text-[40px] font-extrabold leading-none ${CLASSE_TEXTE_SENTIMENT[sentimentTaux]}`}
          >
            {brevet.brevet_taux_reussite_general ?? "—"}
            <span className="text-[20px]">%</span>
          </div>
          {(brevet.taux_reussite_national != null || brevet.taux_reussite_departemental != null) && (
            <div className="mt-3 flex gap-3.5 border-t border-filet-fonce pt-2.5 text-[12px] text-texte-doux">
              {brevet.taux_reussite_national != null && (
                <span>
                  National <b className="text-texte">{brevet.taux_reussite_national.toFixed(0)}%</b>
                </span>
              )}
              {brevet.taux_reussite_departemental != null && (
                <span>
                  Département <b className="text-texte">{brevet.taux_reussite_departemental.toFixed(0)}%</b>
                </span>
              )}
            </div>
          )}
        </div>

        <div className="rounded-[18px] border-2 border-filet bg-white p-[18px_20px]">
          <div className="text-[13.5px] font-bold text-texte">Note moyenne à l&apos;écrit</div>
          <div
            className={`mt-1.5 font-ui text-[40px] font-extrabold leading-none ${CLASSE_TEXTE_SENTIMENT[sentimentNoteEcrit]}`}
          >
            {brevet.brevet_note_ecrit_general ?? "—"}
            <span className="text-[18px]">/20</span>
          </div>
          {(brevet.note_ecrit_national != null || brevet.note_ecrit_departemental != null) && (
            <div className="mt-3 flex gap-3.5 border-t border-filet-fonce pt-2.5 text-[12px] text-texte-doux">
              {brevet.note_ecrit_national != null && (
                <span>
                  National <b className="text-texte">{brevet.note_ecrit_national.toFixed(1)}</b>
                </span>
              )}
              {brevet.note_ecrit_departemental != null && (
                <span>
                  Département <b className="text-texte">{brevet.note_ecrit_departemental.toFixed(1)}</b>
                </span>
              )}
            </div>
          )}
        </div>

        <div className="rounded-[18px] border-2 border-filet bg-white p-[18px_20px]">
          <div className="flex items-center text-[13.5px] font-bold text-texte">
            Accès de la 6ᵉ à la 3ᵉ
            <BoutonAide texte="Part d'élèves qui poursuivent sans redoubler ni partir." />
          </div>
          <div
            className={`mt-1.5 font-ui text-[40px] font-extrabold leading-none ${CLASSE_TEXTE_SENTIMENT[sentimentAcces]}`}
          >
            {brevet.taux_acces_6eme_3eme ?? "—"}
            <span className="text-[20px]">%</span>
          </div>
          {(brevet.taux_acces_6eme_3eme_national != null || brevet.taux_acces_6eme_3eme_departemental != null) && (
            <div className="mt-3 flex gap-3.5 border-t border-filet-fonce pt-2.5 text-[12px] text-texte-doux">
              {brevet.taux_acces_6eme_3eme_national != null && (
                <span>
                  National <b className="text-texte">{brevet.taux_acces_6eme_3eme_national.toFixed(0)}%</b>
                </span>
              )}
              {brevet.taux_acces_6eme_3eme_departemental != null && (
                <span>
                  Département <b className="text-texte">{brevet.taux_acces_6eme_3eme_departemental.toFixed(0)}%</b>
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 grid gap-5 lg:grid-cols-[1fr_1.15fr]">
        <DonutMentions brevet={brevet} />
        <EvolutionTaux evolution={evolution} />
      </div>
    </div>
  );
}
