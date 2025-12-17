# -*- coding: utf-8 -*-
"""
Data models for Reel Tracker.

Contains dataclasses for settings and data structures used throughout the module.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ReelEntry:
    """Represents a single reel record in the tracker."""

    reel_id: str
    persona: str
    release: str
    reel_type: str
    clip_filename: str
    caption: str
    aspect_ratio: str
    file_path: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReelEntry":
        """Create a ReelEntry from a dictionary."""
        return cls(
            reel_id=str(data.get("Reel ID", "")),
            persona=str(data.get("Persona", "")),
            release=str(data.get("Release", "")),
            reel_type=str(data.get("Reel Type", "")),
            clip_filename=str(data.get("Clip Filename", "")),
            caption=str(data.get("Caption", "")),
            aspect_ratio=str(data.get("Aspect Ratio", "")),
            file_path=str(data.get("FilePath", "")),
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary with column names."""
        return {
            "Reel ID": self.reel_id,
            "Persona": self.persona,
            "Release": self.release,
            "Reel Type": self.reel_type,
            "Clip Filename": self.clip_filename,
            "Caption": self.caption,
            "Aspect Ratio": self.aspect_ratio,
            "FilePath": self.file_path,
        }


@dataclass
class TrackerSettings:
    """User-configurable settings for reel tracking."""

    csv_path: str
    auto_load_csv: bool
    auto_save_config: bool
    show_file_stats: bool
    master_export_folder: str
    auto_organize_enabled: bool
    create_persona_release_folders: bool
    safe_mode: bool

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "TrackerSettings":
        """Create TrackerSettings from configuration dictionary."""
        app_settings = config.get("app_settings", {})
        file_org = config.get("file_organization", {})
        return cls(
            csv_path=config.get("last_csv_path", ""),
            auto_load_csv=bool(app_settings.get("auto_load_last_csv", True)),
            auto_save_config=bool(app_settings.get("auto_save_config", True)),
            show_file_stats=bool(app_settings.get("show_file_stats", True)),
            master_export_folder=file_org.get("master_export_folder", ""),
            auto_organize_enabled=bool(file_org.get("auto_organize_enabled", False)),
            create_persona_release_folders=bool(file_org.get("create_persona_release_folders", True)),
            safe_mode=bool(file_org.get("safe_mode", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for persistence."""
        return asdict(self)


@dataclass
class DefaultMetadata:
    """Default metadata values for new reels."""

    persona: str
    release: str
    reel_type: str
    aspect_ratio: str
    caption_template: str

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "DefaultMetadata":
        """Create DefaultMetadata from configuration dictionary."""
        defaults = config.get("default_metadata", {})
        return cls(
            persona=defaults.get("persona", ""),
            release=defaults.get("release", ""),
            reel_type=defaults.get("reel_type", ""),
            aspect_ratio=defaults.get("aspect_ratio", "9:16"),
            caption_template=defaults.get("caption_template", ""),
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for persistence."""
        return asdict(self)
