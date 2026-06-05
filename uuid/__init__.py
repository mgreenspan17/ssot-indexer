from __future__ import annotations

from importlib import util as importlib_util
from pathlib import Path
import sysconfig

_stdlib_uuid_path = Path(sysconfig.get_paths()["stdlib"]) / "uuid.py"
_spec = importlib_util.spec_from_file_location("_stdlib_uuid", _stdlib_uuid_path)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
	raise ImportError("unable to load stdlib uuid module")
_stdlib_uuid = importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_stdlib_uuid)

UUID = _stdlib_uuid.UUID
uuid1 = _stdlib_uuid.uuid1
uuid3 = _stdlib_uuid.uuid3
uuid4 = _stdlib_uuid.uuid4
uuid5 = _stdlib_uuid.uuid5
NAMESPACE_DNS = _stdlib_uuid.NAMESPACE_DNS
NAMESPACE_URL = _stdlib_uuid.NAMESPACE_URL
NAMESPACE_OID = _stdlib_uuid.NAMESPACE_OID
NAMESPACE_X500 = _stdlib_uuid.NAMESPACE_X500
SafeUUID = _stdlib_uuid.SafeUUID
RESERVED_NCS = _stdlib_uuid.RESERVED_NCS
RFC_4122 = _stdlib_uuid.RFC_4122
RESERVED_MICROSOFT = _stdlib_uuid.RESERVED_MICROSOFT
RESERVED_FUTURE = _stdlib_uuid.RESERVED_FUTURE
getnode = _stdlib_uuid.getnode

from uuid.generator import UUID7Value, uuid7, uuid7_str

