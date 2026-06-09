from indexer.models import IngestionBatch, IngestionResult

try:
	from indexer.ingest import ManifestIngestor
except Exception:  # pragma: no cover - optional when DB dependencies are unavailable
	ManifestIngestor = None  # type: ignore[assignment]

try:
	from indexer.postgres import PostgresConfig, PostgresRepository
except Exception:  # pragma: no cover - optional when psycopg2 is unavailable
	PostgresConfig = None  # type: ignore[assignment]
	PostgresRepository = None  # type: ignore[assignment]

