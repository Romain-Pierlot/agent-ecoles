import { API_URL } from "@/lib/api";
import type { RechercheResultats } from "@/lib/types";

// Appel côté serveur (composant serveur Next.js, SSR) — même pattern que
// lib/geographie.ts.

export async function recupererRecherche(query: string): Promise<RechercheResultats> {
  const reponse = await fetch(`${API_URL}/recherche?q=${encodeURIComponent(query)}`, {
    cache: "no-store",
  });
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as RechercheResultats;
}
