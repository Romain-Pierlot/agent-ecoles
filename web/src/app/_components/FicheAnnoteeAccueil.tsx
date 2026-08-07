import Link from "next/link";
import { recupererEtablissement } from "@/lib/etablissement";
import { deriveBadgesDispositifs } from "@/lib/dispositifs";
import { classeStatutSecteur, classeBadgeDispositif } from "@/lib/tokens";
import { formaterDecimale, formaterPourcentage, formaterEcart } from "@/lib/format";
import { hrefBaseVille } from "@/lib/hrefsGeo";
import { construireSlugCollege } from "@/lib/slug";
import { NOTATION_GRADIENTS } from "@/components/CarteCollege";

// Extrait réel (pas des données inventées) : Collège Parc Impérial, Nice —
// choisi dans le handoff design pour son signal mêlé (bons résultats,
// note à l'écrit sous l'attendu), qui illustre bien "pas de classement".
const UAI_EXEMPLE = "0061339Y";

// eslint-disable-next-line no-restricted-syntax -- dégradé dynamique du donut des mentions au brevet, registre légitime cité dans docs/Design_system/REFERENCE.md
const COULEURS_MENTIONS = ["#1F6B43", "#4FA772", "#9BCBAF", "#DDD2BB"];

type Annotation = {
  numero: number;
  titre: string;
  texte: string;
  lien?: { label: string; href: string };
};

const ANNOTATIONS: Annotation[] = [
  {
    numero: 1,
    titre: "Trouvé depuis votre adresse.",
    texte: "La sectorisation est publiée département par département. Nous les rassemblons.",
  },
  {
    numero: 2,
    titre: "Une note de repère, pas un classement.",
    texte:
      "Quatre indicateurs de résultats, à poids égal. Le profil social des élèves n'y entre pas.",
    lien: { label: "La méthode", href: "/methodologie" },
  },
  {
    numero: 3,
    titre: "National et département, sous chaque chiffre.",
    texte: "Un taux seul ne se lit pas.",
  },
  {
    numero: 4,
    titre: "Résultats attendus, résultats obtenus.",
    texte: "L'écart entre les deux, compte tenu du profil des élèves.",
  },
];

function clamp(valeur: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, valeur));
}

function AnnotationTexte({ annotation }: { annotation: Annotation }) {
  return (
    <>
      <span className="font-ui text-[13px] font-bold leading-[1.4] text-texte">
        {annotation.titre}
      </span>{" "}
      <span className="font-ui text-[12px] leading-[1.55] text-texte-doux">{annotation.texte}</span>
      {annotation.lien && (
        <>
          {" "}
          <Link
            href={annotation.lien.href}
            className="font-ui text-[12px] font-semibold text-action underline underline-offset-2 hover:text-action-dark"
          >
            {annotation.lien.label}
          </Link>
        </>
      )}
    </>
  );
}

function PastilleNumero({ numero, className = "" }: { numero: number; className?: string }) {
  return (
    <span
      className={`flex h-[19px] w-[19px] flex-none items-center justify-center rounded-full bg-action font-ui text-[11px] font-extrabold text-white shadow-[0_2px_6px_rgba(191,74,42,.4)] ${className}`}
    >
      {numero}
    </span>
  );
}

function JaugeSociale({
  titre,
  valeur,
  min,
  max,
  labelMin,
  labelMax,
  moyenneNationale,
}: {
  titre: string;
  valeur: number;
  min: number;
  max: number;
  labelMin: string;
  labelMax: string;
  moyenneNationale: number;
}) {
  const pctValeur = clamp(((valeur - min) / (max - min)) * 100, 0, 100);
  const pctNational = clamp(((moyenneNationale - min) / (max - min)) * 100, 0, 100);

  return (
    <div className="rounded-[14px] border border-filet bg-fond-carte p-4 md:rounded-[14px]">
      <div className="flex items-baseline justify-between gap-2.5">
        <div className="flex items-center gap-1.5 font-ui text-[12px] font-bold text-texte md:text-[12.5px]">
          {titre}
          <span className="flex h-[15px] w-[15px] flex-none items-center justify-center rounded-full border border-filet-fonce font-ui text-[9px] font-bold leading-[13px] text-[#8A7A62]">
            ?
          </span>
        </div>
        <div className="font-ui text-[21px] font-extrabold text-descriptif md:text-[24px]">
          {formaterDecimale(valeur, valeur % 1 === 0 ? 0 : 1)}
        </div>
      </div>
      <div className="relative mt-3.5 h-[9px] rounded-full bg-descriptif-pale md:h-2.5">
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: `${pctValeur}%`, background: "linear-gradient(90deg,rgba(51,80,110,.4),#33506E)" }}
        />
        <div
          className="absolute top-1/2 h-5 w-[3px] -translate-x-1/2 -translate-y-1/2 rounded-sm bg-texte md:h-[22px]"
          style={{ left: `${pctNational}%` }}
        />
        <div
          className="absolute top-1/2 h-[15px] w-[15px] -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-fond-carte bg-descriptif md:h-[17px] md:w-[17px]"
          style={{ left: `${pctValeur}%` }}
        />
      </div>
      <div className="mt-1.5 flex justify-between font-ui text-[9.5px] font-semibold text-texte-doux md:text-[10px]">
        <span>
          {min} · {labelMin}
        </span>
        <span>
          {labelMax} · {max}
        </span>
      </div>
      <div className="mt-1 font-ui text-[10px] font-semibold text-texte-doux md:text-[10.5px]">
        Moyenne nationale {formaterDecimale(moyenneNationale, 0)} (trait)
      </div>
    </div>
  );
}

export async function FicheAnnoteeAccueil() {
  const fiche = await recupererEtablissement(UAI_EXEMPLE);
  if (!fiche || !fiche.brevet || !fiche.valeur_ajoutee || !fiche.positionnement_social) return null;

  const { identite, brevet, valeur_ajoutee, evolution, positionnement_social } = fiche;
  const badgesDispositifs = deriveBadgesDispositifs(identite);
  const gradient = identite.notation ? NOTATION_GRADIENTS[identite.notation] : null;
  const mentions = brevet.mentions;
  const totalCandidats = brevet.brevet_nb_candidats_general ?? 0;

  const stopsMentions = mentions.map((m, i) => {
    const debut = mentions.slice(0, i).reduce((s, mm) => s + (mm.taux_pct ?? 0), 0);
    const fin = debut + (m.taux_pct ?? 0);
    return `${COULEURS_MENTIONS[i]} ${debut}% ${fin}%`;
  });

  const hrefFiche = `${hrefBaseVille({
    libelle_region: identite.libelle_region ?? "",
    code_departement: identite.code_departement ?? "",
    libelle_departement: identite.libelle_departement ?? "",
    commune: identite.commune,
  })}/college/${construireSlugCollege(identite.nom, identite.uai)}`;

  const evolutionRecente = [...evolution].reverse().slice(-4);
  const dernierNational = evolutionRecente.at(-1)?.brevet_taux_reussite_national ?? null;
  const hauteurBarre = (v: number) => `${clamp(((v - 70) / 30) * 100, 4, 100)}%`;

  return (
    <div className="border-y border-filet bg-fond-sable">
      <div className="mx-auto max-w-[1280px] px-4 py-8 text-center md:px-[50px] md:pb-[60px] md:pt-[52px] md:text-left">
        <div className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-action md:text-[11.5px]">
          Une fiche établissement
        </div>
        <h2 className="mt-1.5 font-titre text-[25px] font-semibold leading-[1.1] text-texte md:text-[34px]">
          La fiche de synthèse de votre collège
        </h2>
        <p className="mx-auto mt-2 max-w-[560px] font-ui text-[13px] leading-[1.6] text-[#5C554B] md:mx-0 md:mt-3 md:max-w-none md:whitespace-nowrap md:text-[14.5px]">
          Résultats au brevet et leur évolution, écart aux résultats attendus, profil social des
          élèves, langues, sections et dispositifs.
        </p>

        {/* ===== DESKTOP : grille annotée ===== */}
        <div className="mt-[34px] hidden justify-center gap-8 md:grid md:grid-cols-[212px_690px_212px] md:items-start">
          <div className="pt-[26px] text-left">
            <div className="relative mb-[322px]">
              <AnnotationTexte annotation={ANNOTATIONS[0]} />
              <svg width="34" height="52" viewBox="0 0 34 52" fill="none" className="absolute -right-[33px] top-2 overflow-visible">
                <path d="M1 8 C 20 8, 14 30, 33 30" stroke="#C4B79F" strokeWidth="1.2" fill="none" />
              </svg>
            </div>
            <div className="relative">
              <AnnotationTexte annotation={ANNOTATIONS[2]} />
              <svg width="34" height="60" viewBox="0 0 34 60" fill="none" className="absolute -right-[33px] top-2.5 overflow-visible">
                <path d="M1 8 C 20 8, 14 44, 33 44" stroke="#C4B79F" strokeWidth="1.2" fill="none" />
              </svg>
            </div>
          </div>

          <ExtraitFiche
            identite={identite}
            badgesDispositifs={badgesDispositifs}
            gradient={gradient}
            langues={fiche.langues}
            sectionsSportives={fiche.sections_sportives}
            brevet={brevet}
            stopsMentions={stopsMentions}
            totalCandidats={totalCandidats}
            mentions={mentions}
            valeurAjoutee={valeur_ajoutee}
            positionnementSocial={positionnement_social}
            evolutionRecente={evolutionRecente}
            hauteurBarre={hauteurBarre}
            dernierNational={dernierNational}
          />

          <div className="pt-[26px] text-left">
            <div className="relative mb-[640px]">
              <AnnotationTexte annotation={ANNOTATIONS[1]} />
              <svg width="34" height="52" viewBox="0 0 34 52" fill="none" className="absolute -left-[33px] top-2 overflow-visible">
                <path d="M33 8 C 14 8, 20 34, 1 34" stroke="#C4B79F" strokeWidth="1.2" fill="none" />
              </svg>
            </div>
            <div className="relative">
              <AnnotationTexte annotation={ANNOTATIONS[3]} />
              <svg width="34" height="52" viewBox="0 0 34 52" fill="none" className="absolute -left-[33px] top-2 overflow-visible">
                <path d="M33 8 C 14 8, 20 30, 1 30" stroke="#C4B79F" strokeWidth="1.2" fill="none" />
              </svg>
            </div>
          </div>
        </div>

        {/* ===== MOBILE : pastilles numérotées ===== */}
        <div className="mt-[18px] text-left md:hidden">
          <div className="relative rounded-[16px] border border-filet-fonce bg-fond-creme p-3 shadow-[0_10px_26px_rgba(40,28,14,.1)]">
            <div className="rounded-xl border border-filet bg-fond-carte p-3.5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
                    <span className={`rounded-full px-2.5 py-0.5 font-ui text-[10px] font-bold ${classeStatutSecteur(identite.secteur)}`}>
                      {identite.type_etablissement} {identite.secteur.toLowerCase()}
                    </span>
                    <span className="font-ui text-[11px] font-semibold text-texte-doux">
                      {identite.commune} · {identite.libelle_departement} ({identite.code_departement})
                    </span>
                  </div>
                  <div className="font-titre text-[20px] font-semibold leading-[1.08] text-texte">
                    {identite.nom}
                  </div>
                  <div className="relative mt-1 inline-block pl-6 font-ui text-[11px] leading-[1.4] text-texte-doux">
                    <PastilleNumero numero={1} className="absolute left-0 top-1/2 -translate-y-1/2" />
                    {identite.adresse}, {identite.code_postal} {identite.commune}
                  </div>
                </div>
                <div className="relative flex-none text-center">
                  <PastilleNumero numero={2} className="absolute -left-2.5 -top-2" />
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-[13px] font-notation text-[22px] font-bold text-white"
                    style={gradient ? { backgroundImage: gradient.fond } : { backgroundColor: "var(--color-descriptif)" }}
                  >
                    {identite.notation ?? "—"}
                  </div>
                  <div className="mt-1 font-ui text-[8.5px] font-semibold text-texte-doux">
                    A+ → B ·{" "}
                    <Link href="/methodologie" className="text-action underline underline-offset-2">
                      méthode
                    </Link>
                  </div>
                </div>
              </div>

              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {badgesDispositifs.map((b) => (
                  <span key={b} className={`rounded-[8px] px-2.5 py-0.5 font-ui text-[10px] font-bold ${classeBadgeDispositif(b)}`}>
                    {b}
                  </span>
                ))}
              </div>

              {fiche.langues && (
                <div className="mt-3 grid grid-cols-2 gap-2.5 border-t border-dashed border-filet-fonce pt-[11px]">
                  <div>
                    <div className="font-ui text-[9px] font-bold uppercase tracking-[0.09em] text-[#8A7A62]">LV1</div>
                    <div className="mt-0.5 font-ui text-[11.5px] font-semibold text-texte">
                      {fiche.langues.lv1.join(" · ")}
                    </div>
                  </div>
                  <div>
                    <div className="font-ui text-[9px] font-bold uppercase tracking-[0.09em] text-[#8A7A62]">LV2</div>
                    <div className="mt-0.5 font-ui text-[11.5px] font-semibold text-texte">
                      {fiche.langues.lv2.join(" · ")}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-2.5 flex gap-2.5">
              <PastilleNumero numero={1} className="mt-0.5" />
              <p className="flex-1">
                <AnnotationTexte annotation={ANNOTATIONS[0]} />
              </p>
            </div>
            <div className="mt-2.5 flex gap-2.5">
              <PastilleNumero numero={2} className="mt-0.5" />
              <p className="flex-1">
                <AnnotationTexte annotation={ANNOTATIONS[1]} />
              </p>
            </div>

            <div className="mt-2.5 flex flex-col gap-2.5">
              <CarteResultat
                titre="Taux de réussite au brevet"
                valeur={formaterPourcentage(brevet.brevet_taux_reussite_general ?? 0, 0)}
                couleur={
                  (brevet.brevet_taux_reussite_general ?? 0) >= (brevet.taux_reussite_national ?? 0)
                    ? "#1F6B43"
                    : "#9A6714"
                }
                national={formaterPourcentage(brevet.taux_reussite_national ?? 0, 0)}
                departemental={formaterPourcentage(brevet.taux_reussite_departemental ?? 0, 0)}
                libelleDepartement={identite.libelle_departement}
                compact
              />
              <CarteResultat
                titre="Note moyenne à l'écrit"
                valeur={`${formaterDecimale(brevet.brevet_note_ecrit_general ?? 0, 1)}/20`}
                couleur={
                  (brevet.brevet_note_ecrit_general ?? 0) >= (brevet.note_ecrit_national ?? 0)
                    ? "#1F6B43"
                    : "#9A6714"
                }
                national={formaterDecimale(brevet.note_ecrit_national ?? 0, 1)}
                departemental={formaterDecimale(brevet.note_ecrit_departemental ?? 0, 1)}
                libelleDepartement={identite.libelle_departement}
                compact
              />
              <CarteResultat
                titre="Accès de la 6e à la 3e"
                valeur={formaterPourcentage(brevet.taux_acces_6eme_3eme ?? 0, 0)}
                couleur={
                  (brevet.taux_acces_6eme_3eme ?? 0) >= (brevet.taux_acces_6eme_3eme_national ?? 0)
                    ? "#1F6B43"
                    : "#9A6714"
                }
                national={formaterPourcentage(brevet.taux_acces_6eme_3eme_national ?? 0, 0)}
                departemental={formaterPourcentage(brevet.taux_acces_6eme_3eme_departemental ?? 0, 0)}
                libelleDepartement={identite.libelle_departement}
                compact
              />
            </div>
            <div className="mt-2.5 flex gap-2.5">
              <PastilleNumero numero={3} className="mt-0.5" />
              <p className="flex-1">
                <AnnotationTexte annotation={ANNOTATIONS[2]} />
              </p>
            </div>

            <div className="mt-2.5 rounded-xl border border-filet bg-fond-carte p-3.5">
              <div className="flex items-baseline justify-between gap-2.5">
                <div className="font-ui text-[12px] font-bold text-texte">Répartition des mentions</div>
                <div className="font-ui text-[11px] font-semibold text-texte-doux">
                  {totalCandidats} candidats
                </div>
              </div>
              <div className="mt-2.5 flex h-3.5 overflow-hidden rounded-full">
                {mentions.map((m, i) => (
                  <div key={m.libelle} style={{ width: `${m.taux_pct ?? 0}%`, background: COULEURS_MENTIONS[i] }} />
                ))}
              </div>
              <div className="mt-2.5 grid grid-cols-2 gap-x-3 gap-y-1.5">
                {mentions.map((m, i) => (
                  <div key={m.libelle} className="flex items-center gap-1.5 font-ui text-[11px] text-[#4E463C]">
                    <span className="h-[9px] w-[9px] flex-none rounded-[3px]" style={{ background: COULEURS_MENTIONS[i] }} />
                    {m.libelle} <b className="text-texte">{formaterPourcentage(m.taux_pct ?? 0, 1)}</b>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative mt-2.5 rounded-xl border border-filet bg-fond-carte p-3.5">
              <PastilleNumero numero={4} className="absolute -left-2 top-2.5" />
              <div className="font-ui text-[10.5px] font-bold uppercase tracking-[0.08em] text-positif">
                Valeur ajoutée
              </div>
              <div className="mt-2.5 flex flex-col gap-2.5">
                <BlocValeurAjoutee
                  titre="Écart à l'attendu · taux de réussite"
                  ecart={valeur_ajoutee.va_taux}
                  attendu={`${formaterDecimale(valeur_ajoutee.taux_attendu ?? 0, 1)} %`}
                  obtenu={`${formaterDecimale(valeur_ajoutee.taux_observe ?? 0, 1)} %`}
                  compact
                />
                <BlocValeurAjoutee
                  titre="Écart à l'attendu · note à l'écrit"
                  ecart={valeur_ajoutee.va_note}
                  attendu={formaterDecimale(valeur_ajoutee.note_attendue ?? 0, 1)}
                  obtenu={formaterDecimale(valeur_ajoutee.note_observee ?? 0, 1)}
                  compact
                />
              </div>
            </div>
            <div className="mt-2.5 flex gap-2.5">
              <PastilleNumero numero={4} className="mt-0.5" />
              <p className="flex-1">
                <AnnotationTexte annotation={ANNOTATIONS[3]} />
              </p>
            </div>

            <div className="mt-2.5 flex flex-col gap-2.5">
              <JaugeSociale
                titre="Indice de position sociale"
                valeur={positionnement_social.ips_moyen ?? 0}
                min={40}
                max={180}
                labelMin="très défavorisé"
                labelMax="très favorisé"
                moyenneNationale={positionnement_social.ips_national ?? 0}
              />
              <JaugeSociale
                titre="Mixité sociale"
                valeur={positionnement_social.ecart_type_ips ?? 0}
                min={10}
                max={50}
                labelMin="public homogène"
                labelMax="public mélangé"
                moyenneNationale={positionnement_social.ecart_type_ips_national ?? 0}
              />
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-center md:mt-[26px]">
          <Link
            href={hrefFiche}
            className="font-ui text-[13px] font-bold text-action underline underline-offset-[4px] hover:text-action-dark md:text-[14px]"
          >
            Voir la fiche complète →
          </Link>
        </div>
      </div>
    </div>
  );
}

function CarteResultat({
  titre,
  valeur,
  couleur,
  national,
  departemental,
  libelleDepartement,
  compact,
}: {
  titre: string;
  valeur: string;
  couleur: string;
  national: string;
  departemental: string;
  libelleDepartement: string | null;
  compact?: boolean;
}) {
  const [nombre, unite] = valeur.split(/(?=[%/])/);
  return (
    <div className={`rounded-[14px] border border-filet bg-fond-carte ${compact ? "p-3.5" : "p-4"}`}>
      <div className="font-ui text-[12.5px] font-bold leading-[1.3] text-texte">{titre}</div>
      <div className={`mt-2 font-ui font-extrabold leading-none ${compact ? "text-[34px]" : "text-[38px]"}`} style={{ color: couleur }}>
        {nombre}
        {unite && <span className={compact ? "text-[17px]" : "text-[19px]"}>{unite}</span>}
      </div>
      <div className="mt-2.5 flex flex-wrap gap-x-3 gap-y-1 border-t border-filet pt-2 font-ui text-[11.5px] text-texte-doux">
        <span>
          National <b className="text-texte">{national}</b>
        </span>
        <span>
          {libelleDepartement} <b className="text-texte">{departemental}</b>
        </span>
      </div>
    </div>
  );
}

function BlocValeurAjoutee({
  titre,
  ecart,
  attendu,
  obtenu,
  compact,
}: {
  titre: string;
  ecart: number | null;
  attendu: string;
  obtenu: string;
  compact?: boolean;
}) {
  const positif = (ecart ?? 0) >= 0;
  const fondClasse = positif ? "bg-positif-pale border-positif/25" : "bg-[#F6E7DF] border-[#E7CFC2]";
  const couleurValeur = positif ? "#1F6B43" : "#A84123";
  const couleurTexte = positif ? "text-[#3F5548]" : "text-[#6A4437]";

  return (
    <div className={`rounded-xl border p-3.5 ${fondClasse}`}>
      <div className="font-ui text-[11.5px] font-bold text-texte">{titre}</div>
      <div className={`mt-1.5 flex flex-wrap items-baseline gap-x-2.5 gap-y-1 ${compact ? "" : ""}`}>
        <div className={`font-ui font-extrabold leading-none ${compact ? "text-[28px]" : "text-[32px]"}`} style={{ color: couleurValeur }}>
          {formaterEcart(ecart ?? 0, 1)}
          <span className={compact ? "text-[14px]" : "text-[16px]"}> pts</span>
        </div>
        {compact && (
          <div className={`font-ui text-[11px] font-semibold ${couleurTexte}`}>
            attendu {attendu} → obtenu <b className="text-texte">{obtenu}</b>
          </div>
        )}
      </div>
      {!compact && (
        <div className={`mt-2.5 flex gap-1.5 border-t pt-2 font-ui text-[11.5px] font-semibold ${couleurTexte} ${positif ? "border-positif/25" : "border-[#E7CFC2]"}`}>
          <span>attendu {attendu}</span>
          <span>→</span>
          <span>
            obtenu <b className="text-texte">{obtenu}</b>
          </span>
        </div>
      )}
    </div>
  );
}

function ExtraitFiche({
  identite,
  badgesDispositifs,
  gradient,
  langues,
  sectionsSportives,
  brevet,
  stopsMentions,
  totalCandidats,
  mentions,
  valeurAjoutee,
  positionnementSocial,
  evolutionRecente,
  hauteurBarre,
  dernierNational,
}: {
  identite: import("@/lib/types").EtablissementIdentite;
  badgesDispositifs: string[];
  gradient: { fond: string; ombre: string } | null;
  langues: import("@/lib/types").LanguesOffertes | null;
  sectionsSportives: string[];
  brevet: import("@/lib/types").BrevetResultats;
  stopsMentions: string[];
  totalCandidats: number;
  mentions: import("@/lib/types").MentionDetail[];
  valeurAjoutee: import("@/lib/types").ValeurAjouteeDetail;
  positionnementSocial: import("@/lib/types").PositionnementSocial;
  evolutionRecente: import("@/lib/types").EvolutionPoint[];
  hauteurBarre: (v: number) => string;
  dernierNational: number | null;
}) {
  return (
    <div className="rounded-[18px] border border-filet-fonce bg-fond-creme p-5 shadow-[0_14px_34px_rgba(40,28,14,.11)]">
      <div className="rounded-[14px] border border-filet bg-fond-carte p-5">
        <div className="flex items-start justify-between gap-4.5">
          <div className="min-w-0 flex-1">
            <div className="mb-1.5 flex items-center gap-2.5">
              <span className={`rounded-full px-2.5 py-0.5 font-ui text-[11px] font-bold ${classeStatutSecteur(identite.secteur)}`}>
                {identite.type_etablissement} {identite.secteur.toLowerCase()}
              </span>
              <span className="font-ui text-[12px] font-semibold text-texte-doux">
                {identite.commune} · {identite.libelle_departement} ({identite.code_departement})
              </span>
            </div>
            <div className="font-titre text-[28px] font-semibold leading-[1.06] text-texte">{identite.nom}</div>
            <div className="mt-1.5 font-ui text-[12.5px] text-texte-doux">
              {identite.adresse}, {identite.code_postal} {identite.commune}
            </div>
            <div className="mt-3.5 flex flex-wrap gap-1.5">
              {badgesDispositifs.map((b) => (
                <span key={b} className={`rounded-[9px] px-2.5 py-0.5 font-ui text-[11px] font-bold ${classeBadgeDispositif(b)}`}>
                  {b}
                </span>
              ))}
            </div>
          </div>
          <div className="flex-none text-center">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-2xl font-notation text-[30px] font-bold text-white"
              style={gradient ? { backgroundImage: gradient.fond, boxShadow: gradient.ombre } : { backgroundColor: "var(--color-descriptif)" }}
            >
              {identite.notation ?? "—"}
            </div>
            <div className="mt-1.5 font-ui text-[10px] font-semibold text-texte-doux">
              A+ → B ·{" "}
              <Link href="/methodologie" className="text-action underline underline-offset-2 hover:text-action-dark">
                méthode
              </Link>
            </div>
          </div>
        </div>

        {langues && (
          <div className="mt-4 grid grid-cols-[1.15fr_1fr] gap-5 border-t border-dashed border-filet-fonce pt-4">
            <div>
              <div className="font-ui text-[9.5px] font-bold uppercase tracking-[0.09em] text-[#8A7A62]">
                Langues &amp; options
              </div>
              <div className="mt-2 grid grid-cols-2 gap-3.5">
                <div>
                  <div className="font-ui text-[10.5px] font-medium text-[#8A7A62]">LV1</div>
                  <div className="mt-0.5 font-ui text-[12.5px] font-semibold leading-[1.45] text-texte">
                    {langues.lv1.join(" · ")}
                  </div>
                </div>
                <div>
                  <div className="font-ui text-[10.5px] font-medium text-[#8A7A62]">LV2</div>
                  <div className="mt-0.5 font-ui text-[12.5px] font-semibold leading-[1.45] text-texte">
                    {langues.lv2.join(" · ")}
                  </div>
                </div>
              </div>
            </div>
            {sectionsSportives.length > 0 && (
              <div>
                <div className="font-ui text-[9.5px] font-bold uppercase tracking-[0.09em] text-[#8A7A62]">
                  Section sportive
                </div>
                <div className="mt-2 font-ui text-[12.5px] font-semibold leading-[1.45] text-texte">
                  {sectionsSportives.join(" · ")}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3">
        <CarteResultat
          titre="Taux de réussite au brevet"
          valeur={formaterPourcentage(brevet.brevet_taux_reussite_general ?? 0, 0)}
          couleur={(brevet.brevet_taux_reussite_general ?? 0) >= (brevet.taux_reussite_national ?? 0) ? "#1F6B43" : "#9A6714"}
          national={formaterPourcentage(brevet.taux_reussite_national ?? 0, 0)}
          departemental={formaterPourcentage(brevet.taux_reussite_departemental ?? 0, 0)}
          libelleDepartement={identite.libelle_departement}
        />
        <CarteResultat
          titre="Note moyenne à l'écrit"
          valeur={`${formaterDecimale(brevet.brevet_note_ecrit_general ?? 0, 1)}/20`}
          couleur={(brevet.brevet_note_ecrit_general ?? 0) >= (brevet.note_ecrit_national ?? 0) ? "#1F6B43" : "#9A6714"}
          national={formaterDecimale(brevet.note_ecrit_national ?? 0, 1)}
          departemental={formaterDecimale(brevet.note_ecrit_departemental ?? 0, 1)}
          libelleDepartement={identite.libelle_departement}
        />
        <CarteResultat
          titre="Accès de la 6e à la 3e"
          valeur={formaterPourcentage(brevet.taux_acces_6eme_3eme ?? 0, 0)}
          couleur={(brevet.taux_acces_6eme_3eme ?? 0) >= (brevet.taux_acces_6eme_3eme_national ?? 0) ? "#1F6B43" : "#9A6714"}
          national={formaterPourcentage(brevet.taux_acces_6eme_3eme_national ?? 0, 0)}
          departemental={formaterPourcentage(brevet.taux_acces_6eme_3eme_departemental ?? 0, 0)}
          libelleDepartement={identite.libelle_departement}
        />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <div className="rounded-[14px] border border-filet bg-fond-carte p-4">
          <div className="font-ui text-[12.5px] font-bold text-texte">Répartition des mentions</div>
          <div className="mt-3.5 flex items-center gap-3.5">
            <div
              className="flex h-[104px] w-[104px] flex-none items-center justify-center rounded-full"
              style={{ background: `conic-gradient(${stopsMentions.join(",")})` }}
            >
              <div className="flex h-16 w-16 flex-col items-center justify-center rounded-full bg-fond-carte">
                <div className="font-ui text-[20px] font-extrabold leading-none text-texte">{totalCandidats}</div>
                <div className="mt-0.5 font-ui text-[9px] font-medium text-texte-doux">candidats</div>
              </div>
            </div>
            <div className="flex flex-1 flex-col gap-1.5">
              {mentions.map((m, i) => (
                <div key={m.libelle} className="flex items-center gap-2 font-ui text-[11.5px] text-[#4E463C]">
                  <span className="h-2.5 w-2.5 flex-none rounded-[3px]" style={{ background: COULEURS_MENTIONS[i] }} />
                  {m.libelle} <b className="text-texte">{formaterPourcentage(m.taux_pct ?? 0, 1)}</b>{" "}
                  <span className="text-[#8A7A62]">· {m.nb_eleves}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-[14px] border border-filet bg-fond-carte p-4">
          <div className="flex items-baseline justify-between gap-2.5">
            <div className="font-ui text-[12.5px] font-bold text-texte">Évolution du taux de réussite</div>
            <div className="flex items-center gap-1.5 font-ui text-[10.5px] text-texte-doux">
              <span className="w-4 border-t-2 border-dashed border-filet-fonce" />
              National
            </div>
          </div>
          <div className="mt-3.5 flex gap-2.5">
            <div className="relative h-[104px] w-5 flex-none font-ui text-[9.5px] font-medium text-[#8A7A62]">
              <span className="absolute -top-1 right-0">100</span>
              <span className="absolute right-0 top-[30px]">90</span>
              <span className="absolute right-0 top-[65px]">80</span>
              <span className="absolute -bottom-1 right-0">70</span>
            </div>
            <div className="relative h-[104px] flex-1 border-b border-[#C9BCA5] border-l border-filet">
              {dernierNational !== null && (
                <div
                  className="absolute left-0 right-0 border-t-2 border-dashed border-filet-fonce"
                  style={{ bottom: hauteurBarre(dernierNational) }}
                />
              )}
              <div className="absolute inset-0 flex items-end justify-around px-1.5">
                {evolutionRecente.map((e) => (
                  <div
                    key={e.session}
                    className="relative w-[38px] rounded-t-[4px]"
                    style={{
                      height: hauteurBarre(e.brevet_taux_reussite_general ?? 0),
                      background: "linear-gradient(180deg,#4FA772,#2E8F5E)",
                    }}
                  >
                    <span className="absolute -top-4 left-0 right-0 text-center font-ui text-[10.5px] font-bold text-[#1F6B43]">
                      {formaterDecimale(e.brevet_taux_reussite_general ?? 0, 0)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="ml-[29px] mt-1.5 flex justify-around font-ui text-[10.5px] font-medium text-texte-doux">
            {evolutionRecente.map((e) => (
              <span key={e.session} className="w-[38px] text-center">
                {e.session}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 rounded-[14px] border border-filet bg-fond-carte p-4">
        <div className="font-ui text-[11.5px] font-bold uppercase tracking-[0.08em] text-positif">Valeur ajoutée</div>
        <div className="mt-2.5 grid grid-cols-2 gap-3">
          <BlocValeurAjoutee
            titre="Écart à l'attendu · taux de réussite"
            ecart={valeurAjoutee.va_taux}
            attendu={`${formaterDecimale(valeurAjoutee.taux_attendu ?? 0, 1)} %`}
            obtenu={`${formaterDecimale(valeurAjoutee.taux_observe ?? 0, 1)} %`}
          />
          <BlocValeurAjoutee
            titre="Écart à l'attendu · note à l'écrit"
            ecart={valeurAjoutee.va_note}
            attendu={formaterDecimale(valeurAjoutee.note_attendue ?? 0, 1)}
            obtenu={formaterDecimale(valeurAjoutee.note_observee ?? 0, 1)}
          />
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <JaugeSociale
          titre="Indice de position sociale"
          valeur={positionnementSocial.ips_moyen ?? 0}
          min={40}
          max={180}
          labelMin="très défavorisé"
          labelMax="très favorisé"
          moyenneNationale={positionnementSocial.ips_national ?? 0}
        />
        <JaugeSociale
          titre="Mixité sociale"
          valeur={positionnementSocial.ecart_type_ips ?? 0}
          min={10}
          max={50}
          labelMin="public homogène"
          labelMax="public mélangé"
          moyenneNationale={positionnementSocial.ecart_type_ips_national ?? 0}
        />
      </div>
    </div>
  );
}
