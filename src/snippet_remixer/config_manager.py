# -*- coding: utf-8 -*-
"""
Configuration Manager for Video Snippet Remixer.

Handles loading, saving, and managing configuration settings including:
- Input/output folder paths
- BPM and duration settings
- Aspect ratio preferences
- Application state persistence
"""

import json
import os
from .utils import safe_print

# Import centralized configuration system
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from core.path_utils import resolve_config_path, resolve_output_path
    from core.env_loader import get_env_var
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import core configuration system: {e}")
    CORE_AVAILABLE = False

# Constants
BPM_UNITS = {
    "1/6 Beat": 1.0/6.0, "1/4 Beat": 1.0/4.0, "1/3 Beat": 1.0/3.0,
    "1/2 Beat": 1.0/2.0, "Beat": 1.0, "Bar": 4.0
}
DEFAULT_BPM_UNIT = "Beat"
ASPECT_RATIOS = [
    "Original", "16:9", "4:3", "1:1", "9:16", "21:9", "2.35:1", "1.85:1"
]
DEFAULT_ASPECT_RATIO = "Original"


class ConfigManager:
    """
    Manages configuration for the Video Snippet Remixer application.
    """
    
    def __init__(self, config_file="video_remixer_settings.json"):
        # Use centralized path resolution if available
        if CORE_AVAILABLE:
            try:
                self.settings_file_path = str(resolve_config_path(config_file))
                self.config_dir = os.path.dirname(self.settings_file_path)
            except Exception as e:
                safe_print(f"Warning: Could not resolve config path, using fallback: {e}")
                # Fallback to original complex path navigation
                self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                self.config_dir = os.path.join(self.script_dir, '..', 'config')
                self.settings_file_path = os.path.join(self.config_dir, config_file)
        else:
            # Fallback to original complex path navigation
            self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_dir = os.path.join(self.script_dir, '..', 'config')
            self.settings_file_path = os.path.join(self.config_dir, config_file)
        
        self.config_file = config_file
        self.config = self.load_config()
    
    def get_default_config(self):
        """Returns the default configuration settings."""
        # Get default paths using centralized configuration
        if CORE_AVAILABLE:
            try:
                default_output = str(resolve_output_path())
                default_input = default_output  # Use same for input initially
            except Exception as e:
                safe_print(f"Warning: Could not resolve default paths: {e}")
                default_output = getattr(self, 'script_dir', os.getcwd())
                default_input = default_output
        else:
            default_output = getattr(self, 'script_dir', os.getcwd())
            default_input = default_output
        
        return {
            "last_input_folder": default_input,
            "output_folder": default_output,
            "length_mode": "Seconds",
            "duration_seconds": 15.0,
            "bpm": 120.0,
            "bpm_unit": DEFAULT_BPM_UNIT,
            "num_units": 16,
            "aspect_ratio": get_env_var('SLIDESHOW_DEFAULT_ASPECT_RATIO', DEFAULT_ASPECT_RATIO) if CORE_AVAILABLE else DEFAULT_ASPECT_RATIO,
            "export_settings": {
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 23,
                "bitrate": "5M",
                "trim_start": "",
                "trim_end": ""
            }
        }
    
    def load_config(self):
        """Loads configuration from JSON file or creates default."""
        default_settings = self.get_default_config()
        
        # Determine settings path
        if not os.path.exists(self.config_dir) and self.config_dir != self.script_dir:
            try:
                os.makedirs(self.config_dir)
            except OSError as e:
                safe_print(f"Error creating config dir {self.config_dir}: {e}. Using script dir.")
                settings_path = os.path.join(self.script_dir, os.path.basename(self.config_file))
        else:
            settings_path = self.settings_file_path

        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # Validate and fix settings
                    for key, default_val in default_settings.items():
                        if key not in settings or not isinstance(settings[key], type(default_val)):
                            settings[key] = default_val
                            safe_print(f"Warning: Setting '{key}' missing or wrong type, using default: {default_val}")
                        
                        # Specific validation
                        if key in ["last_input_folder", "output_folder"]:
                            if isinstance(settings[key], str):
                                if not os.path.isdir(settings[key]):
                                    safe_print(f"Warning: Saved path '{settings[key]}' for {key} invalid. Using script directory.")
                                    settings[key] = self.script_dir
                            else:
                                safe_print(f"Warning: Saved path for {key} is not a string. Using script directory.")
                                settings[key] = self.script_dir
                        elif key == "length_mode" and settings[key] not in ["Seconds", "BPM"]:
                            settings[key] = default_settings["length_mode"]
                        elif key == "bpm_unit" and settings[key] not in BPM_UNITS:
                            settings[key] = default_settings["bpm_unit"]
                        elif key == "aspect_ratio" and settings[key] not in ASPECT_RATIOS:
                            safe_print(f"Warning: Invalid aspect_ratio '{settings[key]}', using default.")
                            settings[key] = default_settings["aspect_ratio"]
                        elif key in ["duration_seconds", "bpm"]:
                            if isinstance(settings[key], (int, float)) and settings[key] <= 0:
                                settings[key] = default_settings[key]
                            elif not isinstance(settings[key], (int, float)):
                                settings[key] = default_settings[key]
                        elif key == "num_units":
                            if isinstance(settings[key], int) and settings[key] <= 0:
                                settings[key] = default_settings[key]
                            elif not isinstance(settings[key], int):
                                settings[key] = default_settings[key]

                    return settings
            except (json.JSONDecodeError, IOError, TypeError) as e:
                safe_print(f"Error loading settings file '{settings_path}': {e}. Using defaults.")
                return default_settings.copy()
        else:
            safe_print(f"Settings file '{os.path.basename(settings_path)}' not found. Using defaults.")
            return default_settings.copy()
    
    def save_config(self, settings_dict=None):
        """Saves settings to the JSON file."""
        if settings_dict is None:
            settings_dict = self.config
        
        # Determine settings path
        if not os.path.exists(self.config_dir) and self.config_dir != self.script_dir:
            try:
                os.makedirs(self.config_dir)
            except OSError as e:
                safe_print(f"Error creating config dir {self.config_dir}: {e}. Saving to script dir.")
                settings_path = os.path.join(self.script_dir, os.path.basename(self.config_file))
        else:
            settings_path = self.settings_file_path

        try:
            # Basic validation
            for key in ["last_input_folder", "output_folder"]:
                path_to_check = settings_dict.get(key, self.script_dir)
                if not isinstance(path_to_check, str) or not os.path.isdir(path_to_check):
                    safe_print(f"Warning: Path '{path_to_check}' for {key} doesn't exist or is invalid. Saving setting but it might be invalid.")
            
            if settings_dict.get("length_mode") not in ["Seconds", "BPM"]:
                settings_dict["length_mode"] = "Seconds"
            if settings_dict.get("bpm_unit") not in BPM_UNITS:
                settings_dict["bpm_unit"] = DEFAULT_BPM_UNIT
            if settings_dict.get("aspect_ratio") not in ASPECT_RATIOS:
                settings_dict["aspect_ratio"] = DEFAULT_ASPECT_RATIO
            
            try:
                settings_dict["duration_seconds"] = float(settings_dict.get("duration_seconds", 15.0))
            except (ValueError, TypeError):
                settings_dict["duration_seconds"] = 15.0
            
            try:
                settings_dict["bpm"] = float(settings_dict.get("bpm", 120.0))
            except (ValueError, TypeError):
                settings_dict["bpm"] = 120.0
                
            try:
                settings_dict["num_units"] = int(settings_dict.get("num_units", 16))
            except (ValueError, TypeError):
                settings_dict["num_units"] = 16
            
            if settings_dict["duration_seconds"] <= 0:
                settings_dict["duration_seconds"] = 15.0
            if settings_dict["bpm"] <= 0:
                settings_dict["bpm"] = 120.0
            if settings_dict["num_units"] <= 0:
                settings_dict["num_units"] = 16

            # Ensure the directory exists before writing
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                # Remove output_filename just before saving if it somehow sneaked in
                settings_dict.pop("output_filename", None)
                json.dump(settings_dict, f, indent=4)
                
            self.config = settings_dict
            
        except IOError as e:
            safe_print(f"Error saving settings file '{settings_path}': {e}")
        except Exception as e:
            safe_print(f"An unexpected error occurred saving settings: {e}")
    
    def get_setting(self, key, default=None):
        """Get a specific setting value."""
        return self.config.get(key, default)
    
    def set_setting(self, key, value):
        """Set a specific setting value."""
        self.config[key] = value
    
    def get_bpm_units(self):
        """Returns the BPM units dictionary."""
        return BPM_UNITS.copy()
    
    def get_aspect_ratios(self):
        """Returns the available aspect ratios list."""
        return ASPECT_RATIOS.copy()
    
    def get_script_dir(self):
        """Returns the script directory path."""
        return self.script_dir
    
    def get_export_settings(self):
        """Returns the export settings."""
        return self.config.get("export_settings", self.get_default_config()["export_settings"])
    
    def set_export_settings(self, settings):
        """Updates and saves export settings."""
        if "export_settings" not in self.config:
            self.config["export_settings"] = {}
        self.config["export_settings"].update(settings)
        self.save_config()