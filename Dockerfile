FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml setup.cfg README.md VERSION requirements.txt ./
COPY canonical ./canonical
COPY classify ./classify
COPY cli ./cli
COPY hashing ./hashing
COPY health ./health
COPY indexer ./indexer
COPY observability ./observability
COPY orchestrator ./orchestrator
COPY resolver ./resolver
COPY rules ./rules
COPY scanner ./scanner
COPY scripts ./scripts
COPY shortcuts ./shortcuts
COPY sql ./sql
COPY t320 ./t320
COPY tests ./tests
COPY uuid ./uuid

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml setup.cfg VERSION README.md /app/
COPY canonical /app/canonical
COPY classify /app/classify
COPY cli /app/cli
COPY hashing /app/hashing
COPY health /app/health
COPY indexer /app/indexer
COPY observability /app/observability
COPY orchestrator /app/orchestrator
COPY resolver /app/resolver
COPY rules /app/rules
COPY scanner /app/scanner
COPY shortcuts /app/shortcuts
COPY sql /app/sql
COPY t320 /app/t320
COPY uuid /app/uuid

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "-m", "cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
