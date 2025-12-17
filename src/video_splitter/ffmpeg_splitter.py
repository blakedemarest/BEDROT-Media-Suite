# -*- coding: utf-8 -*-
"""
FFmpeg utilities for the Video Splitter module.
"""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .models import SplitJob, SplitSegment, VideoProbeResult
from .utils import seconds_to_timestamp


class FFmpegError(RuntimeError):
    """Raised when FFmpeg operations fail."""


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )


def probe_video(path: Path) -> VideoProbeResult:
    """
    Read duration and stream metadata using ffprobe.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_entries",
        "format=duration",
        "-show_streams",
        str(path),
    ]
    try:
        result = _run_command(command)
    except subprocess.CalledProcessError as exc:
        raise FFmpegError(f"ffprobe failed for {path}: {exc.stderr}") from exc

    payload = json.loads(result.stdout or "{}")
    duration = float(payload.get("format", {}).get("duration", 0.0))

    streams = payload.get("streams", [])
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    video_streams = sum(1 for stream in streams if stream.get("codec_type") == "video")

    if duration <= 0:
        raise FFmpegError(f"Unable to detect duration for {path}")

    return VideoProbeResult(duration=duration, has_audio=has_audio, video_streams=video_streams)


def generate_segments(job: SplitJob, duration: float, rng: Optional[random.Random] = None) -> List[SplitSegment]:
    """
    Build a list of split segments given video metadata and job parameters.
    """
    if job.clip_length <= 0:
        raise ValueError("clip length must be positive")
    if job.min_clip_length <= 0:
        raise ValueError("min clip length must be positive")

    rng = rng or random.Random(job.random_seed)
    jitter_fraction = max(0.0, min(job.jitter_percent, 90.0)) / 100.0
    base_length = job.clip_length
    current_start = 0.0
    segments: List[SplitSegment] = []
    unique_stem = _build_unique_stem(job.source_path)

    if jitter_fraction == 0.0:
        jitter_multiplier = 1.0
    else:
        jitter_multiplier = 1.0 + rng.uniform(-jitter_fraction, jitter_fraction)

    index = 0
    while current_start + job.min_clip_length <= duration:
        if job.per_clip_jitter:
            if jitter_fraction > 0.0:
                jitter_multiplier = 1.0 + rng.uniform(-jitter_fraction, jitter_fraction)
            else:
                jitter_multiplier = 1.0

        segment_length = base_length * jitter_multiplier
        segment_length = max(job.min_clip_length, segment_length)

        remaining = duration - current_start
        if segment_length > remaining:
            segment_length = remaining

        output_name = f"{unique_stem}_clip_{index:03d}.mp4"
        segment = SplitSegment(
            index=index,
            start=current_start,
            duration=segment_length,
            output_path=job.output_dir / output_name,
        )
        segments.append(segment)

        current_start += segment_length
        index += 1

        if remaining <= segment_length:
            break

    # Handle tail shorter than min_clip_length
    remaining_tail = duration - current_start
    if remaining_tail >= 0.5 and remaining_tail < job.min_clip_length:
        output_name = f"{unique_stem}_clip_{index:03d}.mp4"
        segments.append(
            SplitSegment(
                index=index,
                start=current_start,
                duration=remaining_tail,
                output_path=job.output_dir / output_name,
            )
        )

    return segments


def build_segment_command(job: SplitJob, segment: SplitSegment) -> List[str]:
    """
    Build the FFmpeg command used to create a single clip segment.
    """
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-stats",
        "-ss",
        seconds_to_timestamp(segment.start),
        "-i",
        str(job.source_path),
        "-t",
        seconds_to_timestamp(segment.duration),
        "-map",
        "0",
        "-c",
        "copy",
    ]

    if job.reset_timestamps:
        command.extend(["-reset_timestamps", "1"])

    if job.overwrite_existing:
        command.append("-y")
    else:
        command.append("-n")

    command.append(str(segment.output_path))
    return command


def _build_unique_stem(source_path: Path) -> str:
    """
    Derive a deterministic, ASCII-only stem per source path to avoid name collisions
    when different videos share the same basename.
    """
    try:
        normalized = str(source_path.resolve(strict=False))
    except Exception:
        normalized = str(source_path)

    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{source_path.stem}_{digest}"
