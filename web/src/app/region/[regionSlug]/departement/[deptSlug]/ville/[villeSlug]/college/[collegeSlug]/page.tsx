import Link from "next/link";
import { notFound } from "next/navigation";
import { extraireUaiDuSlug, deslugifier } from "@/lib/slug";
import { recupererEtablissement } from "@/lib/etablissement";
import { FicheIdentite } from "./_components/FicheIdentite";
import { ResultatsBrevet } from "./_components/ResultatsBrevet";
import { ValeurAjoutee } from "./_components/ValeurAjoutee";
import { PositionnementSocial } from "./_components/PositionnementSocial";
import { DispositifsExpliques } from "./_components/DispositifsExpliques";

const NOM_ASSISTANT = "Camille";

export default async function Page({
  params,
}: {
  params: Promise<{
    regionSlug: string;
    deptSlug: string;
    villeSlug: string;
    collegeSlug: string;
  }>;
}) {
  const { regionSlug, deptSlug, collegeSlug } = await params;

  const uai = extraireUaiDuSlug(collegeSlug);
  if (!uai) notFound();

  const fiche = await recupererEtablissement(uai);
  if (!fiche) notFound();

  return (
    <div className="min-h-screen bg-fond-creme font-figtree text-texte">
      {/* ===== TOP BAR ===== */}
      <div className="sticky top-0 z-40 border-b border-filet bg-fond-creme/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5 md:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="h-[27px] w-[27px] -rotate-6 rounded-[9px_7px_10px_6px] bg-action" />
            <span className="font-baloo text-[21px] font-extrabold text-texte">écoles</span>
          </Link>
          <div className="flex items-center gap-5.5">
            <div className="hidden items-center gap-5.5 text-[13px] font-semibold text-texte-doux md:flex">
              <Link href="/recherche" className="hover:text-texte">Chercher</Link>
              <Link href="/explorer" className="hover:text-texte">Explorer</Link>
              <Link href="/comprendre/ips" className="hover:text-texte">Comprendre</Link>
            </div>
            <Link
              href="/assistant"
              className="flex items-center gap-2 rounded-[18px] bg-action px-[15px] py-2 text-[12.5px] font-bold text-white"
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white font-baloo text-[11px] font-extrabold text-action">
                C
              </span>
              Demander à {NOM_ASSISTANT}
            </Link>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 pb-24 pt-4.5 md:px-8">
        {/* ===== FIL D'ARIANE ===== */}
        {/* Libellés pris sur les vraies données de l'établissement (avec
            accents), pas déduits des slugs d'URL (region/deptSlug/villeSlug)
            — une déslugification reste irréversible sur les accents (ex.
            "herault" ne redonne jamais "Hérault" par un simple algorithme). */}
        <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
          <Link href="/" className="hover:text-texte-doux">Accueil</Link>
          <span className="text-filet-fonce">›</span>
          <span>{fiche.identite.libelle_region ?? deslugifier(regionSlug)}</span>
          <span className="text-filet-fonce">›</span>
          <span>{fiche.identite.libelle_departement ?? deslugifier(deptSlug)}</span>
          <span className="text-filet-fonce">›</span>
          <span>{fiche.identite.commune}</span>
          <span className="text-filet-fonce">›</span>
          <span className="text-texte">{fiche.identite.nom}</span>
        </div>

        <FicheIdentite
          identite={fiche.identite}
          langues={fiche.langues}
          sectionsSportives={fiche.sections_sportives}
          zoneVacances={fiche.zone_vacances}
          prochainesVacances={fiche.prochaines_vacances}
        />

        <div className="mt-9">
          <ResultatsBrevet brevet={fiche.brevet} evolution={fiche.evolution} />
          <ValeurAjoutee valeurAjoutee={fiche.valeur_ajoutee} />
          <PositionnementSocial positionnementSocial={fiche.positionnement_social} />
        </div>

        <DispositifsExpliques identite={fiche.identite} />

        {/* ===== FOOTER ===== */}
        <div className="mt-11 flex flex-wrap items-center justify-between gap-2.5 border-t border-filet pt-5 text-[11px] font-semibold text-texte-doux">
          <span>Données officielles du Ministère de l&apos;Éducation nationale</span>
          <div className="flex gap-3">
            <Link href="/methodologie" className="hover:text-texte">Notre méthode</Link>
            <Link href="/sources" className="hover:text-texte">Sources</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
