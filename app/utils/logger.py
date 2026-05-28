from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import loguru

from app.config.settings import Settings


class InterceptHandler(logging.Handler):
    """Intercept stdlib logging and forward to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging(
    log_dir: Path,
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "30 days",
    json_format: bool = False,
) -> None:
    """Configure structured logging with loguru.

    Args:
        log_dir: Directory for log files.
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        rotation: Max file size before rotation (e.g. "10 MB").
        retention: Max age for retained logs (e.g. "30 days").
        json_format: If True, use JSON-structured output.
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    loguru.logger.remove()

    fmt = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {name}:{function}:{line} | {message}"
    )
    if json_format:
        fmt = json.dumps

    loguru.logger.add(
        sys.stderr,
        level=level.upper(),
        format=fmt,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    loguru.logger.add(
        log_dir / "correspondence.log",
        level=level.upper(),
        format=fmt,
        rotation=rotation,
        retention=retention,
        compression="gz",
        encoding="utf-8",
        backtrace=True,
        diagnose=False,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    loguru.logger.info(
        "Logging configured",
        extra={
            "log_dir": str(log_dir),
            "level": level,
            "rotation": rotation,
            "retention": retention,
        },
    )


def get_logger(name: str) -> loguru.Logger:
    """Get a named logger instance.

    The name should follow the pattern 'app.{module}' or 'app.{layer}.{module}'.
    """
    return loguru.logger.bind(name=name)
