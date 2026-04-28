"""
Photagger — Logging configuration.
Dual-output: rotating file log + console stream.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .constants import APP_NAME


def get_log_dir() -> Path:
    """Get platform-appropriate log directory."""
    import os
    appdata = os.environ.get("APPDATA", Path.home() / ".config")
    log_dir = Path(appdata) / APP_NAME / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the root Photagger logger with file + console handlers."""
    logger = logging.getLogger(APP_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Rotating file handler (10 MB max, 3 backups)
    try:
        log_file = get_log_dir() / "photagger.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("Could not create log file, continuing with console only.")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger scoped to a module."""
    return logging.getLogger(f"{APP_NAME}.{name}")
