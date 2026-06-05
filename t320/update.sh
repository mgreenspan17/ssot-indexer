#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

if [[ -d .git ]]; then
  git fetch --all --tags --prune || true
fi

"$REPO_ROOT/venv/Scripts/python.exe" scripts/bump_version.py --part patch || true
"$REPO_ROOT/venv/Scripts/python.exe" scripts/validate_sql.py
echo "update complete"
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
systemctl restart ssot-indexer.service ssot-api.service
