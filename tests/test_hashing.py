from hashing.blake3_utils import hash_bytes


def test_hash_bytes_is_deterministic():
    first = hash_bytes(b"hello")
    second = hash_bytes(b"hello")
    assert first.digest == second.digest
    assert first.algorithm == "blake3"
