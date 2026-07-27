import Link from "next/link";
import { NOM_ASSISTANT } from "@/lib/constants";
import { ChampAdresse } from "@/components/ChampAdresse";
import { GaletAgent } from "@/components/GaletAgent";
import { FicheAnnoteeAccueil } from "./_components/FicheAnnoteeAccueil";
import { construireSlugRegion } from "@/lib/slug";

// Découpage administratif des régions françaises : un fait géographique
// stable, pas une donnée du Ministère à recalculer depuis l'API (cf.
// principe templating vs LLM/API, CLAUDE.md).
const REGIONS = [
  { nom: "Auvergne-Rhône-Alpes", departements: 12 },
  { nom: "Bourgogne-Franche-Comté", departements: 8 },
  { nom: "Bretagne", departements: 4 },
  { nom: "Centre-Val de Loire", departements: 6 },
  { nom: "Corse", departements: 2 },
  { nom: "Grand Est", departements: 10 },
  { nom: "Hauts-de-France", departements: 5 },
  { nom: "Île-de-France", departements: 8 },
  { nom: "Normandie", departements: 5 },
  { nom: "Nouvelle-Aquitaine", departements: 12 },
  { nom: "Occitanie", departements: 13 },
  { nom: "Pays de la Loire", departements: 5 },
  { nom: "Provence-Alpes-Côte d'Azur", departements: 6 },
];

const CARTES_COMPRENDRE = [
  {
    slug: "derogation",
    etiquette: "Secteur",
    etiquetteClass: "bg-action-pale text-action-dark",
    titre: "Dérogation : ce qui est possible",
    texte: "Qui décide, sur quels motifs, à quelle échéance.",
  },
  {
    slug: "valeur-ajoutee",
    etiquette: "Valeur ajoutée",
    etiquetteClass: "bg-positif-pale text-[#1F6B43]",
    titre: "Résultats obtenus, résultats attendus",
    texte:
      "Deux collèges au même taux de réussite peuvent être très différents. Ce que mesure l'écart, et comment il est calculé.",
  },
  {
    slug: "ips",
    etiquette: "IPS",
    etiquetteClass: "bg-descriptif-pale text-descriptif",
    titre: "L'IPS décrit les élèves, pas l'établissement",
    texte:
      "Ce que l'indice de position sociale mesure exactement, et pourquoi il n'entre pas dans la notation.",
  },
  {
    slug: "parcours",
    etiquette: "Parcours",
    etiquetteClass: "bg-attention-pale text-attention-dark",
    titre: "Accès de la 6ᵉ à la 3ᵉ",
    texte:
      "La part des élèves entrés en 6ᵉ qui atteignent la 3ᵉ dans le même collège. Ce que l'indicateur compte, et ce qu'il ne distingue pas.",
  },
];

export default function Page() {
  return (
    <div className="bg-fond-creme text-texte min-h-screen">
      {/* ===== HERO ===== */}
      <div className="mx-auto max-w-[1280px] px-4 pb-[50px] pt-[54px] text-center md:px-[50px] md:pb-[66px] md:pt-[74px]">
        <div className="mx-auto max-w-[720px]">
          <h1
            className="font-titre text-[36px] font-semibold leading-[1.06] text-texte md:text-[54px]"
            style={{ textWrap: "pretty" }}
          >
            Votre collège de secteur, au-delà de sa réputation.
          </h1>
          <p className="mx-auto mt-[18px] max-w-[600px] text-[15.5px] leading-[1.55] text-texte-doux md:text-[17.5px]">
            Entrez votre adresse. Résultats au brevet, progression des élèves, profil social —
            chaque chiffre du Ministère, avec de quoi le comparer.
          </p>

          <div className="mt-[34px] text-left">
            <div className="mx-auto max-w-[600px]">
              <ChampAdresse />
            </div>
            <p className="mt-3.5 text-[12.5px] text-texte-doux">
              Données du Ministère de l&apos;Éducation nationale · Sectorisation publiée par les
              conseils départementaux
            </p>
            <p className="mt-2.5 text-[13.5px] text-[#5C554B]">
              Vous connaissez déjà le nom du collège ?{" "}
              <Link
                href="/recherche"
                className="font-semibold text-action underline underline-offset-[3px] hover:text-action-dark"
              >
                Le rechercher directement
              </Link>
            </p>
          </div>
        </div>
      </div>

      <FicheAnnoteeAccueil />

      {/* ===== CAMILLE ===== */}
      <div className="px-4 py-10 md:px-[50px] md:py-14">
        <div className="mx-auto max-w-[900px] rounded-[20px] border border-agent bg-agent-pale px-5 py-6 md:px-8 md:py-[30px]">
          <div className="flex items-start gap-3.5 md:gap-[15px]">
            <GaletAgent taille="carte" />
            <p
              className="max-w-[620px] font-titre text-[16px] font-medium leading-[1.45] text-agent-ink md:text-[18px]"
              style={{ textWrap: "pretty" }}
            >
              {NOM_ASSISTANT}{" "}
              répond à partir des données affichées, et seulement d&apos;elles. Quand l&apos;information
              n&apos;existe pas, elle le dit.
            </p>
          </div>

          <div className="mx-auto mt-5 flex max-w-[640px] flex-col gap-2.5 md:mt-[22px]">
            <div className="max-w-[74%] self-end rounded-[14px_14px_4px_14px] border border-[#EBDCC0] bg-fond-carte px-3.5 py-2.5 font-ui text-[13.5px] font-medium leading-[1.5] text-texte">
              Qu&apos;est-ce que l&apos;IPS de ce collège veut dire ?
            </div>
            <div className="flex max-w-[82%] items-end gap-2">
              <div
                className="mb-0.5 h-5 w-[22px] flex-none"
                style={{ borderRadius: "46% 46% 46% 7px", background: "linear-gradient(150deg,#E79A2C,#C97D14)" }}
              />
              <div className="rounded-[14px_14px_14px_4px] border border-[#E2CDA3] bg-[#F2E2C4] px-3.5 py-3 font-ui text-[13.5px] leading-[1.6] text-agent-ink">
                L&apos;IPS mesure le milieu social des familles des élèves. Celui-ci est à{" "}
                <b className="text-[#201C17]">108</b>, la moyenne nationale est à{" "}
                <b className="text-[#201C17]">106</b>. C&apos;est une information sur le public
                accueilli, pas sur l&apos;établissement.
              </div>
            </div>

            <div className="mt-1.5 max-w-[74%] self-end rounded-[14px_14px_4px_14px] border border-[#EBDCC0] bg-fond-carte px-3.5 py-2.5 font-ui text-[13.5px] font-medium leading-[1.5] text-texte">
              Est-ce qu&apos;il y a une bonne ambiance dans ce collège ?
            </div>
            <div className="flex max-w-[82%] items-end gap-2">
              <div
                className="mb-0.5 h-5 w-[22px] flex-none"
                style={{ borderRadius: "46% 46% 46% 7px", background: "linear-gradient(150deg,#E79A2C,#C97D14)" }}
              />
              <div className="rounded-[14px_14px_14px_4px] border border-[#E2CDA3] bg-[#F2E2C4] px-3.5 py-3 font-ui text-[13.5px] leading-[1.6] text-agent-ink">
                Je n&apos;ai pas cette information. Les données publiques ne mesurent ni le climat
                scolaire, ni la qualité de l&apos;équipe éducative. Je peux en revanche vous donner
                les résultats, l&apos;écart aux résultats attendus et le profil des élèves.
              </div>
            </div>
          </div>

          <div className="mx-auto mt-4 flex max-w-[640px] justify-end md:mt-[18px]">
            <Link
              href="/assistant"
              className="rounded-[13px] bg-agent px-5 py-3 font-ui text-[13.5px] font-extrabold text-agent-ink hover:bg-agent-dark"
            >
              Poser ma question →
            </Link>
          </div>
        </div>
      </div>

      {/* ===== FAIT PAR UN PARENT ===== */}
      <div className="px-4 pb-10 md:px-[50px] md:pb-14">
        <div className="mx-auto flex max-w-[900px] gap-5 rounded-[4px_16px_16px_4px] border border-filet border-l-[3px] border-l-action bg-fond-carte px-5 py-6 md:gap-6 md:px-[30px] md:py-[26px]">
          <div className="flex-1">
            <div className="font-titre text-[19px] font-semibold text-texte md:text-[22px]">
              Ce site est fait par un parent
            </div>
            <p
              className="mt-2.5 max-w-[660px] text-[14px] leading-[1.7] text-[#4E463C] md:mt-[11px] md:text-[15px]"
              style={{ textWrap: "pretty" }}
            >
              Ma fille entre bientôt au collège. Comme beaucoup de parents, j&apos;ai voulu savoir ce
              que valaient les réputations qui circulent sur les établissements de ma ville. Je
              n&apos;ai trouvé que des classements. J&apos;ai fini par lire les données du Ministère
              moi-même — et j&apos;y ai découvert des indicateurs dont je n&apos;avais jamais entendu
              parler. Ce site est ce que j&apos;aurais voulu trouver.
            </p>
            <div className="mt-3 md:mt-3.5">
              <Link
                href="/a-propos"
                className="font-ui text-[13px] font-semibold text-action underline underline-offset-[3px] hover:text-action-dark md:text-[13.5px]"
              >
                → À propos
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* ===== EXPLORER PAR TERRITOIRE ===== */}
      <div className="border-t border-filet px-4 py-9 md:px-[50px] md:py-[50px]">
        <div className="mx-auto max-w-[1080px]">
          <div className="flex items-baseline justify-between gap-3.5">
            <div>
              <div className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-action md:text-[11.5px]">
                Explorer
              </div>
              <div className="mt-1 font-titre text-[22px] font-semibold text-texte md:text-[28px]">
                Par territoire
              </div>
            </div>
            <Link
              href="/region"
              className="font-ui text-[12px] font-semibold text-action underline underline-offset-[3px] hover:text-action-dark md:text-[13px]"
            >
              Départements &amp; académies →
            </Link>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-2.5 md:hidden">
            {REGIONS.slice(0, 4).map((r) => (
              <Link
                key={r.nom}
                href={`/region/${construireSlugRegion(r.nom)}`}
                className="rounded-xl border border-filet bg-fond-carte px-3.5 py-3"
              >
                <div className="font-titre text-[14px] font-semibold text-texte">{r.nom}</div>
                <div className="mt-0.5 font-ui text-[11px] font-medium text-texte-doux">
                  {r.departements} départements
                </div>
              </Link>
            ))}
          </div>
          <div className="mt-3 md:hidden">
            <Link
              href="/region"
              className="font-ui text-[12.5px] font-semibold text-action underline underline-offset-[3px] hover:text-action-dark"
            >
              Toutes les régions
            </Link>
          </div>

          <div className="mt-5 hidden grid-cols-4 gap-2.5 md:grid">
            {REGIONS.map((r) => (
              <Link
                key={r.nom}
                href={`/region/${construireSlugRegion(r.nom)}`}
                className="rounded-xl border border-filet bg-fond-carte px-3.5 py-3.5 hover:border-filet-fonce"
              >
                <div className="font-titre text-[15px] font-semibold text-texte">{r.nom}</div>
                <div className="mt-0.5 font-ui text-[11.5px] font-medium text-texte-doux">
                  {r.departements} départements
                </div>
              </Link>
            ))}
            <div className="col-span-3 flex flex-wrap items-center gap-3 rounded-xl border border-dashed border-filet-fonce bg-fond-sable px-3.5 py-3.5">
              <span className="font-ui text-[11px] font-bold uppercase tracking-[0.07em] text-[#5F574B]">
                Outre-mer
              </span>
              <span className="font-ui text-[13px] font-semibold text-[#5C554B]">
                Guadeloupe · Martinique · Guyane · La Réunion · Mayotte
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ===== COMPRENDRE ===== */}
      <div className="border-t border-filet bg-fond-sable px-4 py-9 md:px-[50px] md:py-[56px]">
        <div className="mx-auto max-w-[1080px]">
          <div className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-action md:text-[11.5px]">
            Comprendre
          </div>
          <div className="mt-1 font-titre text-[22px] font-semibold text-texte md:text-[28px]">
            Lire une fiche sans se tromper
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-4">
            {CARTES_COMPRENDRE.map((carte) => (
              <Link
                key={carte.slug}
                href={`/comprendre/${carte.slug}`}
                className="rounded-[14px] border border-filet bg-fond-carte p-[17px] hover:border-filet-fonce"
              >
                <span className={`rounded-[8px] px-2.5 py-0.5 font-ui text-[10px] font-bold ${carte.etiquetteClass}`}>
                  {carte.etiquette}
                </span>
                <div className="mt-2.5 font-titre text-[17px] font-semibold leading-[1.25] text-texte">
                  {carte.titre}
                </div>
                <div className="mt-1.5 font-ui text-[12.5px] leading-[1.55] text-texte-doux">
                  {carte.texte}
                </div>
              </Link>
            ))}
          </div>

          <Link
            href="/methodologie"
            className="mt-3 flex items-center gap-4.5 rounded-2xl border border-filet-fonce bg-fond-carte px-5 py-5 hover:border-filet-fonce/70 md:gap-[22px] md:px-6"
          >
            <div
              className="flex h-11 w-11 flex-none items-center justify-center rounded-[14px] font-notation text-xl font-bold text-white md:h-[52px] md:w-[52px] md:text-[24px]"
              style={{ background: "linear-gradient(150deg,#4FA772,#2E8F5E)" }}
            >
              A
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-titre text-[16px] font-semibold text-texte md:text-[19px]">
                La méthode de notation, en clair
              </div>
              <div className="mt-1 max-w-[640px] font-ui text-[12px] leading-[1.55] text-texte-doux md:text-[13px]">
                Quels indicateurs entrent dans la note A+ → B, leur poids, et ce qui en est
                volontairement exclu.
              </div>
            </div>
            <span className="flex-none font-ui text-[12.5px] font-bold text-action underline underline-offset-[3px] md:text-[13px]">
              Lire la méthode →
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
