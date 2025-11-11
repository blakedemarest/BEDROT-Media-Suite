# -*- coding: utf-8 -*-
"""
FFmpeg-based renderer for lyric videos.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .. import get_package_logger
from .preset_manager import RenderPreset

LOGGER = get_package_logger("lyric_video.render.ffmpeg")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def _ensure_ffmpeg() -> str:
    """Locate ffmpeg on PATH and ensure NVENC support is available."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not found in PATH. Install FFmpeg before rendering lyric videos.")

    try:
        probe = subprocess.run(
            [ffmpeg_path, "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Failed to inspect FFmpeg encoders.") from exc

    if "h264_nvenc" not in probe.stdout:
        raise RuntimeError(
            "FFmpeg is available but h264_nvenc encoder is missing. "
            "Install NVIDIA drivers and an FFmpeg build with NVENC support."
        )

    return ffmpeg_path


@dataclass(slots=True)
class FFmpegRenderer:
    """Render lyric videos using FFmpeg with NVENC acceleration."""

    video_bitrate: str = "25M"
    audio_bitrate: str = "320k"

    def __post_init__(self) -> None:
        self.ffmpeg_path = _ensure_ffmpeg()
        LOGGER.info("FFmpeg renderer initialized (bitrate=%s/%s)", self.video_bitrate, self.audio_bitrate)

    def render(
        self,
        *,
        ass_path: Path,
        audio_path: Path,
        background_path: Path,
        output_path: Path,
        preset: RenderPreset,
    ) -> None:
        """Render a lyric video using the provided assets."""
        LOGGER.debug("Rendering with preset: %s", preset.name)
        for path in (ass_path, audio_path, background_path):
            if not Path(path).exists():
                raise FileNotFoundError(f"Required render asset not found: {path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        ass_filter = f"ass={ass_path.as_posix()}"

        command = [self.ffmpeg_path, "-y"]
        background_path = background_path.resolve()
        if background_path.suffix.lower() in IMAGE_EXTENSIONS:
            command.extend(["-loop", "1", "-i", str(background_path)])
        else:
            command.extend(["-i", str(background_path)])

        command.extend(["-i", str(audio_path)])
        command.extend(
            [
                "-vf",
                ass_filter,
                "-c:v",
                "h264_nvenc",
                "-b:v",
                self.video_bitrate,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                self.audio_bitrate,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )

        LOGGER.info("Executing FFmpeg render: %s", " ".join(command))
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFmpeg render failed with exit code {exc.returncode}") from exc

        LOGGER.info("Render completed: %s", output_path)


__all__ = ["FFmpegRenderer"]
