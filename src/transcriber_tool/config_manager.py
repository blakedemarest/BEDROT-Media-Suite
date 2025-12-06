# -*- coding: utf-8 -*-
"""
Configuration Manager for Transcriber Tool.

Handles loading, saving, and managing configuration settings including:
- Output folder paths
- API key environment variable name
- Supported audio/video formats
"""

import json
import os
import sys

# Import centralized configuration system
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.path_utils import resolve_config_path, resolve_output_path
from core.env_loader import get_env_var

# Supported audio/video formats
SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".m4a", ".flac"]


class ConfigManager:
    """
    Manages configuration for the Transcriber Tool application.
    """

    def __init__(self, config_file="transcriber_tool_settings.json"):
        # Set script directory for compatibility
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Use centralized path resolution
        self.settings_file_path = str(resolve_config_path(config_file))
        self.config_dir = os.path.dirname(self.settings_file_path)

        self.config_file = config_file
        self.config = self.load_config()

    def get_default_config(self):
        """Returns the default configuration settings."""
        # Get default paths using centralized configuration
        default_output = str(resolve_output_path("transcripts"))

        return {
            "output_folder": default_output,
            "api_key_env": "ELEVENLABS_API_KEY",
            "supported_formats": SUPPORTED_FORMATS.copy(),
            "language_code": "eng",
            "enable_diarization": True,
            "tag_audio_events": True,
            "export_formats": {
                "txt": True,
                "srt": True
            }
        }

    def load_config(self):
        """Loads configuration from JSON file or creates default."""
        default_settings = self.get_default_config()

        # Ensure config directory exists
        if not os.path.exists(self.config_dir) and self.config_dir != self.script_dir:
            try:
                os.makedirs(self.config_dir)
            except OSError as e:
                print(f"Error creating config dir {self.config_dir}: {e}. Using script dir.")
                settings_path = os.path.join(self.script_dir, os.path.basename(self.config_file))
        else:
            settings_path = self.settings_file_path

        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                    # Validate and merge with defaults
                    for key, default_val in default_settings.items():
                        if key not in settings:
                            settings[key] = default_val
                            print(f"[TranscriberTool] Setting '{key}' missing, using default: {default_val}")

                        # Validate output folder
                        if key == "output_folder":
                            if isinstance(settings[key], str):
                                if not os.path.isdir(settings[key]):
                                    print(f"[TranscriberTool] Output folder '{settings[key]}' invalid. Using default.")
                                    settings[key] = default_settings["output_folder"]
                            else:
                                settings[key] = default_settings["output_folder"]

                    return settings
            except (json.JSONDecodeError, IOError, TypeError) as e:
                print(f"[TranscriberTool] Error loading settings file '{settings_path}': {e}. Using defaults.")
                return default_settings.copy()
        else:
            print(f"[TranscriberTool] Settings file not found. Using defaults.")
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
                print(f"[TranscriberTool] Error creating config dir {self.config_dir}: {e}.")
                settings_path = os.path.join(self.script_dir, os.path.basename(self.config_file))
        else:
            settings_path = self.settings_file_path

        try:
            # Ensure the directory exists before writing
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=4)

            self.config = settings_dict

        except IOError as e:
            print(f"[TranscriberTool] Error saving settings file '{settings_path}': {e}")
        except Exception as e:
            print(f"[TranscriberTool] Unexpected error saving settings: {e}")

    def get(self, key, default=None):
        """Get a specific setting value with dot notation support."""
        # Support dotted keys for compatibility
        if "." in key:
            parts = key.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        return self.config.get(key, default)

    def set(self, key, value, autosave=True):
        """Set a specific setting value."""
        # Support dotted keys for compatibility
        if "." in key:
            parts = key.split(".")
            target = self.config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        else:
            self.config[key] = value

        if autosave:
            self.save_config()

    def get_supported_formats(self):
        """Returns the supported file formats list."""
        return self.config.get("supported_formats", SUPPORTED_FORMATS.copy())

    def get_output_folder(self):
        """Returns the output folder path."""
        return self.config.get("output_folder", str(resolve_output_path("transcripts")))

    def get_api_key_env(self):
        """Returns the API key environment variable name."""
        return self.config.get("api_key_env", "ELEVENLABS_API_KEY")


# Global config instance
_config_instance = None


def get_config():
    """Get the global config manager instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
