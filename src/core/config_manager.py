# -*- coding: utf-8 -*-
"""
Centralized configuration manager for Bedrot Productions Media Tool Suite.

Provides unified configuration management with environment variable support,
validation, and fallback mechanisms.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from .env_loader import get_env_loader, get_env_var, get_bool_env_var, get_int_env_var
from .path_utils import get_path_resolver, validate_path


class ConfigManager:
    """Centralized configuration manager with environment variable support."""
    
    def __init__(self, config_name: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_name: Name of the configuration (used for environment variable lookup)
        """
        self.config_name = config_name
        self.env_loader = get_env_loader()
        self.path_resolver = get_path_resolver()
        self._config_cache: Dict[str, Any] = {}
        self._loaded_configs: Dict[str, Dict[str, Any]] = {}
        
        # Load environment variables
        self.env_loader.load_environment()
    
    def _get_config_file_path(self, config_filename: str) -> Path:
        """
        Get the full path to a configuration file.
        
        Args:
            config_filename: Name of the configuration file
            
        Returns:
            Absolute path to configuration file
        """
        return self.path_resolver.resolve_config_path(config_filename)
    
    def _get_default_config_for_app(self, app_name: str) -> Dict[str, Any]:
        """
        Get default configuration for a specific application.
        
        Args:
            app_name: Application name
            
        Returns:
            Default configuration dictionary
        """
        defaults = {
            'media_download': {
                'output_directory': str(self.path_resolver.resolve_output_path()),
                'format': 'mp4',
                'quality': get_env_var('SLIDESHOW_DEFAULT_QUALITY', '720p'),
                'remove_audio': False,
                'adjust_aspect_ratio': False,
                'target_aspect_ratio': get_env_var('SLIDESHOW_DEFAULT_ASPECT_RATIO', '16:9'),
                'time_cutting_enabled': False,
                'start_time': '',
                'end_time': '',
                'video_chopping_enabled': False,
                'chop_duration': 60
            },
            'snippet_remixer': {
                'input_files': [],
                'output_directory': str(self.path_resolver.resolve_output_path()),
                'output_filename': 'remix',
                'duration_seconds': 60,
                'bpm_mode': False,
                'bpm': 120,
                'snippets_per_beat': 4,
                'aspect_ratio': get_env_var('SLIDESHOW_DEFAULT_ASPECT_RATIO', '16:9'),
                'temp_directory': str(self.path_resolver.get_temp_directory())
            },
            'reel_tracker': {
                'csv_file_path': '',
                'auto_save_enabled': True,
                'auto_save_interval': 300,
                'dropdown_values': {
                    'persona': [],
                    'release': [],
                    'reel_type': []
                },
                'default_metadata': {},
                'file_organization': {
                    'master_export_folder': str(self.path_resolver.resolve_output_path()),
                    'auto_organize_enabled': True,
                    'safe_testing_mode': True,
                    'overwrite_protection': True,
                    'preserve_original_files': True
                },
                'version_history': []
            },
            'bedrot_media_suite': {
                'output_directory': str(self.path_resolver.resolve_output_path()),
                'aspect_ratio': get_env_var('SLIDESHOW_DEFAULT_ASPECT_RATIO', '16:9'),
                'duration_per_image': 3.0,
                'transition_duration': 0.5,
                'recent_folders': []
            },
            'lyric_video': {
                'project_root': str(self.path_resolver.resolve_output_path('lyric_video_projects')),
                'stems': {
                    'engine': 'demucs',
                    'model': 'htdemucs_ft',
                    'cache_enabled': True,
                    'overwrite_existing': False,
                    'chunk_size_seconds': 60,
                    'gpu_required': True
                },
                'stt': {
                    'provider': 'elevenlabs',
                    'language': 'en',
                    'model_id': 'eleven_multilingual_v2',
                    'base_url': 'https://api.elevenlabs.io',
                    'api_key_env': 'ELEVENLABS_API_KEY',
                    'request_timeout': 60,
                    'max_retries': 2
                },
                'tempo': {
                    'default_bpm': 120.0,
                    'default_offset_seconds': 0.0,
                    'allow_tempo_map': True,
                    'tempo_map_pattern': '*.csv',
                    'snap_words_to_beats': False
                },
                'render': {
                    'preset': 'default',
                    'encoder': 'h264_nvenc',
                    'video_bitrate': '25M',
                    'audio_bitrate': '320k',
                    'include_ass': True,
                    'include_words_srt': True,
                    'max_render_duration_minutes': 15
                },
                'render_presets': {
                    'default': {
                        'description': 'Looped background with overlaid ASS subtitles.',
                        'background': 'backgrounds/default_loop.mp4',
                        'font': 'fonts/default.ttf',
                        'font_size': 48,
                        'font_color': '#FFFFFF',
                        'outline_color': '#000000',
                        'shadow_color': '#000000'
                    }
                },
                'exports': {
                    'bundle_metadata': True,
                    'bundle_sections': True,
                    'ready_for_upload_dirname': 'ready_for_upload',
                    'snippet_bridge_dirname': 'snippet_bridge',
                    'metadata_template': 'metadata_template.json'
                },
                'logging': {
                    'level': 'INFO',
                    'propagate_to_root': False
                }
            }
        }
        
        return defaults.get(app_name, {})
    
    def load_config(self, config_filename: str, app_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file with fallbacks.
        
        Args:
            config_filename: Name of configuration file
            app_name: Application name for default config lookup
            
        Returns:
            Configuration dictionary
        """
        # Check cache first
        cache_key = f"{config_filename}:{app_name}"
        if cache_key in self._loaded_configs:
            return self._loaded_configs[cache_key]
        
        config_path = self._get_config_file_path(config_filename)
        
        # Start with default configuration
        if app_name:
            config = self._get_default_config_for_app(app_name)
        else:
            config = {}
        
        # Load from file if it exists
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    
                # Merge file config with defaults
                config.update(file_config)
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Error loading config file {config_path}: {e}")
                print("Using default configuration")
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config, app_name)
        
        # Cache the loaded configuration
        self._loaded_configs[cache_key] = config
        
        return config
    
    def save_config(self, config: Dict[str, Any], config_filename: str) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            config_filename: Name of configuration file
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_path = self._get_config_file_path(config_filename)
            
            # Ensure config directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            config_to_save = config.copy()
            config_to_save['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            # Save with pretty formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            # Update cache
            cache_key = f"{config_filename}:unknown"
            self._loaded_configs[cache_key] = config
            
            return True
            
        except (IOError, OSError) as e:
            print(f"Error saving config file {config_filename}: {e}")
            return False
    
    def _apply_env_overrides(self, config: Dict[str, Any], app_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: Base configuration
            app_name: Application name for env var lookup
            
        Returns:
            Configuration with environment overrides applied
        """
        if not app_name:
            return config
        
        # Define environment variable mappings
        env_mappings = {
            'media_download': {
                'output_directory': 'SLIDESHOW_DEFAULT_DOWNLOADS_DIR',
                'quality': 'SLIDESHOW_DEFAULT_QUALITY',
                'target_aspect_ratio': 'SLIDESHOW_DEFAULT_ASPECT_RATIO'
            },
            'snippet_remixer': {
                'output_directory': 'SLIDESHOW_DEFAULT_EXPORTS_DIR',
                'aspect_ratio': 'SLIDESHOW_DEFAULT_ASPECT_RATIO',
                'temp_directory': 'SLIDESHOW_TEMP_DIR'
            },
            'reel_tracker': {
                'file_organization.master_export_folder': 'SLIDESHOW_DEFAULT_EXPORTS_DIR'
            },
            'bedrot_media_suite': {
                'output_directory': 'SLIDESHOW_DEFAULT_OUTPUT_DIR',
                'aspect_ratio': 'SLIDESHOW_DEFAULT_ASPECT_RATIO'
            },
            'lyric_video': {
                'project_root': 'SLIDESHOW_LYRIC_VIDEO_PROJECT_ROOT',
                'render.output_directory': 'SLIDESHOW_DEFAULT_EXPORTS_DIR'
            }
        }
        
        if app_name in env_mappings:
            for config_key, env_var in env_mappings[app_name].items():
                env_value = get_env_var(env_var)
                if env_value:
                    # Handle nested keys
                    if '.' in config_key:
                        keys = config_key.split('.')
                        current = config
                        for key in keys[:-1]:
                            if key not in current:
                                current[key] = {}
                            current = current[key]
                        current[keys[-1]] = str(self.path_resolver.resolve_output_path(env_value))
                    else:
                        if config_key.endswith('_directory'):
                            config[config_key] = str(self.path_resolver.resolve_output_path(env_value))
                        else:
                            config[config_key] = env_value
        
        return config
    
    def get_script_path(self, script_key: str) -> Path:
        """
        Get path to application script.
        
        Args:
            script_key: Script key (e.g., 'media_download', 'snippet_remixer')
            
        Returns:
            Absolute path to script
        """
        env_var = f"SLIDESHOW_{script_key.upper()}_SCRIPT"
        return self.path_resolver.resolve_script_path(env_var)
    
    def get_external_tool_path(self, tool_name: str) -> Optional[str]:
        """
        Get path to external tool (e.g., ffmpeg, yt-dlp).
        
        Args:
            tool_name: Tool name
            
        Returns:
            Path to tool or None if not configured
        """
        env_var = f"SLIDESHOW_{tool_name.upper()}_PATH"
        tool_path = get_env_var(env_var)
        
        if tool_path and validate_path(tool_path):
            return tool_path
        
        return None
    
    def validate_config(self, config: Dict[str, Any], app_name: str) -> List[str]:
        """
        Validate configuration for an application.
        
        Args:
            config: Configuration to validate
            app_name: Application name
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Common validations
        if 'output_directory' in config:
            if not validate_path(config['output_directory']):
                errors.append(f"Invalid output directory path: {config['output_directory']}")
        
        # App-specific validations
        if app_name == 'media_download':
            if 'format' in config and config['format'] not in ['mp4', 'mp3', 'wav']:
                errors.append(f"Invalid format: {config['format']}")
        
        elif app_name == 'snippet_remixer':
            if 'duration_seconds' in config:
                try:
                    duration = float(config['duration_seconds'])
                    if duration <= 0:
                        errors.append("Duration must be positive")
                except ValueError:
                    errors.append("Duration must be a valid number")
        
        return errors


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_app_config(app_name: str, config_filename: str) -> Dict[str, Any]:
    """Load application configuration using the global manager."""
    return get_config_manager().load_config(config_filename, app_name)


def save_app_config(config: Dict[str, Any], config_filename: str) -> bool:
    """Save application configuration using the global manager."""
    return get_config_manager().save_config(config, config_filename)
