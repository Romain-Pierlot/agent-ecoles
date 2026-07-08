import Link from "next/link";
import type { EtablissementIdentite, LanguesOffertes, ProchainesVacances } from "@/lib/types";
import { slugifier } from "@/lib/slug";

const NOM_ASSISTANT = "Camille";

const NOTATION_CLASSES: Record<string, string> = {
  "A+": "bg-notation-a-plus",
  "A": "bg-notation-a",
  "A-": "bg-notation-a-moins",
  "B+": "bg-notation-b-plus",
  "B": "bg-notation-b",
};

const SECTIONS: { cle: keyof EtablissementIdentite; label: string }[] = [
  { cle: "section_sport", label: "Section sportive" },
  { cle: "section_arts", label: "Section arts" },
  { cle: "section_cinema", label: "Section cinéma" },
  { cle: "section_theatre", label: "Section théâtre" },
  { cle: "section_internationale", label: "Section internationale" },
  { cle: "section_europeenne", label: "Section européenne" },
];

function formaterDate(iso: string): string {
  const [annee, mois, jour] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" }).format(
    new Date(annee, mois - 1, jour)
  );
}

function BandeauVacances({ zone, prochainesVacances }: { zone: string; prochainesVacances: ProchainesVacances }) {
  return (
    <div className="mt-4 flex items-center gap-2.5 rounded-2xl border border-filet bg-fond-carte px-3.5 py-2.5">
      <span className="font-baloo text-xl">🗓️</span>
      <p className="text-[12.5px] leading-snug text-texte-doux">
        <b className="text-texte">
          Prochaines vacances (Zone {zone})
        </b>{" "}
        — {prochainesVacances.periode} : {formaterDate(prochainesVacances.date_debut)}
        {prochainesVacances.date_fin ? ` → ${formaterDate(prochainesVacances.date_fin)}` : ""}
      </p>
    </div>
  );
}

function BlocLanguesEtSports({
  langues,
  sectionsSportives,
}: {
  langues: LanguesOffertes | null;
  sectionsSportives: string[];
}) {
  const groupesLangues: { label: string; valeurs: string[] }[] = langues
    ? [
        { label: "LV1", valeurs: langues.lv1 },
        { label: "LV2", valeurs: langues.lv2 },
        { label: "Langues et cultures de l'Antiquité", valeurs: langues.lca },
      ].filter((g) => g.valeurs.length > 0)
    : [];

  return (
    <div className="mt-4.5 grid gap-4 border-t border-dashed border-filet-fonce pt-4.5 sm:grid-cols-2">
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wide text-texte-doux/70">
          Langues &amp; options
        </span>
        {groupesLangues.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-4">
            {groupesLangues.map((g) => (
              <div key={g.label}>
                <div className="text-[10px] font-semibold text-texte-doux/70">{g.label}</div>
                <div className="text-[13.5px] font-bold text-texte">{g.valeurs.join(" · ")}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-2 text-[12.5px] font-semibold text-texte-doux">Données non disponibles</div>
        )}
      </div>
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wide text-texte-doux/70">
          Section sportive
        </span>
        {sectionsSportives.length > 0 ? (
          <div className="mt-2 text-[13.5px] font-bold text-texte">{sectionsSportives.join(" · ")}</div>
        ) : (
          <div className="mt-2 text-[12.5px] font-semibold text-texte-doux">
            Aucune donnée répertoriée
            <br />à vérifier auprès de l&apos;établissement.
          </div>
        )}
      </div>
    </div>
  );
}

export function FicheIdentite({
  identite,
  langues,
  sectionsSportives,
  zoneVacances,
  prochainesVacances,
}: {
  identite: EtablissementIdentite;
  langues: LanguesOffertes | null;
  sectionsSportives: string[];
  zoneVacances: string | null;
  prochainesVacances: ProchainesVacances | null;
}) {
  const badges: string[] = [];
  if (identite.appartenance_education_prioritaire) badges.push(identite.appartenance_education_prioritaire);
  if (identite.ulis) badges.push("ULIS");
  if (identite.segpa) badges.push("SEGPA");
  for (const s of SECTIONS) {
    if (identite[s.cle]) badges.push(s.label);
  }

  const coordonnees: { label: string; valeur: string; classe?: string; lien?: string }[] = [
    { label: "Identifiant UAI", valeur: identite.uai, classe: "font-jetbrains" },
  ];
  if (identite.telephone) coordonnees.push({ label: "Téléphone", valeur: identite.telephone });
  if (identite.mail) coordonnees.push({ label: "Courriel", valeur: identite.mail, classe: "text-positif" });
  if (identite.web) {
    coordonnees.push({
      label: "Site internet",
      valeur: identite.web.replace(/^https?:\/\//, ""),
      classe: "text-action-dark underline underline-offset-2",
      lien: identite.web,
    });
  }
  if (zoneVacances) coordonnees.push({ label: "Zone de vacances", valeur: `Zone ${zoneVacances}` });
  if (identite.libelle_academie) {
    coordonnees.push({
      label: "Académie",
      valeur: identite.libelle_academie,
      classe: "text-action-dark underline underline-offset-2",
      lien: `/academie/${slugifier(identite.libelle_academie)}`,
    });
  }

  return (
    <div className="grid gap-[22px] md:grid-cols-[1fr_340px]" id="identite">
      {/* Carte identité */}
      <div className="rounded-[26px_22px_26px_24px] border-2 border-filet bg-white p-[26px] shadow-[0_3px_14px_rgba(34,59,48,0.06)]">
        <div className="flex items-start justify-between gap-4.5">
          <div className="flex-1">
            <div className="mb-2 flex items-center gap-2">
              <span className="rounded-full bg-positif-pale px-3 py-1 text-[11px] font-bold text-positif">
                {identite.type_etablissement} {identite.secteur.toLowerCase()}
              </span>
              <span className="text-[12.5px] font-semibold text-texte-doux">{identite.commune}</span>
            </div>
            <h1 className="font-baloo text-[34px] font-extrabold leading-[1.05] text-texte">{identite.nom}</h1>
            {identite.adresse && (
              <p className="mt-2 text-[13.5px] text-texte-doux">
                {identite.adresse}
                {identite.code_postal ? `, ${identite.code_postal} ${identite.commune}` : ""}
              </p>
            )}
          </div>

          {identite.notation && (
            <div className="flex-none text-center">
              <div
                className={`flex h-20 w-20 -rotate-3 items-center justify-center rounded-[24px_20px_24px_22px] shadow-lg ${
                  NOTATION_CLASSES[identite.notation] ?? "bg-descriptif"
                }`}
              >
                <span className="font-baloo text-4xl font-extrabold text-white">{identite.notation}</span>
              </div>
              <div className="mt-2 text-[9.5px] font-bold uppercase tracking-wide text-texte-doux/70">
                Notation
              </div>
              <div className="mt-0.5 text-[10px] font-semibold text-texte-doux/60">
                A+ → B ·{" "}
                <Link href="/methodologie" className="text-action-dark underline underline-offset-2">
                  méthode
                </Link>
              </div>
            </div>
          )}
        </div>

        {badges.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {badges.map((b) => (
              <span
                key={b}
                className="rounded-xl border border-filet bg-fond-sable/40 px-3 py-1 text-[11.5px] font-bold text-texte-doux"
              >
                {b}
              </span>
            ))}
          </div>
        )}

        <div className="mt-5 grid grid-cols-2 gap-x-5 gap-y-3.5 border-t border-dashed border-filet-fonce pt-5 sm:grid-cols-3">
          {coordonnees.map((c) => (
            <div key={c.label}>
              <div className="text-[10px] font-bold uppercase tracking-wide text-texte-doux/70">{c.label}</div>
              {c.lien ? (
                <a href={c.lien} className={`mt-0.5 block text-[13.5px] font-semibold ${c.classe ?? "text-texte"}`}>
                  {c.valeur}
                </a>
              ) : (
                <div className={`mt-0.5 text-[13.5px] font-semibold ${c.classe ?? "text-texte"}`}>{c.valeur}</div>
              )}
            </div>
          ))}
        </div>

        <BlocLanguesEtSports langues={langues} sectionsSportives={sectionsSportives} />
        {zoneVacances && prochainesVacances && (
          <BandeauVacances zone={zoneVacances} prochainesVacances={prochainesVacances} />
        )}
      </div>

      {/* Rail droit */}
      <div className="flex flex-col gap-2.5">
        {/* Carte scolaire : à venir dans un chantier séparé (cf. decision_log.md
            S1.4) — cadre conservé pour garder la proportion du rail droit
            cohérente avec la carte identité, plutôt que de laisser la carte
            assistant seule et disproportionnée. */}
        <div className="flex h-[150px] flex-col items-center justify-center gap-1.5 rounded-[22px_18px_22px_20px] border-2 border-dashed border-filet-fonce bg-fond-sable/30 text-center">
          <span className="text-2xl">🗺️</span>
          <span className="px-4 text-[12px] font-semibold text-texte-doux">
            Carte de secteur — à venir
          </span>
        </div>

        {/* Carte assistant (compacte) */}
        <div className="rounded-[22px_18px_22px_20px] bg-gradient-to-br from-action to-action-dark p-4 text-white shadow-lg">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8.5 w-8.5 flex-none items-center justify-center rounded-full bg-white font-baloo text-base font-extrabold text-action">
              C
            </div>
            <div className="leading-tight">
              <div className="font-baloo text-[13.5px] font-bold">Comprendre les chiffres</div>
              <div className="text-[10.5px] opacity-85">{NOM_ASSISTANT} · à partir des données affichées</div>
            </div>
          </div>
          <p className="mt-2.5 text-[11.5px] leading-relaxed opacity-90">
            {NOM_ASSISTANT} explique et nuance les indicateurs de cette page en s&apos;appuyant sur les sources
            officielles de l&apos;Éducation nationale.
          </p>
          <Link
            href="/assistant"
            className="mt-2.5 block rounded-xl bg-white py-2.5 text-center font-baloo text-[12.5px] font-extrabold text-action-dark"
          >
            Interroger {NOM_ASSISTANT} →
          </Link>
        </div>
      </div>
    </div>
  );
}
