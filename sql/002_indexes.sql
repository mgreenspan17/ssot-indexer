create index if not exists idx_files_path on files (path);
create index if not exists idx_versions_file_id on versions (file_id);
create index if not exists idx_locations_file_id on locations (file_id);
create index if not exists idx_canonical_hash on canonical_store (hash);
create index if not exists idx_shortcuts_file_id on shortcuts (file_id);
