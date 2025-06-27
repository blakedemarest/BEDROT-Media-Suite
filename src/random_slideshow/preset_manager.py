# -*- coding: utf-8 -*-
"""
Preset Manager for Random Slideshow Generator.

Provides comprehensive preset management functionality including:
- Creating, loading, saving, and deleting presets
- Storing complete session states (folders, settings, etc.)
- Export/import presets to share configurations
- Default presets for common workflows
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class PresetManager:
    """
    Manages presets for the Random Slideshow Generator.
    Each preset contains a complete session configuration.
    """
    
    def __init__(self, presets_file="config/slideshow_presets.json"):
        self.presets_file = presets_file
        self.presets_dir = os.path.dirname(presets_file)
        self._ensure_presets_dir()
        self.presets = self._load_presets()
        self._ensure_default_presets()
    
    def _ensure_presets_dir(self):
        """Ensure the presets directory exists."""
        if self.presets_dir and not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir, exist_ok=True)
    
    def _load_presets(self) -> Dict[str, Dict]:
        """Load presets from JSON file."""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure it's a dict with a presets key
                    if isinstance(data, dict) and "presets" in data:
                        return data
                    else:
                        # Migrate old format
                        return {"presets": data if isinstance(data, dict) else {}}
            except Exception as e:
                print(f"Warning: Could not load presets file {self.presets_file}. Error: {e}")
        return {"presets": {}, "last_used": None}
    
    def _save_presets(self):
        """Save presets to JSON file."""
        try:
            with open(self.presets_file, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=4)
        except Exception as e:
            print(f"Error saving presets file {self.presets_file}: {e}")
            raise
    
    def _ensure_default_presets(self):
        """Ensure default presets exist."""
        default_presets = {
            "Quick Portrait": {
                "description": "Quick generation for portrait videos (9:16)",
                "image_folder": "",
                "output_folder": "",
                "aspect_ratio": "9:16",
                "batch_settings": {
                    "max_workers": 2,
                    "auto_start": True
                },
                "is_default": True,
                "created_at": datetime.now().isoformat()
            },
            "Quick Landscape": {
                "description": "Quick generation for landscape videos (16:9)",
                "image_folder": "",
                "output_folder": "",
                "aspect_ratio": "16:9",
                "batch_settings": {
                    "max_workers": 2,
                    "auto_start": True
                },
                "is_default": True,
                "created_at": datetime.now().isoformat()
            },
            "High Performance": {
                "description": "Maximum performance with all CPU cores",
                "image_folder": "",
                "output_folder": "",
                "aspect_ratio": "16:9",
                "batch_settings": {
                    "max_workers": os.cpu_count() or 4,
                    "max_memory_mb": 4096,
                    "cache_size": 200,
                    "auto_start": False
                },
                "is_default": True,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Add default presets if they don't exist
        if "presets" not in self.presets:
            self.presets["presets"] = {}
        
        for name, preset in default_presets.items():
            if name not in self.presets["presets"]:
                self.presets["presets"][name] = preset
        
        # Save if we added any defaults
        if any(name in default_presets for name in self.presets["presets"]):
            self._save_presets()
    
    def get_all_presets(self) -> Dict[str, Dict]:
        """Get all available presets."""
        return self.presets.get("presets", {}).copy()
    
    def get_preset_names(self) -> List[str]:
        """Get list of preset names."""
        return list(self.presets.get("presets", {}).keys())
    
    def get_preset(self, name: str) -> Optional[Dict]:
        """Get a specific preset by name."""
        return self.presets.get("presets", {}).get(name)
    
    def save_preset(self, name: str, config: Dict, description: str = "") -> bool:
        """
        Save a preset with the given configuration.
        
        Args:
            name: Preset name
            config: Configuration dictionary containing all settings
            description: Optional description of the preset
            
        Returns:
            bool: True if successful
        """
        try:
            preset_data = config.copy()
            preset_data.update({
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "is_default": False
            })
            
            # Check if updating existing preset
            if name in self.presets.get("presets", {}):
                # Preserve created_at and is_default flag
                existing = self.presets["presets"][name]
                preset_data["created_at"] = existing.get("created_at", preset_data["created_at"])
                preset_data["is_default"] = existing.get("is_default", False)
            
            if "presets" not in self.presets:
                self.presets["presets"] = {}
            
            self.presets["presets"][name] = preset_data
            self._save_presets()
            return True
            
        except Exception as e:
            print(f"Error saving preset '{name}': {e}")
            return False
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset by name.
        
        Args:
            name: Preset name to delete
            
        Returns:
            bool: True if successful
        """
        try:
            if name in self.presets.get("presets", {}):
                # Don't delete default presets
                if self.presets["presets"][name].get("is_default", False):
                    print(f"Cannot delete default preset '{name}'")
                    return False
                
                del self.presets["presets"][name]
                
                # Clear last_used if it was this preset
                if self.presets.get("last_used") == name:
                    self.presets["last_used"] = None
                
                self._save_presets()
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting preset '{name}': {e}")
            return False
    
    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        Rename a preset.
        
        Args:
            old_name: Current preset name
            new_name: New preset name
            
        Returns:
            bool: True if successful
        """
        try:
            if old_name in self.presets.get("presets", {}) and new_name not in self.presets["presets"]:
                # Don't rename default presets
                if self.presets["presets"][old_name].get("is_default", False):
                    print(f"Cannot rename default preset '{old_name}'")
                    return False
                
                self.presets["presets"][new_name] = self.presets["presets"][old_name]
                self.presets["presets"][new_name]["name"] = new_name
                self.presets["presets"][new_name]["modified_at"] = datetime.now().isoformat()
                del self.presets["presets"][old_name]
                
                # Update last_used if necessary
                if self.presets.get("last_used") == old_name:
                    self.presets["last_used"] = new_name
                
                self._save_presets()
                return True
            return False
            
        except Exception as e:
            print(f"Error renaming preset '{old_name}' to '{new_name}': {e}")
            return False
    
    def duplicate_preset(self, source_name: str, new_name: str) -> bool:
        """
        Create a duplicate of an existing preset.
        
        Args:
            source_name: Name of preset to duplicate
            new_name: Name for the duplicate
            
        Returns:
            bool: True if successful
        """
        try:
            source_preset = self.get_preset(source_name)
            if source_preset and new_name not in self.presets.get("presets", {}):
                duplicate = source_preset.copy()
                duplicate["name"] = new_name
                duplicate["description"] = f"Copy of {source_name}"
                duplicate["created_at"] = datetime.now().isoformat()
                duplicate["modified_at"] = datetime.now().isoformat()
                duplicate["is_default"] = False
                
                self.presets["presets"][new_name] = duplicate
                self._save_presets()
                return True
            return False
            
        except Exception as e:
            print(f"Error duplicating preset '{source_name}': {e}")
            return False
    
    def export_preset(self, name: str, export_path: str) -> bool:
        """
        Export a preset to a file.
        
        Args:
            name: Preset name to export
            export_path: Path to export file
            
        Returns:
            bool: True if successful
        """
        try:
            preset = self.get_preset(name)
            if preset:
                export_data = {
                    "slideshow_preset": {
                        "version": "1.0",
                        "exported_at": datetime.now().isoformat(),
                        "preset": preset
                    }
                }
                
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=4)
                return True
            return False
            
        except Exception as e:
            print(f"Error exporting preset '{name}': {e}")
            return False
    
    def import_preset(self, import_path: str, new_name: Optional[str] = None) -> Optional[str]:
        """
        Import a preset from a file.
        
        Args:
            import_path: Path to import file
            new_name: Optional new name for the preset
            
        Returns:
            str: Name of imported preset if successful, None otherwise
        """
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate format
            if not isinstance(data, dict) or "slideshow_preset" not in data:
                print("Invalid preset file format")
                return None
            
            preset_data = data["slideshow_preset"].get("preset")
            if not preset_data:
                print("No preset data found in file")
                return None
            
            # Determine preset name
            original_name = preset_data.get("name", "Imported Preset")
            preset_name = new_name or original_name
            
            # Handle name conflicts
            base_name = preset_name
            counter = 1
            while preset_name in self.presets.get("presets", {}):
                preset_name = f"{base_name} ({counter})"
                counter += 1
            
            # Import the preset
            preset_data["name"] = preset_name
            preset_data["imported_at"] = datetime.now().isoformat()
            preset_data["modified_at"] = datetime.now().isoformat()
            preset_data["is_default"] = False
            
            self.presets["presets"][preset_name] = preset_data
            self._save_presets()
            
            return preset_name
            
        except Exception as e:
            print(f"Error importing preset from '{import_path}': {e}")
            return None
    
    def get_last_used_preset(self) -> Optional[str]:
        """Get the name of the last used preset."""
        return self.presets.get("last_used")
    
    def set_last_used_preset(self, name: str):
        """Set the last used preset."""
        if name in self.presets.get("presets", {}):
            self.presets["last_used"] = name
            self._save_presets()
    
    def create_preset_from_config(self, config_manager, name: str, description: str = "") -> bool:
        """
        Create a preset from current ConfigManager state.
        
        Args:
            config_manager: ConfigManager instance
            name: Preset name
            description: Optional description
            
        Returns:
            bool: True if successful
        """
        try:
            # Extract all relevant settings
            preset_config = {
                "image_folder": config_manager.get_image_folder(),
                "output_folder": config_manager.get_output_folder(),
                "aspect_ratio": config_manager.get_aspect_ratio(),
                "batch_settings": config_manager.get_batch_settings(),
                # Add any other settings that should be saved
            }
            
            return self.save_preset(name, preset_config, description)
            
        except Exception as e:
            print(f"Error creating preset from config: {e}")
            return False
    
    def apply_preset_to_config(self, preset_name: str, config_manager) -> bool:
        """
        Apply a preset to ConfigManager.
        
        Args:
            preset_name: Name of preset to apply
            config_manager: ConfigManager instance
            
        Returns:
            bool: True if successful
        """
        try:
            preset = self.get_preset(preset_name)
            if not preset:
                return False
            
            # Apply settings
            if "image_folder" in preset:
                config_manager.set_image_folder(preset["image_folder"])
            if "output_folder" in preset:
                config_manager.set_output_folder(preset["output_folder"])
            if "aspect_ratio" in preset:
                config_manager.set_aspect_ratio(preset["aspect_ratio"])
            if "batch_settings" in preset:
                config_manager.set_batch_settings(preset["batch_settings"])
            
            # Update last used
            self.set_last_used_preset(preset_name)
            
            return True
            
        except Exception as e:
            print(f"Error applying preset '{preset_name}': {e}")
            return False