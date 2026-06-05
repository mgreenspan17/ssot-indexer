from resolver.zpath import resolve_z_path


def test_resolve_z_path():
    result = resolve_z_path("z://abc", {"abc": "."})
    assert result.uuid7 == "abc"
    assert result.canonical_path
