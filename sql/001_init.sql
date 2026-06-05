create extension if not exists pgcrypto;

create table if not exists ingestion_batches (
    id uuid primary key,
    source text not null,
    generated_at timestamptz not null,
    status text not null,
    manifest jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists files (
    id uuid primary key,
    path text not null,
    source text not null,
    canonical_hash text,
    category text not null,
    mime_type text not null,
    shortcut_allowed boolean not null default false,
    current_version_id uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists hashes (
    id bigserial primary key,
    algorithm text not null,
    digest text not null,
    size bigint not null,
    unique (algorithm, digest)
);

create table if not exists versions (
    id uuid primary key,
    file_id uuid not null references files(id) on delete cascade,
    ingestion_batch_id uuid not null references ingestion_batches(id) on delete cascade,
    version_number integer not null,
    hash_id bigint not null references hashes(id),
    size bigint not null,
    mtime double precision not null,
    mode integer not null,
    created_at timestamptz not null default now(),
    unique (file_id, version_number)
);

create table if not exists locations (
    id bigserial primary key,
    file_id uuid not null references files(id) on delete cascade,
    version_id uuid not null references versions(id) on delete cascade,
    path text not null,
    source text not null,
    is_canonical boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists metadata (
    id bigserial primary key,
    version_id uuid not null references versions(id) on delete cascade,
    data jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists classifications (
    id bigserial primary key,
    version_id uuid not null references versions(id) on delete cascade,
    category text not null,
    mime_type text not null,
    shortcut_allowed boolean not null,
    created_at timestamptz not null default now()
);

create table if not exists canonical_store (
    id bigserial primary key,
    file_id uuid not null references files(id) on delete cascade,
    version_id uuid not null references versions(id) on delete cascade,
    hash text not null,
    canonical_path text not null unique,
    verified boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists shortcuts (
    id bigserial primary key,
    file_id uuid not null references files(id) on delete cascade,
    version_id uuid not null references versions(id) on delete cascade,
    shortcut_path text not null unique,
    target_path text not null,
    shortcut_kind text not null,
    created_at timestamptz not null default now()
);
