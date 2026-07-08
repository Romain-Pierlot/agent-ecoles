import { API_URL } from "@/lib/api";
import type { FicheEtablissement } from "@/lib/types";

// Appel côté serveur (composant serveur Next.js, SSR) — ne passe jamais par
// le navigateur, donc aucune question de CORS ici (contrairement au /chat
// appelé côté client dans lib/api.ts).
export async function recupererEtablissement(uai: string): Promise<FicheEtablissement | null> {
  const reponse = await fetch(`${API_URL}/etablissement/${uai}`, { cache: "no-store" });
  if (reponse.status === 404) return null;
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as FicheEtablissement;
}
