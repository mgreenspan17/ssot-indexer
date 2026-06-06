from __future__ import annotations

"""Provider registry with auto-discovery.

Assumptions:
- Provider modules live under scanner.providers and subclass ProviderScanner.

Boundaries:
- Discovery imports provider modules but does not execute scans.

Integration notes:
- New provider modules can be added without modifying this file.
"""

import importlib
from importlib import metadata as importlib_metadata
import inspect
import os
import pkgutil

from scanner.providers.base import ProviderMetadata, ProviderScanner


def _discover() -> dict[str, ProviderScanner]:
    scanners: dict[str, ProviderScanner] = {}
    package_name = "scanner.providers"
    package = importlib.import_module(package_name)
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name in {"base", "registry"}:
            continue
        module = importlib.import_module(f"{package_name}.{module_info.name}")
        for value in vars(module).values():
            if inspect.isclass(value) and issubclass(value, ProviderScanner) and value is not ProviderScanner:
                instance = value()
                scanners[instance.provider_name] = instance
    for module_path in filter(None, os.environ.get("SSOT_SCANNER_PROVIDER_MODULES", "").split(os.pathsep)):
        module = importlib.import_module(module_path)
        for value in vars(module).values():
            if inspect.isclass(value) and issubclass(value, ProviderScanner) and value is not ProviderScanner:
                instance = value()
                scanners[instance.provider_name] = instance
    try:
        entry_points = importlib_metadata.entry_points()
        selected = entry_points.select(group="ssot_indexer.scanner_providers")
    except Exception:
        selected = ()
    for entry_point in selected:
        value = entry_point.load()
        if inspect.isclass(value) and issubclass(value, ProviderScanner):
            instance = value()
            scanners[instance.provider_name] = instance
    return scanners


def get_provider_registry() -> dict[str, ProviderScanner]:
    return _discover()


def list_provider_names() -> tuple[str, ...]:
    return tuple(sorted(get_provider_registry()))


def get_provider_scanner(name: str) -> ProviderScanner:
    registry = get_provider_registry()
    if name not in registry:
        raise KeyError(f"unknown provider scanner: {name}")
    return registry[name]


def get_provider_metadata(name: str) -> ProviderMetadata:
    return get_provider_scanner(name).metadata()


def detect_provider_scanner(target: str | None = None) -> ProviderScanner | None:
    for scanner in get_provider_registry().values():
        if scanner.detect(target):
            return scanner
    return None
