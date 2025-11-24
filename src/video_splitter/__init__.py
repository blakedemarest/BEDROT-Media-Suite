"""
Video Splitter module package initialization.

This package provides a Tkinter-based GUI for slicing long-form videos
into evenly timed clips with optional jitter randomization.
"""

from .main import main  # re-export for convenience

__all__ = ["main"]
