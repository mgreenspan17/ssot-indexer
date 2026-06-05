#!/usr/bin/env bash
set -euo pipefail

sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses = 'localhost';"
sudo systemctl reload postgresql
echo "PostgreSQL configured for localhost connections"
