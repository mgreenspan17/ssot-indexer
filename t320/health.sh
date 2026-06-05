#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SYSTEMD_SCOPE="${SYSTEMD_SCOPE:-system}"

systemctl ${SYSTEMD_SCOPE:+--${SYSTEMD_SCOPE}} is-active ssot-indexer.service
systemctl ${SYSTEMD_SCOPE:+--${SYSTEMD_SCOPE}} is-active ssot-api.service
echo "healthy"
