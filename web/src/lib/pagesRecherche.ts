// Mapping mots-clés → page dédiée, utilisé en repli par le champ de
// recherche (RechercheChamp/RechercheMobile) quand une requête ne
// correspond à aucun établissement ni aucune commune — ex. "calendrier",
// "dérogation". Liste volontairement courte et curatée à la main (pas
// d'indexation automatique du site), cf. docs/roadmap_technique.md pour
// la piste de génération assistée par IA une fois du contenu réel
// disponible.
//
// PAGES est vide pour l'instant : les seules pages candidates
// (calendrier, comprendre, méthodologie...) sont encore des squelettes
// (PagePlaceholder), et /carte-scolaire a déjà son propre lien permanent
// dans la nav. Ajouter une entrée ici suffit à activer la catégorie
// "Pages" dans le menu de suggestions, sans rien recoder ailleurs.

export type PageSuggestion = {
  titre: string;
  url: string;
};

type EntreePage = PageSuggestion & { motsCles: string[] };

const PAGES: EntreePage[] = [];

/** Comparaison insensible à la casse ET aux accents, même logique que
 * RechercheChamp/RechercheBloc (ex. « Vitré » ↔ « vitre »). Exportée :
 * réutilisée par lib/rechercheAffichage.tsx pour le surlignage inversé. */
export function normaliser(s: string): string {
  return s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}

export function chercherPages(query: string): PageSuggestion[] {
  const q = normaliser(query.trim());
  if (!q) return [];
  return PAGES.filter((page) =>
    page.motsCles.some((motCle) => normaliser(motCle).includes(q) || q.includes(normaliser(motCle))),
  ).map(({ titre, url }) => ({ titre, url }));
}
