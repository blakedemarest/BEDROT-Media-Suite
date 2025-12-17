# -*- coding: utf-8 -*-
"""
Random Slideshow Generator Module

A modular random slideshow generation application with PyQt5 GUI.
This module provides functionality for creating randomized video slideshows
from image folders with customizable aspect ratios and settings.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

from .config_manager import ConfigManager

# Import modules with dependencies only when needed
def get_image_processor():
    """Lazy import for ImageProcessor to avoid PIL dependency issues."""
    from image_processor import ImageProcessor
    return ImageProcessor

def get_slideshow_editor():
    """Lazy import for RandomSlideshowEditor to avoid PyQt5 dependency issues."""
    from main_app import RandomSlideshowEditor
    return RandomSlideshowEditor

def get_slideshow_worker():
    """Lazy import for RandomSlideshowWorker to avoid PyQt5 dependency issues."""
    from slideshow_worker import RandomSlideshowWorker
    return RandomSlideshowWorker

__version__ = "1.0.0"
__author__ = "Random Slideshow Generator"

__all__ = [
    "ConfigManager", 
    "get_image_processor",
    "get_slideshow_editor",
    "get_slideshow_worker"
]