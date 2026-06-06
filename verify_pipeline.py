#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import psycopg2
import requests

# Expected runtime and data locations
EXPECTED_REPO_PATH = "/opt/ssot-indexer"
MANIFEST_PATH = Path("/srv/data/ssot/ingestion/authoritative_manifest.json")
CHECKPOINT_DIR = Path("/srv/data/ssot/pipeline/checkpoints")
PIPELINE_STATE_PATH = CHECKPOINT_DIR / "pipeline_state.json"
STAGE1_SAMPLE_PATH = CHECKPOINT_DIR / "stage1_sample.json"
STAGE2_INDEX_PATH = CHECKPOINT_DIR / "stage2_index.json"
STAGE3_RESULTS_PATH = CHECKPOINT_DIR / "stage3_results.json"
PIPELINE_LOG_PATH = Path("/tmp/pipeline.log")
PGDATA_DIRS = [
    Path("/srv/data/ssot/postgres-data/global"),
    Path("/srv/data/ssot/postgres-data/base"),
]
DB_ACTIVITY_WINDOW_SECONDS = 5
API_BASE_URL = os.environ.get("SSOT_API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DSN = "postgresql://ssot:ssot@127.0.0.1:5433/ssot"


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str
    data: dict[str, Any] | None = None


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iter_json_array(path: Path, chunk_size: int = 65536) -> Iterator[dict[str, Any]]:
    """Stream a top-level JSON array from disk without loading whole file into memory."""
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
                    raise ValueError("Manifest root must be a JSON array")
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
                except json.JSONDecodeError:
                    break

                if isinstance(value, dict):
                    yield value
                else:
                    raise ValueError("Manifest entries must be JSON objects")

                index = next_index

            if index > 0:
                buffer = buffer[index:]

            if not chunk:
                if buffer.strip():
                    raise ValueError("Unexpected trailing content in manifest")
                break


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_runtime_check() -> CheckResult:
    cwd = str(Path.cwd().resolve())
    script_dir = str(Path(__file__).resolve().parent)

    in_expected = cwd == EXPECTED_REPO_PATH and script_dir == EXPECTED_REPO_PATH
    has_repo_markers = Path(EXPECTED_REPO_PATH, "pipeline_api").exists() and Path(
        EXPECTED_REPO_PATH,
        "scripts",
    ).exists()

    if in_expected and has_repo_markers:
        return CheckResult(
            name="runtime_context",
            passed=True,
            details=f"Running in expected repo context ({EXPECTED_REPO_PATH})",
            data={"cwd": cwd, "script_dir": script_dir},
        )

    return CheckResult(
        name="runtime_context",
        passed=False,
        details=(
            f"Script must run from {EXPECTED_REPO_PATH} with script located there; "
            f"got cwd={cwd}, script_dir={script_dir}"
        ),
        data={"cwd": cwd, "script_dir": script_dir},
    )


def check_manifest() -> CheckResult:
    if not MANIFEST_PATH.exists() or not MANIFEST_PATH.is_file():
        return CheckResult(
            name="manifest",
            passed=False,
            details=f"Manifest not found: {MANIFEST_PATH}",
        )

    try:
        total = 0
        required_keys = {"path", "size", "mtime", "category", "mime_type", "shortcut_allowed"}
        first_missing: list[str] | None = None

        for record in _iter_json_array(MANIFEST_PATH):
            total += 1
            if total == 1:
                first_missing = sorted(k for k in required_keys if k not in record)

        if total == 0:
            return CheckResult(
                name="manifest",
                passed=False,
                details="Manifest is valid JSON but empty",
                data={"manifest_path": str(MANIFEST_PATH), "records": 0},
            )

        if first_missing:
            return CheckResult(
                name="manifest",
                passed=False,
                details=f"Manifest integrity failed: first record missing keys {first_missing}",
                data={"manifest_path": str(MANIFEST_PATH), "records": total},
            )

        return CheckResult(
            name="manifest",
            passed=True,
            details="Manifest exists and passed streamed integrity checks",
            data={"manifest_path": str(MANIFEST_PATH), "records": total},
        )
    except Exception as exc:
        return CheckResult(
            name="manifest",
            passed=False,
            details=f"Manifest integrity error: {exc}",
            data={"manifest_path": str(MANIFEST_PATH)},
        )


def check_stage2() -> CheckResult:
    if not PIPELINE_LOG_PATH.exists() or not PIPELINE_LOG_PATH.is_file():
        return CheckResult(
            name="stage2",
            passed=False,
            details=f"Pipeline log not found: {PIPELINE_LOG_PATH}",
        )

    try:
        text = PIPELINE_LOG_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return CheckResult(
            name="stage2",
            passed=False,
            details=f"Cannot read pipeline log: {exc}",
        )

    stage2_done = re.search(r"Stage 2 complete:\s*(\d+)\s*files indexed", text)
    if stage2_done:
        count = int(stage2_done.group(1))
        return CheckResult(
            name="stage2",
            passed=True,
            details=f"Stage 2 completion found in log ({count} files indexed)",
            data={"indexed_files": count, "log": str(PIPELINE_LOG_PATH)},
        )

    return CheckResult(
        name="stage2",
        passed=False,
        details="Stage 2 completion marker not found in /tmp/pipeline.log",
        data={"log": str(PIPELINE_LOG_PATH)},
    )


def check_stage3() -> CheckResult:
    if not PIPELINE_STATE_PATH.exists() or not PIPELINE_STATE_PATH.is_file():
        return CheckResult(
            name="stage3",
            passed=False,
            details=f"Missing pipeline state file: {PIPELINE_STATE_PATH}",
        )

    try:
        state = _load_json_file(PIPELINE_STATE_PATH)
    except Exception as exc:
        return CheckResult(
            name="stage3",
            passed=False,
            details=f"Invalid pipeline state JSON: {exc}",
        )

    stage2_complete = bool(state.get("stage2_complete"))
    if not stage2_complete:
        return CheckResult(
            name="stage3",
            passed=False,
            details="Stage 2 is not complete in pipeline_state.json; Stage 3 not ready",
            data={"stage2_complete": stage2_complete},
        )

    stage2_index_exists = STAGE2_INDEX_PATH.exists() and STAGE2_INDEX_PATH.is_file()
    if not stage2_index_exists:
        return CheckResult(
            name="stage3",
            passed=False,
            details=f"Stage 2 index missing; Stage 3 cannot run: {STAGE2_INDEX_PATH}",
            data={"stage2_complete": stage2_complete},
        )

    stage3_started = bool(state.get("stage3_started_at")) or int(state.get("stage3_files_processed") or 0) > 0
    stage3_complete = bool(state.get("stage3_complete"))

    return CheckResult(
        name="stage3",
        passed=True,
        details=(
            "Stage 3 readiness verified"
            if not stage3_started and not stage3_complete
            else "Stage 3 has started or completed"
        ),
        data={
            "stage3_started": stage3_started,
            "stage3_complete": stage3_complete,
            "stage3_results_exists": STAGE3_RESULTS_PATH.exists(),
        },
    )


def check_ingestion_worker() -> CheckResult:
    # Read-only process inspection for ingestion worker activity.
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid=,comm=,args="],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        return CheckResult(
            name="ingestion_worker",
            passed=False,
            details=f"Unable to inspect process table: {exc}",
        )

    if proc.returncode != 0:
        return CheckResult(
            name="ingestion_worker",
            passed=False,
            details=f"ps command failed: {proc.stderr.strip()}",
        )

    worker_lines: list[str] = []
    patterns = [
        "ingestion_worker",
        "worker_ingestion",
        "ingest_worker",
        "ingestion worker",
        "ingest-and-canonicalize",
    ]

    for line in proc.stdout.splitlines():
        lower = line.lower()
        if "verify_pipeline.py" in lower:
            continue
        if any(p in lower for p in patterns):
            worker_lines.append(line.strip())

    if worker_lines:
        return CheckResult(
            name="ingestion_worker",
            passed=True,
            details=f"Detected {len(worker_lines)} ingestion worker process(es)",
            data={"processes": worker_lines[:5]},
        )

    return CheckResult(
        name="ingestion_worker",
        passed=False,
        details="No ingestion worker process detected",
    )


def check_api() -> CheckResult:
    endpoints = [
        ("live_status", f"{API_BASE_URL}/pipeline/live_status"),
        ("status", f"{API_BASE_URL}/pipeline/status"),
    ]
    timeout = float(os.environ.get("SSOT_VERIFY_HTTP_TIMEOUT", "5"))

    endpoint_results: dict[str, Any] = {}
    failures: list[str] = []

    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=timeout)
            endpoint_results[name] = {"status_code": response.status_code}
            if response.status_code != 200:
                failures.append(f"{name} returned HTTP {response.status_code}")
                continue

            payload = response.json()
            if not isinstance(payload, dict):
                failures.append(f"{name} response is not a JSON object")
                continue

            if name == "live_status":
                required = {
                    "current_stage",
                    "stage_description",
                    "stage_elapsed_seconds",
                    "pipeline_active",
                    "db_active",
                }
            else:
                required = {
                    "filesystem_count",
                    "stage1_count",
                    "stage2_count",
                    "stage3_count",
                    "db_indexed_count",
                }
            missing = sorted(k for k in required if k not in payload)
            if missing:
                failures.append(f"{name} missing fields: {missing}")
            else:
                endpoint_results[name]["fields_ok"] = True
        except Exception as exc:
            failures.append(f"{name} error: {exc}")

    if failures:
        return CheckResult(
            name="api",
            passed=False,
            details="; ".join(failures),
            data={"base_url": API_BASE_URL, "results": endpoint_results},
        )

    return CheckResult(
        name="api",
        passed=True,
        details="API endpoints /pipeline/live_status and /pipeline/status are healthy",
        data={"base_url": API_BASE_URL, "results": endpoint_results},
    )


def _pid_cmdline(pid: int) -> str:
    path = Path(f"/proc/{pid}/cmdline")
    try:
        raw = path.read_bytes()
        if not raw:
            return ""
        return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()
    except OSError:
        return ""


def check_port_8000() -> CheckResult:
    # Ensure exactly the expected API service is bound on 8000.
    try:
        proc = subprocess.run(
            ["ss", "-ltnp", "sport", "=", ":8000"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        return CheckResult(
            name="port_8000",
            passed=False,
            details=f"Unable to run ss for port check: {exc}",
        )

    if proc.returncode != 0:
        return CheckResult(
            name="port_8000",
            passed=False,
            details=f"ss command failed: {proc.stderr.strip()}",
        )

    text = proc.stdout
    pids = {int(x) for x in re.findall(r"pid=(\d+)", text)}

    if not pids:
        return CheckResult(
            name="port_8000",
            passed=False,
            details="No process is listening on TCP port 8000",
        )

    cmdlines = {pid: _pid_cmdline(pid) for pid in pids}
    offenders = []
    for pid, cmd in cmdlines.items():
        lower = cmd.lower()
        if not (
            "pipeline_api" in lower
            or "examples.pipeline_api_main:app" in lower
            or "pipeline_api.main:app" in lower
        ):
            offenders.append({"pid": pid, "cmd": cmd})

    if offenders:
        return CheckResult(
            name="port_8000",
            passed=False,
            details="Port 8000 has non-pipeline_api listener(s)",
            data={"listeners": cmdlines, "offenders": offenders},
        )

    return CheckResult(
        name="port_8000",
        passed=True,
        details="Port 8000 listener ownership verified (pipeline_api only)",
        data={"listeners": cmdlines},
    )


def check_db() -> CheckResult:
    dsn = os.environ.get("SSOT_DATABASE_DSN", DEFAULT_DSN)

    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
    except Exception as exc:
        return CheckResult(
            name="database",
            passed=False,
            details=f"Database connection failed: {exc}",
            data={"dsn": dsn},
        )

    counts: dict[str, int] = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM files")
            counts["files"] = int(cur.fetchone()[0])

            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cur.fetchall()]

            for table in ("canonical", "shortcuts"):
                if table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = int(cur.fetchone()[0])
    except Exception as exc:
        conn.close()
        return CheckResult(
            name="database",
            passed=False,
            details=f"Database query failed: {exc}",
            data={"dsn": dsn},
        )

    conn.close()
    return CheckResult(
        name="database",
        passed=True,
        details="Database connectivity and core table counts verified",
        data={"dsn": dsn, "counts": counts},
    )


def generate_report(results: list[CheckResult]) -> str:
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("SSOT PIPELINE VERIFICATION REPORT")
    lines.append("=" * 78)
    lines.append(f"Timestamp (UTC): {_now_utc_iso()}")
    lines.append("")

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"[{status}] {result.name}: {result.details}")
        if result.data:
            lines.append(f"       data={json.dumps(result.data, ensure_ascii=True, default=str)}")

    overall_pass = all(r.passed for r in results)
    lines.append("")
    lines.append("-" * 78)
    lines.append(f"OVERALL: {'PASS' if overall_pass else 'FAIL'}")
    lines.append("=" * 78)
    return "\n".join(lines)


def main() -> int:
    checks: list[CheckResult] = [
        _repo_runtime_check(),
        check_manifest(),
        check_stage2(),
        check_stage3(),
        check_ingestion_worker(),
        check_api(),
        check_port_8000(),
        check_db(),
    ]

    report = generate_report(checks)
    print(report)

    return 0 if all(c.passed for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
