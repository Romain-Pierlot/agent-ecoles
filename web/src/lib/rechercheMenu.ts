import { hrefEtablissement, hrefCommune } from "@/lib/hrefsGeo";
import type { EtablissementRecherche, CommuneRecherche } from "@/lib/types";
import type { PageSuggestion } from "@/lib/pagesRecherche";

// Construction des lignes du menu de suggestions + résolution de leur
// destination — partagé entre RechercheChamp (desktop) et RechercheMobile
// (overlay plein écran), pour que les deux gardent exactement le même
// ordre et le même comportement de navigation sans dupliquer cette partie
// sensible (celle qui décide où chaque ligne mène).

export type LigneMenu =
  | { type: "etablissement"; data: EtablissementRecherche }
  | { type: "commune"; data: CommuneRecherche }
  | { type: "voir-tout" }
  | { type: "page"; data: PageSuggestion }
  | { type: "lien-fixe"; href: string; label: string }
  | { type: "camille" };

// Ordre non négociable (tour 14 + décisions actées) : établissements →
// communes → « voir tous les résultats » → (repli) pages dédiées →
// Camille toujours en dernier. Pages n'apparaît que si établissements ET
// communes sont vides — pas de mélange avec de vrais résultats.
export function construireLignes({
  etablissements,
  communes,
  pages,
  aucunResultat,
}: {
  etablissements: EtablissementRecherche[];
  communes: CommuneRecherche[];
  pages: PageSuggestion[];
  aucunResultat: boolean;
}): LigneMenu[] {
  if (etablissements.length > 0 || communes.length > 0) {
    return [
      ...etablissements.map((data): LigneMenu => ({ type: "etablissement", data })),
      ...communes.map((data): LigneMenu => ({ type: "commune", data })),
      { type: "voir-tout" },
      { type: "camille" },
    ];
  }
  if (pages.length > 0) {
    return [...pages.map((data): LigneMenu => ({ type: "page", data })), { type: "camille" }];
  }
  if (aucunResultat) {
    return [
      { type: "lien-fixe", href: "/carte-scolaire", label: "Mon collège de secteur" },
      { type: "lien-fixe", href: "/comprendre", label: "Comprendre" },
      { type: "camille" },
    ];
  }
  return [];
}

export function hrefLigne(ligne: LigneMenu, requete: string, hrefAssistant: string): string {
  switch (ligne.type) {
    case "etablissement":
      return hrefEtablissement(ligne.data);
    case "commune":
      return hrefCommune(ligne.data);
    case "voir-tout":
      return `/recherche?q=${encodeURIComponent(requete)}`;
    case "page":
      return ligne.data.url;
    case "lien-fixe":
      return ligne.href;
    case "camille":
      return `${hrefAssistant}?situation=${encodeURIComponent(requete)}`;
  }
}
