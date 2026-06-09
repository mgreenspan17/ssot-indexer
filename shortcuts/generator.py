from __future__ import annotations

from pathlib import Path
import os
import shutil


def create_shortcut(link_path: str | Path, target_path: str | Path) -> Path:
    link = Path(link_path)
    target = Path(target_path)
    if link.exists() or link.is_symlink():
        if link.is_symlink() and link.resolve() == target.resolve():
            return link
        if link.is_file() and not link.is_symlink():
            try:
                if link.resolve() == target.resolve():
                    return link
            except Exception:
                pass
        if link.is_symlink() or link.is_file():
            link.unlink()
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link)
    except OSError:
        # Windows may block symlink creation without developer mode/admin rights.
        shutil.copy2(target, link)
    return link
