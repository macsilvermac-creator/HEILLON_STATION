"""Structured logging setup for Heillon Legal.

In production: JSON lines to stdout — parseable by log aggregators (Grafana Loki, Datadog, etc.).
In development/staging: coloured human-readable format.

Usage::

    from app.core.logging_config import configure_logging
    configure_logging(environment="production")
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record, written to stdout."""

    _LEVEL_NAMES = {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warning",
        logging.ERROR: "error",
        logging.CRITICAL: "critical",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": self._LEVEL_NAMES.get(record.levelno, record.levelname.lower()),
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        for key in ("request_id", "organization_id", "mission_id", "user_id"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val

        return json.dumps(payload, ensure_ascii=False, default=str)


_COLOUR_RESET = "\033[0m"
_COLOUR_MAP = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[35m",
}


class _DevFormatter(logging.Formatter):
    """Colourised single-line format for local development."""

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOUR_MAP.get(record.levelno, "")
        ts = datetime.now(UTC).strftime("%H:%M:%S")
        level = record.levelname[:4]
        msg = record.getMessage()
        location = f"{record.module}:{record.lineno}"
        formatted = f"{ts} {colour}{level}{_COLOUR_RESET} [{record.name}] {msg}  ({location})"
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        return formatted


def configure_logging(environment: str = "development", level: str = "INFO") -> None:
    """Configure the root logger and all Heillon loggers.

    Args:
        environment: ``"production"`` → JSON formatter; everything else → dev formatter.
        level: Minimum log level (e.g. ``"DEBUG"``, ``"INFO"``).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_DevFormatter())

    root = logging.getLogger()
    root.setLevel(numeric_level)

    if root.handlers:
        root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for quiet_logger in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(quiet_logger).setLevel(logging.WARNING)

    logging.getLogger("heillon").setLevel(numeric_level)
