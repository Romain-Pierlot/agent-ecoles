"""
dictionnaire_donnees.py — Source de vérité sémantique
Descriptions officielles des colonnes, issues du Guide méthodologique IVAC 2025 (DEPP)
et de l'annuaire de l'Éducation Nationale.

Ce fichier sert à deux choses :
1. Générer automatiquement le schéma documenté (docs/schema.md)
2. Alimenter le system prompt de l'agent — le LLM connaît la signification exacte de chaque colonne

Structure de chaque entrée :
- description : définition officielle complète
- source : origine de la définition
- synonymes : formulations alternatives qu'un utilisateur pourrait employer
- notes : points de vigilance importants pour l'interprétation
"""

DICTIONNAIRE = {

    # ================================================================
    # TABLE : etablissements
    # ================================================================

    "etablissements.uai": {
        "description": "Unité Administrative Immatriculée — identifiant unique officiel de chaque établissement scolaire en France. Format : 7 chiffres + 1 lettre (ex: 0750001A). Clé de jointure centrale entre toutes les tables.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["code établissement", "identifiant établissement", "numéro UAI"],
        "notes": "Permanent et stable — ne change pas si l'établissement déménage ou change de nom.",
    },

    "etablissements.nom": {
        "description": "Nom officiel de l'établissement tel qu'il apparaît dans le système d'information du ministère.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["nom du collège", "nom de l'école", "intitulé"],
        "notes": "Peut différer du nom d'usage local. Toujours en majuscules dans la source.",
    },

    "etablissements.type_etablissement": {
        "description": "Type d'établissement scolaire. Valeurs principales : Collège, Lycée Général et Technologique, Lycée Professionnel, Lycée Polyvalent.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["nature établissement", "type école"],
        "notes": "En V1, l'agent répond uniquement sur les Collèges. Les lycées sont stockés pour la V2.",
    },

    "etablissements.secteur": {
        "description": "Statut de l'établissement : Public ou Privé. Les établissements privés dans notre périmètre sont exclusivement sous contrat avec l'Éducation Nationale.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["statut", "public ou privé", "école publique", "école privée", "sous contrat"],
        "notes": "Les établissements privés hors contrat ne sont pas dans les données.",
    },

    "etablissements.adresse": {
        "description": "Adresse postale de l'établissement (rue et numéro).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["adresse", "rue"],
        "notes": None,
    },

    "etablissements.code_postal": {
        "description": "Code postal de la commune d'implantation.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["CP", "code postal"],
        "notes": None,
    },

    "etablissements.commune": {
        "description": "Nom de la commune d'implantation de l'établissement.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["ville", "commune", "localité"],
        "notes": None,
    },

    "etablissements.code_departement": {
        "description": "Code INSEE du département (ex: 75 pour Paris, 69 pour le Rhône, 13 pour les Bouches-du-Rhône).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["département", "code dept"],
        "notes": "Utilisé pour les filtres géographiques et les comparaisons départementales.",
    },

    "etablissements.libelle_departement": {
        "description": "Nom du département en clair (ex: Paris, Rhône, Bouches-du-Rhône).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["nom département", "département"],
        "notes": None,
    },

    "etablissements.code_academie": {
        "description": "Code numérique de l'académie de rattachement (ex: 01 pour Paris, 10 pour Île-de-France).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["académie", "code académie"],
        "notes": None,
    },

    "etablissements.libelle_academie": {
        "description": "Nom de l'académie en clair (ex: Paris, Lyon, Versailles, Créteil, Normandie).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["académie", "nom académie", "rectorat"],
        "notes": None,
    },

    "etablissements.libelle_region": {
        "description": "Nom de la région académique (ex: Île-de-France, Auvergne-Rhône-Alpes, Normandie).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["région", "nom région"],
        "notes": None,
    },

    "etablissements.latitude": {
        "description": "Coordonnée GPS latitude en degrés décimaux (système WGS84). Utilisée pour le calcul de distance lors des recherches géographiques par rayon.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": [],
        "notes": "Combinée à la longitude pour calculer la distance entre deux points via la formule haversine.",
    },

    "etablissements.longitude": {
        "description": "Coordonnée GPS longitude en degrés décimaux (système WGS84). Utilisée pour le calcul de distance lors des recherches géographiques par rayon.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": [],
        "notes": "Combinée à la latitude pour calculer la distance entre deux points via la formule haversine.",
    },

    "etablissements.telephone": {
        "description": "Numéro de téléphone officiel de l'établissement.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["tel", "téléphone", "contact"],
        "notes": None,
    },

    "etablissements.mail": {
        "description": "Adresse email officielle de l'établissement.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["email", "courriel", "contact"],
        "notes": None,
    },

    "etablissements.web": {
        "description": "URL du site web officiel de l'établissement.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["site web", "site internet", "URL"],
        "notes": None,
    },

    "etablissements.restauration": {
        "description": "Présence d'un service de restauration scolaire (cantine). Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["cantine", "restauration scolaire", "déjeuner"],
        "notes": None,
    },

    "etablissements.hebergement": {
        "description": "Présence d'un service d'hébergement (internat). Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["internat", "hébergement", "pensionnat"],
        "notes": None,
    },

    "etablissements.ulis": {
        "description": "Présence d'une Unité Localisée pour l'Inclusion Scolaire — dispositif d'accueil d'élèves en situation de handicap permettant une scolarisation en milieu ordinaire. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["ULIS", "handicap", "inclusion", "élèves handicapés"],
        "notes": None,
    },

    "etablissements.apprentissage": {
        "description": "Présence d'une filière d'apprentissage. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["apprentissage", "alternance"],
        "notes": None,
    },

    "etablissements.segpa": {
        "description": "Présence d'une Section d'Enseignement Général et Professionnel Adapté — dispositif destiné aux élèves en grande difficulté scolaire ne maîtrisant pas les compétences de base en fin de CM2. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["SEGPA", "section adaptée", "élèves en difficulté"],
        "notes": "Les élèves SEGPA passent un brevet professionnel, pas général. La VA n'est pas calculée pour cette série.",
    },

    "etablissements.section_arts": {
        "description": "Présence d'une section arts. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["arts", "section artistique"],
        "notes": None,
    },

    "etablissements.section_cinema": {
        "description": "Présence d'une section cinéma. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["cinéma", "section cinéma", "audiovisuel"],
        "notes": None,
    },

    "etablissements.section_theatre": {
        "description": "Présence d'une section théâtre. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["théâtre", "section théâtre", "art dramatique"],
        "notes": None,
    },

    "etablissements.section_sport": {
        "description": "Présence d'une section sportive. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["sport", "section sportive", "classe sport"],
        "notes": None,
    },

    "etablissements.section_internationale": {
        "description": "Présence d'une section internationale — enseignement renforcé en langue étrangère avec une partie des cours dans cette langue. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["section internationale", "classe internationale", "SI", "bilingue"],
        "notes": None,
    },

    "etablissements.section_europeenne": {
        "description": "Présence d'une section européenne — une discipline non linguistique est enseignée en langue étrangère. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["section européenne", "classe européenne", "DNL"],
        "notes": None,
    },

    "etablissements.voie_generale": {
        "description": "Présence d'une filière générale (lycée). Binaire : 1 = oui, 0 = non. NULL pour les collèges.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["bac général", "filière générale", "lycée général"],
        "notes": "Uniquement pertinent pour les lycées. Toujours 0 pour les collèges.",
    },

    "etablissements.voie_technologique": {
        "description": "Présence d'une filière technologique (lycée). Binaire : 1 = oui, 0 = non. NULL pour les collèges.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["bac technologique", "filière technologique", "STI2D", "STL"],
        "notes": "Uniquement pertinent pour les lycées.",
    },

    "etablissements.voie_professionnelle": {
        "description": "Présence d'une filière professionnelle (lycée). Binaire : 1 = oui, 0 = non. NULL pour les collèges.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["bac pro", "filière professionnelle", "lycée professionnel", "CAP", "BEP"],
        "notes": "Uniquement pertinent pour les lycées.",
    },

    "etablissements.lycee_agricole": {
        "description": "Établissement agricole sous tutelle du Ministère de l'Agriculture. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["lycée agricole", "MFR", "LEAP"],
        "notes": None,
    },

    "etablissements.lycee_militaire": {
        "description": "Lycée militaire. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["lycée militaire", "école militaire"],
        "notes": None,
    },

    "etablissements.lycee_des_metiers": {
        "description": "Label Lycée des Métiers — reconnaissance d'un lycée professionnel d'excellence dans un domaine de formation. Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["lycée des métiers", "label métiers"],
        "notes": None,
    },

    "etablissements.post_bac": {
        "description": "Présence de formations post-baccalauréat (BTS, CPGE, etc.). Binaire : 1 = oui, 0 = non.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["post-bac", "BTS", "CPGE", "classes préparatoires", "STS"],
        "notes": None,
    },

    "etablissements.appartenance_education_prioritaire": {
        "description": "Appartenance au dispositif d'éducation prioritaire. Valeurs : REP (Réseau d'Éducation Prioritaire), REP+ (REP renforcé), ou vide si hors dispositif.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["éducation prioritaire", "REP", "REP+", "ZEP", "zone prioritaire"],
        "notes": "Les établissements REP et REP+ accueillent des publics défavorisés — leur IPS est généralement bas. À prendre en compte dans l'interprétation de la VA.",
    },

    "etablissements.etat": {
        "description": "État de l'établissement. Valeur principale : OUVERT. Seuls les établissements ouverts sont chargés dans la base.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": [],
        "notes": "Filtré à l'ingestion — les établissements fermés sont exclus.",
    },

    "etablissements.fiche_onisep": {
        "description": "URL de la fiche établissement sur le site ONISEP (Office National d'Information Sur les Enseignements et les Professions).",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["fiche ONISEP", "lien ONISEP"],
        "notes": None,
    },

    "etablissements.date_ouverture": {
        "description": "Date d'ouverture officielle de l'établissement.",
        "source": "Annuaire Éducation Nationale",
        "synonymes": ["ouverture", "création"],
        "notes": "Utile pour identifier les établissements récents dont les données historiques sont incomplètes.",
    },

    # ================================================================
    # TABLE : ips
    # ================================================================

    "ips.uai": {
        "description": "Clé étrangère vers la table etablissements. Identifiant unique de l'établissement.",
        "source": "IPS DEPP",
        "synonymes": [],
        "notes": None,
    },

    "ips.annee_scolaire": {
        "description": "Année scolaire de mesure de l'IPS. Format : '2023-2024'. Correspond à l'année de rentrée scolaire.",
        "source": "IPS DEPP",
        "synonymes": ["année", "année scolaire", "rentrée"],
        "notes": "Voir table referentiel_temporel pour la correspondance avec les sessions IVAC. Ne pas comparer les IPS avant et après 2023-2024 — rupture de série méthodologique.",
    },

    "ips.ips_moyen": {
        "description": "Indice de Position Sociale moyen de l'établissement. Calculé comme la moyenne des IPS individuels de tous les élèves à partir des catégories socioprofessionnelles des parents. Échelle continue : environ 50 (très défavorisé) à 180 (très favorisé). La valeur 100 représente approximativement la moyenne nationale.",
        "source": "IPS DEPP — Thierry Rocher, 'Construction d'un Indice de position sociale des élèves', Education & formations n°90, avril 2016",
        "synonymes": ["IPS", "indice social", "milieu social", "profil social", "origine sociale", "niveau socioéconomique"],
        "notes": "L'IPS mesure le profil social des élèves, PAS la qualité pédagogique du collège. Un IPS élevé reflète un recrutement favorisé, pas un bon enseignement. Toujours croiser avec la valeur ajoutée pour évaluer l'action propre du collège.",
    },

    "ips.ecart_type_ips": {
        "description": "Écart-type des IPS individuels au sein de l'établissement. Mesure l'hétérogénéité sociale : plus il est élevé, plus les élèves viennent de milieux sociaux diversifiés.",
        "source": "IPS DEPP",
        "synonymes": ["mixité sociale", "hétérogénéité", "diversité sociale"],
        "notes": "Un écart-type élevé indique une bonne mixité sociale. Un écart-type faible indique une population homogène (soit très favorisée, soit très défavorisée).",
    },

    "ips.ips_national_public": {
        "description": "IPS moyen national pour les établissements publics. Référence de comparaison nationale pour le secteur public.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne nationale public", "référence nationale"],
        "notes": None,
    },

    "ips.ips_national_prive": {
        "description": "IPS moyen national pour les établissements privés sous contrat. Référence de comparaison nationale pour le secteur privé.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne nationale privé"],
        "notes": "Les établissements privés ont en moyenne un IPS significativement plus élevé que les publics.",
    },

    "ips.ips_national": {
        "description": "IPS moyen national tous secteurs confondus (public + privé).",
        "source": "IPS DEPP",
        "synonymes": ["moyenne nationale", "IPS national"],
        "notes": None,
    },

    "ips.ips_academique_public": {
        "description": "IPS moyen de l'académie pour les établissements publics. Permet de comparer l'établissement à son académie.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne académique public"],
        "notes": None,
    },

    "ips.ips_academique_prive": {
        "description": "IPS moyen de l'académie pour les établissements privés sous contrat.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne académique privé"],
        "notes": None,
    },

    "ips.ips_academique": {
        "description": "IPS moyen de l'académie tous secteurs confondus.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne académique", "IPS académie"],
        "notes": None,
    },

    "ips.ips_departemental_public": {
        "description": "IPS moyen du département pour les établissements publics.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne départementale public"],
        "notes": None,
    },

    "ips.ips_departemental_prive": {
        "description": "IPS moyen du département pour les établissements privés sous contrat.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne départementale privé"],
        "notes": None,
    },

    "ips.ips_departemental": {
        "description": "IPS moyen du département tous secteurs confondus.",
        "source": "IPS DEPP",
        "synonymes": ["moyenne départementale", "IPS département"],
        "notes": None,
    },

    # ================================================================
    # TABLE : ivac
    # ================================================================

    "ivac.uai": {
        "description": "Clé étrangère vers la table etablissements.",
        "source": "IVAC DEPP",
        "synonymes": [],
        "notes": None,
    },

    "ivac.session": {
        "description": "Année de la session du brevet (DNB). Format : '2023'. Correspond à l'année où les élèves de 3ème ont passé l'examen en juin.",
        "source": "IVAC DEPP",
        "synonymes": ["année brevet", "session brevet", "promotion"],
        "notes": "Voir table referentiel_temporel pour la correspondance avec les années scolaires IPS. Sessions disponibles : 2022, 2023, 2024, 2025.",
    },

    "ivac.brevet_nb_candidats_general": {
        "description": "Nombre de candidats présentés au brevet voie générale lors de cette session. Indicateur de taille de l'établissement et de fiabilité statistique des résultats.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["nombre de candidats", "effectif brevet", "élèves présentés"],
        "notes": "La valeur ajoutée n'est pas calculée (ND) si le nombre de candidats en série générale est inférieur à 40. En dessous de 20 candidats, aucun indicateur n'est publié.",
    },

    "ivac.brevet_taux_reussite_general": {
        "description": "Taux de réussite au brevet voie générale en pourcentage. Calculé en divisant le nombre de diplômés par le nombre de candidats présents. Le brevet est évalué sur 800 points (400 socle commun + 300 épreuves écrites + 100 oral). L'élève est reçu s'il cumule 400 points.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["taux de réussite", "taux de passage", "résultats brevet", "pourcentage reçus"],
        "notes": "Indicateur brut — ne tient pas compte du profil social des élèves. Toujours interpréter avec la valeur ajoutée pour évaluer la performance réelle du collège.",
    },

    "ivac.brevet_va_taux_reussite_general": {
        "description": "Valeur ajoutée du taux de réussite au brevet voie générale. Écart entre le taux de réussite observé et le taux attendu compte tenu du profil de chaque élève (âge, IPS, niveau scolaire à l'entrée en 6ème via évaluations exhaustives, sexe) et des caractéristiques de l'établissement. Une VA positive signifie que le collège obtient de meilleurs résultats que ce qu'on attendrait pour ce profil d'élèves. Une VA négative ne signifie pas que les élèves régressent — elle indique seulement que le collège est en dessous de la moyenne des établissements comparables.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["valeur ajoutée", "VA", "plus-value pédagogique", "apport du collège", "ce que le collège apporte"],
        "notes": "IMPORTANT : calculée UNIQUEMENT pour la série générale du brevet — pas pour la série professionnelle. Absente (NULL) si effectif insuffisant (<40 candidats en général, ou données manquantes >25%). Cette métrique est au cœur d'EduScope.",
    },

    "ivac.brevet_note_ecrit_general": {
        "description": "Note moyenne obtenue à l'épreuve écrite du brevet voie générale. Calculée sur 300 points (100 français, 100 mathématiques, 50 histoire-géographie, 50 sciences), ramenée sur 20 en divisant par 15. Notes avant majoration éventuelle par le jury.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["note moyenne", "moyenne au brevet", "résultats écrits", "note à l'écrit"],
        "notes": "Plus nuancé que le taux de réussite — mesure le niveau de performance académique, pas seulement le passage/échec. Un établissement peut avoir un bon taux de réussite mais une note moyenne basse (les élèves passent juste).",
    },

    "ivac.brevet_va_note_ecrit_general": {
        "description": "Valeur ajoutée de la note à l'écrit au brevet voie générale. Même principe que la VA du taux de réussite, appliqué à la note moyenne. Mesure si le collège obtient des notes plus élevées que ce qu'on attendrait pour son profil d'élèves.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["valeur ajoutée note", "VA note"],
        "notes": "IMPORTANT : calculée UNIQUEMENT pour la série générale — pas pour la série professionnelle. Absente (NULL) si effectif insuffisant.",
    },

    "ivac.brevet_nb_candidats_pro": {
        "description": "Nombre de candidats présentés au brevet voie professionnelle (série professionnelle du DNB, principalement élèves SEGPA).",
        "source": "IVAC DEPP",
        "synonymes": ["candidats pro", "candidats SEGPA", "brevet professionnel"],
        "notes": "Aucune valeur ajoutée n'est calculée pour la série professionnelle.",
    },

    "ivac.brevet_taux_reussite_pro": {
        "description": "Taux de réussite au brevet voie professionnelle en pourcentage.",
        "source": "IVAC DEPP",
        "synonymes": ["taux réussite pro", "résultats brevet pro", "résultats SEGPA"],
        "notes": "Aucune valeur ajoutée n'est calculée pour cette série.",
    },

    "ivac.brevet_note_ecrit_pro": {
        "description": "Note moyenne à l'écrit au brevet voie professionnelle.",
        "source": "IVAC DEPP",
        "synonymes": ["note écrit pro"],
        "notes": "Aucune valeur ajoutée n'est calculée pour cette série.",
    },

    "ivac.taux_acces_6eme_3eme": {
        "description": "Part d'élèves de sixième ayant poursuivi leur scolarité jusqu'en troisième dans l'établissement, quel que soit le nombre d'années nécessaires pour l'atteindre (redoublements comptabilisés). Calculé comme le produit des taux d'accès intermédiaires : 6ème→5ème × 5ème→4ème × 4ème→3ème. Les déménagements et changements d'établissement liés à une formation non disponible dans le collège d'origine ne pénalisent pas le collège.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["taux de rétention", "taux de fidélisation", "élèves qui restent", "garde ses élèves", "scolarité complète"],
        "notes": "Un taux faible peut indiquer un décrochage scolaire, des orientations précoces, ou simplement une carte scolaire attractive qui pousse les familles vers d'autres établissements. À interpréter avec le contexte local.",
    },

    "ivac.part_3eme_ordinaire": {
        "description": "Part des élèves présents en classe de troisième ordinaire sur le total des élèves inscrits en troisième ordinaire à la rentrée précédente. Mesure la capacité de l'établissement à présenter l'ensemble de ses élèves au brevet.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["présents au brevet", "élèves présentés", "3ème ordinaire"],
        "notes": "Hors ULIS et UPE2A (Unité Pédagogique pour Élèves Allophones Arrivants).",
    },

    "ivac.part_3eme_segpa": {
        "description": "Part des élèves présents en classe de troisième SEGPA sur le total des élèves inscrits en troisième SEGPA. Mesure la capacité de l'établissement à présenter ses élèves en grande difficulté au brevet professionnel.",
        "source": "IVAC DEPP — Guide méthodologique IVAC 2025",
        "synonymes": ["présents brevet SEGPA", "élèves SEGPA présentés"],
        "notes": None,
    },

    "ivac.nb_mentions_ab": {
        "description": "Nombre d'élèves ayant obtenu la mention Assez Bien au brevet (moyenne générale entre 12 et 14/20).",
        "source": "IVAC DEPP",
        "synonymes": ["mention AB", "assez bien"],
        "notes": "À rapporter au nombre total de candidats pour calculer un ratio.",
    },

    "ivac.nb_mentions_b": {
        "description": "Nombre d'élèves ayant obtenu la mention Bien au brevet (moyenne générale entre 14 et 16/20).",
        "source": "IVAC DEPP",
        "synonymes": ["mention B", "bien"],
        "notes": None,
    },

    "ivac.nb_mentions_tb": {
        "description": "Nombre d'élèves ayant obtenu la mention Très Bien au brevet (moyenne générale supérieure ou égale à 16/20). Indicateur de l'excellence académique au sein de l'établissement.",
        "source": "IVAC DEPP",
        "synonymes": ["mention TB", "très bien", "excellence", "meilleurs élèves"],
        "notes": "Le ratio nb_mentions_tb / brevet_nb_candidats_general permet de comparer l'excellence entre établissements.",
    },

    "ivac.nb_mentions_total": {
        "description": "Nombre total de mentions obtenues (AB + B + TB). Permet de calculer le taux de mentions global.",
        "source": "IVAC DEPP",
        "synonymes": ["total mentions", "mentions toutes confondues"],
        "notes": None,
    },

    # ================================================================
    # TABLE : scores
    # ================================================================

    "scores.score_principal": {
        "description": "Score EduScope sur 100. Calculé comme la somme pondérée du taux de réussite normalisé (60%) et de la note à l'écrit normalisée (40%). La normalisation min/max est appliquée par session pour ramener chaque métrique sur une échelle 0-100 par rapport aux établissements de la même session. Score absent (NULL) si taux_reussite ou note_ecrit manquants.",
        "source": "Calculé par EduScope",
        "synonymes": ["score", "classement", "performance", "note globale"],
        "notes": "IMPORTANT : ce score mesure la performance brute, pas la valeur ajoutée. Un score élevé peut refléter un bon recrutement plutôt qu'une bonne pédagogie. Toujours présenter le badge VA à côté du score.",
    },

    "scores.badge_va": {
        "description": "Badge qualitatif de valeur ajoutée. Valeurs : 'positif' (VA taux de réussite > +2 points), 'neutre' (dans l'intervalle -2 à +2), 'negatif' (VA taux de réussite < -2 points). NULL si la VA n'est pas disponible.",
        "source": "Calculé par EduScope",
        "synonymes": ["badge", "niveau valeur ajoutée", "apport pédagogique"],
        "notes": "Le badge est calculé depuis brevet_va_taux_reussite_general. Il est affiché séparément du score et ne modifie pas le classement.",
    },

    # ================================================================
    # TABLE : referentiel_temporel
    # ================================================================

    "referentiel_temporel.session_ivac": {
        "description": "Année de session du brevet. Valeurs : 2022, 2023, 2024, 2025.",
        "source": "Manuel EduScope",
        "synonymes": [],
        "notes": None,
    },

    "referentiel_temporel.annee_scolaire_ips": {
        "description": "Année scolaire IPS correspondant à la session IVAC. NULL pour la session 2022 (pas de données IPS disponibles à cette période).",
        "source": "Manuel EduScope",
        "synonymes": [],
        "notes": "Correspondances : session 2023 → 2023-2024 / session 2024 → 2024-2025 / session 2025 → 2025-2026.",
    },

    "referentiel_temporel.libelle_affichage": {
        "description": "Libellé affiché à l'utilisateur dans l'interface pour lever l'ambiguïté temporelle. Ex : 'Année 2023-2024'.",
        "source": "Manuel EduScope",
        "synonymes": [],
        "notes": "Utilisé par l'agent quand un utilisateur mentionne une année sans préciser s'il veut la session brevet ou l'année scolaire.",
    },
}

if __name__ == "__main__":
    print(f"Dictionnaire de données : {len(DICTIONNAIRE)} colonnes documentées")
    for cle, val in DICTIONNAIRE.items():
        print(f"\n{cle}")
        print(f"  → {val['description'][:80]}...")
