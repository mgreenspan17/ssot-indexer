from __future__ import annotations

import argparse
import json
from pathlib import Path

from canonical.store import CanonicalStoreManager
from indexer.ingest import ManifestIngestor
from indexer.postgres import PostgresConfig, PostgresRepository
from observability.logging import configure_logging
from orchestrator.api import create_app
from orchestrator.service import SSOTOrchestrator
from resolver.zpath import resolve_z_path
from scanner.service import manifest_to_json, scan_target
import uvicorn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ssot-indexer")
    subcommands = parser.add_subparsers(dest="command", required=True)

    scan_parser = subcommands.add_parser("scan", help="scan a local, ssh, or rclone target")
    scan_parser.add_argument("target")
    scan_parser.add_argument("--json", dest="json_path")

    ingest_parser = subcommands.add_parser("ingest", help="ingest a manifest into Postgres")
    ingest_parser.add_argument("manifest")
    ingest_parser.add_argument("--dsn", required=True)

    canonical_parser = subcommands.add_parser("canonicalize", help="canonicalize files from a manifest")
    canonical_parser.add_argument("manifest")
    canonical_parser.add_argument("--dsn", required=True)
    canonical_parser.add_argument("--storage-root", default="/ssot")
    canonical_parser.add_argument("--shortcut-root", default="/ssot/shortcuts")

    resolve_parser = subcommands.add_parser("resolve", help="resolve a z path")
    resolve_parser.add_argument("z_path")
    resolve_parser.add_argument("--lookup-json", required=True)

    serve_parser = subcommands.add_parser("serve", help="run the FastAPI app")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        result = scan_target(args.target)
        payload = manifest_to_json(result.manifest)
        if args.json_path:
            Path(args.json_path).write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.command == "ingest":
        manifest_data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        from scanner.models import FileRecord, ScanManifest

        manifest = ScanManifest(
            source=manifest_data["source"],
            generated_at=manifest_data["generated_at"],
            records=[FileRecord(**item) for item in manifest_data["records"]],
        )
        repository = PostgresRepository(PostgresConfig(args.dsn))
        results = ManifestIngestor(repository).ingest(manifest)
        print(json.dumps([result.__dict__ for result in results], indent=2))
        return 0

    if args.command == "canonicalize":
        manifest_data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        from scanner.models import FileRecord, ScanManifest

        manifest = ScanManifest(
            source=manifest_data["source"],
            generated_at=manifest_data["generated_at"],
            records=[FileRecord(**item) for item in manifest_data["records"]],
        )
        repository = PostgresRepository(PostgresConfig(args.dsn))
        ingestor = ManifestIngestor(repository)
        ingestion_results = ingestor.ingest(manifest)
        manager = CanonicalStoreManager(Path(args.storage_root), Path(args.shortcut_root), repository)
        output = [manager.materialize(record, ingestion) for record, ingestion in zip(manifest.records, ingestion_results, strict=True)]
        print(json.dumps([item.__dict__ for item in output], indent=2))
        return 0

    if args.command == "resolve":
        lookup = json.loads(Path(args.lookup_json).read_text(encoding="utf-8"))
        result = resolve_z_path(args.z_path, lookup)
        print(json.dumps(result.__dict__, indent=2))
        return 0

    if args.command == "serve":
        app = create_app(SSOTOrchestrator())
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
