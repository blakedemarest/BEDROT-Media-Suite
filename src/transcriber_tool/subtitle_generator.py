# -*- coding: utf-8 -*-
"""
Subtitle generation utilities for SRT format.

Converts ElevenLabs word-level timestamps to SRT subtitle format.
"""

import pysrt
from typing import List, Dict, Any


def words_to_segments(words: List[Any],
                      max_words: int = 8,
                      max_duration_s: float = 5.0) -> List[Dict]:
    """
    Group words into subtitle segments.

    Args:
        words: List of word objects with 'text', 'start', 'end' attributes
        max_words: Maximum words per segment
        max_duration_s: Maximum segment duration in seconds

    Returns:
        List of segment dicts with 'text', 'start', 'end'
    """
    segments = []
    current_segment = {"words": [], "start": None, "end": None}

    for word in words:
        # Handle both dict and object access patterns
        if hasattr(word, 'type'):
            word_type = word.type
            word_text = word.text
            word_start = word.start
            word_end = word.end
        else:
            word_type = word.get("type")
            word_text = word.get("text", "")
            word_start = word.get("start")
            word_end = word.get("end")

        # Skip non-word items (spacing, audio events)
        if word_type not in (None, "word"):
            continue

        if word_start is None or word_end is None:
            continue

        if current_segment["start"] is None:
            current_segment["start"] = word_start

        current_segment["words"].append(word_text)
        current_segment["end"] = word_end

        # Check segment limits
        segment_duration = current_segment["end"] - current_segment["start"]
        word_count = len(current_segment["words"])

        if word_count >= max_words or segment_duration >= max_duration_s:
            segments.append({
                "text": " ".join(current_segment["words"]),
                "start": current_segment["start"],
                "end": current_segment["end"]
            })
            current_segment = {"words": [], "start": None, "end": None}

    # Append remaining words
    if current_segment["words"]:
        segments.append({
            "text": " ".join(current_segment["words"]),
            "start": current_segment["start"],
            "end": current_segment["end"]
        })

    return segments


def seconds_to_srt_time(seconds: float) -> pysrt.SubRipTime:
    """Convert seconds to pysrt SubRipTime object."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=secs, milliseconds=millis)


def generate_srt(segments: List[Dict], output_path: str) -> bool:
    """
    Generate SRT file from segments.

    Args:
        segments: List of dicts with 'text', 'start', 'end'
        output_path: Output .srt file path

    Returns:
        True if successful, False otherwise
    """
    if not segments:
        return False

    try:
        srt_file = pysrt.SubRipFile()

        for idx, segment in enumerate(segments, start=1):
            item = pysrt.SubRipItem(
                index=idx,
                start=seconds_to_srt_time(segment["start"]),
                end=seconds_to_srt_time(segment["end"]),
                text=segment["text"]
            )
            srt_file.append(item)

        srt_file.save(output_path, encoding='utf-8')
        return True
    except Exception:
        return False
