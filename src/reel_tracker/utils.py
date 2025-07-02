# -*- coding: utf-8 -*-
"""
Utility functions for the Reel Tracker application.
"""

def safe_print(text):
    """Safe print function that handles Unicode encoding issues on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe output
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)