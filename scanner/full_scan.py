#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sys

# Add project root to sys.path so we can import our modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scanner.local import scan_local_directory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("full_scan")


def count_files_in_roots(roots: list[str]) -> int:
    total_files = 0
    logger.info("Starting quick file count across all roots...")
    exclusions = {"containerd", "docker", "lost+found", "cache", "caches", "temp", "tmp", "android"}
    if os.name == "nt":
        from scanner.base import WINDOWS_EXCLUDED_DIRS
        exclusions.update(d.lower() for d in WINDOWS_EXCLUDED_DIRS)
        exclusions.update({"appdata", "node_modules", ".git", "venv", ".venv", "$winreagent"})
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            logger.warning(f"Root path does not exist: {root}")
            continue
        logger.info(f"Counting files in {root}...")
        for _, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d.lower() not in exclusions]
            total_files += len(files)
    logger.info(f"Total estimated files to index: {total_files}")
    return total_files


def load_completed_files(jsonl_path: Path) -> dict[str, float]:
    completed: dict[str, float] = {}
    if jsonl_path.exists():
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        if "path" in record and "mtime" in record:
                            completed[record["path"]] = float(record["mtime"])
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to read completed files from {jsonl_path}: {e}")
    return completed


def main() -> None:
    parser = argparse.ArgumentParser(description="Full SSOT System File Indexer")
    parser.add_argument(
        "roots",
        nargs="*",
        default=["/srv/data", "/DATA", "/home"],
        help="Root directories to scan (default: /srv/data /DATA /home)"
    )
    parser.add_argument(
        "--state-path",
        default="/tmp/ssot_scan_state.json",
        help="Path to write live progress JSON state file (default: /tmp/ssot_scan_state.json)"
    )
    parser.add_argument(
        "--output-dir",
        default="/srv/data/ssot/scan_results/",
        help="Directory to save the final JSONL scan results (default: /srv/data/ssot/scan_results/)"
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Path to an existing JSONL manifest to resume from"
    )
    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create output directory {args.output_dir}: {e}")
        sys.exit(1)

    # Determine output file path and load completed files (auto-resume by default if interrupted)
    completed_files = {}
    is_resuming = False
    
    if args.resume:
        output_file_path = Path(args.resume)
        completed_files = load_completed_files(output_file_path)
        is_resuming = len(completed_files) > 0
        logger.info(f"Manual resume requested. Output will be appended to {output_file_path}")
    else:
        # Check if the latest scan manifest can be auto-resumed
        jsonl_files = sorted(
            output_dir.glob("scan_manifest_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        was_completed = False
        state_file = Path(args.state_path)
        if state_file.exists():
            try:
                with open(state_file, "r") as sf:
                    state_data = json.load(sf)
                    if state_data.get("status") == "completed":
                        was_completed = True
            except Exception:
                pass
                
        if jsonl_files and not was_completed:
            output_file_path = jsonl_files[0]
            completed_files = load_completed_files(output_file_path)
            is_resuming = len(completed_files) > 0
            logger.info(f"Auto-resuming interrupted scan: {output_file_path}")
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file_path = output_dir / f"scan_manifest_{timestamp}.jsonl"
            logger.info(f"Starting fresh scan: {output_file_path}")

    if is_resuming:
        logger.info(f"Loaded {len(completed_files)} already-hashed files. Skipping them during scan.")

    # First count files to get estimate
    total_estimate = count_files_in_roots(args.roots)

    logger.info(f"Scan results will be written to {output_file_path}")

    # Run the scan across all roots
    existing_state = None
    all_records_count = len(completed_files)

    # Filter out non-existent roots to avoid scanning failures
    valid_roots = []
    for r in args.roots:
        if Path(r).exists():
            valid_roots.append(r)
        else:
            logger.warning(f"Skipping non-existent root: {r}")

    if not valid_roots:
        logger.error("No valid roots to scan.")
        sys.exit(1)

    total_roots = len(valid_roots)

    # Populate initial state if resuming
    if is_resuming and Path(args.state_path).exists():
        try:
            with open(args.state_path, "r") as state_file:
                existing_state = json.load(state_file)
                # Ensure status is reset to scanning
                existing_state["status"] = "scanning"
                existing_state["files_indexed"] = len(completed_files)
        except Exception:
            pass

    for idx, root in enumerate(valid_roots):
        logger.info(f"Scanning root {idx + 1}/{total_roots}: {root}")
        try:
            scan_result = scan_local_directory(
                root=root,
                state_path=args.state_path,
                total_estimate=total_estimate,
                roots_list=valid_roots,
                current_root_idx=idx,
                total_roots=total_roots,
                existing_state=existing_state,
                jsonl_output_path=output_file_path,
                completed_files=completed_files
            )
            
            all_records_count += len(scan_result.manifest.records)
            
            # Retrieve updated state to pass to the next root scan
            if Path(args.state_path).exists():
                with open(args.state_path, "r") as state_file:
                    existing_state = json.load(state_file)
            
        except Exception as e:
            logger.error(f"Error during scan of root {root}: {e}")

    logger.info("Scan completed successfully!")
    logger.info(f"Total indexed files written: {all_records_count}")


if __name__ == "__main__":
    main()
