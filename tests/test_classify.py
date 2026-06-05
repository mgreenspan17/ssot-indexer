from pathlib import Path

from classify.classifier import classify_file


def test_classify_python_file(tmp_path: Path):
    path = tmp_path / "example.py"
    path.write_text("print('hi')\n", encoding="utf-8")
    classification = classify_file(path)
    assert classification.category == "code"
    assert classification.shortcut_allowed is True
