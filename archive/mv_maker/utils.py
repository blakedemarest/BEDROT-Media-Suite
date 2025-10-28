"""Utility functions for MV Maker."""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import re

# Import environment loader for proper configuration
try:
    from ..core.env_loader import get_env_var
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    def get_env_var(key, default=None):
        return os.environ.get(key, default)

def safe_print(*args, **kwargs):
    """Print with proper encoding handling."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert args to strings with safe encoding
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('utf-8', errors='replace').decode('utf-8'))
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)

def get_ffmpeg_path():
    """Get FFmpeg executable path using environment configuration."""
    # Check environment variable first
    env_path = get_env_var('SLIDESHOW_FFMPEG_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Check if ffmpeg is in PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    
    # Platform-specific fallback paths from environment or defaults
    if sys.platform == "win32":
        # Get configurable paths from environment or use minimal defaults
        custom_paths = get_env_var('SLIDESHOW_FFMPEG_SEARCH_PATHS', '').split(';')
        common_paths = [path.strip() for path in custom_paths if path.strip()]
        
        # Add minimal fallback paths if no custom paths provided
        if not common_paths:
            common_paths = [
                "ffmpeg.exe",  # Try current directory
                os.path.expandvars(r"%PROGRAMFILES%\ffmpeg\bin\ffmpeg.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\ffmpeg\bin\ffmpeg.exe"),
            ]
        
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
    
    return "ffmpeg"  # Fallback to PATH

def get_ffprobe_path():
    """Get FFprobe executable path."""
    # Check if ffprobe is in PATH
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        return ffprobe_path
    
    # Try to find it relative to ffmpeg
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path and ffmpeg_path != "ffmpeg":
        ffprobe_path = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
        if sys.platform == "win32":
            ffprobe_path += ".exe"
        if os.path.exists(ffprobe_path):
            return ffprobe_path
    
    return "ffprobe"  # Fallback to PATH

def run_ffmpeg_command(command, shell=False):
    """Run an FFmpeg command with proper error handling."""
    try:
        # Windows-specific handling
        if sys.platform == "win32" and not shell:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, command, result.stdout, result.stderr
            )
        
        return result.stdout
    
    except subprocess.CalledProcessError as e:
        safe_print(f"FFmpeg command failed: {e.stderr}")
        raise
    except Exception as e:
        safe_print(f"Error running FFmpeg: {e}")
        raise

def get_video_info(video_path):
    """Get video information using ffprobe."""
    ffprobe_path = get_ffprobe_path()
    
    command = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,r_frame_rate",
        "-of", "json",
        video_path
    ]
    
    try:
        import json
        output = run_ffmpeg_command(command)
        data = json.loads(output)
        
        if 'streams' in data and data['streams']:
            stream = data['streams'][0]
            
            # Parse frame rate
            fps = 30.0  # Default
            if 'r_frame_rate' in stream:
                fps_parts = stream['r_frame_rate'].split('/')
                if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                    fps = float(fps_parts[0]) / float(fps_parts[1])
            
            return {
                'width': stream.get('width', 1920),
                'height': stream.get('height', 1080),
                'duration': float(stream.get('duration', 0)),
                'fps': fps
            }
    except Exception as e:
        safe_print(f"Error getting video info: {e}")
    
    # Return defaults
    return {
        'width': 1920,
        'height': 1080,
        'duration': 0,
        'fps': 30.0
    }

def get_audio_duration(audio_path):
    """Get audio duration using ffprobe."""
    ffprobe_path = get_ffprobe_path()
    
    command = [
        ffprobe_path,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    
    try:
        output = run_ffmpeg_command(command)
        return float(output.strip())
    except Exception as e:
        safe_print(f"Error getting audio duration: {e}")
        return 0

def create_temp_directory():
    """Create a temporary directory for processing."""
    temp_dir = tempfile.mkdtemp(prefix="caption_generator_")
    return temp_dir

def cleanup_temp_directory(temp_dir):
    """Clean up temporary directory."""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        safe_print(f"Error cleaning up temp directory: {e}")

def format_timestamp(seconds, fmt='srt'):
    """Format seconds to timestamp string."""
    original_seconds = seconds  # Store the original value
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = seconds % 60
    
    if fmt == 'srt':
        # SRT format: HH:MM:SS,mmm
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:06.3f}".replace('.', ',')
    elif fmt == 'vtt':
        # WebVTT format: HH:MM:SS.mmm
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:06.3f}"
    elif fmt == 'simple':
        # Simple format: [MM:SS] (with brackets)
        total_minutes = int(original_seconds // 60)
        simple_seconds = int(original_seconds % 60)
        return f"[{total_minutes}:{simple_seconds:02d}]"
    else:
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:06.3f}"

def parse_timestamp(timestamp_str):
    """Parse timestamp string to seconds."""
    # Handle both SRT (comma) and VTT (period) formats
    timestamp_str = timestamp_str.replace(',', '.')
    
    parts = timestamp_str.split(':')
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    return 0

def sanitize_filename(filename):
    """Sanitize filename for safe file system usage."""
    # Remove invalid characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename

def split_text_for_captions(text, max_length=42):
    """Split text into caption-friendly lines."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        
        # If adding this word exceeds max length, start new line
        if current_length + word_length + len(current_line) > max_length and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            current_line.append(word)
            current_length += word_length
    
    # Add remaining words
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def estimate_processing_time(duration, model_size='base'):
    """Estimate processing time based on audio duration and model size."""
    # Rough estimates based on CPU processing
    # These are very approximate and depend heavily on hardware
    multipliers = {
        'tiny': 0.5,
        'base': 1.0,
        'small': 2.0,
        'medium': 5.0,
        'large': 10.0
    }
    
    multiplier = multipliers.get(model_size, 1.0)
    
    # Base estimate: 1x realtime for 'base' model on average CPU
    estimated_seconds = duration * multiplier
    
    return estimated_seconds

def get_available_languages():
    """Get list of available languages for Whisper."""
    # This is a subset of languages Whisper supports well
    return {
        'auto': 'Auto-detect',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'tr': 'Turkish',
        'pl': 'Polish',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish'
    }

def check_cuda_available():
    """Check if CUDA is available for GPU acceleration."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def get_optimal_device():
    """Get optimal device for processing."""
    if check_cuda_available():
        return 'cuda'
    return 'cpu'