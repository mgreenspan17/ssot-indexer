from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from pil.ingestion.ssot_adapter import dry_run_ingestion_cycle
from scanner.factory import scan_provider
from scanner.providers.registry import list_provider_names
from scanner.service import manifest_to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ssotctl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ingestion_parser = subcommands.add_parser("ingestion", help="ingestion diagnostics")
    ingestion_commands = ingestion_parser.add_subparsers(dest="ingestion_command", required=True)
    ingestion_commands.add_parser("verify", help="verify ingestion module wiring")

    scan_parser = subcommands.add_parser("scan", help="cross-platform scanning")
    scan_commands = scan_parser.add_subparsers(dest="scan_command", required=True)

    for provider_name in ("windows", "wsl", "gdrive", "onedrive", "dropbox"):
        provider_parser = scan_commands.add_parser(provider_name, help=f"scan using the {provider_name} provider")
        provider_parser.add_argument("target", nargs="?")
        provider_parser.add_argument("--json", dest="json_path")

    provider_parser = scan_commands.add_parser("provider", help="scan with an explicit provider name")
    provider_parser.add_argument("name", choices=list_provider_names())
    provider_parser.add_argument("target", nargs="?")
    provider_parser.add_argument("--json", dest="json_path")
    return parser


def _emit_manifest(payload: str, json_path: str | None) -> None:
    if json_path:
        Path(json_path).write_text(payload, encoding="utf-8")
    else:
        print(payload)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingestion" and args.ingestion_command == "verify":
        sample_manifest = {
            "source": "ssotctl",
            "generated_at": "dry-run",
            "records": [
                {
                    "uuid7": "00000000-0000-7000-8000-000000000100",
                    "path": "/tmp/ssotctl.txt",
                    "blake3": "a" * 64,
                    "category": "code",
                    "mime_type": "text/plain",
                }
            ],
        }
        report = asyncio.run(dry_run_ingestion_cycle(sample_manifest))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.command == "scan":
        provider_name = args.scan_command if args.scan_command != "provider" else args.name
        target = getattr(args, "target", None)
        manifest = scan_provider(provider_name, target)
        _emit_manifest(manifest_to_json(manifest), getattr(args, "json_path", None))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
