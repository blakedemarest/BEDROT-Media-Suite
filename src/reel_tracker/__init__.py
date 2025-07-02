# -*- coding: utf-8 -*-
"""
Reel Tracker Module - A modular PyQt5 application for tracking reels with CSV import/export.

This module provides:
- Configuration management
- Media randomization functionality
- Reel entry and editing dialogs
- Main application interface
"""

from .main_app import ReelTrackerApp
from .config_manager import ConfigManager
from .media_randomizer import MediaRandomizerDialog
from .reel_dialog import ReelEntryDialog
from .custom_item_manager import CustomItemManagerDialog

__version__ = "3.1.0"
__author__ = "Bedrot Productions"

__all__ = [
    'ReelTrackerApp',
    'ConfigManager', 
    'MediaRandomizerDialog',
    'ReelEntryDialog',
    'CustomItemManagerDialog'
]