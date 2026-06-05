#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

if git rev-parse HEAD^ >/dev/null 2>&1; then
  git checkout HEAD^ -- VERSION pyproject.toml setup.cfg || true
  echo "rollback completed"
else
  echo "no previous commit available" >&2
  exit 1
fi
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/ssot-indexer}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/ssot-indexer-backup}"

if [[ ! -d "$BACKUP_ROOT" ]]; then
  echo "backup root not found: $BACKUP_ROOT" >&2
  exit 1
fi

rsync -a --delete "$BACKUP_ROOT/" "$DEPLOY_ROOT/"
systemctl restart ssot-indexer.service ssot-api.service
