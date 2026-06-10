#!/usr/bin/env python3
# ingest_notion_w9_artifacts.py
# Use case: dry-run planning for W9 Notion JSON/JSONL artifacts without touching production systems.

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indexer.notion_ingest import (
    NotionPlanPostgresWriter,
    build_ingest_plan,
    format_dry_run_summary,
    resolve_database_write_request,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run Notion W9 artifact ingest planner")
    parser.add_argument("artifact_paths", nargs="+", help="Paths to JSON or JSONL artifacts")
    parser.add_argument("--tenant-id", default="default-tenant")
    parser.add_argument("--workspace-id", default="default-workspace")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--emit-json", action="store_true", help="Emit a JSON summary instead of text")
    parser.add_argument("--write", action="store_true", help="Enable DB-write mode (disabled by default)")
    parser.add_argument("--confirm-db-write", action="store_true", help="Required confirmation flag when --write is used")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dsn = resolve_database_write_request(
        write_enabled=args.write,
        confirm_db_write=args.confirm_db_write,
        environ=os.environ,
    )

    plan = build_ingest_plan(
        args.artifact_paths,
        tenant_id=args.tenant_id,
        workspace_id=args.workspace_id,
        run_id=args.run_id,
    )

    if dsn is not None:
        writer = NotionPlanPostgresWriter(dsn)
        report = writer.write_plan(plan)
        print(f"run_id: {report.run_id}")
        print(f"tenant_id: {report.tenant_id}")
        print(f"workspace_id: {report.workspace_id}")
        print(f"artifact_count: {report.artifact_count}")
        print(f"transaction_committed: {report.transaction_committed}")
        print("table_counts:")
        for table_name in NotionPlanPostgresWriter.WRITE_ORDER:
            counts = report.table_counts.get(table_name)
            if counts is None:
                continue
            print(
                "  "
                f"{table_name}: attempted={counts.attempted} inserted={counts.inserted} "
                f"updated={counts.updated} skipped={counts.skipped}"
            )
        return 0

    if args.emit_json:
        payload = {
            "tenant_id": plan.tenant_id,
            "workspace_id": plan.workspace_id,
            "run_id": plan.run_id,
            "crawl_run_merkle_root": plan.crawl_run_merkle_root,
            "artifacts": [
                {
                    "artifact_path": artifact.artifact_path,
                    "artifact_type": artifact.artifact_type,
                    "artifact_file_blake3": artifact.artifact_file_blake3,
                    "record_count": artifact.record_count,
                    "batch_merkle_root": artifact.batch_merkle_root,
                }
                for artifact in plan.artifacts
            ],
            "counts": {
                "raw_artifacts": len(plan.raw_artifacts),
                "ingest_batches": len(plan.ingest_batches),
                "object_snapshots": len(plan.object_snapshots),
                "object_current_rows": len(plan.object_current_rows),
                "parent_edges": len(plan.parent_edges),
                "block_snapshots": len(plan.block_snapshots),
                "status_events": len(plan.status_events),
                "merkle_nodes": len(plan.merkle_nodes),
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(format_dry_run_summary(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
