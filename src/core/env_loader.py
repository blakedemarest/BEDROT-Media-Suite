# -*- coding: utf-8 -*-
"""
Environment variable loader for Bedrot Productions Media Tool Suite.

Provides secure loading of environment variables with fallback defaults
and validation. Supports both .env files and system environment variables.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Union, Any


class EnvironmentLoader:
    """Handles loading and validation of environment variables."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize environment loader.
        
        Args:
            project_root: Project root directory. If None, auto-detected.
        """
        self.project_root = project_root or self._detect_project_root()
        self.env_file = self.project_root / ".env"
        self._loaded = False
        self._env_cache: Dict[str, str] = {}
    
    def _detect_project_root(self) -> Path:
        """Auto-detect project root directory."""
        # Start from current file location and search upward
        current = Path(__file__).resolve().parent
        
        # Look for project indicators
        indicators = [
            "launcher.py",
            "requirements.txt", 
            ".env.example",
            "README.md"
        ]
        
        while current != current.parent:
            if any((current / indicator).exists() for indicator in indicators):
                return current
            current = current.parent
        
        # Fallback to current working directory
        return Path.cwd()
    
    def load_env_file(self) -> Dict[str, str]:
        """
        Load environment variables from .env file.
        
        Returns:
            Dictionary of environment variables loaded from file.
        """
        env_vars = {}
        
        if not self.env_file.exists():
            return env_vars
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
                    else:
                        print(f"Warning: Invalid format in .env file at line {line_num}: {line}")
        
        except Exception as e:
            print(f"Warning: Error reading .env file: {e}")
        
        return env_vars
    
    def load_environment(self) -> None:
        """Load environment variables from .env file into os.environ."""
        if self._loaded:
            return
        
        env_vars = self.load_env_file()
        
        # Set environment variables, but don't override existing ones
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
                self._env_cache[key] = value
        
        self._loaded = True
    
    def get_env_var(self, key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """
        Get environment variable with validation.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether the variable is required
            
        Returns:
            Environment variable value or default
            
        Raises:
            ValueError: If required variable is not found
        """
        self.load_environment()
        
        value = os.environ.get(key, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable '{key}' not found")
        
        return value
    
    def get_bool_env_var(self, key: str, default: bool = False) -> bool:
        """
        Get boolean environment variable.
        
        Args:
            key: Environment variable name
            default: Default boolean value
            
        Returns:
            Boolean value
        """
        value = self.get_env_var(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_int_env_var(self, key: str, default: int = 0) -> int:
        """
        Get integer environment variable.
        
        Args:
            key: Environment variable name
            default: Default integer value
            
        Returns:
            Integer value
        """
        value = self.get_env_var(key, str(default))
        try:
            return int(value)
        except ValueError:
            print(f"Warning: Invalid integer value for {key}: {value}, using default: {default}")
            return default
    
    def get_path_env_var(self, key: str, default: Optional[Union[str, Path]] = None) -> Optional[Path]:
        """
        Get path environment variable with expansion.
        
        Args:
            key: Environment variable name
            default: Default path value
            
        Returns:
            Path object or None
        """
        value = self.get_env_var(key, str(default) if default else None)
        
        if value is None:
            return None
        
        # Expand user home directory
        expanded = os.path.expanduser(value)
        
        # Convert to absolute path if relative
        if not os.path.isabs(expanded):
            expanded = str(self.project_root / expanded)
        
        return Path(expanded)


# Global environment loader instance
_env_loader: Optional[EnvironmentLoader] = None


def get_env_loader() -> EnvironmentLoader:
    """Get the global environment loader instance."""
    global _env_loader
    if _env_loader is None:
        _env_loader = EnvironmentLoader()
    return _env_loader


def load_environment() -> None:
    """Load environment variables using the global loader."""
    get_env_loader().load_environment()


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get environment variable using the global loader."""
    return get_env_loader().get_env_var(key, default, required)


def get_bool_env_var(key: str, default: bool = False) -> bool:
    """Get boolean environment variable using the global loader."""
    return get_env_loader().get_bool_env_var(key, default)


def get_int_env_var(key: str, default: int = 0) -> int:
    """Get integer environment variable using the global loader."""
    return get_env_loader().get_int_env_var(key, default)


def get_path_env_var(key: str, default: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Get path environment variable using the global loader."""
    return get_env_loader().get_path_env_var(key, default)