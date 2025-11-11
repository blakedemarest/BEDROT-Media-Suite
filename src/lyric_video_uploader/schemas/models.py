# -*- coding: utf-8 -*-
"""
Canonical data models used by the Lyric Video Uploader pipeline.

These dataclasses provide a minimal contract between the transcription,
tempo/beat grid services, renderers, and export packaging routines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(slots=True)
class WordToken:
    """Represents a single transcribed word aligned to audio."""

    text: str
    start: float
    end: float
    confidence: float | None = None

    def duration(self) -> float:
        """Return the token duration in seconds."""
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict:
        """Serialize token to a dictionary."""
        payload = {
            "text": self.text,
            "start": self.start,
            "end": self.end,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload


@dataclass(slots=True)
class LineSegment:
    """Represents a contiguous line of lyrics composed of multiple words."""

    words: Sequence[WordToken]
    text: str
    start: float
    end: float

    def to_dict(self) -> dict:
        """Serialize the line segment."""
        return {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "words": [word.to_dict() for word in self.words],
        }


@dataclass(slots=True)
class TempoEvent:
    """Defines a tempo breakpoint as supplied by manual authoring."""

    start: float
    bpm: float

    def to_dict(self) -> dict:
        return {"start": self.start, "bpm": self.bpm}


@dataclass(slots=True)
class BeatGrid:
    """Container describing beat timing derived from manual tempo inputs."""

    source: str
    events: List[TempoEvent] = field(default_factory=list)
    subdivision: int = 4

    def require_events(self) -> None:
        """Fail fast if no tempo events exist."""
        if not self.events:
            raise ValueError("Beat grid has no tempo events; manual tempo input is required.")

    def to_dict(self) -> dict:
        """Serialize beat grid to JSON-compatible structure."""
        return {
            "source": self.source,
            "subdivision": self.subdivision,
            "events": [event.to_dict() for event in self.events],
        }

    def generate_beats(self, *, until: float | None = None, max_beats: int | None = 20000) -> List[float]:
        """
        Generate beat timestamps based on tempo events.

        Args:
            until: Optional ceiling for beat timestamps. If None, runs until max_beats.
            max_beats: Safety cap to prevent runaway generation.
        """
        self.require_events()
        beats: List[float] = []
        sorted_events = sorted(self.events, key=lambda event: event.start)

        for idx, event in enumerate(sorted_events):
            segment_start = event.start
            segment_end = (
                sorted_events[idx + 1].start if idx + 1 < len(sorted_events) else until
            )
            # If until is not provided, segment_end remains None and we rely on max_beats.
            step = (60.0 / event.bpm) / max(self.subdivision, 1)
            current = segment_start

            while True:
                if until is not None and current > until:
                    break
                beats.append(round(current, 6))
                if max_beats is not None and len(beats) >= max_beats:
                    return beats
                current += step
                if segment_end is not None and current >= segment_end:
                    break

        return beats

    @classmethod
    def from_dict(cls, payload: dict) -> BeatGrid:
        """Create a beat grid from serialized data."""
        events_payload = payload.get("events") or []
        events = [TempoEvent(start=float(item["start"]), bpm=float(item["bpm"])) for item in events_payload]
        subdivision = int(payload.get("subdivision", 4))
        return cls(source=str(payload.get("source", "manual")), events=events, subdivision=subdivision)


@dataclass(slots=True)
class LyricDocument:
    """Complete lyric/timing bundle for downstream rendering."""

    audio_path: Path
    words: Sequence[WordToken]
    lines: Sequence[LineSegment]
    beat_grid: BeatGrid | None = None

    def ensure_consistency(self) -> None:
        """Perform lightweight validation to catch obvious alignment issues."""
        if not self.words:
            raise ValueError("Lyric document contains no words.")
        if any(token.start < 0 or token.end < 0 for token in self.words):
            raise ValueError("Word timings must be non-negative.")
        if self.lines and any(line.start < 0 or line.end < 0 for line in self.lines):
            raise ValueError("Line timings must be non-negative.")

    def to_dict(self) -> dict:
        """Serialize lyric document."""
        payload = {
            "audio_path": str(self.audio_path),
            "words": [word.to_dict() for word in self.words],
            "lines": [line.to_dict() for line in self.lines],
        }
        if self.beat_grid:
            payload["beat_grid"] = self.beat_grid.to_dict()
        return payload


def coerce_word_tokens(records: Iterable[dict]) -> List[WordToken]:
    """
    Convert an iterable of dictionaries into word token instances.

    Args:
        records: Iterable of dictionaries with keys 'text', 'start', 'end', optional 'confidence'.

    Returns:
        List of WordToken objects.
    """
    tokens: List[WordToken] = []
    for item in records:
        try:
            tokens.append(
                WordToken(
                    text=str(item["text"]),
                    start=float(item["start"]),
                    end=float(item["end"]),
                    confidence=float(item["confidence"]) if "confidence" in item and item["confidence"] is not None else None,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid word token payload: {item}") from exc
    return tokens


__all__ = [
    "BeatGrid",
    "LyricDocument",
    "LineSegment",
    "TempoEvent",
    "WordToken",
    "coerce_word_tokens",
]
