import { redirect } from "next/navigation";
import { recupererRecherche } from "@/lib/recherche";
import {
  construireSlugRegion,
  construireSlugDepartement,
  construireSlugCollege,
  slugifier,
} from "@/lib/slug";
import type { EtablissementRecherche, CommuneRecherche } from "@/lib/types";
import { AgentBlock } from "@/components/AgentBlock";
import { RechercheBloc } from "@/components/RechercheBloc";
import { ListeColleges } from "@/components/ListeColleges";
import { CarteCommune } from "./_components/CarteCommune";

// Base de route ville (région/département/ville) à partir de la lignée
// géographique d'un résultat — chaque résultat peut venir d'une ville
// différente (contrairement à la page ville, où hrefBase est unique).
function hrefBaseVille(entite: {
  libelle_region: string;
  code_departement: string;
  libelle_departement: string;
  commune: string;
}): string {
  const regionSlug = construireSlugRegion(entite.libelle_region);
  const deptSlug = construireSlugDepartement(entite.code_departement, entite.libelle_departement);
  const villeSlug = slugifier(entite.commune);
  return `/region/${regionSlug}/departement/${deptSlug}/ville/${villeSlug}`;
}

function hrefEtablissement(e: EtablissementRecherche): string {
  return `${hrefBaseVille(e)}/college/${construireSlugCollege(e.nom, e.uai)}`;
}

function hrefCommune(c: CommuneRecherche): string {
  return hrefBaseVille(c);
}

// "50+" plutôt que "50" quand la liste a été coupée par la borne de
// résultats côté backend (recherche_tool.LIMITE_RESULTATS) — sans ça, une
// requête large ("e") affiche un total qui a l'air exact alors que ce n'est
// qu'une borne basse (cf. campagne de test /recherche).
function formaterCompte(n: number, tronque: boolean): string {
  return tronque ? `${n}+` : `${n}`;
}

export default async function Page({
  searchParams,
}: {
  // Next.js fournit un tableau si le paramètre est répété dans l'URL
  // (?q=a&q=b) — un cas réel (testé), pas seulement théorique : ignorer ça
  // et supposer `string` fait planter la page (`.trim is not a function`).
  searchParams: Promise<{ q?: string | string[] }>;
}) {
  const { q } = await searchParams;
  const qBrut = Array.isArray(q) ? q[0] : q;
  const query = (qBrut ?? "").trim();

  if (!query) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-20 text-center md:px-8">
        <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">Recherche</span>
        <h1 className="mt-1 font-baloo text-[26px] font-extrabold leading-tight text-texte">
          Chercher un collège ou une ville
        </h1>
        <p className="mt-1.5 text-[12.5px] text-texte-doux">
          Un nom de collège, une ville, un département…
        </p>
        <RechercheBloc />
      </div>
    );
  }

  const resultats = await recupererRecherche(query);

  // Règle V1 (docs/Design_system/recherche) : un résultat unique et non
  // ambigu route directement vers sa page, sans passer par la liste.
  if (resultats.etablissements.length === 1 && resultats.communes.length === 0) {
    redirect(hrefEtablissement(resultats.etablissements[0]));
  }
  if (resultats.communes.length === 1 && resultats.etablissements.length === 0) {
    redirect(hrefCommune(resultats.communes[0]));
  }

  const collegesAvecHrefBase = resultats.etablissements.map((e) => ({ ...e, hrefBase: hrefBaseVille(e) }));
  const aucunResultat = resultats.etablissements.length === 0 && resultats.communes.length === 0;

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-4.5 md:px-8">
      {/* ===== HERO ===== */}
      <div className="pt-3.5">
        <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">Recherche</span>
        <h1 className="mt-1 font-baloo text-[26px] font-extrabold leading-tight text-texte">
          Résultats pour « {query} »
        </h1>
        <p className="mt-1.5 text-[12.5px] text-texte-doux">
          {formaterCompte(resultats.communes.length, resultats.communes_tronquees)} commune
          {resultats.communes.length > 1 ? "s" : ""} ·{" "}
          {formaterCompte(resultats.etablissements.length, resultats.etablissements_tronques)} établissement
          {resultats.etablissements.length > 1 ? "s" : ""}
        </p>
      </div>

      <RechercheBloc placeholder="Rechercher un autre collège ou une autre ville…" />

      {aucunResultat ? (
        <div className="mt-7 rounded-2xl border-[1.5px] border-dashed border-filet-fonce bg-white py-10 text-center text-[13px] font-semibold text-texte-doux">
          Aucun résultat pour « {query} ». Vérifie l&apos;orthographe ou essaie un autre terme.
        </div>
      ) : (
        <>
          {resultats.communes.length > 0 && (
            <div className="mt-7">
              <h2 className="font-baloo text-[15px] font-extrabold text-texte">
                Communes · {formaterCompte(resultats.communes.length, resultats.communes_tronquees)}
              </h2>
              <div className="mt-2.5 flex flex-col gap-2.5">
                {resultats.communes.map((c) => (
                  <CarteCommune key={`${c.commune}-${c.code_departement}`} commune={c} href={hrefCommune(c)} />
                ))}
              </div>
            </div>
          )}

          {resultats.etablissements.length > 0 && (
            <div className="mt-7">
              <h2 className="font-baloo text-[15px] font-extrabold text-texte">
                Établissements · {formaterCompte(resultats.etablissements.length, resultats.etablissements_tronques)}
              </h2>

              {/* Barre de filtres — visuelle seule pour cette tranche, même
                  convention que la page ville avant l'activation des filtres
                  (cf. commit "Rend les filtres et le tri de la page ville
                  interactifs") : interactivité différée à une passe
                  ultérieure sur /recherche. */}
              <div className="mt-3.5 flex flex-wrap items-center gap-2">
                <span className="mr-0.5 text-[10px] font-bold uppercase tracking-wide text-texte-doux">Filtrer</span>
                <span className="rounded-[9px] border-[1.5px] border-filet bg-white px-2.5 py-1.5 text-[11px] font-semibold text-texte-doux">
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

              <ListeColleges
                colleges={collegesAvecHrefBase}
                tauxReussiteNational={resultats.taux_reussite_national}
              />
            </div>
          )}
        </>
      )}

      <AgentBlock exemple={`Aide-moi à comparer les résultats de "${query}"`} />
    </div>
  );
}
