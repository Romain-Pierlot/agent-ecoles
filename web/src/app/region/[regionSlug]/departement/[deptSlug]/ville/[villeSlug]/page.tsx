import Link from "next/link";
import { notFound } from "next/navigation";
import { recupererVille } from "@/lib/geographie";
import { AgentBlock } from "@/components/AgentBlock";
import { RechercheBloc } from "@/components/RechercheBloc";
import { ListeColleges } from "./_components/ListeColleges";

function formaterTaux(taux: number | null): string {
  return taux === null ? "—" : `${taux.toFixed(0)} %`;
}

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
          {ville.libelle_departement}
        </Link>
        <span className="text-filet-fonce">›</span>
        <span className="text-texte">{ville.commune}</span>
      </div>

      {/* ===== HERO ===== */}
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">Ville</span>
          <h1 className="mt-1 font-baloo text-[30px] font-extrabold leading-tight text-texte">
            Collèges à {ville.commune}
          </h1>
          <p className="mt-1.5 text-[12.5px] text-texte-doux">
            {ville.global.nb_etablissements} collèges · {ville.nb_publics} publics, {ville.nb_prives} privés
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-baloo text-[22px] font-extrabold text-texte">{ville.global.nb_etablissements}</div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Collèges</div>
          </div>
          <div className="w-[123px] rounded-xl border-[1.5px] border-filet bg-white px-3.5 py-3 text-center">
            <div className="font-baloo text-[22px] font-extrabold text-positif">
              {formaterTaux(ville.global.taux_reussite_moyen)}
            </div>
            <div className="mt-0.5 text-[10px] font-semibold text-texte-doux">Réussite moyenne</div>
          </div>
        </div>
      </div>

      <RechercheBloc placeholder="Rechercher une autre ville, ou saisir une adresse pour trouver son secteur…" />

      {/* ===== BARRE DE FILTRES (visuelle — activation en phase C) ===== */}
      <div className="mt-3.5 flex flex-wrap items-center gap-2">
        <span className="mr-0.5 text-[10px] font-bold uppercase tracking-wide text-texte-doux">Filtrer</span>
        <span className="rounded-[9px] border-[1.5px] border-[#E9A9C0] bg-action-pale px-2.5 py-1.5 text-[11px] font-bold text-action-dark">
          Public / Privé ▾
        </span>
        <span className="rounded-[9px] border-[1.5px] border-filet bg-white px-2.5 py-1.5 text-[11px] font-semibold text-texte-doux">
          Dispositifs ▾
        </span>
        <span className="rounded-[9px] border-[1.5px] border-filet bg-white px-2.5 py-1.5 text-[11px] font-semibold text-texte-doux">
          Sections ▾
        </span>
        <span className="rounded-[9px] border-[1.5px] border-filet bg-white px-2.5 py-1.5 text-[11px] font-semibold text-texte-doux">
          Notation min. ▾
        </span>
      </div>

      {/* ===== TRI + RÉSULTATS (visuel — activation en phase C) ===== */}
      <div className="mt-3.5 flex items-center justify-between">
        <div className="text-[12px] font-bold text-texte-doux">{ville.colleges.length} résultats</div>
        <span className="rounded-[9px] border-[1.5px] border-filet bg-white px-2.5 py-1.5 text-[11px] font-semibold text-texte-doux">
          Trier : Notation ↓ ⇅
        </span>
      </div>

      <ListeColleges
        colleges={ville.colleges}
        hrefBase={hrefBase}
        tauxReussiteNational={ville.taux_reussite_national}
      />

      <AgentBlock exemple={`Comment choisir entre les collèges de ${ville.commune} ?`} />
    </div>
  );
}
