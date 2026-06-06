from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from scanner.models import ScanManifest


class ProviderScanner(ABC):
    provider_name: str = "provider"

    @abstractmethod
    def detect(self, target: str | None = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def scan(self, target: str | None = None) -> ScanManifest:
        raise NotImplementedError

    def default_target(self) -> Path | None:
        return None
