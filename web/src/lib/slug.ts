// Slug de la fiche établissement : {nom-slugifié}-{uai}, ex.
// "college-jean-moulin-0341065y" — décision actée : accents supprimés,
// minuscules, UAI en suffixe pour l'unicité et la stabilité de l'URL même
// si le nom change (cf. docs/decision_log.md).

export function slugifier(texte: string): string {
  return texte
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // diacritiques (accents décomposés par NFD)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Format UAI officiel : 7 chiffres + 1 lettre (ex. "0341065Y"), toujours en
// position finale du slug.
const RE_UAI_FIN_DE_SLUG = /([0-9]{7}[a-zA-Z])$/;

export function extraireUaiDuSlug(collegeSlug: string): string | null {
  const match = RE_UAI_FIN_DE_SLUG.exec(collegeSlug);
  return match ? match[1].toUpperCase() : null;
}

export function construireSlugCollege(nom: string, uai: string): string {
  return `${slugifier(nom)}-${uai.toLowerCase()}`;
}

// Résolution réelle en place côté API (cf. agent/tools/hierarchie_tool.py,
// decision_log.md S15.4) — ces deux fonctions construisent les liens vers
// les pages hub à partir des libellés déjà résolus par l'API, jamais depuis
// un slug reconstitué à l'aveugle.
export function construireSlugRegion(libelleRegion: string): string {
  return slugifier(libelleRegion);
}

export function construireSlugDepartement(codeDepartement: string, libelleDepartement: string): string {
  return `${codeDepartement.toLowerCase()}-${slugifier(libelleDepartement)}`;
}

// Reconstruction best-effort d'un libellé lisible depuis un slug de la
// hiérarchie géographique (région/département/ville), en l'absence d'un
// vrai service de libellés (ces pages sont encore des placeholders) —
// imparfait sur les noms accentués/composés (ex. "cote-d-or" → "Cote D
// Or" et non "Côte-d'Or"), limitation temporaire assumée.
export function deslugifier(slug: string): string {
  return slug
    .split("-")
    .map((mot) => mot.charAt(0).toUpperCase() + mot.slice(1))
    .join(" ");
}
