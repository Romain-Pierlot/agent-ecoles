import { API_URL } from "@/lib/api";
import type { CalendrierScolaire } from "@/lib/types";

// Appel côté serveur (composant serveur Next.js, SSR), même pattern que
// lib/etablissement.ts. Pas de 404 possible ici : contrairement à une fiche
// établissement, cette route ne dépend d'aucun paramètre d'URL.
export async function recupererCalendrierScolaire(): Promise<CalendrierScolaire> {
  const reponse = await fetch(`${API_URL}/calendrier-scolaire`, { cache: "no-store" });
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as CalendrierScolaire;
}
