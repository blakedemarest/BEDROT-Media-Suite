# -*- coding: utf-8 -*-
"""
Snippet Remixer bridge placeholder.

Responsible for emitting lyric timing artifacts that the Snippet Remixer can
consume. Currently validates inputs and raises a descriptive error.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from .. import ProjectContext, get_package_logger
from ..schemas import LyricDocument, LineSegment

LOGGER = get_package_logger("lyric_video.bridge")


def _verify_snippet_remixer_importable() -> None:
    """Ensure the snippet_remixer package can be imported."""
    try:
        importlib.import_module("snippet_remixer")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "snippet_remixer package is not importable. Activate the correct virtual "
            "environment before running the Lyric Video Uploader."
        ) from exc


def publish(doc: LyricDocument, context: ProjectContext) -> dict[str, Path]:
    """Publish lyric timing metadata for Snippet Remixer."""
    _verify_snippet_remixer_importable()
    context.ensure_structure()
    bridge_dir = context.exports_dir / "snippet_bridge"
    bridge_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = bridge_dir / "lyric_timeline.json"
    sections_path = bridge_dir / "sections.json"
    beatgrid_path = bridge_dir / "beatgrid.json"

    timeline_payload = _build_timeline_payload(doc)
    with timeline_path.open("w", encoding="utf-8") as handle:
        json.dump(timeline_payload, handle, indent=2)

    sections_payload = _build_sections_payload(doc)
    with sections_path.open("w", encoding="utf-8") as handle:
        json.dump(sections_payload, handle, indent=2)

    if doc.beat_grid:
        with beatgrid_path.open("w", encoding="utf-8") as handle:
            json.dump(doc.beat_grid.to_dict(), handle, indent=2)
        beatgrid_file = beatgrid_path
    else:
        beatgrid_file = None

    LOGGER.info("Snippet Remixer bridge artifacts written to %s", bridge_dir)
    LOGGER.info("LyricTimingReady")
    if doc.beat_grid:
        LOGGER.info("BeatGridReady")
    return {
        "timeline": timeline_path,
        "sections": sections_path,
        "beatgrid": beatgrid_file,
    }


def _build_timeline_payload(doc: LyricDocument) -> list[dict]:
    entries = []
    lines = doc.lines if doc.lines else [LineSegment(words=doc.words, text=" ".join(w.text for w in doc.words), start=doc.words[0].start, end=doc.words[-1].end)]  # type: ignore[name-defined]
    for line in lines:
        entries.append(
            {
                "text": line.text,
                "start": line.start,
                "end": line.end,
                "words": [word.to_dict() for word in line.words],
            }
        )
    return entries


def _build_sections_payload(doc: LyricDocument) -> list[dict]:
    if doc.beat_grid and doc.beat_grid.events:
        events = sorted(doc.beat_grid.events, key=lambda evt: evt.start)
        sections: list[dict] = []
        for idx, event in enumerate(events):
            section = {
                "start": event.start,
                "bpm": event.bpm,
            }
            if idx + 1 < len(events):
                section["end"] = events[idx + 1].start
            sections.append(section)
        return sections

    # Default fallback covering the entire document duration
    if doc.words:
        start = doc.words[0].start
        end = doc.words[-1].end
    else:
        start = 0.0
        end = 0.0
    return [{"start": start, "end": end, "bpm": None}]


__all__ = ["publish"]
