"""Structured logging for UHB with JSON and console formatters."""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for machine-readable output."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            payload["exception"] = str(record.exc_info[1])
        return json.dumps(payload)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with colors."""

    COLORS = {
        logging.DEBUG: "\033[36m",     # cyan
        logging.INFO: "\033[32m",      # green
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        level = f"{color}{record.levelname:<8}{self.RESET}"
        return f"{level} | {record.name} | {record.getMessage()}"


def get_logger(name: str, level: int = logging.INFO, json_output: bool = False) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__).
        level: Logging level.
        json_output: If True, emit JSON; otherwise console with colors.

    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = JSONFormatter() if json_output else ConsoleFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def configure_root(level: int = logging.INFO, json_output: bool = False) -> None:
    """Configure the root logger for the entire UHB application.

    Args:
        level: Logging level for all UHB loggers.
        json_output: If True, structured JSON output.
    """
    root = logging.getLogger("uhb")
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    formatter = JSONFormatter() if json_output else ConsoleFormatter()
    handler.setFormatter(formatter)
    root.addHandler(handler)
