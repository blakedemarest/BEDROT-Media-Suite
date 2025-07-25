"""
Calendar Logic for Release Calendar Module

Contains the core business logic for managing release calendars,
including multi-artist support, deliverable tracking, and scheduling.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pandas as pd
from pathlib import Path

from .utils import logger, format_deliverable_name, days_until
from .config_manager import ConfigManager
from .data_manager import CalendarDataManager


class ReleaseCalendar:
    """Base class for managing release calendars."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the release calendar.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.releases = []
        
    def add_release(self, artist: str, title: str, release_date: datetime,
                   release_type: str = "single", deliverables: Optional[Dict] = None,
                   notes: str = "") -> Dict[str, Any]:
        """Add a release to the calendar.
        
        Args:
            artist: Artist name
            title: Release title
            release_date: Release date
            release_type: Type of release (single, ep, album)
            deliverables: Custom deliverables (uses defaults if None)
            notes: Additional notes
            
        Returns:
            Release dictionary
        """
        if deliverables is None:
            deliverables = self.get_default_deliverables(release_type)
            
        # Initialize checklist
        checklist = self._create_checklist(deliverables, release_date)
        
        release = {
            'artist': artist,
            'title': title,
            'release_date': release_date.isoformat() if isinstance(release_date, datetime) else release_date,
            'type': release_type,
            'deliverables': deliverables,
            'checklist': checklist,
            'notes': notes,
            'artwork_path': None,
            'created_date': datetime.now().isoformat()
        }
        
        self.releases.append(release)
        return release
        
    def get_default_deliverables(self, release_type: str) -> Dict[str, int]:
        """Get default deliverable deadlines from configuration.
        
        Args:
            release_type: Type of release
            
        Returns:
            Dictionary of deliverable names to days offset
        """
        return self.config_manager.get_deliverables_config(release_type)
        
    def _create_checklist(self, deliverables: Dict[str, int], release_date: datetime) -> Dict[str, Dict]:
        """Create a checklist from deliverables.
        
        Args:
            deliverables: Dictionary of deliverable names to days offset
            release_date: Release date
            
        Returns:
            Checklist dictionary
        """
        checklist = {}
        
        # Ensure release_date is a datetime object
        if isinstance(release_date, str):
            release_date = datetime.fromisoformat(release_date)
            
        for deliverable_name, days_offset in deliverables.items():
            due_date = release_date + timedelta(days=days_offset)
            checklist[deliverable_name] = {
                'completed': False,
                'completed_date': None,
                'due_date': due_date.isoformat(),
                'notes': ''
            }
            
        return checklist
        
    def generate_schedule(self, start_date: datetime, end_date: datetime,
                         frequency_weeks: int, artist: str, prefix: str = "Release") -> List[Dict]:
        """Generate a regular release schedule.
        
        Args:
            start_date: Start date
            end_date: End date
            frequency_weeks: Weeks between releases
            artist: Artist name
            prefix: Prefix for release titles
            
        Returns:
            List of generated releases
        """
        generated_releases = []
        current_date = start_date
        release_num = 1
        
        while current_date <= end_date:
            release = self.add_release(
                artist=artist,
                title=f"{prefix} #{release_num}",
                release_date=current_date,
                release_type="single"
            )
            generated_releases.append(release)
            current_date += timedelta(weeks=frequency_weeks)
            release_num += 1
            
        return generated_releases
        
    def get_deliverables_calendar(self) -> pd.DataFrame:
        """Get all deliverables with their deadlines as a DataFrame.
        
        Returns:
            DataFrame with deliverable information
        """
        deliverables_list = []
        
        for release in self.releases:
            release_date = release['release_date']
            if isinstance(release_date, str):
                release_date = datetime.fromisoformat(release_date)
                
            checklist = release.get('checklist', {})
            
            for deliverable_name, details in checklist.items():
                due_date = details['due_date']
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date)
                    
                deliverables_list.append({
                    'artist': release['artist'],
                    'release': release['title'],
                    'release_date': release_date,
                    'deliverable': format_deliverable_name(deliverable_name),
                    'due_date': due_date,
                    'days_until_release': (release_date - due_date).days,
                    'completed': details.get('completed', False),
                    'completed_date': details.get('completed_date'),
                    'notes': details.get('notes', '')
                })
                
        df = pd.DataFrame(deliverables_list)
        if not df.empty:
            df = df.sort_values(['due_date', 'artist', 'release'])
        return df
        
    def cleanup_old_releases(self, days_old: int = 365) -> int:
        """Remove releases older than specified days.
        
        Args:
            days_old: Number of days to keep
            
        Returns:
            Number of releases removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        original_count = len(self.releases)
        
        self.releases = [
            release for release in self.releases
            if datetime.fromisoformat(release['release_date']) > cutoff_date
        ]
        
        return original_count - len(self.releases)
        
    def clear_all_releases(self) -> None:
        """Clear all release data."""
        self.releases.clear()
        
    def get_release_count(self) -> int:
        """Get total number of releases."""
        return len(self.releases)


class BedrotReleaseCalendar(ReleaseCalendar):
    """Extended release calendar with multi-artist support and advanced features."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None,
                 data_manager: Optional[CalendarDataManager] = None):
        """Initialize the BEDROT release calendar.
        
        Args:
            config_manager: Configuration manager instance
            data_manager: Data manager instance
        """
        super().__init__(config_manager)
        self.data_manager = data_manager or CalendarDataManager()
        self.artists = {}  # Dictionary of artist -> releases
        self._load_from_data_manager()
        
    def _load_from_data_manager(self) -> None:
        """Load data from the data manager."""
        all_data = self.data_manager.get_all_releases()
        for artist, releases in all_data.items():
            self.artists[artist] = releases
            
    def save_to_data_manager(self) -> bool:
        """Save current state to data manager.
        
        Returns:
            True if successful
        """
        # Update data manager with current state
        for artist, releases in self.artists.items():
            self.data_manager.set_artist_releases(artist, releases)
            
        # Save to file
        return self.data_manager.save_data()
        
    def add_artist(self, artist_name: str, config: Optional[Dict] = None) -> None:
        """Add a new artist to the calendar system.
        
        Args:
            artist_name: Name of the artist
            config: Artist configuration
        """
        if artist_name not in self.artists:
            self.artists[artist_name] = []
            logger.info(f"Added artist: {artist_name}")
            
    def add_release(self, artist: str, title: str, release_date: datetime,
                   release_type: str = "single", custom_deliverables: Optional[Dict] = None,
                   notes: str = "") -> Dict[str, Any]:
        """Add a release to an artist's calendar.
        
        Args:
            artist: Artist name
            title: Release title
            release_date: Release date
            release_type: Type of release
            custom_deliverables: Custom deliverables
            notes: Additional notes
            
        Returns:
            Release dictionary
        """
        if artist not in self.artists:
            self.add_artist(artist)
            
        # Create release using parent method
        release = super().add_release(
            artist, title, release_date, release_type,
            custom_deliverables, notes
        )
        
        # Add to artist's releases
        self.artists[artist].append(release)
        
        # Save to data manager
        self.save_to_data_manager()
        
        return release
        
    def get_artist_releases(self, artist: str) -> List[Dict[str, Any]]:
        """Get all releases for a specific artist.
        
        Args:
            artist: Artist name
            
        Returns:
            List of releases
        """
        return self.artists.get(artist, [])
        
    def get_all_releases(self) -> List[Dict[str, Any]]:
        """Get all releases for all artists.
        
        Returns:
            Flat list of all releases
        """
        all_releases = []
        for artist, releases in self.artists.items():
            all_releases.extend(releases)
        return all_releases
        
    def update_release(self, artist: str, title: str, updates: Dict[str, Any]) -> bool:
        """Update a specific release.
        
        Args:
            artist: Artist name
            title: Release title
            updates: Dictionary of updates
            
        Returns:
            True if successful
        """
        if artist not in self.artists:
            return False
            
        for release in self.artists[artist]:
            if release.get('title') == title:
                release.update(updates)
                self.save_to_data_manager()
                return True
                
        return False
        
    def delete_release(self, artist: str, title: str) -> bool:
        """Delete a specific release.
        
        Args:
            artist: Artist name
            title: Release title
            
        Returns:
            True if successful
        """
        if artist not in self.artists:
            return False
            
        original_count = len(self.artists[artist])
        self.artists[artist] = [
            r for r in self.artists[artist]
            if r.get('title') != title
        ]
        
        if len(self.artists[artist]) < original_count:
            self.save_to_data_manager()
            return True
            
        return False
        
    def update_checklist_item(self, artist: str, title: str, deliverable: str,
                             completed: Optional[bool] = None, notes: Optional[str] = None) -> bool:
        """Update a checklist item for a release.
        
        Args:
            artist: Artist name
            title: Release title
            deliverable: Deliverable name
            completed: Completion status
            notes: Additional notes
            
        Returns:
            True if successful
        """
        if artist not in self.artists:
            return False
            
        for release in self.artists[artist]:
            if release.get('title') == title:
                if deliverable in release.get('checklist', {}):
                    if completed is not None:
                        release['checklist'][deliverable]['completed'] = completed
                        if completed:
                            release['checklist'][deliverable]['completed_date'] = datetime.now().isoformat()
                        else:
                            release['checklist'][deliverable]['completed_date'] = None
                            
                    if notes is not None:
                        release['checklist'][deliverable]['notes'] = notes
                        
                    self.save_to_data_manager()
                    return True
                    
        return False
        
    def check_release_conflicts(self, artist: str, release_date: datetime,
                               window_days: int = 7) -> List[Dict[str, Any]]:
        """Check for release conflicts within a time window.
        
        Args:
            artist: Artist to check
            release_date: Proposed release date
            window_days: Days to check before/after
            
        Returns:
            List of conflicting releases
        """
        conflicts = []
        window_start = release_date - timedelta(days=window_days)
        window_end = release_date + timedelta(days=window_days)
        
        # Check all artists for conflicts
        for check_artist, releases in self.artists.items():
            if check_artist == artist:
                continue  # Skip same artist
                
            for release in releases:
                rel_date = release['release_date']
                if isinstance(rel_date, str):
                    rel_date = datetime.fromisoformat(rel_date)
                    
                if window_start <= rel_date <= window_end:
                    conflicts.append({
                        'artist': check_artist,
                        'title': release['title'],
                        'release_date': rel_date,
                        'days_apart': abs((rel_date - release_date).days)
                    })
                    
        return conflicts
        
    def generate_waterfall_schedule(self, artist: str, start_date: datetime,
                                   singles_per_year: int = 8, ep_months: int = 12,
                                   album_months: int = 12) -> List[Dict[str, Any]]:
        """Generate a waterfall release schedule for an artist.
        
        Args:
            artist: Artist name
            start_date: Start date
            singles_per_year: Number of singles per year
            ep_months: Months between EPs
            album_months: Months between albums
            
        Returns:
            List of scheduled releases
        """
        scheduled_releases = []
        current_date = start_date
        
        # Calculate single frequency
        if singles_per_year > 0:
            weeks_between_singles = 52 // singles_per_year
            
            # Schedule singles
            for i in range(singles_per_year):
                release = self.add_release(
                    artist=artist,
                    title=f"Single {i+1}",
                    release_date=current_date,
                    release_type="single"
                )
                scheduled_releases.append(release)
                current_date += timedelta(weeks=weeks_between_singles)
                
        # Schedule EP
        if ep_months > 0:
            ep_date = start_date + relativedelta(months=ep_months)
            release = self.add_release(
                artist=artist,
                title="EP",
                release_date=ep_date,
                release_type="ep"
            )
            scheduled_releases.append(release)
            
        # Schedule Album
        if album_months > 0:
            album_date = start_date + relativedelta(months=album_months)
            release = self.add_release(
                artist=artist,
                title="Album",
                release_date=album_date,
                release_type="album"
            )
            scheduled_releases.append(release)
            
        return scheduled_releases