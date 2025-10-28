# -*- coding: utf-8 -*-
"""
Configuration Manager for Random Slideshow Generator.

Handles loading, saving, and managing configuration settings including:
- Image and output folder paths
- Aspect ratio preferences
- Application settings
- Batch processing settings
- Job presets and history
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class ConfigManager:
    """
    Manages configuration for the Random Slideshow Generator application.
    """
    
    def __init__(self, config_file="combined_random_config.json"):
        # Use absolute path to centralized config directory
        import os
        # Get project root (3 levels up from this file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_file = os.path.join(project_root, 'config', config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """Loads configuration from JSON file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}. Error: {e}")
                return {}
        return {}
    
    def save_config(self, config_data=None):
        """Saves configuration to JSON file."""
        try:
            data_to_save = config_data if config_data is not None else self.config
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save config file {self.config_file}. Error: {e}")
    
    def get_image_folder(self):
        """Get the configured image folder path."""
        return self.config.get("image_folder", os.getcwd())
    
    def set_image_folder(self, folder_path):
        """Set the image folder path and save config."""
        self.config["image_folder"] = folder_path
        self.save_config()
    
    def get_output_folder(self):
        """Get the configured output folder path."""
        default_output = os.path.join(os.path.expanduser("~"), "Videos", "RandomSlideshows")
        return self.config.get("output_folder", default_output)
    
    def set_output_folder(self, folder_path):
        """Set the output folder path and save config."""
        self.config["output_folder"] = folder_path
        self.save_config()
    
    def get_aspect_ratio(self):
        """Get the configured aspect ratio preference."""
        return self.config.get("aspect_ratio", "16:9")
    
    def set_aspect_ratio(self, aspect_ratio):
        """Set the aspect ratio preference and save config."""
        self.config["aspect_ratio"] = aspect_ratio
        self.save_config()
    
    def get_all_settings(self):
        """Get all configuration settings."""
        return self.config.copy()
    
    def update_settings(self, **kwargs):
        """Update multiple settings at once."""
        self.config.update(kwargs)
        self.save_config()
    
    # --- Batch Processing Settings ---
    
    def get_batch_settings(self) -> Dict:
        """Get batch processing settings."""
        return self.config.get("batch_settings", {
            "max_workers": 4,
            "max_memory_mb": 2048,
            "cache_size": 100,
            "auto_start": False,
            "preserve_completed_jobs": True,
            "completed_jobs_limit": 50
        })
    
    def set_batch_settings(self, settings: Dict):
        """Set batch processing settings."""
        self.config["batch_settings"] = settings
        self.save_config()
    
    def update_batch_setting(self, key: str, value):
        """Update a single batch setting."""
        batch_settings = self.get_batch_settings()
        batch_settings[key] = value
        self.set_batch_settings(batch_settings)
    
    # --- Job Presets ---
    
    def get_job_presets(self) -> List[Dict]:
        """Get saved job presets."""
        return self.config.get("job_presets", [])
    
    def add_job_preset(self, preset: Dict) -> bool:
        """Add a new job preset."""
        presets = self.get_job_presets()
        
        # Check if preset with same name exists
        for i, p in enumerate(presets):
            if p.get("name") == preset.get("name"):
                # Update existing preset
                presets[i] = preset
                self.config["job_presets"] = presets
                self.save_config()
                return True
        
        # Add new preset
        presets.append(preset)
        self.config["job_presets"] = presets
        self.save_config()
        return True
    
    def remove_job_preset(self, preset_name: str) -> bool:
        """Remove a job preset by name."""
        presets = self.get_job_presets()
        original_count = len(presets)
        
        presets = [p for p in presets if p.get("name") != preset_name]
        
        if len(presets) < original_count:
            self.config["job_presets"] = presets
            self.save_config()
            return True
        return False
    
    def get_job_preset(self, preset_name: str) -> Optional[Dict]:
        """Get a specific job preset by name."""
        presets = self.get_job_presets()
        for preset in presets:
            if preset.get("name") == preset_name:
                return preset
        return None
    
    # --- Job History ---
    
    def get_job_history(self) -> List[Dict]:
        """Get job history."""
        return self.config.get("job_history", [])
    
    def add_to_job_history(self, job_data: Dict):
        """Add a completed job to history."""
        history = self.get_job_history()
        
        # Add timestamp if not present
        if "completed_at" not in job_data:
            job_data["completed_at"] = datetime.now().isoformat()
        
        # Add to beginning of list (most recent first)
        history.insert(0, job_data)
        
        # Limit history size
        max_history = self.get_batch_settings().get("completed_jobs_limit", 50)
        history = history[:max_history]
        
        self.config["job_history"] = history
        self.save_config()
    
    def clear_job_history(self):
        """Clear all job history."""
        self.config["job_history"] = []
        self.save_config()
    
    def get_job_statistics(self) -> Dict:
        """Get statistics from job history."""
        history = self.get_job_history()
        
        if not history:
            return {
                "total_jobs": 0,
                "total_videos": 0,
                "success_rate": 0.0,
                "average_duration": 0.0
            }
        
        total_jobs = len(history)
        successful_jobs = sum(1 for job in history if job.get("status") == "completed")
        total_videos = sum(job.get("videos_completed", 0) for job in history)
        
        # Calculate average duration for completed jobs
        durations = []
        for job in history:
            if job.get("duration"):
                durations.append(job["duration"])
        
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "total_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "total_videos": total_videos,
            "success_rate": (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0,
            "average_duration": average_duration
        }
    
    # --- Queue State Persistence ---
    
    def save_queue_state(self, queue_data: Dict):
        """Save the current queue state for recovery."""
        self.config["queue_state"] = {
            "saved_at": datetime.now().isoformat(),
            "data": queue_data
        }
        self.save_config()
    
    def get_queue_state(self) -> Optional[Dict]:
        """Get saved queue state."""
        return self.config.get("queue_state")
    
    def clear_queue_state(self):
        """Clear saved queue state."""
        if "queue_state" in self.config:
            del self.config["queue_state"]
            self.save_config()