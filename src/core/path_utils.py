# -*- coding: utf-8 -*-
"""
Path resolution utilities for Bedrot Productions Media Tool Suite.

Provides secure, platform-agnostic path resolution with validation,
sanitization, and fallback mechanisms.
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional, List, Set
import re

from .env_loader import get_env_loader, get_bool_env_var


class PathResolver:
    """Handles secure path resolution and validation."""
    
    # Allowed file extensions by category
    ALLOWED_EXTENSIONS = {
        'video': {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.ts', '.flv'},
        'audio': {'.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
        'config': {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'},
        'data': {'.csv', '.txt', '.log', '.xml'},
        'executable': {'.py', '.bat', '.sh', '.exe'}
    }
    
    # Dangerous path patterns to block
    DANGEROUS_PATTERNS = [
        r'\.\./',  # Directory traversal
        r'\.\.\\',  # Directory traversal (Windows)
        r'\$\{',   # Environment variable injection
        r'`',      # Command injection
        r';',      # Command chaining
        r'\|',     # Pipe operations
        r'&(?![a-zA-Z0-9])',      # Background operations (but allow & in filenames)
    ]
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize path resolver.
        
        Args:
            project_root: Project root directory. If None, auto-detected.
        """
        self.env_loader = get_env_loader()
        self.project_root = project_root or self.env_loader.project_root
        self.enable_validation = get_bool_env_var('SLIDESHOW_ENABLE_PATH_VALIDATION', True)
        self.restrict_to_project = get_bool_env_var('SLIDESHOW_RESTRICT_TO_PROJECT', True)
        self.enable_extension_validation = get_bool_env_var('SLIDESHOW_ENABLE_EXTENSION_VALIDATION', True)
    
    def validate_path_security(self, path: Union[str, Path]) -> bool:
        """
        Validate path for security issues.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        if not self.enable_validation:
            return True
        
        path_str = str(path)
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                return False
        
        # Check for null bytes
        if '\x00' in path_str:
            return False
        
        # Check for excessive path length
        if len(path_str) > 260:  # Windows MAX_PATH limitation
            return False
        
        return True
    
    def sanitize_path(self, path: Union[str, Path]) -> Path:
        """
        Sanitize and normalize path.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized Path object
        """
        path_str = str(path).strip()
        
        # Remove null bytes
        path_str = path_str.replace('\x00', '')
        
        # Normalize path separators
        path_str = path_str.replace('\\', os.sep).replace('/', os.sep)
        
        # Remove duplicate separators
        while f'{os.sep}{os.sep}' in path_str:
            path_str = path_str.replace(f'{os.sep}{os.sep}', os.sep)
        
        # Create Path object for further normalization
        return Path(path_str).resolve()
    
    def resolve_project_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Resolve path relative to project root.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Absolute Path object
            
        Raises:
            ValueError: If path validation fails
        """
        if not self.validate_path_security(relative_path):
            raise ValueError(f"Path security validation failed: {relative_path}")
        
        # Handle absolute paths
        if Path(relative_path).is_absolute():
            if self.restrict_to_project:
                # Check if absolute path is within project
                try:
                    abs_path = Path(relative_path).resolve()
                    abs_path.relative_to(self.project_root)
                    return abs_path
                except ValueError:
                    raise ValueError(f"Absolute path outside project directory: {relative_path}")
            else:
                return self.sanitize_path(relative_path)
        
        # Resolve relative to project root
        full_path = self.project_root / relative_path
        return self.sanitize_path(full_path)
    
    def resolve_config_path(self, config_filename: str) -> Path:
        """
        Resolve configuration file path.
        
        Args:
            config_filename: Configuration file name
            
        Returns:
            Absolute path to configuration file
        """
        config_dir = self.env_loader.get_path_env_var('SLIDESHOW_CONFIG_DIR', 'config')
        return self.resolve_project_path(config_dir / config_filename)
    
    def resolve_script_path(self, script_path: str) -> Path:
        """
        Resolve application script path.
        
        Args:
            script_path: Script path (can be environment variable key or direct path)
            
        Returns:
            Absolute path to script
        """
        # Check if it's an environment variable
        if script_path.startswith('SLIDESHOW_') and script_path.endswith('_SCRIPT'):
            env_path = self.env_loader.get_env_var(script_path)
            if env_path:
                return self.resolve_project_path(env_path)
            
            # If env var not set, use default script paths
            script_defaults = {
                'SLIDESHOW_MEDIA_DOWNLOAD_SCRIPT': 'src/media_download_app.py',
                'SLIDESHOW_SNIPPET_REMIXER_SCRIPT': 'src/snippet_remixer.py',
                'SLIDESHOW_REEL_TRACKER_SCRIPT': 'src/reel_tracker_modular.py',
                'SLIDESHOW_EDITOR_SCRIPT': 'tools/slideshow_editor.py',
                'SLIDESHOW_RELEASE_CALENDAR_SCRIPT': 'src/release_calendar_modular.py',
                'SLIDESHOW_LYRIC_VIDEO_SCRIPT': 'src/lyric_video_uploader_modular.py',
                'SLIDESHOW_VIDEO_SPLITTER_SCRIPT': 'src/video_splitter_modular.py'
            }
            
            if script_path in script_defaults:
                return self.resolve_project_path(script_defaults[script_path])
        
        # Treat as direct path
        return self.resolve_project_path(script_path)
    
    def resolve_output_path(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Resolve output directory path with fallbacks.
        
        Args:
            output_path: Desired output path
            
        Returns:
            Absolute path to output directory
        """
        if output_path:
            # Expand home directory if needed
            expanded = os.path.expanduser(str(output_path))
            return self.sanitize_path(expanded)
        
        # Use default from environment
        default_output = self.env_loader.get_path_env_var(
            'SLIDESHOW_DEFAULT_OUTPUT_DIR', 
            '~/Videos/RandomSlideshows'
        )
        
        if default_output:
            return default_output
        
        # Final fallback
        return Path.home() / 'Videos' / 'RandomSlideshows'
    
    def validate_file_extension(self, file_path: Union[str, Path], 
                              allowed_categories: Optional[List[str]] = None) -> bool:
        """
        Validate file extension against allowed categories.
        
        Args:
            file_path: File path to validate
            allowed_categories: List of allowed categories (e.g., ['video', 'audio'])
            
        Returns:
            True if extension is allowed, False otherwise
        """
        if not self.enable_extension_validation or not allowed_categories:
            return True
        
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        # Check against allowed categories
        for category in allowed_categories:
            if category in self.ALLOWED_EXTENSIONS:
                if extension in self.ALLOWED_EXTENSIONS[category]:
                    return True
        
        return False
    
    def ensure_directory(self, dir_path: Union[str, Path], 
                        create_parents: bool = True) -> Path:
        """
        Ensure directory exists, creating it if necessary.
        
        Args:
            dir_path: Directory path
            create_parents: Whether to create parent directories
            
        Returns:
            Absolute path to directory
            
        Raises:
            OSError: If directory cannot be created
        """
        resolved_path = self.resolve_project_path(dir_path)
        
        try:
            resolved_path.mkdir(parents=create_parents, exist_ok=True)
            return resolved_path
        except OSError as e:
            raise OSError(f"Cannot create directory {resolved_path}: {e}")
    
    def get_temp_directory(self) -> Path:
        """
        Get temporary directory path.
        
        Returns:
            Absolute path to temporary directory
        """
        temp_dir = self.env_loader.get_path_env_var('SLIDESHOW_TEMP_DIR', 'temp')
        return self.ensure_directory(temp_dir)
    
    def get_log_directory(self) -> Path:
        """
        Get log directory path.
        
        Returns:
            Absolute path to log directory
        """
        log_dir = self.env_loader.get_path_env_var('SLIDESHOW_LOG_DIR', 'logs')
        return self.ensure_directory(log_dir)


# Global path resolver instance
_path_resolver: Optional[PathResolver] = None


def get_path_resolver() -> PathResolver:
    """Get the global path resolver instance."""
    global _path_resolver
    if _path_resolver is None:
        _path_resolver = PathResolver()
    return _path_resolver


def resolve_path(path: Union[str, Path]) -> Path:
    """Resolve path using the global resolver."""
    return get_path_resolver().resolve_project_path(path)


def resolve_config_path(config_filename: str) -> Path:
    """Resolve configuration path using the global resolver."""
    return get_path_resolver().resolve_config_path(config_filename)


def resolve_script_path(script_path: str) -> Path:
    """Resolve script path using the global resolver."""
    return get_path_resolver().resolve_script_path(script_path)


def resolve_output_path(output_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve output path using the global resolver."""
    return get_path_resolver().resolve_output_path(output_path)


def validate_path(path: Union[str, Path]) -> bool:
    """Validate path security using the global resolver."""
    return get_path_resolver().validate_path_security(path)


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """Ensure directory exists using the global resolver."""
    return get_path_resolver().ensure_directory(dir_path)
