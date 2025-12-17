"""
MV Maker Package

A sophisticated tool for extracting audio from videos and audio files, transcribing speech,
and generating time-synchronized caption files with advanced styling and real-time preview.

Features:
- Multi-format support: MP4, AVI, MOV, MKV, MP3, WAV, FLAC, etc.
- AI-powered transcription (ElevenLabs Scribe + Whisper fallback)
- Real-time caption preview with live styling updates
- Advanced positioning with X/Y coordinates and alignment
- Professional font support: Arial, Helvetica, Verdana, Roboto, Open Sans, Impact
- Color wheel interface for intuitive color selection
- Audio-to-video conversion for audio-only inputs
- Multiple aspect ratios and resolutions
- Burned-in caption export (MP4 with embedded captions)
"""

def get_main_app():
    """Get main application class with enhanced UI and real-time preview."""
    from .main_app import MVMaker
    return MVMaker

def get_transcriber():
    """Get transcriber instance (ElevenLabs or Whisper)."""
    from .transcriber import Transcriber
    return Transcriber

def get_audio_extractor():
    """Get audio extractor for video/audio file processing."""
    from .audio_extractor import AudioExtractor
    return AudioExtractor

def get_caption_generator():
    """Get caption generator for creating timed captions."""
    from .caption_generator import CaptionGenerator
    return CaptionGenerator

def get_caption_exporter():
    """Get caption exporter for SRT, VTT, and MP4 output."""
    from .caption_exporter import CaptionExporter
    return CaptionExporter

def get_video_processor():
    """Get video processor for MP4 generation with captions."""
    from .video_processor import VideoProcessor
    return VideoProcessor

def get_font_manager():
    """Get font manager for cross-platform font handling."""
    from .font_manager import get_font_manager
    return get_font_manager()

def get_live_preview_widget():
    """Get live preview widget class for real-time caption display."""
    from .live_preview_widget import LivePreviewWidget
    return LivePreviewWidget

def get_color_wheel_widget():
    """Get color wheel widget class for advanced color selection."""
    from .color_wheel_widget import ColorWheelWidget
    return ColorWheelWidget

def get_audio_to_video_generator():
    """Get audio-to-video generator for MP4 creation from audio files."""
    from .audio_to_video_generator import AudioToVideoGenerator
    return AudioToVideoGenerator

__all__ = [
    'get_main_app',
    'get_transcriber',
    'get_audio_extractor',
    'get_caption_generator',
    'get_caption_exporter',
    'get_video_processor',
    'get_font_manager',
    'get_live_preview_widget',
    'get_color_wheel_widget',
    'get_audio_to_video_generator'
]