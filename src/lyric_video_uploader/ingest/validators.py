# -*- coding: utf-8 -*-
"""File validation helpers for lyric video ingestion."""

from __future__ import annotations

from pathlib import Path

ALLOWED_AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a"}


def validate_audio_file(path: Path) -> Path:
    """Validate that an audio file exists and uses an approved extension."""
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if path.suffix.lower() not in ALLOWED_AUDIO_SUFFIXES:
        raise ValueError(f"Unsupported audio format: {path.suffix}")
    return path


__all__ = ["validate_audio_file", "ALLOWED_AUDIO_SUFFIXES"]

