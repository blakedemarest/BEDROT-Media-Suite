"""
Data models used by the Video Splitter module.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
