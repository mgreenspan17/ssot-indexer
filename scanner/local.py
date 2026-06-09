from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from stat import S_ISREG
import time
from typing import Any

from classify.classifier import classify_file
from hashing.blake3_utils import dual_hash_file
from scanner.base import build_source_descriptor
from scanner.models import FileRecord, ScanManifest, SourceType
from uuid.generator import uuid7_str

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocalScanResult:
    manifest: ScanManifest


def _write_state(state_path: str | Path, state: dict[str, Any]) -> None:
    try:
        p = Path(state_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        temp_path = p.with_suffix(p.suffix + ".tmp")
        with open(temp_path, "w") as f:
            json.dump(state, f, indent=2)
        temp_path.replace(p)
    except Exception as e:
        logger.error(f"Failed to write scan state: {e}")


def scan_local_directory(
    root: str | Path,
    state_path: str | Path | None = None,
    total_estimate: int | None = None,
    roots_list: list[str] | None = None,
    current_root_idx: int = 0,
    total_roots: int = 1,
    existing_state: dict[str, Any] | None = None,
    jsonl_output_path: str | Path | None = None,
    completed_files: dict[str, float] | None = None,
) -> LocalScanResult:
    root_path = Path(root)
    records: list[FileRecord] = []
    descriptor = build_source_descriptor("local", root_path, source_label=root_path.name or str(root_path))
    
    started_at = datetime.now(timezone.utc).isoformat()
    if existing_state:
        state = existing_state
        state["current_root"] = str(root_path.resolve())
        state["current_root_index"] = current_root_idx
        start_time = time.time() - state.get("elapsed_seconds", 0.0)
    else:
        start_time = time.time()
        state = {
            "status": "scanning",
            "started_at": started_at,
            "current_file": "",
            "files_indexed": 0,
            "files_total_estimate": total_estimate or 0,
            "bytes_hashed": 0,
            "errors": 0,
            "error_log": [],
            "recent_files": [],
            "files_per_second": 0.0,
            "elapsed_seconds": 0.0,
            "eta_seconds": 0.0,
            "roots": roots_list or [str(root_path.resolve())],
            "current_root": str(root_path.resolve()),
            "current_root_index": current_root_idx,
            "total_roots": total_roots
        }

    if state_path:
        _write_state(state_path, state)

    import os
    
    last_log_time = time.time()
    
    exclusions = {"containerd", "docker", "lost+found", "cache", "caches", "temp", "tmp", "android"}
    if os.name == "nt":
        from scanner.base import WINDOWS_EXCLUDED_DIRS
        exclusions.update(d.lower() for d in WINDOWS_EXCLUDED_DIRS)
        # Exclude temporary, cache, and standard developer package directories by default
        exclusions.update({"appdata", "node_modules", ".git", "venv", ".venv", "$winreagent"})
    
    for current_root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d.lower() not in exclusions]
        for file_name in files:
            path = Path(current_root) / file_name
            abs_path_str = str(path)
            try:
                abs_path_str = str(path.resolve())
                state["current_file"] = abs_path_str
                
                # If already scanned and unmodified, skip hashing
                if completed_files and abs_path_str in completed_files:
                    try:
                        stat_result = path.stat()
                        if stat_result.st_mtime == completed_files[abs_path_str]:
                            state["files_indexed"] += 1
                            state["bytes_hashed"] += stat_result.st_size
                            continue
                    except Exception:
                        pass
                if state_path and time.time() - last_log_time > 0.5:
                    elapsed = time.time() - start_time
                    state["elapsed_seconds"] = round(elapsed, 2)
                    total_indexed = state["files_indexed"]
                    fps = total_indexed / elapsed if elapsed > 0 else 0.0
                    state["files_per_second"] = round(fps, 2)
                    
                    total_est = state["files_total_estimate"]
                    if total_est > total_indexed and fps > 0:
                        state["eta_seconds"] = round((total_est - total_indexed) / fps, 2)
                    else:
                        state["eta_seconds"] = 0.0
                        
                    _write_state(state_path, state)
                    last_log_time = time.time()
                    
                stat_result = path.stat()
                if not S_ISREG(stat_result.st_mode):
                    continue
                
                classification = classify_file(path)
                hash_result = dual_hash_file(path)
                
                record = FileRecord(
                    uuid7=uuid7_str(),
                    path=abs_path_str,
                    source=str(root_path.resolve()),
                    size=stat_result.st_size,
                    mtime=stat_result.st_mtime,
                    mode=stat_result.st_mode,
                    hash_algorithm=hash_result.algorithm,
                    blake3=hash_result.blake3_digest,
                    sha256=hash_result.sha256_digest,
                    category=classification.category,
                    mime_type=classification.mime_type,
                    shortcut_allowed=classification.shortcut_allowed,
                    source_id=descriptor.source_id,
                    source_type=descriptor.source_type,
                    source_label=descriptor.source_label,
                    source_device_uuid=descriptor.source_device_uuid,
                )
                records.append(record)
                
                if jsonl_output_path:
                    try:
                        with open(jsonl_output_path, "a", encoding="utf-8", buffering=1) as out_f:
                            out_f.write(json.dumps(record.to_dict()) + "\n")
                    except Exception as e:
                        logger.error(f"Failed to write record to JSONL: {e}")
                
                state["files_indexed"] += 1
                state["bytes_hashed"] += stat_result.st_size
                
                state["recent_files"].insert(0, abs_path_str)
                state["recent_files"] = state["recent_files"][:20]
                
            except Exception as e:
                err_str = str(e)
                logger.error(f"Error scanning {path}: {err_str}")
                
                # Check for transient browser locks and broken symlinks
                is_transient = False
                status = "error"
                is_sym = False
                try:
                    is_sym = path.is_symlink()
                except Exception:
                    pass
                    
                if isinstance(e, FileNotFoundError) or "no such file or directory" in err_str.lower():
                    if is_sym or "lock" in path.name.lower() or ".lock" in path.name.lower():
                        is_transient = True
                        status = "auto-healed"
                
                state["errors"] += 1
                state["error_log"].append({
                    "path": abs_path_str,
                    "error": err_str + " (Transient file/symlink auto-resolved)" if is_transient else err_str,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": status
                })
                state["error_log"] = state["error_log"][:100]
                
            total_indexed = state["files_indexed"]
            if total_indexed % 1000 == 0:
                elapsed = time.time() - start_time
                state["elapsed_seconds"] = round(elapsed, 2)
                fps = total_indexed / elapsed if elapsed > 0 else 0.0
                state["files_per_second"] = round(fps, 2)
                
                total_est = state["files_total_estimate"]
                if total_est > total_indexed and fps > 0:
                    state["eta_seconds"] = round((total_est - total_indexed) / fps, 2)
                else:
                    state["eta_seconds"] = 0.0
                    
                logger.info(
                    f"Indexed {total_indexed} files. "
                    f"Bytes: {state['bytes_hashed']}. "
                    f"Speed: {fps:.2f} files/sec. "
                    f"Current: {abs_path_str}"
                )
                if state_path:
                    _write_state(state_path, state)

    elapsed = time.time() - start_time
    state["elapsed_seconds"] = round(elapsed, 2)
    fps = state["files_indexed"] / elapsed if elapsed > 0 else 0.0
    state["files_per_second"] = round(fps, 2)
    state["eta_seconds"] = 0.0
    
    if current_root_idx == total_roots - 1:
        state["status"] = "completed"
        state["current_file"] = ""
        
    if state_path:
        _write_state(state_path, state)
        
    manifest = ScanManifest(
        source=str(root_path.resolve()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        records=records,
        source_id=descriptor.source_id,
        source_type=descriptor.source_type,
        source_label=descriptor.source_label,
        source_device_uuid=descriptor.source_device_uuid,
    )
    return LocalScanResult(manifest=manifest)