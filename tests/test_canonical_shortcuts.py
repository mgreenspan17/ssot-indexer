from __future__ import annotations

from pathlib import Path

from canonical.store import CanonicalStoreManager
from hashing.blake3_utils import hash_bytes
from indexer.models import IngestionResult
from scanner.models import FileRecord
from shortcuts.generator import create_shortcut


class _FakeRepository:
    def __init__(self) -> None:
        self.canonical_calls: list[tuple[str, str, str, str, bool]] = []
        self.shortcut_calls: list[tuple[str, str, str, str, str]] = []

    def record_canonical_store(self, file_id: str, version_id: str, hash_digest: str, canonical_path: str, verified: bool) -> None:
        self.canonical_calls.append((file_id, version_id, hash_digest, canonical_path, verified))

    def record_shortcut(self, file_id: str, version_id: str, shortcut_path: str, target_path: str, shortcut_kind: str) -> None:
        self.shortcut_calls.append((file_id, version_id, shortcut_path, target_path, shortcut_kind))


def _sample_record(path: Path, *, shortcut_allowed: bool = True, category: str = "code") -> FileRecord:
    digest = hash_bytes(b"hello").digest
    return FileRecord(
        path=str(path),
        source="local",
        uuid7="00000000-0000-7000-8000-000000000777",
        hash_algorithm="blake3",
        blake3=digest,
        sha256=None,
        size=5,
        mtime=1.0,
        mode=0o644,
        category=category,
        mime_type="text/plain",
        shortcut_allowed=shortcut_allowed,
    )


def test_create_shortcut_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("hello", encoding="utf-8")
    link = tmp_path / "links" / "a"

    first = create_shortcut(link, target)
    second = create_shortcut(link, target)

    assert first == second
    assert link.exists()
    if link.is_symlink():
        assert link.resolve() == target.resolve()
    else:
        assert link.read_text(encoding="utf-8") == "hello"


def test_materialize_writes_canonical_and_shortcut_and_records_db(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")

    repo = _FakeRepository()
    manager = CanonicalStoreManager(tmp_path / "store", tmp_path / "shortcuts", repository=repo)

    record = _sample_record(source)
    ingestion = IngestionResult(file_id=record.uuid7, version_id="00000000-0000-7000-8000-000000000888", hash_id=1)
    result = manager.materialize(record, ingestion)

    assert result.verified is True
    assert result.shortcut_path is not None
    assert Path(result.canonical_path).exists()
    assert Path(result.shortcut_path).exists()
    assert len(repo.canonical_calls) == 1
    assert len(repo.shortcut_calls) == 1


def test_materialize_skips_shortcut_for_system_category(tmp_path: Path) -> None:
    source = tmp_path / "system.bin"
    source.write_text("hello", encoding="utf-8")

    repo = _FakeRepository()
    manager = CanonicalStoreManager(tmp_path / "store", tmp_path / "shortcuts", repository=repo)

    record = _sample_record(source, shortcut_allowed=True, category="system")
    ingestion = IngestionResult(file_id=record.uuid7, version_id="00000000-0000-7000-8000-000000000999", hash_id=2)
    result = manager.materialize(record, ingestion)

    assert result.verified is True
    assert result.shortcut_path is None
    assert len(repo.canonical_calls) == 1
    assert len(repo.shortcut_calls) == 0
