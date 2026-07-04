-- Journal des échanges question/réponse du chatbot.
-- Sert à la fois d'analytics et de vivier pour le futur golden dataset
-- (promotion manuelle/semi-automatique, jamais automatique — cf. journal_de_bord S10.6).

create table conversations_log (
    id bigint generated always as identity primary key,
    session_id text not null,
    question text not null,
    reponse text not null,
    categorie text,
    outils_appeles text[],
    guardrail_declenche text,
    latence_ms integer,
    cree_le timestamptz not null default now()
);

create index conversations_log_session_id_idx on conversations_log (session_id);
create index conversations_log_cree_le_idx on conversations_log (cree_le);
