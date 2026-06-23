# Agent Écoles

Agent conversationnel d'aide au choix d'établissement scolaire (collèges) basé sur les données officielles du Ministère de l'Éducation Nationale.

## Stack technique
- Python + LangGraph + LangChain
- SQLite (données IPS, IVAC, Annuaire)
- ChromaDB (RAG méthodologie DEPP)
- GPT-4o-mini
- Streamlit
- LangSmith

## Structure du projet
- `data/` — scripts d'ingestion CSV → SQLite
- `agent/` — orchestrateur LangGraph + outils
- `rag/` — pipeline ingestion docs DEPP
- `app/` — interface Streamlit
- `evaluation/` — golden dataset + harness
- `guardrails/` — règles et tests
- `docs/` — fiches architecture et conception

## Données sources
Données publiques data.education.gouv.fr — IPS collèges, IVAC valeur ajoutée, Annuaire établissements.
