from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import mimetypes

try:
    import magic
except Exception:  # pragma: no cover - optional runtime fallback
    magic = None

from rules.defaults import CODE_EXTENSIONS, MEDIA_EXTENSIONS, is_system_path, shortcut_allowed


@dataclass(frozen=True)
class FileClassification:
    category: str
    mime_type: str
    shortcut_allowed: bool


def _mime_type_for(path: Path) -> str:
    if magic is not None:
        try:
            return magic.from_file(str(path), mime=True) or "application/octet-stream"
        except Exception:
            return "application/octet-stream"
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "application/octet-stream"


def classify_file(path: str | Path) -> FileClassification:
    file_path = Path(path)
    mime_type = _mime_type_for(file_path)
    name = file_path.name
    suffix = file_path.suffix.lower()

    if is_system_path(name, file_path.parent.name if file_path.parent else None):
        category = "system"
    elif suffix in CODE_EXTENSIONS or mime_type.startswith(("text/", "application/json", "application/xml")):
        category = "code"
    elif suffix in MEDIA_EXTENSIONS or mime_type.startswith(("image/", "audio/", "video/")):
        category = "media"
    elif mime_type == "application/octet-stream":
        category = "binary"
    else:
        category = "user"

    return FileClassification(category=category, mime_type=mime_type, shortcut_allowed=shortcut_allowed(category))