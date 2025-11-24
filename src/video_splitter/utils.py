# -*- coding: utf-8 -*-
"""
Utility helpers for the Video Splitter module.
"""

from __future__ import annotations

import os
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, List

from core.path_utils import get_path_resolver, resolve_path


VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".ts", ".flv"]
_video_extension_set = set(VIDEO_EXTENSIONS)


def safe_print(message: str) -> None:
    """
    Print ASCII-safe log lines to stdout.

    Args:
        message: The message to print.
    """
    if message is None:
        return

    normalized = unicodedata.normalize("NFKD", str(message))
    ascii_message = normalized.encode("ascii", "ignore").decode("ascii", "ignore")
    sys.stdout.write(ascii_message + os.linesep)
    sys.stdout.flush()


def is_video_file(path: Path | str) -> bool:
    """Return True if path has a known video extension."""
    return Path(path).suffix.lower() in _video_extension_set


def collect_video_files(paths: Iterable[str | Path]) -> List[str]:
    """
    Collect video file paths from iterable of files/folders.

    Args:
        paths: Iterable of file or directory paths.

    Returns:
        List of absolute file paths that point to supported video files.
    """
    video_files: List[str] = []

    for path in paths:
        if not path:
            continue
        try:
            path_obj = Path(path)
            if path_obj.is_absolute():
                resolved = path_obj.expanduser()
            else:
                resolved = resolve_path(path_obj)
            resolved = Path(resolved).resolve()
        except Exception:
            continue

        if resolved.is_dir():
            for root, _, files in os.walk(resolved):
                for file_name in files:
                    candidate = Path(root) / file_name
                    if is_video_file(candidate):
                        video_files.append(str(candidate))
        else:
            if is_video_file(resolved):
                video_files.append(str(resolved))

    # Deduplicate while preserving order
    seen = set()
    unique_files: List[str] = []
    for file_path in video_files:
        if file_path not in seen:
            unique_files.append(file_path)
            seen.add(file_path)

    return unique_files


def seconds_to_timestamp(value: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format for FFmpeg.
    """
    millis = int(round(value * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def ensure_directory(path: str | Path) -> Path:
    """Ensure directory exists and return resolved path."""
    resolver = get_path_resolver()
    return resolver.ensure_directory(path)
