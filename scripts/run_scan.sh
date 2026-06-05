#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ROOT_DIR="${1:-${ROOT_DIR:-$REPO_ROOT}}"
OUTPUT_FILE="${2:-${OUTPUT_FILE:-$REPO_ROOT/manifest.json}}"

cd "$REPO_ROOT"

python -m cli scan "$ROOT_DIR" --json "$OUTPUT_FILE"
