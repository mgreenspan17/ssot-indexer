from __future__ import annotations

import re
from pathlib import Path

from hashing.provenance import build_merkle_tree, canonical_json_dumps
from indexer.notion_ingest import (
    NotionPlanPostgresWriter,
    build_ingest_plan,
    format_dry_run_summary,
    resolve_database_write_request,
)


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


def test_write_mode_requires_confirmation_flag():
    try:
        resolve_database_write_request(
            write_enabled=True,
            confirm_db_write=False,
            environ={"DATABASE_URL": "postgresql://redacted"},
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "--confirm-db-write" in str(exc)


def test_write_mode_requires_database_url():
    try:
        resolve_database_write_request(
            write_enabled=True,
            confirm_db_write=True,
            environ={},
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "DATABASE_URL" in str(exc)


def test_write_mode_resolves_database_url_only_when_enabled():
    dsn = resolve_database_write_request(
        write_enabled=False,
        confirm_db_write=False,
        environ={"DATABASE_URL": "postgresql://hidden"},
    )
    assert dsn is None


def test_writer_order_and_strategy_map():
    expected_order = (
        "notion_index.crawl_run",
        "notion_index.raw_artifact",
        "notion_index.ingest_batch",
        "notion_index.merkle_tree",
        "notion_index.merkle_node",
        "notion_index.object_snapshot",
        "notion_index.block_snapshot",
        "notion_index.parent_edge",
        "notion_index.blob_pointer",
        "notion_index.status_event",
        "notion_index.object_current",
    )
    assert NotionPlanPostgresWriter.WRITE_ORDER == expected_order
    strategy = NotionPlanPostgresWriter.sql_strategy_map()
    assert strategy["notion_index.object_current"] == "insert_object_current_upsert"
    assert strategy["notion_index.object_snapshot"].endswith("append_only")


def test_object_current_rows_keep_tenant_workspace_scope(tmp_path: Path):
    discovered = tmp_path / "discovered_pages.jsonl"
    discovered.write_text(
        '{"run_id":"run-b9580189","page_id":"page-1","page_title":"Alpha","object":"page"}\n',
        encoding="utf-8",
    )
    plan = build_ingest_plan([str(discovered)], tenant_id="tenant-a", workspace_id="workspace-a")
    assert plan.object_current_rows
    row = plan.object_current_rows[0].row
    assert row["tenant_id"] == "tenant-a"
    assert row["workspace_id"] == "workspace-a"
    assert row["object_id"] == "page-1"


class _FakeCursor:
    def __init__(self, table_order: list[str]):
        self._table_order = table_order
        self.rowcount = 0
        self._fetch: tuple[bool] | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str, _params=None):
        match = re.search(r"insert\s+into\s+([a-zA-Z0-9_.]+)", sql, flags=re.IGNORECASE)
        if match:
            self._table_order.append(match.group(1).lower())
        self.rowcount = 1
        if "returning (xmax = 0) as inserted" in sql:
            self._fetch = (True,)
        else:
            self._fetch = None

    def fetchone(self):
        return self._fetch


class _FakeConnection:
    def __init__(self):
        self.table_order: list[str] = []
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return _FakeCursor(self.table_order)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_writer_uses_fk_safe_order_and_commits(tmp_path: Path):
    discovered = tmp_path / "discovered_pages.jsonl"
    discovered.write_text(
        '{"run_id":"run-b9580189","page_id":"page-1","page_title":"Alpha","object":"page"}\n',
        encoding="utf-8",
    )
    plan = build_ingest_plan([str(discovered)], tenant_id="tenant-a", workspace_id="workspace-a")
    fake_connection = _FakeConnection()
    writer = NotionPlanPostgresWriter("postgresql://redacted", connect_fn=lambda _dsn: fake_connection)
    report = writer.write_plan(plan)

    first_seen: list[str] = []
    for table in fake_connection.table_order:
        if table not in first_seen:
            first_seen.append(table)

    expected_order = [
        table_name
        for table_name, rows in NotionPlanPostgresWriter.planned_table_rows(plan)
        if rows
    ]
    assert first_seen == expected_order
    assert report.transaction_committed is True
    assert fake_connection.committed is True
