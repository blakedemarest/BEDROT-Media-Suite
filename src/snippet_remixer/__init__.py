# -*- coding: utf-8 -*-
"""
Snippet Remixer Package - A modular Video Snippet Remixer application.

This package provides functionality for:
- Video snippet cutting and remixing
- Aspect ratio adjustment
- BPM-based or duration-based remix generation
- Background processing with progress tracking
- Configuration management
"""

# Import core classes
from .config_manager import ConfigManager
from .video_processor import VideoProcessor
from .processing_worker import ProcessingWorker
from .utils import safe_print, parse_aspect_ratio, generate_unique_suffix

# Lazy imports for optional components to avoid tkinter dependency issues
def get_main_app():
    """Lazy import for VideoRemixerApp to avoid tkinter dependency issues."""
    from .main_app import VideoRemixerApp, main
    return VideoRemixerApp, main

def get_gui_main():
    """Lazy import for main GUI function."""
    from .main_app import main
    return main

__version__ = "1.0.0"
__author__ = "Bedrot Productions"

__all__ = [
    "ConfigManager",
    "VideoProcessor", 
    "ProcessingWorker",
    "safe_print",
    "parse_aspect_ratio",
    "generate_unique_suffix",
    "get_main_app",
    "get_gui_main"
]