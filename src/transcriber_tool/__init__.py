# -*- coding: utf-8 -*-
"""
Transcriber Tool - Audio/Video Transcription Module

A drag-and-drop transcription tool using ElevenLabs Speech-to-Text API.
Supports MP3, MP4, WAV, M4A, and FLAC formats with automatic conversion.
"""

from .config_manager import ConfigManager, get_config

# Lazy imports to avoid PyQt5 dependency issues at import time
def get_main_app():
    """Lazy import for TranscriberApp."""
    from .main_app import TranscriberApp, main
    return TranscriberApp, main


def get_worker():
    """Lazy import for Worker thread."""
    from .main_app import Worker
    return Worker


__version__ = "1.0.0"
__all__ = [
    "ConfigManager",
    "get_config",
    "get_main_app",
    "get_worker",
]
