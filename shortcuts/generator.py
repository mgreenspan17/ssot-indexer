from __future__ import annotations

from pathlib import Path
import os


def create_shortcut(link_path: str | Path, target_path: str | Path) -> Path:
    link = Path(link_path)
    target = Path(target_path)
    if link.exists() or link.is_symlink():
        if link.is_symlink() and link.resolve() == target.resolve():
            return link
        if link.is_symlink() or link.is_file():
            link.unlink()
    link.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target, link)
    return link
