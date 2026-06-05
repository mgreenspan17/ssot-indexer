#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

cd "$REPO_ROOT"

python - <<'PY'
import os
from pathlib import Path
from indexer.postgres import PostgresConfig, PostgresRepository

repo = PostgresRepository(PostgresConfig(os.environ["DATABASE_URL"]))
for sql_file in sorted(Path("sql").glob("*.sql")):
    repo.apply_sql(sql_file)
    print(f"applied {sql_file}")
PY
