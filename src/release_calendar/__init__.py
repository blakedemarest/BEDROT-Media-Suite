"""
Release Calendar Module - Music Release Management System

This module provides a comprehensive release calendar for managing music releases
across multiple artists with deliverable tracking, visual calendar interface,
and export capabilities.

Key Features:
- Multi-artist release scheduling with conflict detection
- Visual calendar with drag-and-drop rescheduling
- Comprehensive checklist system (9+ deliverables per release)
- Waterfall release strategy support
- Export to Excel and iCal formats
- PyQt6-based GUI with interactive widgets
"""

__version__ = "1.0.0"
__author__ = "Bedrot Productions"

# Core imports that don't require PyQt6
from .config_manager import ConfigManager
from .calendar_logic import ReleaseCalendar, BedrotReleaseCalendar
from .data_manager import CalendarDataManager

# Lazy imports for PyQt6 components
def get_main_app():
    """Lazy import for MainApplication to avoid PyQt6 dependency issues."""
    from .main_app import CalendarApp
    return CalendarApp

def get_visual_calendar():
    """Lazy import for VisualCalendarWidget."""
    from .visual_calendar import VisualCalendarWidget
    return VisualCalendarWidget

def get_checklist_dialog():
    """Lazy import for ReleaseChecklistDialog."""
    from .checklist_dialog import ReleaseChecklistDialog
    return ReleaseChecklistDialog

__all__ = [
    "ConfigManager",
    "ReleaseCalendar",
    "BedrotReleaseCalendar",
    "CalendarDataManager",
    "get_main_app",
    "get_visual_calendar",
    "get_checklist_dialog"
]