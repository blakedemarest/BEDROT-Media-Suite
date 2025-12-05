# -*- coding: utf-8 -*-
"""
Caption Generator Module

Creates lyric/caption videos from SRT/VTT subtitle files and audio.
"""

__version__ = "1.0.0"
__author__ = "BEDROT Productions"

# Lazy imports for faster startup
def get_main_app():
    """Get the main application class."""
    from .main_app import CaptionGeneratorApp
    return CaptionGeneratorApp

def get_config_manager():
    """Get the config manager class."""
    from .config_manager import ConfigManager
    return ConfigManager

def get_video_generator():
    """Get the video generator module."""
    from . import video_generator
    return video_generator

__all__ = [
    "get_main_app",
    "get_config_manager",
    "get_video_generator",
]
