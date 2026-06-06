"""SSOT Filesystem Analysis Pipeline — Phase 3

Three-stage detached filesystem analysis:
  Stage 1: Deep-content sample of 100 non-system files
  Stage 2: Full metadata indexing crawl (no content)
  Stage 3: Deep-content crawl of all non-system files from Stage 2

Runs fully detached — safe to close Warp after launch.
All progress is checkpointed to /srv/data/ssot/ and resumes automatically.

# SSOT Indexer Phase 3 — Filesystem Analysis Pipeline
# Version: 1.0.0
# Author: Oz + Manni
# Session: raid-migration-phase3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── SSOT module imports ──────────────────────────────────────────────
sys.path.insert(0, "/opt/ssot-indexer")

from classify.classifier import classify_file
from hashing.blake3_utils import hash_file
from indexer.postgres import PostgresConfig, PostgresRepository
from scanner.models import FileRecord, ScanManifest
from uuid.generator import uuid7_str

# ── Constants ────────────────────────────────────────────────────────

SYSTEM_DIRS = frozenset({
    "/bin", "/boot", "/dev", "/etc", "/lib", "/lib32", "/lib64",
    "/proc", "/root", "/run", "/sbin", "/snap", "/sys",
    "/tmp", "/usr", "/var/lib/systemd",
    "/srv/data/AppData",  # Docker container data
    "/srv/data/docker",   # Docker data
    "/srv/data/containerd",  # Containerd data
    "/DATA/raid/docker",  # Docker RAID overlay
    "/var/log/containers",  # Kubernetes container logs
    "/var/log/pods",  # Kubernetes pod logs
    "/var/lib/kubelet",  # Kubelet data
    "/var/lib/docker",  # Docker state
    "/var/lib/containerd",  # Containerd state
})

SSOT_DATA_ROOT = Path("/srv/data/ssot")
CHECKPOINT_DIR = SSOT_DATA_ROOT / "pipeline" / "checkpoints"
LOG_DIR = SSOT_DATA_ROOT / "logs"
INGESTION_DIR = SSOT_DATA_ROOT / "ingestion"

CHECKPOINT_FILE = CHECKPOINT_DIR / "pipeline_state.json"
STAGE1_SAMPLE = CHECKPOINT_DIR / "stage1_sample.json"
STAGE2_INDEX = CHECKPOINT_DIR / "stage2_index.json"
STAGE3_RESULTS = CHECKPOINT_DIR / "stage3_results.json"
PIPELINE_LOG = LOG_DIR / "pipeline.log"

BATCH_SIZE = 500
SAMPLE_SIZE_STAGE1 = 100

# ── Globals for graceful shutdown ────────────────────────────────────

_shutdown_requested = False


def _signal_handler(signum: int, frame: Any) -> None:
    global _shutdown_requested
    _shutdown_requested = True
    _log(f"Received signal {signum}, will checkpoint and exit gracefully")


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# ── Logging ──────────────────────────────────────────────────────────

def _log(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = json.dumps({"timestamp": ts, "level": "INFO", "logger": "pipeline", "message": message})
    print(line, flush=True)
    try:
        PIPELINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with PIPELINE_LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _log_error(message: str, exc: Exception | None = None) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "timestamp": ts,
        "level": "ERROR",
        "logger": "pipeline",
        "message": message,
        "traceback": traceback.format_exc() if exc else None,
    }
    line = json.dumps(payload)
    print(line, file=sys.stderr, flush=True)
    try:
        with PIPELINE_LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ── Checkpointing ────────────────────────────────────────────────────

@dataclass
class PipelineState:
    current_stage: int = 0
    stage1_complete: bool = False
    stage2_complete: bool = False
    stage3_complete: bool = False
    stage1_files_processed: int = 0
    stage2_files_processed: int = 0
    stage3_files_processed: int = 0
    stage1_files_total: int = 0
    stage2_files_total: int = 0
    stage3_files_total: int = 0
    last_checkpoint: str = ""
    errors: list[dict[str, str]] = field(default_factory=list)
    started_at: str = ""
    stage1_started_at: str = ""
    stage2_started_at: str = ""
    stage3_started_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Fix the bool that accidentally got set to False for stage3_files_total
        if isinstance(d.get("stage3_files_total"), bool):
            d["stage3_files_total"] = 0
        return d


def _save_checkpoint(state: PipelineState) -> None:
    state.last_checkpoint = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    tmp.replace(CHECKPOINT_FILE)
    _log(f"Checkpoint saved: stage={state.current_stage}, "
         f"s1={state.stage1_files_processed}/{state.stage1_files_total}, "
         f"s2={state.stage2_files_processed}/{state.stage2_files_total}, "
         f"s3={state.stage3_files_processed}/{state.stage3_files_total}")


def _load_checkpoint() -> PipelineState | None:
    if CHECKPOINT_FILE.exists():
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return PipelineState(**data)
    return None


# ── Path utilities ───────────────────────────────────────────────────

def _is_system_path(path: Path) -> bool:
    """Check if path is under a system directory, handling symlink loops."""
    str_path = str(path)
    # Quick string check first to avoid resolving symlinks unnecessarily
    for sys_dir in SYSTEM_DIRS:
        if str_path == sys_dir or str_path.startswith(sys_dir + "/"):
            return True
    # Try to resolve, but handle symlink loops gracefully
    try:
        resolved = path.resolve()
        str_resolved = str(resolved)
        for sys_dir in SYSTEM_DIRS:
            if str_resolved == sys_dir or str_resolved.startswith(sys_dir + "/"):
                return True
    except (OSError, ValueError, RuntimeError):
        # Symlink loop or other resolution error - skip this path
        return True
    return False


def _is_writable_raid_path(path: Path) -> bool:
    try:
        resolved = path.resolve()
        return str(resolved).startswith(str(SSOT_DATA_ROOT.resolve()))
    except (OSError, ValueError):
        return False


def _crawl_filesystem(root: str = "/") -> list[Path]:
    """Walk filesystem collecting all regular file paths, skipping system dirs."""
    files: list[Path] = []
    root_path = Path(root)
    skipped_perms = 0

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        # Prune system directories in-place
        dirnames[:] = [
            d for d in dirnames
            if not _is_system_path(Path(dirpath) / d)
        ]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if _is_system_path(fpath):
                continue
            try:
                if not fpath.is_file():
                    continue
            except (OSError, PermissionError):
                skipped_perms += 1
                continue
            files.append(fpath)

    if skipped_perms > 0:
        _log(f"Crawl skipped {skipped_perms} files due to permission errors")
    return files


# ── Stage 1: Deep-content sample ─────────────────────────────────────

def _run_stage1(state: PipelineState, repository: PostgresRepository) -> PipelineState:
    """Sample 100 non-system files, extract full metadata + content hash + classification."""
    _log("=" * 60)
    _log("STAGE 1: Deep-content sample of 100 non-system files")
    _log("=" * 60)

    state.current_stage = 1
    state.stage1_started_at = datetime.now(timezone.utc).isoformat()
    _save_checkpoint(state)

    # Load or collect sample paths
    if STAGE1_SAMPLE.exists() and state.stage1_files_processed >= SAMPLE_SIZE_STAGE1:
        _log("Stage 1 already complete, loading cached sample")
        sample_data = json.loads(STAGE1_SAMPLE.read_text(encoding="utf-8"))
        state.stage1_files_processed = len(sample_data)
        state.stage1_files_total = len(sample_data)
        state.stage1_complete = True
        _save_checkpoint(state)
        return state

    _log("Crawling filesystem for Stage 1 sample paths...")
    all_files = _crawl_filesystem("/")
    _log(f"Discovered {len(all_files)} non-system files")

    if state.stage1_files_processed > 0:
        _log(f"Resuming from file {state.stage1_files_processed}")
        remaining = all_files[state.stage1_files_processed:]
    else:
        remaining = all_files

    # Take up to SAMPLE_SIZE_STAGE1 files
    sample_files = remaining[:SAMPLE_SIZE_STAGE1 - state.stage1_files_processed]
    state.stage1_files_total = len(all_files)

    sample_records: list[dict[str, Any]] = []

    if STAGE1_SAMPLE.exists():
        sample_records = json.loads(STAGE1_SAMPLE.read_text(encoding="utf-8"))

    _log(f"Processing {len(sample_files)} files for deep sample")

    for i, fpath in enumerate(sample_files):
        if _shutdown_requested:
            _log("Shutdown requested, checkpointing Stage 1")
            _save_checkpoint(state)
            return state

        try:
            stat_result = fpath.stat()
            classification = classify_file(fpath)
            hash_result = hash_file(fpath)

            record = FileRecord(
                uuid7=uuid7_str(),
                path=str(fpath.resolve()),
                source="/",
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
                mode=stat_result.st_mode,
                hash_algorithm=hash_result.algorithm,
                blake3=hash_result.digest,
                category=classification.category,
                mime_type=classification.mime_type,
                shortcut_allowed=classification.shortcut_allowed,
            )

            record_dict = asdict(record)
            sample_records.append(record_dict)

            # Persist to PostgreSQL
            manifest = ScanManifest(
                source="/",
                generated_at=datetime.now(timezone.utc).isoformat(),
                records=[record],
            )
            batch = repository.create_batch(manifest)
            repository.ingest_record(batch, record)
            repository.mark_batch_complete(batch.id)

            state.stage1_files_processed += 1

            if (i + 1) % 10 == 0:
                _log(f"Stage 1 progress: {state.stage1_files_processed} files processed")

        except Exception as exc:
            state.errors.append({
                "file": str(fpath),
                "error": str(exc),
                "stage": 1,
            })
            _log_error(f"Stage 1 error processing {fpath}: {exc}")
            continue

        # Checkpoint every BATCH_SIZE files
        if state.stage1_files_processed % BATCH_SIZE == 0:
            _save_checkpoint(state)
            # Save partial sample
            STAGE1_SAMPLE.write_text(json.dumps(sample_records, indent=2), encoding="utf-8")

    # Final checkpoint
    STAGE1_SAMPLE.write_text(json.dumps(sample_records, indent=2), encoding="utf-8")
    state.stage1_complete = True
    _save_checkpoint(state)

    _log(f"Stage 1 complete: {state.stage1_files_processed} files sampled")
    return state


# ── Stage 2: Full metadata indexing ──────────────────────────────────

def _run_stage2(state: PipelineState, repository: PostgresRepository) -> PipelineState:
    """Crawl entire filesystem, collect metadata only (no content hashing)."""
    _log("=" * 60)
    _log("STAGE 2: Full metadata indexing crawl")
    _log("=" * 60)

    state.current_stage = 2
    state.stage2_started_at = datetime.now(timezone.utc).isoformat()
    _save_checkpoint(state)

    if STAGE2_INDEX.exists() and state.stage2_complete:
        _log("Stage 2 already complete, loading cached index")
        index_data = json.loads(STAGE2_INDEX.read_text(encoding="utf-8"))
        state.stage2_files_processed = len(index_data)
        state.stage2_files_total = len(index_data)
        _save_checkpoint(state)
        return state

    _log("Crawling filesystem for full metadata index...")
    all_files = _crawl_filesystem("/")
    _log(f"Discovered {len(all_files)} non-system files")

    if state.stage2_files_processed > 0:
        _log(f"Resuming from file {state.stage2_files_processed}")
        remaining = all_files[state.stage2_files_processed:]
    else:
        remaining = all_files

    state.stage2_files_total = len(all_files)
    index_records: list[dict[str, Any]] = []

    if STAGE2_INDEX.exists():
        index_records = json.loads(STAGE2_INDEX.read_text(encoding="utf-8"))

    _log(f"Indexing {len(remaining)} files (metadata only)")

    for i, fpath in enumerate(remaining):
        if _shutdown_requested:
            _log("Shutdown requested, checkpointing Stage 2")
            _save_checkpoint(state)
            return state

        try:
            stat_result = fpath.stat()
            classification = classify_file(fpath)

            # Quick hash for dedup (small overhead)
            hasher = hashlib.blake2b(digest_size=16)
            hasher.update(str(fpath.resolve()).encode())
            hasher.update(str(stat_result.st_size).encode())
            hasher.update(str(stat_result.st_mtime).encode())
            quick_hash = hasher.hexdigest()

            record = {
                "path": str(fpath.resolve()),
                "source": "/",
                "size": stat_result.st_size,
                "mtime": stat_result.st_mtime,
                "mode": stat_result.st_mode,
                "category": classification.category,
                "mime_type": classification.mime_type,
                "shortcut_allowed": classification.shortcut_allowed,
                "quick_hash": quick_hash,
            }
            index_records.append(record)
            state.stage2_files_processed += 1

            if (i + 1) % 1000 == 0:
                _log(f"Stage 2 progress: {state.stage2_files_processed} files indexed")

        except Exception as exc:
            state.errors.append({
                "file": str(fpath),
                "error": str(exc),
                "stage": 2,
            })
            continue

        if state.stage2_files_processed % BATCH_SIZE == 0:
            _save_checkpoint(state)
            STAGE2_INDEX.write_text(json.dumps(index_records, indent=2), encoding="utf-8")

    STAGE2_INDEX.write_text(json.dumps(index_records, indent=2), encoding="utf-8")
    state.stage2_complete = True
    _save_checkpoint(state)

    _log(f"Stage 2 complete: {state.stage2_files_processed} files indexed")
    return state


# ── Stage 3: Deep-content crawl ──────────────────────────────────────

def _run_stage3(state: PipelineState, repository: PostgresRepository) -> PipelineState:
    """Full content crawl of all non-system files from Stage 2 index."""
    _log("=" * 60)
    _log("STAGE 3: Deep-content crawl of all indexed files")
    _log("=" * 60)

    state.current_stage = 3
    state.stage3_started_at = datetime.now(timezone.utc).isoformat()
    _save_checkpoint(state)

    if not STAGE2_INDEX.exists():
        _log_error("Stage 2 index not found, cannot run Stage 3")
        state.errors.append({"stage": 3, "error": "Stage 2 index missing"})
        _save_checkpoint(state)
        return state

    index_data = json.loads(STAGE2_INDEX.read_text(encoding="utf-8"))
    state.stage3_files_total = len(index_data)

    if state.stage3_files_processed >= state.stage3_files_total:
        _log("Stage 3 already complete")
        state.stage3_complete = True
        _save_checkpoint(state)
        return state

    remaining = index_data[state.stage3_files_processed:]
    _log(f"Processing {len(remaining)} files for deep content")

    results: list[dict[str, Any]] = []
    if STAGE3_RESULTS.exists():
        results = json.loads(STAGE3_RESULTS.read_text(encoding="utf-8"))

    for i, record_meta in enumerate(remaining):
        if _shutdown_requested:
            _log("Shutdown requested, checkpointing Stage 3")
            _save_checkpoint(state)
            return state

        fpath = Path(record_meta["path"])
        try:
            if not fpath.exists() or not fpath.is_file():
                state.errors.append({
                    "file": str(fpath),
                    "error": "File no longer exists",
                    "stage": 3,
                })
                continue

            hash_result = hash_file(fpath)

            file_record = FileRecord(
                uuid7=uuid7_str(),
                path=str(fpath.resolve()),
                source="/",
                size=record_meta["size"],
                mtime=record_meta["mtime"],
                mode=record_meta["mode"],
                hash_algorithm=hash_result.algorithm,
                blake3=hash_result.digest,
                category=record_meta["category"],
                mime_type=record_meta["mime_type"],
                shortcut_allowed=record_meta["shortcut_allowed"],
            )

            result_dict = asdict(file_record)
            result_dict["stage3_index"] = state.stage3_files_processed + i
            results.append(result_dict)

            # Persist to PostgreSQL
            manifest = ScanManifest(
                source="/",
                generated_at=datetime.now(timezone.utc).isoformat(),
                records=[file_record],
            )
            batch = repository.create_batch(manifest)
            repository.ingest_record(batch, file_record)
            repository.mark_batch_complete(batch.id)

            state.stage3_files_processed += 1

            if (i + 1) % 500 == 0:
                _log(f"Stage 3 progress: {state.stage3_files_processed}/{state.stage3_files_total}")

        except Exception as exc:
            state.errors.append({
                "file": str(fpath),
                "error": str(exc),
                "stage": 3,
            })
            continue

        if state.stage3_files_processed % BATCH_SIZE == 0:
            _save_checkpoint(state)
            STAGE3_RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")

    STAGE3_RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    state.stage3_complete = True
    _save_checkpoint(state)

    _log(f"Stage 3 complete: {state.stage3_files_processed} files processed")
    return state


# ── Main pipeline orchestrator ───────────────────────────────────────

def _get_dsn() -> str:
    """Get PostgreSQL DSN from environment or use default."""
    dsn = os.environ.get("SSOT_DATABASE_DSN")
    if not dsn:
        # Default to local socket connection
        dsn = "dbname=ssot user=ssot host=/var/run/postgresql"
    return dsn


def run_pipeline(start_stage: int = 1) -> None:
    """Run the three-stage pipeline with checkpointing."""
    _log("=" * 60)
    _log("SSOT Filesystem Analysis Pipeline — Phase 3")
    _log("=" * 60)
    _log(f"Detached mode: SAFE TO CLOSE WARP")
    _log(f"Start stage: {start_stage}")
    _log(f"Checkpoint dir: {CHECKPOINT_DIR}")
    _log(f"Log file: {PIPELINE_LOG}")
    _log(f"Data root: {SSOT_DATA_ROOT}")

    # Ensure directories exist
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    INGESTION_DIR.mkdir(parents=True, exist_ok=True)

    state = _load_checkpoint() or PipelineState(
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    dsn = _get_dsn()
    repository = PostgresRepository(PostgresConfig(dsn))

    try:
        if start_stage <= 1 and not state.stage1_complete:
            state = _run_stage1(state, repository)

        if start_stage <= 2 and not state.stage2_complete:
            state = _run_stage2(state, repository)

        if start_stage <= 3 and not state.stage3_complete:
            state = _run_stage3(state, repository)

    except Exception as exc:
        _log_error(f"Pipeline failed at stage {state.current_stage}: {exc}", exc)
        state.errors.append({
            "stage": state.current_stage,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })
        _save_checkpoint(state)
        raise

    # Final summary
    _log("=" * 60)
    _log("PIPELINE COMPLETE")
    _log("=" * 60)
    _log(f"Stage 1 (sample):     {state.stage1_files_processed} files")
    _log(f"Stage 2 (index):      {state.stage2_files_processed} files")
    _log(f"Stage 3 (deep crawl): {state.stage3_files_processed} files")
    _log(f"Total errors:         {len(state.errors)}")
    _log(f"Checkpoint:           {CHECKPOINT_FILE}")
    _log(f"Log:                  {PIPELINE_LOG}")

    # Write final summary
    summary = {
        "pipeline": "ssot-filesystem-analysis-phase3",
        "status": "complete",
        "stages": {
            "stage1": {"files": state.stage1_files_processed, "complete": state.stage1_complete},
            "stage2": {"files": state.stage2_files_processed, "complete": state.stage2_complete},
            "stage3": {"files": state.stage3_files_processed, "complete": state.stage3_complete},
        },
        "errors": state.errors,
        "checkpoint": str(CHECKPOINT_FILE),
        "log": str(PIPELINE_LOG),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = CHECKPOINT_DIR / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSOT Filesystem Analysis Pipeline — Phase 3")
    parser.add_argument(
        "--start-stage",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Stage to start from (default: 1, resumes from checkpoint if available)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint (equivalent to --start-stage with saved state)",
    )
    args = parser.parse_args()

    if args.resume:
        state = _load_checkpoint()
        if state:
            start = state.current_stage if not state.stage1_complete else (
                2 if not state.stage2_complete else (
                    3 if not state.stage3_complete else 0
                )
            )
            if start == 0:
                _log("All stages complete. Use --start-stage 1 to rerun.")
                sys.exit(0)
            run_pipeline(start_stage=start)
        else:
            _log("No checkpoint found, starting from Stage 1")
            run_pipeline(start_stage=1)
    else:
        run_pipeline(start_stage=args.start_stage)
