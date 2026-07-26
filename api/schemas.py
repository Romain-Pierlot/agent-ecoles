"""api/schemas.py — Contrats de données de l'API (requêtes/réponses HTTP)."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    question: str = ""
    # Choix cliqué en réponse à une clarification structurée précédente, ou
    # à un bouton "voir plus" (cf. graph_router.poser_resolution_choix) —
    # présent seulement quand l'utilisateur clique plutôt que de taper une
    # question.
    # {"type": "zone", "commune": str, "code_departement": str}
    # {"type": "noms", "choix": {nom: uai, ...}}
    # {"type": "voir_plus", "secteur": "public"|"prive"}
    resolution: Optional[dict] = None


class OptionChoix(BaseModel):
    label: str
    valeur: dict


class GroupeChoix(BaseModel):
    titre: str
    options: list[OptionChoix]


class Choix(BaseModel):
    type: str  # "zone", "noms" ou "voir_plus"
    groupes: list[GroupeChoix]


class ChatResponse(BaseModel):
    reponse: str
    # Présent seulement quand une clarification ambiguë (zone ou noms
    # d'établissements) attend un choix cliquable — cf. docs/fiches/
    # (désambiguïsation par boutons, S11.2). Absent sinon.
    choix: Optional[Choix] = None


# ============================================================
# Fiche établissement (GET /etablissement/{uai})
# ============================================================

class EtablissementIdentite(BaseModel):
    uai: str
    nom: str
    type_etablissement: str
    secteur: str
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    commune: str
    code_departement: Optional[str] = None
    libelle_departement: Optional[str] = None
    code_academie: Optional[str] = None
    libelle_academie: Optional[str] = None
    libelle_region: Optional[str] = None
    telephone: Optional[str] = None
    mail: Optional[str] = None
    web: Optional[str] = None
    date_ouverture: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notation: Optional[str] = None
    badge_va: Optional[str] = None
    # True si la VA de cet établissement était absente et a été substituée
    # par 0 (neutre) pour calculer sa notation — cf. data/ingest.py::calculer_scores.
    va_imputee: bool = False
    appartenance_education_prioritaire: Optional[str] = None
    ulis: bool
    segpa: bool
    section_arts: bool
    section_cinema: bool
    section_theatre: bool
    section_sport: bool
    section_internationale: bool
    section_europeenne: bool


class MentionDetail(BaseModel):
    libelle: str
    nb_eleves: Optional[int] = None
    taux_pct: Optional[float] = None


class BrevetResultats(BaseModel):
    session: str
    brevet_nb_candidats_general: Optional[int] = None
    brevet_taux_reussite_general: Optional[float] = None
    brevet_note_ecrit_general: Optional[float] = None
    taux_acces_6eme_3eme: Optional[float] = None
    taux_reussite_national: Optional[float] = None
    taux_reussite_departemental: Optional[float] = None
    note_ecrit_national: Optional[float] = None
    note_ecrit_departemental: Optional[float] = None
    taux_acces_6eme_3eme_national: Optional[float] = None
    taux_acces_6eme_3eme_departemental: Optional[float] = None
    mentions: list[MentionDetail]


class ValeurAjouteeDetail(BaseModel):
    va_taux: Optional[float] = None
    taux_observe: Optional[float] = None
    taux_attendu: Optional[float] = None
    va_note: Optional[float] = None
    note_observee: Optional[float] = None
    note_attendue: Optional[float] = None


class EvolutionPoint(BaseModel):
    session: str
    brevet_taux_reussite_general: Optional[float] = None
    brevet_note_ecrit_general: Optional[float] = None
    brevet_taux_reussite_national: Optional[float] = None
    notation: Optional[str] = None
    badge_va: Optional[str] = None


class PositionnementSocial(BaseModel):
    annee_scolaire: str
    ips_moyen: Optional[float] = None
    ecart_type_ips: Optional[float] = None
    ips_national: Optional[float] = None
    ips_academique: Optional[float] = None
    ips_departemental: Optional[float] = None
    ecart_type_ips_national: Optional[float] = None
    ecart_type_ips_departemental: Optional[float] = None


class LanguesOffertes(BaseModel):
    lv1: list[str]
    lv2: list[str]
    lca: list[str]


class ProchainesVacances(BaseModel):
    zone: str
    periode: str
    date_debut: str
    date_fin: Optional[str] = None


class CollegeSecteurItem(BaseModel):
    """Mêmes champs que CollegeVille/EtablissementRecherche (notation,
    dispositifs) + la lignée géo complète (nécessaire pour construire le
    lien vers la fiche établissement, cf. web/src/lib/hrefsGeo.ts) + une
    distance (calculée par rapport à un point de référence : adresse
    recherchée pour /secteur, établissement consulté pour la fiche) — pas de
    brevet_taux_reussite_general, ces contextes affichent la distance à la
    place. Défini ici (avant FicheEtablissement) car partagé par deux
    endpoints : FicheEtablissement.etablissements_proches (GET
    /etablissement/{uai}) et SecteurResultats.colleges_secteur/
    colleges_alentours (GET /secteur) — même forme produite des deux côtés
    par agent/tools/geo_tool.py::ligne_vers_college."""
    uai: str
    nom: str
    commune: str
    secteur: str
    libelle_region: str
    code_departement: str
    libelle_departement: str
    distance_km: float
    notation: Optional[str] = None
    badge_va: Optional[str] = None
    appartenance_education_prioritaire: Optional[str] = None
    ulis: bool
    segpa: bool
    section_arts: bool
    section_cinema: bool
    section_theatre: bool
    section_sport: bool
    section_internationale: bool
    section_europeenne: bool


class FicheEtablissement(BaseModel):
    identite: EtablissementIdentite
    brevet: Optional[BrevetResultats] = None
    valeur_ajoutee: Optional[ValeurAjouteeDetail] = None
    evolution: list[EvolutionPoint]
    positionnement_social: Optional[PositionnementSocial] = None
    langues: Optional[LanguesOffertes] = None
    sections_sportives: list[str] = []
    zone_vacances: Optional[str] = None
    prochaines_vacances: Optional[ProchainesVacances] = None
    etablissements_proches: list[CollegeSecteurItem] = []


# ============================================================
# Hub région/département (GET /region/{slug}, .../departement/{slug})
# ============================================================

class AgregatEtablissements(BaseModel):
    nb_etablissements: int
    taux_reussite_moyen: Optional[float] = None
    # Moyenne non pondérée de la VA du taux de réussite, calculée uniquement
    # sur les collèges du périmètre ayant une VA publiée par le Ministère
    # (jamais une VA imputée à 0) — cf. agent/tools/hierarchie_tool.py::
    # agreger_sous_divisions. None si aucun collège du périmètre n'en a.
    va_moyenne: Optional[float] = None
    # Proportion de collèges du périmètre avec VA renseignée (0 à 1) —
    # nuance va_moyenne quand elle repose sur peu de collèges.
    va_couverture: Optional[float] = None
    # Nombre brut de collèges du périmètre avec VA renseignée — sert de seuil
    # d'affichage minimal (ex: page ville, cf. web/src/app/.../ville/page.tsx :
    # une moyenne sur 1-2 établissements n'est pas un indicateur territorial).
    va_nb_renseignees: int = 0
    # Pas de notation en lettres au niveau agrégat (région/département/ville)
    # — cf. decision_log.md : la notation combine résultats + valeur ajoutée
    # d'un établissement précis, ça n'a pas de sens transposé à une zone
    # géographique, et la médiane d'un groupe se classait quasi toujours
    # dans la même lettre (signal inutilisable). Notation individuelle
    # inchangée, cf. EtablissementIdentite.notation.


class SousDivision(AgregatEtablissements):
    code: str
    libelle: str


class TopEtablissement(BaseModel):
    """Ligne des blocs "Meilleure notation" / "Meilleure valeur ajoutée"
    des pages région/département (cf. docs/Design_system/Sitemap.dc.html) —
    mêmes champs que CollegeVille, plus la lignée département (commune +
    code/libellé département) : sur la page région, un établissement du
    top 5 peut appartenir à n'importe lequel des départements de la région,
    il faut son propre département pour reconstruire l'URL complète vers
    sa fiche. Pas besoin de la région (déjà connue de la page). Plus la VA
    du taux de réussite seule (chiffre affiché sur le bloc VA)."""
    uai: str
    nom: str
    commune: str
    code_departement: str
    libelle_departement: str
    secteur: str
    notation: Optional[str] = None
    appartenance_education_prioritaire: Optional[str] = None
    ulis: bool
    segpa: bool
    section_arts: bool
    section_cinema: bool
    section_theatre: bool
    section_sport: bool
    section_internationale: bool
    section_europeenne: bool
    brevet_va_taux_reussite_general: Optional[float] = None


class NationalHub(BaseModel):
    session_utilisee: Optional[str] = None
    global_: AgregatEtablissements = Field(alias="global")
    regions: list[SousDivision]

    model_config = {"populate_by_name": True}


class RegionHub(BaseModel):
    libelle_region: str
    session_utilisee: Optional[str] = None
    global_: AgregatEtablissements = Field(alias="global")
    departements: list[SousDivision]
    top_notation: list[TopEtablissement]
    top_va: list[TopEtablissement]

    model_config = {"populate_by_name": True}


class DepartementHub(BaseModel):
    libelle_region: str
    code_departement: str
    libelle_departement: str
    session_utilisee: Optional[str] = None
    global_: AgregatEtablissements = Field(alias="global")
    communes: list[SousDivision]
    top_notation: list[TopEtablissement]
    top_va: list[TopEtablissement]

    model_config = {"populate_by_name": True}


# ============================================================
# Page terminale ville (GET /region/{slug}/departement/{slug}/ville/{slug})
# ============================================================

class CollegeVille(BaseModel):
    """Sous-ensemble de EtablissementIdentite + réussite brevet, pour une
    carte résultat de la page ville — pas la fiche établissement complète."""
    uai: str
    nom: str
    secteur: str
    notation: Optional[str] = None
    badge_va: Optional[str] = None
    va_imputee: bool = False
    appartenance_education_prioritaire: Optional[str] = None
    ulis: bool
    segpa: bool
    section_arts: bool
    section_cinema: bool
    section_theatre: bool
    section_sport: bool
    section_internationale: bool
    section_europeenne: bool
    brevet_taux_reussite_general: Optional[float] = None
    # VA du taux de réussite, session la plus récente — None si non publiée
    # par le Ministère (dans ce cas va_imputee ci-dessus vaut True).
    brevet_va_taux_reussite_general: Optional[float] = None


class VilleHub(BaseModel):
    libelle_region: str
    code_departement: str
    libelle_departement: str
    commune: str
    session_utilisee: Optional[str] = None
    global_: AgregatEtablissements = Field(alias="global")
    nb_publics: int
    nb_prives: int
    # Taux national de la session affichée, pour le seuil de couleur relatif
    # (cf. web/src/lib/tokens.ts::sentimentReussite) — pas un jugement porté
    # ici, juste la donnée brute transmise au front.
    taux_reussite_national: Optional[float] = None
    colleges: list[CollegeVille]

    model_config = {"populate_by_name": True}


# ============================================================
# Recherche libre (GET /recherche)
# ============================================================

class EtablissementRecherche(BaseModel):
    """Résultat établissement d'une recherche libre — mêmes champs que
    CollegeVille, plus la lignée géographique complète (contrairement à la
    page ville où région/département/commune sont déjà connus de la page,
    les résultats de recherche viennent potentiellement de partout en
    France)."""
    uai: str
    nom: str
    secteur: str
    notation: Optional[str] = None
    badge_va: Optional[str] = None
    va_imputee: bool = False
    appartenance_education_prioritaire: Optional[str] = None
    ulis: bool
    segpa: bool
    section_arts: bool
    section_cinema: bool
    section_theatre: bool
    section_sport: bool
    section_internationale: bool
    section_europeenne: bool
    brevet_taux_reussite_general: Optional[float] = None
    brevet_va_taux_reussite_general: Optional[float] = None
    libelle_region: str
    code_departement: str
    libelle_departement: str
    commune: str


class CommuneRecherche(BaseModel):
    commune: str
    code_departement: str
    libelle_departement: str
    libelle_region: str
    nb_etablissements: int
    taux_reussite_moyen: Optional[float] = None


class RechercheResultats(BaseModel):
    query: str
    session_utilisee: Optional[str] = None
    # Même convention que VilleHub.taux_reussite_national — sert au seuil de
    # couleur relatif des cartes établissement (cf. web/src/lib/tokens.ts).
    taux_reussite_national: Optional[float] = None
    etablissements: list[EtablissementRecherche]
    communes: list[CommuneRecherche]
    # Vrai total filtré (COUNT(*) sur le même WHERE, sans LIMIT) — pas une
    # borne basse : le nombre réel de résultats, indépendamment de la
    # longueur de la liste ci-dessus (bornée à LIMITE_RESULTATS).
    etablissements_total: int = 0
    communes_total: int = 0
    # True si la liste retournée est plus courte que le total réel
    # ci-dessus (cf. decision_log.md, campagne de test /recherche).
    etablissements_tronques: bool = False
    communes_tronquees: bool = False


# ============================================================
# Collège de secteur (GET /secteur) — rattachement officiel (carte
# scolaire du Ministère, collèges publics uniquement) à partir d'une
# adresse, cf. agent/tools/carte_scolaire_tool.py.
# ============================================================

class SuggestionAdresse(BaseModel):
    label: str
    type: Optional[str] = None


class SecteurResultats(BaseModel):
    adresse_recherchee: str
    # "adresse_non_reconnue"/"adresse_ambigue" sont des résultats normaux et
    # attendus (échec du géocodage BAN / plusieurs communes candidates),
    # pas des pannes techniques — cf. carte_scolaire_tool.py.
    etat: Literal["trouve", "multi_secteur", "non_determinable", "adresse_ambigue", "adresse_non_reconnue"]
    adresse_normalisee: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Académie du département géocodé — utilisée par l'état "non_determinable"
    # pour orienter vers le bon rectorat (cf. carte_scolaire_tool.py).
    academie: Optional[str] = None
    colleges_secteur: list[CollegeSecteurItem] = []
    colleges_alentours: list[CollegeSecteurItem] = []
    # Rempli seulement pour l'état "adresse_ambigue" : candidats parmi
    # lesquels l'utilisateur doit choisir avant qu'on résolve le secteur.
    suggestions_ambigues: list[SuggestionAdresse] = []


class SuggestionsAdresseResultats(BaseModel):
    suggestions: list[SuggestionAdresse] = []


class RechercheLogRequest(BaseModel):
    """Corps de POST /recherche/log — journalisation d'une recherche par nom.

    Envoyé une seule fois par recherche réelle (composant serveur
    recherche/page.tsx, jamais à chaque changement de filtre côté client,
    cf. decision_log.md).
    """
    terme: str
    nb_etablissements: int
    nb_communes: int
