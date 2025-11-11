# -*- coding: utf-8 -*-
"""
Beat grid service placeholder combining manual tempo input and tempo maps.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import json

from .. import ProjectContext, get_package_logger
from ..schemas import BeatGrid, TempoEvent
from .manual_input import ManualTempoSettings
from .tempo_map_loader import load_tempo_map, validate_tempo_events

LOGGER = get_package_logger("lyric_video.tempo")


@dataclass(slots=True)
class BeatGridResult:
    """Wrapper describing where the beat grid was stored."""

    beat_grid: BeatGrid
    destination: Path


def build_manual_grid(settings: ManualTempoSettings) -> BeatGrid:
    """Construct a BeatGrid from manual settings."""
    grid = BeatGrid(
        source="manual",
        events=[TempoEvent(start=settings.offset_seconds, bpm=settings.bpm)],
        subdivision=settings.subdivision,
    )
    LOGGER.info("Built manual beat grid: bpm=%s, offset=%s", settings.bpm, settings.offset_seconds)
    return grid


def build_from_tempo_map(path: Path, *, subdivision: int = 4) -> BeatGrid:
    """Construct a BeatGrid from an external tempo map."""
    events = load_tempo_map(path)
    validate_tempo_events(events)
    LOGGER.info("Loaded tempo map with %d events from %s", len(events), path)
    return BeatGrid(source=path.name, events=list(events), subdivision=subdivision)


def persist_beat_grid(grid: BeatGrid, context: ProjectContext) -> BeatGridResult:
    """Persist beat grid metadata to the project timing directory."""
    context.ensure_structure()
    destination = context.timing_dir / "beatgrid.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(grid.to_dict(), handle, indent=2)
    LOGGER.info("Beat grid saved to %s", destination)
    return BeatGridResult(beat_grid=grid, destination=destination)


def load_persisted_beat_grid(path: Path) -> BeatGrid:
    """Load a beat grid from disk."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return BeatGrid.from_dict(payload)


__all__ = ["BeatGridResult", "build_manual_grid", "build_from_tempo_map", "persist_beat_grid", "load_persisted_beat_grid"]
