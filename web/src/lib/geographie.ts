import { API_URL } from "@/lib/api";
import type { NationalHub, RegionHub, DepartementHub } from "@/lib/types";

// Appels côté serveur (composants serveur Next.js, SSR) — même pattern que
// lib/etablissement.ts. 404 traduit en null (slug inconnu, pas une erreur).

export async function recupererNational(): Promise<NationalHub> {
  const reponse = await fetch(`${API_URL}/region`, { cache: "no-store" });
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as NationalHub;
}

export async function recupererRegion(regionSlug: string): Promise<RegionHub | null> {
  const reponse = await fetch(`${API_URL}/region/${regionSlug}`, { cache: "no-store" });
  if (reponse.status === 404) return null;
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as RegionHub;
}

export async function recupererDepartement(
  regionSlug: string,
  deptSlug: string
): Promise<DepartementHub | null> {
  const reponse = await fetch(`${API_URL}/region/${regionSlug}/departement/${deptSlug}`, {
    cache: "no-store",
  });
  if (reponse.status === 404) return null;
  if (!reponse.ok) {
    throw new Error(`L'API a répondu avec le statut ${reponse.status}`);
  }
  return (await reponse.json()) as DepartementHub;
}
