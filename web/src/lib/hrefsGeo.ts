// Construction de liens vers la hiérarchie géographique (ville, fiche
// établissement) à partir d'un résultat de recherche libre (GET /recherche)
// — chaque résultat porte sa propre lignée région/département/commune,
// contrairement aux pages hub où le contexte géo est déjà fixé. Partagé
// entre la page /recherche (composant serveur) et RechercheBloc
// (composant client, autocomplétion) : même logique de construction d'URL
// des deux côtés, un seul endroit à faire évoluer si le schéma de slug change.

import {
  construireSlugRegion,
  construireSlugDepartement,
  construireSlugCollege,
  slugifier,
} from "@/lib/slug";
import type { EtablissementRecherche, CommuneRecherche } from "@/lib/types";

export function hrefBaseVille(entite: {
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

export function hrefEtablissement(e: EtablissementRecherche): string {
  return `${hrefBaseVille(e)}/college/${construireSlugCollege(e.nom, e.uai)}`;
}

export function hrefCommune(c: CommuneRecherche): string {
  return hrefBaseVille(c);
}
