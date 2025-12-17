# -*- coding: utf-8 -*-
"""
Utility functions for the Video Snippet Remixer.

Provides common utility functions including:
- Safe printing for thread-safe output
- Aspect ratio parsing
- Unique filename generation
"""

import os
import random
import string
import re
from datetime import datetime


def safe_print(message):
    """Thread-safe print function with Unicode encoding handling."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fall back to ASCII-safe version if Unicode fails
        try:
            # Try encoding to ASCII, replacing problematic characters
            ascii_message = message.encode('ascii', 'replace').decode('ascii')
            print(ascii_message)
        except Exception:
            # Last resort: print without special characters
            safe_message = ''.join(c if ord(c) < 128 else '?' for c in str(message))
            print(safe_message)


def parse_aspect_ratio(ratio_str):
    """
    Parse aspect ratio string to numeric value. Supports both new HD format and legacy format.
    
    Args:
        ratio_str (str): Aspect ratio string like "1920x1080 (16:9 Landscape)" or "16:9" or "Original"
        
    Returns:
        float or None: Numeric aspect ratio value or None for "Original"
    """
    if ratio_str == "Original":
        return None
    
    # Try to extract from new HD format (e.g., "1920x1080 (16:9 Landscape)")
    hd_match = re.match(r'(\d+)x(\d+)', ratio_str)
    if hd_match:
        w, h = int(hd_match.group(1)), int(hd_match.group(2))
        if h == 0:
            return None
        return w / h
    
    # Fall back to legacy format (e.g., "16:9")
    try:
        w_str, h_str = ratio_str.split(':')
        w, h = float(w_str), float(h_str)
        if h == 0:
            return None
        return w / h
    except (ValueError, TypeError):
        safe_print(f"Warning: Could not parse aspect ratio string: {ratio_str}")
        return None


def generate_unique_suffix(length=8):
    """
    Generates a unique suffix string using datetime and random characters.
    
    Args:
        length (int): Length of the random part
        
    Returns:
        str: Unique suffix in format _YYYYMMDD_HHMMSS_randomstring
    """
    now = datetime.now()
    # Format: YYYYMMDD_HHMMSS_randomstring
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"_{timestamp}_{random_part}"


def validate_file_path(file_path):
    """
    Validate that a file path exists and is accessible.
    
    Args:
        file_path (str): Path to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        return os.path.exists(file_path) and os.path.isfile(file_path)
    except (TypeError, OSError):
        return False


def validate_directory_path(dir_path):
    """
    Validate that a directory path exists and is accessible.
    
    Args:
        dir_path (str): Directory path to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        return os.path.exists(dir_path) and os.path.isdir(dir_path)
    except (TypeError, OSError):
        return False


def safe_filename(filename):
    """
    Make a filename safe for the filesystem.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Safe filename with invalid characters replaced
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def parse_time_to_seconds(time_str):
    """
    Parse time string to seconds.
    
    Args:
        time_str (str): Time string in format HH:MM:SS, MM:SS, or seconds
        
    Returns:
        float or None: Time in seconds or None if invalid
    """
    if not time_str:
        return None
    
    time_str = time_str.strip()
    
    # Try to parse as direct seconds first
    try:
        return float(time_str)
    except ValueError:
        pass
    
    # Try to parse as time format
    parts = re.split(r'[: ]+', time_str)  # Allow space as separator too
    try:
        if len(parts) == 3:  # HH:MM:SS.ms
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:  # MM:SS.ms
            m, s = map(float, parts)
            return m * 60 + s
        elif len(parts) == 1 and ':' not in time_str:  # Just seconds
            return float(parts[0])
        else:
            return None
    except (ValueError, TypeError):
        return None