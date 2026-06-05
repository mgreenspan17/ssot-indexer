#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/ssot-indexer}"

if [[ ! -d "$DEPLOY_ROOT" ]]; then
  echo "deployment root not found: $DEPLOY_ROOT" >&2
  exit 1
fi

rsync -a --delete --exclude .git --exclude venv --exclude .pytest_cache "$REPO_ROOT/" "$DEPLOY_ROOT/"

# Restart only the API service. Restarting ssot-indexer from within
# itself would create a systemd job loop (oneshot restarts oneshot).
# The orchestrator runs once per update; the API runs continuously.
systemctl restart ssot-api.service 2>/dev/null || true
