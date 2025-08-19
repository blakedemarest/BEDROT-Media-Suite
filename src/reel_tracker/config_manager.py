# -*- coding: utf-8 -*-
"""
Configuration Manager for Reel Tracker Application.

Handles loading, saving, and managing configuration settings including:
- Dropdown values persistence
- Last CSV file path
- Application settings
"""

import json
import os
import datetime
from .utils import safe_print

# Import centralized configuration system
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.path_utils import resolve_config_path, resolve_output_path
from core.env_loader import get_env_var


class ConfigManager:
    """
    Manages configuration for the Reel Tracker application.
    """
    
    def __init__(self, config_file="reel_tracker_config.json"):
        try:
            # Use centralized path resolution
            self.config_file = str(resolve_config_path(config_file))
            self.config_dir = os.path.dirname(self.config_file)
            
            self.config = self.load_config()
            # Remove duplicate dropdown entries if any
            self.deduplicate_dropdowns()
        except Exception as e:
            safe_print(f"Error initializing ConfigManager: {e}")
            self.config = self.get_default_config()
        
    def load_config(self):
        """Load configuration from JSON file or create default."""
        try:
            # Ensure config directory exists
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
                
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default config if file doesn't exist
                default_config = self.get_default_config()
                self.save_config(default_config)
                return default_config
        except Exception as e:
            safe_print(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration."""
        return {
            "dropdown_values": {
                "persona": [
                    "", "Fitness Influencer", "Tech Reviewer", "Lifestyle Blogger", 
                    "Food Creator", "Travel Vlogger", "Educational", "Entertainment",
                    "Business", "Music Artist", "Fashion", "Gaming", "Comedy"
                ],
                "release": [
                    "", "RENEGADE PIPELINE", "THE STATE OF THE WORLD", "THE SCALE"
                ],
                "reel_type": [
                    "", "Tutorial", "Product Review", "Behind the Scenes", "Q&A",
                    "Transformation", "Day in Life", "Tips & Tricks", "Unboxing",
                    "Comparison", "Story Time", "Challenge", "Trend", "Educational"
                ],
                "aspect_ratio": [
                    "", "9:16", "16:9", "1:1", "4:5", "5:4", "3:4", "4:3", "21:9", "2:3", "unknown"
                ],
                # visual_template removed from schema
            },
            "last_csv_path": "",
            "window_settings": {
                "geometry": "1600x800",
                "column_widths": {
                    "Reel ID": 140,
                    "Persona": 130,
                    "Release": 100,
                    "Reel Type": 130,
                    "Clip Filename": 180,
                    "Caption": 200,
                    "Aspect Ratio": 90,
                    "FilePath": 350
                }
            },
            "app_settings": {
                "auto_load_last_csv": True,
                "auto_save_config": True,
                "show_file_stats": True
            },
            "default_metadata": {
                "persona": "",
                "release": "RENEGADE PIPELINE",
                "reel_type": "",
                "caption_template": ""
            },
            "file_organization": {
                "master_export_folder": self._get_default_export_folder(),
                "auto_organize_enabled": True,
                "safe_testing_mode": True,
                "overwrite_protection": True,
                "preserve_original_files": True
            },
            "version_history": []
        }
    
    def _get_default_export_folder(self):
        """Get default export folder using centralized configuration."""
        if CORE_AVAILABLE:
            try:
                return str(resolve_output_path())
            except Exception as e:
                safe_print(f"Warning: Could not resolve default export folder: {e}")
        
        # Fallback to empty string (user will need to configure)
        return ""
    
    def deduplicate_dropdowns(self):
        """Remove duplicate (case-insensitive) values from dropdown lists and save if changed."""
        try:
            cleaned = False
            for key, values in self.config.get("dropdown_values", {}).items():
                seen = set()
                unique_values = []
                for v in values:
                    norm = v.strip().lower()
                    if norm not in seen:
                        seen.add(norm)
                        unique_values.append(v)
                if len(unique_values) != len(values):
                    self.config["dropdown_values"][key] = unique_values
                    cleaned = True
            if cleaned and self.config.get("app_settings", {}).get("auto_save_config", True):
                self.save_config()
                safe_print("[CONFIG] Duplicate dropdown entries removed and config saved")
        except Exception as e:
            safe_print(f"Error deduplicating dropdown values: {e}")

    def save_config(self, config=None):
        """Save configuration to JSON file."""
        try:
            config_to_save = config if config is not None else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
        except Exception as e:
            safe_print(f"Error saving config: {e}")
    
    def get_dropdown_values(self, dropdown_type):
        """Get dropdown values for a specific type."""
        return self.config.get("dropdown_values", {}).get(dropdown_type, [])
    
    def remove_dropdown_value(self, dropdown_type, value):
        """Remove a value from a dropdown list if it exists."""
        try:
            if dropdown_type in self.config["dropdown_values"]:
                values = self.config["dropdown_values"][dropdown_type]
                if value in values:
                    old_values = values.copy()
                    values.remove(value)
                    
                    # Add version tracking for dropdown changes
                    self._add_dropdown_version_entry(dropdown_type, "removed", old_values, values.copy(), value)
                    
                    if self.config.get("app_settings", {}).get("auto_save_config", True):
                        self.save_config()
                    return True
            return False
        except Exception as e:
            safe_print(f"Error removing dropdown value: {e}")
            return False
    
    def add_dropdown_value(self, dropdown_type, value):
        """Add a new value to a dropdown list if it doesn't exist."""
        try:
            if dropdown_type not in self.config["dropdown_values"]:
                self.config["dropdown_values"][dropdown_type] = []
                
            values = self.config["dropdown_values"][dropdown_type]
            if value and value not in values:
                old_values = values.copy()
                values.append(value)
                
                # Add version tracking for dropdown changes
                self._add_dropdown_version_entry(dropdown_type, "added", old_values, values.copy(), value)
                
                if self.config.get("app_settings", {}).get("auto_save_config", True):
                    self.save_config()
                return True
            return False
        except Exception as e:
            safe_print(f"Error adding dropdown value: {e}")
            return False
    
    def set_last_csv_path(self, path):
        """Set the last loaded CSV path."""
        self.config["last_csv_path"] = path
        if self.config.get("app_settings", {}).get("auto_save_config", True):
            self.save_config()
    
    def get_last_csv_path(self):
        """Get the last loaded CSV path."""
        return self.config.get("last_csv_path", "")
    
    def export_dropdown_audit(self, output_file=None):
        """Export a comprehensive audit of all dropdown changes."""
        try:
            if not output_file:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"dropdown_audit_{timestamp}.json"
            
            audit_data = {
                "export_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "current_dropdown_values": self.config.get("dropdown_values", {}),
                "current_default_metadata": self.config.get("default_metadata", {}),
                "change_history": self.get_dropdown_change_history(),
                "metadata_history": self.get_version_history(filter_type="default_metadata")
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(audit_data, f, indent=4, ensure_ascii=False)
            
            safe_print(f"[CONFIG] Exported dropdown audit to: {output_file}")
            return output_file
            
        except Exception as e:
            safe_print(f"Error exporting dropdown audit: {e}")
            return None
    
    def should_auto_load_csv(self):
        """Check if auto-loading CSV is enabled."""
        return self.config.get("app_settings", {}).get("auto_load_last_csv", True)
    
    def get_default_metadata(self):
        """Get default metadata values."""
        return self.config.get("default_metadata", {
            "persona": "",
            "release": "RENEGADE PIPELINE",
            "reel_type": "",
            "caption_template": ""
        })
    
    def set_default_metadata(self, defaults):
        """Set default metadata values with version tracking."""
        try:
            # Get current defaults for comparison
            current_defaults = self.get_default_metadata()
            
            # Update defaults
            self.config["default_metadata"] = defaults
            
            # Add version history entry
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            version_entry = {
                "timestamp": timestamp,
                "action": "default_metadata_updated",
                "previous": current_defaults,
                "new": defaults
            }
            
            if "version_history" not in self.config:
                self.config["version_history"] = []
            
            self.config["version_history"].append(version_entry)
            
            # Keep only last 50 version entries to prevent file bloat
            if len(self.config["version_history"]) > 50:
                self.config["version_history"] = self.config["version_history"][-50:]
            
            # Save config
            if self.config.get("app_settings", {}).get("auto_save_config", True):
                self.save_config()
                safe_print(f"[CONFIG] Default metadata updated at {timestamp}")
            
            return True
        except Exception as e:
            safe_print(f"Error setting default metadata: {e}")
            return False
    
    def _add_dropdown_version_entry(self, dropdown_type, action, old_values, new_values, changed_value=None):
        """Add a version history entry for dropdown changes."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            version_entry = {
                "timestamp": timestamp,
                "action": f"dropdown_{action}",
                "dropdown_type": dropdown_type,
                "changed_value": changed_value,
                "previous_values": old_values,
                "new_values": new_values
            }
            
            if "version_history" not in self.config:
                self.config["version_history"] = []
            
            self.config["version_history"].append(version_entry)
            
            # Keep only last 100 version entries to prevent file bloat
            if len(self.config["version_history"]) > 100:
                self.config["version_history"] = self.config["version_history"][-100:]
            
            safe_print(f"[CONFIG] {action.title()} {dropdown_type} value: {changed_value} at {timestamp}")
            
        except Exception as e:
            safe_print(f"Error adding dropdown version entry: {e}")
    
    def get_version_history(self, limit=10, filter_type=None):
        """Get recent version history entries with optional filtering."""
        history = self.config.get("version_history", [])
        
        if filter_type:
            # Filter by action type (e.g., 'dropdown_added', 'default_metadata_updated')
            history = [entry for entry in history if entry.get("action", "").startswith(filter_type)]
        
        return history[-limit:] if limit else history
    
    def get_dropdown_change_history(self, dropdown_type=None, limit=20):
        """Get history of dropdown changes with optional filtering by dropdown type."""
        history = self.config.get("version_history", [])
        
        # Filter for dropdown-related changes
        dropdown_history = [
            entry for entry in history 
            if entry.get("action", "").startswith("dropdown_")
        ]
        
        # Further filter by dropdown type if specified
        if dropdown_type:
            dropdown_history = [
                entry for entry in dropdown_history
                if entry.get("dropdown_type") == dropdown_type
            ]
        
        return dropdown_history[-limit:] if limit else dropdown_history
    
    def get_file_organization_settings(self):
        """Get file organization settings."""
        return self.config.get("file_organization", {
            "master_export_folder": "",
            "auto_organize_enabled": True,
            "safe_testing_mode": True,
            "overwrite_protection": True,
            "preserve_original_files": True
        })
    
    def set_master_export_folder(self, folder_path):
        """Set the master export folder path."""
        try:
            if "file_organization" not in self.config:
                self.config["file_organization"] = self.get_default_config()["file_organization"]
            
            old_path = self.config["file_organization"].get("master_export_folder", "")
            self.config["file_organization"]["master_export_folder"] = folder_path
            
            # Add version history entry
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            version_entry = {
                "timestamp": timestamp,
                "action": "export_folder_updated",
                "previous": old_path,
                "new": folder_path
            }
            
            if "version_history" not in self.config:
                self.config["version_history"] = []
            
            self.config["version_history"].append(version_entry)
            
            # Keep only last 100 version entries
            if len(self.config["version_history"]) > 100:
                self.config["version_history"] = self.config["version_history"][-100:]
            
            # Save config
            if self.config.get("app_settings", {}).get("auto_save_config", True):
                self.save_config()
                safe_print(f"[CONFIG] Master export folder updated: {folder_path}")
            
            return True
        except Exception as e:
            safe_print(f"Error setting master export folder: {e}")
            return False
    
    def get_master_export_folder(self):
        """Get the master export folder path."""
        settings = self.get_file_organization_settings()
        return settings.get("master_export_folder", "")
    
    def update_file_organization_setting(self, setting_name, value):
        """Update a specific file organization setting."""
        try:
            if "file_organization" not in self.config:
                self.config["file_organization"] = self.get_default_config()["file_organization"]
            
            old_value = self.config["file_organization"].get(setting_name)
            self.config["file_organization"][setting_name] = value
            
            # Add version history entry
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            version_entry = {
                "timestamp": timestamp,
                "action": f"file_org_setting_updated",
                "setting": setting_name,
                "previous": old_value,
                "new": value
            }
            
            if "version_history" not in self.config:
                self.config["version_history"] = []
            
            self.config["version_history"].append(version_entry)
            
            # Save config
            if self.config.get("app_settings", {}).get("auto_save_config", True):
                self.save_config()
                safe_print(f"[CONFIG] File organization setting updated: {setting_name} = {value}")
            
            return True
        except Exception as e:
            safe_print(f"Error updating file organization setting: {e}")
            return False