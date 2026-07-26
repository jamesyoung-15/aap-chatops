"""Logging configuration: rotating file handler plus console output."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aap_chatops.settings import Settings

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "aap_chatops.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(settings: Settings) -> None:
    """Configure the root logger with a rotating file handler and console output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Avoid attaching duplicate handlers if called more than once (eg. in tests).
    # Checking `root_logger.handlers` isn't reliable since other tools (eg.
    # pytest's log capture) may already have attached their own handlers.
    if any(getattr(h, "_aap_chatops_handler", False) for h in root_logger.handlers):
        return

    formatter = logging.Formatter(_FORMAT)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler._aap_chatops_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler._aap_chatops_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(console_handler)
