import asyncio

from pil.ingestion.ssot_adapter import dry_run_ingestion_cycle, ingest_manifest_async


def _sample_manifest() -> dict:
    return {
        "source": "tests",
        "generated_at": "now",
        "records": [
            {
                "uuid7": "00000000-0000-7000-8000-000000000201",
                "path": "/tmp/a.py",
                "blake3": "1" * 64,
                "category": "code",
                "mime_type": "text/x-python",
            },
            {
                "uuid7": "00000000-0000-7000-8000-000000000202",
                "path": "/tmp/b.py",
                "blake3": "2" * 64,
                "category": "code",
                "mime_type": "text/x-python",
            },
        ],
    }


def test_ingestion_to_graph_to_consolidation():
    result = asyncio.run(ingest_manifest_async(_sample_manifest()))
    assert len(result.nodes) == 2
    assert len(result.edges) == 2
    assert len(result.embeddings) == 2
    assert result.consolidation["repositories"]
    assert result.consolidation["rules"]


def test_ingestion_error_isolation():
    manifest = _sample_manifest()
    manifest["records"].append({"path": "/tmp/missing.txt"})
    result = asyncio.run(ingest_manifest_async(manifest, isolate_errors=True))
    assert len(result.nodes) == 2
    assert len(result.errors) == 1


def test_ingestion_idempotency():
    manifest = _sample_manifest()
    first = asyncio.run(dry_run_ingestion_cycle(manifest))
    second = asyncio.run(dry_run_ingestion_cycle(manifest))
    assert first["processed_records"] == second["processed_records"]
    assert first["graph_integration"] == second["graph_integration"]
    assert first["consolidation_integration"] == second["consolidation_integration"]
    assert first["errors"] == second["errors"]