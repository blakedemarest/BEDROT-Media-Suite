# -*- coding: utf-8 -*-
"""
Core utilities package for Bedrot Productions Media Tool Suite.

This package provides centralized configuration management,
path resolution, and common utilities shared across all applications.
"""

from .config_manager import ConfigManager, get_config_manager, load_app_config, save_app_config
from .path_utils import PathResolver, resolve_path, validate_path, resolve_config_path, resolve_output_path
from .env_loader import load_environment

__version__ = "1.0.0"
__author__ = "Bedrot Productions"

__all__ = [
    "ConfigManager",
    "get_config_manager",
    "load_app_config",
    "save_app_config",
    "PathResolver",
    "resolve_path",
    "resolve_config_path",
    "resolve_output_path",
    "validate_path",
    "load_environment"
]