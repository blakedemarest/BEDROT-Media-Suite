# -*- coding: utf-8 -*-
"""
Tempo map loader placeholder.

Will be responsible for parsing CSV/JSON tempo maps that contain bpm changes
over time. For now, the module performs basic validation of file extensions and
gives a descriptive error to align with the no-fallback policy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import csv
import json

from ..schemas import TempoEvent

SUPPORTED_EXTENSIONS = {".csv", ".json"}


def load_tempo_map(path: Path) -> List[TempoEvent]:
    """
    Load a tempo map file.

    Args:
        path: File path to the tempo map.

    Raises:
        FileNotFoundError: If the file is missing.
        ValueError: If the extension is unsupported or parsing fails.
    """
    if not path.exists():
        raise FileNotFoundError(f"Tempo map not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported tempo map extension: {path.suffix}. "
            "Supported formats: CSV, JSON."
        )

    if suffix == ".csv":
        return _load_csv_tempo_map(path)
    return _load_json_tempo_map(path)


def validate_tempo_events(events: Iterable[TempoEvent]) -> None:
    """Ensure tempo events are sorted and non-empty."""
    events_list = list(events)
    if not events_list:
        raise ValueError("Tempo map produced no tempo events.")

    previous_start = None
    for event in events_list:
        if event.bpm <= 0:
            raise ValueError("Tempo event BPM must be positive.")
        if previous_start is not None and event.start < previous_start:
            raise ValueError("Tempo events must be in ascending order.")
        previous_start = event.start


def _load_csv_tempo_map(path: Path) -> List[TempoEvent]:
    events: List[TempoEvent] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Tempo map CSV has no header: {path}")

        for row in reader:
            events.append(_row_to_tempo_event(row))
    validate_tempo_events(events)
    return events


def _load_json_tempo_map(path: Path) -> List[TempoEvent]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        events_payload = payload.get("events") or payload.get("tempo") or []
    else:
        events_payload = payload

    if not isinstance(events_payload, list):
        raise ValueError(f"Invalid tempo map structure in {path}.")

    events = [_row_to_tempo_event(item) for item in events_payload]
    validate_tempo_events(events)
    return events


def _row_to_tempo_event(row: dict) -> TempoEvent:
    """Convert a CSV/JSON row into a TempoEvent."""
    try:
        start = float(
            row.get("start")
            or row.get("start_time")
            or row.get("time")
            or row.get("seconds")
        )
        bpm = float(row.get("bpm") or row.get("tempo"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid tempo event payload: {row}") from exc
    if start < 0:
        raise ValueError("Tempo event start time must be non-negative.")
    if bpm <= 0:
        raise ValueError("Tempo event BPM must be positive.")
    return TempoEvent(start=start, bpm=bpm)


__all__ = ["load_tempo_map", "validate_tempo_events"]
