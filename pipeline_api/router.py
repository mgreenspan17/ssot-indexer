from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from pipeline_api.models import (
    CategoryCount,
    LiveStatusResponse,
    PipelineCategoriesResponse,
    PipelineErrorsResponse,
    PipelineStatusResponse,
    PipelineSummaryResponse,
    ProgressMetric,
)

CHECKPOINT_DIR = Path("/srv/data/ssot/pipeline/checkpoints")
INGESTION_MANIFEST = Path("/srv/data/ssot/ingestion/authoritative_manifest.json")
PIPELINE_STATE_FILE = CHECKPOINT_DIR / "pipeline_state.json"
PIPELINE_SUMMARY_FILE = CHECKPOINT_DIR / "pipeline_summary.json"
STAGE1_SAMPLE_FILE = CHECKPOINT_DIR / "stage1_sample.json"
STAGE2_INDEX_FILE = CHECKPOINT_DIR / "stage2_index.json"
STAGE3_RESULTS_FILE = CHECKPOINT_DIR / "stage3_results.json"
PIPELINE_LOG_FILE = Path("/srv/data/ssot/logs/pipeline.log")
PGDATA_DIRS = [
    Path("/srv/data/ssot/postgres-data/global"),
    Path("/srv/data/ssot/postgres-data/base"),
]
DB_ACTIVITY_WINDOW_SECONDS = 5

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


async def get_db_connection(request: Request) -> AsyncIterator[asyncpg.Connection]:
    pool: asyncpg.Pool | None = getattr(request.app.state, "pg_pool", None)
    if pool is None:
        raise HTTPException(status_code=500, detail="Database pool is not configured")

    connection = await pool.acquire()
    try:
        yield connection
    finally:
        await pool.release(connection)


def _progress(numerator: int, denominator: int) -> ProgressMetric:
    percent = 100.0 if denominator == 0 else round((numerator / denominator) * 100.0, 2)
    return ProgressMetric(numerator=numerator, denominator=denominator, percent=percent)


def _require_file(path: Path) -> Path:
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Required file not found: {path}")
    return path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_json_array(path: Path, chunk_size: int = 65536) -> Iterator[dict]:
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8") as infile:
        buffer = ""
        in_array = False

        while True:
            chunk = infile.read(chunk_size)
            if chunk:
                buffer += chunk

            index = 0
            length = len(buffer)

            while index < length and buffer[index].isspace():
                index += 1

            if not in_array:
                if index >= length:
                    if not chunk:
                        break
                    buffer = ""
                    continue

                if buffer[index] != "[":
                    raise ValueError("Manifest must be a JSON array")
                in_array = True
                index += 1

            while True:
                while index < length and buffer[index].isspace():
                    index += 1

                if index >= length:
                    break

                token = buffer[index]
                if token == "]":
                    return
                if token == ",":
                    index += 1
                    continue

                try:
                    value, next_index = decoder.raw_decode(buffer, index)
                except JSONDecodeError:
                    break

                if isinstance(value, dict):
                    yield value
                index = next_index

            if index > 0:
                buffer = buffer[index:]

            if not chunk:
                if buffer.strip():
                    raise ValueError("Unexpected trailing data in manifest")
                break


def _manifest_counts(path: Path) -> tuple[int, int, int]:
    total = 0
    canonical_count = 0
    shortcut_count = 0

    for record in _iter_json_array(path):
        total += 1
        category = str(record.get("category", "")).lower()
        if category == "canonical":
            canonical_count += 1
        if bool(record.get("shortcut_allowed")):
            shortcut_count += 1

    return total, canonical_count, shortcut_count


# ── Live-status helpers ──────────────────────────────────────────────


def _tail_log(path: Path, n_bytes: int = 4096) -> str:
    """Return last non-empty line from a log file without loading it fully."""
    if not path.exists() or not path.is_file():
        return ""
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            read_size = min(n_bytes, size)
            f.seek(-read_size, os.SEEK_END)
            tail = f.read(read_size).decode("utf-8", errors="replace")
        lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
        return lines[-1] if lines else ""
    except OSError:
        return ""


def _db_active(window_seconds: int = DB_ACTIVITY_WINDOW_SECONDS) -> bool:
    """Return True if any PostgreSQL data file changed within window_seconds."""
    cutoff = time.time() - window_seconds
    for base_dir in PGDATA_DIRS:
        try:
            if not base_dir.is_dir():
                continue
            for entry in os.scandir(base_dir):
                try:
                    if entry.stat().st_mtime >= cutoff:
                        return True
                except (OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            continue
    return False


def _parse_iso(ts: str | None) -> float | None:
    """Parse ISO-8601 UTC timestamp to POSIX float; None on failure."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


def _stage_elapsed(state: dict[str, Any], current_stage: int) -> float:
    """Compute elapsed seconds for the current stage."""
    now = time.time()
    key = f"stage{current_stage}_started_at"
    ts = _parse_iso(state.get(key))
    if ts is not None:
        return max(0.0, now - ts)
    # Fallback: use pipeline_state.json mtime
    try:
        mtime = PIPELINE_STATE_FILE.stat().st_mtime
        return max(0.0, now - mtime)
    except OSError:
        return 0.0


_STAGE_DESCRIPTIONS: dict[int, str] = {
    1: "Sampling filesystem…",
    2: "Building manifest…",
    3: "Hashing files…",
}

_NEXT_EVENTS: dict[int, str] = {
    1: "Waiting for Stage 1 sample…",
    2: "Waiting for Stage 2 manifest…",
    3: "Waiting for Stage 3 results…",
}


def _build_live_status() -> LiveStatusResponse:
    """Construct LiveStatusResponse from checkpoint files and system state."""
    state: dict[str, Any] = {}
    if PIPELINE_STATE_FILE.exists() and PIPELINE_STATE_FILE.is_file():
        try:
            state = json.loads(PIPELINE_STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}

    current_stage = int(state.get("current_stage") or 0)
    stage1_count = int(state.get("stage1_files_processed") or 0)
    stage2_count = int(state.get("stage2_files_processed") or 0)
    stage3_count = int(state.get("stage3_files_processed") or 0)
    filesystem_count = int(
        state.get("stage2_files_total")
        or state.get("stage1_files_total")
        or 0
    )

    stage1_complete = bool(state.get("stage1_complete"))
    stage2_complete = bool(state.get("stage2_complete"))
    stage3_complete = bool(state.get("stage3_complete"))

    # Determine active stage from completion flags when current_stage not set
    if current_stage == 0:
        if not stage1_complete:
            current_stage = 1
        elif not stage2_complete:
            current_stage = 2
        elif not stage3_complete:
            current_stage = 3

    pipeline_active = bool(state) and not (stage1_complete and stage2_complete and stage3_complete)

    stage1_json_missing = not STAGE1_SAMPLE_FILE.exists()
    crawl_phase = current_stage == 1 and stage1_json_missing
    if crawl_phase:
        crawl_progress = "indeterminate"
        crawl_message = "Filesystem crawl in progress…"
        stage_description = "Crawling filesystem…"
    else:
        crawl_progress = "available" if (STAGE1_SAMPLE_FILE.exists() or STAGE2_INDEX_FILE.exists()) else "pending"
        crawl_message = ""
        stage_description = _STAGE_DESCRIPTIONS.get(current_stage, "Idle")

    next_expected = _NEXT_EVENTS.get(current_stage, "Pipeline complete")
    if current_stage == 1 and not stage1_json_missing:
        next_expected = "Waiting for Stage 2 manifest…"

    elapsed = _stage_elapsed(state, current_stage) if current_stage > 0 else 0.0
    last_log = _tail_log(PIPELINE_LOG_FILE)
    db_active_now = _db_active()

    return LiveStatusResponse(
        current_stage=current_stage,
        stage_description=stage_description,
        stage_elapsed_seconds=round(elapsed, 2),
        pipeline_active=pipeline_active,
        db_active=db_active_now,
        next_expected_event=next_expected,
        last_log_line=last_log,
        filesystem_count=filesystem_count,
        stage1_count=stage1_count,
        stage2_count=stage2_count,
        stage3_count=stage3_count,
        crawl_phase=crawl_phase,
        crawl_progress=crawl_progress,
        crawl_message=crawl_message,
    )


@router.get("/live_status", response_model=LiveStatusResponse)
async def get_live_status() -> LiveStatusResponse:
    """Real-time pipeline activity telemetry; safe to call even before any stage JSON exists."""
    return await asyncio.to_thread(_build_live_status)


# ── Existing endpoints ────────────────────────────────────────────────


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    connection: asyncpg.Connection = Depends(get_db_connection),
) -> PipelineStatusResponse:
    state_path = _require_file(PIPELINE_STATE_FILE)
    manifest_path = _require_file(INGESTION_MANIFEST)

    state_data = await asyncio.to_thread(_load_json, state_path)
    manifest_total, canonical_count, shortcut_count = await asyncio.to_thread(
        _manifest_counts,
        manifest_path,
    )

    row = await connection.fetchrow("SELECT COUNT(*)::BIGINT AS count FROM files")
    db_indexed_count = int(row["count"]) if row and row["count"] is not None else 0

    stage1_count = int(state_data.get("stage1_files_processed") or 0)
    stage2_count = int(state_data.get("stage2_files_processed") or 0)
    stage3_count = int(state_data.get("stage3_files_processed") or 0)

    filesystem_count = int(
        state_data.get("stage2_files_total")
        or state_data.get("stage1_files_total")
        or manifest_total
        or 0
    )

    return PipelineStatusResponse(
        filesystem_count=filesystem_count,
        stage1_count=stage1_count,
        stage2_count=stage2_count,
        stage3_count=stage3_count,
        db_indexed_count=db_indexed_count,
        canonical_count=canonical_count,
        shortcut_count=shortcut_count,
        scanner_progress=_progress(stage2_count, filesystem_count),
        processed_progress=_progress(db_indexed_count, stage2_count),
        ingestion_progress=_progress(db_indexed_count, filesystem_count),
    )


@router.get("/manifest")
async def get_pipeline_manifest() -> FileResponse:
    manifest_path = _require_file(INGESTION_MANIFEST)
    return FileResponse(
        path=manifest_path,
        media_type="application/json",
        filename="authoritative_manifest.json",
    )


@router.get("/errors", response_model=PipelineErrorsResponse)
async def get_pipeline_errors() -> PipelineErrorsResponse:
    state_path = _require_file(PIPELINE_STATE_FILE)
    state_data = await asyncio.to_thread(_load_json, state_path)
    errors = state_data.get("errors", [])
    if not isinstance(errors, list):
        errors = []
    return PipelineErrorsResponse(errors=errors)


@router.get("/summary", response_model=PipelineSummaryResponse)
async def get_pipeline_summary() -> PipelineSummaryResponse:
    summary_path = _require_file(PIPELINE_SUMMARY_FILE)
    summary_data = await asyncio.to_thread(_load_json, summary_path)
    return PipelineSummaryResponse(**summary_data)


@router.get("/categories", response_model=PipelineCategoriesResponse)
async def get_pipeline_categories(
    connection: asyncpg.Connection = Depends(get_db_connection),
) -> PipelineCategoriesResponse:
    rows = await connection.fetch(
        """
        SELECT category, COUNT(*)::BIGINT AS count
        FROM files
        GROUP BY category
        ORDER BY COUNT(*) DESC
        """
    )

    categories = [
        CategoryCount(category=row["category"], count=int(row["count"]))
        for row in rows
    ]
    return PipelineCategoriesResponse(categories=categories)
