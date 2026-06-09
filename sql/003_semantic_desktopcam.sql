-- Semantic Similarity Layer
create table if not exists semantic_cluster (
    cluster_id uuid primary key,
    canonical_file_ids uuid[] not null,
    similarity_scores jsonb not null default '{}'::jsonb,
    representative_embedding double precision[] not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists semantic_membership (
    cluster_id uuid not null references semantic_cluster(cluster_id) on delete cascade,
    file_id uuid not null references files(id) on delete cascade,
    canonical_file_id uuid not null references files(id) on delete cascade,
    similarity_score double precision not null,
    primary key (cluster_id, file_id)
);

create index if not exists idx_semantic_membership_file_id on semantic_membership(file_id);
create index if not exists idx_semantic_membership_canonical_id on semantic_membership(canonical_file_id);

-- DesktopCam Forensic Layer
create table if not exists desktopcam_frame (
    frame_id uuid primary key,
    timestamp_uuid7 uuid not null,
    session_id uuid not null,
    device_id text not null,
    file_id uuid not null references files(id),
    version_id uuid not null references versions(id),
    blake3_hash text not null,
    bytes_size bigint not null,
    created_at timestamptz not null default now()
);

create table if not exists audit_event (
    event_id uuid primary key,
    timestamp_uuid7 uuid not null,
    blake3_hash text not null,
    frame_id uuid not null references desktopcam_frame(frame_id),
    previous_event_hash text,
    event_hash text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_audit_event_frame_id on audit_event(frame_id);
create index if not exists idx_audit_event_timestamp on audit_event(created_at);

-- Append-only enforcement for forensic audit table.
create or replace function prevent_audit_event_mutation()
returns trigger as $$
begin
    raise exception 'audit_event is append-only; % not allowed', tg_op;
end;
$$ language plpgsql;

drop trigger if exists trg_audit_event_no_update on audit_event;
create trigger trg_audit_event_no_update
before update on audit_event
for each row execute function prevent_audit_event_mutation();

drop trigger if exists trg_audit_event_no_delete on audit_event;
create trigger trg_audit_event_no_delete
before delete on audit_event
for each row execute function prevent_audit_event_mutation();
