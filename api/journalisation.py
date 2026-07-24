"""api/journalisation.py — Écriture dans conversations_log et recherches_log.

Best-effort et non bloquant : une panne d'écriture (base éteinte, réseau,
etc.) ne doit jamais faire échouer ni ralentir la réponse. Toute erreur est
journalisée côté serveur, jamais propagée à l'appelant.
"""
import logging
import os

import psycopg

logger = logging.getLogger("api.journalisation")

_DB_URL = os.environ.get("SUPABASE_DB_URL")


def journaliser_echange(
    session_id: str,
    question: str,
    reponse: str,
    categorie: str | None = None,
    outils_appeles: list[str] | None = None,
    guardrail_declenche: str | None = None,
    latence_ms: int | None = None,
) -> None:
    if not _DB_URL:
        logger.warning("SUPABASE_DB_URL absent — échange non journalisé.")
        return

    try:
        with psycopg.connect(_DB_URL, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into conversations_log
                        (session_id, question, reponse, categorie,
                         outils_appeles, guardrail_declenche, latence_ms)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_id, question, reponse, categorie,
                        outils_appeles, guardrail_declenche, latence_ms,
                    ),
                )
    except Exception:
        logger.exception("Échec de la journalisation de l'échange (session=%s).", session_id)


def journaliser_recherche(
    page_origine: str,
    terme: str | None = None,
    nb_etablissements: int | None = None,
    nb_communes: int | None = None,
    commune: str | None = None,
    code_departement: str | None = None,
    etat_carte_scolaire: str | None = None,
) -> None:
    if not _DB_URL:
        logger.warning("SUPABASE_DB_URL absent — recherche non journalisée.")
        return

    try:
        with psycopg.connect(_DB_URL, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into recherches_log
                        (page_origine, terme, nb_etablissements, nb_communes,
                         commune, code_departement, etat_carte_scolaire)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        page_origine, terme, nb_etablissements, nb_communes,
                        commune, code_departement, etat_carte_scolaire,
                    ),
                )
    except Exception:
        logger.exception("Échec de la journalisation de la recherche (origine=%s).", page_origine)
