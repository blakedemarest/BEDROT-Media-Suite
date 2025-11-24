# -*- coding: utf-8 -*-
"""
Configuration manager for the Video Splitter module.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from core.path_utils import resolve_config_path, resolve_output_path

from .utils import safe_print

CONFIG_FILENAME = "video_splitter_settings.json"


class ConfigManager:
    """
    Manage persistent settings for the video splitter.
    """

    def __init__(self, config_path: Optional[Path] = None):
        if config_path:
            self.settings_file = Path(config_path)
        else:
            self.settings_file = Path(resolve_config_path(CONFIG_FILENAME))

        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.config = self._load()

    def _default_config(self) -> Dict[str, Any]:
        default_output = str(resolve_output_path())
        return {
            "last_source_dir": default_output,
            "output_dir": default_output,
            "clip_length_seconds": 15.0,
            "jitter_percent": 0.0,
            "min_clip_length": 1.0,
            "per_clip_jitter": True,
            "reset_timestamps": True,
            "overwrite_existing": False,
            "max_parallel_jobs": 1,
            "recent_files": [],
        }

    def _load(self) -> Dict[str, Any]:
        default_config = self._default_config()
        if not self.settings_file.exists():
            self._write(default_config)
            return default_config.copy()

        try:
            with self.settings_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            safe_print(f"[video_splitter] WARNING: Failed to read config ({exc}). Recreating defaults.")
            self._write(default_config)
            return default_config.copy()

        # Ensure all keys exist with proper types
        for key, default_value in default_config.items():
            if key not in data or not isinstance(data[key], type(default_value)):
                data[key] = default_value

        return data

    def _write(self, config: Dict[str, Any]) -> None:
        try:
            with self.settings_file.open("w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2)
        except OSError as exc:
            safe_print(f"[video_splitter] ERROR: Failed to write config ({exc})")

    def save(self) -> None:
        with self._lock:
            self._write(self.config)

    def update(self, key: str, value: Any) -> None:
        with self._lock:
            self.config[key] = value
            self._write(self.config)

    def update_batch(self, values: Dict[str, Any]) -> None:
        with self._lock:
            self.config.update(values)
            self._write(self.config)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self.config)
