# Agent Écoles

Agent conversationnel d'aide au choix d'établissement scolaire (collèges) basé sur les données officielles du Ministère de l'Éducation Nationale.

## Stack technique
- Python + LangGraph + LangChain
- SQLite (données IPS, IVAC, Annuaire)
- ChromaDB (RAG méthodologie DEPP) + sentence-transformers (re-ranking)
- GPT-4o-mini
- FastAPI (API backend)
- sqlglot (validation du SQL généré par le LLM avant exécution)
- Supabase / PostgreSQL (journalisation des conversations)
- Next.js / React / TypeScript (frontend)
- Tailwind CSS
- Leaflet / react-leaflet (carte de localisation)
- Recharts (graphiques)
- Umami (analytics)
- LangSmith

## Structure du projet
- `data/` — scripts d'ingestion CSV → SQLite
- `agent/` — orchestrateur LangGraph + outils
- `api/` — API HTTP (FastAPI) au-dessus de l'agent
- `web/` — frontend Next.js
- `rag/` — pipeline ingestion docs DEPP
- `evaluation/` — golden dataset + harness
- `guardrails/` — règles et tests
- `docs/` — fiches architecture et conception

## Données sources
Données publiques data.education.gouv.fr — IPS collèges, IVAC valeur ajoutée, Annuaire établissements.
