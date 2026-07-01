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

**Rejeté** : bascule complète sans cadrage — jugée risquée pour un profil non-développeur dont l'objectif est la compréhension, pas seulement la livraison. Révise la position prise en S3.D16 (maintien du chat, refusé alors car "Claude Code ne résout pas davantage le problème") — le contexte a changé : le goulot d'étranglement identifié en session 3 était la perte de contexte entre sessions, celui identifié en session 7 est la friction du copier-coller de fichiers volumineux au sein même d'une session active.

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
