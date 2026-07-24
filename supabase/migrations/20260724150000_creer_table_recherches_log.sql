-- Journal des recherches effectuées sur le site (par nom sur /recherche,
-- par adresse sur /carte-scolaire). Sert à l'analytics de recherche
-- (termes les plus tapés, recherches sans résultat, zones géographiques les
-- plus demandées) — distinct de conversations_log (échanges avec l'agent).
--
-- Une seule table pour les deux origines plutôt que deux tables séparées :
-- elles partagent l'essentiel (origine, horodatage), les colonnes propres à
-- chaque origine restent nullables plutôt que dupliquées. Aucune adresse
-- brute stockée pour carte_scolaire (uniquement la commune résolue par
-- géocodage) : une adresse précise est une donnée personnelle, la commune
-- ne l'est pas (cf. journal_de_bord.md).

create table recherches_log (
    id bigint generated always as identity primary key,
    page_origine text not null check (page_origine in ('recherche', 'carte_scolaire')),
    -- Rempli seulement pour page_origine = 'recherche'.
    terme text,
    nb_etablissements integer,
    nb_communes integer,
    -- Rempli seulement pour page_origine = 'carte_scolaire'.
    commune text,
    code_departement text,
    etat_carte_scolaire text,
    cree_le timestamptz not null default now()
);

create index recherches_log_page_origine_idx on recherches_log (page_origine);
create index recherches_log_cree_le_idx on recherches_log (cree_le);
