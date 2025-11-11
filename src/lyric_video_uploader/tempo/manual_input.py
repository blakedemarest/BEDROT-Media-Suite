# -*- coding: utf-8 -*-
"""
Manual tempo input parsing helpers.

Validates BPM and offset fields collected from the CLI/GUI before the beat grid
service consumes them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ManualTempoSettings:
    """User-provided tempo controls."""

    bpm: float
    offset_seconds: float = 0.0
    subdivision: int = 4


def parse_bpm(value: str) -> float:
    """Parse and validate BPM from a string value."""
    try:
        bpm = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid BPM: {value}") from exc

    if bpm <= 0:
        raise ValueError("BPM must be greater than zero.")
    if bpm > 400:
        raise ValueError("BPM exceeds supported maximum (400).")
    return bpm


def parse_offset(value: str | None) -> float:
    """Parse an optional offset string into seconds."""
    if value in (None, "", "0"):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid tempo offset: {value}") from exc


def build_settings(bpm: str, offset: str | None = None, subdivision: int = 4) -> ManualTempoSettings:
    """Create settings from raw user input."""
    if subdivision <= 0:
        raise ValueError("Subdivision must be positive.")
    return ManualTempoSettings(
        bpm=parse_bpm(bpm),
        offset_seconds=parse_offset(offset),
        subdivision=subdivision,
    )


__all__ = ["ManualTempoSettings", "build_settings", "parse_bpm", "parse_offset"]

