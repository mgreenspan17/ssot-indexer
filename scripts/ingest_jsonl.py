#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indexer.postgres import PostgresConfig, PostgresRepository
from indexer.ingest import ManifestIngestor
from scanner.models import FileRecord, ScanManifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest JSONL scan results into Postgres")
    parser.add_argument("jsonl_path", help="Path to the scan_manifest_*.jsonl file")
    parser.add_argument("--dsn", required=True, help="Postgres connection DSN")
    args = parser.parse_args()

    jsonl_path = Path(args.jsonl_path)
    if not jsonl_path.exists():
        print(f"Error: File not found: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting ingestion of {jsonl_path}...")
    
    repository = PostgresRepository(PostgresConfig(args.dsn))
    
    manifest = ScanManifest(
        source="full_scan",
        generated_at=datetime.now(timezone.utc).isoformat(),
        records=[]
    )
    batch = repository.create_batch(manifest)
    print(f"Created ingestion batch: {batch.id}")

    count = 0
    batch_size = 1000
    records_buffer = []
    
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record_data = json.loads(line)
                record = FileRecord(**record_data)
                records_buffer.append(record)
                
                if len(records_buffer) >= batch_size:
                    repository.ingest_records_batch(batch, records_buffer)
                    count += len(records_buffer)
                    print(f"Ingested {count} records...")
                    records_buffer.clear()
            except Exception as e:
                print(f"Error buffering/ingesting line: {e}", file=sys.stderr)
                
        # Ingest any remaining records
        if records_buffer:
            try:
                repository.ingest_records_batch(batch, records_buffer)
                count += len(records_buffer)
                print(f"Ingested {count} records...")
                records_buffer.clear()
            except Exception as e:
                print(f"Error ingesting final batch: {e}", file=sys.stderr)

    repository.mark_batch_complete(batch.id)
    print(f"Successfully completed ingestion of {count} records in batch {batch.id}!")


if __name__ == "__main__":
    main()
