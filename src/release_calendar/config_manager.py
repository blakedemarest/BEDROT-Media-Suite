"""
Configuration Manager for Release Calendar Module

Handles loading, saving, and management of release calendar configuration.
Integrates with the media suite's centralized configuration system.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import media suite's centralized config utilities
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core import get_config_manager as get_core_config_manager
from core import resolve_config_path
from core.path_utils import validate_path


class ConfigManager:
    """Manages configuration for the release calendar module."""
    
    def __init__(self, config_file: str = "config/release_calendar_config.json"):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Returns:
            Configuration dictionary
        """
        try:
            config_path = resolve_config_path(os.path.basename(self.config_file))
                
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[Release Calendar] Config file not found at {config_path}, using defaults")
                return self.get_default_config()
                
        except Exception as e:
            print(f"[Release Calendar] Error loading config: {e}")
            return self.get_default_config()
    
    def save_config(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file.
        
        Args:
            config_data: Configuration data to save (uses self.config if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_data is None:
                config_data = self.config
                
            config_path = resolve_config_path(os.path.basename(self.config_file))
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
                
            self.config = config_data
            return True
            
        except Exception as e:
            print(f"[Release Calendar] Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
    
    def get_artist_config(self, artist: str) -> Dict[str, Any]:
        """Get configuration for a specific artist.
        
        Args:
            artist: Artist name
            
        Returns:
            Artist configuration dictionary
        """
        return self.config.get('artists', {}).get(artist, {})
    
    def get_deliverables_config(self, release_type: str) -> Dict[str, int]:
        """Get deliverables configuration for a release type.
        
        Args:
            release_type: Type of release (single, ep, album)
            
        Returns:
            Deliverables configuration with days before release
        """
        return self.config.get('deliverables', {}).get(release_type, {})
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "artists": {
                "ZONE A0": {
                    "emoji": "[CD]",
                    "genre": "Electronic/Experimental",
                    "singles_per_year": 8,
                    "ep_per_year": 1,
                    "album_per_year": 1
                },
                "PIG1987": {
                    "emoji": "[PIG]",
                    "genre": "TBD",
                    "singles_per_year": 8,
                    "ep_per_year": 1,
                    "album_per_year": 1
                }
            },
            "deliverables": {
                "single": {
                    "distributor_submission": -21,
                    "final_master": -21,
                    "album_artwork": -21,
                    "spotify_canvas": -21,
                    "reels_124": -14,
                    "carousel_posts_25": -14,
                    "music_video": -7,
                    "ad_creatives_5": -3,
                    "release_day_campaign": 0
                },
                "ep": {
                    "distributor_submission": -28,
                    "final_master": -28,
                    "album_artwork": -28,
                    "spotify_canvas": -28,
                    "reels_248": -21,
                    "carousel_posts_50": -21,
                    "music_video": -14,
                    "visualizers": -7,
                    "ad_creatives_10": -7,
                    "release_day_campaign": 0,
                    "listening_party": -1
                },
                "album": {
                    "distributor_submission": -42,
                    "final_master": -42,
                    "album_artwork": -42,
                    "spotify_canvas": -42,
                    "reels_496": -35,
                    "carousel_posts_100": -35,
                    "music_videos_3": -21,
                    "visualizers": -14,
                    "ad_creatives_20": -14,
                    "release_day_campaign": 0,
                    "listening_party": -1,
                    "behind_the_scenes": -7,
                    "press_kit": -28
                }
            },
            "release_frequencies": {
                "single_weeks": [5, 6],
                "ep_months": 12,
                "album_months": 12
            },
            "content_requirements": {
                "reels_per_single": 124,
                "carousel_posts_per_single": 25,
                "ad_creatives_per_single": 5,
                "reels_per_ep": 248,
                "carousel_posts_per_ep": 50,
                "ad_creatives_per_ep": 10,
                "reels_per_album": 496,
                "carousel_posts_per_album": 100,
                "ad_creatives_per_album": 20
            },
            "default_settings": {
                "default_artist": "ZONE A0",
                "highlight_fridays": True,
                "show_deliverable_badges": True,
                "enable_conflict_detection": True,
                "backup_on_save": True,
                "max_backups": 10
            }
        }