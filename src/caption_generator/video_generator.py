# -*- coding: utf-8 -*-
"""
Video Generator for Caption Generator.

Handles ffmpeg video generation with burned-in subtitles.
"""

import os
import subprocess
import re
from typing import Dict, Optional, Tuple


def hex_to_bgr(hex_color: str) -> str:
    """
    Convert hex color (#RRGGBB) to BGR format for ASS subtitles (&HBBGGRR).

    Args:
        hex_color: Color in #RRGGBB format (e.g., "#ffffff")

    Returns:
        Color in BGR format without prefix (e.g., "ffffff")
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
        return f"{b}{g}{r}"
    return "ffffff"  # Default to white


def get_alignment_value(alignment: str) -> int:
    """
    Convert alignment string to ASS alignment value.

    ASS alignment values (numpad style):
    7 8 9  (top)
    4 5 6  (middle)
    1 2 3  (bottom)

    Args:
        alignment: "top", "center", or "bottom"

    Returns:
        ASS alignment integer
    """
    alignments = {
        "top": 8,      # Top center
        "center": 10,  # Middle center (actually 5, but 10 works for some reason in force_style)
        "middle": 10,
        "bottom": 2    # Bottom center
    }
    return alignments.get(alignment.lower(), 10)


def escape_path_for_subtitles(path: str) -> str:
    """
    Escape a file path for use in ffmpeg subtitles filter.

    Windows paths need special escaping for the subtitles filter.

    Args:
        path: Original file path

    Returns:
        Escaped path suitable for subtitles filter
    """
    # For Windows, we need to escape colons and backslashes
    # The subtitles filter uses libass which has its own escaping rules
    escaped = path.replace('\\', '/')
    escaped = escaped.replace(':', '\\:')
    return escaped


def build_ffmpeg_command(
    srt_path: str,
    audio_path: str,
    output_path: str,
    settings: Dict,
    transparent: bool = False
) -> list:
    """
    Build the ffmpeg command for generating a caption video.

    Args:
        srt_path: Path to SRT/VTT subtitle file
        audio_path: Path to audio file (WAV, MP3, FLAC, etc.)
        output_path: Path for output video file (MP4 or WebM)
        settings: Dictionary with style settings
        transparent: If True, creates WebM with transparent background

    Returns:
        List of command arguments for subprocess
    """
    # Extract settings with defaults
    font_name = settings.get("font_name", "Arial Narrow")
    font_size = settings.get("font_size", 56)
    font_color = settings.get("font_color", "#ffffff")
    bg_color = settings.get("background_color", "#000000").lstrip('#')
    resolution = settings.get("resolution", "1920x1080")
    fps = settings.get("fps", 30)
    alignment = settings.get("alignment", "center")
    outline_size = settings.get("outline_size", 2)

    # Convert colors
    font_color_bgr = hex_to_bgr(font_color)
    align_value = get_alignment_value(alignment)

    # Escape subtitle path
    escaped_srt = escape_path_for_subtitles(srt_path)

    # Build force_style string
    force_style = (
        f"FontName={font_name},"
        f"FontSize={font_size},"
        f"PrimaryColour=&H{font_color_bgr},"
        f"Alignment={align_value},"
        f"BorderStyle=1,"
        f"Outline={outline_size},"
        f"Shadow=0"
    )

    # Build video filter based on transparency mode
    if transparent:
        # Transparent mode: use yuva420p format for alpha channel
        color_input = f"color=c=black@0.0:s={resolution}:r={fps},format=yuva420p"
        subtitle_filter = f"subtitles='{escaped_srt}':force_style='{force_style}'"

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", color_input,
            "-i", audio_path,
            "-vf", subtitle_filter,
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-crf", "20",
            "-b:v", "0",
            "-c:a", "libopus",
            "-b:a", "128k",
            "-shortest",
            "-y",
            output_path
        ]
    else:
        # Standard mode: solid background, H.264 MP4
        subtitle_filter = f"subtitles='{escaped_srt}':force_style='{force_style}'"

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={resolution}:r={fps}",
            "-i", audio_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-y",
            output_path
        ]

    return cmd


def generate_caption_video(
    srt_path: str,
    audio_path: str,
    output_path: str,
    settings: Dict,
    progress_callback=None,
    transparent: bool = False
) -> Tuple[bool, str]:
    """
    Generate a caption video using ffmpeg.

    Args:
        srt_path: Path to SRT/VTT subtitle file
        audio_path: Path to audio file
        output_path: Path for output video file (MP4 or WebM)
        settings: Dictionary with style settings
        progress_callback: Optional callback function for progress updates
        transparent: If True, creates WebM with transparent background

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validate inputs
    if not os.path.exists(srt_path):
        return False, f"Subtitle file not found: {srt_path}"

    if not os.path.exists(audio_path):
        return False, f"Audio file not found: {audio_path}"

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Build command
    cmd = build_ffmpeg_command(srt_path, audio_path, output_path, settings, transparent)

    if progress_callback:
        progress_callback(f"[Caption Generator] Running ffmpeg...")
        progress_callback(f"[Caption Generator] Command: {' '.join(cmd[:5])}...")

    try:
        # Run ffmpeg with output capture
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        # Read stderr for progress (ffmpeg outputs to stderr)
        output_lines = []
        for line in process.stderr:
            output_lines.append(line.strip())

            # Parse progress from ffmpeg output
            if "frame=" in line and progress_callback:
                # Extract frame info
                match = re.search(r'frame=\s*(\d+)', line)
                if match:
                    frame = match.group(1)
                    progress_callback(f"[Caption Generator] Processing frame {frame}...")

        process.wait()

        if process.returncode == 0:
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                return True, f"Video created successfully: {os.path.basename(output_path)} ({file_size:.1f} MB)"
            else:
                return False, "ffmpeg completed but output file not found"
        else:
            # Get last few lines of error output
            error_msg = '\n'.join(output_lines[-10:]) if output_lines else "Unknown error"
            return False, f"ffmpeg failed with code {process.returncode}: {error_msg}"

    except FileNotFoundError:
        return False, "ffmpeg not found. Please ensure ffmpeg is installed and in PATH."
    except Exception as e:
        return False, f"Error running ffmpeg: {str(e)}"


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    Get the duration of an audio file using ffprobe.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds, or None if failed
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass

    return None
