# SSOT Indexer

SSOT Indexer is a modular file inventory and canonicalization system. It scans local and remote sources, computes BLAKE3 hashes, assigns UUID7 identities, classifies content, stores canonical copies, generates shortcuts for non-system files, ingests manifests into Postgres, and resolves `z://<uuid7>` paths back to canonical storage.

## What Ships

- `scanner`: recursive local scanning plus SSH and rclone-backed discovery
- `hashing`: BLAKE3 hashing utilities for files and bytes
- `uuid`: UUID7 generation while preserving stdlib `uuid` compatibility
- `classify` and `rules`: MIME, file type, and shortcut policy classification
- `indexer`: Postgres ingestion and batch tracking
- `canonical`: canonical store management and integrity verification
- `shortcuts`: safe shortcut generation
- `resolver`: `z://` path resolution
- `orchestrator`: end-to-end coordination, FastAPI app wiring, and scan/canonicalize flows
- `cli`: command-line entrypoints for scan, ingest, canonicalize, resolve, and serve
- `sql`: sequential schema and index migrations

## Requirements

- Python 3.9+
- Postgres 13+
- Optional: `rclone`, `ssh`, and symlink permission on Windows

## Install

```bash
python -m venv venv
.\\venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

```bash
python -m cli --help
python -m cli scan C:\\data --json manifest.json
python -m cli ingest manifest.json --dsn "postgresql://user:pass@localhost:5432/ssot"
python -m cli canonicalize manifest.json --dsn "postgresql://user:pass@localhost:5432/ssot" --storage-root C:\\ssot
python -m cli resolve z://<uuid7> --lookup-json lookup.json
python -m cli serve --host 127.0.0.1 --port 8000
```

## Scripts

The `scripts/` directory contains Warp-friendly Bash wrappers that resolve the repository root automatically.

```bash
./scripts/run_scan.sh
./scripts/run_api.sh
DATABASE_URL="postgresql://user:pass@localhost:5432/ssot" ./scripts/apply_migrations.sh
```

## API

- `GET /health`
- `POST /scan`
- `POST /resolve`

## Storage Layout

- Canonical files: `/ssot/blake3/<hash>`
- Shortcuts: `/ssot/shortcuts/<uuid7>`
- Resolver input: `z://<uuid7>`

## Validation

The repository currently validates with `pytest` in the project venv.
