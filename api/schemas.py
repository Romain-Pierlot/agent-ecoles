"""api/schemas.py — Contrats de données de l'API (requêtes/réponses HTTP)."""
from typing import Optional
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


# ============================================================
# Hub région/département (GET /region/{slug}, .../departement/{slug})
# ============================================================

class AgregatEtablissements(BaseModel):
    nb_etablissements: int
    taux_reussite_moyen: Optional[float] = None
    # Médiane du score_principal du périmètre, reclassée en lettre via
    # notation_seuils — cf. agent/tools/hierarchie_tool.py.
    notation_mediane: Optional[str] = None


class SousDivision(AgregatEtablissements):
    code: str
    libelle: str


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

    model_config = {"populate_by_name": True}


class DepartementHub(BaseModel):
    libelle_region: str
    code_departement: str
    libelle_departement: str
    session_utilisee: Optional[str] = None
    global_: AgregatEtablissements = Field(alias="global")
    communes: list[SousDivision]

    model_config = {"populate_by_name": True}
