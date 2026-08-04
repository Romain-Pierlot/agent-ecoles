# Agent Écoles

Plateforme d'information sur les collèges construite à partir des données publiques du Ministère de l'Éducation Nationale : fiches établissement, carte scolaire, calendrier, guides pédagogiques et agent conversationnel.

## Stack technique
- Python + LangGraph + LangChain
- SQLite (données du Ministère de l'Éducation Nationale)
- ChromaDB (recherche documentaire) + text-embedding-3-small (embedding)
- GPT-4o-mini
- FastAPI (API backend)
- sqlglot (validation du SQL généré par le LLM avant exécution)
- Supabase / PostgreSQL (journalisation des conversations)
- Next.js / React / TypeScript (frontend)
- Tailwind CSS
- react-markdown + remark-gfm (rendu du contenu éditorial)
- Leaflet / react-leaflet (carte de localisation)
- Recharts (graphiques)
- Umami (analytics)
- LangSmith

## Structure du projet
- `data/` : scripts d'ingestion CSV → SQLite
- `agent/` : orchestrateur LangGraph + outils
- `api/` : API HTTP (FastAPI) au-dessus de l'agent
- `web/` : frontend Next.js
- `rag/` : pipeline ingestion documentaire
- `evaluation/` : golden dataset + harness
- `guardrails/` : règles et tests
- `docs/` : fiches architecture et conception
