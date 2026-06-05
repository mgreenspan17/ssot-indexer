import argparse
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release notes from the changelog")
    parser.add_argument("--output", default="release-notes.md")
    args = parser.parse_args()

    version = Path("VERSION").read_text(encoding="utf-8").strip()
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    recent_commits = subprocess.run(
        ["git", "log", "--oneline", "--decorate=short", "-n", "10"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    output = Path(args.output)
    output.write_text(
        f"# Release {version}\n\n{changelog}\n\n## Recent Commits\n\n{recent_commits}\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
