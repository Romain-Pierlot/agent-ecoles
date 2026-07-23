import { API_URL } from "@/lib/api";
import type { SecteurResultats, SuggestionAdresse } from "@/lib/types";

// Même pattern que lib/recherche.ts : appelée côté serveur (SSR) et côté
// client, fetch direct vers FastAPI, pas de route Next.js intermédiaire.
export async function recupererSecteur(
  adresse: string,
  options?: { signal?: AbortSignal }
): Promise<SecteurResultats> {
  const params = new URLSearchParams({ adresse });
  const reponse = await fetch(`${API_URL}/secteur?${params.toString()}`, {
    cache: "no-store",
    signal: options?.signal,
  });
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as SecteurResultats;
}

// Autocomplétion du champ adresse (ChampAdresse.tsx) — plusieurs candidats,
// contrairement à recupererSecteur qui résout une adresse déjà choisie.
export async function recupererSuggestionsAdresse(
  q: string,
  options?: { signal?: AbortSignal }
): Promise<SuggestionAdresse[]> {
  const params = new URLSearchParams({ q });
  const reponse = await fetch(`${API_URL}/secteur/adresses?${params.toString()}`, {
    cache: "no-store",
    signal: options?.signal,
  });
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  const donnees = (await reponse.json()) as { suggestions: SuggestionAdresse[] };
  return donnees.suggestions;
}
