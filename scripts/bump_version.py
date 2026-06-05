from __future__ import annotations

import argparse
from pathlib import Path
import re


VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _read_version() -> str:
    return Path("VERSION").read_text(encoding="utf-8").strip()


def _write_version(version: str) -> None:
    Path("VERSION").write_text(version + "\n", encoding="utf-8")
    for file_name in ("pyproject.toml", "setup.cfg"):
        path = Path(file_name)
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'version = "[^"]+"', f'version = "{version}"', text, count=1)
        text = re.sub(r'version\s*=\s*[^\n]+', f'version = {version}', text, count=1)
        path.write_text(text, encoding="utf-8")


def _bump(version: str, part: str) -> str:
    match = VERSION_PATTERN.match(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version}")
    major, minor, patch = map(int, match.groups())
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


bump = _bump


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bump the repository version files")
    parser.add_argument("part", nargs="?", choices=["major", "minor", "patch"])
    parser.add_argument("--set", dest="set_version")
    args = parser.parse_args(argv)

    if args.set_version:
        version = args.set_version
    else:
        current = _read_version()
        version = _bump(current, args.part or "patch")
    _write_version(version)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

