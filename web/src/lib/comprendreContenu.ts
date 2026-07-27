// Contenu éditorial de la section « Comprendre ». Premier guide repris du
// bundle de référence (design_handoff_comprendre, écran 23a) : texte déjà
// rédigé côté bundle, à relire avant toute mise en ligne réelle (cf.
// README du bundle, section « Fidélité »).
//
// URLs de sources reprises du bundle sous forme de domaine seulement
// (ex. "data.education.gouv.fr") : à remplacer par le lien précis vers le
// jeu de données ou la note avant publication réelle, une fois vérifié.

import type { Guide, QuestionGlossaire } from "@/lib/comprendre";

export const GUIDES: Guide[] = [
  {
    slug: "ips-indice-position-sociale",
    titre: "IPS : ce que mesure l'indice de position sociale",
    resume:
      "Un indice de composition sociale des familles, publié par établissement. Comment il est calculé, à quoi il se compare, et pourquoi il ne dit rien du niveau scolaire.",
    categorie: "indicateurs-resultats",
    sousTheme: "IPS & mixité",
    publieLe: "2026-06-18",
    resumeCourt: [
      "L'indice résume les professions et le niveau de diplôme des responsables des élèves d'un établissement, sur une échelle centrée autour de 100.",
      "Il décrit la population accueillie, et non les pratiques pédagogiques de l'établissement.",
      "Il entre dans le calcul de la valeur ajoutée : c'est lui qui définit le résultat attendu au brevet.",
    ],
    corps: [
      {
        titre: "Ce que l'indice agrège",
        paragraphes: [
          "L'indice de position sociale est construit par la DEPP à partir des données administratives d'inscription. Pour chaque élève, la profession déclarée des deux responsables légaux est convertie en un score, à l'aide d'une table établie sur des enquêtes couvrant les conditions matérielles du foyer, le niveau de diplôme des parents et leur implication dans la scolarité.",
          "L'indice publié pour un établissement est la moyenne des scores de ses élèves. Deux collèges d'un même quartier peuvent afficher des indices distants de vingt points si leurs recrutements diffèrent, par exemple entre un secteur unique et un établissement à sections spécifiques.",
        ],
        encadre: {
          titre: "Score par profession",
          texte: "La table de conversion associe un score à chacune des 32 catégories socioprofessionnelles de la nomenclature de l'Insee. Elle est réévaluée à chaque refonte de l'enquête, ce qui rend les comparaisons entre millésimes éloignés imprécises.",
        },
      },
      {
        titre: "L'échelle et ses repères",
        paragraphes: [
          "L'indice n'a pas de minimum ni de maximum théorique. En pratique, les collèges publics se répartissent entre 60 et 150 environ, la moyenne nationale des collèges publics s'établissant à 103 à la rentrée 2023.",
        ],
      },
      {
        titre: "Portée et limites",
        paragraphes: [
          "L'indice porte sur la composition sociale des familles. Les résultats scolaires, l'encadrement, le climat de l'établissement et la stabilité des équipes relèvent d'autres indicateurs, publiés séparément.",
          "Deux précautions de lecture sont rappelées par la DEPP : l'indice repose sur des professions déclarées, dont une part reste inconnue ou mal renseignée ; et sa moyenne d'établissement masque la dispersion interne, forte dans les collèges à recrutement contrasté.",
          "Le rapport de la Cour des comptes de 2023 sur la mixité sociale au collège recommande de lire l'indice conjointement à l'écart avec les établissements voisins, plutôt qu'en valeur absolue.",
        ],
      },
    ],
    figure: {
      min: 60,
      max: 160,
      graduations: [60, 85, 110, 135, 160],
      moitieCentrale: [74, 132],
      reperes: [
        { label: "Collège Parc Impérial", valeur: 120, accent: true },
        { label: "Moyenne nationale, collèges publics", valeur: 103 },
      ],
    },
    apparaitSur: [
      {
        label: "Sur une fiche de collège",
        description: "Bloc « Profil social » : indice de l'établissement, valeur départementale, écart.",
      },
      {
        label: "Dans le calcul de la note de repère",
        description: "L'indice n'entre pas directement dans la note ; il sert à établir le résultat attendu au brevet.",
        href: "/comprendre/methodologie/note-de-repere",
      },
    ],
    sources: [
      {
        producteur: "DEPP",
        titre: "Indices de position sociale des collèges",
        millesime: "rentrée 2023",
        url: "https://data.education.gouv.fr",
        dateReleve: "2026-06-12",
      },
      {
        producteur: "DEPP",
        titre: "Note d'information — méthode de construction de l'indice",
        millesime: "juin 2024",
        url: "https://www.education.gouv.fr",
        dateReleve: "2026-06-12",
      },
      {
        producteur: "Cour des comptes",
        titre: "Rapport sur la mixité sociale au collège",
        millesime: "2023",
        url: "https://www.ccomptes.fr",
        dateReleve: "2026-06-12",
      },
    ],
  },
];

// Glossaire : squelette au lancement, une seule réponse rédigée dans le
// bundle de référence (écran 26a) — les autres questions listées dans le
// bundle n'ont pas de réponse écrite, donc pas reprises ici (cf. règle
// contre l'invention de contenu non vérifié).
export const QUESTIONS_GLOSSAIRE: QuestionGlossaire[] = [
  {
    question: "Un IPS élevé signifie-t-il un bon collège ?",
    reponse:
      "L'indice de position sociale décrit la composition sociale des familles d'un établissement. Un indice élevé indique une population de familles favorisées, et n'informe pas sur la qualité de l'enseignement. Pour situer les résultats d'un collège compte tenu de son public, la valeur ajoutée est l'indicateur prévu à cet effet.",
    categorie: "indicateurs-resultats",
    source: {
      producteur: "DEPP",
      titre: "Note d'information — méthode de construction de l'indice",
      millesime: "juin 2024",
      url: "https://www.education.gouv.fr",
      dateReleve: "2026-06-12",
    },
    guideSlug: "ips-indice-position-sociale",
  },
];
