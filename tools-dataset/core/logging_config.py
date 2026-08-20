"""Application-wide logging configuration."""

import logging
import os
from logging.handlers import RotatingFileHandler


DEFAULT_LOG_LEVEL = "INFO"
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
LOG_FILE_NAME = "tools-dataset.log"
LOG_FORMAT = (
    "%(asctime)s %(levelname)s [%(process)d] %(name)s: %(message)s"
)


def _log_level(value):
    level_name = value.strip().upper()
    if level_name not in VALID_LOG_LEVELS:
        raise ValueError(
            f"Invalid LOG_LEVEL {value!r}. Use DEBUG, INFO, WARNING, ERROR, "
            "or CRITICAL."
        )
    return logging.getLevelName(level_name)


def configure_logging(app):
    """Write application and dependency logs to the Flask instance folder."""
    level = _log_level(os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL))
    os.makedirs(app.instance_path, exist_ok=True)
    log_path = os.path.join(app.instance_path, LOG_FILE_NAME)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for existing_handler in root_logger.handlers[:]:
        if getattr(existing_handler, "_tools_dataset_handler", False):
            root_logger.removeHandler(existing_handler)
            existing_handler.close()
    handler._tools_dataset_handler = True
    root_logger.addHandler(handler)

    # Python warnings are part of conversion diagnostics and belong in the
    # same log as regular application events.
    logging.captureWarnings(True)

    app.config["LOG_FILE"] = log_path
    app.config["LOG_LEVEL"] = logging.getLevelName(level)
    app.logger.setLevel(level)
    app.logger.info(
        "Logging initialized at %s level; writing to %s",
        logging.getLevelName(level),
        log_path,
    )
