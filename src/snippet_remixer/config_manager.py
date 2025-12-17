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
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.path_utils import resolve_config_path, resolve_output_path
from core.env_loader import get_env_var

# Constants
BPM_UNITS = {
    "1/16 Beat": 1.0/16.0,
    "1/6 Beat": 1.0/6.0,
    "1/4 Beat": 1.0/4.0,
    "1/3 Beat": 1.0/3.0,
    "1/2 Beat": 1.0/2.0,
    "Beat": 1.0,
    "1/16 Bar": 4.0/16.0,
    "1/6 Bar": 4.0/6.0,
    "1/4 Bar": 4.0/4.0,
    "1/3 Bar": 4.0/3.0,
    "1/2 Bar": 4.0/2.0,
    "Bar": 4.0
}
DEFAULT_BPM_UNIT = "Beat"

# HD Aspect Ratio Presets (Width x Height format with smart detection)
ASPECT_RATIOS = [
    "Original", 
    "1920x1080 (16:9 Landscape)", 
    "1080x1920 (9:16 Portrait)", 
    "1080x1080 (1:1 Square)", 
    "1440x1080 (4:3 Classic)", 
    "2560x1080 (21:9 Ultrawide)", 
    "1920x817 (2.35:1 Cinema)", 
    "1920x1038 (1.85:1 Film)"
]
DEFAULT_ASPECT_RATIO = "1920x1080 (16:9 Landscape)"


class ConfigManager:
    """
    Manages configuration for the Video Snippet Remixer application.
    """
    
    def __init__(self, config_file="video_remixer_settings.json"):
        # Always set script_dir first for compatibility
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Use centralized path resolution
        self.settings_file_path = str(resolve_config_path(config_file))
        self.config_dir = os.path.dirname(self.settings_file_path)
        
        self.config_file = config_file
        self.config = self.load_config()
    
    def get_default_config(self):
        """Returns the default configuration settings."""
        # Get default paths using centralized configuration
        default_output = str(resolve_output_path())
        default_input = default_output  # Use same for input initially
        
        return {
            "last_input_folder": default_input,
            "output_folder": default_output,
            "length_mode": "Seconds",
            "duration_seconds": 15.0,
            "bpm": 120.0,
            "bpm_unit": DEFAULT_BPM_UNIT,
            "num_units": 16,
            "tempo_mod_enabled": False,
            "tempo_mod_start_bpm": 120.0,
            "tempo_mod_end_bpm": 120.0,
            "tempo_mod_duration_seconds": 15.0,
            "tempo_mod_points": [
                {"time": 0.0, "bpm": 120.0},
                {"time": 15.0, "bpm": 120.0}
            ],
            "aspect_ratio": get_env_var('SLIDESHOW_DEFAULT_ASPECT_RATIO', DEFAULT_ASPECT_RATIO),
            "continuous_mode": False,
            "mute_audio": False,
            "jitter_enabled": False,
            "jitter_intensity": 50,
            "aspect_ratio_mode": "Crop to Fill",
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
                        elif key == "aspect_ratio_mode" and settings[key] not in ["Crop to Fill", "Pad to Fit"]:
                            safe_print(f"Warning: Invalid aspect_ratio_mode '{settings[key]}', using default.")
                            settings[key] = default_settings["aspect_ratio_mode"]
                        elif key in ["duration_seconds", "bpm", "tempo_mod_start_bpm", "tempo_mod_end_bpm", "tempo_mod_duration_seconds"]:
                            if isinstance(settings[key], (int, float)) and settings[key] <= 0:
                                settings[key] = default_settings[key]
                            elif not isinstance(settings[key], (int, float)):
                                settings[key] = default_settings[key]
                        elif key == "tempo_mod_points":
                            settings[key] = self._sanitize_tempo_points(
                                settings.get("tempo_mod_points"),
                                settings.get("tempo_mod_duration_seconds", default_settings["tempo_mod_duration_seconds"]),
                                settings.get("tempo_mod_start_bpm", default_settings["tempo_mod_start_bpm"]),
                                settings.get("tempo_mod_end_bpm", default_settings["tempo_mod_end_bpm"])
                            )
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
            if settings_dict.get("aspect_ratio_mode") not in ["Crop to Fill", "Pad to Fit"]:
                settings_dict["aspect_ratio_mode"] = "Crop to Fill"
            
            try:
                settings_dict["duration_seconds"] = float(settings_dict.get("duration_seconds", 15.0))
            except (ValueError, TypeError):
                settings_dict["duration_seconds"] = 15.0
            
            try:
                settings_dict["bpm"] = float(settings_dict.get("bpm", 120.0))
            except (ValueError, TypeError):
                settings_dict["bpm"] = 120.0
            try:
                settings_dict["tempo_mod_start_bpm"] = float(settings_dict.get("tempo_mod_start_bpm", settings_dict["bpm"]))
            except (ValueError, TypeError):
                settings_dict["tempo_mod_start_bpm"] = settings_dict["bpm"]
            try:
                settings_dict["tempo_mod_end_bpm"] = float(settings_dict.get("tempo_mod_end_bpm", settings_dict["tempo_mod_start_bpm"]))
            except (ValueError, TypeError):
                settings_dict["tempo_mod_end_bpm"] = settings_dict["tempo_mod_start_bpm"]
            try:
                settings_dict["tempo_mod_duration_seconds"] = float(settings_dict.get("tempo_mod_duration_seconds", settings_dict["duration_seconds"]))
            except (ValueError, TypeError):
                settings_dict["tempo_mod_duration_seconds"] = settings_dict["duration_seconds"]
                
            try:
                settings_dict["num_units"] = int(settings_dict.get("num_units", 16))
            except (ValueError, TypeError):
                settings_dict["num_units"] = 16
            
            if settings_dict["duration_seconds"] <= 0:
                settings_dict["duration_seconds"] = 15.0
            if settings_dict["bpm"] <= 0:
                settings_dict["bpm"] = 120.0
            if settings_dict["tempo_mod_start_bpm"] <= 0:
                settings_dict["tempo_mod_start_bpm"] = settings_dict["bpm"]
            if settings_dict["tempo_mod_end_bpm"] <= 0:
                settings_dict["tempo_mod_end_bpm"] = settings_dict["tempo_mod_start_bpm"]
            if settings_dict["tempo_mod_duration_seconds"] <= 0:
                settings_dict["tempo_mod_duration_seconds"] = settings_dict["duration_seconds"]
            if settings_dict["num_units"] <= 0:
                settings_dict["num_units"] = 16

            # Sanitize tempo modulation points
            settings_dict["tempo_mod_points"] = self._sanitize_tempo_points(
                settings_dict.get("tempo_mod_points"),
                settings_dict["tempo_mod_duration_seconds"],
                settings_dict["tempo_mod_start_bpm"],
                settings_dict["tempo_mod_end_bpm"]
            )

            settings_dict["mute_audio"] = bool(settings_dict.get("mute_audio", False))

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

    def _sanitize_tempo_points(self, points, total_duration, start_bpm, end_bpm):
        """Validate and normalize tempo modulation points."""
        default_points = [
            {"time": 0.0, "bpm": start_bpm},
            {"time": float(total_duration) if total_duration else 15.0, "bpm": end_bpm}
        ]
        if not isinstance(points, list):
            return default_points
        
        sanitized = []
        for p in points:
            if not isinstance(p, dict):
                continue
            try:
                t = float(p.get("time", 0.0))
                bpm_val = float(p.get("bpm", start_bpm))
            except (TypeError, ValueError):
                continue
            if t < 0 or bpm_val <= 0:
                continue
            sanitized.append({"time": t, "bpm": bpm_val})
        
        if len(sanitized) < 2:
            return default_points
        
        # Sort and clamp end time to duration
        sanitized.sort(key=lambda x: x["time"])
        end_time = float(total_duration) if total_duration and total_duration > 0 else sanitized[-1]["time"]
        if end_time <= 0:
            end_time = 15.0
        
        # Ensure first point at time 0
        first = sanitized[0]
        if first["time"] != 0.0:
            sanitized.insert(0, {"time": 0.0, "bpm": first.get("bpm", start_bpm)})
        
        # Ensure last point at end_time
        last = sanitized[-1]
        if abs(last["time"] - end_time) > 1e-6:
            sanitized.append({"time": end_time, "bpm": last.get("bpm", end_bpm)})
        else:
            sanitized[-1]["time"] = end_time
        
        return sanitized
