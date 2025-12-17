"""
Data models used by the Video Splitter module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class SplitJob:
    """Represents a single video splitting request."""

    source_path: Path
    output_dir: Path
    clip_length: float
    jitter_percent: float
    per_clip_jitter: bool = True
    min_clip_length: float = 1.0
    reset_timestamps: bool = True
    overwrite_existing: bool = False
    random_seed: Optional[int] = None


@dataclass
class SplitSegment:
    """Represents a single clip to be generated."""

    index: int
    start: float
    duration: float
    output_path: Path


@dataclass
class VideoProbeResult:
    """Metadata returned from ffprobe."""

    duration: float
    has_audio: bool
    video_streams: int


@dataclass
class SplitterSettings:
    """User-configurable settings for video splitting."""

    output_dir: str
    clip_length_seconds: float
    jitter_percent: float
    min_clip_length: float
    per_clip_jitter: bool
    reset_timestamps: bool
    overwrite_existing: bool

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SplitterSettings":
        """Create settings from configuration dictionary."""
        return cls(
            output_dir=config.get("output_dir", ""),
            clip_length_seconds=float(config.get("clip_length_seconds", 15.0)),
            jitter_percent=float(config.get("jitter_percent", 0.0)),
            min_clip_length=float(config.get("min_clip_length", 1.0)),
            per_clip_jitter=bool(config.get("per_clip_jitter", True)),
            reset_timestamps=bool(config.get("reset_timestamps", True)),
            overwrite_existing=bool(config.get("overwrite_existing", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for persistence."""
        return asdict(self)
