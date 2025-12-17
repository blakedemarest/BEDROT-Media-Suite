# -*- coding: utf-8 -*-
"""
Caption Generator Module

Creates lyric/caption videos from SRT subtitle files and audio.
Supports drag-and-drop, bulk processing, and auto-transcription.
"""

__version__ = "2.0.0"
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

def get_pairing_history():
    """Get the pairing history class."""
    from .pairing_history import PairingHistory
    return PairingHistory

def get_batch_worker():
    """Get the batch caption worker class."""
    from .batch_worker import BatchCaptionWorker
    return BatchCaptionWorker

def get_drop_zone():
    """Get the drop zone widget class."""
    from .drop_zone import DropZoneWidget
    return DropZoneWidget

def get_settings_dialog():
    """Get the settings dialog class."""
    from .settings_dialog import SettingsDialog
    return SettingsDialog

__all__ = [
    "get_main_app",
    "get_config_manager",
    "get_video_generator",
    "get_pairing_history",
    "get_batch_worker",
    "get_drop_zone",
    "get_settings_dialog",
]
