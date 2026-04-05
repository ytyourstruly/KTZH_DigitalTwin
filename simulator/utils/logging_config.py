"""
logging_config.py — Configures stdlib logging from the YAML config dict.
"""

from __future__ import annotations
import logging


def setup_logging(config: dict) -> None:
    log_cfg = config.get("logging", {})
    level_str = log_cfg.get("level", "INFO").upper()
    fmt = log_cfg.get(
        "format",
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    level = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler()],
    )

    # Quieten noisy uvicorn/websockets internals unless DEBUG
    if level > logging.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("websockets").setLevel(logging.WARNING)