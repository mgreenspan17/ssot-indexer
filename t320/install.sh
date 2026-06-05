#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"
TARGET_USER="${TARGET_USER:-ssot}"

install -d -m 0755 "$SYSTEMD_DIR"
install -d -m 0755 /var/log/ssot-indexer || true
install -d -m 0755 /ssot || true

install -m 0644 "$REPO_ROOT/t320/systemd/ssot-indexer.service" "$SYSTEMD_DIR/ssot-indexer.service"
install -m 0644 "$REPO_ROOT/t320/systemd/ssot-api.service" "$SYSTEMD_DIR/ssot-api.service"

if id "$TARGET_USER" >/dev/null 2>&1; then
  chown -R "$TARGET_USER:$TARGET_USER" /var/log/ssot-indexer /ssot || true
fi

systemctl daemon-reload
echo "installed systemd units"
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/ssot-indexer}"
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"

install -d "$DEPLOY_ROOT"
rsync -a --delete --exclude .git --exclude venv --exclude .pytest_cache "$REPO_ROOT/" "$DEPLOY_ROOT/"

python -m venv "$DEPLOY_ROOT/venv"
"$DEPLOY_ROOT/venv/Scripts/pip.exe" install -r "$DEPLOY_ROOT/requirements.txt" 2>/dev/null || true
"$DEPLOY_ROOT/venv/bin/pip" install -r "$DEPLOY_ROOT/requirements.txt" 2>/dev/null || true

install -d "$SYSTEMD_DIR"
install -m 0644 "$REPO_ROOT/t320/systemd/ssot-indexer.service" "$SYSTEMD_DIR/ssot-indexer.service"
install -m 0644 "$REPO_ROOT/t320/systemd/ssot-api.service" "$SYSTEMD_DIR/ssot-api.service"

systemctl daemon-reload
systemctl enable ssot-indexer.service ssot-api.service
