from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


SYSTEM_NAMES = {"$recycle.bin", "desktop.ini", "thumbs.db", ".ds_store"}
SYSTEM_PREFIXES = (".", "~$")
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".sql",
    ".sh",
    ".ps1",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".xml",
    ".html",
    ".css",
}
MEDIA_EXTENSIONS = {
    ".mp3",
    ".mp4",
    ".mov",
    ".mkv",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".wav",
    ".flac",
}


@dataclass(frozen=True)
class ClassificationRule:
    kind: str
    shortcut_allowed: bool


def is_system_path(name: str, parent: str | None = None) -> bool:
    lowered = name.lower()
    if lowered in SYSTEM_NAMES:
        return True
    if any(lowered.startswith(prefix) for prefix in SYSTEM_PREFIXES):
        return True
    if parent:
        parent_path = PurePosixPath(parent)
        if parent_path.parts and parent_path.parts[0].lower() in {"windows", "system32", "program files", "program files (x86)"}:
            return True
    return False


def shortcut_allowed(kind: str) -> bool:
    return kind not in {"system", "binary"}