# SSOT Agent Capabilities

## Read-Only Capabilities

- `scan`: discover files and produce manifests without modification.
- `resolve`: translate `z://<uuid7>` references to canonical paths.
- `inspect`: read metadata, hashes, versions, and relationship graphs.

## Write Capabilities

- `ingest`: store manifest data in Postgres.
- `canonicalize`: materialize canonical copies and record integrity checks.
- `shortcuts`: create symlink-based access paths for non-system files.

## Safety Boundaries

- Agents in read-only roles must never mutate canonical storage.
- Only canonicalization roles may write into `/ssot/blake3/<hash>`.
- Shortcut creation is allowed only for non-system files.
- All agent actions must be deterministic and idempotent.
