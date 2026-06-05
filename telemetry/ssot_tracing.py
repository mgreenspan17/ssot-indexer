from __future__ import annotations

from observability.tracing import configure_tracing


def tracing_provider(service_name: str = "ssot-indexer"):
    return configure_tracing(service_name)
