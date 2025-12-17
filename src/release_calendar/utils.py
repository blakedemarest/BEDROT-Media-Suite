"""
Utility functions for the Release Calendar module.

Provides logging, safe printing, and other utility functions.
"""

import os
import sys
import json
from datetime import datetime
from typing import Any, Optional
from pathlib import Path


def safe_print(message: str) -> None:
    """Print a message safely, handling Unicode errors.
    
    Args:
        message: The message to print
    """
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback for terminals that can't handle Unicode
        print(message.encode('ascii', 'replace').decode('ascii'))


class SimpleLogger:
    """Simple logging utility for the release calendar module."""
    
    def __init__(self, module_name: str = "Release Calendar"):
        """Initialize the logger.
        
        Args:
            module_name: Name to prefix log messages with
        """
        self.module_name = module_name
        self.enabled = True
        
    def log(self, level: str, message: str) -> None:
        """Log a message with timestamp and level.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Message to log
        """
        if not self.enabled:
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{self.module_name}] {level}: {message}"
        safe_print(formatted_message)
        
    def info(self, message: str) -> None:
        """Log an info message."""
        self.log("INFO", message)
        
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.log("WARNING", message)
        
    def error(self, message: str) -> None:
        """Log an error message."""
        self.log("ERROR", message)
        
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.log("DEBUG", message)


# Global logger instance
logger = SimpleLogger()


def format_deliverable_name(deliverable_key: str) -> str:
    """Format a deliverable key into a human-readable name.
    
    Args:
        deliverable_key: The deliverable key (e.g., 'final_master')
        
    Returns:
        Formatted name (e.g., 'Final Master')
    """
    # Special cases
    special_cases = {
        'spotify_canvas': 'Spotify Canvas',
        'ad_creatives_5': 'Ad Creatives (5)',
        'ad_creatives_10': 'Ad Creatives (10)',
        'ad_creatives_20': 'Ad Creatives (20)',
        'reels_124': 'Reels (124)',
        'reels_248': 'Reels (248)',
        'reels_496': 'Reels (496)',
        'carousel_posts_25': 'Carousel Posts (25)',
        'carousel_posts_50': 'Carousel Posts (50)',
        'carousel_posts_100': 'Carousel Posts (100)',
        'music_videos_3': 'Music Videos (3)'
    }
    
    if deliverable_key in special_cases:
        return special_cases[deliverable_key]
    
    # General formatting
    return ' '.join(word.capitalize() for word in deliverable_key.split('_'))


def days_until(target_date: datetime) -> int:
    """Calculate days until a target date.
    
    Args:
        target_date: The target date
        
    Returns:
        Number of days (negative if in the past)
    """
    today = datetime.now().date()
    target = target_date.date() if hasattr(target_date, 'date') else target_date
    delta = target - today
    return delta.days


def format_date(date: datetime, format_str: str = "%Y-%m-%d") -> str:
    """Format a date as a string.
    
    Args:
        date: The date to format
        format_str: Format string
        
    Returns:
        Formatted date string
    """
    if isinstance(date, str):
        # If already a string, try to parse and reformat
        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except:
            return date
    
    return date.strftime(format_str)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string to datetime.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    return None


def ensure_dir_exists(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to directory
    """
    path = Path(path)
    if path.is_file():
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)


def create_backup(file_path: str, max_backups: int = 10) -> Optional[str]:
    """Create a timestamped backup of a file.
    
    Args:
        file_path: Path to file to backup
        max_backups: Maximum number of backups to keep
        
    Returns:
        Path to backup file or None if backup failed
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        # Create backup directory
        backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
        ensure_dir_exists(backup_dir)
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(file_path)
        backup_name = f"{base_name}.{timestamp}.backup"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Copy file
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
                
        # Clean up old backups
        cleanup_old_backups(backup_dir, base_name, max_backups)
        
        logger.info(f"Created backup: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def cleanup_old_backups(backup_dir: str, base_name: str, max_backups: int) -> None:
    """Remove old backup files, keeping only the most recent ones.
    
    Args:
        backup_dir: Directory containing backups
        base_name: Base filename to match
        max_backups: Maximum number of backups to keep
    """
    try:
        # Find all backup files
        pattern = f"{base_name}.*.backup"
        backups = []
        
        for filename in os.listdir(backup_dir):
            if filename.startswith(base_name) and filename.endswith('.backup'):
                file_path = os.path.join(backup_dir, filename)
                mtime = os.path.getmtime(file_path)
                backups.append((mtime, file_path))
                
        # Sort by modification time (newest first)
        backups.sort(reverse=True)
        
        # Remove old backups
        for _, file_path in backups[max_backups:]:
            os.remove(file_path)
            logger.debug(f"Removed old backup: {file_path}")
            
    except Exception as e:
        logger.warning(f"Error cleaning up backups: {e}")


def get_week_range(date: datetime) -> tuple[datetime, datetime]:
    """Get the start and end dates of the week containing the given date.
    
    Args:
        date: Date to get week range for
        
    Returns:
        Tuple of (week_start, week_end) dates
    """
    # Monday is 0, Sunday is 6
    days_since_monday = date.weekday()
    week_start = date - datetime.timedelta(days=days_since_monday)
    week_end = week_start + datetime.timedelta(days=6)
    
    return week_start, week_end