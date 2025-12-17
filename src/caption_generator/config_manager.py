# -*- coding: utf-8 -*-
"""
Configuration Manager for Caption Generator.

Handles loading, saving, and managing configuration settings.
"""

import json
import os
import sys

# Import centralized configuration system
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.path_utils import resolve_config_path, resolve_output_path


class ConfigManager:
    """Manages configuration for the Caption Generator application."""

    def __init__(self, config_file="caption_generator_settings.json"):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_file_path = str(resolve_config_path(config_file))
        self.config_dir = os.path.dirname(self.settings_file_path)
        self.config_file = config_file
        self.config = self.load_config()

    def get_default_config(self):
        """Returns the default configuration settings."""
        default_output = str(resolve_output_path("caption_videos"))
        default_transcripts = str(resolve_output_path("transcripts"))
        default_history_db = str(resolve_config_path("caption_generator_history.db"))

        return {
            "output_folder": default_output,
            "font_name": "Arial Narrow",
            "font_size": 56,
            "font_color": "#ffffff",
            "background_color": "#000000",
            "transparent_background": False,
            "resolution": "1920x1080",
            "fps": 30,
            "alignment": "center",
            "outline_size": 2,
            "last_srt_folder": "",
            "last_audio_folder": "",
            # New settings for drag-and-drop and batch processing
            "history_db_path": default_history_db,
            "auto_transcribe_on_drop": True,
            "transcription_output_folder": default_transcripts,
            "api_key_env": "ELEVENLABS_API_KEY",
            "max_words_per_segment": 1,
            "batch_continue_on_error": True,
            "all_caps": False,
            "ignore_grammar": False,
            "safe_area_mode": True
        }

    def load_config(self):
        """Loads configuration from JSON file or creates default."""
        default_settings = self.get_default_config()

        # Ensure config directory exists
        if not os.path.exists(self.config_dir) and self.config_dir != self.script_dir:
            try:
                os.makedirs(self.config_dir)
            except OSError as e:
                print(f"[Caption Generator] Error creating config dir: {e}")

        if os.path.exists(self.settings_file_path):
            try:
                with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Merge with defaults (add any missing keys)
                for key, default_val in default_settings.items():
                    if key not in settings:
                        settings[key] = default_val
                        print(f"[Caption Generator] Setting '{key}' missing, using default: {default_val}")

                return settings
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Caption Generator] Error loading settings: {e}. Using defaults.")
                return default_settings.copy()
        else:
            print("[Caption Generator] Settings file not found. Using defaults.")
            return default_settings.copy()

    def save_config(self, settings_dict=None):
        """Saves settings to the JSON file."""
        if settings_dict is None:
            settings_dict = self.config

        try:
            os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=4)
            self.config = settings_dict
        except IOError as e:
            print(f"[Caption Generator] Error saving settings: {e}")

    def get(self, key, default=None):
        """Get a specific setting value."""
        return self.config.get(key, default)

    def set(self, key, value, autosave=True):
        """Set a specific setting value."""
        self.config[key] = value
        if autosave:
            self.save_config()

    def get_output_folder(self):
        """Returns the output folder path."""
        return self.config.get("output_folder", str(resolve_output_path("caption_videos")))

    def get_history_db_path(self):
        """Returns the path to the pairing history database."""
        return self.config.get("history_db_path", str(resolve_config_path("caption_generator_history.db")))

    def get_transcript_folder(self):
        """Returns the folder path for generated transcripts."""
        return self.config.get("transcription_output_folder", str(resolve_output_path("transcripts")))


# Global config instance
_config_instance = None


def get_config():
    """Get the global config manager instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
