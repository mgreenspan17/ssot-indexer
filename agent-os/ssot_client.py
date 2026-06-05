from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any
from urllib import request


@dataclass(frozen=True)
class SSOTClientConfig:
    base_url: str
    timeout_seconds: int = 30


class SSOTClient:
    def __init__(self, config: SSOTClientConfig) -> None:
        self._config = config

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            f"{self._config.base_url.rstrip('/')}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=self._config.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def scan(self, target: str) -> dict[str, Any]:
        return self._post("/scan", {"target": target})

    def resolve(self, z_path: str, lookup: dict[str, str]) -> dict[str, Any]:
        return self._post("/resolve", {"z_path": z_path, "lookup": lookup})


def build_client(base_url: str) -> SSOTClient:
    return SSOTClient(SSOTClientConfig(base_url=base_url))
