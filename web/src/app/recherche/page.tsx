import { recupererRecherche } from "@/lib/recherche";
import { lireFiltres, filtresActifs } from "@/lib/rechercheParams";
import { AgentBlock } from "@/components/AgentBlock";
import { RechercheBloc } from "@/components/RechercheBloc";
import { ResultatsRecherche } from "./_components/ResultatsRecherche";

// Next.js fournit un tableau si un paramètre est répété dans l'URL
// (?q=a&q=b) — un cas réel (testé), pas seulement théorique.
function premiereValeur(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const tousParams = await searchParams;
  const query = (premiereValeur(tousParams.q) ?? "").trim();

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

  const filtresInitiaux = lireFiltres((cle) => premiereValeur(tousParams[cle]));
  const filtresPresents = filtresActifs(filtresInitiaux);

  // Toujours un appel non filtré : le compte du hero doit porter sur la
  // recherche brute, jamais sur un lot déjà filtré (sinon le header
  // afficherait des comptes incohérents selon les filtres actifs).
  const resultatsBruts = await recupererRecherche(query);
  const resultats = filtresPresents ? await recupererRecherche(query, filtresInitiaux) : resultatsBruts;

  // Pas de redirection automatique sur un résultat unique (ancienne "Règle
  // V1", cf. decision_log.md) : la bascule instantanée, sans transition,
  // donnait l'impression d'un bug plutôt qu'un raccourci — la page de
  // résultats s'affiche désormais systématiquement, même à 1 résultat.
  const aucunResultat = resultatsBruts.etablissements.length === 0 && resultatsBruts.communes.length === 0;

  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-4.5 md:px-8">
      {/* ===== HERO ===== */}
      <div className="pt-3.5">
        <span className="text-[11px] font-bold uppercase tracking-[0.06em] text-action">Recherche</span>
        <h1 className="mt-1 font-baloo text-[26px] font-extrabold leading-tight text-texte">
          Résultats pour « {query} »
        </h1>
        <p className="mt-1.5 text-[12.5px] text-texte-doux">
          {resultatsBruts.communes_total} commune{resultatsBruts.communes_total > 1 ? "s" : ""} ·{" "}
          {resultatsBruts.etablissements_total} établissement{resultatsBruts.etablissements_total > 1 ? "s" : ""}
        </p>
      </div>

      <RechercheBloc placeholder="Rechercher un autre collège ou une autre ville…" />

      {aucunResultat ? (
        <div className="mt-7 rounded-2xl border-[1.5px] border-dashed border-filet-fonce bg-white py-10 text-center text-[13px] font-semibold text-texte-doux">
          Aucun résultat pour « {query} ». Vérifie l&apos;orthographe ou essaie un autre terme.
        </div>
      ) : (
        <ResultatsRecherche query={query} resultatsInitiaux={resultats} filtresInitiaux={filtresInitiaux} />
      )}

      <AgentBlock exemple={`Aide-moi à comparer les résultats de "${query}"`} />
    </div>
  );
}
