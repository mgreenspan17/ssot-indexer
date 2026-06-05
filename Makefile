PYTHON ?= python

.PHONY: test build run scan ingest canonicalize api lint typecheck sql-validate

test:
	$(PYTHON) -m pytest -q

build:
	$(PYTHON) -m build

run:
	$(PYTHON) -m cli --help

scan:
	$(PYTHON) -m cli scan .

ingest:
	$(PYTHON) -m cli ingest manifest.json --dsn "$${DATABASE_URL:?DATABASE_URL required}"

canonicalize:
	$(PYTHON) -m cli canonicalize manifest.json --dsn "$${DATABASE_URL:?DATABASE_URL required}"

api:
	$(PYTHON) -m cli serve --host 127.0.0.1 --port 8000

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy .

sql-validate:
	$(PYTHON) -c "from pathlib import Path; files=sorted(Path('sql').glob('*.sql')); assert [p.name for p in files]==['001_init.sql','002_indexes.sql']; print('sql ok')"
