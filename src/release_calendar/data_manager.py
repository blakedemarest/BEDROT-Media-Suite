"""
Calendar Data Manager for Release Calendar Module

Handles saving and loading calendar data with automatic backups.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .utils import logger, create_backup, ensure_dir_exists

# Import media suite's path utilities if available
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from core import resolve_config_path
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


class CalendarDataManager:
    """Manages calendar data persistence with automatic backups."""
    
    def __init__(self, data_file: str = "config/calendar_data.json"):
        """Initialize the data manager.
        
        Args:
            data_file: Path to the calendar data file
        """
        self.data_file = self._resolve_data_path(data_file)
        self.data = self.load_data()
        
    def _resolve_data_path(self, data_file: str) -> str:
        """Resolve the data file path.
        
        Args:
            data_file: Relative or absolute path to data file
            
        Returns:
            Resolved absolute path
        """
        if CORE_AVAILABLE:
            try:
                return resolve_config_path(os.path.basename(data_file))
            except:
                pass
                
        # Fallback to relative path from script location
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(script_dir, data_file)
        
    def load_data(self) -> Dict[str, Any]:
        """Load calendar data from file.
        
        Returns:
            Calendar data dictionary
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded calendar data from {self.data_file}")
                    return data
            else:
                logger.info(f"No existing calendar data found at {self.data_file}, starting fresh")
                return self.get_default_data()
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing calendar data: {e}")
            # Create backup of corrupted file
            backup_path = self.data_file + '.corrupted.' + datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                os.rename(self.data_file, backup_path)
                logger.warning(f"Moved corrupted data file to {backup_path}")
            except:
                pass
            return self.get_default_data()
            
        except Exception as e:
            logger.error(f"Error loading calendar data: {e}")
            return self.get_default_data()
            
    def save_data(self, create_backup_copy: bool = True, max_backups: int = 10) -> bool:
        """Save calendar data to file.
        
        Args:
            create_backup_copy: Whether to create a backup before saving
            max_backups: Maximum number of backups to keep
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            ensure_dir_exists(os.path.dirname(self.data_file))
            
            # Create backup if requested and file exists
            if create_backup_copy and os.path.exists(self.data_file):
                create_backup(self.data_file, max_backups)
                
            # Save data
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Saved calendar data to {self.data_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving calendar data: {e}")
            return False
            
    def get_default_data(self) -> Dict[str, Any]:
        """Get default calendar data structure.
        
        Returns:
            Default data dictionary
        """
        return {
            "artists": {},
            "metadata": {
                "version": "1.0.0",
                "last_modified": datetime.now().isoformat(),
                "created": datetime.now().isoformat()
            }
        }
        
    def get_artist_releases(self, artist: str) -> List[Dict[str, Any]]:
        """Get all releases for an artist.
        
        Args:
            artist: Artist name
            
        Returns:
            List of release dictionaries
        """
        return self.data.get("artists", {}).get(artist, [])
        
    def set_artist_releases(self, artist: str, releases: List[Dict[str, Any]]) -> None:
        """Set releases for an artist.
        
        Args:
            artist: Artist name
            releases: List of release dictionaries
        """
        if "artists" not in self.data:
            self.data["artists"] = {}
            
        self.data["artists"][artist] = releases
        
        # Update metadata
        if "metadata" not in self.data:
            self.data["metadata"] = {}
        self.data["metadata"]["last_modified"] = datetime.now().isoformat()
        
    def add_release(self, artist: str, release: Dict[str, Any]) -> None:
        """Add a release for an artist.
        
        Args:
            artist: Artist name
            release: Release dictionary
        """
        releases = self.get_artist_releases(artist)
        releases.append(release)
        self.set_artist_releases(artist, releases)
        
    def update_release(self, artist: str, title: str, updates: Dict[str, Any]) -> bool:
        """Update a specific release.
        
        Args:
            artist: Artist name
            title: Release title
            updates: Dictionary of updates to apply
            
        Returns:
            True if release was found and updated, False otherwise
        """
        releases = self.get_artist_releases(artist)
        
        for release in releases:
            if release.get("title") == title:
                release.update(updates)
                self.set_artist_releases(artist, releases)
                return True
                
        return False
        
    def delete_release(self, artist: str, title: str) -> bool:
        """Delete a specific release.
        
        Args:
            artist: Artist name
            title: Release title
            
        Returns:
            True if release was found and deleted, False otherwise
        """
        releases = self.get_artist_releases(artist)
        original_count = len(releases)
        
        # Filter out the release to delete
        releases = [r for r in releases if r.get("title") != title]
        
        if len(releases) < original_count:
            self.set_artist_releases(artist, releases)
            return True
            
        return False
        
    def get_all_releases(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all releases for all artists.
        
        Returns:
            Dictionary mapping artist names to release lists
        """
        return self.data.get("artists", {})
        
    def export_data(self) -> Dict[str, Any]:
        """Export the complete calendar data.
        
        Returns:
            Complete calendar data dictionary
        """
        return self.data.copy()
        
    def import_data(self, data: Dict[str, Any], merge: bool = False) -> bool:
        """Import calendar data.
        
        Args:
            data: Calendar data to import
            merge: If True, merge with existing data; if False, replace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if merge and "artists" in self.data and "artists" in data:
                # Merge artist data
                for artist, releases in data.get("artists", {}).items():
                    if artist in self.data["artists"]:
                        # Merge releases (avoid duplicates based on title)
                        existing_titles = {r.get("title") for r in self.data["artists"][artist]}
                        for release in releases:
                            if release.get("title") not in existing_titles:
                                self.data["artists"][artist].append(release)
                    else:
                        self.data["artists"][artist] = releases
            else:
                # Replace data
                self.data = data
                
            # Update metadata
            if "metadata" not in self.data:
                self.data["metadata"] = {}
            self.data["metadata"]["last_modified"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing calendar data: {e}")
            return False