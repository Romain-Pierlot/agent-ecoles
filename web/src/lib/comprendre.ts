// Modèle de contenu de la section « Comprendre » (guides, notes de méthode,
// glossaire). Contenu éditorial propre au site, pas un miroir de l'API
// Python (contrairement à src/lib/types.ts) : ces objets sont rédigés à la
// main, pas issus d'une base de données.
//
// Décisions actées avant l'écriture de ce fichier (à ne pas redéfaire sans
// repasser par une nouvelle décision) :
// - Pas de mécanique de « vérification » : un guide affiche « Publié le »,
//   et sert de tri au sein de sa catégorie — pas de champ verifieLe.
// - Les sources d'un guide sont une liste simple façon bibliographie,
//   rédigée à la main, sans registre partagé automatisé avec les chunks du
//   RAG (rag/chunks_manuels.json). Un guide n'est jamais lui-même une
//   source citable par l'agent : l'agent cite toujours le document
//   officiel sous-jacent.

export type CategorieSlug =
  | "indicateurs-resultats"
  | "sectorisation-inscription"
  | "dispositifs-accompagnement"
  | "college-fil-du-cycle";

export type Categorie = {
  slug: CategorieSlug;
  label: string;
  role: string; // phrase de rôle affichée en en-tête de carte catégorie
  sousThemes?: string[]; // repères internes (intertitres, ancres, filtres) — pas d'URL propre
};

// Ordre fixe, jamais recalculé : c'est cet ordre qui pilote l'affichage sur
// l'index et le rail, indépendamment du nombre de guides par catégorie.
export const CATEGORIES: Categorie[] = [
  {
    slug: "indicateurs-resultats",
    label: "Indicateurs & résultats",
    role: "Ce que chaque chiffre de la fiche mesure, et ce qu'il ne mesure pas.",
    sousThemes: ["IPS & mixité", "Valeur ajoutée", "Brevet", "Effectifs & parcours"],
  },
  {
    slug: "sectorisation-inscription",
    label: "Sectorisation & inscription",
    role: "Qui décide de votre collège de secteur, et par quelles étapes passe une inscription.",
    sousThemes: ["Secteur", "Démarches", "Calendrier"],
  },
  {
    slug: "dispositifs-accompagnement",
    label: "Dispositifs & accompagnement",
    role: "Les dispositifs signalés sur une fiche, et ce qu'ils impliquent au quotidien.",
  },
  {
    slug: "college-fil-du-cycle",
    label: "Le collège au fil du cycle",
    role: "Ce qui attend un élève de la 6e à la 3e, puis au moment de l'orientation.",
  },
];

export function trouverCategorie(slug: CategorieSlug): Categorie {
  const categorie = CATEGORIES.find((c) => c.slug === slug);
  if (!categorie) throw new Error(`Catégorie inconnue : ${slug}`);
  return categorie;
}

export type Source = {
  producteur: string;
  titre: string;
  millesime?: string; // année de référence de l'édition citée, distincte de dateReleve
  url: string;
  dateReleve: string; // ISO — date à laquelle le site a relevé cette source
};

export type SectionGuide = {
  titre: string; // rendu en <h2>, une entrée du sommaire "Sur cette page"
  paragraphes: string[];
  encadre?: { titre: string; texte: string }; // encart secondaire optionnel (ex. "Score par profession")
};

// Figure d'échelle positionnelle (ex. repères IPS) — au plus une par guide,
// cf. gabarit de lecture. Type dédié plutôt que du HTML libre : la même
// figure doit pouvoir se rendre identiquement sur plusieurs guides
// d'indicateurs (IPS, valeur ajoutée...).
export type FigureEchelle = {
  min: number;
  max: number;
  graduations: number[];
  moitieCentrale: [number, number]; // bornes de la plage mise en évidence
  reperes: { label: string; valeur: number; accent?: boolean }[];
};

export type Guide = {
  slug: string;
  titre: string;
  resume: string; // 1-2 lignes, affiché dans toute ligne de guide
  categorie: CategorieSlug;
  sousTheme?: string;
  publieLe: string; // ISO — affiché "Publié le ..." sur la page du guide, sert aussi à trier au sein de la catégorie
  resumeCourt: string[]; // 3 puces de l'encadré "En résumé"
  corps: SectionGuide[];
  figure?: FigureEchelle;
  sources: Source[];
  apparaitSur?: { label: string; description: string; href?: string }[]; // "Où il apparaît sur le site"
};

export type NoteMethode = {
  slug: string;
  titre: string;
  version: number;
  enVigueurDepuis: string; // ISO
  revisions: { version: number; date: string; changement: string }[];
  corps: SectionGuide[];
};

export type QuestionGlossaire = {
  question: string;
  reponse: string; // 2-4 lignes, autonome
  categorie: CategorieSlug;
  source?: Source;
  guideSlug?: string; // "Approfondir" affiché seulement si le guide correspondant existe
};

export function guidesTriesParCategorie(guides: Guide[], categorie: CategorieSlug): Guide[] {
  return guides
    .filter((g) => g.categorie === categorie)
    .sort((a, b) => (a.publieLe < b.publieLe ? 1 : -1)); // plus récent d'abord
}
