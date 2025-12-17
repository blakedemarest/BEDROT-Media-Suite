# -*- coding: utf-8 -*-
"""
Video Generator for Caption Generator.

Handles ffmpeg video generation with burned-in subtitles.
"""

import os
import subprocess
import re
import tempfile
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


def calculate_safe_area_params(resolution: str, font_size: int, safe_area_enabled: bool) -> dict:
    """
    Calculate safe area margins and adjusted font size.

    For portrait videos (height > width), applies larger margins and reduces
    font size to prevent text overflow.

    Args:
        resolution: Video resolution string (e.g., "1080x1920")
        font_size: Original font size
        safe_area_enabled: Whether safe area mode is on

    Returns:
        Dict with keys: margin_l, margin_r, margin_v, adjusted_font_size
    """
    if not safe_area_enabled:
        return {
            "margin_l": 0,
            "margin_r": 0,
            "margin_v": 0,
            "adjusted_font_size": font_size
        }

    # Parse resolution
    width, height = map(int, resolution.split('x'))
    is_portrait = height > width

    # Calculate margins as percentage of dimensions
    # Portrait: 8% horizontal margin (each side), 5% vertical
    # Landscape: 5% horizontal margin (each side), 3% vertical
    if is_portrait:
        margin_h_pct = 0.08
        margin_v_pct = 0.05
        # Reduce font size by 25% for portrait to prevent overflow
        font_scale = 0.75
    else:
        margin_h_pct = 0.05
        margin_v_pct = 0.03
        font_scale = 1.0

    margin_l = int(width * margin_h_pct)
    margin_r = int(width * margin_h_pct)
    margin_v = int(height * margin_v_pct)
    adjusted_font_size = int(font_size * font_scale)

    return {
        "margin_l": margin_l,
        "margin_r": margin_r,
        "margin_v": margin_v,
        "adjusted_font_size": adjusted_font_size
    }


def transform_srt_text(srt_path: str, all_caps: bool, ignore_grammar: bool) -> Optional[str]:
    """
    Create a temporary SRT file with text transformations applied.

    This function reads the original SRT file, applies the requested transformations
    (uppercase, remove punctuation), and writes to a temporary file. The original
    SRT file is NOT modified.

    Args:
        srt_path: Path to the original SRT file
        all_caps: If True, convert all text to uppercase
        ignore_grammar: If True, remove punctuation characters

    Returns:
        Path to the temporary SRT file with transformations applied,
        or None if no transformations are needed or an error occurs
    """
    if not all_caps and not ignore_grammar:
        return None

    if not os.path.exists(srt_path):
        return None

    try:
        # Read the original SRT file
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Apply transformations
        lines = content.split('\n')
        transformed_lines = []

        for line in lines:
            # Check if this is a timestamp line (contains --> )
            if '-->' in line:
                # Don't transform timestamp lines
                transformed_lines.append(line)
            elif line.strip().isdigit():
                # Don't transform sequence numbers
                transformed_lines.append(line)
            elif line.strip() == '':
                # Preserve empty lines
                transformed_lines.append(line)
            else:
                # This is subtitle text - apply transformations
                text = line

                if ignore_grammar:
                    # Remove punctuation characters
                    # Pattern: period, comma, hyphen, exclamation, question, semicolon, colon,
                    # apostrophe, quotation marks, parentheses, brackets, braces
                    text = re.sub(r'[.,\-!?;:\'"()\[\]{}]', '', text)
                    # Clean up any double spaces that may result
                    text = re.sub(r'  +', ' ', text)
                    text = text.strip()

                if all_caps:
                    text = text.upper()

                transformed_lines.append(text)

        transformed_content = '\n'.join(transformed_lines)

        # Create a temporary file with the same extension
        ext = os.path.splitext(srt_path)[1]
        fd, temp_path = tempfile.mkstemp(suffix=ext, prefix='caption_transform_')

        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(transformed_content)

        return temp_path

    except Exception as e:
        print(f"[Caption Generator] Error transforming SRT: {e}")
        return None


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
        srt_path: Path to SRT subtitle file
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
    safe_area_mode = settings.get("safe_area_mode", False)

    # Calculate safe area parameters (margins and adjusted font size)
    safe_params = calculate_safe_area_params(resolution, font_size, safe_area_mode)
    effective_font_size = safe_params["adjusted_font_size"]

    # Convert colors
    font_color_bgr = hex_to_bgr(font_color)
    align_value = get_alignment_value(alignment)

    # Escape subtitle path
    escaped_srt = escape_path_for_subtitles(srt_path)

    # Build force_style string
    force_style = (
        f"FontName={font_name},"
        f"FontSize={effective_font_size},"
        f"PrimaryColour=&H{font_color_bgr},"
        f"Alignment={align_value},"
        f"BorderStyle=1,"
        f"Outline={outline_size},"
        f"Shadow=0"
    )

    # Add margins and word wrap if safe area mode is enabled
    if safe_area_mode:
        force_style += (
            f",MarginL={safe_params['margin_l']}"
            f",MarginR={safe_params['margin_r']}"
            f",MarginV={safe_params['margin_v']}"
            f",WrapStyle=2"
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
        srt_path: Path to SRT subtitle file
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

    # Apply text transformations if needed (creates temp file, preserves original)
    temp_srt_path = None
    all_caps = settings.get("all_caps", False)
    ignore_grammar = settings.get("ignore_grammar", False)
    effective_srt_path = srt_path

    if all_caps or ignore_grammar:
        temp_srt_path = transform_srt_text(srt_path, all_caps, ignore_grammar)
        if temp_srt_path:
            effective_srt_path = temp_srt_path
            if progress_callback:
                transforms = []
                if all_caps:
                    transforms.append("ALL CAPS")
                if ignore_grammar:
                    transforms.append("No Punctuation")
                progress_callback(f"[Caption Generator] Applying text transforms: {', '.join(transforms)}")

    try:
        # Build command using the effective SRT path (original or transformed)
        cmd = build_ffmpeg_command(effective_srt_path, audio_path, output_path, settings, transparent)

        if progress_callback:
            progress_callback(f"[Caption Generator] Running ffmpeg...")
            progress_callback(f"[Caption Generator] Command: {' '.join(cmd[:5])}...")

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
    finally:
        # Clean up temporary SRT file
        if temp_srt_path and os.path.exists(temp_srt_path):
            try:
                os.remove(temp_srt_path)
            except Exception:
                pass  # Ignore cleanup errors


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
