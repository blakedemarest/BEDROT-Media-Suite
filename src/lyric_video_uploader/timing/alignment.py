# -*- coding: utf-8 -*-
"""
Timing alignment and subtitle generation utilities.

Transforms word/line timing data into SRT, ASS, and JSON outputs and provides
helpers for snapping timings to beat grids.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    import pysubs2
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    pysubs2 = None  # type: ignore[assignment]

from .. import ProjectContext, get_package_logger
from ..schemas import BeatGrid, LineSegment, LyricDocument, WordToken

LOGGER = get_package_logger("lyric_video.timing")


def build_document(
    audio_path: Path,
    words: Sequence[WordToken],
    lines: Sequence[LineSegment],
    beat_grid: BeatGrid | None = None,
) -> LyricDocument:
    """Construct a LyricDocument instance with validation."""
    doc = LyricDocument(audio_path=audio_path, words=words, lines=lines, beat_grid=beat_grid)
    doc.ensure_consistency()
    LOGGER.info("Lyric document with %d words and %d lines prepared.", len(words), len(lines))
    return doc


def write_outputs(doc: LyricDocument, context: ProjectContext) -> dict[str, Path]:
    """Persist timing outputs (SRT/ASS/JSON) and return their paths."""
    context.ensure_structure()
    timing_dir = context.timing_dir
    timing_dir.mkdir(parents=True, exist_ok=True)

    words_path = timing_dir / "words.srt"
    lines_path = timing_dir / "lines.srt"
    ass_path = timing_dir / "lyrics.ass"
    json_path = timing_dir / "lyrics.json"

    _write_srt_words(doc.words, words_path)
    _write_srt_lines(doc.lines, lines_path)
    _write_ass(doc.lines, ass_path)

    payload = doc.to_dict()
    if doc.beat_grid is not None:
        payload["beat_metadata"] = _compute_snap_metadata(doc.words, doc.beat_grid)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    LOGGER.info("Timing outputs written to %s", timing_dir)
    return {
        "words_srt": words_path,
        "lines_srt": lines_path,
        "lyrics_ass": ass_path,
        "lyrics_json": json_path,
    }


def snap_words_to_beats(words: Sequence[WordToken], beat_grid: BeatGrid) -> List[WordToken]:
    """
    Return a new list of WordToken objects with start/end snapped to nearest beats.

    The original list is left untouched so raw timestamps remain available.
    """
    beat_grid.require_events()
    if not words:
        return []

    max_end = max(token.end for token in words)
    beats = beat_grid.generate_beats(until=max_end + 5.0)
    if not beats:
        return list(words)

    snapped: List[WordToken] = []
    for token in words:
        start_index = _find_previous_index(beats, token.start)
        end_index = _find_next_index(beats, token.end)

        start_time = beats[start_index] if start_index is not None else token.start
        end_time = beats[end_index] if end_index is not None else token.end
        if end_time <= start_time:
            end_time = start_time + max(token.duration(), 0.05)

        snapped.append(
            WordToken(
                text=token.text,
                start=round(start_time, 6),
                end=round(end_time, 6),
                confidence=token.confidence,
            )
        )

    LOGGER.debug("Snapped %d words to beats.", len(snapped))
    return snapped


def _write_srt_words(words: Sequence[WordToken], destination: Path) -> None:
    if pysubs2 is None:
        raise RuntimeError("pysubs2 is required to generate SRT files.")
    subs = pysubs2.SSAFile()
    for token in words:
        start = int(token.start * 1000)
        end = max(start + 30, int(token.end * 1000))
        subs.events.append(pysubs2.SSAEvent(start=start, end=end, text=token.text))
    subs.save(str(destination), format_="srt")


def _write_srt_lines(lines: Sequence[LineSegment], destination: Path) -> None:
    if pysubs2 is None:
        raise RuntimeError("pysubs2 is required to generate SRT files.")
    subs = pysubs2.SSAFile()
    for line in lines:
        start = int(line.start * 1000)
        end = max(start + 100, int(line.end * 1000))
        subs.events.append(pysubs2.SSAEvent(start=start, end=end, text=line.text))
    subs.save(str(destination), format_="srt")


def _write_ass(lines: Sequence[LineSegment], destination: Path) -> None:
    if pysubs2 is None:
        raise RuntimeError("pysubs2 is required to generate ASS files.")
    subs = pysubs2.SSAFile()
    default_style = subs.styles.get("Default")
    if default_style:
        default_style.fontname = "Arial"
        default_style.fontsize = 48
        default_style.primarycolor = pysubs2.Color(255, 255, 255)
        default_style.outline = 2
        default_style.shadow = 1

    for line in lines:
        text = line.text.replace("{", r"\{").replace("}", r"\}")
        start = int(line.start * 1000)
        end = max(start + 100, int(line.end * 1000))
        subs.events.append(pysubs2.SSAEvent(start=start, end=end, text=text))

    subs.save(str(destination), format_="ass")


def _compute_snap_metadata(words: Sequence[WordToken], beat_grid: BeatGrid) -> List[dict]:
    """Return metadata describing the nearest beat for each word."""
    if not words:
        return []
    max_end = max(token.end for token in words)
    beats = beat_grid.generate_beats(until=max_end + 5.0)
    if not beats:
        return []

    metadata: List[dict] = []
    for idx, token in enumerate(words):
        nearest_idx = _find_nearest_index(beats, token.start)
        metadata.append(
            {
                "word_index": idx,
                "word_start": token.start,
                "nearest_beat_index": nearest_idx,
                "nearest_beat_time": beats[nearest_idx] if nearest_idx is not None else None,
            }
        )
    return metadata


def _find_previous_index(beats: Sequence[float], timestamp: float) -> int | None:
    for index in range(len(beats) - 1, -1, -1):
        if beats[index] <= timestamp:
            return index
    return None


def _find_next_index(beats: Sequence[float], timestamp: float) -> int | None:
    for index, beat in enumerate(beats):
        if beat >= timestamp:
            return index
    return None


def _find_nearest_index(beats: Sequence[float], timestamp: float) -> int | None:
    if not beats:
        return None
    nearest_index = min(range(len(beats)), key=lambda idx: abs(beats[idx] - timestamp))
    return nearest_index


__all__ = ["build_document", "write_outputs", "snap_words_to_beats"]
