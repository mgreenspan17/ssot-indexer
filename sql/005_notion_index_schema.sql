-- notion-index-schema
-- Use case: auditable Notion ingest and canonical snapshot storage inside the SSOT Postgres.

create schema if not exists notion_index;

create table if not exists notion_index.crawl_run (
    run_id text primary key,
    tenant_id text not null,
    workspace_id text not null,
    status text not null,
    scheduler_name text null,
    bounds_json jsonb not null default '{}'::jsonb,
    pages_discovered bigint not null default 0,
    pages_indexed bigint not null default 0,
    blocks_indexed bigint not null default 0,
    api_calls bigint not null default 0,
    crawl_run_merkle_root text null,
    started_at timestamptz not null default now(),
    finished_at timestamptz null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists ix_notion_index_crawl_run_tenant_workspace_started
    on notion_index.crawl_run (tenant_id, workspace_id, started_at desc);

create index if not exists ix_notion_index_crawl_run_status
    on notion_index.crawl_run (status);

create table if not exists notion_index.raw_artifact (
    artifact_id text primary key,
    run_id text not null references notion_index.crawl_run(run_id) on delete cascade,
    tenant_id text not null,
    workspace_id text not null,
    artifact_type text not null,
    source_path text not null,
    storage_path text null,
    artifact_file_blake3 text not null,
    byte_size bigint not null,
    line_count bigint not null default 0,
    record_count bigint not null default 0,
    mime_type text null,
    created_at timestamptz not null default now()
);

create unique index if not exists ux_notion_index_raw_artifact_hash
    on notion_index.raw_artifact (tenant_id, workspace_id, artifact_file_blake3);

create index if not exists ix_notion_index_raw_artifact_run
    on notion_index.raw_artifact (run_id, artifact_type);

create table if not exists notion_index.ingest_batch (
    batch_id text primary key,
    run_id text not null references notion_index.crawl_run(run_id) on delete cascade,
    tenant_id text not null,
    workspace_id text not null,
    artifact_id text not null references notion_index.raw_artifact(artifact_id) on delete cascade,
    batch_seq integer not null,
    validation_status text not null,
    record_count bigint not null default 0,
    ingest_batch_merkle_root text not null,
    verified_at timestamptz null,
    created_at timestamptz not null default now()
);

create unique index if not exists ux_notion_index_ingest_batch_run_seq
    on notion_index.ingest_batch (run_id, batch_seq);

create index if not exists ix_notion_index_ingest_batch_run_verified
    on notion_index.ingest_batch (run_id, verified_at desc);

create table if not exists notion_index.merkle_tree (
    tree_id text primary key,
    run_id text not null references notion_index.crawl_run(run_id) on delete cascade,
    batch_id text null references notion_index.ingest_batch(batch_id) on delete cascade,
    tenant_id text not null,
    workspace_id text not null,
    tree_type text not null,
    algorithm text not null default 'blake3',
    leaf_count bigint not null,
    root_hash text not null,
    computed_at timestamptz not null default now()
);

create unique index if not exists ux_notion_index_merkle_tree_batch_type
    on notion_index.merkle_tree (batch_id, tree_type);

create index if not exists ix_notion_index_merkle_tree_run_type
    on notion_index.merkle_tree (run_id, tree_type);

create table if not exists notion_index.merkle_node (
    node_id text primary key,
    tree_id text not null references notion_index.merkle_tree(tree_id) on delete cascade,
    level integer not null,
    position integer not null,
    node_kind text not null,
    node_hash text not null,
    left_hash text null,
    right_hash text null,
    record_blake3 text null,
    created_at timestamptz not null default now()
);

create unique index if not exists ux_notion_index_merkle_node_tree_level_pos
    on notion_index.merkle_node (tree_id, level, position);

create index if not exists ix_notion_index_merkle_node_tree_hash
    on notion_index.merkle_node (tree_id, node_hash);

create table if not exists notion_index.object_snapshot (
    snapshot_id text primary key,
    tenant_id text not null,
    workspace_id text not null,
    run_id text not null references notion_index.crawl_run(run_id) on delete cascade,
    artifact_id text null references notion_index.raw_artifact(artifact_id) on delete set null,
    batch_id text null references notion_index.ingest_batch(batch_id) on delete set null,
    object_type text not null,
    object_id text not null,
    parent_id text null,
    source_version text null,
    record_blake3 text not null,
    raw_json_blake3 text not null,
    normalized_content_blake3 text not null,
    structure_blake3 text not null,
    observed_at timestamptz not null default now(),
    raw_payload jsonb not null default '{}'::jsonb
);

create unique index if not exists ux_notion_index_object_snapshot_identity
    on notion_index.object_snapshot (tenant_id, workspace_id, object_id, source_version, observed_at);

create index if not exists ix_notion_index_object_snapshot_object
    on notion_index.object_snapshot (tenant_id, workspace_id, object_type, observed_at desc);

create table if not exists notion_index.object_current (
    tenant_id text not null,
    workspace_id text not null,
    object_id text not null,
    latest_snapshot_id text not null references notion_index.object_snapshot(snapshot_id) on delete restrict,
    object_type text not null,
    parent_id text null,
    current_version text null,
    current_hash text not null,
    archived boolean not null default false,
    latest_seen_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (tenant_id, workspace_id, object_id)
);

create index if not exists ix_notion_index_object_current_tenant_workspace
    on notion_index.object_current (tenant_id, workspace_id, latest_seen_at desc);

create index if not exists ix_notion_index_object_current_parent
    on notion_index.object_current (tenant_id, workspace_id, parent_id);

create table if not exists notion_index.parent_edge (
    edge_id text primary key,
    tenant_id text not null,
    workspace_id text not null,
    run_id text not null references notion_index.crawl_run(run_id) on delete cascade,
    parent_id text not null,
    child_id text not null,
    parent_type text null,
    child_type text null,
    edge_type text not null,
    effective_at timestamptz not null default now(),
    record_blake3 text not null
);

create index if not exists ix_notion_index_parent_edge_parent
    on notion_index.parent_edge (tenant_id, workspace_id, parent_id, effective_at desc);

create index if not exists ix_notion_index_parent_edge_child
    on notion_index.parent_edge (tenant_id, workspace_id, child_id, effective_at desc);

create table if not exists notion_index.block_snapshot (
    block_snapshot_id text primary key,
    tenant_id text not null,
    workspace_id text not null,
    run_id text not null references notion_index.crawl_run(run_id) on delete cascade,
    artifact_id text null references notion_index.raw_artifact(artifact_id) on delete set null,
    batch_id text null references notion_index.ingest_batch(batch_id) on delete set null,
    page_id text not null,
    block_id text not null,
    parent_block_id text null,
    block_type text not null,
    depth integer not null default 0,
    position integer not null default 0,
    record_blake3 text not null,
    raw_json_blake3 text not null,
    normalized_content_blake3 text not null,
    structure_blake3 text not null,
    observed_at timestamptz not null default now(),
    raw_payload jsonb not null default '{}'::jsonb
);

create index if not exists ix_notion_index_block_snapshot_block
    on notion_index.block_snapshot (tenant_id, workspace_id, block_id, observed_at desc);

create index if not exists ix_notion_index_block_snapshot_page
    on notion_index.block_snapshot (tenant_id, workspace_id, page_id, position);

create table if not exists notion_index.blob_pointer (
    blob_pointer_id text primary key,
    tenant_id text not null,
    workspace_id text not null,
    blob_blake3 text not null,
    object_store_path text not null,
    byte_size bigint not null,
    mime_type text null,
    source_kind text not null,
    source_url text null,
    ref_count bigint not null default 1,
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now()
);

create unique index if not exists ux_notion_index_blob_pointer_hash
    on notion_index.blob_pointer (tenant_id, workspace_id, blob_blake3);

create index if not exists ix_notion_index_blob_pointer_tenant_workspace
    on notion_index.blob_pointer (tenant_id, workspace_id, source_kind, last_seen_at desc);

create table if not exists notion_index.status_event (
    status_event_id text primary key,
    tenant_id text not null,
    workspace_id text not null,
    run_id text null references notion_index.crawl_run(run_id) on delete set null,
    event_type text not null,
    severity text not null default 'info',
    message text not null,
    payload_json jsonb not null default '{}'::jsonb,
    status_hash text not null,
    observed_at timestamptz not null default now()
);

create index if not exists ix_notion_index_status_event_run
    on notion_index.status_event (run_id, observed_at desc);

create index if not exists ix_notion_index_status_event_tenant_workspace
    on notion_index.status_event (tenant_id, workspace_id, observed_at desc);
