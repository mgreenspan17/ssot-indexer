from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from scanner.models import ScanManifest


@dataclass(frozen=True)
class ProviderMetadata:
    name: str
    version: str
    capabilities: tuple[str, ...]
    description: str


class ProviderScanner(ABC):
    provider_name: str = "provider"
    version: str = "1.0.0"
    capabilities: tuple[str, ...] = ("scan",)
    description: str = "Provider-backed scanner"

    @abstractmethod
    def detect(self, target: str | None = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def scan(self, target: str | None = None) -> ScanManifest:
        raise NotImplementedError

    def default_target(self) -> Path | None:
        return None

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.provider_name,
            version=self.version,
            capabilities=self.capabilities,
            description=self.description,
        )
