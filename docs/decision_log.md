# Journal de décisions — Agent Écoles

Document de traçabilité consolidé des décisions techniques, architecturales, fonctionnelles et méthodologiques du projet, fusionné à partir des journaux de 4 sessions de travail. Ordre chronologique. Les sections sont numérotées par session (S1, S2, S3, S4) pour garder la traçabilité d'origine.

---

# Phase 1 — Cadrage fonctionnel, architecture, données, premiers outils

## S1.1 — Cadrage fonctionnel du projet

**Décision** : Agent d'aide au choix de collège basé sur les données publiques IPS/IVAC du Ministère de l'Éducation Nationale.

**Pourquoi** : Sujet personnel, volume de recherche potentiel réel (comparable à EcoleScope.fr), complexité technique suffisante pour démontrer Text-to-SQL, RAG et architecture agentique sans cas d'usage business artificiel.

**Conséquence** : Nom provisoire `agent-ecoles`.

## S1.2 — Périmètre V1 limité aux collèges

**Décision** : V1 limitée aux collèges, lycées hors périmètre mais données stockées en base pour évolution future (table `etablissements` contient tous les types, filtre applicatif côté agent, pas à l'ingestion).

**Pourquoi** : Les indicateurs IVAL (lycées) diffèrent des IVAC (collèges) et nécessiteraient un schéma de scoring séparé.

## S1.3 — Méthodologie de scoring : résultats bruts pondérés, VA en badge séparé

**Options envisagées** : score basé uniquement sur la VA / score composite avec VA pondérée / résultats bruts + VA en badge contextuel.

**Décision** : Score = 60% taux de réussite + 40% note à l'écrit (résultats bruts). VA affichée en badge (`positif`/`neutre`/`négatif`) sans influencer le classement.

**Pourquoi** : Un score basé sur la VA seule produit des classements contre-intuitifs (un collège à 95% de réussite peut être moins bien classé qu'un collège à 85% si sa VA est meilleure) — principe retenu : le score doit rester monotone sur les résultats bruts.

**Rejeté** : Score 100% VA.

**Conséquence** : Implémenté dans `calculer_scores()` — normalisation min/max par session, seuils `VA_SEUIL_POSITIF`/`VA_SEUIL_NEGATIF` dans `config.py`.

## S1.4 — Secteur scolaire (carte scolaire) hors périmètre V1

**Décision** : Hors scope — mention systématique "vérifiez sur le site de votre mairie".

**Pourquoi** : Donnée non centralisée au niveau national, gérée commune par commune.

## S1.5 — Architecture hybride Workflow + Agent

**Décision** : Router LangGraph qui classifie chaque question. Questions à chemin prévisible → workflows codés. Questions complexes/combinées → agent ReAct.

**Pourquoi** : Un agent pur sur tout est plus lent, plus coûteux, moins fiable sur les cas simples. Un workflow pur ne gère pas les cas imprévus.

**Rejeté** : Agent pur sur 100% des questions — identifié comme un raccourci de facilité dégradant fiabilité, coût et latence.

**Conséquence** : Nécessite LangGraph (pas LangChain seul).

## S1.6 — LangGraph pour l'orchestration, LangChain pour les briques utilitaires

**Options envisagées** : from-scratch intégral / LangChain seul / LangGraph + LangChain.

**Décision** : LangGraph pour router/workflows/agent, LangChain pour connecteurs et mémoire.

**Pourquoi** : Standard marché pour les architectures hybrides workflow/agent. Position retenue : "primitives construites from-scratch pour comprendre, orchestration via le standard marché pour la maintenabilité."

**Conséquence** : Trajectoire — primitives d'abord (SQL/geo/RAG tools testés isolément), LangGraph ensuite.

## S1.7 — LangSmith pour le monitoring (pas Langfuse)

**Décision** : LangSmith.

**Pourquoi** : Intégration native LangGraph, configuration en 3 variables d'env, traces nœud par nœud, free tier suffisant (5000 traces/mois).

**Rejeté** : Langfuse — reste une alternative si auto-hébergement futur nécessaire (free tier plus généreux, 50k events/mois) mais moins intégré.

## S1.8 — FinOps : LangSmith (analyse fine) + Dashboard OpenAI (budget cap)

**Décision** : Les deux outils sont complémentaires — LangSmith n'a pas de plafond strict, OpenAI dashboard n'a pas d'analyse par composant.

**Conséquence** : Guardrail de sécurité (rate limiting IP) identifié mais non implémenté à ce stade.

## S1.9 — Hébergement : Streamlit Cloud (POC) → serveur personnel (production)

**Décision** : POC sur Streamlit Cloud gratuit. Production future sur serveur personnel avec nom de domaine (Docker Compose, Streamlit + ChromaDB server).

**Pourquoi** : Zéro coût/friction pour le POC, portabilité du code entre environnements, contrôle total en production.

**Conséquence** : Attention au filesystem éphémère de Streamlit Cloud — réingestion à chaque redéploiement.

## S1.10 — ChromaDB en mode local (pas Chroma Cloud)

**Décision** : Mode local (fichier persistant).

**Pourquoi** : Corpus très petit, très loin de la limite de robustesse du mode local.

**Conséquence** : Migration vers mode serveur Docker envisageable si concurrence d'utilisateurs simultanés.

## S1.11 — Contraintes non fonctionnelles cadrées

10-100 utilisateurs simultanés (POC), latence cible 5-6s (mitigée par streaming), coût minimal variable (GPT-4o-mini), disponibilité 24h/24 visée, zéro stockage d'adresse utilisateur, logs anonymisés avec zone géographique approximative.

## S1.12 — Schéma SQLite : 5 tables normalisées, pas de table par année

**Décision** : Tables uniques avec colonne temporelle (`annee_scolaire`, `session`). 5 tables : `etablissements`, `ips`, `ivac`, `scores`, `referentiel_temporel`.

**Pourquoi** : Une table par année complexifierait les jointures de tendance et la maintenance.

## S1.13 — Table `scores` matérialisée (calculée à l'ingestion)

**Pourquoi** : Évite de recalculer la normalisation min/max à chaque requête ; centralise la formule de scoring pour modification future facile.

## S1.14 — Table `referentiel_temporel` pour l'ambiguïté session IVAC / année scolaire IPS

**Problème** : Les deux référentiels temporels ne sont pas alignés terme à terme.

**Décision** : Table de correspondance à 4 lignes, `NULL` explicite pour la session 2022 (pas d'IPS cette année-là).

**Conséquence** : Prévu — choix par boutons dans l'interface si ambiguïté détectée. **Non implémenté.**

## S1.15 — Stockage exhaustif des colonnes (y compris lycées, toutes sections)

**Pourquoi** : Volumétrie très faible (~14 800 lignes), coût de stockage négligeable face au coût de migration de schéma plus tard.

## S1.16 — Suppression des établissements "Fermé" à l'ingestion

**Décision** : `df = df[df['etat'] == 'OUVERT']` plutôt qu'un filtre répété dans chaque requête SQL.

## S1.17 — Déduplication des UAI multi-sites (conservation du premier enregistrement)

**Décision** : `drop_duplicates(subset='uai', keep='first')`.

**Pourquoi** : Gestion fine multi-sites jugée hors scope V1.

## S1.18 — Renommage des colonnes IVAC : explicitation "général"/"professionnel"

**Problème** : Suffixes sources ambigus "G"/"P" (initialement mal interprétés comme Global/Privé).

**Décision** : Préfixe `brevet_`, suffixe explicite `_general`/`_pro`.

**Conséquence** : Convention à respecter pour toute colonne future (lycées notamment).

## S1.19 — Règle métier critique : la VA n'existe que pour la série générale du brevet

**Décision actée** : Aucune VA calculée pour la série professionnelle (élèves SEGPA notamment).

**Source** : Guide méthodologique IVAC 2025 (DEPP).

**Conséquence** : Information critique à intégrer au prompt système de l'agent. *(Confirmée et reprécisée en session 4.)*

## S1.20 — Dictionnaire de données centralisé (`data/dictionnaire_donnees.py`)

**Décision** : Fichier centralisant pour chaque colonne : description officielle, source, synonymes utilisateur, notes d'interprétation. Basé sur Dublin Core + champs custom RAG.

**Méthode de mise à jour** : enrichissement itératif manuel, pas d'automatisation sans validation humaine.

**Conséquence** : 74 colonnes documentées avant la V1.

## S1.21 — Licence GitHub différée, MIT par défaut envisagée

**Décision** : Pas de sujet bloquant. Repo public, MIT envisagée. La vraie protection réside dans la profondeur de compréhension du créateur et sa capacité à justifier chaque choix technique, pas dans la licence.

## S1.22 — Text-to-SQL : schéma enrichi + few-shot, pas de framework dédié

**Décision** : Prompt système avec schéma, règles métier, exemples few-shot. GPT-4o-mini, retry automatique avec réinjection de l'erreur SQLite.

**Conséquence validée** : 4/4 questions tests réussies en une tentative au premier test.

## S1.23 — Géolocalisation : API BAN + haversine custom

**Décision** : API BAN (gratuite, sans clé) + fonction haversine injectée dans SQLite via `create_function`. Pas de recherche de "communes voisines" — distance directe sur coordonnées GPS.

**Rejeté** : Google Maps (clé payante au-delà d'un seuil), Nominatim (limité à 1 appel/s).

**Rayon par défaut** : 10 km (`GEO_RAYON_DEFAUT_KM`).

**Point de vigilance** : l'API BAN retourne un point de référence approximatif pour un simple nom de ville (mairie/centre administratif), pas un centroïde — biais possible sur grandes villes. Mitigation prévue : afficher l'adresse normalisée, encourager une adresse précise.

## S1.24 — Limite de résultats affichés : pas de filtre automatique public/privé, pagination différée

**Décision** : Secteur toujours affiché, aucun filtre automatique sauf demande explicite (l'agent peut suggérer). Gestion du volume de résultats (pagination/"load more") reportée à la phase Streamlit.

## S1.25 — Pipeline RAG : abandon de pdfplumber pur, adoption d'Unstructured (`chunk_by_title`)

**Itérations testées** : chunking par taille de police fixe (échec, coupures en plein milieu de phrase) → accumulation de mots de titre + reconstruction d'ordinaux (échoue sur les pages 2 colonnes) → `extract_text()` simple (confirme l'entrelacement) → découpage par `crop()` de page (fonctionne mais demande un travail manuel lourd) → rasterisation + LLM vision (validée provisoirement) → **Unstructured identifié comme standard industrie** (`chunk_by_title`, gère colonnes/titres/tableaux nativement).

**Décision finale** : Unstructured (`unstructured[pdf]`) avec `chunk_by_title`.

**Rejeté** : pdfplumber maison (trop fragile, ne scale pas) ; rasterisation systématique + LLM vision (pas la pratique standard pour ce niveau de complexité).

**Statut fin S1** : Installation bloquée par incompatibilité `pi-heif`/Python 3.9.

## S1.26 — Migration Python 3.9 → 3.11

**Décision** : Migration complète (recréation du venv) plutôt que contournement ponctuel (épinglage de version `pi-heif`).

**Pourquoi** : Le contournement ne résout que le symptôme ; LangGraph/LangChain recommandent déjà Python 3.11+.

**Statut fin S1** : Non exécutée, reportée à la session suivante.

## S1.27 — Décision de méthode : changement de conversation après accumulation d'erreurs non validées

**Problème** : Plusieurs décisions techniques d'affilée prises/exécutées sans présentation préalable d'options, rompant le contrat méthodologique du projet (conception avant code, validation à chaque étape).

**Décision** : Clôture de la session, document de transition rédigé, reprise en nouvelle conversation (même projet Claude).

**Pourquoi** : Perte de confiance explicitement constatée par l'utilisateur, mécanisme connu de dégradation du jugement sur longues conversations.

---

# Phase 2 — Pipeline RAG, chunking, golden dataset (amorce), outils

## S2.1 — Migration Python 3.9 → 3.11 (exécutée)

**Conséquence** : `pi-heif-1.4.0` installé sans erreur, `partition_pdf`/`chunk_by_title` opérationnels. *(Clôture de la dette S1.26.)*

## S2.2 — Unstructured + `chunk_by_title` (confirmé)

**Décision** : Classification automatique des éléments (Title, NarrativeText, Footer...) puis regroupement par titre.

**Rejeté** : pdfplumber par taille de police — non scalable.

**Conséquence** : Réécriture complète d'`ingest_rag.py`.

## S2.3 — Paramètres de chunking validés

```python
max_characters = 1500
new_after_n_chars = 1000
combine_text_under_n_chars = 500
```

Appliqués de façon constante v3 à v6.

## S2.4 — Stratégie d'exclusion de pages : numéro de page + filtrage résiduel par règles

**Décision** : Combiner exclusion par numéro de page (structurelle, prévisible) et exclusion par mots-clés/regex (artefacts résiduels).

**Conséquence** : `pages_exclure` par source + `KEYWORDS_EXCLUSION` + règles de filtrage dans `extraire_chunks`.

## S2.5 — Exclusion des exemples chiffrés fictifs du RAG

**Problème** : Risque de confusion entre exemples pédagogiques inventés (ex. "Cas d'un collège", taux fictif 89%) et vraies données d'établissement.

**Décision** : Exclusion systématique (page 7 Guide IVAC, section "Calcul pratique" page 10).

## S2.6 — Exclusion des tableaux de valeurs IPS par PCS (annexes, doublons SQLite)

**Décision** : Exclues du RAG — ces données vivent uniquement dans SQLite, pas de duplication.

## S2.7 — Pattern "chunks manuels" pour les pages non parsables automatiquement

**Options envisagées** : filtrage automatique des chunks mal formés (perte d'info) / mode `hi_res` Detectron2 (dépendances lourdes) / extraction et rédaction manuelle.

**Décision** : Chunks manuels — pages exclues du parsing Unstructured, texte extrait manuellement, structure éditoriale respectée, notes de bas de page intégrées au point d'appel avec préfixe "Note :".

**Conséquence** : Pattern réutilisé pour Note d'information IPS 23.16 (pages 1-4) et Guide IVAC 2025 (pages 9-11). 17 chunks manuels en v5, 23 en v6.

## S2.8 — Changement de niveau d'ambition : de POC à produit visant la qualité réelle

**Décision** : Abandon de la posture POC après constat qu'un concurrent (données similaires) a un trafic réel et une monétisation.

**Conséquence** : Justifie le travail minutieux de correction des chunks, du golden dataset détaillé, refus des simplifications hâtives pour le reste du projet.

## S2.9 — Métadonnées Dublin Core sur chaque chunk

**Décision** : `dc_title`, `dc_creator`, `dc_publisher`, `dc_date`, `dc_type`, `dc_source` + champs navigation `chunk_domaine`, `chunk_page`, `chunk_titre_section`.

**Conséquence** : Permet la citation précise de page dans les futures réponses de l'agent.

## S2.10 — Filtrage qualité en cascade des chunks (8 règles)

**Décision** : 8 filtres empilés (footers, mots-clés, fragments tronqués en début de chunk, artefacts d'espacement, artefacts d'encodage `(cid:`, chunks <100 caractères, ratio alphabétique <60%, mots collés/fragmentation multi-colonnes).

**Conséquence** : Réduction progressive (34 → 26 → 19 → 17 → 11 sur le Guide IVAC seul) à chaque itération, qualité croissante validée manuellement.

## S2.11 — Distinction contenu méthodologique vs contenu dangereux

**Décision** : Contenu de référence (définitions, formules, méthodologie) gardé ; exemples chiffrés fictifs, légendes/graphiques exclus. Les PDFs DEPP servent exclusivement à la méthodologie, jamais aux données chiffrées réelles (rôle de SQLite).

## S2.12 — Champ `dc_niveau` (avancé/accessible) pour le metadata filtering

**Problème** : Risque de mismatch de granularité — question simple remontant des chunks trop techniques.

**Décision** : Ingestion de sources web officielles complémentaires (data.education.gouv.fr, education.gouv.fr/depp), champ `dc_niveau` ("avancé" PDFs techniques, "accessible" — renommé depuis "vulgarisation"/"vulgaire" jugé maladroit).

**Conséquence** : Nouveaux chunks manuels `ivac_accessible_xxx`/`ips_accessible_xxx` **prévus**. Filtrage par niveau prévu dans le futur prompt système du router. **Correction de nommage "vulgaire" → "accessible" identifiée comme dette technique.** *(Toujours non traitée en session 4 — confirmé par `grep` : 6 occurrences de "vulgaire" dans `ingest_rag.py`.)*

## S2.13 — Chunks de précautions d'usage (IPS et IVAC)

**Problème** : Risque de surinterprétation (écarts d'IPS, VA négative = "élèves qui régressent", IVAC perçus comme classement officiel).

**Décision** : Chunks manuels dédiés — "ne constituent pas un classement officiel" (IVAC), "pas une mesure directe de revenu/diplôme", "ne pas surinterpréter des écarts de 3 points" (IPS).

**Conséquence** : Intégrés en v6 (`ivac_vulgaire_002`/`ips_vulgaire_002`, à renommer).

## S2.14 — Position sur la question des classements de collèges

**Décision (actée, implémentation reportée)** : L'agent peut proposer un classement multi-critères si demandé, mais doit systématiquement nuancer : pas un classement officiel, sélection possible à l'entrée dans le privé.

**Conséquence** : À formaliser dans le prompt système du router. *(Toujours non rédigé en session 4.)*

## S2.15 — Architecture de raisonnement : agent LangGraph à décision dynamique

**Options envisagées** : un seul outil par question / séquence fixe SQL puis RAG / agent à décision dynamique.

**Décision** : Agent à décision dynamique, appelant les outils nécessaires dans l'ordre jugé pertinent.

**Rejeté** : Les deux alternatives plus simples — dégradent la qualité de service pour ce cas d'usage.

**Conséquence** : Prompt système riche nécessaire pour le router (contexte métier, description des outils, règles de décision et de cohérence inter-outils, format de réponse) — identifié comme pièce centrale, reporté.

## S2.16 — `rag_tool` retourne des données brutes, pas une réponse formatée

**Décision** : `rag_tool` ne formate jamais de réponse finale — retourne chunks + scores + métadonnées Dublin Core, interprétés et synthétisés par le router.

```python
{
  "success": bool, "query": str,
  "chunks": [{"contenu": str, "score": float, "source": str, "page": str,
              "section": str, "domaine": str, "url": str, "auteur": str, "date": str}]
}
```

## S2.17 — Seuil de pertinence `SIMILARITY_THRESHOLD` dans `rag_tool`

**Décision** : Seuil initial 0.70 (heuristique), à calibrer empiriquement via le harness.

**Conséquence** : Guardrail minimal — complété par la correction du score (S2.22) et noté comme insuffisant seul (S2.23).

## S2.18 — Stratégie d'évaluation par blocs indépendants avant assemblage

**Décision** : Bloc 1 `rag_tool` (recall, MRR, precision) → Bloc 2 `sql_tool` → Bloc 3 `geo_tool` → Bloc 4 assemblage LangGraph.

**Conséquence** : `rag_tool` devient le chantier prioritaire immédiat.

## S2.19 — Gestion des incohérences inter-outils : régénération partielle ciblée

**Options envisagées** : régénération complète / régénération partielle ciblée / garde-fou en sortie uniquement.

**Décision** : Régénération partielle ciblée, jugée possible car les outils sont peu nombreux, indépendants, sorties vérifiables séparément.

**Conséquence** : Nécessite un niveau de vérification propre à chaque outil. Logique de régénération elle-même reportée à l'assemblage LangGraph (Bloc 4) — **non codée à ce stade.**

## S2.20 — Format du golden dataset RAG

**Décision** : `id, question, reformulations, reponse_reference, chunks_attendus, position_minimale, type, domaine, difficulte, notes`. `reponse_attendue`/`reponse_complete` fusionnés en `reponse_reference`. `validee_par` écarté (projet solo). `chunks_attendus` par ordre de priorité décroissante (sert au MRR). Champ `chunks_obligatoires` envisagé puis explicitement reporté ("on ne résout pas des problèmes qu'on n'a pas encore observés").

## S2.21 — Réponses de référence courtes et minimalistes

**Décision** : Ne contenir que les éléments strictement indispensables — pas de contexte/nuance non essentielle, sous peine de pénaliser à tort des réponses correctes mais moins exhaustives.

## S2.22 — Correction d'un bug critique du calcul du score de similarité

**Problème** : Tous les scores anormalement bas (~0.51) quelle que soit la requête.

**Diagnostic** : Formule `score = 1 - (distance/2)` calibrée pour des distances cosinus dans [0,2], alors que `text-embedding-3-small` produit des vecteurs normalisés (distance dans [0,1]).

**Décision** : `score = round(1 - distance, 4)`, seuil abaissé de 0.70 à 0.50.

**Conséquence** : Bug corrigé **avant** la construction du golden dataset — sinon toutes les métriques de retrieval auraient été faussées.

## S2.23 — Le guardrail hors-domaine doit être une pièce dédiée, pas un patch dans `rag_tool`

**Décision** : Pas de filtre de mots-clés bricolé dans `rag_tool`. Le seuil de similarité reste une protection minimale ; la vraie protection viendra d'un guardrail dédié (après assemblage LangGraph, avant déploiement).

**Conséquence** : `rag_tool` reste volontairement un retrieval pur. **Guardrail dédié non construit à ce stade.**

## S2.24 — Méthode de génération du golden dataset : approche "chunk-driven" automatisée

**Options envisagées** : construction manuelle question par question / génération automatique par LLM à partir des chunks d'une thématique.

**Décision** : Approche chunk-driven avec validation humaine allégée a posteriori. Trois passes : 1 (mono-thématique par `chunk_domaine`), 2 (cross-thématique), 3 (hors-domaine, rédigée manuellement).

**Rejeté** : Construction 100% manuelle — non scalable, non représentative des pratiques réelles de production.

**Conséquence** : Cible ~35 questions (5 thématiques × ~4 en passe 1, ~8-10 en passe 2, ~4-5 en passe 3). Premier script de génération écrit, **non encore exécuté avec succès à la fin de S2.**

---

# Phase 3 — Golden dataset, audit qualité, sources, méthode de travail

## S3.D1 — Report de la correction des IDs de chunks (`vulgaire` → `accessible`)

**Décision** : Reporter la correction après génération complète des 35 questions, pour ne faire qu'une seule réingestion.

**Pourquoi** : Éviter une interruption au milieu de la construction du dataset.

*(Toujours non traitée en session 4.)*

## S3.D2 — Suppression d'une question hors registre parent

**Décision** : Suppression de "Quelles conditions doivent être remplies pour publier les résultats des IVAC ?" — trop procédurale, aucun parent ne la formule en pratique.

**Conséquence** : A motivé une reformulation du prompt de génération (S3.D9) pour éviter ce type de question par défaut.

## S3.D3 — Audit qualité systématique des chunks (`audit_chunks.py`)

**Contexte** : découverte d'un chunk tronqué (`ivac_2025_003`) et d'un chunk mélangeant deux sections (`ivac_2025_004`).

**Décision** : Script d'audit détectant chunks trop courts, trop longs, multi-sections, avec artefacts de parsing, ou ne finissant pas par une ponctuation.

**Pourquoi** : Sans audit, le harness mesurerait des performances faussées sans distinguer problème de retrieval vs problème de données.

**Conséquence** : 1 chunk critique (`ips_2016_000`, page de titre) + 42 chunks en "attention" (essentiellement faux positifs, cf. S3.D4).

## S3.D4 — Faux positif identifié : tirets de césure typographique

**Investigation** : caractères suspects = tirets de césure en fin de ligne (`com-\nparaison`), normaux dans un PDF, sans impact réel.

**Décision** : Qualifié comme faux positif, pas un problème de fond.

**Conséquence** : Nettoyage (`re.sub(r'-\n', '', texte)`) classé en dette technique. *(Toujours non traité en session 4.)*

## S3.D5 — Correction de la page 4 du Guide IVAC 2025 (chunk manuel)

**Problème** : Page à 2 colonnes mal parsée — `ivac_2025_003` tronqué, `ivac_2025_004` mélange deux sections, aucun chunk avec la liste complète des 4 indicateurs.

**Options envisagées** : source web externe (catalogue DEPP, écartée — contradiction interne détectée "deux" vs "quatre" indicateurs) / ne rien changer / chunk manuel de synthèse.

**Décision** : Chunk manuel `ivac_2025_manual_page4`, reconstruit depuis le contenu réel de la page.

**Conséquence** : Page 4 ajoutée à `pages_exclure`.

## S3.D6 — Principe de validation : pas de chunk manuel sans vérification croisée

**Problème soulevé par l'utilisateur** : risque qu'un chunk manuel devienne un moyen de fabriquer du contenu sans ancrage réel ("on pourrait créer les chunks qui nous arrangent").

**Décision** : Accepter un chunk manuel seulement après vérification explicite, via ChromaDB, que le contenu source couvre bien chaque affirmation.

**Conséquence** : Principe réappliqué de façon répétée (S3.D10) — toute réponse de référence du golden dataset doit être vérifiée comme inférable des chunks attendus avant validation. *(Principe directement réutilisé en session 4 lors de la lecture des chunks avant génération des questions.)*

## S3.D7 — Réécriture complète de `ingest_rag.py` en v7

**Problème** : Corrections incrémentales (sed, édition manuelle) ont rendu le fichier incohérent — doublons dans `CHUNKS_ARTEFACTS`, exclusions non appliquées, nombre de chunks fluctuant de façon erratique (76→74→71→70).

**Décision** : Réécriture complète plutôt que correctifs successifs.

## S3.D10 — Règle de vérification systématique des réponses de référence

**Décision** : Avant de valider une `reponse_reference`, vérifier explicitement (relecture du contenu brut) que chaque affirmation est présente ou raisonnablement inférable des chunks attendus.

**Pourquoi** : Distinction entre rôle du golden dataset pour le retrieval (les chunks doivent remonter) et pour la faithfulness (la réponse doit être strictement ancrée) — une réponse trop construite produirait des faux négatifs de faithfulness sur un RAG par ailleurs correct.

## S3.D11 — Concept de "knowledge gap" comme limite structurelle du RAG

**Décision (de compréhension)** : Un expert métier peut détenir des nuances non formalisées dans aucun document ingéré — un RAG ne peut structurellement pas restituer une information absente de sa base. Seule solution robuste : formaliser la connaissance experte en document source citable avant ingestion, jamais en dur dans le prompt système sans source.

*(Principe directement réinvoqué et opérationnalisé en session 4 sur le positionnement éditorial.)*

## S3.D12 — Suppression de questions doublons

**Décision** : Conserver une seule formulation entre deux questions testant le même angle avec les mêmes chunks attendus.

**Conséquence** : Golden dataset IVAC stabilisé à 4 questions validées (registre simple/accessible).

## S3.D13 — Un seul fichier centralisé pour le golden dataset

**Décision** : `rag/golden_dataset.json` unique, enrichi au fil des sessions, plutôt qu'un fichier par thématique.

**Pourquoi** : Facilite l'exécution du harness sur l'ensemble du dataset.

## S3.D14 — Réécriture complète de `ingest_rag.py` en v8

**Problème** : Une tentative d'insertion via script intermédiaire a échoué silencieusement (bloc inséré hors de la liste `CHUNKS_MANUELS`).

**Décision** : Abandon des correctifs successifs, réécriture complète et unique.

**Pourquoi** : L'accumulation de patches sur un fichier Python à indentation significative est une source d'erreurs récurrente et difficile à déboguer à distance.

**Conséquence** : 79 chunks stables, chunk Cour des comptes vérifié en première position sur sa requête de test. **Décision de méthode actée : privilégier la réécriture complète plutôt que les correctifs incrémentaux** dès que plusieurs modifications sont nécessaires sur un fichier généré par Claude. *(Principe directement appliqué en session 4 pour les modifications de `harness.py`.)*

## S3.D15 — Report du refactoring `CHUNKS_MANUELS` → JSON externe

**Décision** : Reporté au démarrage du router LangGraph (étape 8 de la roadmap).

**Pourquoi** : Structure encore instable, le harness RAG (prochaine étape) interroge directement ChromaDB et n'est pas affecté par l'organisation interne du script d'ingestion.

*(Cohérent — non traité en session 4 mais le router n'a pas encore démarré, donc pas un écart.)*

## S3.D16 — Maintien du chat comme outil principal (pas de bascule vers Claude Code)

**Décision** : Rester sur le chat, conception et code entremêlés.

**Pourquoi** : Le goulot d'étranglement identifié est la perte de contexte entre sessions, pas la friction des allers-retours terminal (jugée utile pour voir les résultats et apprendre) — Claude Code ne résout pas davantage ce problème.

*(Révisé en session 7 — cf. S7.6, bascule effectuée avec cadrage explicite via CLAUDE.md.)*

---

# Phase 4 — Harness RAG, corrections golden dataset, re-ranker, positionnement éditorial

## S4.D1 — Correction définitive du chemin ChromaDB (chemins absolus)

**Problème** : Collection introuvable de façon répétée — trois bases ChromaDB coexistaient (`rag/chroma_db`, `chroma_db` racine, `data/chroma`), créées par des versions différentes de `config.py` avec un chemin relatif.

**Décision** : `CHROMA_PATH`/`DB_PATH` construits dynamiquement en chemin absolu, ancrés sur l'emplacement de `config.py`. Suppression des deux bases orphelines.

**Conséquence** : Problème éliminé à la racine, plus de contournement ponctuel.

## S4.D2 — Lecture intégrale des chunks avant génération de questions (réaffirmation S3.D6)

**Décision** : Afficher et lire les 7 chunks de la Passe 1b avant toute rédaction de question.

## S4.D3 — Sélection des angles pour la Passe 1b IVAC avancé

**Décision** : 2 questions retenues — taux de réussite attendu (GD_RAG_005), taux d'accès / cohorte fictive (GD_RAG_006). Question sur la part d'élèves présents au DNB écartée — source insuffisante pour expliquer le "pourquoi" (dette documentaire actée).

## S4.D4 — Recalibrage : question hybride SQL+RAG reportée en Passe 2

**Décision** : La question "85% de réussite, est-ce bien ?" nécessite à la fois comparaison chiffrée (SQL) et interprétation VA (RAG) — reportée en Passe 2 avec flag explicite, pas mélangée à la Passe 1b RAG pur.

## S4.D5 — Calibration de la difficulté : "moyen" plutôt que "facile"

**Décision** : GD_RAG_005 et GD_RAG_006 classées "moyen" malgré peu de chunks attendus.

**Pourquoi** : La difficulté ne se mesure pas qu'au nombre de chunks à croiser, mais aussi à l'écart entre vocabulaire naturel de la question et vocabulaire technique des chunks.

## S4.D6 — Correction de deux erreurs de golden dataset identifiées via le harness

**Problème A (GD_RAG_004)** : chunk attendu `ivac_vulgaire_002` hors sujet par rapport à la question — Recall structurellement bloqué.

**Problème B (GD_RAG_001)** : chunks attendus `ivac_vulgaire_001` et `ivac_2025_manual_page4` répondant à des questions différentes (comment calcule-t-on / quels indicateurs), pas à la question de définition posée.

**Décision** : Corriger les `chunks_attendus`, ne pas reformuler les questions pour les faire coller au retrieval existant.

**Principe explicite validé** : l'objectif du golden dataset est de refléter fidèlement les vraies questions des parents et la vraie capacité du système — pas de maximiser une statistique.

**Conséquence** : Recall@3 global 0.53 → 0.64 par seule correction des données de test.

## S4.D7 — Gap structurel identifié : absence de source sur "VA → progression réelle"

**Problème** : Les textes DEPP ne parlent jamais de "progression" — seulement de performance relative au profil. GD_RAG_004 ne peut recevoir de réponse strictement sourcée avec le corpus actuel.

**Décision** : Garder la question, documenter la limite, chercher une source tierce (OCDE, recherche en sciences de l'éducation, Haut Conseil de l'Évaluation de l'École).

## S4.D8 — Positionnement éditorial : interprétation assumée, sourçage rigoureux obligatoire

**Décision** : Le produit assume une dimension interprétative (au-delà du factuel pur) à condition de toujours sourcer sur des sources tierces fiables et reconnues — jamais d'interprétation non sourcée dans le prompt système.

**Pourquoi** : Cohérent avec ce qui était déjà fait implicitement (chunk Cour des comptes, session 3) ; opérationnalise le concept de knowledge gap (S3.D11).

**Conséquence actée pour plus tard** : politique éditoriale à rédiger, champ `dc_type_source` à ajouter au schéma Dublin Core, règle de citation systématique dans le prompt système du router.

## S4.D9 — Harness RAG construit from-scratch (pas RAGAS)

**Décision** : Implémentation manuelle prioritaire pour garantir une compréhension complète du mécanisme d'évaluation. RAGAS prévu en complément/comparaison, non encore fait.

## S4.D10 — Métriques retrieval retenues : Recall@K, Precision@K, MRR

**Décision finale** (après un long processus de clarification conceptuelle marqué par plusieurs erreurs corrigées, cf. S4.D16) : Recall@K (oublis), Precision@K (bruit), MRR (qualité du ranking). Precision@expected envisagée puis écartée — redondante avec Recall dans une configuration à golden dataset explicite.

**Règle méthodologique** : tester plusieurs K (3, 5, 10) en phase de diagnostic pour distinguer problème de ranking (Recall s'améliore avec K plus grand) vs problème d'embedding/chunking (Recall reste bas même à K élevé) — mais le K de mesure en production doit rester celui réellement envoyé au LLM.

## S4.D11 — Métriques génération retenues : Faithfulness, Answer Relevance, Answer Correctness

**Décision** : Trois métriques LLM-as-a-judge, trois appels séparés (pas un appel combiné) pour fiabilité et lisibilité — surcoût négligeable à l'échelle actuelle. BLEU/ROUGE écartés (obsolètes pour langage naturel). Détection d'hallucination séparée écartée pour l'instant — réservée aux cas à enjeux élevés (médical/juridique/finance), pas le profil actuel du produit.

## S4.D12 — Architecture de versioning des résultats du harness

**Décision** : 3 fichiers — détail horodaté par run, copie `latest`, historique synthétique cumulatif (`resultats_harness_history.json`).

**Pourquoi** : Principe de versioning des expériences (MLOps) — comparer les configurations dans le temps sans dérive non détectée. Le harness lit dynamiquement le golden dataset à chaque run (couplage faible).

## S4.D13 — Premier run et diagnostic question par question

**Résultat** : Recall@3 = 0.53, Precision@3 = 0.39, mais Faithfulness/Answer Relevance/Answer Correctness déjà bons (0.88-1.0).

**Diagnostic affiné** : 2 questions parfaites, 2 questions avec problème de ranking réel (chunks présents mais tardifs), 2 questions initialement classées "problème d'embedding profond" — diagnostic révisé après inspection : c'étaient en réalité des erreurs de golden dataset (S4.D6), pas des limites du retriever.

## S4.D14 — Test du re-ranker : conception modulaire, deux modèles, décision de non-activation

**Décision de conception** : `reranker.py` en module séparé et réutilisable, interface stable, provider configurable (`local`/`cohere`) via `config.py`.

**Test 1** (`ms-marco-MiniLM-L-6-v2`, anglophone) : dégrade toutes les métriques retrieval.

**Test 2** (`mmarco-mMiniLMv2-L12-H384-v1`, multilingue) : dégrade toujours, mais écart plus faible.

**Décision finale** : Re-ranker non activé en production — sur un corpus de 79 chunks avec embeddings déjà bien différenciés, il n'apporte pas de valeur (conçu pour des corpus à plus grande échelle). Code conservé, configurable, désactivé par défaut (`TESTER_RERANKER = False`).

**Note sécurité** : `jina-reranker-v2-base-multilingual` identifié comme alternative plus performante mais nécessitant `trust_remote_code=True` (exécution de code distant) — évité tant qu'une alternative standard suffit.

## S4.D15 — Ajustement de K_PRODUCTION : 3 → 5

**Comparatif** : K=3 → Recall 0.64/Precision 0.50. K=5 → Recall 0.78/Precision 0.37, génération stable.

**Décision** : `RAG_TOP_K = 5` en production. Gain de Recall significatif sans dégradation observable de la génération.

**Conséquence** : Bug d'affichage corrigé au passage (le comparatif du harness restait codé en dur sur K=3).

## S4.D16 — Méthode pédagogique : correction explicite sur des erreurs d'explication

**Contexte** : Plusieurs erreurs et contradictions de l'assistant sur Precision@K vs Recall@K et Faithfulness vs Hallucination, repérées et challengées par l'utilisateur, arbitrées en partie via une source externe.

**Décision de méthode actée** : Partir systématiquement de la définition canonique avant simplification pédagogique, plutôt que d'improviser et de défendre une explication en cas de challenge.

## S4.D17 — Audit croisé des dettes techniques : confirmation de l'écart sur le renommage

**Décision** : Avant de fusionner les 4 journaux de décisions, vérifier objectivement (via `grep`) plutôt que de supposer si les dettes techniques listées étaient réellement traitées ou seulement reportées.

**Résultat** : Confirmé — le renommage `vulgarisation`/`vulgaire` → `accessible` (identifié S2.12, reporté S3.D1) n'avait toujours pas été traité avant cette vérification. Les autres dettes listées sont des reports cohérents (dépendant d'étapes non encore démarrées comme le router), pas des oublis.

**Conséquence** : Décision de traiter cet écart dans la foulée plutôt que de le reporter une quatrième fois.

## S4.D18 — Refactoring CHUNKS_MANUELS : code Python → JSON externe

**Décision** : Sortir les 25 chunks manuels de `ingest_rag.py` (liste de dictionnaires en dur, avec appels à `chunk_meta()`) vers `rag/chunks_manuels.json`, généré une fois par exécution du module puis figé. `ingest_rag.py` lit désormais ce JSON au lieu de contenir les données.

**Pourquoi** : Ajouter une source ne nécessitait jusqu'ici que d'éditer du code Python à indentation significative — source d'erreurs récurrente (cf. S3.D7, S3.D14, réécritures complètes en v7 et v8). Séparer données et code, même principe que ce qui a été appliqué à `config.py` et au golden dataset.

**Incident en cours de route** : suppression initiale trop large des constantes `META_*` — `META_IVAC` et `META_NI` étaient aussi utilisées par le pipeline d'ingestion Unstructured (variable `SOURCES`), pas uniquement par les chunks manuels. Erreur reconnue explicitement, corrigée en réintégrant ces deux métadonnées inline dans `SOURCES`.

**Conséquence** : Constantes `META_*` et fonction `chunk_meta()` supprimées. Validé par ré-ingestion identique (79 chunks, mêmes résultats de test) et harness stable (Recall@5=0.78, Precision@K5=0.37, MRR=0.64).

## S4.D19 — Renommage `vulgarisation` → `accessible` (clôture de la dette S2.12/S3.D1)

**Décision** : Exécuter le renommage en étape strictement séparée du refactoring JSON, pour isoler les risques de débogage — une opération mécanique réversible ne doit pas être mélangée à une opération qui change des identifiants référencés ailleurs.

**Périmètre** : 6 chunks renommés (`ivac_vulgaire_000-002` → `ivac_accessible_000-002`, `ips_vulgaire_000-002` → `ips_accessible_000-002`) dans `chunks_manuels.json` ; 8 références mises à jour dans `golden_dataset.json` (`chunks_attendus` + 2 mentions en texte libre dans des champs `notes`) ; 1 ligne de log dans `ingest_rag.py`.

**Conséquence** : Validé par ré-ingestion identique (79 chunks, étiquettes `[accessible]` au lieu de `[vulgarisation]`) et harness stable. Dette technique la plus ancienne du projet (identifiée S2.12, reportée S3.D1) close après trois sessions.

## S4.D20 — Tri des scripts non versionnés : suppression des artefacts morts, correction d'`audit_chunks.py`

**Contexte** : 4 fichiers untracked découverts au moment du commit (`agent/tools/rag_tool.py`, `audit_chunks.py`, `fix_chunk_ccomptes.py`, `insert_chunk_ccomptes.py`), sans certitude sur leur statut (vivant/mort) faute de traçabilité inter-session.

**Décision méthodologique** : inspecter le contenu de chaque fichier avant de décider, plutôt que de supposer à partir du nom ou de la date.

**Verdicts** :
- `rag_tool.py` — fonctionnel, correspond à l'architecture décrite en S2.16/17/22 (chunks bruts + scores + métadonnées Dublin Core). Conservé, mais corrigé pour éliminer le hardcoding (`DEFAULT_N_RESULTS=3`, `SIMILARITY_THRESHOLD=0.50` codés en dur) au profit d'imports depuis `config.py` (nouvelle constante `SIMILARITY_THRESHOLD` ajoutée à `config.py`). Validé par test direct.
- `fix_chunk_ccomptes.py` et `insert_chunk_ccomptes.py` — scripts de débogage ponctuels d'un bug déjà résolu autrement (réécriture complète v8, cf. S3.D14), opérant sur une structure de `ingest_rag.py` qui n'existe plus depuis le refactoring JSON. **Supprimés.**
- `audit_chunks.py` — outil fonctionnel et réutilisable (cf. S3.D3), mais avec le même défaut de chemin relatif déjà corrigé partout ailleurs ce soir. Corrigé pour utiliser `config.py`. Conservé et versionné pour la première fois.

## S4.D21 — Audit qualité réexécuté : identification de deux nouvelles causes de faux positifs dans le détecteur

**Contexte** : `audit_chunks.py` signalait 44 chunks "ATTENTION" sur 79. Hypothèse de départ (portée par le journal S3.D4) : tirets de césure typographique, déjà qualifiés de faux positif sans gravité.

**Décision méthodologique** : vérifier empiriquement sur des extraits réels plutôt que de supposer que la cause connue expliquait tout.

**Résultat de l'investigation** : la cause réelle des 44 alertes n'était **pas** les tirets de césure mais un défaut du pattern de détection lui-même (`PATTERN_ARTEFACT`), qui ne reconnaissait pas l'apostrophe typographique française (`'`, U+2019) ni les majuscules accentuées (`É`, `È`...) comme caractères valides — alors que ce sont des caractères français corrects et attendus.

**Décision** : corriger le pattern de détection (ajout de `\u2019` et des majuscules accentuées à la liste autorisée) plutôt que de modifier les données, qui étaient en réalité correctes.

**Conséquence** : 44 → 1 "ATTENTION" après correction. Le seul cas restant (`ips_2023_ni_manual_010`, trop long) est un chunk manuel volontairement étendu, jugé non problématique.

## S4.D22 — Découverte et correction d'un vrai bug de césure, et fermeture définitive de la dette S3.D4

**Contexte** : après correction du détecteur, 8 chunks classés "VERIFIER" (catégorie `COUPURE_POSSIBLE`) sont apparus — invisibles dans le run précédent car noyés dans les 44 faux positifs.

**Investigation menée** : inspection du contenu réel de ces 8 chunks. Confirmé : un vrai pattern de césure existe (`avan- tages`, `cha- cun`, `va- riable` — tiret suivi d'un espace au lieu d'un saut de ligne, introduit par le traitement Unstructured), distinct de la cause identifiée en S3.D4 (qui portait sur `mot-\nmot`, jamais observé tel quel dans le corpus réel).

**Décision** : ajouter un nettoyage ciblé dans `extraire_chunks()` (`ingest_rag.py`) : `re.sub(r'(\w)- ([a-zàâ...])', r'\1\2', ...)`, testé au préalable sur 15 exemples réels extraits du corpus (15/15 corrects, aucun faux positif sur la ponctuation légitime) avant application au pipeline complet.

**Incident en cours de route, significatif pour la méthode** : la première implémentation du correctif ne produisait aucun effet observable en sortie malgré une syntaxe correcte. Cause : le nettoyage modifiait une variable locale (`texte`) qui n'était jamais relue — l'ingestion réelle relit `chunk.text` directement depuis l'objet retourné par `chunk_by_title`, pas la variable locale dérivée. Corrigé en modifiant `chunk.text` en place. Plusieurs tentatives de correction ont elles-mêmes échoué silencieusement à cause d'erreurs de copier-coller dans le terminal (heredoc tronqué, échappement de regex mal interprété par le shell) — résolu en basculant vers une manipulation de fichier par numéro de ligne plutôt que par remplacement de bloc de texte.

**Décision complémentaire** : ajout de `?` et `!` à la liste de ponctuation de fin de phrase valide dans `audit_chunks.py` (absents par erreur, causant un faux positif supplémentaire).

**Résultat final de l'audit** : 0 critique, 1 attention (chunk long volontaire), 7 vérifier (coupures en milieu de phrase, reclassées comme limite assumée du chunking par taille — pas un bug).

**Conséquence** : dette technique S3.D4 close, mais avec un diagnostic corrigé par rapport à l'hypothèse initiale de session 3 — il y avait bien un vrai bug de césure (jamais identifié avec précision avant ce soir), distinct des deux catégories de faux positifs de détection.

## S4.D23 — Test et rejet de l'overlap de chunking (`chunk_overlap`/`overlap_all`)

**Contexte** : `RAG_CHUNK_OVERLAP = 50` existait dans `config.py` depuis la session 1 mais n'avait jamais été branché au pipeline — dette non identifiée jusqu'ici faute de vérification. Proposé comme piste pour réduire l'impact des coupures de phrase en milieu de chunk.

**Recherche préalable** : la documentation Unstructured précise que `overlap` (seul) ne s'applique que lors d'un text-splitting d'élément trop volumineux ; pour l'appliquer aussi aux chunks "normaux" (regroupés par titre, non subdivisés), le paramètre `overlap_all=True` est nécessaire — avec un avertissement de la documentation elle-même sur le risque de "pollution" des frontières sémantiques propres.

**Décision de méthode** : tester avant d'adopter (même principe que pour le re-ranker, S4.D14), plutôt que d'activer sur la base du raisonnement théorique seul.

**Résultat du test** (`overlap=50, overlap_all=True`) : régression sévère et immédiate — 79 chunks tombés à 29, avec des mots cassés en plein milieu (`"L es résultats"` au lieu de `"Les résultats"`), vraisemblablement par interaction destructive avec les règles de filtrage qualité maison.

**Décision finale** : rejeté. Retour à la configuration sans overlap, validé par ré-ingestion identique (79 chunks, mêmes résultats de test). `RAG_CHUNK_OVERLAP` reste déclaré dans `config.py` mais non utilisé — à documenter explicitement comme tel pour éviter la confusion dans une future session.

## S4.D24 — Comparatif RAG vs no-RAG vs long-context : validation objective du choix d'architecture

**Problème posé** : déterminer si l'investissement d'ingénierie du RAG (chunking, embeddings, filtrage qualité, golden dataset) apporte une valeur mesurable, par rapport à deux alternatives plus simples — un LLM sans aucun contexte (connaissances d'entraînement seules), et un LLM avec les documents sources entiers injectés en contexte sans aucun traitement (simulant un usage "copier-coller dans ChatGPT/Claude").

**Vérification préalable** : volume total des 4 PDFs sources en tokens (34 188 tokens) confirmé compatible avec la fenêtre de contexte de GPT-4o-mini (128k) avant de construire le test, avec large marge.

**Conception méthodologique actée** :
- Prompts système volontairement minimaux et neutres pour les deux configurations de comparaison, distincts du prompt RAG optimisé, pour rester fidèle à un usage non technique
- Pas de Faithfulness pour les configurations no-RAG et long-context (pas de "contexte récupéré" comparable au sens RAG) — seulement Answer Relevance et Answer Correctness, jugées par les mêmes prompts de judge que la configuration RAG pour une comparaison homogène
- Activation via flag dédié (`TESTER_NO_RAG_LONGCONTEXT`, défaut `False`), même principe que `TESTER_RERANKER`, pour ne pas alourdir les runs courants

**Résultats sur le golden dataset actuel (6 questions IVAC)** :

| Configuration | Answer Relevance | Answer Correctness | Coût/run | Latence moy. |
|---|---|---|---|---|
| RAG (nous) | 0.88 | **0.92** | $0.0045 | — |
| No-RAG | 0.88 | 0.68 | $0.0024 | 4.3s |
| Long-context | **0.97** | 0.83 | $0.033 (7×) | 11.6s |

**Interprétation actée, explicitement nuancée** : le RAG l'emporte sur Answer Correctness (le critère jugé le plus important) et très largement sur le coût et la latence. Le no-RAG confirme que GPT-4o-mini invente ou approxime sur des indicateurs aussi spécifiques que les IVAC/IPS. Mais le long-context obtient un score de correction étonnamment proche (0.83 vs 0.92) avec zéro travail d'ingénierie — sur un corpus aussi petit (4 PDFs, 79 chunks), l'écart de qualité brute apporté par le RAG est plus modeste qu'attendu. La décision actée est de ne pas survendre l'avantage qualité du RAG sur ce projet à cette échelle : c'est principalement l'économie de coût et de latence qui justifie l'architecture ici, pas un fossé de qualité écrasant — nuance importante à garder précise plutôt que de céder au slogan "le RAG est toujours meilleur".

**Nuances complémentaires actées a posteriori, à conserver dans l'argumentaire** :

1. **Biais du modèle unique** — la comparaison a été faite à modèle constant (GPT-4o-mini) pour isoler l'effet de l'architecture. Un modèle plus capable en long-context (Claude Sonnet, GPT-4o complet, modèles de raisonnement) resserrerait probablement l'écart de qualité avec le RAG, voire l'inverserait sur certaines questions — ces modèles sont meilleurs pour localiser l'information pertinente dans un contexte long et bruyant. Ce que ça ne change probablement pas : l'écart de coût et de latence, structurellement lié au volume de tokens traité plutôt qu'au modèle utilisé.

2. **Coût de conception non mesuré par le harness** — le harness ne capture que le coût d'inférence par requête, pas le temps humain investi (lecture des PDFs, design du chunking, construction du golden dataset, harness lui-même — plusieurs sessions de travail). Face à "coller les PDFs dans ChatGPT/Claude", qui ne coûte quasiment rien et ne demande aucun travail de conception, ce coût d'ingénierie est un investissement réel à amortir, pas neutre dans l'arbitrage global.

3. **Valeur de service indépendante de la technique** — un parent visiteur du site n'a pas nécessairement d'abonnement ChatGPT Plus/Claude Pro, ne sait pas que ces documents DEPP existent, ne saurait pas formuler la bonne requête ni où trouver les PDFs sources. Le produit, même avec un avantage de qualité modeste sur ce test à architecture égale, rend un service d'accessibilité et de structuration que "coller un PDF soi-même" ne rend pas pour le grand public.

## S4.D25 — Exploration du RAG managé comme alternative architecturale (information, non actée)

**Contexte** : en prolongement du comparatif RAG vs no-RAG vs long-context (S4.D24), exploration d'une quatrième famille d'architecture non testée empiriquement — le RAG managé (file search hébergé par un fournisseur, ex. OpenAI `file_search` sur la Responses API, anciennement Assistants API).

**Point de vigilance factuel relevé en recherche** : l'Assistants API d'OpenAI est en cours de dépréciation, fermeture prévue le 26 août 2026, remplacée par la Responses API qui propose une fonctionnalité équivalente (`file_search` tool, vector stores managés). Toute référence future au "RAG managé OpenAI" doit viser la Responses API, pas les Assistants.

**Avantages identifiés** : zéro infrastructure à maintenir (pas de ChromaDB à héberger ni de pipeline d'ingestion à déboguer), mise en place en quelques lignes de code, maintenance du chunking/embedding déléguée au fournisseur.

**Limites identifiées, justifiant le choix du from-scratch pour ce projet** :
- Boîte noire — pas de contrôle sur la stratégie de chunking, impossible de calculer Recall/Precision/MRR sur le retrieval comme fait dans `harness.py`, donc impossible de diagnostiquer une mauvaise réponse avec la même précision
- Pas de levier pour appliquer le travail de filtrage qualité réalisé cette session (exclusion des exemples fictifs, correction des césures, métadonnées Dublin Core) — ce filtrage suppose un contrôle du pipeline que le RAG managé n'offre pas
- Fiabilité de citation des sources non garantie avec la même rigueur que l'architecture maison (sourcée par construction via les métadonnées `dc_source`/`chunk_page`)
- Verrouillage fournisseur — illustré concrètement par la dépréciation de l'Assistants API elle-même
- Coût de stockage vectoriel propre au fournisseur, distinct du coût d'inférence

**Distinction conceptuelle notée pour la suite du projet** : un article de veille (mars 2026) distingue "File Search" (RAG managé, chemin fixe retrieve-then-generate) d'"Agentic RAG" (boucle de raisonnement autour du retrieval — décider s'il faut chercher, reformuler la requête, évaluer la suffisance des résultats, relancer si besoin). Ni le RAG managé simple ni le RAG actuel du projet (non-agentique à ce stade) ne couvrent cette dimension — c'est précisément l'objectif de l'architecture cible (router LangGraph + agent ReAct, cf. S1.5) à venir dans une prochaine session.

**Décision** : pas de RAG managé testé empiriquement à ce stade — exploration purement informative. Position assumée : le RAG managé est adapté à un MVP rapide à faible enjeu ; écarté ici parce que l'objectif du projet est de comprendre et maîtriser chaque étape du pipeline pour pouvoir diagnostiquer et améliorer, ce qu'une boîte noire ne permet pas.

**Approfondissement technique (recherche complémentaire)** :

- **Mécanisme réel du chunking managé OpenAI** : par défaut, blocs fixes de 800 tokens avec 400 tokens d'overlap (50%, bien plus agressif que les 50 caractères testés et rejetés en S4.D23) — un découpage mécanique par taille, structurellement plus naïf que `chunk_by_title` utilisé dans ce projet, sans compréhension de la structure du document (titres, sections).
- **Retrieval managé plus sophistiqué que notre implémentation sur un point précis** : hybrid search (embedding sémantique + recherche par mots-clés type BM25, combinés par reciprocal rank fusion) — supérieur à la simple similarité cosinus utilisée dans `rag_tool.py`. Un re-ranker est aussi disponible en option côté managé.
- **Témoignage de praticiens (Team400, avril 2026)** confirmant empiriquement le risque anticipé : des réponses pertinentes à cheval sur un saut de page se retrouvent coupées entre deux chunks sans contexte suffisant dans aucun des deux — exactement le type de défaut corrigé manuellement dans cette session (S4.D22, S3.D5).
- **Littérature de recherche sur le chunking** : plusieurs études récentes (Qu et al. 2025, Merola & Singh 2025, NAACL 2025 Findings) montrent que le chunking fixe à taille raisonnable égale ou bat le chunking sémantique sophistiqué sur de nombreuses tâches réelles, pour un coût de calcul bien moindre — nuance importante : la sophistication de la stratégie de chunking compte parfois moins que la qualité du texte source en amont (nettoyage, exclusions).
- **Limite structurelle identifiée malgré les progrès attendus** (Adaptive Chunking, mars 2026) : aucune stratégie de chunking unique n'est optimale pour tous les documents — l'optimal dépend de la structure et du contenu, ce qui plaide pour des stratégies adaptatives par document plutôt qu'une règle générique uniforme.

**Position prospective actée (discussion, non un résultat empirique)** : analogie assumée avec l'arbitrage build-vs-buy en infrastructure — ce n'est pas une compétition que le managé "gagnera" définitivement, mais un choix récurrent selon le contexte, les enjeux et le moment. Deux nuances complémentaires actées :
1. Les services managés deviendront probablement plus performants avec le temps (stratégies de chunking adaptatives par type de document, chunkers pilotés par LLM déjà en recherche) — il restera toujours un segment d'utilisateurs préférant payer pour gagner du temps plutôt que de répliquer ce travail manuel, comme pour tout autre service managé en informatique.
2. Le travail de **sélection et filtrage qualité des documents** (exclure les exemples fictifs, détecter une coupure problématique) n'est pas non plus une forteresse durablement humaine — un LLM-as-a-judge appliqué au chunking lui-même (plutôt qu'à la génération finale comme dans `harness.py`) pourrait potentiellement automatiser une bonne partie de ce travail dès aujourd'hui, pas seulement "un jour". Ce qui reste plus probablement durable n'est pas le geste technique d'exécution, mais la **décision de ce qui compte et pourquoi** dans un domaine donné (ex. : savoir que la VA n'existe pas pour la série professionnelle, S1.19, est une règle métier critique à ne jamais perdre — une connaissance du domaine, pas une compétence d'exécution technique).

---

# Dettes techniques consolidées (état après session 4, deuxième partie)

## Closes cette session
- ~~Renommage `vulgarisation`/`vulgaire` → `accessible`~~ — clos S4.D19, validé par ré-ingestion et harness stables
- ~~Nettoyage des tirets de césure~~ — clos S4.D22, vrai bug identifié et corrigé (distinct du diagnostic initial de session 3)
- ~~Refactoring `CHUNKS_MANUELS` → JSON externe~~ — clos S4.D18, anticipé par rapport à la roadmap (prévu "avant le router", fait avant même que le router démarre)
- ~~`rag_tool.py` non versionné et avec hardcoding~~ — clos S4.D20, versionné et variabilisé

## Encore ouvertes / nouvelles

### Critiques
- **Prompt système du router** — toujours pas rédigé, pièce centrale identifiée depuis S2.15
- **Guardrail hors-domaine dédié** — toujours pas construit, identifié S2.23

### RAG / Données
- Source sur l'interprétation du taux d'accès — S4.D3
- Source sur le lien VA → progression réelle des élèves — S4.D7
- Source sur l'interprétation de la part d'élèves présents au DNB — S4.D3
- Query expansion sur les acronymes (pipeline) — identifié S4.D6
- Champ `dc_type_source` à ajouter au schéma Dublin Core — S4.D8
- `RAG_CHUNK_OVERLAP` dans `config.py` : testé et rejeté (S4.D23), reste déclaré mais non utilisé — à clarifier dans le code (commentaire explicite) pour éviter qu'une future session ne suppose qu'il est actif

### Golden dataset
- 6 questions validées (IVAC uniquement) sur ~35 ciblées
- Passe 1c (IPS, ~5 questions) — non commencée
- Passe 2 (cross-thématique + question hybride SQL+RAG) — non commencée
- Passe 3 (hors domaine) — non commencée

### Harness / Évaluation
- RAGAS non testé en complément (S4.D9)
- Re-ranker désactivé, à retester si le corpus grossit (S4.D14)
- Comparatif no-RAG/long-context construit et validé (S4.D24) — à refaire une fois le golden dataset enrichi (IPS, cross-thématique) pour confirmer si la tendance se maintient sur un périmètre plus large
- `sql_tool` et `geo_tool` : fonctionnels mais sans harness formel (S2.18)
- Métrique de cohérence inter-outils (S2.19) : conçue, non implémentée

### Agent / Orchestration
- Router LangGraph — non commencé
- Mémoire de session — non implémentée
- Logique de régénération partielle ciblée (S2.19) — non implémentée
- Gestion de l'ambiguïté temporelle session IVAC/année IPS côté interface (S1.14) — non implémentée

### Sécurité / Guardrails
- Rate limiting par IP — non implémenté
- Cache de géocodage anti-abus — non implémenté
- Validation structurée des inputs/outputs de l'agent — non implémentée

### Interface / Front
- Décision d'affichage du volume de résultats (pagination) — non tranchée
- Gestion responsive — non commencée
- Affichage lisible et non trompeur du badge VA et du secteur — non implémenté

### Infra / DevOps
- LangSmith en conditions réelles — clé intégrée, traces non vérifiées en usage agent complet
- Budget cap OpenAI — non configuré sur le dashboard
- Déploiement (question d'hébergement alternatif à Streamlit Cloud soulevée mais reportée) — non commencé
- Pipeline de relance d'ingestion à chaque redéploiement — anticipé, non implémenté

### Gouvernance projet
- Nom de produit définitif — toujours provisoire (`agent-ecoles`)
- Licence GitHub définitive — MIT envisagée, non actée formellement
- **Identité Git mal configurée** — nom/email déduits automatiquement du nom d'utilisateur système plutôt que configurés explicitement (signalé par Git lors d'un commit cette session, pas bloquant mais à corriger via `git config --global`)
- Politique éditoriale sur les sources d'interprétation (S4.D8) — à rédiger formellement

---

# Phase 5 — Router : désambiguïsation d'établissements nommés

## S7.1 — Résolution de noms d'établissements par lookup SQL, pas par LLM

**Décision** : `rechercher_etablissements_par_nom()` fait une recherche SQL directe (`LIKE`) sur le nom, sans appel LLM.

**Pourquoi** : trouver les établissements correspondant à un nom donné est une recherche déterministe, pas une tâche d'interprétation de texte libre — cohérent avec le principe templating vs LLM déjà établi (S1.5, fiche dédiée). Extraction des noms eux-mêmes fusionnée dans l'appel LLM du router déjà existant (même mécanisme que l'extraction de zone géo), pour éviter un appel LLM séparé.

**Conséquence** : ajout de `noms_etablissements` au state du graphe, extrait en même temps que `categorie` et `zone_geo` en un seul appel function-calling.

## S7.2 — Exclusion des SEGPA/sections dans la recherche par nom

**Problème identifié en test** : la recherche par nom remontait aussi les SEGPA rattachées aux collèges (ex: "Section d'enseignement général et professionnel adapté Victor Hugo") comme candidats au même titre que le collège lui-même — des sous-structures internes, pas des établissements comparables.

**Décision** : exclusion des lignes dont le nom contient "Section d'" dans `rechercher_etablissements_par_nom()`.

**Conséquence** : réduction de 49 à 39 candidats sur le cas test "Victor Hugo".

## S7.3 — Entonnoir de désambiguïsation à 2 niveaux (département puis ville), boutons plutôt que texte libre en cible finale

**Problème** : un nom d'établissement seul peut remonter des dizaines de candidats (39 pour "Victor Hugo", 72 pour "Jean Moulin") — une liste numérotée de cette taille est inexploitable.

**Options envisagées** : liste complète toujours affichée / seuil fixe avec redemande département seul / entonnoir à 2 niveaux (département puis ville si insuffisant).

**Décision** : seuil de 5 candidats maximum pour un affichage direct en liste numérotée (destinée à devenir des boutons cliquables une fois hors console, cf. interface Streamlit à venir). Au-delà, demande du département (2 chiffres) ; si le département ne suffit pas à redescendre sous le seuil, demande la ville.

**Pourquoi 2 niveaux et pas 1 seul** : vérifié empiriquement sur les 7723 collèges réels du CSV annuaire — le département seul ne suffit pas toujours (5 groupes nom+département dépassent le seuil de 5, jusqu'à 10 candidats pour "Collège Saint-Joseph" dans plusieurs départements). Une hypothèse initiale ("un seul edge case à 5") a été vérifiée et invalidée par cette analyse avant d'être adoptée.

**Rejeté** : demander directement la ville sans passer par le département — le département est plus facile à saisir sans erreur (2 chiffres) qu'un nom de ville (source d'erreurs de frappe/orthographe), donc gardé comme premier niveau de filtre.

**Conséquence** : `interpreter_precision()` et `filtrer_candidats_par_precision()` ajoutées à `sql_tool.py`. Résolution automatique sans confirmation demandée dès qu'un seul candidat reste à n'importe quelle étape de l'entonnoir (évite une friction inutile sur un choix qui n'en est plus un).

## S7.4 — Prise en compte d'une zone déjà donnée dans la question (pré-filtre automatique avant l'entonnoir)

**Problème identifié en test** : une question comme "Compare le collège Victor Hugo à Nantes" contient déjà l'information de zone, mais le chemin `comparaison_etablissements_nommes` ignorait complètement `zone_geo` (extraite par le router mais jamais consultée sur ce chemin), redemandant un département déjà implicitement donné.

**Décision** : `zone_geo`, si présente, est appliquée comme pré-filtre automatique dans `noeud_resolution_noms`, avant même de lancer l'entonnoir interactif. Le niveau de départ de l'entonnoir s'ajuste en conséquence (saute le département si `zone_geo` était déjà un département, etc.).

**Pourquoi** : cohérence avec le traitement de `zone_geo` déjà en place sur le chemin `recherche_geo_classement` (la zone extraite alimente directement `geo_tool` sans être redemandée) — éviter une incohérence entre chemins qui traitent la même information différemment.

**Garde-fou associé** : si la zone donnée ne correspond à aucun candidat (ex: "Jean Moulin à Perpignan" si aucun n'existe là-bas), le système ne se rabat jamais silencieusement sur la liste complète — il le signale explicitement via `zones_sans_resultat` et redemande une autre zone. Cohérent avec le principe de grounding déjà appliqué ailleurs (jamais de substitution silencieuse d'une contrainte utilisateur, cf. `router_apres_geo` qui ne laisse jamais `sql_tool` deviner une zone en silence).

**Conséquence** : `noeud_resolution_noms` et `noeud_clarification_noms` modifiés pour gérer ce pré-filtre et ce garde-fou. Messages de clarification rendus contextuels au niveau réel de l'entonnoir (ne pas proposer de nouveau le département si déjà consommé).

## S7.5 — Dette technique identifiée, non corrigée cette session

- **Recherche par nom (`LIKE '%nom%'`) trop permissive sur les noms composés** : "Saint-Joseph" remonte aussi "Saint-Joseph de Cluny", "Saint-Joseph La Salle", "Notre-Dame-Saint-Joseph" — des établissements différents, pas des homonymes du même nom. Vérifié empiriquement : 127 résultats bruts vs un vrai nombre d'homonymes exacts bien inférieur. Le nombre affiché à l'utilisateur est donc gonflé sur les noms composés, même si le filtrage final par zone reste correct.
- **Plusieurs noms ambigus simultanément non géré** : le cas d'usage affiché en exemple du script de test lui-même ("Compare Victor Hugo et Jean Moulin") déclenche cette limite — reformulation demandée plutôt que double entonnoir.
- **Cas "niveau épuisé" de l'entonnoir jamais rencontré empiriquement** avec les vraies données pendant les tests — géré en théorie dans le code, non vérifié en pratique.

## S7.6 — Adoption de Claude Code pour l'exécution mécanique, chat conservé pour la conception

**Problème** : friction croissante du mode "copier-coller de fichiers entiers dans le chat" au fil des sessions (reformalisation du contexte à chaque nouvelle conversation, réécriture de fichiers volumineux pour des corrections mineures).

**Décision** : bascule vers Claude Code pour la lecture/modification directe des fichiers et l'exécution des tests, avec un fichier `CLAUDE.md` à la racine du repo encodant explicitement les règles de méthode (conception avant code, jamais d'exécution silencieuse, patch ciblé vs réécriture complète, challenge constructif, git comme filet de sécurité obligatoire avant changement structurel).

**Pourquoi** : le gain de vitesse est réel, mais le risque identifié est la perte du garde-fou de compréhension qu'impose le copier-coller manuel (lecture attentive de chaque sortie, ce qui a permis de détecter plusieurs bugs réels cette session). `CLAUDE.md` vise à préserver la discipline pédagogique malgré l'autonomie d'exécution plus large de l'outil.

**Rejeté** : bascule complète sans cadrage — jugée risquée sans garde-fous explicites, l'objectif du projet étant la compréhension de chaque décision, pas seulement la vitesse de livraison. Révise la position prise en S3.D16 (maintien du chat, refusé alors car "Claude Code ne résout pas davantage le problème") — le contexte a changé : le goulot d'étranglement identifié en session 3 était la perte de contexte entre sessions, celui identifié en session 7 est la friction du copier-coller de fichiers volumineux au sein même d'une session active.

**Conséquence** : `CLAUDE.md` et les documents de transition de session sont volontairement exclus du suivi git (`.gitignore`) — fichiers de méthode de travail personnelle, pas des artefacts du projet à exposer publiquement sur le repo GitHub.

## S8.1 — Correction de la recherche par nom trop permissive sur les noms composés (clôture de la dette S7.5)

**Décision** : `rechercher_etablissements_par_nom()` garde le `LIKE` SQL comme filtre large (recall), mais ajoute un filtrage Python en sortie qui ne conserve que les candidats dont le nom nettoyé (minuscules, sans accents, sans préfixe institutionnel Collège/Collège privé/École/CLG) correspond exactement au nom recherché nettoyé de la même façon.

**Pourquoi** : vérifié empiriquement sur "Saint-Joseph" — 191 candidats bruts via `LIKE`, dont seulement 146 sont de vrais homonymes ("Collège Saint-Joseph" / "Collège privé Saint-Joseph") ; le reste (45) était des noms composés différents ("Saint-Joseph de Cluny", "Saint-Joseph La Salle"...) qui gonflaient artificiellement le nombre de candidats affiché à l'utilisateur.

**Conséquence** : ajout de `_normaliser_nom()` et de la constante `PREFIXES_INSTITUTIONNELS` (limitée aux 4 préfixes ayant un poids statistique réel sur l'ensemble des collèges — vérifié avant d'élargir, cf. S8.2).

## S8.2 — Portée du nettoyage des noms limitée aux préfixes à poids statistique réel

**Décision** : liste de préfixes retenue = Collège, Collège privé, École/Ecole, CLG (fréquence ≥10 sur l'ensemble des collèges). Les préfixes plus rares (Institution, Institut, Centre, Ensemble, Cours, Annexe...) ne sont pas traités.

**Pourquoi** : vérification empirique sur l'ensemble des établissements de type Collège avant de trancher — ces préfixes rares (2 à 5 occurrences chacun) risquent de faire partie du nom distinctif réel de l'établissement plutôt que d'être un simple équivalent de "Collège" ; les traiter sans plus de vérification aurait été une généralisation non fondée.

**Rejeté** : liste exhaustive de tous les préfixes observés — jugée trop risquée (sur-nettoyage potentiel) pour un gain marginal.

**Conséquence** : limite documentée, pas une dette cachée — à revoir seulement si un cas concret avec un autre préfixe se présente.

## S8.3 — Retrait du préfixe institutionnel du nom recherché avant la requête SQL (pas seulement des candidats)

**Problème découvert en test** : le LLM du router extrait parfois le nom en gardant le mot "collège" (ex: "collège Saint-Joseph" plutôt que "Saint-Joseph"). Le `LIKE` construit à partir de cette chaîne exige une sous-chaîne continue, donc "Collège privé Saint-Joseph" n'est jamais retrouvé (le mot "privé" casse la continuité) — 108 candidats au lieu de 146 selon que le LLM garde ou non "collège".

**Décision** : `_retirer_prefixe_recherche()` retire le même préfixe institutionnel du nom recherché avant de construire le `LIKE`, sans toucher aux accents/casse du reste (pour ne pas casser la recherche sur les noms accentués).

**Pourquoi** : la fiabilité de la recherche ne doit pas dépendre d'un aléa d'extraction LLM — cohérent avec le principe templating vs LLM déjà établi.

**Conséquence** : validé par test (146 candidats identiques que "collège" soit gardé ou non par le LLM) et par un test de non-régression sur un nom accentué réel en base.

## S8.4 — Extension du filtre d'exclusion SEGPA au motif "SEGPA"

**Problème découvert en creusant S8.1** : le filtre existant (`NOT LIKE '%Section d%'`) laissait passer 27 lignes commençant directement par "SEGPA" (ex: "SEGPA du Collège privé Saint-Joseph La Salle").

**Décision** : ajout de `AND nom NOT LIKE '%SEGPA%'` à la requête.

**Conséquence** : les 27 lignes concernées sont désormais exclues, cohérent avec l'intention originale de S7.2.

## S8.5 — Correction d'un bug de saisie vide dans l'entonnoir de désambiguïsation

**Problème découvert en test** : appuyer sur Entrée sans rien taper à l'étape département ou ville était interprété par `interpreter_precision()` comme une recherche par ville avec valeur vide — et une chaîne vide est une sous-chaîne de n'importe quel nom de commune, donc **tous** les candidats passaient le filtre silencieusement. Conséquence observée en test réel : la saisie vide faisait croire au filtrage qu'il avait réussi, jusqu'à afficher la liste complète des 146 candidats un par un.

**Décision** : `interpreter_precision()` reconnaît maintenant explicitement une saisie vide comme un type "invalide" à part, pour lequel `filtrer_candidats_par_precision()` retourne une liste vide — ça réactive le mécanisme de nouvelle tentative déjà prévu (message "Aucune correspondance", compteur 3 tentatives max) au lieu de l'ignorer.

**Conséquence** : validé par test automatisé et par test manuel réel (le message "Aucune correspondance... tentative 1/3" puis "2/3" s'affiche désormais correctement).

## S8.6 — Formalisation détaillée de la formule de calcul du score (clarification de S1.3)

**Contexte** : la pondération 60% taux de réussite / 40% note à l'écrit était déjà actée (S1.3), mais le mécanisme de normalisation qui précède cette pondération n'avait jamais été détaillé en français dans le journal — retrouvé dans `data/ingest.py` et reformulé aujourd'hui en préparant la conception du chemin recherche_geo_classement (répartition public/privé).

**Formule exacte** (fonction `calculer_scores()`) : pour chaque session (année) séparément, parmi les établissements ayant un taux de réussite et une note à l'écrit renseignés :
1. Normalisation min-max du taux de réussite : ramène chaque établissement sur une échelle de 0 (pire taux de l'année) à 1 (meilleur taux de l'année), relativement aux autres établissements de la même session.
2. Même normalisation, indépendamment, pour la note à l'écrit.
3. Score final = `(taux normalisé × 0.60 + note normalisée × 0.40) × 100`

**Pourquoi une normalisation min-max par session (et pas une échelle fixe)** : le taux de réussite (%) et la note à l'écrit (/20) n'ont pas la même échelle brute — sans normalisation, le taux écraserait la note dans la pondération. Le faire par session plutôt qu'une bonne fois pour toutes évite qu'un collège soit comparé à un étalon devenu obsolète si le niveau global du brevet varie d'une année à l'autre.

**Conséquence** : un score n'est comparable qu'entre établissements de la même session, jamais d'une année sur l'autre. Poids (`SCORE_POIDS_TAUX = 0.60`, `SCORE_POIDS_NOTE = 0.40`) et seuils VA (`VA_SEUIL_POSITIF = 2.0`, `VA_SEUIL_NEGATIF = -2.0`) définis dans `config.py`.

## S8.7 — Fusion de `recherche_geo_comparaison` dans `recherche_geo_classement`

**Problème découvert en testant les chemins restants du router** : ces deux catégories routaient vers exactement le même pipeline (`geo_tool` → `sql_tool` → `synthese`), avec un texte de sortie strictement identique (`_generer_intro_template()` ne lit ni la question ni la catégorie) — malgré une intention de différenciation visible dans le prompt du router ("tri par indicateur" vs "+ comparaison"), jamais implémentée en pratique.

**Décision** : suppression de `recherche_geo_comparaison` des catégories du router ; sa description est absorbée dans celle de `recherche_geo_classement`.

**Pourquoi** : la seule différence envisageable aurait été cosmétique (formulation de l'intro), pas une différence de données ou de traitement — pas assez de valeur pour justifier deux catégories, avec le risque que le LLM du router hésite entre deux formulations proches ("meilleurs collèges de Lyon" vs "compare les collèges de Lyon"). Cohérent avec le principe déjà acté de ne pas construire pour un besoin hypothétique.

**Validé par test** : `test_router_classification.py` (5/5 sur les cas concernés) et test bout en bout sur "Compare les collèges publics et privés autour de Bordeaux", correctement classée et traitée par le pipeline fusionné.

**Conséquence** : 4 fichiers mis à jour (`graph_router.py`, `prompts/router_system_prompt.py`, `test_router_classification.py`, `benchmark_router.py`). A aussi révélé, en testant ce cas de comparaison public/privé, un angle mort pré-existant (non causé par cette fusion) sur la représentation des deux secteurs dans les résultats affichés — traité séparément (cf. S8.8).

## S8.8 — Split déterministe public/privé quand le secteur n'est pas précisé, et explication du score ajoutée à l'affichage

**Problème découvert en testant `recherche_geo_classement` sur "Compare les collèges publics et privés autour de Bordeaux"** : le classement global top 15 ne contenait qu'1 seul établissement public sur 15, alors que 36 publics existaient dans la zone (contre 14 privés) — pas un bug, un vrai écart de score entre secteurs (biais de sélection à l'entrée, déjà documenté dans l'avertissement affiché), mais qui rendait dans les faits le secteur public quasiment invisible dès qu'on ne filtrait pas explicitement dessus.

**Décision** :
- Le router extrait un signal supplémentaire (`secteur_souhaite` : `public`/`prive`/`indifferent`), dans le même appel LLM déjà utilisé pour la catégorie/zone/noms.
- Secteur précisé explicitement → comportement inchangé (Text-to-SQL habituel, un seul secteur).
- Secteur non précisé → nouvelle fonction déterministe `rechercher_top_par_secteur()` (aucun appel LLM), qui retourne séparément les 10 meilleurs établissements de chaque secteur, affichés en deux tableaux distincts et étiquetés plutôt qu'un classement mélangé.

**Pourquoi une requête déterministe plutôt que de le déléguer au Text-to-SQL existant** : "prendre le top 10 de chaque secteur quand rien n'est précisé" est une règle fixe une fois l'ambiguïté résolue par le router — pas une tâche d'interprétation de texte libre. Fiabilité garantie à chaque appel, sans coût ni latence LLM supplémentaire, cohérent avec le principe templating vs LLM déjà établi.

**Décision complémentaire** : ajout d'une explication courte et fixe du Score (même principe que celle déjà existante pour la VA), affichée systématiquement dès qu'un tableau de résultats est montré — jusqu'ici seule la VA était expliquée, alors que le Score (critère de tri principal) ne l'était jamais. Colonnes réordonnées (Score, VA, puis Taux/Note) pour rapprocher visuellement le score de sa nuance.

**Gain de latence constaté en effet de bord** : mesure par étape sur le chemin split — router 2.02s, geo_tool 0.16s, sql_tool 0.00s (contre un appel Text-to-SQL LLM auparavant), synthese 0.00s. Total 2.18s contre 3.8s mesurés avant cette session sur le même type de question — quasiment divisé par 2, uniquement parce que le Text-to-SQL est devenu inutile sur ce chemin précis. Le goulot d'étranglement restant est l'appel LLM du router lui-même (~93% du temps) ; un benchmark multi-fournisseurs (`benchmark_router.py`) avait déjà été mené sur cet appel et n'avait montré aucune différence significative entre gpt-4o-mini, claude-haiku-4-5 et gemini-2.5-flash — pas de nouvelle piste à ce stade.

**Conséquence** : `agent/tools/sql_tool.py` (nouvelle fonction), `graph_router.py` (state, schéma d'extraction, branchement `noeud_sql`, affichage `noeud_synthese`), `prompts/router_system_prompt.py`. Validé par test bout en bout mené par l'utilisateur lui-même sur Bordeaux — le meilleur collège public réel de la zone (Émile Combes, score 86.60) apparaît désormais, alors qu'il était totalement absent de l'ancien affichage.

## S8.9 — Correction du router : classification `non_reconnu` + température non fixée

**Problème découvert** : "Mon fils a du mal à se concentrer, quel collège lui conviendrait ?" classée en `question_methodologique` au lieu de `non_reconnu`, de façon stable (3/3), avec l'ancien prompt à 5 comme à 6 catégories — confirmé non causé par la fusion S8.7.

**Diagnostic initial** : description de `non_reconnu` purement négative ("aucune catégorie ne correspond"), sans exemple positif — signal plus faible pour le LLM qu'une catégorie décrite positivement.

**Tentatives testées et écartées** : resserrer `question_methodologique` + exemple sur `non_reconnu` → corrige le cas ciblé mais déstabilise "Compare les collèges publics et privés autour de Bordeaux" (5/6). Resserrer aussi `comparaison_etablissements_nommes` en plus → aggrave l'instabilité (5/6 à chaque run, vers une catégorie différente à chaque fois).

**Cause réelle identifiée** : le router n'avait jamais de `temperature` fixée (1.0 par défaut, aléatoire), contrairement au Text-to-SQL (`generer_sql`, `temperature=0` depuis la phase 1). Resserrer une frontière de décision entre catégories rend cet aléa visible.

**Décision finale** : exemple ajouté à `non_reconnu` seul (sans toucher aux autres catégories) + `temperature=0` sur l'appel LLM du router.

**Validé par test** : 6/6 sur 3 exécutions du script réel (`test_router_classification.py`), aucune régression.

**Conséquence** : `graph_router.py`, `prompts/router_system_prompt.py`. Point de vigilance noté pour plus tard : `noeud_synthese` (appel LLM de nuance RAG) n'a pas non plus de température fixée — pas de risque fonctionnel identifié (sortie déjà très contrainte par son prompt système), donc traité comme piste facultative plutôt que bug à corriger.

## S8.10 — Généralisation du signal de nuance méthodologique (remplace `recherche_geo_methodologique`)

**Problème découvert** : en questionnant pourquoi seule la combinaison géo+méthodologie avait une catégorie dédiée, vérification empirique : "Compare le collège Saint-Joseph et Victor Hugo à Nantes, et est-ce que leur VA est fiable ?" était classée en `comparaison_etablissements_nommes` sans jamais déclencher `rag_tool` — la partie méthodologique de la question était silencieusement ignorée. Angle mort de la conception initiale des catégories, pas un choix délibéré.

**Décision** : suppression de `recherche_geo_methodologique` comme catégorie. Extraction d'un signal indépendant `nuance_methodologique_demandee` (booléen) dans le même appel LLM fusionné que le reste. `router_apres_sql` route vers `rag_tool` avant `synthese` dès que ce signal est vrai, quelle que soit la catégorie de base (géo ou noms).

**Pourquoi** : sépare deux dimensions indépendantes (quelle donnée récupérer / faut-il une nuance méthodologique en plus) plutôt que de les combiner dans des catégories dédiées — évite une explosion combinatoire si d'autres combinaisons apparaissent plus tard (ex: ajout futur des lycées).

**Rejeté** : garder une catégorie dédiée par combinaison (aurait nécessité `comparaison_etablissements_nommes_methodologique` en plus, et toute future combinaison à multiplier).

**Conséquence** : `noeud_synthese` (déjà générique — composait tableau + nuance RAG sans modification nécessaire) fonctionne désormais pour les deux combinaisons. Validé par test sur les deux cas (géo+méthodo, noms+méthodo).

## S8.11 — Refactor de qualité de code (enums, constantes centralisées, découpage de `noeud_synthese`)

**Contexte** : à l'occasion de S8.10, décision de traiter aussi les défauts de structure accumulés au fil de la construction du router (code additif session après session, jamais réorganisé, hérité d'itérations par copier-coller en chat plutôt que Claude Code).

**Décision** :
- `Categorie`, `SecteurSouhaite`, `Secteur` : enums Python (`StrEnum`) dans `config.py`, remplaçant les chaînes libres répétées à plusieurs endroits (risque de faute de frappe silencieuse en cas de renommage).
- Constantes éparpillées (`MAX_LIGNES_SYNTHESE`, `SPLIT_SECTEUR_N`, `SEUIL_CANDIDATS_AVANT_PRECISION`, `PREFIXES_INSTITUTIONNELS`) centralisées dans `config.py`, y compris une copie dupliquée trouvée dans `test_comparaison_noms.py`.
- `noeud_synthese()` (~75 lignes, 6 responsabilités mélangées) découpée en fonctions nommées à responsabilité unique.
- Suppression de `_tronquer_resultats_geo()` (code mort confirmé — jamais appelée).
- Docstrings obsolètes mis à jour.

**Pourquoi** : cohérent avec l'objectif du projet de disposer d'une base saine et évolutive.

**Conséquence** : 7 fichiers modifiés, comportement final identique vérifié par re-test complet (classification 7/7 sur 3 runs, pipelines Bordeaux/méthodologique/comparaison tous intacts).

## S8.12 — Squelette de l'agent ReAct (dernier nœud du router)

**Décision** : boucle de décision dynamique (`noeud_agent_react`) — à chaque tour, le LLM choisit d'appeler un outil (`recherche_geo`, `recherche_sql`, `recherche_rag`) ou de répondre directement, jusqu'à `AGENT_MAX_TOURS` (5). Génère sa propre réponse finale, sans repasser par `noeud_synthese` (arête `agent_react → END` directe) — celui-ci suppose une forme de données fixe, incompatible avec des appels multiples en ordre libre.

**Pourquoi bypasser noeud_synthese** : conçu pour les 3 chemins déterministes à un seul appel SQL ; un agent qui peut appeler plusieurs outils dans un ordre imprévisible ne produit pas une forme de données compatible avec ce templating.

**Décision complémentaire — réutilisation du templating existant** : l'outil `recherche_sql` mis à disposition de l'agent renvoie un champ `tableau_formate` pré-généré (mêmes fonctions que les chemins déterministes : tableau, explication du score, badge VA, avertissement secteur privé). Corrige un problème observé en test : sans ça, l'agent affichait les valeurs de VA brutes non expliquées au lieu du badge positif/neutre/négatif. Cohérent avec le principe templating vs LLM déjà établi.

**Bug de routage trouvé et corrigé en testant** : "Compare le meilleur collège de Lyon et le meilleur collège de Marseille" était classée `comparaison_etablissements_nommes` alors que le router extrayait lui-même une liste de noms vide — incohérence interne. Garde-fou déterministe ajouté dans `noeud_router` (pas un patch de prompt, pour éviter le risque déjà observé aujourd'hui de déstabiliser d'autres cas) : si cette catégorie est choisie sans nom extrait, bascule automatique vers `non_reconnu`.

**Limite résiduelle connue, non corrigée** : quand l'agent doit combiner plusieurs appels `recherche_sql` (ex: comparaison multi-zones, un appel par zone), chaque appel ne renvoie qu'un `tableau_formate` partiel (une zone à la fois) — l'agent doit les fusionner lui-même pour présenter un tableau combiné, ce qui le pousse à résumer chaque résultat en puces avant le tableau final (redondance de style, pas d'erreur de données). Tentative de correction par prompt jugée à rendement décroissant — laissé tel quel, à réévaluer après la batterie de tests si ça se révèle gênant sur plusieurs cas.

**Conséquence** : nouveau fichier `prompts/agent_react_system_prompt.py`. Validé par test sur un cas hors-sujet (refus honnête sans appel d'outil inutile) et un cas complexe multi-zones (tableau correctement formaté avec badges VA, conclusion nuancée). Latence élevée sur ce chemin (~45s sur le cas multi-zones) — attendu et accepté pour l'instant, chemin réservé aux cas trop complexes pour les chemins déterministes. Affichage progressif pendant l'attente identifié comme besoin pour le futur chantier Streamlit (roadmap), pas réalisable sans interface aujourd'hui.

## S8.13 — Garde-fou déterministe : demande de classement à échelle non gérée mal classée en `question_methodologique`

**Problème découvert en construisant la batterie de tests de l'agent ReAct** : "Quel est le meilleur collège de France ?" classée en `question_methodologique` (zone non détectée, correctement — mais catégorie de repli incorrecte). Même phénomène que S8.9 (`question_methodologique` agit comme catégorie "par défaut" quand rien d'autre ne colle), mais sur un déclencheur différent de celui déjà corrigé (pas de nouvelle preuve que le fix de température/exemple de S8.9 couvre ce cas).

**Impact réel vérifié** : cette classification appelle `rag_tool` sur une requête sans rapport avec le corpus (guides méthodologiques DEPP, pas un palmarès national) — réponse vide ou incohérente plutôt qu'une clarification utile sur le périmètre du produit (pas de recherche à l'échelle nationale).

**Décision** : garde-fou déterministe dans `noeud_router` (pas un nouveau réglage de prompt) : si `categorie == question_methodologique`, qu'aucune zone n'est détectée, ET que la question contient un mot superlatif ("meilleur(s)/meilleure(s)", "pire(s)"), bascule vers `non_reconnu`. Volontairement restreint aux superlatifs — "classement" est exclu du déclencheur (peut légitimement désigner le concept lui-même, ex: "est-ce que le classement des collèges est fiable en général ?", vérifié : reste bien en `question_methodologique`).

**Pourquoi un garde-fou en code plutôt qu'un prompt** : deux épisodes le même jour (Bordeaux instable après resserrement de `comparaison_etablissements_nommes`/`non_reconnu`, cf. S8.9) ont montré qu'une modification de prompt sur une catégorie peut déstabiliser une autre catégorie de façon imprévisible. Un garde-fou en code, borné à une condition précise (`categorie == question_methodologique AND zone_geo is None AND mot superlatif`), ne peut affecter que ce cas exact.

**Conséquence** : `test_router_classification.py` étendu à 11 cas (4 cas limites ajoutés pour la batterie de tests de l'agent). 11/11 validés, y compris re-vérification manuelle de la variante "pire" et de l'absence de faux positif sur une vraie question conceptuelle contenant "classement".

## S8.14 — Batterie de tests de l'agent ReAct : résolution de noms fiable, tri VA/score, tableaux d'agrégation, transparence temporelle

**Contexte** : construction d'une batterie de tests dédiée (`test_agent_react.py`) pour l'agent ReAct — jugé le point le plus sensible du router (pas de séquence d'outils fixe). Plusieurs problèmes réels découverts en creusant, tous corrigés dans la foulée (pas différés — nouvelle règle de méthode actée cette session : chercher une solution directe sur un défaut trouvé en cours de route, sauf si disproportionné).

**Problème 1 — Text-to-SQL perd le nom d'un établissement nommé** : "Trouve les résultats du Collège Chevreul..." générait `WHERE e.nom IN ('Chevreul', ...)` (égalité exacte, sans le préfixe "Collège") → 0 résultat alors que l'établissement existe. Même classe de problème que celui corrigé le matin sur `rechercher_etablissements_par_nom`, mais sur un chemin de code différent (Text-to-SQL général, pas la fonction dédiée).

**Décision** : plutôt que de complexifier encore le prompt Text-to-SQL (risque de régression déjà observé 2 fois ce jour sur le prompt du router), nouvel outil pour l'agent — `rechercher_etablissement_par_nom` (réutilise la fonction déjà durcie le matin) — et `recherche_sql` étendu pour accepter un `uai_filtre` côté agent. L'agent résout maintenant le nom en UAI fiable AVANT d'interroger les données, au lieu de laisser le Text-to-SQL deviner nom + zone + dates en une seule requête libre (la vraie cause de fragilité : trop de contraintes combinées dans un seul appel LLM).

**Problème 2 — Session par défaut codée en dur et incohérente avec l'exemple du prompt** : `SCHEMA_PROMPT` disait "2025, sinon 2024" mais l'exemple few-shot utilisait `s.session = '2024'` — contradiction interne, l'exemple l'emportant en pratique. Décision : `s.session = (SELECT MAX(session) FROM scores)` en sous-requête, plus jamais d'année en dur. Itération : la première version de la règle ("toujours filtrer sauf si plusieurs années demandées") a fait disparaître le filtre de session sur une requête d'agrégation sans année précisée (mélange de 2022-2025) — resserrée pour explicitement interdire l'absence de filtre de session, y compris sans année précisée dans la question.

**Problème 3 — Tri par VA au lieu du score composite** : "le meilleur collège... en tenant compte de la valeur ajoutée" triait sur `brevet_va_taux_reussite_general` au lieu de `score_principal` — contredit une décision actée depuis la phase 1 (S1.3 : VA en badge, jamais critère de tri). Règle ajoutée au `SCHEMA_PROMPT`, avec exemple correct/incorrect explicite. Nuance validée avec l'utilisateur : le tri par VA reste légitime si la question le demande *littéralement* ("quel collège a la meilleure VA"), seulement pas quand la VA est mentionnée comme facteur secondaire d'un "meilleur collège" général.

**Problème 4 — Extraction de noms bloquée par une condition circulaire** : le champ `noms_etablissements` du schéma d'extraction du router était documenté "pertinent seulement si categorie=comparaison_etablissements_nommes" — un établissement nommé dans une question qui n'est pas perçue comme une "comparaison" (ex: évolution d'UN SEUL collège sur plusieurs années) ne déclenchait pas cette catégorie, donc le nom n'était jamais extrait, donc rien ne pouvait rattraper l'incohérence. Décision : condition retirée de la description du schéma (extraction inconditionnelle) + garde-fou déterministe symétrique au premier (S8.13) : noms extraits mais catégorie différente de comparaison_etablissements_nommes -> bascule forcée vers cette catégorie, pour toujours passer par la résolution de nom fiable.

**Problème 5 — Template de synthèse cassé sur un résultat d'agrégation** : `noeud_synthese` suppose toujours la forme "une ligne = un établissement" (nom/secteur/score_principal...) ; une requête d'agrégation (AVG, COUNT) ne retourne qu'une valeur calculée, sans ces colonnes -> tableau rempli de "?". Confirmé plus large que prévu : touche aussi le chemin géo dès qu'un secteur est précisé avec une question d'agrégation, pas seulement les établissements nommés.

**Décision** : `_generer_tableau_depuis_lignes` détecte la forme des données (`"nom" not in lignes[0]`) et bascule vers `_generer_tableau_generique` (colonnes réellement présentes) au lieu d'appliquer le template à colonnes fixes. Détection de la présence de VA/score corrigée au passage : vérifiait auparavant tout l'objet sérialisé (y compris le texte SQL, qui contient littéralement "score_principal" dans `AVG(s.score_principal)` même quand la colonne résultat s'appelle "moyenne_score") plutôt que les vraies clés des lignes — nouvelle fonction `_lignes_contiennent()`.

**Problème 6 — Aucune transparence sur la profondeur historique réelle** : "moyenne sur les 10 dernières années" ne plante pas (LIMIT sur une liste de 4 sessions renvoie simplement les 4 disponibles) mais ne signale jamais l'écart entre ce qui est demandé et ce qui existe. Vérifié empiriquement : seulement 4 sessions en base (2022-2025, pas depuis 2003 comme supposé initialement) ; VA renseignée dès la première session disponible (2022), pas depuis 2023 comme supposé.

**Décision** : `recherche_sql` retourne désormais `sessions_disponibles` (calculé en Python, déterministe). `_generer_tableau_generique` ajoute une note factuelle ("Calculé sur les N années disponibles : ...") chaque fois qu'un tableau d'agrégation s'affiche. Note de méthode : la première version de ce fix ciblait uniquement le prompt de l'agent, mais le problème 4 a changé le routage de ce cas précis vers le chemin déterministe — fix étendu pour s'appliquer aux deux chemins.

**Conséquence** : `graph_router.py`, `agent/tools/sql_tool.py`, `prompts/agent_react_system_prompt.py`, nouveau fichier `test_agent_react.py`. Re-validé intégralement après chaque changement : `test_router_classification.py` (11/11), `test_agent_react.py` (batterie complète), cas Bordeaux/méthodologique/comparaison de noms standard (non-régression confirmée).

## S8.15 — Correction de l'ordre chronologique du journal (S8.7 déplacée)

**Problème découvert en documentant S8.14** : l'entrée S8.7 s'était retrouvée en fin de fichier au lieu de sa place chronologique entre S8.6 et S8.8, suite à une erreur d'édition dans une session précédente — jamais remarqué depuis, découvert en cherchant où insérer une nouvelle entrée.

**Décision** : contenu déplacé à sa place correcte, pas de contenu perdu ni modifié — uniquement un problème d'ordre dans le fichier.

## S8.16 — `e.secteur` parfois absent du SELECT Text-to-SQL : risque réel sur l'avertissement secteur privé

**Problème signalé par l'utilisateur, initialement sous-évalué par l'assistant** : la colonne "Secteur" d'un tableau généré par l'agent affichait "?" dans un cas réel. Écarté à tort comme "cosmétique" — corrigé après que l'utilisateur a fait remarquer que ce n'en est pas un.

**Impact réel identifié en y regardant** : `e.secteur` n'était jamais une colonne obligatoire dans `SCHEMA_PROMPT` (contrairement à `e.uai`, déjà marqué "TOUJOURS inclure"). Une ligne d'établissement sans ce champ fait échouer silencieusement `_etablissement_prive_present()` (`row.get("secteur") == Secteur.PRIVE` sur un champ absent renvoie toujours faux) — risque concret de ne pas afficher l'avertissement sur la sélection à l'entrée du privé pour un établissement réellement privé.

**Décision** :
- Règle ajoutée à `SCHEMA_PROMPT`, avec la même formulation forte que la règle déjà existante sur `e.uai` : "TOUJOURS inclure e.secteur... dès que la requête retourne des lignes d'établissement".
- Défense supplémentaire en code (pas seulement dans le prompt, cohérent avec la méthode de la session) : `_etablissement_prive_present()` traite maintenant une ligne d'établissement (qui a un "nom") sans champ "secteur" comme potentiellement privée par défaut plutôt que de l'ignorer — mieux vaut un avertissement affiché à tort qu'un avertissement de sécurité manquant à tort. Explicitement exclu des lignes d'agrégation (sans "nom"), qui n'ont jamais de secteur par nature et ne doivent pas déclencher l'avertissement.

**Conséquence** : validé sur 3 exécutions consécutives (`e.secteur` toujours présent), et vérifié qu'aucun faux positif n'apparaît sur les résultats d'agrégation ni de régression sur le split public/privé déjà validé. Rappel de méthode retenu : un défaut affectant l'affichage d'un avertissement de sécurité n'est jamais "cosmétique", même s'il ressemble à un détail de présentation au premier regard.

## S8.17 — Fonction déterministe pour l'évolution multi-années d'établissements nommés

**Contexte** : suite à la discussion sur la latence et la fiabilité du Text-to-SQL pour les questions multi-années (cf. S8.14), décision de construire une fonction dédiée pour le cas concrètement rencontré et cassé ce jour — évolution/moyenne d'un ou plusieurs établissements **nommés** sur plusieurs sessions. Le cas "géo + agrégation sur une zone large" (ex: moyenne de tous les collèges publics d'une ville) est explicitement laissé de côté pour une session future — périmètre plus flou, pas de fragilité constatée à ce jour sur ce cas précis après le renforcement du Text-to-SQL en S8.14.

**Décision** : nouvelle fonction déterministe `obtenir_evolution_etablissements()` (aucun appel LLM) — retourne une ligne par (établissement, session) pour une liste d'UAI déjà résolue. Nouveau signal extrait par le router (même appel fusionné que les autres) : `evolution_demandee`. Dans `noeud_sql`, sur le chemin `comparaison_etablissements_nommes` avec noms déjà résolus, ce signal déclenche la nouvelle fonction plutôt que le Text-to-SQL général.

**Gain mesuré** : ~2.04s (Text-to-SQL, appel LLM) contre ~0.01s (fonction déterministe) sur une requête équivalente — facteur ~200x sur cette étape, ~45% de réduction du temps total sur les chemins déterministes concernés (pas sur le chemin agent, où le goulot d'étranglement est ailleurs).

**Affichage** : `noeud_synthese` affiche désormais une colonne "Session" quand elle est présente dans les données (absente sur le tableau standard un-seul-an), plus une note de transparence sur le nombre d'années réellement disponibles en base (réutilise `sessions_disponibles`, cf. S8.14).

**Itération sur la moyenne** : la première version affichait seulement le détail année par année, sans moyenne chiffrée — corrigé après retour explicite de l'utilisateur ("si on demande une moyenne, il faut afficher une moyenne, sinon ça sert à rien"). Nouvelle fonction `_generer_moyennes_par_etablissement()` : moyennes de score/taux/note calculées séparément (jamais mélangées en un seul chiffre composite), groupées par établissement (jamais mélangées entre deux établissements différents comparés ensemble), affichées avant le tableau de détail. La VA n'est volontairement jamais moyennée — c'est un badge catégoriel (positif/neutre/négatif), pas une valeur continue.

**Conséquence** : `agent/tools/sql_tool.py`, `graph_router.py`, `prompts/router_system_prompt.py`. Validé sur les deux cas concrets ayant motivé cette fonction (évolution 3 ans, moyenne 10 ans de Collège Chevreul à Lyon) et re-confirmé sans régression sur `test_router_classification.py` (11/11), la comparaison de noms standard et le split public/privé.

## S8.18 — Fonction déterministe pour la moyenne/agrégation sur une zone géographique

**Contexte** : deuxième volet annoncé en S8.17 — "géo + agrégation" (ex: moyenne du score de tous les collèges publics d'une ville), cette fois traité dans la foulée plutôt que reporté, à la demande explicite de l'utilisateur.

**Décision** :
- Nouvelle fonction déterministe `calculer_moyenne_etablissements()` (aucun appel LLM) — calcule TOUJOURS 3 jeux de statistiques (globale tous secteurs confondus, publique, privée) pour un ensemble d'établissements déjà présélectionné par géolocalisation, sur la session la plus récente. Pas de tableau détaillé par établissement pour ce cas : c'est une agrégation statistique, pas une liste.
- Détection déterministe par mot-clé ("moyenne(s)") sur la question, même principe que `_MOTS_SUPERLATIFS` (S8.13) — pas un champ de plus extrait par le LLM du router.
- Affichage conditionné à `secteur_souhaite` : si un secteur est précisé, seule sa moyenne s'affiche. Sinon (question vague, ex: "moyenne des collèges de Nantes"), la moyenne globale s'affiche en premier, puis le détail public/privé en complément — décision de l'utilisateur, corrigeant la proposition initiale de l'assistant (secteurs séparés uniquement) : "si la demande [porte] sur un secteur ou une ville... on doit faire la moyenne des deux en premier, [...] la moyenne publique et privée ensuite". Justifié empiriquement : moyenne globale à Lyon 74.9, mais publique 68.0 et privée 89.2 — la moyenne seule masque un écart réel.

**Bug de routage trouvé en testant, même famille que S8.13** : "moyenne des collèges publics à Lyon" (zone détectée) tombait quand même en `question_methodologique` au lieu de `recherche_geo_classement`. Nouveau garde-fou déterministe symétrique à celui de S8.13, cette fois sur zone détectée + mot-clé "moyenne" → bascule vers `recherche_geo_classement`.

**Deuxième bug trouvé en testant** : l'avertissement sur le secteur privé s'affichait même quand seul le secteur public était montré à l'écran (les stats "privé" sont toujours calculées en interne par la fonction, même non affichées). `_etablissement_prive_present()` et `_ajouter_nuance_privee_si_besoin()` étendues pour recevoir `secteur_souhaite` et ne déclencher l'avertissement que si une donnée privée est réellement affichée, pas seulement calculée.

**Conséquence** : `agent/tools/sql_tool.py`, `graph_router.py`. Validé sur les 2 cas (secteur précisé, secteur indifférent) + non-régression complète (classification 11/11, évolution nommée, split Bordeaux, question méthodologique pure, avertissement privé correct dans les 4 configurations de secteur).

## S8.19 — Routage et robustesse de l'agent sur les questions multi-zones

**Contexte** : test explicite demandé par l'utilisateur sur des cas extrêmes multi-zones ("moyenne à Lyon, Perpignan et Poitiers"), pour trancher un débat de fond — construire une capacité déterministe multi-zones, ou laisser l'agent gérer avec ses outils existants ?

**Décision de principe** : ne pas construire de déterminisme multi-zones dédié. L'espace combinatoire (N zones × secteur × années × noms mélangés...) grossirait vite et referait à la main ce pour quoi l'agent existe (S1.5). Contrairement aux cas "1 nom + évolution" et "1 zone + agrégation" (S8.17/S8.18), aucune fragilité constatée ne justifiait cet investissement pour le cas multi-zones — seule la fréquence réelle était une hypothèse, jamais vérifiée.

**Bug de routage trouvé et corrigé** : une question à plusieurs zones ("Lyon, Perpignan, Poitiers") était extraite comme une seule chaîne de zone combinée, échouant systématiquement au géocodage (une seule adresse attendue) — échec silencieux vers `clarification_geo`, pas d'aide réelle. Garde-fou déterministe : zone contenant une virgule → bascule vers `non_reconnu` (agent), qui peut appeler `recherche_geo` séparément par zone.

**Découverte critique en testant ce nouveau routage** : l'agent plantait avec un timeout réel (`openai.APITimeoutError`, exception non gérée remontant jusqu'à l'utilisateur) sur 3 zones. Cause identifiée : `recherche_geo` retournait à l'agent le détail complet et non filtré de chaque établissement trouvé (36 Ko de JSON pour Lyon seul), jamais allégé contrairement au chemin déterministe (`_tronquer_resultats_geo`, déjà en place depuis les phases 1-2). Le contexte de conversation dépassait 57 Ko avant même le 2e tour.

**Décision** :
- Nouvelle fonction `_resultat_geo_pour_agent()` : ne renvoie à l'agent que les UAI + un résumé, jamais le détail individuel — même principe que `_tronquer_resultats_geo` côté déterministe.
- Nouvel outil `calculer_moyenne` exposé à l'agent (appelle directement `calculer_moyenne_etablissements`, S8.18) — évite de faire deviner une agrégation par le Text-to-SQL général à chaque zone.
- **Résultat mesuré** : 3 zones passe de "plantage" à 24.5s, résultat complet et correct. 5 zones reste en échec (timeout à 96s au lieu d'un plantage quasi instantané) — amélioration nette mais pas totale.

**Garde-fou final, à la demande de l'utilisateur** : `MAX_ZONES_COMPAREES = 3` (config.py). Au-delà, `noeud_agent_react` bloque immédiatement (avant tout appel LLM) avec un message explicite invitant à reformuler — évite de payer le coût et la latence d'une tentative vouée à l'échec au-delà de la limite mesurée empiriquement.

**Conséquence** : `config.py`, `graph_router.py`, `prompts/agent_react_system_prompt.py`. Validé sur 3 zones (fonctionne, 23-25s), 5 zones (bloqué en 2.5s, message clair), et non-régression complète (classification 11/11, hors-sujet, comparaison 2 zones, moyenne 1 zone).

## S8.20 — Cahier de test end-to-end consolidé + bug "pire" trouvé et corrigé

**Contexte** : cahier de test consolidé (`test_e2e_complet.py`, 22 cas — tous les chemins déterministes et variantes construits pendant la session, plus une série de cas limites/questions bancales demandée explicitement par l'utilisateur). 22/22 sans exception levée, mais relecture qualitative (pas juste "pas de crash") ayant révélé un bug réel, trompeur.

**Bug trouvé** : "Quels sont les pires collèges publics à Lyon ?" affichait bien les données correctes (scores les plus bas de la zone) mais avec le texte "Voici les X présentant les **meilleurs** résultats" — activement trompeur, pas juste imprécis. Cause : `_generer_intro_template()` est un texte figé, indifférent au sens réel du tri effectué par le Text-to-SQL.

**Bug plus grave trouvé en creusant** : le chemin split (`rechercher_top_par_secteur`, utilisé quand aucun secteur n'est précisé, cf. S8.8) n'avait **aucune option de tri ascendant** — une demande "pires collèges de Lyon" sans secteur précisé aurait donc affiché les MEILLEURS établissements (mauvaises données, pas juste un mauvais texte).

**Décision** :
- `rechercher_top_par_secteur()` accepte désormais un paramètre `ordre` ("DESC"/"ASC", validé strictement avant interpolation SQL).
- Détection déterministe `_MOTS_PIRE` (sous-ensemble de `_MOTS_SUPERLATIFS`) — bascule l'ordre du split et adapte le texte d'intro dans les deux chemins (Text-to-SQL et split).
- Règle explicite "pire/moins bon → ORDER BY score_principal ASC" ajoutée au `SCHEMA_PROMPT` du Text-to-SQL (même si son tri ASC pour "pire" s'est révélé fiable sans cette règle sur 3 essais — ajoutée pour la robustesse et la documentation, pas pour corriger un défaut observé).

**Deuxième trou identifié, non corrigé (documenté)** : "Comment ont évolué les résultats des collèges de Lyon sur les 3 dernières années ?" (géo + évolution, SANS nom d'établissement) est silencieusement traité comme une question de classement standard (année en cours) — la demande d'évolution est ignorée sans aucun signal à l'utilisateur. On avait construit l'évolution seulement pour un établissement nommé (S8.17) ; jamais pour une zone géographique entière. Plan de résolution à discuter séparément.

**Conséquence** : `agent/tools/sql_tool.py`, `graph_router.py`, nouveau fichier `test_e2e_complet.py`. Re-validé sur les 2 cas "pire" (secteur précisé et split) + non-régression complète (classification 11/11, cas "meilleurs" standards, split Bordeaux).

## S8.21 — Détection "pire"/"moyenne" déplacée du mot-clé en dur vers l'extraction LLM

**Contexte** : remarque de l'utilisateur après S8.20 — `_MOTS_PIRE` (regex `\bpires?\b`) ne couvre que le mot littéral "pire". Une question formulée avec un synonyme ("le plus mauvais", "en difficulté", "moins performant") ne serait jamais détectée. Même limite pour `_MOTS_AGREGATION` ("moyenne" seul, rate "en général", "globalement", "dans l'ensemble").

**Décision** : remplacer ces deux regex par deux nouveaux champs extraits par le LLM du router, dans le même appel fusionné que les champs existants (secteur_souhaite, nuance_methodologique_demandee, evolution_demandee) — donc sans latence supplémentaire :
- `ordre_souhaite` (enum "meilleur"/"pire"/"indifferent", nouveau `OrdreSouhaite` dans config.py) — remplace `_MOTS_SUPERLATIFS`/`_MOTS_PIRE`.
- `agregation_demandee` (booléen) — remplace `_MOTS_AGREGATION`.

**Pourquoi le LLM plutôt qu'une liste de mots-clés plus longue** : une liste de synonymes ne serait jamais exhaustive (nouvelle formulation = nouveau trou). Le LLM comprend nativement les reformulations. Contrairement aux régressions de prompt observées ailleurs cette session (modifications de la DESCRIPTION des catégories, avec effets de bord imprévisibles sur d'autres catégories), ceci est un champ additif dans le même schéma déjà validé — risque jugé plus faible, mais testé avec la même rigueur.

**Validation** : extraction vérifiée directement sur des synonymes non couverts par l'ancienne regex — "les plus mauvais" → pire, "en difficulté" → pire, "globalement"/"en général" → agregation_demandee=true — tous corrects et propagés jusqu'à la réponse finale. Suite complète re-passée : classification 11/11, cahier de test end-to-end 22/22 sans régression (y compris le fix "pire" de S8.20, toujours correct).

**Conséquence** : `config.py` (nouvel enum `OrdreSouhaite`), `graph_router.py` (suppression des 3 regex, ajout des 2 champs, module `re` retiré car plus utilisé), `prompts/router_system_prompt.py`.

## S8.22 — Évolution multi-années sur une zone géographique (sans nom d'établissement)

**Contexte** : deuxième trou identifié en S8.20 — "comment ont évolué les résultats des collèges de Lyon sur les 3 dernières années ?" (zone géo, pas de nom) était silencieusement traité comme une question de classement/agrégation sur la seule session la plus récente, sans aucun signal indiquant que la demande d'évolution avait été ignorée.

**Pourquoi pas la même fonction que pour un établissement nommé (S8.17)** : `obtenir_evolution_etablissements` produit une ligne par (établissement, session) — viable pour 1-3 noms, illisible pour une zone entière (ex: 104 établissements x 4 sessions = 416 lignes). La bonne unité ici est l'évolution de la MOYENNE de la zone, peu importe son nombre d'établissements.

**Décision** :
- Nouvelle fonction déterministe `calculer_evolution_moyenne_zone()` (sql_tool.py) — même logique de calcul que `calculer_moyenne_etablissements` (S8.18), répétée pour chaque session au lieu de la seule la plus récente.
- Déclenchée dans `noeud_sql` sur `evolution_demandee=true` (chemin géo, pas de nom résolu), **avant** l'agrégation simple : une évolution est elle-même une forme d'agrégation, par année plutôt que sur une session unique.
- Affichage : un tableau par secteur (Session | Score moyen | Taux moyen | Note moyenne), respectant `secteur_souhaite` (un seul tableau si précisé, trois — global/public/privé — sinon), même principe que S8.18. Intro précisant explicitement le nombre d'années réellement disponibles en base, même logique de transparence que l'évolution nommée (S8.17).

**Validation** : testé secteur précisé et indifférent, avertissement secteur privé correct dans les deux cas (absent si secteur=public, présent sinon). Suite complète re-passée sans régression : classification 11/11, cahier de test end-to-end 22/22 — y compris le cas qui avait motivé ce chantier, qui affiche désormais une vraie tendance par année au lieu d'une vue figée sur l'année en cours.

**Point observé, non corrigé (documenté)** : un cas de test annexe ("Compare le collège Victor Hugo à Paris et à Lyon") est passé du chemin agent au chemin déterministe entre deux exécutions, à cause d'une extraction de zone "Paris et Lyon" (avec "et") au lieu de "Paris, Lyon" (avec virgule) — le garde-fou multi-zones (S8.19) ne détecte que les virgules. Résultat toujours sûr (demande de clarification, pas de donnée fausse), mais moins satisfaisant que le traitement par l'agent. Même famille de fragilité que le bug "pire" (S8.20/S8.21) mais sur l'extraction de zone plutôt que le tri — chantier séparé, non traité ici (cas très marginal, question artificiellement construite pour les tests).

**Conséquence** : `agent/tools/sql_tool.py` (nouvelle fonction), `graph_router.py` (branchement + 3 nouvelles fonctions de template).

## S8.23 — L'agent invente parfois une méthodologie non fondée sur les données reçues

**Contexte** : rapport visuel du cahier de test (Artifact, demandé par l'utilisateur pour voir tous les rendus) — en le relisant, l'utilisateur a repéré que le cas "Agent : 2 zones" affirmait "basée sur les résultats des trois dernières années" alors que la question ne mentionnait aucune période, et sans savoir quel score avait réellement été retenu.

**Diagnostic** : reproduction pas à pas, tour par tour. Le SQL réellement généré par `recherche_sql` pour "meilleur collège à Lyon" filtre sur `s.session = (SELECT MAX(session) FROM scores) LIMIT 1` — une seule année, la plus récente, aucune moyenne multi-années. Le `SELECT` n'incluait même pas la colonne `session`. En relançant la même question, la réponse ne contenait plus cette affirmation — confirme que c'est une invention du LLM au moment de la synthèse, pas un calcul multi-années caché : l'agent n'avait tout simplement aucune donnée sur la période et a comblé le vide par une formulation plausible mais fausse.

**Tentative de fix par le prompt, jugée insuffisante** : ajout d'une règle dans `SCHEMA_PROMPT` ("TOUJOURS inclure s.session dans le SELECT") — testée sur 4 essais indépendants, suivie 0 fois sur 4. Contrairement à la règle "pire → ASC" (S8.20, fiable sans même de règle explicite), cette règle n'est pas naturellement suivie par le Text-to-SQL. Règle retirée du prompt (inutile, alourdit sans bénéfice mesuré).

**Décision** : plutôt que de dépendre de la fiabilité du LLM sur ce point, `recherche_sql()` calcule et retourne désormais un champ `session_utilisee` déterministe (MAX des sessions disponibles, calculé en Python, indépendamment de ce que le SQL généré sélectionne réellement) — même principe que `session_utilisee` déjà présent dans `rechercher_top_par_secteur`/`calculer_moyenne_etablissements`. Règle ajoutée dans `AGENT_REACT_SYSTEM_PROMPT` : ne jamais affirmer une période/méthodologie non confirmée par `session_utilisee`/`sessions_disponibles`. `tableau_formate` (utilisé par l'agent) préfixé automatiquement d'une mention de session déterministe, pour ne pas dépendre uniquement du respect de cette règle par le LLM au moment de rédiger.

**Validation** : reproduit 2 fois après le fix, aucune affirmation non fondée dans les deux cas. Pas une garantie à 100% (LLM non parfaitement déterministe même à température 0), mais la cause structurelle (absence de donnée pour se fonder) est éliminée.

**Conséquence** : `agent/tools/sql_tool.py` (`session_utilisee` déterministe), `graph_router.py` (`tableau_formate` enrichi), `prompts/agent_react_system_prompt.py`.

## S8.24 — Transparence sur la session utilisée étendue à tous les chemins déterministes

**Contexte** : en creusant S8.23, l'utilisateur a signalé que le même trou existait sur les chemins 100% déterministes (pas seulement l'agent) — ex: "Quels sont les pires collèges publics à Lyon ?" affiche un tableau sans jamais dire de quelle année il s'agit.

**Constat en auditant systématiquement** : `session_utilisee` (ou `sessions_disponibles`) était déjà calculé déterministiquement dans TOUTES les fonctions sous-jacentes (`recherche_sql`, `rechercher_top_par_secteur`, `calculer_moyenne_etablissements`) — mais seules les fonctions d'intro des chemins évolution (S8.17/S8.22) le faisaient réellement apparaître dans le texte affiché. Les 3 autres (classement standard, split public/privé, agrégation simple) ignoraient complètement cette donnée pourtant déjà disponible.

**Décision** : nouveau helper `_mention_session(session_utilisee)` — fragment de phrase (" (données de la session la plus récente : 2025)") réutilisé par les 3 fonctions d'intro concernées (`_generer_intro_template`, `_generer_intro_split_template`, `_generer_intro_agregation_template`), alimenté par le `session_utilisee` déjà présent dans `resultats_sql` pour chaque forme. Aucun nouveau calcul : seulement la donnée déjà là, enfin affichée.

**Validation** : vérifié sur les 4 chemins concernés (pire/secteur précisé, split, agrégation, comparaison de noms standard) — mention présente et correcte dans les 3 qui aboutissent, non-régression complète (classification 11/11, cahier e2e 22/22).

**Conséquence** : `graph_router.py` uniquement (nouveau helper + 3 signatures de fonction + câblage dans `_preparer_affichage_resultats`).

## S8.25 — Centralisation de la mention de session + garde-fou structurel

**Contexte** : discussion de fond après S8.24. La mention de session ajoutée en S8.24 était "opt-in" — chacune des 3 fonctions d'intro devait individuellement recevoir le paramètre `session_utilisee` ET penser à l'insérer dans sa phrase. L'utilisateur a fait remarquer que ce n'est pas juste un oubli ponctuel possible mais un vrai problème structurel : rien n'empêche une future fonction d'oublier ce câblage, et rien ne le signalerait.

**Option écartée, explicitement déconseillée** : remplacer les dictionnaires de résultats par une structure typée stricte (dataclass/TypedDict) forçant la présence du champ à la compilation. Refusée pour disproportion : toucherait tous les points d'accès `.get(...)` dans `sql_tool.py` et `graph_router.py`, un vrai refactor à risque de régression, pour un projet qui n'a pas la taille justifiant ce niveau d'infrastructure. Point technique clarifié à l'utilisateur : un `TypedDict` seul n'aurait de toute façon rien vérifié à l'exécution (seulement pour un outil d'analyse statique comme mypy) — ne donne pas la garantie "l'oubli fait planter le code" sans un mécanisme de vérification actif en plus.

**Décision retenue (proportionnée)** :
- La mention de session n'est plus construite par les 3 fonctions d'intro individuellement (revert du paramètre ajouté en S8.24) — elle est ajoutée une seule fois, après coup, dans `_preparer_affichage_resultats` (le point d'orchestration déjà existant), après que tableau/intro ont été produits par la branche appropriée.
- Garde-fou (`assert`) au même endroit : si `resultats_sql["success"]` est vrai mais qu'il ne contient ni `session_utilisee` ni `sessions_disponibles`, le code lève immédiatement une erreur explicite plutôt que de laisser passer un trou de transparence en silence.
- Corrigé au passage : le retour anticipé de `noeud_sql` pour une zone sans aucun établissement (`uai_filtre` vide) ne suivait pas la convention (`session_utilisee` absent du dict, pas même `None`) — aurait fait échouer le nouveau garde-fou à tort ; harmonisé.

**Bénéfice concret** : une future 5ᵉ fonction de recherche n'a plus besoin d'un câblage spécifique dans les fonctions d'intro pour que la mention apparaisse — il suffit que sa fonction SQL sous-jacente respecte la convention déjà établie (`session_utilisee` ou `sessions_disponibles` toujours présent, même à `None`/vide). Si elle l'oublie, le garde-fou le signale immédiatement au lieu d'un trou silencieux.

**Validation** : garde-fou testé directement (lève bien une `AssertionError` sur un dict volontairement incomplet). Suite complète re-passée sans régression : classification 11/11, cahier e2e 22/22 — le garde-fou ne s'est déclenché sur aucun des 22 cas réels, confirmant que les 6 chemins qui produisent `resultats_sql` respectent tous la convention.

**Conséquence** : `graph_router.py` (`_preparer_affichage_resultats` restructurée, 3 fonctions d'intro simplifiées, `noeud_sql` harmonisé).

## S8.26 — Corrections issues de la relecture qualitative du rapport visuel (lots A+B)

**Contexte** : relecture ligne par ligne du rapport visuel du cahier de test par l'utilisateur — a fait remonter 11 points distincts. Traités en deux lots (A : formulation peu risquée, B : vrais bugs), le reste (C) discuté séparément.

**Lot A** :
- En-tête de tableau "VA" → "Valeur ajoutée" (plus explicite qu'une abréviation à faire deviner en bas de tableau).
- Évolution multi-années sur zone géo (`calculer_evolution_moyenne_zone`, S8.22) : ordre inversé pour afficher l'année la plus récente en premier (la version nommée, S8.17, le faisait déjà correctement via `ORDER BY session DESC`).

**Lot B — bug confirmé** : pour "compare le **meilleur** collège de Lyon et de Marseille", l'agent appelait `calculer_moyenne` (moyenne de tous les établissements de la zone) au lieu de chercher LE meilleur établissement — régression introduite en donnant cet outil à l'agent (S8.19), avec une description trop large. Confirmé en retraçant l'appel pas à pas : `calculer_moyenne` appelé avec la liste complète des UAI de la zone au lieu de `recherche_sql` avec un tri + LIMIT 1. Corrigé en ajoutant une distinction explicite ("meilleur"/"pire" ≠ moyenne) à la fois dans la description de l'outil (schéma) et dans le prompt système de l'agent.

**Lot B — cadrage du périmètre** : deux réponses de l'agent laissaient penser à un périmètre plus large que la réalité — "je peux vous aider à trouver des données pertinentes" (sur une question hors de France) et "pour vous aider à choisir un collège" (sur une question quasi vide). Le prompt système de l'agent est réécrit dès sa première phrase : l'app fournit de l'information factuelle sur les collèges de France, elle n'accompagne pas un choix ni ne donne de recommandation. Deux règles explicites ajoutées (périmètre géographique France uniquement, jamais "aider à choisir").

**Validation** : chaque fix testé isolément puis suite complète (classification 11/11, cahier e2e 22/22) à plusieurs reprises sans régression.

**Conséquence** : `graph_router.py` (en-tête tableau), `agent/tools/sql_tool.py` (ordre évolution géo), `prompts/agent_react_system_prompt.py` (reformulation + 2 nouvelles règles), schéma de l'outil `calculer_moyenne`.

## S8.27 — Recherche déterministe par région/département

**Contexte** : question ouverte de l'utilisateur ("que se passe-t-il si on met une région ?") — testée, révèle un vrai problème : `recherche_geo("Bretagne")` renvoie succès, mais géocode vers une rue à Denain (Nord), à l'autre bout de la France. Aucune erreur, résultats silencieusement faux.

**Décision** : la table `etablissements` contient déjà `libelle_region`/`code_departement`/`libelle_departement` — pas besoin de construire une correspondance région↔département nous-mêmes. Nouvelle fonction `resoudre_zone_administrative()` (sql_tool.py) : détecte si la zone extraite par le router est une région/département (nom actuel, tolérant aux tirets/accents/casse et aux fautes de frappe via `difflib`, ensemble volontairement restreint à ~30 noms connus pour une tolérance fiable) plutôt qu'une ville — et si oui, requête directe sur nos propres colonnes, aucun appel à l'API de géocodage.

**Anciennes régions (réforme 2016)** : table figée `REGIONS_HERITEES` (Midi-Pyrénées → Occitanie, Nord-Pas-de-Calais → Hauts-de-France, etc.) — encore couramment utilisées, fait historique stable.

**Effet de bord positif découvert en testant** : "Paris" est désormais résolu comme département 75 (ville exacte) plutôt que ville+rayon 10km (qui débordait sur la petite couronne) — 229 établissements au lieu de 496.

**Validation** : batterie de variantes (tirets/espaces, casse, faute de frappe, ancien nom, faux positifs sur des noms de villes) toutes correctes ; non-régression complète (classification 11/11, cahier e2e 22/22).

**Conséquence** : `agent/tools/sql_tool.py` (résolution), `agent/tools/geo_tool.py` (`rechercher_etablissements_region_departement`), `graph_router.py` (`noeud_geo`).

## S8.28 — Recherche par ville : commune exacte plutôt que rayon arbitraire

**Contexte** : discussion sur le rayon de 10km par défaut — l'utilisateur soulevait le risque qu'un rayon fixe rate des établissements en périphérie d'une grande ville comme Toulouse.

**Vérifié empiriquement avant de conclure** : rayon 10km actuel vs commune exacte — Toulouse 78 vs 50, Marseille 113 vs 92. Dans les deux cas le rayon actuel trouve PLUS d'établissements, pas moins : il déborde sur les communes voisines plutôt que de rater des établissements. Le vrai sujet n'était donc pas un risque d'incomplétude mais un choix de définition ("collèges à Toulouse" = la commune, ou commune + périphérie ?).

**Décision** : l'API de géocodage renvoie déjà `"type": "municipality"` quand la question ne contient qu'un nom de ville (pas une adresse précise), avec le nom de commune et le code département pour désambiguïser les homonymes. Nouvelle fonction `trouver_etablissements_par_commune()` : correspondance exacte sur `commune` + `code_departement`, sans rayon. Une adresse précise (type != "municipality") garde le comportement par rayon inchangé — pertinent dans ce cas.

**Changement d'ampleur variable selon la ville, signalé avant validation finale** : Toulouse 78→50, Marseille 113→92, mais **Lyon 145→44** (~70%) — la commune de Lyon est petite et dense, entourée de communes proches (Villeurbanne, Vénissieux...) auparavant incluses dans le rayon. Confirmé comme comportement voulu par l'utilisateur avant de poursuivre.

**Validation** : ville seule (pas de rayon) vs adresse précise (rayon conservé) vs code postal, testés séparément ; tolérance aux fautes de frappe toujours fonctionnelle (le "type: municipality" de l'API BAN résout aussi "Lyeon" en "Lyon") ; non-régression complète (classification 11/11, cahier e2e 22/22).

**Conséquence** : `agent/tools/geo_tool.py` (`geocoder` enrichi de city/depcode, `trouver_etablissements_par_commune`, branchement dans `recherche_geo`).

## S8.29 — Respecter le nombre exact d'années demandé sur une évolution

**Contexte** : point C restant — "compare sur les 3 dernières années" affichait toujours les 4 années disponibles en base, sans respecter le "3" demandé littéralement.

**Décision** : nouveau champ `nb_annees_demandees` extrait par le router (même appel LLM fusionné que les autres signaux) — nombre exact si la question en précise un, sinon 0 (toutes les années disponibles, comportement inchangé). Câblé dans le paramètre `n_sessions`, déjà existant mais jusqu'ici jamais utilisé, des deux fonctions d'évolution (`obtenir_evolution_etablissements` S8.17, `calculer_evolution_moyenne_zone` S8.22).

**Bug de transparence trouvé en implémentant** : le texte d'accompagnement ("*Sur les 4 années disponibles en base...*") utilisait `sessions_disponibles` (TOUJOURS toutes les années en base), pas ce qui est réellement affiché — aurait affiché "4 années disponibles" même quand seules 3 sont montrées suite à la demande. Corrigé en dérivant le texte des sessions réellement présentes dans les lignes affichées, plutôt que du total en base — gère naturellement les deux cas (nombre demandé respecté, ou demande supérieure à ce qui existe réellement).

**Point observé en testant, non lié à ce changement** : la suite de classification a montré 10/11 sur une exécution isolée (le cas "meilleur collège de France" retombant en `question_methodologique`) — creusé et confirmé comme de la variance déjà connue de l'extraction LLM de `ordre_souhaite` (S8.21), pas une régression : 7/8 correct sur des essais répétés, confirmé 11/11 en relançant la suite complète juste après.

**Validation** : testé nombre respecté (3 sur 4 disponibles), demande excessive (10 demandées, 4 affichées avec transparence honnête), chemin nommé et chemin géo. Suite complète re-passée sans régression (classification 11/11, cahier e2e 22/22).

**Conséquence** : `graph_router.py` (nouveau champ + câblage + 2 fonctions d'intro corrigées), `prompts/router_system_prompt.py`.

## S8.30 — Nuance méthodologique traitée même quand la résolution de noms échoue

**Contexte** : dernier point C — quand la résolution d'un nom d'établissement échouait, toute la question de nuance méthodologique posée en même temps ("et leur VA est-elle fiable ?") était silencieusement abandonnée, seule la demande de clarification s'affichait.

**Décision** : `noeud_clarification_noms` interroge maintenant le RAG méthodologique (même appel que `noeud_rag`/`_generer_nuance_rag`) si `nuance_methodologique_demandee` est vrai, et ajoute la réponse à la clarification, plutôt que de terminer directement sur `END` sans jamais y passer.

**Corrigé au passage (même fonction)** : la question de clôture ("Peux-tu préciser lequel tu veux (numéro, ville ou département) ?") était accolée systématiquement, y compris pour un cas "introuvable" où il n'y a aucune liste numérotée — "numéro de quoi ?" (repéré dans le rapport visuel). Désormais conditionnelle : "numéro" seulement s'il y a réellement plusieurs candidats ambigus.

**Trouvé en testant le fix, problème distinct et plus large, non résolu ici** : la recherche RAG sur une question de comparaison nommée + nuance ("Compare le collège X et Y, et est-ce que leur VA est fiable ?") ne trouve souvent aucun chunk pertinent — vérifié : des chunks pertinents existent (score jusqu'à 0.397, sur la fiabilité des IVAC) mais restent sous le seuil de similarité (0.5). Confirmé que ce problème touche identiquement le chemin de succès (les deux noms trouvés) : la dilution vient du mélange noms propres + "Compare... et..." dans la requête d'embedding, pas de la résolution de noms elle-même. Le fix de ce commit est donc correctement câblé mais sa valeur pratique reste limitée tant que cette dilution n'est pas traitée séparément.

**Validation** : formulation de clôture correcte sur un cas "introuvable" ; suite complète sans régression (classification 11/11, cahier e2e 22/22).

**Conséquence** : `graph_router.py` (`noeud_clarification_noms`).

## S9.1 — Mémoire de conversation générale (routeur) + report du contexte sur continuation

**Contexte** : pivot du projet vers une mise en production réelle, multi-utilisateurs, plutôt qu'un exercice d'apprentissage isolé (cf. décision utilisateur hors code). Jusqu'ici, chaque question était traitée indépendamment — une relance sans répéter le nom ou la zone ("et son adresse ?", "et leur VA est-elle fiable ?") était traitée comme une question vide de sens, faute de toute mémoire entre deux appels du graphe.

**Décision** : nouveau champ `nouveau_sujet` (bool) extrait par le routeur, dans le même appel LLM fusionné que les champs existants — true si la question ouvre un sujet sans lien avec l'historique, false si elle continue sur les mêmes établissements/zone. Historique des `HISTORIQUE_MAX_TOURS` (5) derniers tours injecté comme de vrais tours de conversation (rôles user/assistant) dans ce même appel, pour que le LLM interprète les relances avec ce contexte. Sur continuation (`nouveau_sujet=false`), `zone_geo`/`noms_etablissements`/`secteur_souhaite` retombent sur la valeur du tour précédent si le LLM ne les extrait pas explicitement du tour courant — même principe "LLM interprète, code sécurise le repli" que `requete_rag_nuance` (S8.30/S9.x).

**Pourquoi 5 tours et pas plus** : coût mesuré négligeable à cette échelle (~0,0003$/appel en gpt-4o-mini pour 5 tours, contre ~0,00013$/appel sans historique), donc pas un facteur limitant réel — 5 retenu car l'état de session (zone/noms déjà résolus) couvre par ailleurs la continuité factuelle au-delà de cette fenêtre pour le cas d'usage identifié (une comparaison, puis plusieurs relances dessus, puis une nouvelle comparaison).

**Rejeté** : résumé/compaction de l'historique au-delà de 5 tours (sur-ingénierie à ce stade, aucun usage réel ne le justifie encore — pratique standard des produits de chat, à ajouter plus tard si le besoin se confirme) ; report explicite d'`uai_resolus`/`resolution_noms` sur continuation (immédiatement écrasé par `noeud_resolution_noms`, qui tourne de toute façon systématiquement après le routeur pour cette catégorie — la résolution SQL sous-jacente est déterministe et bon marché, pas un appel LLM, donc rien à économiser en la refaisant) ; tenter de sauter l'appel LLM du routeur sur les relances "évidentes" (risque de louper un vrai changement de sujet, pour un gain de coût négligeable aux volumes actuels).

**Levier de coût non activé, à garder en tête si le trafic augmente** : la mise en cache automatique de préfixe d'OpenAI (`cached input`, -50% sur la partie mise en cache du prompt) est pertinente ici car l'historique s'ajoute à la fin d'un préfixe stable (prompt système + tours précédents identiques d'un appel au suivant) — non nécessaire à l'échelle actuelle, mais à réévaluer si le coût du routeur devient un sujet réel.

**Conséquence** : `config.py` (`HISTORIQUE_MAX_TOURS`), `prompts/router_system_prompt.py`, `graph_router.py` (`AgentState`, `noeud_router`, nouvelles fonctions `nouvelle_session()`/`poser_question()` réutilisables par toute future interface).

## S9.2 — Deux bugs trouvés en testant la mémoire de conversation

**Bug 1 — tableau incomplet sur une relance sans mot de comparaison** : `noeud_sql` appelait `recherche_sql(state["question"], ...)` (Text-to-SQL libre) même pour une comparaison d'établissements déjà résolus par nom. Piloté par le seul texte du tour courant, il régénère un jeu de colonnes différent selon le phrasé exact — "Et leur valeur ajoutée est-elle fiable ?" faisait ressortir les colonnes delta VA au lieu des valeurs brutes attendues par le gabarit d'affichage, affichant `?` à la place du taux de réussite et de la note écrit (visibles et corrects au tour précédent, sur la même donnée).

**Décision (bug 1)** : nouvelle fonction déterministe `rechercher_etablissements_par_uai()` (`sql_tool.py`) — même principe que S8.17/S8.18/S8.22 (remplacer le Text-to-SQL libre par une requête déterministe dès que le besoin est fixe, ici : afficher le tableau standard pour des UAI déjà résolus). Câblée dans `noeud_sql` pour le cas standard (hors évolution, qui a déjà sa propre fonction déterministe depuis S8.17).

**Bug 2 — crash sur un cas limite (5 zones géographiques)** : le LLM du routeur a renvoyé `"agregation_demandee"` comme valeur du champ `categorie` (JSON syntaxiquement valide, valeur sémantiquement incohérente — le nom d'un autre champ du schéma au lieu d'une catégorie valide). `Categorie(args["categorie"])` levait une exception non rattrapée, faisant planter tout le graphe au lieu d'afficher le message de blocage prévu ("je peux comparer jusqu'à 3 zones..."). Isolé comme provoqué par l'ajout du champ `nouveau_sujet` au schéma déjà chargé (12 champs requis) : reproduit de façon systématique (3/3) avec le nouveau schéma sur ce cas, absent à 3/3 avec le schéma d'avant cette session.

**Décision (bug 2)** : nouvelle fonction `_enum_securise()` (`graph_router.py`) — repli sur une valeur par défaut sûre (`Categorie.NON_RECONNU`, `SecteurSouhaite.INDIFFERENT`, `OrdreSouhaite.INDIFFERENT`) plutôt que de laisser planter le graphe sur une sortie LLM incohérente, appliquée aux 3 conversions d'enum du routeur. Un système en production ne doit jamais planter sur une réponse LLM malformée, même rare — dégrader proprement (ici : `non_reconnu` → agent ReAct, qui applique déjà le garde-fou multi-zones) plutôt que de renvoyer une erreur brute à l'utilisateur.

**Validation** : cahier de test complet re-passé après les deux fixs — 22/22 sans exception (21/22 avant le fix du bug 2, le cas "5 zones" plantait) ; scénario de mémoire à 3 tours revérifié, tableau cohérent entre les tours.

**Conséquence** : `agent/tools/sql_tool.py` (`rechercher_etablissements_par_uai`), `graph_router.py` (`noeud_sql`, `_enum_securise`).

## S10.1 — Entonnoir de désambiguïsation (D1) : implémentation différée à la conception de l'interface

**Décision** : le comportement actuel de `noeud_clarification_noms` (lister tous les candidats ambigus en texte, sans filtrage département/ville) reste en place tel quel pour l'instant.

**Pourquoi** : `SEUIL_CANDIDATS_AVANT_PRECISION` et la logique associée (S7.3) n'ont de sens qu'avec une interface à boutons cliquables — la construire en texte brut avant que l'interface soit conçue serait spéculatif, potentiellement à refaire.

**Conséquence** : l'inclusion ou non d'un niveau région dans l'entonnoir (en plus de département/ville) est reportée à la conception de l'interface, pas tranchée maintenant.

## S10.3 — Module `guardrails/` créé : validation d'entrée, limites de ressources, refus hors-domaine, validation SQL, anti-extraction de prompt

**Décision** : nouveau module `guardrails/`, regroupant des protections auparavant dispersées dans `graph_router.py`/`sql_tool.py`, et plusieurs protections nouvelles : plafond de longueur sur l'entrée utilisateur avant tout appel LLM, refus déterministe des questions hors du périmètre du produit, validation de la requête SQL générée par le LLM avant exécution (connexion en lecture seule + validateur syntaxique sur un vrai parseur SQL), détection d'une reproduction du prompt système dans une réponse, détection de vocabulaire d'implémentation dans une réponse destinée à l'utilisateur.

**Pourquoi** : critère retenu pour "guardrails/ vs code local" — une protection y va si elle porte sur une frontière de confiance (entrée utilisateur, sortie LLM, texte libre → SQL exécuté) et reste testable indépendamment de la logique métier environnante ; le reste garde sa place dans le code du nœud concerné.

**Conséquence** : `guardrails/llm_output_safety.py`, `resource_limits.py`, `output_contracts.py`, `input_limits.py`, `scope_guard.py`, `sql_safety.py`, `prompt_leakage.py`, `output_vocabulary.py`. Nouvelle dépendance : `sqlglot`. ~60 cas de test ajoutés, tous passants.

## S10.4 — Frontend Next.js (React/TypeScript), backend Python exposé via API

**Décision** : Frontend Next.js (React/TypeScript), backend Python exposé via API (FastAPI probable), reste à concevoir.

**Pourquoi** : Le produit central est un site public à trafic variable et croissant, avec des pages de contenu individuelles devant rester rapides, référençables et partageables par URL directe, ainsi qu'une zone interactive (chatbot) nécessitant un état de conversation et un rendu en streaming. Next.js couvre ces deux besoins avec un seul modèle de rendu cohérent : génération de pages statiques/à la demande pour le contenu (performance, référencement, mise à l'échelle), rendu serveur ou client pour la zone interactive, et un routage par fichier qui simplifie l'ajout de pages à mesure que le produit évolue. Le typage statique (TypeScript) réduit une classe entière d'erreurs d'exécution en production.

**Rejeté** :
- Tout-Streamlit : modèle d'exécution (script rejoué à chaque interaction) ne permet ni rendu par URL ni contrôle fin du cache — deux prérequis pour un site public destiné à monter en charge.
- Tout-Python (FastAPI + Jinja2 + htmx) : viable techniquement, mais impose de reconstruire manuellement des briques que Next.js fournit déjà de façon standardisée (routage, récupération de données, réutilisation de composants), au prix d'une surface de maintenance plus importante à mesure que le produit grandit.

**Conséquence** : Backend agentique inchangé dans sa logique, à envelopper dans une API. Implémentation non commencée.

## S13.3 — Filtre par critère de section + factorisation SQL générique

**Décision** : factoriser la validation + construction du filtre SQL sur les colonnes de section dans une fonction unique (`_filtre_section_sql` dans `sql_tool.py`), dérivée d'un seul registre (`COLONNE_SECTION` dans `config.py`), plutôt que dupliquer cette logique dans chaque fonction déterministe qui en a besoin.

**Pourquoi** : 3 fonctions déterministes (`rechercher_top_par_secteur`, `rechercher_etablissements_par_uai`, `calculer_moyenne_etablissements`) reproduisaient la même validation par liste blanche et la même construction de clause SQL pour filtrer sur une section (sport, arts, cinéma, théâtre, internationale, européenne). Un nouveau critère de filtre binaire (ex: futures colonnes restauration/hébergement) ne doit s'ajouter qu'à un seul endroit.

**Conséquence** : ajouter un nouveau critère de filtre binaire ne demande plus que d'étendre le registre (`COLONNE_SECTION`) et d'ajouter un paramètre par fonction déterministe, pas de recopier la validation. `rechercher_etablissements_par_uai` récupère aussi systématiquement les colonnes de section pour un établissement nommé (coût négligeable, petit nombre de lignes), pour répondre directement ("a-t-il une section théâtre ?") sans nouvelle requête ciblée.

## S13.4 — Refonte de la formule de score : 4 indicateurs à parts égales, VA à 50% du poids total, mixité sortie du calcul

**Décision** : Score = 25% taux de réussite + 25% note écrite + 25% VA taux de réussite + 25% VA note écrite (normalisation min-max par session, remplace la formule S1.3/S8.6 à 60%/40% sur les seuls résultats bruts). Notation finale en lettres (B/B+/A-/A/A+, du plus faible au plus élevé), répartition par quantiles selon le Stanine adapté à 5 groupes (10/15/50/15/10%).

**Options testées** : poids égal par indicateur (retenu) / VA renforcée à 30% puis 35% chacune (60%/70% du poids total sur la VA).

**Pourquoi** : le poids égal par indicateur est la pondération la moins arbitraire à l'œil, mais ce n'est pas un choix neutre pour autant — la VA (taux + note) représente déjà 50% du poids total du score, bien plus que sa part dans l'ancienne formule (qui ne comptait que les résultats bruts). C'est une prise de position assumée : valoriser la progression réelle d'un établissement autant que le niveau brut qu'il atteint. Les pondérations plus engagées (30/30, 35/35) ont été écartées après vérification empirique : elles produisent des cas où un établissement à excellents résultats bruts tombe dans un groupe inférieur à un établissement aux résultats plus modestes mais à VA très forte — un renversement jugé trop surprenant pour un parent qui compare deux fiches. Seule la répartition à parts égales ne produit aucun cas de ce type sur les 6 199 établissements testés.

**Répartition en lettres** : le découpage 10/15/50/15/10% correspond au Stanine (standard nine), une convention de mesure statistique standard utilisée en psychométrie de l'évaluation scolaire — bande centrale large (la moitié des établissements), bandes resserrées aux extrêmes pour réserver les meilleures/moins bonnes notes aux établissements réellement atypiques.

**Rejeté** : intégration de l'IPS et de la mixité sociale dans le calcul du score, sous toute pondération testée (proximité à la moyenne nationale, diversité interne, ou combinaison des deux) — un établissement ne choisit pas le profil social de son secteur de recrutement, notamment sous carte scolaire ; aucune combinaison testée ne corrige ce biais sans le déplacer ailleurs.

**Conséquence** : à implémenter dans `calculer_scores()` / `config.py`. L'IPS et l'écart-type de mixité sociale restent affichés sur la fiche d'identité de l'établissement (déjà prévu), sans influencer le score ni la notation en lettres. L'explicatif affiché à côté de la notation devra détailler la méthode de calcul et préciser explicitement que le choix méthodologique valorise les établissements à forte valeur ajoutée.

---

# Phase 4 — Frontend : architecture de routes

## S14.1 — Arborescence de routes Next.js calquée sur le sitemap validé

**Décision** : squelette de routes (App Router) avec pages stub minimales pour chaque gabarit prévu : accueil, assistant, recherche, explorer, guides (`/comprendre/{slug}`), hiérarchie géographique région › département › ville (chacune adressable indépendamment), fiche établissement portant le chemin complet (`/region/{r}/departement/{d}/ville/{v}/college/{nom-uai}`), académie en rattachement transverse (`/academie/{slug}`, jamais dans l'URL ni le fil d'Ariane des autres pages), pages utilitaires (méthodologie, sources, à propos, mentions légales).

**Pourquoi** : un squelette de routes avec pages stub permet de valider la structure de navigation (imbrication des segments dynamiques, absence de collision entre les routes courtes région/département/ville et la route complète de la fiche) avant d'investir du temps de design sur le contenu visuel de chaque page. Testé en local après création : les 14 routes se résolvent correctement, y compris les segments dynamiques imbriqués sur 4 niveaux de la fiche établissement.

**Rejeté** : décliner le calendrier scolaire par académie via une sous-route dynamique (`/calendrier/{academie}`) — la page reste unique, toutes les académies affichées ensemble (zones de vacances), une recherche par adresse/ville pour retrouver sa zone étant prévue comme évolution ultérieure de cette même page plutôt qu'un besoin de route supplémentaire.

**Conséquence** : `web/src/components/PagePlaceholder.tsx` (composant de stub partagé par toutes les routes, évite de dupliquer la même logique). Chaque nouvelle page de contenu (département, ville, fiche établissement...) remplacera son placeholder sans changer l'architecture de dossiers. Deux points restent ouverts, à trancher à la conception de chacune des pages concernées : format des slugs (accents, UAI dans l'URL) et existence d'une page dédiée "adresse → collège de secteur".

## S15.2 — Implémentation de la fiche établissement en tranche verticale (DB → API → page Next.js), sans carte scolaire ni synthèse IA

**Décision** : Construire d'abord une tranche verticale complète et fonctionnelle de la fiche établissement (nouvelles tables SQL, route API, composants front) plutôt que d'intégrer immédiatement la carte scolaire, les établissements voisins ou la synthèse IA.

**Périmètre livré** :
- Données : nouvelles tables `langues_scolaires`, `langues_offertes`, `sections_sportives` ; colonnes précalculées `ivac.brevet_taux_reussite_national/departemental` et `ivac.brevet_note_ecrit_national/departemental`. Nouvelles sources : `data/zones_academiques.csv` (34 académies, zones A/B/C vérifiées sur l'arrêté Légifrance du 22/10/2025, NULL pour la Corse et les DOM-TOM), `data/vacances_scolaires_2026_2027.csv`.
- Backend : `agent/tools/etablissement_tool.py::obtenir_fiche_etablissement(uai)`.
- API : route `GET /etablissement/{uai}`, nouveaux modèles dans `api/schemas.py`.
- Frontend : page `web/.../college/[collegeSlug]/page.tsx` remplace le placeholder ; composants `_components/` (FicheIdentite, ResultatsBrevet, ValeurAjoutee, PositionnementSocial, DispositifsExpliques) ; format de slug `{nom-slugifié}-{uai}`.

**Principe appliqué** : toute donnée potentiellement interrogeable par une question utilisateur doit vivre en base (table + entrée `SCHEMA_PROMPT`), jamais en config applicative — appliqué ici au mapping académie → zone de vacances scolaires.

**Rejeté** : intégration immédiate de la carte scolaire, des établissements voisins et de la synthèse IA dans ce même chantier — différée à un chantier séparé (cf. S1.4 pour la carte scolaire).

**Conséquence** : la couverture des données livrées est partielle par nature (langues ~78% des collèges, sections sportives ~25%) — état réel des sources, pas un bug. La convention de couleur des badges de dispositifs/sections (8-9 catégories) reste à trancher, notée dans `journal_de_bord.md`.

## S15.3 — Finalisation de la fiche établissement : données manquantes explicites, pas de catégorisation inventée sur l'IPS, harmonisation visuelle brevet/VA/milieu social

**Décision** : Trois ajustements sur la fiche établissement issue de la S15.2, après retours sur le rendu réel :
1. Absence de données (langues, sections sportives) toujours signalée explicitement, jamais silencieuse.
2. IPS et mixité sociale affichés sans catégorie qualitative ("favorisé"/"défavorisé") — seulement les bornes de l'échelle nommées et le positionnement réel de l'établissement / de la moyenne nationale.
3. Les 3 sections de contenu (brevet, valeur ajoutée, milieu social) suivent désormais la même grammaire visuelle : titre nu sur fond de page pour les données descriptives (brevet, milieu social), cadre teinté réservé aux données évaluatives (valeur ajoutée) ; cartes internes toutes en blanc.

**Pourquoi (données manquantes)** : `langues_offertes` et `sections_sportives` ont une couverture partielle (~78% et ~25% des collèges, cf. S15.2) pour des raisons différentes — LV1/LV2 sont une obligation légale (absence = quasi certainement un trou de collecte), alors qu'une section sportive est un dispositif optionnel réellement absent dans la majorité des collèges. Un même message masquerait cette différence : "Données non disponibles" pour les langues (on affirme un vide de collecte), "Aucune donnée répertoriée — à vérifier auprès de l'établissement" pour le sport (on ne garantit pas une absence qu'on ne peut pas confirmer à 100%).

**Pourquoi (pas de catégorisation IPS)** : la notation en lettres du score (S13.4) est une méthode propre au produit, assumée et documentée comme telle. L'IPS et l'écart-type IPS sont en revanche des indicateurs officiels publiés par le ministère — leur attribuer une catégorie qualitative maison sans base officielle ferait passer un jugement du produit pour une lecture ministérielle. Vérification faite dans les 4 sources DEPP déjà ingérées dans le RAG (guide méthodologique IVAC, construction de l'IPS, actualisation 2022, note d'information 23.16) : aucune catégorisation officielle par seuils n'existe. D'où le choix de n'afficher que les bornes de l'échelle, sans trancher où se situe la limite entre les deux.

**Pourquoi (harmonisation visuelle)** : le fond `fond-carte` (#FBF6EC) utilisé initialement pour les cartes descriptives est visuellement quasi indissociable du fond de page `fond-creme` (#FCF4E9) — la distinction ne tenait qu'à une fine bordure, jugée insuffisamment lisible en test réel. Le blanc uniforme sur toutes les cartes de données résout ce problème de contraste, en gardant le cadre teinté de la valeur ajoutée comme seul signal visuel réservé aux données évaluatives.

**Rejeté** : catégorisation IPS/mixité par quantiles calculés sur la distribution réelle des établissements (seuils Stanine 10/15/50/15/10, même méthode que la notation en lettres) — écartée après vérification qu'aucune source officielle ne la justifie. Fond beige (`fond-carte`) pour toutes les cartes de données — écarté pour manque de lisibilité face au fond de page, de teinte quasi identique.

**Conséquence** : `FicheIdentite.tsx` (messages de repli différenciés), `PositionnementSocial.tsx` (jauge sans catégorie, aide contextuelle au clic pour les termes techniques IPS/écart-type, cartes blanches, titre de section renommé "Le milieu social des élèves"), `ResultatsBrevet.tsx` (cartes de stats passées en blanc). Aucun changement de schéma de données — ces trois ajustements sont purement côté frontend.

## S15.4 — Convention de slugs pour la hiérarchie géographique (région/département/ville), hiérarchie de routes entièrement imbriquée, et résolution dynamique sans table de correspondance

**Décision** :
- Hiérarchie de routes entièrement imbriquée : `/region/{regionSlug}` (racine, seule route indépendante) → `/region/{regionSlug}/departement/{deptSlug}` → `.../ville/{villeSlug}` → `.../college/{collegeSlug}` (fiche établissement, déjà en place). Revient sur "chacune adressable indépendamment" (S14.1) pour le département et la ville, qui existaient jusqu'ici en routes à plat séparées (`/departement/{deptSlug}`, `/ville/{villeSlug}`) — chaque niveau reste adressable seul, mais imbriqué dans le précédent plutôt qu'isolé, pour une organisation de pages cohérente de bout en bout.
- Académie : jamais incluse dans le slug de la fiche établissement (confirme S14.1 — rattachement transverse, absent de l'URL des autres pages).
- Région : slug = nom seul slugifié (ex. `auvergne-rhone-alpes`), sans code.
- Département : slug = `{code}-{nom-slugifié}` (ex. `27-eure`), numéro en tête.
- Ville : slug = nom seul slugifié (ex. `lyon`), sans code postal ni identifiant supplémentaire — l'imbrication sous département suffit à garantir l'unicité.
- Résolution slug → donnée réelle : calcul à la volée à chaque requête (pas de colonne de slug précalculée/stockée en base). Le département se résout par extraction directe du numéro en tête du slug (requête exacte sur `code_departement`, pas de comparaison slug par slug). La ville se résout par comparaison de slugs, mais uniquement parmi les communes du département déjà résolu par l'étage au-dessus (pas sur l'ensemble des communes de France).

**Pourquoi (hiérarchie imbriquée plutôt que routes indépendantes)** : la vérification anti-collision faite pour la ville (voir plus bas) ne portait que sur les doublons **à l'intérieur d'un même département** — pertinente seulement si la ville est imbriquée sous département dans l'URL. Or `/ville/{villeSlug}` existait jusqu'ici en route à plat, indépendante. Vérification refaite sur le bon périmètre (doublons de nom de commune **entre départements différents**, parmi les communes ayant un établissement) : 36 noms de commune sont partagés par au moins deux départements différents (ex. Valence : Drôme et Tarn-et-Garonne ; Saint-Denis : La Réunion et Seine-Saint-Denis ; Saint-Marcel : Saône-et-Loire et Eure). Une route à plat avec un slug "nom seul" ne peut pas lever cette ambiguïté. Plutôt que d'ajouter un identifiant technique (code département) au slug ville tout en gardant une route à plat, ou de gérer la collision au cas par cas par une désambiguïsation applicative pour ces 36 noms seulement, le choix retenu est de nicher toute la hiérarchie (région › département › ville › collège) : l'ambiguïté est levée structurellement par l'URL elle-même, et l'organisation des pages reste cohérente et uniforme à tous les niveaux plutôt qu'un mélange de routes à plat et imbriquées.

**Pourquoi (académie exclue)** : un parent ne formule pas sa recherche par académie (découpage administratif), mais par ville/quartier — l'ajouter n'aiderait aucune intention de recherche réelle et contredirait le rattachement transverse déjà acté en S14.1. Le vrai potentiel SEO de l'académie (recherches "vacances scolaires académie de X", pattern réel et fréquent) concerne la page calendrier scolaire, pas le slug du collège — sujet distinct, non traité ici.

**Pourquoi (numéro pour le département, pas pour la région)** : le numéro de département est un repère culturel largement reconnu (101 valeurs, apprises dès l'école, présentes sur les plaques d'immatriculation) — l'inclure aide un visiteur à se repérer même sans connaître le nom exact. Le code région INSEE n'a pas cet effet de reconnaissance (aucun repère grand public équivalent) — l'ajouter n'apporterait que de la longueur sans bénéfice de compréhension.

**Pourquoi (pas de code postal pour la ville)** : trois raisons cumulatives. Redondance avec le département déjà présent dans l'URL (les deux premiers chiffres d'un code postal sont le numéro de département). Absence du même effet de reconnaissance que le département (un code postal à 5 chiffres n'est pas identifiable au premier coup d'œil comme les 101 numéros de département, et un visiteur qui cherche une ville par son nom n'a pas besoin de son code postal pour s'orienter). Problème technique concret vérifié en base : une même commune peut avoir plusieurs codes postaux (32 pour Toulouse, une quinzaine pour Paris et Marseille dans le référentiel actuel) — il n'existe pas de valeur canonique unique à afficher, ce qui rendrait le choix arbitraire et potentiellement trompeur.

**Pourquoi (pas de suffixe d'unicité sur le nom de la ville elle-même)** : vérification empirique sur les 14 732 établissements de la base (4 371 couples département/commune distincts), en comparant les coordonnées GPS des établissements partageant un même couple département+nom de commune — aucun cas confirmé de deux communes distinctes portant le même nom au sein d'un même département (les seuls écarts géographiques significatifs relevés sont de grandes villes réelles étendues sur plusieurs km, des communes nouvelles issues de fusions récentes, ou une erreur de géocodage isolée, cf. dette technique `roadmap_technique.md`). Combinée à l'imbrication sous département (qui élimine par construction les doublons entre départements différents, cf. plus haut), l'unicité du slug ville est ainsi garantie sans avoir besoin d'ajouter un identifiant dans le nom lui-même.

**Pourquoi (résolution à la volée plutôt que slug stocké en base)** : un slug stocké créerait une deuxième source de vérité (la colonne stockée vs la fonction de calcul), avec un risque de divergence silencieuse si la fonction de calcul évolue sans que la colonne soit recalculée — le type de bug dispersé que le principe de factorisation du projet cherche à éviter. Le volume en jeu (18 régions, 101 départements, ~4300 communes) rend le recalcul à chaque requête sans coût mesurable ; aucune table de dimension géographique dédiée n'existe aujourd'hui pour justifier l'inverse.

**Rejeté** : inclusion de l'académie dans le slug du collège pour un bénéfice SEO supposé — écartée après vérification que la présence d'un mot-clé dans une URL n'est pas un facteur de classement significatif d'après les guidelines Google (Search Central), documentées de longue date, et qu'aucune intention de recherche réelle ne le justifie ici. Suffixe de code postal pour la ville et suffixe de code région pour le département — écartés (raisons détaillées ci-dessus). Routes indépendantes pour département et ville (approche S14.1) et, alternative envisagée un temps, suffixe de code département sur le slug ville en gardant une route à plat — écartés tous les deux au profit de l'imbrication complète, jugée plus cohérente pour l'organisation du site. Stockage d'un slug précalculé en base pour région/département/ville — écarté tant que le volume de données reste à cette échelle.

**Conséquence** : les routes `web/src/app/departement/[deptSlug]/page.tsx` et `web/src/app/ville/[villeSlug]/page.tsx` (routes à plat) doivent être déplacées sous `web/src/app/region/[regionSlug]/departement/[deptSlug]/...`, à côté de la route déjà imbriquée de la fiche établissement. `web/src/lib/slug.ts` à faire évoluer (fonction de résolution slug → entité, distincte de la fabrication du slug ; le `deslugifier()` actuel devient obsolète une fois la résolution réelle en place). Aucun changement de schéma de données. Le risque commun aux deux approches de résolution (si `slugifier()` change de règle un jour, les URLs déjà indexées cassent sans redirection) reste non traité, accepté pour l'instant vu le faible trafic actuel.

## S15.5 — VA absente substituée par une valeur neutre (0) plutôt que d'exclure l'établissement de la notation

**Décision** : Quand la valeur ajoutée (VA) d'un établissement n'est pas publiée par le Ministère pour une session donnée, `score_principal` (et donc la notation en lettres) est désormais calculé en substituant VA = 0 pour les deux composantes manquantes (taux et note), au lieu de laisser la notation absente. Un champ `va_imputee` (table `scores`) trace cette substitution établissement par établissement.

**Pourquoi** : La VA mesure un écart à un résultat attendu, centrée sur 0 par construction — vérifié empiriquement sur les 4 sessions disponibles (moyenne entre -0.94 et -0.73 pour le taux, quasi nulle pour la note). Substituer 0 revient donc à supposer « résultat conforme à l'attendu » en l'absence de preuve du contraire, sans avantager ni pénaliser l'établissement. Sans cette substitution, environ un quart des établissements n'avaient jamais de notation, quel que soit leur résultat brut — les excluant structurellement de tout tri ou classement basé sur la notation, y compris ceux ayant un bon taux de réussite (cas vérifié : Bourg-Lastic 94%, Arlanc 100%, La Tour-d'Auvergne 96%, tous sans notation avant ce changement). Les bornes de normalisation de la VA restent calculées sur les valeurs réelles uniquement, jamais faussées par les zéros substitués.

**Rejeté** : Ne rien faire et exclure ces établissements de tout tri par notation — écarté car pénalise injustement des établissements aux bons résultats bruts, uniquement absents des classements faute de VA publiée. Calculer une notation de repli séparée à partir de `score_resultats` seul (sans VA) — écarté : aurait créé deux méthodologies de notation visuellement identiques (mêmes lettres A+/A/A-/B+/B) mais mesurant des choses différentes, risque de confusion.

**Conséquence** : `data/ingest.py::calculer_scores` modifié, réingestion effectuée. `va_imputee` exposé via l'API (`EtablissementIdentite.va_imputee`) et signalé dans l'interface (bouton d'aide contextuelle) quand la notation d'un établissement n'a pas de VA réelle derrière. Sujet resté ouvert : `/methodologie` (encore un stub) devra expliquer cette convention en clair.

## S16.1 — Suppression de la redirection automatique sur résultat unique dans `/recherche`

**Décision** : La page `/recherche` n'effectue plus de redirection automatique vers la fiche établissement ou la page ville quand la recherche ne remonte qu'un seul résultat dans une seule catégorie (ancienne "Règle V1", `docs/Design_system/recherche`). La page de résultats s'affiche désormais systématiquement, y compris pour un résultat unique.

**Pourquoi** : Vérifié en usage réel — la bascule instantanée, sans transition ni confirmation visuelle, donnait l'impression d'un dysfonctionnement plutôt que d'un raccourci volontaire, l'utilisateur n'ayant pas le temps de percevoir qu'un seul résultat avait été trouvé avant d'être redirigé ailleurs.

**Rejeté** : Garder la redirection avec une transition visible avant la bascule (ex: message "Un seul résultat, redirection…") — écarté, la complexité ajoutée (délai artificiel, état intermédiaire à gérer) ne compensait pas le gain d'un clic économisé.

**Conséquence** : `web/src/app/recherche/page.tsx` — suppression du bloc de redirection conditionnelle et des imports devenus inutiles (`redirect`, `hrefEtablissement`, `hrefCommune`).

## S16.2 — `Sitemap.dc.html` comme document de référence unique pour l'état des pages du site

**Décision** : `docs/Design_system/Sitemap.dc.html` sert de document de référence unique pour connaître l'ensemble des pages du site et leur état d'implémentation (contenu réel vs. `PagePlaceholder`), mis à jour à chaque page terminée plutôt que de créer un document de suivi séparé.

**Pourquoi** : Le fichier documentait déjà l'intention de conception (plan de site, portes de navigation, hiérarchie géographique). Centraliser aussi l'état réel dans le même document évite deux sources d'information sur le même sujet susceptibles de diverger avec le temps.

**Conséquence** : Audit du 23/07/2026 intégré au fichier — 10 routes sur 17 ont un contenu réel, 7 restent en `PagePlaceholder` (`Sitemap.dc.html` fait foi pour le décompte à jour). `/explorer`, précédemment un stub affiché au même niveau que `/recherche` dans la navigation principale, réexporte désormais la page `/region` et n'est donc plus un placeholder.

## S16.3 — Classements "meilleure notation" / "meilleure valeur ajoutée" sur les pages région et département

**Décision** : Les pages région et département affichent deux blocs de 5 établissements — le meilleur score global (`score_principal`) et la meilleure valeur ajoutée du taux de réussite seule (`brevet_va_taux_reussite_general`, triée indépendamment, pas un score combiné). Calcul à la demande à chaque requête, via `rechercher_top_par_secteur` (étendue avec `critere_tri="valeur_ajoutee"`), pas de table précalculée. Non retenu au niveau ville.

**Pourquoi** : Vérifié sur les vraies données (session 2025, 6 809 collèges) — région et département montrent un chevauchement moyen limité entre les deux classements (2,24/5 et 2,92/5), preuve qu'ils apportent une information réellement différente. Au niveau ville, 95% des communes ont moins de 5 collèges (un "top 5" y serait la liste complète) et les 5% restantes ont un chevauchement de 4,14/5 — peu d'intérêt à un second classement à cette échelle. Le calcul à la demande plutôt que le stockage évite une deuxième source de vérité qui se périmerait silencieusement à chaque évolution de la formule de score (déjà arrivé une fois, S13.4) — à l'échelle actuelle, la requête reste triviale en temps de calcul. Réutiliser `rechercher_top_par_secteur` (déjà utilisée par l'agent conversationnel) pour la page évite aussi de dupliquer la logique de classement dans deux implémentations distinctes.

**Rejeté** : Matérialiser les classements en base — écarté (risque de deuxième source de vérité, cf. ci-dessus). Séparer les listes par secteur public/privé — écarté, aurait doublé le nombre de blocs affichés pour un gain de lisibilité jugé insuffisant. Trier la valeur ajoutée sur un score combiné (taux + note) — écarté au profit du taux seul, pour que le chiffre affiché corresponde exactement à ce qui justifie le classement.

**Conséquence** : `agent/tools/sql_tool.py` (`rechercher_top_par_secteur` étendue), `agent/tools/hierarchie_tool.py` (nouvelle fonction `obtenir_top_etablissements_zone`), `api/schemas.py` + `api/main.py` (`TopEtablissement`, `RegionHub`/`DepartementHub` étendus), `web/src/lib/types.ts` (miroir), nouveau composant `web/src/components/BlocTopEtablissements.tsx`, branché dans `ZoneHub.tsx`. Testé via `TestClient` (API) et Playwright (rendu réel, dont un lien vers un établissement d'un département différent de celui affiché).

## S16.4 — Format d'affichage du département : nom devant, code entre parenthèses

**Décision** : Partout où un département est affiché (H1 et fil d'Ariane de la page département, maillon département du fil d'Ariane des pages ville et fiche établissement, tableau des départements de la page région), le format est `Rhône (69)` — nom d'abord, code entre parenthèses.

**Pourquoi** : Recherche menée sur les conventions réelles d'affichage en France. Deux usages distincts selon le contexte, pas une convention unique : les tables de codification technique (liste de numérotation Wikipédia, tableau de codification du ministère de l'Éducation nationale) placent le code devant ("01 Ain"), tandis que les pages destinées au grand public (page département Insee, site gouv.fr grand public) placent le nom devant avec le code en complément ("Ain (01)"). Le site s'adresse à des parents qui cherchent une entité déjà nommée, pas à un usage de codification — le format nom-devant a été retenu, alignant du même coup la nouvelle convention sur celle déjà en place dans `RechercheBloc`, plutôt que d'introduire une deuxième convention pour la même information.

**Rejeté** : Format code-devant ("69 · Rhône") — envisagé initialement, écarté après vérification que ce n'est pas le format dominant dans les sources destinées au grand public, contrairement à l'hypothèse de départ.

**Conséquence** : `web/src/components/SousDivisionsTable.tsx` (nouvelle prop `afficherCode`, désactivée par défaut), `ZoneHub.tsx` (relais de la prop), `region/[regionSlug]/page.tsx` (activation), `departement/[deptSlug]/page.tsx` (H1 + fil d'Ariane), `.../ville/[villeSlug]/page.tsx` et `.../college/[collegeSlug]/page.tsx` (maillon département du fil d'Ariane). Testé avec `tsc --noEmit` et vérifié visuellement (captures d'écran Rhône et Auvergne-Rhône-Alpes).

## S17.1 — Analytics d'audience du site : Umami auto-hébergé, plutôt que Google Analytics ou un outil tiers non maîtrisé

**Décision** : Suivi des pages vues et du parcours de navigation sur le site via Umami, un outil open source auto-hébergé (conteneurs Docker : application Node.js + base Postgres dédiée), plutôt qu'un service tiers hébergé chez un tiers non maîtrisé. Intégration par un script chargé sur toutes les pages via le layout racine Next.js (`next/script`, stratégie `afterInteractive`), activé uniquement si les variables d'environnement `NEXT_PUBLIC_UMAMI_SRC` et `NEXT_PUBLIC_UMAMI_WEBSITE_ID` sont renseignées.

**Pourquoi** : Umami ne nécessite que Postgres, le moteur de base de données déjà utilisé par ailleurs dans le projet (via Supabase pour `conversations_log`), ce qui limite le nombre de technologies différentes à opérer sur l'ensemble de la stack. L'auto-hébergement conserve la maîtrise complète des données de navigation des visiteurs, contrairement à Google Analytics, dont l'usage a été jugé non conforme au RGPD par la CNIL en France (transfert de données vers les Etats-Unis sans garanties suffisantes après l'arrêt Schrems II).

**Rejeté** : Google Analytics, écarté pour la raison de conformité ci-dessus. Matomo, écarté car il nécessite MySQL/MariaDB, un moteur de base de données supplémentaire non utilisé ailleurs dans le projet. Plausible, écarté car il nécessite à la fois Postgres et ClickHouse, deux moteurs différents à opérer pour un seul outil.

**Conséquence** : `web/src/app/layout.tsx` (composant `Script`), `web/.env.local` (non suivi par git, contient l'identifiant du site Umami de test). Testé en local uniquement pour l'instant (Docker via Colima, base de données jetable) : pages vues confirmées visibles dans le tableau de bord Umami après navigation sur le site en développement. L'hébergement définitif de l'instance Umami en production reste à trancher avec le reste du stack (cf. S9.5 dans `journal_de_bord.md`), pas encore acté.

## S17.2 — Carte interactive multi-résultats ("explorer") hors périmètre : liste privilégiée sur les pages de résultats

**Décision** : Pas de carte interactive permettant d'explorer plusieurs établissements simultanément (résultats de recherche, pages région/département/ville) : la liste reste le mode d'exploration principal.

**Pourquoi** : le choix d'un collège s'appuie sur un point de référence déjà connu de l'utilisateur (domicile, secteur de rattachement), pas sur une exploration libre d'un territoire inconnu. La littérature UX distingue ces deux cas : une carte améliore mesurablement la comparaison quand elle porte sur la position relative de nombreuses options inconnues entre elles (étude Baymard Institute sur la réservation hôtelière, tests utilisateurs en laboratoire), mais n'apporte rien de plus qu'une distance affichée en texte quand il s'agit de situer des options par rapport à un point de référence déjà connu (étude Nielsen Norman Group sur la recherche de points de vente). Sur mobile, une carte occupant l'écran introduit en outre un conflit de geste documenté entre le scroll de page et le déplacement sur la carte. Vérification sur trois répertoires scolaires comparables (GreatSchools.org, Niche.com, palmarès des collèges de L'Etudiant) : aucun ne fait de la carte l'outil central d'exploration de plusieurs établissements, elle y est absente ou strictement secondaire.

**Rejeté** : carte interactive multi-pins comme mode d'exploration principal ou par défaut des résultats (à la manière des sites immobiliers type Bien'ici), écartée car elle répond à un besoin de comparaison géographique sans point de référence connu, différent du parcours réel de choix d'un collège.

**Conséquence** : les pages de résultats (recherche, hubs géographiques) restent en liste, sans carte. La localisation d'un établissement unique sur sa propre fiche (un point, pas une exploration multi-résultats) est un sujet distinct, traité séparément.

## S18.1 — Calendrier scolaire DOM-TOM 2026-2027 intégré à `vacances_scolaires`, données collectées manuellement

**Décision** : Ajout des dates de vacances scolaires 2026-2027 (année civile 2026 pour la Nouvelle-Calédonie et Wallis-et-Futuna, qui suivent un calendrier austral) pour les 9 académies et collectivités d'outre-mer (Guadeloupe, Martinique, Guyane, Mayotte, La Réunion, Saint-Pierre-et-Miquelon, Polynésie française, Nouvelle-Calédonie, Wallis-et-Futuna) dans la table `vacances_scolaires`, jusque-là limitée aux 3 zones métropolitaines. Nouveau fichier `data/vacances_scolaires_2026_2027_domtom.csv`, même format que le fichier métropole existant, repris par la même fonction d'ingestion (`ingerer_vacances` dans `data/ingest.py`).

**Source des dates** : page officielle du ministère de l'Education nationale, education.gouv.fr, page "Calendrier scolaire : toutes les dates des cours et des vacances", section outre-mer. Page inaccessible aux outils de récupération automatisée du fait d'une protection Cloudflare (erreur 403 constatée), dates collectées manuellement. Le calendrier métropolitain découle par ailleurs de l'arrêté du 22 octobre 2025 (Légifrance, JORF n°0248 du 23 octobre 2025, texte n°15), qui renvoie lui-même aux calendriers propres à chaque territoire d'outre-mer plutôt que de les fixer directement.

**Pourquoi une collecte manuelle plutôt qu'un fichier data.gouv.fr** : le jeu de données `fr-en-calendrier-scolaire` (data.gouv.fr), envisagé initialement, ne couvre aucun territoire d'outre-mer au-delà de l'année scolaire 2025-2026, donc pas la rentrée à venir. Une incohérence a été repérée et corrigée avant intégration sur Saint-Pierre-et-Miquelon : la source indiquait une reprise des vacances de printemps le 3 avril 2027, antérieure à la date de fin de vacances du 16 avril 2027 ; vérifiée et corrigée en 3 mai 2027.

**Rejeté** : le fichier `fr-en-calendrier-scolaire` de data.gouv.fr dans son ensemble, écarté pour la métropole (redondant avec les données déjà en place) et insuffisant pour l'outre-mer (cf. ci-dessus).

**Conséquence** : `data/vacances_scolaires_2026_2027_domtom.csv` (nouveau, 65 lignes), insérées dans `data/agent_ecoles.db` directement plutôt que via une réingestion complète (`data/ingest.py` reconstruit toute la base depuis les sources brutes, action disproportionnée pour cet ajout) ; le fichier sera repris automatiquement lors d'une prochaine réingestion complète. Point de vigilance non résolu, noté dans `roadmap_technique.md` : les dates de Wallis-et-Futuna et de Nouvelle-Calédonie sont strictement identiques dans la source collectée, plausible vu qu'elles partagent historiquement le même vice-rectorat, mais non vérifié indépendamment contrairement à la correction ci-dessus.

## S18.2 — Retrait du cadre teinté "valeur ajoutée", harmonisation totale du style des 3 sections de la fiche établissement

**Décision** : Retrait du cadre teinté (fond `fond-carte`, bordure `--color-positif-pale`) qui distinguait visuellement la section "La valeur ajoutée" des deux autres sections de la fiche établissement (brevet, milieu social), introduit en S15.3. Les 3 sections partagent désormais exactement le même traitement : titre nu sur fond de page, sans distinction de cadre entre donnée évaluative et donnée descriptive.

**Pourquoi** : le cadre teinté visait à signaler qu'une valeur ajoutée résulte d'une évaluation (comparaison à un attendu), contrairement aux données brutes des deux autres sections. En usage réel, ce traitement différent a été perçu comme une incohérence de style entre sections plutôt que comme un signal volontaire. La nature évaluative de la donnée reste portée par le contenu textuel lui-même : chaque indicateur de la section affiche explicitement la comparaison attendu → obtenu, ce qui rend le cadre de fond redondant avec cette information.

**Rejeté** : conserver un cadre plus discret (bordure seule, sans fond teinté) pour garder un signal minimal, écarté, l'objectif explicite était une cohérence totale entre les 3 sections plutôt qu'une distinction atténuée.

**Conséquence** : `web/.../college/[collegeSlug]/_components/ValeurAjoutee.tsx`. Aucun changement de données ni de schéma, purement visuel.
