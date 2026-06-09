-- Global Chat Ingestion Layer (draft schema)

create table if not exists canonical_message (
    message_id uuid primary key,
    source_platform text not null,
    source_workspace text,
    source_channel text,
    source_message_id text not null,
    author_id text,
    author_display text,
    role text not null,
    body_text text not null,
    body_markdown text,
    body_hash_blake3 text not null,
    created_at timestamptz,
    ingested_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    unique (source_platform, source_workspace, source_channel, source_message_id)
);

create table if not exists canonical_message_classification (
    id bigserial primary key,
    message_id uuid not null references canonical_message(message_id) on delete cascade,
    topic text,
    intent text,
    domain text,
    confidence double precision,
    labels text[] not null default '{}',
    created_at timestamptz not null default now()
);

create table if not exists canonical_message_embedding (
    id bigserial primary key,
    message_id uuid not null references canonical_message(message_id) on delete cascade,
    embedding_model text not null,
    embedding_vector double precision[] not null,
    embedded_at timestamptz not null default now(),
    unique (message_id, embedding_model)
);

create table if not exists idea_candidate (
    idea_id uuid primary key,
    message_id uuid not null references canonical_message(message_id) on delete cascade,
    title text not null,
    summary text not null,
    feasibility_score double precision not null,
    impact_score double precision not null,
    novelty_score double precision not null,
    ranking_score double precision not null,
    extracted_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_canonical_message_platform_created
    on canonical_message (source_platform, created_at desc);

create index if not exists idx_canonical_message_hash
    on canonical_message (body_hash_blake3);

create index if not exists idx_message_classification_topic_intent
    on canonical_message_classification (topic, intent);

create index if not exists idx_idea_candidate_ranking
    on idea_candidate (ranking_score desc);
