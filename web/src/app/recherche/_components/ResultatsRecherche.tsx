"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { RechercheResultats } from "@/lib/types";
import { recupererRecherche } from "@/lib/recherche";
import { hrefBaseVille } from "@/lib/hrefsGeo";
import {
  filtresEtablissementsActifs,
  construireParams,
  type FiltresRecherche,
  type FiltresEtablissements,
  type TriCommunes,
  type Direction,
} from "@/lib/rechercheParams";
import { FiltresEtListeColleges } from "@/components/FiltresEtListeColleges";
import { ListeCommunes } from "./ListeCommunes";

// Le total est réel (COUNT(*) sans LIMIT côté backend, cf.
// agent/tools/recherche_tool.py) — la liste affichée reste bornée à
// LIMITE_RESULTATS. Formulation explicite ("affichage limité à N") plutôt
// que "(N affichés)" : sans ça, le bouton "voir plus" (qui ne fait que
// déplier ce lot déjà plafonné, jamais aller chercher au-delà) donnait
// l'impression d'être cassé une fois les N atteints — retour utilisateur
// du 2026-07-24.
function formaterTitreSection(total: number, nbAffiches: number, tronque: boolean): string {
  return tronque ? `${total} (affichage limité à ${nbAffiches})` : `${total}`;
}

// Message d'incitation à affiner, affiché à côté du titre de section quand
// le lot est tronqué — volontairement générique (pas "ajoute une ville ou
// un département") : n'importe quel mot supplémentaire affine la recherche
// depuis le correctif multi-mots (cf. recherche_tool.py::
// _construire_clause_recherche_etablissements), pas seulement un lieu.
function MessageAffiner() {
  return (
    <p className="mt-1 text-[11.5px] font-bold text-attention-dark">
      Trop de résultats pour tous les afficher. Ajoutez un mot à votre recherche pour affiner.
    </p>
  );
}

// Possède l'état des filtres/tri établissements + tri communes et le fetch
// client vers /recherche : les deux sections (établissements, communes)
// partagent un seul appel, puisque l'API renvoie les deux dans la même
// réponse. Un changement de filtre/tri met à jour l'URL (history.replaceState
// — pas de navigation Next.js, juste un lien copiable) puis relance l'appel.
export function ResultatsRecherche({
  query,
  resultatsInitiaux,
  filtresInitiaux,
}: {
  query: string;
  resultatsInitiaux: RechercheResultats;
  filtresInitiaux: FiltresRecherche;
}) {
  const [filtres, setFiltres] = useState(filtresInitiaux);
  const [resultats, setResultats] = useState(resultatsInitiaux);
  const abortRef = useRef<AbortController | null>(null);

  const relancerRecherche = useCallback(
    (nouveauxFiltres: FiltresRecherche) => {
      setFiltres(nouveauxFiltres);

      const params = construireParams(query, nouveauxFiltres);
      window.history.replaceState(null, "", `?${params.toString()}`);

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      recupererRecherche(query, nouveauxFiltres, { signal: controller.signal })
        .then((donnees) => setResultats(donnees))
        .catch(() => {
          // Requête annulée (nouveau changement avant la fin) ou API
          // indisponible — on garde le dernier résultat affiché plutôt que
          // de casser l'affichage sur une erreur transitoire.
        });
    },
    [query]
  );

  const onFiltresEtablissementsChange = useCallback(
    (f: FiltresEtablissements) => relancerRecherche({ ...filtres, ...f }),
    [filtres, relancerRecherche]
  );

  const onTriCommunesChange = useCallback(
    (triCommunes: TriCommunes, directionCommunes: Direction) =>
      relancerRecherche({ ...filtres, triCommunes, directionCommunes }),
    [filtres, relancerRecherche]
  );

  const collegesAvecHrefBase = useMemo(
    () => resultats.etablissements.map((e) => ({ ...e, hrefBase: hrefBaseVille(e) })),
    [resultats.etablissements]
  );

  // Un filtre établissement actif peut réduire le compte à 0 : la section
  // reste visible dans ce cas (avec le message "Aucun collège ne correspond
  // à ces filtres" déjà géré par FiltresEtListeColleges) pour que
  // l'utilisateur puisse changer ses filtres sans repartir de l'URL.
  const afficherSectionEtablissements =
    resultats.etablissements.length > 0 || filtresEtablissementsActifs(filtres);

  return (
    <>
      {afficherSectionEtablissements && (
        <div className="mt-7">
          <h2 className="font-titre text-[15px] font-semibold text-texte">
            Établissements · {formaterTitreSection(
              resultats.etablissements_total, resultats.etablissements.length, resultats.etablissements_tronques
            )}
          </h2>
          {resultats.etablissements_tronques && <MessageAffiner />}

          <FiltresEtListeColleges
            colleges={collegesAvecHrefBase}
            apercu={10}
            modeServeur={{
              filtresInitiaux: {
                secteur: filtresInitiaux.secteur,
                dispositif: filtresInitiaux.dispositif,
                section: filtresInitiaux.section,
                notationMin: filtresInitiaux.notationMin,
                tri: filtresInitiaux.tri,
                direction: filtresInitiaux.direction,
              },
              onFiltresChange: onFiltresEtablissementsChange,
              nbTotal: resultats.etablissements_total,
              tronque: resultats.etablissements_tronques,
            }}
          />
        </div>
      )}

      {resultats.communes.length > 0 && (
        <div className="mt-7">
          <h2 className="font-titre text-[15px] font-semibold text-texte">
            Communes · {formaterTitreSection(
              resultats.communes_total, resultats.communes.length, resultats.communes_tronquees
            )}
          </h2>
          {resultats.communes_tronquees && <MessageAffiner />}
          <ListeCommunes
            communes={resultats.communes}
            tri={filtres.triCommunes}
            direction={filtres.directionCommunes}
            onTriChange={onTriCommunesChange}
          />
        </div>
      )}
    </>
  );
}
