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
import inspect
import pkgutil

from scanner.providers.base import ProviderScanner


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
