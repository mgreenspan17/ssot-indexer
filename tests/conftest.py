from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _ensure_uuid7_compat() -> None:
    """Expose local uuid7 helpers even when stdlib uuid is imported first."""
    import uuid as std_uuid

    generator_path = REPO_ROOT / "uuid" / "generator.py"
    spec = importlib.util.spec_from_file_location("ssot_uuid_generator", generator_path)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    setattr(std_uuid, "uuid7", module.uuid7)
    setattr(std_uuid, "uuid7_str", module.uuid7_str)
    setattr(std_uuid, "UUID7Value", module.UUID7Value)

    bridge = ModuleType("uuid.generator")
    bridge.uuid7 = module.uuid7
    bridge.uuid7_str = module.uuid7_str
    bridge.UUID7Value = module.UUID7Value
    sys.modules["uuid.generator"] = bridge


_ensure_uuid7_compat()
