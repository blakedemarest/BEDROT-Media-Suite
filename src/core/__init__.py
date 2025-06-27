# -*- coding: utf-8 -*-
"""
Core utilities package for Bedrot Productions Media Tool Suite.

This package provides centralized configuration management,
path resolution, and common utilities shared across all applications.
"""

from .config_manager import ConfigManager, get_config_manager
from .path_utils import PathResolver, resolve_path, validate_path
from .env_loader import load_environment

__version__ = "1.0.0"
__author__ = "Bedrot Productions"

__all__ = [
    "ConfigManager",
    "get_config_manager", 
    "PathResolver",
    "resolve_path",
    "validate_path",
    "load_environment"
]