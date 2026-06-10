from __future__ import annotations

from pathlib import Path

from hashing.provenance import build_merkle_tree, canonical_json_dumps, blake3_hex_json
from indexer.notion_ingest import build_ingest_plan, format_dry_run_summary


def test_canonical_json_is_stable():
    first = canonical_json_dumps({"b": 2, "a": 1})
    second = canonical_json_dumps({"a": 1, "b": 2})
    assert first == second


def test_merkle_root_is_deterministic():
    left = build_merkle_tree(["a" * 64, "b" * 64, "c" * 64])
    right = build_merkle_tree(["a" * 64, "b" * 64, "c" * 64])
    assert left.root_hash == right.root_hash
    assert len(left.nodes) == len(right.nodes)


def test_w9_artifact_dry_run_plan(tmp_path: Path):
    discovered = tmp_path / "discovered_pages.jsonl"
    discovered.write_text(
        "\n".join(
            [
                '{"run_id":"run-b9580189","page_id":"page-1","page_title":"Alpha","url":"https://example.test/a","object":"page"}',
                '{"run_id":"run-b9580189","page_id":"page-2","page_title":"Beta","url":"https://example.test/b","object":"page","parent_id":"page-1"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    block_children = tmp_path / "block_children_snapshots.jsonl"
    block_children.write_text(
        '{"run_id":"run-b9580189","page_id":"page-1","page_title":"Alpha","blocks":[{"id":"block-1","type":"paragraph","has_children":false,"depth":0,"position":0},{"id":"block-2","type":"to_do","has_children":false,"depth":0,"position":1}]}\n',
        encoding="utf-8",
    )

    status = tmp_path / "notion_index_run_status.json"
    status.write_text(
        '{"run_id":"run-b9580189","status":"complete","stage":"complete","stage_detail":"done","pages_discovered":2}',
        encoding="utf-8",
    )

    plan = build_ingest_plan(
        [str(discovered), str(block_children), str(status)],
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )

    assert plan.run_id == "run-b9580189"
    assert len(plan.raw_artifacts) == 3
    assert len(plan.ingest_batches) == 3
    assert len(plan.object_snapshots) >= 2
    assert len(plan.block_snapshots) == 2
    assert len(plan.parent_edges) >= 3
    assert plan.crawl_run_merkle_root

    summary = format_dry_run_summary(plan)
    assert "Notion ingest dry-run summary" in summary
    assert "run-b9580189" in summary
    assert "object_current_rows" in summary


def test_artifact_and_batch_ids_are_consistent_across_rows(tmp_path: Path):
    discovered = tmp_path / "discovered_pages.jsonl"
    discovered.write_text(
        '{"run_id":"run-b9580189","page_id":"page-1","page_title":"Alpha","object":"page"}\n',
        encoding="utf-8",
    )

    block_children = tmp_path / "block_children_snapshots.jsonl"
    block_children.write_text(
        '{"run_id":"run-b9580189","page_id":"page-1","page_title":"Alpha","blocks":[{"id":"block-1","type":"paragraph","has_children":false}] }\n',
        encoding="utf-8",
    )

    plan = build_ingest_plan(
        [str(discovered), str(block_children)],
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )

    raw_artifact_ids = {row.row["artifact_id"] for row in plan.raw_artifacts}
    ingest_batch_ids = {row.row["batch_id"] for row in plan.ingest_batches}

    for artifact in plan.artifacts:
        assert artifact.raw_artifact.row["artifact_id"] in raw_artifact_ids
        assert artifact.ingest_batch.row["batch_id"] in ingest_batch_ids

        for row in artifact.object_snapshots:
            assert row.row["artifact_id"] == artifact.raw_artifact.row["artifact_id"]
            assert row.row["batch_id"] == artifact.ingest_batch.row["batch_id"]

        for row in artifact.block_snapshots:
            assert row.row["artifact_id"] == artifact.raw_artifact.row["artifact_id"]
            assert row.row["batch_id"] == artifact.ingest_batch.row["batch_id"]
