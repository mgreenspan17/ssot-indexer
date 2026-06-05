#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SYSTEMD_SCOPE="${SYSTEMD_SCOPE:-system}"

systemctl ${SYSTEMD_SCOPE:+--${SYSTEMD_SCOPE}} is-active ssot-indexer.service
systemctl ${SYSTEMD_SCOPE:+--${SYSTEMD_SCOPE}} is-active ssot-api.service
echo "healthy"
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

python - <<'PY'
from health.api_health import check as api_check
from health.orchestrator_health import check as orchestrator_check
from health.scanner_health import check as scanner_check
from health.canonical_store_health import check as canonical_check
from health.shortcut_health import check as shortcut_check

for check in (api_check, orchestrator_check, scanner_check, canonical_check, shortcut_check):
    print(check())
PY
