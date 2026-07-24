import { API_URL } from "@/lib/api";
import type { RechercheResultats } from "@/lib/types";
import { FILTRES_PAR_DEFAUT, construireParams, type FiltresRecherche } from "@/lib/rechercheParams";

// Appelée à la fois côté serveur (page.tsx, SSR — même pattern que
// lib/geographie.ts) et côté client (ResultatsRecherche, à chaque
// changement de filtre/tri) : navigateur et Node.js appellent tous les
// deux l'API FastAPI directement, pas de route Next.js intermédiaire.
export async function recupererRecherche(
  query: string,
  filtres: FiltresRecherche = FILTRES_PAR_DEFAUT,
  options?: { signal?: AbortSignal }
): Promise<RechercheResultats> {
  const params = construireParams(query, filtres);
  const reponse = await fetch(`${API_URL}/recherche?${params.toString()}`, {
    cache: "no-store",
    signal: options?.signal,
  });
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as RechercheResultats;
}

// Best-effort, ne doit jamais faire échouer le rendu de la page — appelée
// une seule fois par recherche réelle (recherche/page.tsx, via after()),
// jamais à chaque changement de filtre/tri côté client.
export function journaliserRecherche(terme: string, nbEtablissements: number, nbCommunes: number): void {
  fetch(`${API_URL}/recherche/log`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ terme, nb_etablissements: nbEtablissements, nb_communes: nbCommunes }),
  }).catch(() => {
    // Panne de journalisation (API indisponible, etc.) — jamais remontée.
  });
}
