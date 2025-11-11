# -*- coding: utf-8 -*-
"""
Render preset management.

Loads preset metadata from configuration files and verifies referenced assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .. import get_config_manager, get_package_logger

LOGGER = get_package_logger("lyric_video.render.presets")


@dataclass(slots=True)
class RenderPreset:
    """Container for render preset metadata."""

    name: str
    background: Path
    font_path: Path
    font_size: int = 48
    font_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    shadow_color: str = "#000000"
    description: str | None = None


class PresetManager:
    """Loads preset descriptors from configuration and asset directories."""

    def __init__(self, assets_root: Path | None = None):
        base = assets_root or Path("assets/lyric_video")
        self.backgrounds_dir = base / "backgrounds"
        self.templates_dir = base / "templates"
        self.fonts_dir = base / "fonts"
        self.config = get_config_manager().load_config("lyric_video_config.json", "lyric_video")
        self._presets = self._load_presets()

    def _load_presets(self) -> Dict[str, RenderPreset]:
        presets_config = self.config.get("render_presets", {})
        presets: Dict[str, RenderPreset] = {}
        for name, payload in presets_config.items():
            background = self.backgrounds_dir / payload.get("background", "")
            font_path = self.fonts_dir / payload.get("font", "")
            presets[name] = RenderPreset(
                name=name,
                background=background,
                font_path=font_path,
                font_size=int(payload.get("font_size", 48)),
                font_color=payload.get("font_color", "#FFFFFF"),
                outline_color=payload.get("outline_color", "#000000"),
                shadow_color=payload.get("shadow_color", "#000000"),
                description=payload.get("description"),
            )
        LOGGER.debug("Loaded %d render presets from config.", len(presets))
        return presets

    def list_presets(self) -> Dict[str, RenderPreset]:
        """Return preset metadata keyed by preset name."""
        return self._presets

    def get_preset(self, name: str) -> RenderPreset:
        """Fetch a preset by name and validate its assets exist."""
        preset = self._presets.get(name)
        if preset is None:
            raise KeyError(f"Render preset '{name}' not found in configuration.")
        if not preset.background.exists():
            raise FileNotFoundError(f"Background asset for preset '{name}' not found: {preset.background}")
        if not preset.font_path.exists():
            raise FileNotFoundError(f"Font asset for preset '{name}' not found: {preset.font_path}")
        return preset


__all__ = ["PresetManager", "RenderPreset"]
