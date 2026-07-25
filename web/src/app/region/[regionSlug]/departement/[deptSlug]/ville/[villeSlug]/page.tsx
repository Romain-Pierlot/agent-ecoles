import Link from "next/link";
import { notFound } from "next/navigation";
import { recupererVille } from "@/lib/geographie";
import { formaterTaux } from "@/lib/format";
import { AgentBlock } from "@/components/AgentBlock";
import { FiltresEtListeColleges } from "@/components/FiltresEtListeColleges";

export default async function Page({
  params,
}: {
  params: Promise<{ regionSlug: string; deptSlug: string; villeSlug: string }>;
}) {
  const { regionSlug, deptSlug, villeSlug } = await params;

  const ville = await recupererVille(regionSlug, deptSlug, villeSlug);
  if (!ville) notFound();

  const hrefBase = `/region/${regionSlug}/departement/${deptSlug}/ville/${villeSlug}`;

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-4.5 md:px-8">
      {/* ===== FIL D'ARIANE ===== */}
      <div className="flex flex-wrap items-center gap-1.5 py-3.5 text-[12px] font-semibold text-texte-doux/70">
        <Link href="/" className="hover:text-texte-doux">Accueil</Link>
        <span className="text-filet-fonce">›</span>
        <Link href={`/region/${regionSlug}`} className="hover:text-texte-doux">
          {ville.libelle_region}
        </Link>
        <span className="text-filet-fonce">›</span>
        <Link href={`/region/${regionSlug}/departement/${deptSlug}`} className="hover:text-texte-doux">
          {ville.libelle_departement} ({ville.code_departement})
        </Link>
        <span className="text-filet-fonce">›</span>
        <span className="text-texte">{ville.commune}</span>
      </div>

      {/* ===== HERO ===== */}
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">Ville</span>
          <h1 className="mt-1 font-titre text-[30px] font-semibold leading-tight text-texte">
            Collèges à {ville.commune}
          </h1>
          <p className="mt-1.5 text-[12.5px] text-texte-doux">
            {ville.global.nb_etablissements} collèges · {ville.nb_publics} publics, {ville.nb_prives} privés
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-ui text-[22px] font-extrabold text-texte">{ville.global.nb_etablissements}</div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Collèges</div>
          </div>
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-ui text-[22px] font-extrabold text-positif">
              {formaterTaux(ville.global.taux_reussite_moyen)}
            </div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Réussite moyenne</div>
          </div>
        </div>
      </div>

      <FiltresEtListeColleges
        colleges={ville.colleges.map((c) => ({
          ...c,
          hrefBase,
          // Convention établie sur /recherche : chaque carte porte toujours
          // nom + ville + département, même ici où c'est déjà dans le
          // fil d'Ariane — pour qu'un copier-coller depuis n'importe quelle
          // liste de résultats donne toujours ces trois informations.
          commune: ville.commune,
          libelle_departement: ville.libelle_departement,
          code_departement: ville.code_departement,
        }))}
        tauxReussiteNational={ville.taux_reussite_national}
      />

      <AgentBlock exemple={`Comment choisir entre les collèges de ${ville.commune} ?`} />
    </div>
  );
}
