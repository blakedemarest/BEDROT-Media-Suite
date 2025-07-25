"""
Bedrot Media Suite - Source Modules

This package contains all the modular components of the Bedrot Media Suite,
including media processing, tracking, and management tools.

Modules:
- core: Centralized configuration and utilities
- media_download_app: YouTube/media downloader with format conversion
- reel_tracker: CSV-based content tracking and management
- snippet_remixer: Video remixing and snippet generation
- random_slideshow: Automated slideshow creation
- video_caption_generator: AI-powered caption generation
- release_calendar: Music release scheduling and management
"""

# Core utilities
def get_config_manager():
    """Get centralized configuration manager."""
    from .core import get_config_manager
    return get_config_manager()

def get_path_resolver():
    """Get path resolution utilities."""
    from .core.path_utils import get_path_resolver
    return get_path_resolver()

# Media Download App
def get_media_download_app():
    """Get media download application (Tkinter-based)."""
    from .media_download_app import MediaDownloadApp
    return MediaDownloadApp

# Reel Tracker Module
def get_reel_tracker():
    """Get reel tracker main application (PyQt5)."""
    from .reel_tracker import get_main_app
    return get_main_app()

def get_reel_tracker_config():
    """Get reel tracker configuration manager."""
    from .reel_tracker import ConfigManager
    return ConfigManager

# Snippet Remixer Module
def get_snippet_remixer():
    """Get snippet remixer main application (Tkinter)."""
    from .snippet_remixer import get_main_app
    return get_main_app()

def get_video_processor():
    """Get snippet remixer video processor."""
    from .snippet_remixer import VideoProcessor
    return VideoProcessor

# Random Slideshow Module
def get_random_slideshow():
    """Get random slideshow main window (PyQt5)."""
    from .random_slideshow import get_main_window
    return get_main_window()

def get_slideshow_generator():
    """Get slideshow generator class."""
    from .random_slideshow import get_slideshow_generator
    return get_slideshow_generator()

# Video Caption Generator Module
def get_video_caption_generator():
    """Get video caption generator main app (PyQt5)."""
    from .video_caption_generator import get_main_app
    return get_main_app()

def get_transcriber():
    """Get caption transcriber (ElevenLabs/Whisper)."""
    from .video_caption_generator import get_transcriber
    return get_transcriber()

def get_caption_exporter():
    """Get caption exporter for multiple formats."""
    from .video_caption_generator import get_caption_exporter
    return get_caption_exporter()

def get_live_preview_widget():
    """Get live preview widget for captions."""
    from .video_caption_generator import get_live_preview_widget
    return get_live_preview_widget()

# Release Calendar Module (NEW)
def get_release_calendar():
    """Get release calendar main application (PyQt6)."""
    from .release_calendar import get_main_app
    return get_main_app()

def get_release_calendar_config():
    """Get release calendar configuration manager."""
    from .release_calendar import ConfigManager
    return ConfigManager

def get_bedrot_release_calendar():
    """Get multi-artist release calendar logic."""
    from .release_calendar import BedrotReleaseCalendar
    return BedrotReleaseCalendar

def get_calendar_data_manager():
    """Get calendar data persistence manager."""
    from .release_calendar import CalendarDataManager
    return CalendarDataManager

def get_visual_calendar_widget():
    """Get visual calendar widget (PyQt6)."""
    from .release_calendar import get_visual_calendar
    return get_visual_calendar()

def get_checklist_dialog():
    """Get release checklist dialog (PyQt6)."""
    from .release_calendar import get_checklist_dialog
    return get_checklist_dialog()

__all__ = [
    # Core
    'get_config_manager',
    'get_path_resolver',
    
    # Media Download
    'get_media_download_app',
    
    # Reel Tracker
    'get_reel_tracker',
    'get_reel_tracker_config',
    
    # Snippet Remixer
    'get_snippet_remixer',
    'get_video_processor',
    
    # Random Slideshow
    'get_random_slideshow',
    'get_slideshow_generator',
    
    # Video Caption Generator
    'get_video_caption_generator',
    'get_transcriber',
    'get_caption_exporter',
    'get_live_preview_widget',
    
    # Release Calendar
    'get_release_calendar',
    'get_release_calendar_config',
    'get_bedrot_release_calendar',
    'get_calendar_data_manager',
    'get_visual_calendar_widget',
    'get_checklist_dialog'
]