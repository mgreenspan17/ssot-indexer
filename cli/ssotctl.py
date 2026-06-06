from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from pil.ingestion.ssot_adapter import dry_run_ingestion_cycle
from scanner.autoscan import AutoScanManager
from scanner.factory import scan_any_target, scan_provider
from scanner.providers.registry import get_provider_metadata, list_provider_names
from scanner.service import manifest_to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ssotctl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ingestion_parser = subcommands.add_parser("ingestion", help="ingestion diagnostics")
    ingestion_commands = ingestion_parser.add_subparsers(dest="ingestion_command", required=True)
    ingestion_commands.add_parser("verify", help="verify ingestion module wiring")

    scan_parser = subcommands.add_parser("scan", help="cross-platform scanning")
    scan_commands = scan_parser.add_subparsers(dest="scan_command", required=True)

    auto_parser = scan_commands.add_parser("auto", help="auto-detect a scanner from environment or target")
    auto_parser.add_argument("target", nargs="?")
    auto_parser.add_argument("--json", dest="json_path")

    for provider_name in ("windows", "wsl", "gdrive", "onedrive", "dropbox"):
        provider_parser = scan_commands.add_parser(provider_name, help=f"scan using the {provider_name} provider")
        provider_parser.add_argument("target", nargs="?")
        provider_parser.add_argument("--json", dest="json_path")

    provider_parser = scan_commands.add_parser("provider", help="scan with an explicit provider name")
    provider_parser.add_argument("name", choices=list_provider_names())
    provider_parser.add_argument("target", nargs="?")
    provider_parser.add_argument("--json", dest="json_path")

    providers_parser = subcommands.add_parser("providers", help="provider registry information")
    providers_commands = providers_parser.add_subparsers(dest="providers_command", required=True)
    providers_commands.add_parser("list", help="list available provider scanners")
    provider_info = providers_commands.add_parser("info", help="show provider metadata")
    provider_info.add_argument("name", choices=list_provider_names())

    autoscan_parser = subcommands.add_parser("autoscan", help="autoscan controller")
    autoscan_commands = autoscan_parser.add_subparsers(dest="autoscan_command", required=True)
    autoscan_commands.add_parser("enable", help="enable autoscan")
    autoscan_commands.add_parser("disable", help="disable autoscan")
    autoscan_commands.add_parser("status", help="show autoscan status")
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
        if args.scan_command == "auto":
            manifest = scan_any_target(args.target or "auto")
        else:
            provider_name = args.scan_command if args.scan_command != "provider" else args.name
            target = getattr(args, "target", None)
            manifest = scan_provider(provider_name, target)
        _emit_manifest(manifest_to_json(manifest), getattr(args, "json_path", None))
        return 0

    if args.command == "providers":
        if args.providers_command == "list":
            print(json.dumps({"providers": list_provider_names()}, indent=2))
            return 0
        if args.providers_command == "info":
            metadata = get_provider_metadata(args.name)
            print(json.dumps(metadata.__dict__, indent=2, sort_keys=True))
            return 0

    if args.command == "autoscan":
        manager = AutoScanManager()
        if args.autoscan_command == "enable":
            print(json.dumps(manager.enable(), indent=2, sort_keys=True))
            return 0
        if args.autoscan_command == "disable":
            print(json.dumps(manager.disable(), indent=2, sort_keys=True))
            return 0
        if args.autoscan_command == "status":
            print(json.dumps(manager.status(), indent=2, sort_keys=True))
            return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
