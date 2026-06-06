from __future__ import annotations

from pathlib import Path
import sys

from scanner.providers.registry import get_provider_scanner, list_provider_names


def test_provider_registry_supports_dynamic_module_paths(tmp_path: Path, monkeypatch):
    module_path = tmp_path / "dynamic_provider.py"
    module_path.write_text(
        "from scanner.providers.base import ProviderScanner\n"
        "from scanner.base import build_source_descriptor, manifest_from_records\n"
        "from scanner.models import ScanManifest\n"
        "class DynamicProvider(ProviderScanner):\n"
        "    provider_name = 'dynamic'\n"
        "    def detect(self, target=None):\n"
        "        return target == 'dynamic'\n"
        "    def scan(self, target=None):\n"
        "        descriptor = build_source_descriptor('provider', 'dynamic', source_label='dynamic')\n"
        "        return manifest_from_records('dynamic://root', [], descriptor)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("SSOT_SCANNER_PROVIDER_MODULES", "dynamic_provider")
    assert "dynamic" in set(list_provider_names())
    assert get_provider_scanner("dynamic").provider_name == "dynamic"
