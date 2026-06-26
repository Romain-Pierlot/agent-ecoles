"""
ingest_rag.py — Pipeline d'ingestion des documents DEPP dans ChromaDB
Version 7 — correction filtrage artefacts + chunk manuel page 4 IVAC

Corrections v7 :
- Correction du filtrage CHUNKS_ARTEFACTS (index calculé avant filtrage)
- Suppression doublon ivac_2025_004 dans CHUNKS_ARTEFACTS
- Ajout chunk manuel ivac_2025_manual_page4 (page 4 deux colonnes)
- Page 4 guide IVAC ajoutée aux pages exclues
"""

import os
import re
import sys
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHROMA_PATH, CHROMA_COLLECTION, EMBEDDING_MODEL

SOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources")

CHUNK_MAX_CHARACTERS = 1500
CHUNK_NEW_AFTER_N_CHARS = 1000
CHUNK_COMBINE_UNDER_N_CHARS = 500

CHUNKS_ARTEFACTS = {
    "ivac_2025_003",  # page 4 deux colonnes — tronqué, remplacé par chunk manuel
    "ivac_2025_004",  # page 4 deux colonnes — contenu mélangé, remplacé par chunk manuel
    "ivac_2025_005",  # note isolée "1 Les conditions de publication sont précisées page 9."
    "ips_2016_000",   # page de titre — sans contenu utile
    "ips_2016_004",   # note de bas de page isolée
    "ips_2016_015",   # note de bas de page numérotée isolée
    "ips_2016_018",   # note de bas de page numérotée isolée
    "ips_2016_020",   # note de bas de page numérotée isolée
    "ips_2016_035",   # "Kernel" — légende de graphique
    "ips_2023_000",   # "↘ Introduction" — trop court, sans contenu
}

KEYWORDS_EXCLUSION = [
    "SOMMAIRE",
    "BIBLIOGRAPHIE",
    "ANNEXES",
    "Table des matières",
    "Pour aller plus loin",
    "Retrouvez les travaux",
    "Calcul pratique",
    "FIGURE 2",
]

# ================================================================
# MÉTADONNÉES DE BASE PAR DOCUMENT
# ================================================================
META_NI = {
    "dc_title":      "Note d'information — L'IPS, un outil pour décrire les inégalités sociales entre établissements",
    "dc_creator":    "Fannie Dauphant, Franck Evain, Marine Guillerm, Catherine Simon, Thierry Rocher — DEPP B3",
    "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
    "dc_date":       "2023",
    "dc_type":       "note_information",
    "dc_source":     "https://www.education.gouv.fr/ni-23-16-l-indice-de-position-sociale-ips-364089",
    "chunk_domaine": "ips",
    "dc_niveau":     "avancé",
}

META_IVAC = {
    "dc_title":      "Guide méthodologique IVAC 2025",
    "dc_creator":    "Franck Evain, Violette Marmion — DEPP B3",
    "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
    "dc_date":       "2025",
    "dc_type":       "methodologie",
    "dc_source":     "https://www.education.gouv.fr/depp/les-indicateurs-de-resultats-des-colleges-et-des-lycees-377729",
    "chunk_domaine": "ivac",
    "dc_niveau":     "avancé",
}

META_IVAC_VULGAIRE = {
    "dc_title":      "Indicateurs de valeur ajoutée des collèges (IVAC) — Description officielle",
    "dc_creator":    "DEPP — Ministère de l'Éducation Nationale",
    "dc_publisher":  "Ministère de l'Éducation Nationale",
    "dc_date":       "2022",
    "dc_type":       "description_dataset",
    "dc_source":     "https://data.education.gouv.fr/explore/assets/fr-en-indicateurs-valeur-ajoutee-colleges/",
    "chunk_domaine": "ivac",
    "dc_niveau":     "vulgarisation",
}

META_IPS_VULGAIRE = {
    "dc_title":      "L'indice de position sociale (IPS) — Page officielle DEPP",
    "dc_creator":    "DEPP — Ministère de l'Éducation Nationale",
    "dc_publisher":  "Ministère de l'Éducation Nationale",
    "dc_date":       "2023",
    "dc_type":       "page_officielle",
    "dc_source":     "https://www.education.gouv.fr/depp/l-indice-de-position-sociale-ips-357755",
    "chunk_domaine": "ips",
    "dc_niveau":     "vulgarisation",
}


def chunk_meta(base: dict, page: str, titre: str) -> dict:
    return {**base, "chunk_page": page, "chunk_titre_section": titre}


# ================================================================
# CHUNKS MANUELS
# ================================================================
CHUNKS_MANUELS = [

    # ── Note d'information IPS 23.16 — Page 1 ───────────────────
    {
        "id": "ips_2023_ni_manual_000",
        "contenu": """L'indice de position sociale (IPS) : un outil statistique pour décrire les inégalités sociales entre établissements. Focus sur les collèges.

L'indice de position sociale (IPS) d'un collège est un indicateur qui résume les conditions socio-économiques et culturelles des familles des élèves qu'il accueille. Il permet de rendre compte des disparités sociales existantes entre collèges, ainsi qu'à l'intérieur d'entre eux. De fortes différences sont constatées selon les territoires et selon le secteur de scolarisation. Par ailleurs, les performances au diplôme national du brevet (DNB) et les IPS sont très corrélés. Cependant, lorsque l'on contrôle le niveau scolaire initial à l'entrée au collège ainsi que l'IPS, certains collèges parviennent à mieux réussir que d'autres au DNB. Les indicateurs de valeur ajoutée des collèges (IVAC) permettent ainsi de quantifier pour chaque collège l'écart entre la réussite observée au DNB et la réussite attendue en regard du profil scolaire et social des élèves accueillis.""",
        "metadata": chunk_meta(META_NI, "1", "L'indice de position sociale (IPS) : un outil statistique pour décrire les inégalités sociales entre établissements"),
    },
    {
        "id": "ips_2023_ni_manual_001",
        "contenu": """Quel est le niveau social moyen d'un collège ? Quel est le degré d'hétérogénéité sociale des élèves qu'il accueille ? Comment comparer ce collège à un autre, du point de vue de leur situation sociale ? L'indice de position sociale (IPS) est un outil construit pour répondre à ce type de questions. L'idée est simple : il s'agit tout d'abord de déterminer des valeurs de référence pour chaque PCS (profession et catégorie sociale) des parents, ou pour chaque couple de PCS (père et mère). Puis, il suffit d'appliquer ces valeurs de référence aux PCS disponibles dans l'établissement scolaire et de calculer leur moyenne pour obtenir l'IPS moyen de l'établissement. On aboutit ainsi à un indicateur statistique continu qui permet aussi de prendre en compte le profil des deux parents des élèves.""",
        "metadata": chunk_meta(META_NI, "1", "Comment l'IPS moyen d'un établissement est-il calculé ?"),
    },
    {
        "id": "ips_2023_ni_manual_002",
        "contenu": """Les valeurs de l'IPS représentent les conditions socio-économiques et culturelles moyennes des professions. Concrètement, les valeurs de référence de l'indice pour chaque PCS, ou couple de PCS, sont déterminées grâce à l'analyse de données d'enquêtes statistiques : les panels d'élèves de la DEPP. Ces panels sont des dispositifs de suivis de cohortes composés de plusieurs milliers d'élèves représentatifs des élèves scolarisés en France. Ils permettent notamment, via des enquêtes auprès des familles des élèves, de recueillir des informations très précises sur les conditions socio-économiques et culturelles des familles des élèves, telles que les niveaux de diplômes, les conditions matérielles, les pratiques culturelles, etc. Ces caractéristiques sont synthétisées par PCS au moyen d'une analyse factorielle. L'IPS d'une PCS donnée est ainsi le résumé quantitatif d'un certain nombre d'attributs socio-économiques et culturels favorables à la réussite scolaire, que l'on retrouve en moyenne pour cette PCS. L'IPS permet ainsi d'attribuer un score aux PCS en fonction de multiples dimensions favorables à l'apprentissage.""",
        "metadata": chunk_meta(META_NI, "1", "Les valeurs de l'IPS représentent les conditions socio-économiques et culturelles moyennes des professions"),
    },

    # ── Note d'information IPS 23.16 — Page 2 ───────────────────
    {
        "id": "ips_2023_ni_manual_003",
        "contenu": """Les valeurs de l'IPS varient de 45 à 185 : plus l'IPS est élevé, plus les conditions familiales sont favorables à l'apprentissage. Par exemple, un élève dont la mère est professeure des écoles et le père ingénieur a un IPS de 175, tandis qu'un autre élève dont la mère est employée de commerce et le père est ouvrier qualifié de l'industrie a un IPS de 75. Il convient de noter que l'IPS est le résultat de la compilation de plusieurs dimensions, mais il n'est pas en lui-même une mesure de ces dimensions. Ainsi, dans les deux exemples donnés, le fait que le premier élève ait un IPS plus élevé que le second ne signifie pas nécessairement que sa famille est concrètement plus avantagée. Cela signifie plutôt qu'en moyenne, les familles qui ressemblent à la sienne ont des conditions plus favorables à l'apprentissage. Au final, lorsque les PCS des parents sont disponibles, il suffit d'appliquer ces valeurs de référence et de considérer cette nouvelle variable comme un indice, c'est-à-dire de manière quantitative. Il est alors aisé d'apprécier le niveau social d'un établissement scolaire, à travers le calcul de l'indice moyen, ou encore les disparités sociales au sein de l'établissement, au moyen de l'écart-type de l'indice. En outre, l'IPS permet de s'appuyer sur les PCS des deux parents, et non pas seulement sur celle du responsable légal, comme cela pouvait être le cas précédemment. Or, nombre d'études et de recherches montrent qu'il est important de tenir compte des profils des deux parents.""",
        "metadata": chunk_meta(META_NI, "2", "Les valeurs de l'IPS varient de 45 à 185"),
    },
    {
        "id": "ips_2023_ni_manual_004",
        "contenu": """L'IPS un indicateur statistique remis à jour à la rentrée 2022

La première version de l'IPS a été publiée en 2016. Depuis, l'IPS a été mobilisé pour des applications diverses : un indicateur du milieu social utilisé dans des études statistiques (par exemple pour l'analyse des résultats des évaluations Cedre) ; une variable, caractéristique du profil social des élèves accueillis dans les établissements, et à ce titre intégrée dans des modélisations statistiques, telles que les indicateurs de valeurs ajoutées des lycées ; un outil d'aide à la gestion des moyens alloués aux académies et aux établissements scolaires ; un critère utilisé dans le processus d'affectation au lycée, dans certaines académies ; un indice pour mettre en évidence la ségrégation et les écarts entre territoires ; un outil de mesure du niveau social utilisé par les chercheurs. Depuis leur mise en ligne en open data, les journalistes les ont aussi utilisés pour décrire les disparités sociales entre établissements.

Une actualisation des valeurs de référence de l'IPS a été effectuée à la rentrée 2022. En effet, la première version publiée en 2016 s'appuyait sur les données du panel d'élèves entrés en sixième en 2007, et plus précisément sur celles du questionnaire aux familles, passé en 2008. Or, la DEPP dispose de données plus récentes avec un questionnaire aux familles administré en 2020, dans le cadre du panel d'élèves entrés en CP en 2011, lorsque ces élèves étaient majoritairement en troisième. Cette actualisation sur des données plus récentes intègre des améliorations techniques, dont la meilleure prise en compte des PCS non renseignées, ainsi qu'une estimation de la variabilité de l'IPS : il convient ainsi de ne pas surinterpréter des écarts de 3 points d'IPS moyen de collèges.""",
        "metadata": chunk_meta(META_NI, "2", "L'IPS un indicateur statistique remis à jour à la rentrée 2022"),
    },
    {
        "id": "ips_2023_ni_manual_005",
        "contenu": """De fortes disparités géographiques

À la rentrée 2022, l'IPS moyen des collégiens en France est de 105 (Note : Il s'agit de l'IPS moyen des collégiens et non l'IPS moyen des collèges.). Il existe cependant une forte disparité territoriale. En effet, alors que les huit départements les plus défavorisés socialement ont un IPS moyen inférieur à 95, douze départements ont, quant à eux, un IPS moyen supérieur à 110. Les départements les plus défavorisés sont majoritairement situés en outremer et dans le nord-est de la France métropolitaine. Ainsi Mayotte, la Guyane et La Réunion ont un IPS moyen inférieur à 88 ; la Seine-Saint-Denis, l'Aisne, les Ardennes, la Haute-Marne et le Pas-de-Calais ont un IPS moyen compris entre 92 et 95. À l'opposé, les départements les plus favorisés sont situés à Paris (126), au sud-ouest de l'Île-de-France (Hauts-de-Seine : 124 et Yvelines : 122), dans les Alpes (Isère, Savoie et Haute-Savoie) et dans les départements des grandes métropoles (Toulouse, Nantes, Rennes, Bordeaux, Lyon). Ces disparités géographiques de l'IPS des collégiens reflètent les différences de contexte économique et sociale des départements. La corrélation entre l'IPS des élèves de troisième et le revenu médian de la commune est de 0,87.""",
        "metadata": chunk_meta(META_NI, "2", "De fortes disparités géographiques"),
    },
    {
        "id": "ips_2023_ni_manual_006",
        "contenu": """L'IPS moyen des collégiens du secteur privé est nettement plus élevé que celui du secteur public

Au-delà des disparités géographiques, on observe des écarts importants d'IPS des collégiens selon le secteur d'enseignement. L'IPS moyen des collégiens du secteur privé sous contrat (121) est nettement supérieur à celui des collégiens du secteur public (101). Au sein du secteur public, il existe également une forte disparité des IPS moyens selon l'appartenance à un réseau d'éducation prioritaire (REP) ou à un réseau d'éducation prioritaire renforcé (REP+). En effet, l'IPS moyen des élèves scolarisés dans des collèges en éducation prioritaire (EP) est de 74 en REP+ et de 85 en REP, tandis que celui des élèves du secteur public hors EP est de 106.""",
        "metadata": chunk_meta(META_NI, "2", "L'IPS moyen des collégiens du secteur privé est nettement plus élevé que celui du secteur public"),
    },
    {
        "id": "ips_2023_ni_manual_007",
        "contenu": """La distribution des IPS des collèges varie selon le secteur, mais aussi à l'intérieur de chaque secteur

L'étendue des IPS des collèges est très différente selon les secteurs d'appartenance. En particulier, 90 % des collèges en REP+ ont un IPS inférieur à 83 alors que 90 % des collèges du secteur public hors EP ont un IPS supérieur à 91 et 90 % des collèges du secteur privé ont un IPS supérieur à 101. Ces données sont cohérentes avec la politique de l'éducation prioritaire, qui repose sur une allocation différenciée des moyens, en donnant davantage aux établissements défavorisés socialement. Si la quasi-totalité des collèges en REP+ et les trois quarts des collèges en REP ont un IPS inférieur à 90, cela ne concerne que 8 % des collèges publics hors EP et moins de 1 % des collèges privés sous contrat. À l'opposé, 65 % des collèges privés et 28 % des collèges publics hors EP ont un IPS supérieur à 110, contre moins de 0,5 % des collèges en EP.""",
        "metadata": chunk_meta(META_NI, "2", "La distribution des IPS des collèges varie selon le secteur, mais aussi à l'intérieur de chaque secteur"),
    },

    # ── Note d'information IPS 23.16 — Page 3 ───────────────────
    {
        "id": "ips_2023_ni_manual_008",
        "contenu": """Une diversité sociale plus faible en REP+ et dans le secteur privé

Au sein d'un collège, les élèves peuvent être de milieux sociaux plus ou moins diversifiés. La moyenne de l'IPS du collège ne permet pas de rendre compte de ce phénomène. Un indice d'hétérogénéité sociale d'un établissement est nécessaire pour quantifier ce phénomène. L'écart-type de l'IPS des élèves d'un collège répond à cette problématique : plus il est élevé, plus le profil social des élèves est diversifié. Les collèges en REP+, avec une forte concentration d'élèves de milieu défavorisé, sont les collèges les moins hétérogènes socialement. À l'opposé les collèges publics hors EP scolarisent des élèves de milieux sociaux plus diversifiés. En effet, les trois quarts des collèges de REP+ ont un écart-type d'IPS inférieur à 26, tandis que les trois quarts des collèges publics hors EP ont un écart-type d'IPS supérieur à 30. La répartition des collèges selon la PCS des représentants légaux confirme cette faible diversité de l'origine sociale en REP+ : 97 % des collèges en REP+ scolarisent plus de 50 % d'élèves de milieu défavorisé alors que seul 1 % de ces collèges scolarisent plus de 25 % d'élèves de milieu favorisé ou très favorisé. La répartition des élèves selon la PCS des parents est plus équilibrée parmi les collèges publics hors EP : 79 % accueillent plus d'un quart d'élèves de milieu défavorisé et 76 % accueillent plus d'un quart d'élèves de milieu favorisé ou très favorisé. Dans le secteur privé, les collèges scolarisent en moyenne des élèves dont le profil social est favorisé et peu diversifié. Ainsi, les trois quarts des collèges privés ont un indice d'hétérogénéité inférieur à 29. En comparaison avec le secteur public hors EP, la répartition selon les PCS est, en effet, moins hétérogène : 30 % des collèges privés sous contrat scolarisent plus d'un quart d'élèves de milieu défavorisé alors que 93 % de ces collèges scolarisent plus d'un quart d'élèves de milieu favorisé ou très favorisé.""",
        "metadata": chunk_meta(META_NI, "3", "Une diversité sociale plus faible en REP+ et dans le secteur privé"),
    },
    {
        "id": "ips_2023_ni_manual_009",
        "contenu": """Des résultats au DNB fortement corrélés à l'IPS

L'IPS permet de décrire le profil social des élèves d'un collège, mais il peut aussi être mis en regard des résultats des établissements aux examens pour les relativiser. En effet, par construction, l'IPS mesure des facteurs extérieurs à l'établissement, mais dont on sait par la littérature scientifique qu'ils peuvent jouer un rôle dans la réussite scolaire des élèves. Les collèges présentent des performances hétérogènes au diplôme national du brevet (DNB). À la session 2022, le taux de réussite moyen des collèges pour la série générale s'établit à 89 %. Mais dans 10 % des collèges, il est inférieur à 78 % et dans un dixième, il est supérieur à 99 %. De même, pour 10 % des collèges, la note moyenne aux épreuves écrites du DNB est inférieure à 8,4/20, alors que pour 10 % des collèges elle est supérieure à 12,4/20. Les résultats au DNB sont en moyenne meilleurs dans les collèges les plus favorisés socialement. Le taux de réussite au DNB est ainsi de 97 % dans les collèges dont l'IPS moyen des candidats en série générale est supérieur à 130, soit 18 points de pourcentage de plus que dans les collèges les moins favorisés socialement, c'est-à-dire ceux dont l'IPS est inférieur à 80. De même, la note aux épreuves écrites du DNB est en moyenne plus élevée de 5 points (sur 20) pour les collèges les plus favorisés socialement, par rapport aux moins favorisés.""",
        "metadata": chunk_meta(META_NI, "3", "Des résultats au DNB fortement corrélés à l'IPS"),
    },

    # ── Note d'information IPS 23.16 — Page 4 ───────────────────
    {
        "id": "ips_2023_ni_manual_010",
        "contenu": """Pour la première fois, des indicateurs de valeur ajoutée des collèges (IVAC)

Cependant, l'IPS ne permet pas à lui seul d'expliquer les différences de résultats au DNB des collèges : des collèges au profil social proche présentent des résultats variables. Par exemple, parmi les collèges dont l'IPS est compris entre 100 et 110, un quart présente un taux de réussite au DNB inférieur à 85 % et un quart un taux supérieur à 95 %. L'IPS fait partie des facteurs, parmi d'autres, qui influent sur les résultats des collèges au DNB et sur lesquels le collège n'a pas ou peu de prise. Il illustre le fait que tous les collèges ne sont donc pas confrontés aux mêmes difficultés, aux mêmes enjeux pour faire réussir leurs élèves. À partir de cette année, la DEPP publie ainsi des indicateurs de valeur ajoutée des collèges, les IVAC, construits selon la même méthodologie que les indicateurs de valeur ajoutée des lycées, les IVAL et avec les mêmes objectifs : aller au-delà des résultats bruts aux examens que sont par exemple les taux de réussite et offrir une évaluation plus juste de l'action des collèges, de leur contribution pour accompagner leurs élèves jusqu'à la réussite. Les indicateurs en valeur ajoutée consistent pour cela à confronter les résultats de chaque collège à ceux attendus, compte tenu du profil des élèves scolarisés. L'IPS, au même titre que d'autres variables comme le niveau des élèves à l'entrée en sixième, est ainsi mobilisé pour construire des éléments pertinents d'évaluation des collèges. Le niveau scolaire à l'entrée au collège influant fortement sur les parcours et la réussite ultérieure des élèves, il était nécessaire d'attendre d'en avoir une mesure fine. C'est désormais le cas : la première cohorte d'élèves ayant passé les évaluations exhaustives à l'entrée en sixième en 2017, année de leur mise en place, a passé le brevet à la session 2021. Si les résultats au DNB des collèges dépendent fortement de leur IPS, ce n'est pas le cas de la valeur ajoutée. Les collèges qui ont une valeur ajoutée positive sont aussi bien représentés parmi les collèges avec un IPS plutôt faible que parmi ceux avec un IPS élevé.""",
        "metadata": chunk_meta(META_NI, "4", "Pour la première fois, des indicateurs de valeur ajoutée des collèges (IVAC)"),
    },

    # ── Guide IVAC 2025 — Page 4 ─────────────────────────────────
    # Exclue : mise en page deux colonnes mal parsée par Unstructured
    # ivac_2025_003 tronqué, ivac_2025_004 contenu mélangé
    {
        "id": "ivac_2025_manual_page4",
        "contenu": """Quels indicateurs de résultats retenir ?

Le ministère présente quatre indicateurs complémentaires publiés pour tous les collèges publics et privés sous contrat.

Deux indicateurs sont accompagnés d'une valeur ajoutée (résultat constaté comparé au résultat attendu compte tenu du profil des élèves) :
— La note moyenne aux épreuves écrites du DNB (français, mathématiques, sciences, histoire-géographie), calculée sur 20 points.
— Le taux de réussite au DNB : proportion d'élèves reçus parmi ceux présents à l'examen.

Deux indicateurs sont publiés en valeur brute uniquement, sans valeur ajoutée associée :
— Le taux d'accès de la 6ème à la 3ème : probabilité pour un élève de sixième d'atteindre la troisième en restant dans le collège, quel que soit le nombre d'années nécessaire.
— La part d'élèves présents au DNB : proportion des élèves de troisième présentés aux épreuves écrites du brevet.""",
        "metadata": chunk_meta(META_IVAC, "4", "Quels indicateurs de résultats retenir"),
    },

    # ── Guide IVAC 2025 — Pages 9, 10, 11 ───────────────────────
    # Exclues : formules mathématiques classifiées comme Title par Unstructured
    # Page 10 section "Calcul pratique" exclue car exemple fictif
    {
        "id": "ivac_2025_manual_000",
        "contenu": """Le calcul des indicateurs

Les IVAC correspondent à quatre indicateurs : taux de réussite, note moyenne aux épreuves écrites, taux d'accès et part d'élèves présents au DNB. À chacun des deux premiers indicateurs sont associés des taux attendus, qui correspondent aux résultats moyens estimés pour des élèves d'âge, d'origine sociale, de niveau scolaire à l'entrée en sixième et de sexe comparables, scolarisés dans des établissements comparables en termes de caractéristiques de la population accueillie.""",
        "metadata": chunk_meta(META_IVAC, "9", "Le calcul des indicateurs"),
    },
    {
        "id": "ivac_2025_manual_001",
        "contenu": """Note moyenne constatée aux épreuves écrites

Cet indicateur mesure pour chaque établissement la moyenne pondérée des notes obtenues par ses élèves aux épreuves écrites (mathématiques, français, histoire-géographie, sciences) du diplôme national du brevet. Cette note est établie sur 300 points : 100 pour le français, 100 pour les mathématiques, 50 pour l'histoire-géographie et 50 pour les sciences. La note est ensuite divisée par 15 pour être ramenée sur 20 points. L'indicateur s'écrit ainsi : Note moyenne constatée = Somme des notes aux quatre épreuves écrites divisée par 15, le tout divisé par le nombre de Présents. Où : Présents = élèves inscrits au brevet dans le collège et ayant obtenu au moins une note aux épreuves écrites. Notes aux épreuves écrites : notes aux épreuves de français, maths, histoire-géographie et sciences, avant majoration éventuelle par le jury.""",
        "metadata": chunk_meta(META_IVAC, "9", "Note moyenne constatée aux épreuves écrites"),
    },
    {
        "id": "ivac_2025_manual_002",
        "contenu": """Taux de réussite constaté

Le brevet est évalué sur 800 points : l'évaluation du socle commun représente 400 points, les quatre épreuves écrites terminales représentent 300 points, la soutenance orale représente 100 points. L'élève est reçu s'il cumule 400 points sur les 800. Le taux de réussite au brevet est la proportion, parmi les élèves présents à l'examen (Note : Les candidats qui ont déjà obtenu le brevet en N-1 sont retirés du calcul.), de ceux qui ont obtenu le diplôme. Le taux constaté de réussite au brevet = Diplômés × 100 / Présents. Où : Diplômés = élèves de l'établissement ayant obtenu le brevet en juin ou en septembre de l'année (N). Présents = élèves inscrits au brevet dans le collège et ayant obtenu au moins une note aux épreuves écrites.""",
        "metadata": chunk_meta(META_IVAC, "9", "Taux de réussite constaté"),
    },
    {
        "id": "ivac_2025_manual_003",
        "contenu": """Taux d'accès constaté

Le taux d'accès de la sixième à la troisième est la probabilité, pour un élève, d'accéder successivement de sixième en cinquième, de cinquième en quatrième, et de quatrième en troisième au sein de l'établissement (Note : Les déménagements sont pris en compte dans le calcul du taux d'accès. Un élève qui accède au niveau supérieur tout en changeant d'établissement ne pénalise pas le taux d'accès du collège d'origine si cela fait suite à un changement de commune de résidence ou si le département de l'établissement de destination est différent du département de l'établissement d'origine. Les départs d'établissement pour suivre une formation non-disponible dans le collège d'origine sont considérés comme des réussites pour le collège d'origine. Depuis la session 2025 du DNB, les élèves en Upe2a sont retirés du calcul du taux d'accès.). Ainsi, le taux d'accès de la sixième à la troisième est le produit de ces trois taux intermédiaires (6ème-5ème, 5ème-4ème et 4ème-3ème).

Pour les IVAC session N du brevet, chaque taux d'accès intermédiaire est calculé en observant ce que les élèves inscrits dans l'établissement en octobre N-1 sont devenus en octobre N. Le taux d'accès de la sixième à la troisième, produit de ces taux intermédiaires, n'est donc pas fondé sur le suivi d'une cohorte réelle d'élèves, mais sur l'observation du parcours des élèves présents à tous les niveaux une même année scolaire. C'est ce qu'il est convenu d'appeler un suivi de cohorte fictive.

Le taux d'accès constaté d'un niveau à l'autre = Succès × 100 / (Inscrits − Doublants). Où : Inscrits = élèves inscrits dans le niveau de départ en octobre de l'année (N-1). Doublants = élèves de l'établissement qui redoublent le niveau de départ dans le collège en octobre de l'année (N). Succès = élèves qui passent dans le niveau supérieur dans le collège en octobre de l'année (N).""",
        "metadata": chunk_meta(META_IVAC, "10", "Taux d'accès constaté"),
    },
    {
        "id": "ivac_2025_manual_004",
        "contenu": """Part d'élèves présents à l'examen

La part d'élèves présents à l'examen est la proportion d'élèves qui se sont présentés à au moins une épreuve écrite du brevet parmi l'ensemble des élèves du collège (Note : Les élèves qui ont déjà obtenu le brevet en N-1, s'ils ne se représentent pas en N, sont retirés du calcul.), et ce quelle que soit la série, générale ou professionnelle. L'indicateur distingue les élèves de troisième ordinaire et ceux de troisième Segpa.

Cette proportion est calculée de la manière suivante : Part d'élèves présents au brevet = Présents / Nombre total d'élèves. Où : Présents = élèves inscrits en 3ème ordinaire ou Segpa, et présents à la série générale ou professionnelle du brevet. Nombre total d'élèves = nombre total d'élèves de l'établissement en 3ème ordinaire ou Segpa à la rentrée N-1.""",
        "metadata": chunk_meta(META_IVAC, "11", "Part d'élèves présents à l'examen"),
    },
    {
        "id": "ivac_2025_manual_005",
        "contenu": """Taux attendus et valeurs ajoutées

La DEPP a mis au point un modèle statistique (Note : La mise en œuvre du modèle se base sur des théories statistiques élaborées et fait appel à des procédures de calculs longues et complexes qui ne peuvent être reproduites à la main. Il n'est donc pas possible d'expliciter dans le présent document les formules de calcul.) de calcul du taux et de la note attendus de chaque collège. Il permet de simuler, pour chaque élève, sa probabilité d'obtenir le brevet et d'avoir une note moyenne donnée aux épreuves écrites, en fonction de ses caractéristiques (âge, niveau scolaire à l'entrée en sixième (Note : Lorsque la note individuelle d'un élève aux évaluations exhaustives de sixième n'est pas retrouvée, elle est imputée par la note moyenne des élèves de son collège.), origine sociale et sexe) et des caractéristiques du collège dans lequel il évolue.

Une fois obtenues ces probabilités pour chaque élève, il suffit ensuite d'en calculer les moyennes. Le taux de réussite attendu pour l'établissement est obtenu en faisant la moyenne des probabilités de réussite de chaque élève ayant passé la série générale. Le taux de réussite attendu n'est pas calculé pour la série professionnelle du brevet.

Pour chaque indicateur, taux de réussite ou note moyenne à l'écrit, la valeur ajoutée de l'établissement est la différence entre le taux constaté de l'établissement et le taux attendu. Aucune valeur ajoutée n'est calculée pour la série professionnelle du brevet. Valeur ajoutée = Taux constaté – Taux attendu.""",
        "metadata": chunk_meta(META_IVAC, "11", "Taux attendus et valeurs ajoutées"),
    },

    # ── Source vulgarisation — Description IVAC ──────────────────
    {
        "id": "ivac_vulgaire_000",
        "contenu": """Les indicateurs de valeur ajoutée des collèges (IVAC) sont une batterie d'indicateurs qui visent à évaluer l'action propre de chaque collège pour faire réussir les élèves qu'il accueille, en termes de réussite au diplôme national du brevet (DNB) et d'accompagnement tout au long de sa scolarité au collège. Ils sont calculés pour la première fois pour la session 2022 du DNB.

Les IVAC permettent un diagnostic qui va au-delà de celui qui peut être fait à partir des seuls taux de réussite bruts à l'examen. Pour donner une image de l'apport de chaque collège, le calcul statistique s'efforce d'éliminer l'incidence des facteurs de réussite scolaire extérieurs au collège, pour essayer de conserver ce qui est dû à son action propre. Pour juger de l'efficacité d'un collège, la réussite de chacun de ses élèves doit ainsi être comparée à celle des élèves comparables scolarisés dans des collèges comparables.""",
        "metadata": chunk_meta(META_IVAC_VULGAIRE, "1", "Définition et objectifs des IVAC"),
    },
    {
        "id": "ivac_vulgaire_001",
        "contenu": """Pour chaque collège, la valeur ajoutée correspond à la différence entre les résultats obtenus et les résultats qui étaient attendus, compte tenu des caractéristiques scolaires et sociodémographiques des élèves accueillis. L'analyse combine des facteurs individuels des élèves (âge et sexe, score obtenu aux évaluations à l'entrée en sixième, profil social) et des facteurs liés à la structure de l'établissement (pourcentage de filles, part d'élèves en retard scolaire, profil social et score moyen obtenu aux évaluations de sixième).

La valeur ajoutée est une approche relative et non pas absolue. Si la valeur ajoutée est positive, on a tout lieu de penser que l'établissement a plus fait réussir ses élèves que ce qui était prévu, au vu du profil des élèves qu'il accueillait. Si elle est négative, cela signifie que les résultats de l'établissement sont inférieurs à la moyenne des résultats des établissements qui lui ressemblent.""",
        "metadata": chunk_meta(META_IVAC_VULGAIRE, "1", "Calcul et interprétation de la valeur ajoutée"),
    },
    {
        "id": "ivac_vulgaire_002",
        "contenu": """Conditions de publication et précautions d'usage des IVAC

Les résultats bruts sont calculés dès lors que le nombre de candidats présents en série générale est supérieur ou égal à 20. Pour que les valeurs ajoutées soient calculées, il est nécessaire qu'au moins 40 élèves soient présents en série générale. La valeur ajoutée n'est pas calculée si les scores aux évaluations de sixième sont retrouvés pour moins de 75 % des candidats.

Les IVAC ne constituent pas un classement officiel des collèges. Ils visent à évaluer la capacité d'un établissement à accompagner la progression de ses élèves par rapport à leur profil sociodémographique et scolaire initial. Ils sont destinés à servir d'outils de pilotage pédagogique et de transparence, et non à établir des palmarès entre établissements. Une valeur ajoutée négative ne signifie pas que les élèves régressent — elle signifie que les résultats sont inférieurs à ce qui était attendu compte tenu du profil des élèves. Seule l'analyse combinée de l'ensemble des indicateurs donne une image juste d'un établissement.""",
        "metadata": chunk_meta(META_IVAC_VULGAIRE, "1", "Conditions de publication et précautions d'usage des IVAC"),
    },

    # ── Source vulgarisation — Page IPS officielle ───────────────
    {
        "id": "ips_vulgaire_000",
        "contenu": """L'indice de position sociale (IPS) d'un établissement scolaire est un indicateur calculé par la DEPP. Ce dernier résume les conditions socio-économiques et culturelles des familles des élèves accueillis dans l'établissement. L'IPS permet ainsi de rendre compte des disparités sociales existantes entre établissements et à l'intérieur de ces mêmes établissements.

Quel est le niveau social moyen d'un établissement scolaire ? Quel est le degré d'hétérogénéité sociale des élèves qu'il accueille ? Comment comparer cet établissement à un autre, du point de vue de leur situation sociale ? L'indice de position sociale (IPS) est un outil construit par la DEPP pour répondre à ce type de questions.""",
        "metadata": chunk_meta(META_IPS_VULGAIRE, "1", "Définition et objectif de l'IPS"),
    },
    {
        "id": "ips_vulgaire_001",
        "contenu": """Méthodologie de l'IPS

Les valeurs de l'IPS représentent les conditions socio-économiques et culturelles moyennes des professions. Elles sont déterminées à partir des valeurs de référence des catégories socio-professionnelles des parents ou du parent de l'élève. Elles peuvent être calculées pour chaque établissement scolaire. Il en résulte un indicateur statistique qui permet de rendre compte de la composition sociale de l'établissement.

L'IPS d'un élève correspond à la valeur de référence du croisement des PCS de ses deux parents. L'IPS moyen d'un collège est la moyenne des IPS de l'ensemble des élèves qu'il accueille. Les valeurs d'IPS varient de 45 à 185 : plus l'IPS est élevé, plus les conditions familiales sont favorables à l'apprentissage. Il existe 1 600 combinaisons possibles de PCS père et mère.""",
        "metadata": chunk_meta(META_IPS_VULGAIRE, "1", "Méthodologie de l'IPS"),
    },
    {
        "id": "ips_vulgaire_002",
        "contenu": """Précautions d'usage de l'IPS

L'IPS n'est pas en lui-même une mesure directe des revenus ou du niveau d'éducation des parents. Il résume des conditions socio-économiques et culturelles moyennes associées à chaque catégorie socioprofessionnelle. Un IPS élevé signifie que, en moyenne, les familles qui ressemblent à celle de l'élève ont des conditions plus favorables à l'apprentissage — pas nécessairement que la famille de cet élève précis est plus avantagée.

Il convient de ne pas surinterpréter des écarts de 3 points d'IPS moyen entre deux collèges : la marge d'erreur de mesure est de l'ordre de plus ou moins 3 points. L'IPS mesure le contexte social d'un établissement, pas sa qualité pédagogique. Un collège avec un IPS faible peut très bien avoir une excellente valeur ajoutée — c'est-à-dire faire mieux réussir ses élèves que ce qu'on attendrait compte tenu de leur profil social.

Mise à jour 2023 : grâce à une meilleure remontée des professions des deux parents dans le secteur privé sous contrat, l'IPS de ces établissements reflète mieux leur profil social. Du fait de cette évolution, la comparabilité 2022-2023 n'est pas assurée pour les établissements privés sous contrat.""",
        "metadata": chunk_meta(META_IPS_VULGAIRE, "1", "Précautions d'usage de l'IPS"),
    },
]

SOURCES = [
    {
        "fichier": "Depp_Guide_méthodologique_IVAC_2025.pdf-515492.pdf",
        "pages_exclure": [1, 2, 4, 7, 9, 10, 11],
        **META_IVAC,
    },
    {
        "fichier": "EF-90-chap-01-construction-d-un-indice-de-position-sociale-des-eleves-pdfa.pdf",
        "pages_exclure": [10, 19, 20, 21, 22, 23, 24],
        "dc_title":      "Construction d'un Indice de Position Sociale des élèves",
        "dc_creator":    "Thierry Rocher — MENESR-DEPP",
        "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
        "dc_date":       "2016",
        "dc_type":       "article_methodologique",
        "dc_source":     "https://www.education.gouv.fr/education-formations-n-90-avril-2016-5959",
        "chunk_domaine": "ips",
        "dc_niveau":     "avancé",
    },
    {
        "fichier": "Indice de position sociale (IPS) _ actualisation 2022-476864.pdf",
        "pages_exclure": [1, 2, 3, 4, 5, 16, 17, 18, 19, 20, 21, 22],
        "dc_title":      "Indice de position sociale (IPS) — Actualisation 2022",
        "dc_creator":    "Thierry Rocher — DEPP",
        "dc_publisher":  "Ministère de l'Éducation Nationale — DEPP",
        "dc_date":       "2023",
        "dc_type":       "document_travail",
        "dc_source":     "https://www.education.gouv.fr/indice-de-position-sociale-ips-actualisation-2022-476864",
        "chunk_domaine": "ips",
        "dc_niveau":     "avancé",
    },
    {
        "fichier": "NI 23.16-364089_IPS.pdf",
        "pages_exclure": [1, 2, 3, 4],
        **META_NI,
    },
]


def est_chunk_fragmente(texte: str) -> bool:
    lignes = [l.strip() for l in texte.split("\n") if l.strip()]
    if len(lignes) < 4:
        return False
    lignes_courtes = sum(1 for l in lignes if len(l) < 40)
    return (lignes_courtes / len(lignes)) > 0.5


def extraire_chunks(chemin: str, pages_exclure: list) -> list:
    elements = partition_pdf(chemin)
    elements = [e for e in elements if type(e).__name__ != "Footer"]

    if pages_exclure:
        elements_filtres = []
        for e in elements:
            page = None
            try:
                page = e.metadata.page_number
            except AttributeError:
                pass
            if page not in pages_exclure:
                elements_filtres.append(e)
        elements = elements_filtres

    chunks_raw = chunk_by_title(
        elements,
        max_characters=CHUNK_MAX_CHARACTERS,
        new_after_n_chars=CHUNK_NEW_AFTER_N_CHARS,
        combine_text_under_n_chars=CHUNK_COMBINE_UNDER_N_CHARS,
    )

    chunks_valides = []
    for chunk in chunks_raw:
        texte = chunk.text.strip()

        if any(kw.lower() in texte.lower() for kw in KEYWORDS_EXCLUSION):
            continue
        premier_mot = texte.split()[0] if texte.split() else ""
        if premier_mot and premier_mot[0].islower():
            continue
        if re.match(r'^[A-Z] [a-z]', texte):
            continue
        if texte.startswith("(cid:"):
            continue
        if len(texte) < 100:
            continue
        chars_alpha = sum(1 for c in texte if c.isalpha())
        ratio_alpha = chars_alpha / len(texte) if texte else 0
        if ratio_alpha < 0.60:
            continue
        if re.search(r'[a-zàâéèêëîïôùûü][A-ZÀÂÉÈÊËÎÏÔÙÛÜ]', texte) and \
           len(re.findall(r'[a-zàâéèêëîïôùûü][A-ZÀÂÉÈÊËÎÏÔÙÛÜ]', texte)) > 3:
            continue
        if est_chunk_fragmente(texte):
            continue

        chunks_valides.append(chunk)

    return chunks_valides


def construire_metadata(chunk, source: dict) -> dict:
    page = "N/A"
    try:
        page = str(chunk.metadata.page_number)
    except AttributeError:
        pass
    titre_section = ""
    try:
        titre_section = chunk.metadata.section or ""
    except AttributeError:
        pass
    return {
        "dc_title":            source["dc_title"],
        "dc_creator":          source["dc_creator"],
        "dc_publisher":        source["dc_publisher"],
        "dc_date":             source["dc_date"],
        "dc_type":             source["dc_type"],
        "dc_source":           source["dc_source"],
        "chunk_domaine":       source["chunk_domaine"],
        "dc_niveau":           source["dc_niveau"],
        "chunk_page":          page,
        "chunk_titre_section": titre_section,
    }


def main():
    print("=== INGESTION RAG AGENT-ECOLES v7 ===")
    print("=== Unstructured + chunks manuels + sources vulgarisation ===\n")

    chroma_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        CHROMA_PATH
    )
    os.makedirs(chroma_path, exist_ok=True)

    client = chromadb.PersistentClient(path=chroma_path)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL,
    )

    try:
        client.delete_collection(CHROMA_COLLECTION)
        print("Collection existante supprimée\n")
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = 0

    print(f"→ Chunks manuels ({len(CHUNKS_MANUELS)} chunks)")
    collection.upsert(
        ids=[c["id"] for c in CHUNKS_MANUELS],
        documents=[c["contenu"] for c in CHUNKS_MANUELS],
        metadatas=[c["metadata"] for c in CHUNKS_MANUELS],
    )
    total_chunks += len(CHUNKS_MANUELS)
    print(f"  ✓ {len(CHUNKS_MANUELS)} chunks manuels ingérés\n")

    for source in SOURCES:
        chemin = os.path.join(SOURCES_DIR, source["fichier"])

        if not os.path.exists(chemin):
            print(f"⚠  Fichier non trouvé : {source['fichier'][:60]}")
            continue

        print(f"→ {source['dc_title'][:55]}")
        print(f"  Niveau : {source['dc_niveau']} | Pages exclues : {source['pages_exclure']}")

        chunks_bruts = extraire_chunks(chemin, source["pages_exclure"])

        prefix = f"{source['chunk_domaine']}_{source['dc_date']}"

        # Assignation des IDs AVANT filtrage artefacts
        chunks_avec_ids = [
            (f"{prefix}_{i:03d}", c)
            for i, c in enumerate(chunks_bruts)
        ]

        # Filtrage artefacts sur les IDs définitifs
        chunks_filtres = [
            (id_, c) for id_, c in chunks_avec_ids
            if id_ not in CHUNKS_ARTEFACTS
        ]

        if not chunks_filtres:
            print(f"  ⚠  Aucun chunk après filtrage artefacts\n")
            continue

        ids_filtres = [x[0] for x in chunks_filtres]
        chunks_ok = [x[1] for x in chunks_filtres]

        documents = [c.text.strip() for c in chunks_ok]
        metadatas = [construire_metadata(c, source) for c in chunks_ok]

        collection.upsert(
            ids=ids_filtres,
            documents=documents,
            metadatas=metadatas,
        )

        total_chunks += len(chunks_filtres)
        print(f"  ✓ {len(chunks_filtres)} chunks ingérés")
        for i, (doc, meta) in enumerate(zip(documents[:2], metadatas[:2])):
            print(f"    [{i}] p.{meta['chunk_page']} — {doc[:100]}...")
        print()

    print(f"✓ Total : {total_chunks} chunks dans ChromaDB\n")

    print("=== TEST DE RECHERCHE ===\n")
    questions = [
        "qu'est-ce que la valeur ajoutée d'un collège",
        "quels sont les quatre indicateurs IVAC",
        "comment est calculé l'IPS",
        "différence IPS public privé",
        "taux d'accès sixième troisième",
        "précautions d'usage des IVAC",
        "météo Paris demain",
    ]

    for question in questions:
        results = collection.query(query_texts=[question], n_results=2)
        print(f"Q : '{question}'")
        for i, (doc, meta) in enumerate(zip(
            results["documents"][0], results["metadatas"][0]
        )):
            print(f"  [{i+1}] [{meta.get('dc_niveau','?')}] {meta['dc_title'][:45]} — p.{meta['chunk_page']}")
            print(f"       {doc[:110]}...")
        print()


if __name__ == "__main__":
    main()
