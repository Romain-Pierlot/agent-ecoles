import type { PeriodeVacances } from "@/lib/types";
import { DateLongue } from "./DateLongue";
import { formaterDateCourte } from "@/lib/formatDateLongue";

const ORDRE_TERRITOIRES = [
  "Guadeloupe", "Martinique", "Guyane", "Mayotte", "Réunion",
  "Saint Pierre et Miquelon", "Polynésie", "Nouvelle Calédonie", "Wallis et Futuna",
];

const LABEL_TERRITOIRE: Record<string, string> = {
  Guadeloupe: "Guadeloupe",
  Martinique: "Martinique",
  Guyane: "Guyane",
  Mayotte: "Mayotte",
  Réunion: "La Réunion",
  "Saint Pierre et Miquelon": "Saint-Pierre-et-Miquelon",
  Polynésie: "Polynésie française",
  "Nouvelle Calédonie": "Nouvelle-Calédonie",
  "Wallis et Futuna": "Wallis-et-Futuna",
};

// Commentaires éditoriaux propres à chaque territoire — pas une donnée
// structurée en base (aucune table ne modélise "rythme austral" ou "rentrée
// avancée"), donc contenu fixe comme la phrase de lecture et l'encart
// "À noter" de page.tsx.
const NOTE_TERRITOIRE: Record<string, string> = {
  Mayotte: "rentrée avancée",
  Réunion: "rythme austral",
  "Nouvelle Calédonie": "année civile 2026",
  "Wallis et Futuna": "année civile 2026",
};

type DonneesTerritoire = {
  cles: string[];
  rentree: PeriodeVacances | null;
  finAnnee: PeriodeVacances | null;
  vacances: PeriodeVacances[];
};

// Deux territoires aux dates rigoureusement identiques (Nouvelle-Calédonie
// et Wallis-et-Futuna, même vice-rectorat) fusionnent en une seule ligne —
// détecté par égalité de contenu plutôt que codé en dur sur ces deux noms,
// pour rester correct si la source change un jour.
function construireTerritoires(outreMer: PeriodeVacances[]): DonneesTerritoire[] {
  const parZone = new Map<string, PeriodeVacances[]>();
  for (const ligne of outreMer) {
    if (!parZone.has(ligne.zone)) parZone.set(ligne.zone, []);
    parZone.get(ligne.zone)!.push(ligne);
  }

  const brut: DonneesTerritoire[] = ORDRE_TERRITOIRES.filter((zone) => parZone.has(zone)).map((zone) => {
    const lignes = parZone.get(zone)!;
    return {
      cles: [zone],
      rentree: lignes.find((l) => l.periode === "Rentrée") ?? null,
      finAnnee: lignes.find((l) => l.periode === "Fin d'année scolaire") ?? null,
      vacances: lignes.filter((l) => l.type_periode === "vacances"),
    };
  });

  const signature = (t: DonneesTerritoire) =>
    JSON.stringify([
      t.rentree?.date_debut ?? null,
      t.finAnnee?.date_debut ?? null,
      t.vacances.map((v) => [v.periode, v.date_debut, v.date_fin]),
    ]);

  const fusionnes: DonneesTerritoire[] = [];
  for (const territoire of brut) {
    const jumeau = fusionnes.find((f) => signature(f) === signature(territoire));
    if (jumeau) jumeau.cles.push(...territoire.cles);
    else fusionnes.push(territoire);
  }
  return fusionnes;
}

export function TableauOutreMer({ outreMer }: { outreMer: PeriodeVacances[] }) {
  const territoires = construireTerritoires(outreMer);

  return (
    <section id="outre-mer" className="border-t border-filet bg-fond-sable px-4.5 py-9 md:px-11">
      <div className="mx-auto max-w-6xl">
        <h2 className="font-titre text-[21px] font-semibold text-texte md:text-[26px]">Outre-mer</h2>
        <p className="mt-1.5 max-w-[720px] font-ui text-[13px] leading-[1.6] text-texte-doux md:text-[14px]">
          Chaque territoire a son calendrier, avec ses propres intitulés de vacances. La
          Nouvelle-Calédonie et Wallis-et-Futuna suivent l&apos;année civile australe. Les dates ci-dessous
          sont celles de 2026.
        </p>

        <div className="mt-4 overflow-x-auto rounded-2xl border border-filet-fonce bg-fond-carte">
          <table className="w-full min-w-[640px] border-collapse">
            <caption className="sr-only">Dates des vacances scolaires par territoire d&apos;outre-mer</caption>
            <thead>
              <tr className="bg-fond-encart">
                <th scope="col" className="w-[210px] px-3.5 py-2.5 text-left font-ui text-[10.5px] font-bold uppercase tracking-[.09em] text-texte-doux">
                  Territoire
                </th>
                <th scope="col" className="w-[180px] px-3.5 py-2.5 text-left font-ui text-[10.5px] font-bold uppercase tracking-[.09em] text-texte-doux">
                  Rentrée des élèves
                </th>
                <th scope="col" className="px-3.5 py-2.5 text-left font-ui text-[10.5px] font-bold uppercase tracking-[.09em] text-texte-doux">
                  Vacances de l&apos;année
                </th>
                <th scope="col" className="w-[132px] px-3.5 py-2.5 text-left font-ui text-[10.5px] font-bold uppercase tracking-[.09em] text-texte-doux">
                  Fin d&apos;année
                </th>
              </tr>
            </thead>
            <tbody>
              {territoires.map((territoire, index) => {
                const note = NOTE_TERRITOIRE[territoire.cles[0]];
                return (
                  <tr
                    key={territoire.cles.join("-")}
                    className={`border-t border-filet ${index % 2 === 1 ? "bg-fond-carte-alt" : "bg-fond-carte"}`}
                  >
                    <th scope="row" className="px-3.5 py-3 text-left align-top">
                      <div className="font-ui text-[14px] font-bold text-texte">
                        {territoire.cles.map((cle) => LABEL_TERRITOIRE[cle]).join(" / ")}
                      </div>
                      {note && <div className="mt-0.5 font-ui text-[11px] font-medium text-texte-doux">{note}</div>}
                    </th>
                    <td className="px-3.5 py-3 align-top font-ui text-[13px] font-semibold text-texte">
                      {territoire.rentree && <DateLongue iso={territoire.rentree.date_debut} capitaliser />}
                    </td>
                    <td className="px-3.5 py-3 align-top">
                      <div className="grid grid-cols-2 gap-x-5 gap-y-[7px]">
                        {territoire.vacances.map((v) => (
                          <div key={v.periode}>
                            <div className="font-ui text-[11px] font-semibold text-texte-doux">{v.periode}</div>
                            <div className="font-ui text-[13px] font-semibold text-texte">
                              {formaterDateCourte(v.date_debut)}
                              {v.date_fin ? ` → ${formaterDateCourte(v.date_fin)}` : ""}
                            </div>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-3.5 py-3 align-top font-ui text-[13px] font-semibold text-texte">
                      {territoire.finAnnee && <DateLongue iso={territoire.finAnnee.date_debut} capitaliser />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="mt-3 font-ui text-[12px] leading-[1.6] text-texte-doux">
          Dates de la Nouvelle-Calédonie et de Wallis-et-Futuna identiques dans la source consultée ;
          les deux territoires relèvent du même vice-rectorat.
        </p>
      </div>
    </section>
  );
}
