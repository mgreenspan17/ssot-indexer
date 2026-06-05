from __future__ import annotations

import argparse
import asyncio
import json

from pil.ingestion.ssot_adapter import dry_run_ingestion_cycle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ssotctl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ingestion_parser = subcommands.add_parser("ingestion", help="ingestion diagnostics")
    ingestion_commands = ingestion_parser.add_subparsers(dest="ingestion_command", required=True)
    ingestion_commands.add_parser("verify", help="verify ingestion module wiring")
    return parser


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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
