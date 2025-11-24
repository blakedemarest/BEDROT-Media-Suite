# -*- coding: utf-8 -*-
"""
Logging setup for the Video Splitter module.
"""

from __future__ import annotations

import logging
from pathlib import Path

from core.path_utils import ensure_directory


def setup_logger(name: str = "video_splitter") -> logging.Logger:
    """
    Configure a rotating logger for the module.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_dir = ensure_directory("logs/video_splitter")
    log_path = Path(log_dir) / "video_splitter.log"

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
