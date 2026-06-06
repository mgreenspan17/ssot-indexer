# SSOT Pipeline API

## Run

1. Ensure dependencies are installed:

   ```bash
   pip install fastapi uvicorn asyncpg
   ```

2. Set database DSN (optional if default works):

   ```bash
   export SSOT_DATABASE_DSN='postgresql://ssot:ssot@127.0.0.1:5433/ssot'
   ```

3. Start the service:

   ```bash
   uvicorn pipeline_api.main:app --host 0.0.0.0 --port 8000
   ```

## Endpoints

- `GET /pipeline/live_status` — Real-time telemetry; safe at any pipeline phase including silent Stage 1 crawl window (no JSON required).
- `GET /pipeline/status` — Counts from checkpoint + manifest + DB (requires state and manifest files).
- `GET /pipeline/manifest` — Streamed authoritative Stage 2 manifest.
- `GET /pipeline/errors` — Errors array from pipeline_state.json.
- `GET /pipeline/summary` — pipeline_summary.json.
- `GET /pipeline/categories` — Category counts from PostgreSQL.

### GET /pipeline/live_status

Returns a `LiveStatusResponse` with zero hard file dependencies — all missing files return sane zero defaults.

Key fields:

| Field | Description |
|---|---|
| `current_stage` | 1 / 2 / 3 (0 = idle) |
| `stage_description` | Human-readable stage label |
| `stage_elapsed_seconds` | Seconds since stage started (fallback to state file mtime) |
| `pipeline_active` | `true` while any stage is incomplete |
| `db_active` | `true` if PostgreSQL data files touched in last 5 s |
| `next_expected_event` | What to watch for next |
| `last_log_line` | Last non-empty line from `pipeline.log` |
| `filesystem_count` | Discovered file count (0 until Stage 2 writes totals) |
| `stage1_count` | Files processed in Stage 1 (0 if not started) |
| `stage2_count` | Files processed in Stage 2 (0 if not started) |
| `stage3_count` | Files processed in Stage 3 (0 if not started) |
| `crawl_phase` | `true` while Stage 1 is running with no sample JSON yet |
| `crawl_progress` | `"indeterminate"` / `"available"` / `"pending"` |
| `crawl_message` | Human-readable crawl status message |

## Notes

- Checkpoint files are read from `/srv/data/ssot/pipeline/checkpoints/`.
- Authoritative manifest is read from `/srv/data/ssot/ingestion/authoritative_manifest.json`.
- `GET /pipeline/manifest` returns a streamed file response and does not load the manifest into memory.
