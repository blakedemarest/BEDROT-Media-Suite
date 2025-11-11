# -*- coding: utf-8 -*-
"""
MoviePy-based renderer (optional fallback when NVENC is unavailable).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:  # pragma: no cover - dependency optional in some environments.
    import moviepy.editor as mpy
except ModuleNotFoundError:  # pragma: no cover
    mpy = None  # type: ignore[assignment]

import pysubs2

from .. import get_package_logger
from .preset_manager import RenderPreset

LOGGER = get_package_logger("lyric_video.render.moviepy")


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) != 6:
        return 255, 255, 255
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b


@dataclass(slots=True)
class MoviePyRenderer:
    """Renderer that composes the video using MoviePy."""

    video_bitrate: str = "12M"
    audio_bitrate: str = "320k"

    def __post_init__(self) -> None:
        if mpy is None:
            raise RuntimeError(
                "MoviePy is not installed. Install moviepy extras to enable fallback rendering."
            )

    def render(
        self,
        *,
        lines_srt: Path,
        audio_path: Path,
        background_path: Path,
        output_path: Path,
        preset: RenderPreset,
    ) -> None:
        """Render a lyric video using MoviePy composites."""
        if mpy is None:  # pragma: no cover - guarded in __post_init__
            raise RuntimeError("MoviePy is unavailable.")

        for path in (lines_srt, audio_path, background_path):
            if not Path(path).exists():
                raise FileNotFoundError(f"Required render asset not found: {path}")

        LOGGER.info("MoviePy render started with preset=%s", preset.name)
        subtitle_data = pysubs2.load(str(lines_srt))
        subtitles = [
            (event.start / 1000.0, event.end / 1000.0, event.text)
            for event in subtitle_data
            if event.text
        ]

        audio_clip = mpy.AudioFileClip(str(audio_path))
        background_clip = self._load_background(background_path, audio_clip.duration)

        def make_text_clip(text: str) -> mpy.TextClip:
            r, g, b = _hex_to_rgb(preset.font_color)
            return mpy.TextClip(
                text,
                font=str(preset.font_path),
                fontsize=preset.font_size,
                color=f"rgb({r},{g},{b})",
                method="caption",
                align="center",
                size=(background_clip.w - 80, None),
            )

        subtitle_clip = mpy.SubtitlesClip(subtitles, make_text_clip)
        subtitle_clip = subtitle_clip.set_position(("center", "bottom"))

        composite = mpy.CompositeVideoClip([background_clip, subtitle_clip])
        composite = composite.set_audio(audio_clip)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        composite.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            bitrate=self.video_bitrate,
            audio_bitrate=self.audio_bitrate,
            fps=background_clip.fps or 30,
            threads=2,
        )

        composite.close()
        background_clip.close()
        audio_clip.close()
        LOGGER.info("MoviePy render completed: %s", output_path)

    def _load_background(self, background_path: Path, duration: float):
        if background_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
            clip = mpy.ImageClip(str(background_path)).set_duration(duration)
            clip = clip.set_fps(30)
            return clip

        clip = mpy.VideoFileClip(str(background_path))
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        else:
            clip = clip.subclip(0, duration)
        return clip


__all__ = ["MoviePyRenderer"]
