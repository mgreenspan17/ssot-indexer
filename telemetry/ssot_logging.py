from __future__ import annotations

from observability.logging import configure_logging, get_logger


def logger(name: str):
    configure_logging()
    return get_logger(name)
