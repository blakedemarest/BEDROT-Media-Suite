# -*- coding: utf-8 -*-
"""
Centralized logging system for Bedrot Productions Media Tool Suite.

This module provides a comprehensive logging setup with:
- Rotating file handlers with size limits
- Console handlers with optional color support
- Thread-safe logging
- Module-specific loggers with proper namespaces
- Environment variable configuration
- JSON logging support for structured logs
- Integration with safe_print module
"""

import os
import sys
import json
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union
import threading
from queue import Queue, Empty
import traceback

# Import environment loader for configuration
from .env_loader import get_env_var, get_int_env_var, get_bool_env_var
from .path_utils import resolve_path


# Default constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_LOG_DIR = "logs"


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with optional color support for console output.
    Only adds colors if the terminal supports it and colors are enabled.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and self._supports_color()
    
    def _supports_color(self):
        """Check if the terminal supports color output."""
        # Check if stdout is a terminal
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check for color support on Windows
        if sys.platform == 'win32':
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                return False
        
        # Unix-like systems generally support colors
        return True
    
    def format(self, record):
        """Format the log record with optional colors."""
        formatted = super().format(record)
        
        if self.use_colors and record.levelname in self.COLORS:
            formatted = f"{self.COLORS[record.levelname]}{formatted}{self.COLORS['RESET']}"
        
        return formatted


class SafePrintHandler(logging.Handler):
    """
    Custom handler that integrates with the safe_print module
    to handle Unicode output safely across different environments.
    """
    
    def __init__(self, stream=None):
        super().__init__()
        self.stream = stream or sys.stdout
        self._lock = threading.Lock()
    
    def emit(self, record):
        """Emit a record using safe_print functionality."""
        try:
            msg = self.format(record)
            with self._lock:
                # Use safe encoding for Unicode handling
                self._safe_write(msg + '\n')
                self.flush()
        except Exception:
            self.handleError(record)
    
    def _safe_write(self, text):
        """Safely write text to stream, handling encoding issues."""
        try:
            self.stream.write(text)
        except UnicodeEncodeError:
            # Fallback to ASCII with replacement
            encoded = text.encode('ascii', errors='replace').decode('ascii')
            self.stream.write(encoded)
    
    def flush(self):
        """Flush the stream."""
        if self.stream and hasattr(self.stream, 'flush'):
            self.stream.flush()


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Useful for log aggregation systems and automated processing.
    """
    
    def format(self, record):
        """Format the log record as JSON."""
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
            'process_name': record.processName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class LoggerConfig:
    """Configuration class for logger setup."""
    
    def __init__(self):
        # Load configuration from environment variables
        self.log_level = get_env_var('SLIDESHOW_LOG_LEVEL', DEFAULT_LOG_LEVEL).upper()
        self.log_format = get_env_var('SLIDESHOW_LOG_FORMAT', DEFAULT_LOG_FORMAT)
        self.date_format = get_env_var('SLIDESHOW_DATE_FORMAT', DEFAULT_DATE_FORMAT)
        self.log_dir = get_env_var('SLIDESHOW_LOG_DIR', DEFAULT_LOG_DIR)
        self.max_bytes = get_int_env_var('SLIDESHOW_LOG_MAX_BYTES', DEFAULT_MAX_BYTES)
        self.backup_count = get_int_env_var('SLIDESHOW_LOG_BACKUP_COUNT', DEFAULT_BACKUP_COUNT)
        self.enable_console = get_bool_env_var('SLIDESHOW_LOG_CONSOLE', True)
        self.enable_file = get_bool_env_var('SLIDESHOW_LOG_FILE', True)
        self.enable_colors = get_bool_env_var('SLIDESHOW_LOG_COLORS', True)
        self.enable_json = get_bool_env_var('SLIDESHOW_LOG_JSON', False)
        self.log_file_prefix = get_env_var('SLIDESHOW_LOG_FILE_PREFIX', 'slideshow')
        
        # Validate log level
        numeric_level = getattr(logging, self.log_level, None)
        if not isinstance(numeric_level, int):
            self.log_level = DEFAULT_LOG_LEVEL


class LogManager:
    """
    Central log manager for the application.
    Handles logger creation, configuration, and management.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the log manager."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.config = LoggerConfig()
            self._loggers = {}
            self._handlers = {}
            self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Configure the root logger."""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.log_level))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add console handler if enabled
        if self.config.enable_console:
            console_handler = self._create_console_handler()
            root_logger.addHandler(console_handler)
            self._handlers['console'] = console_handler
        
        # Add file handler if enabled
        if self.config.enable_file:
            file_handler = self._create_file_handler()
            root_logger.addHandler(file_handler)
            self._handlers['file'] = file_handler
        
        # Add JSON file handler if enabled
        if self.config.enable_json:
            json_handler = self._create_json_handler()
            root_logger.addHandler(json_handler)
            self._handlers['json'] = json_handler
    
    def _create_console_handler(self):
        """Create and configure console handler."""
        handler = SafePrintHandler(sys.stdout)
        handler.setLevel(getattr(logging, self.config.log_level))
        
        formatter = ColoredFormatter(
            fmt=self.config.log_format,
            datefmt=self.config.date_format,
            use_colors=self.config.enable_colors
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self):
        """Create and configure rotating file handler."""
        # Ensure log directory exists
        log_dir = resolve_path(self.config.log_dir)
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file path
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"{self.config.log_file_prefix}_{timestamp}.log"
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        handler.setLevel(getattr(logging, self.config.log_level))
        
        formatter = logging.Formatter(
            fmt=self.config.log_format,
            datefmt=self.config.date_format
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_json_handler(self):
        """Create and configure JSON file handler."""
        # Ensure log directory exists
        log_dir = resolve_path(self.config.log_dir)
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create JSON log file path
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"{self.config.log_file_prefix}_{timestamp}.json"
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        handler.setLevel(getattr(logging, self.config.log_level))
        
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        return handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def set_level(self, level: Union[str, int], logger_name: Optional[str] = None):
        """
        Set logging level for a specific logger or all loggers.
        
        Args:
            level: Logging level (string or integer)
            logger_name: Optional logger name (None for all loggers)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        
        if logger_name:
            if logger_name in self._loggers:
                self._loggers[logger_name].setLevel(level)
        else:
            # Set level for root logger and all handlers
            logging.getLogger().setLevel(level)
            for handler in self._handlers.values():
                handler.setLevel(level)
    
    def add_file_handler(self, filename: str, logger_name: Optional[str] = None):
        """
        Add an additional file handler to a specific logger.
        
        Args:
            filename: Path to log file
            logger_name: Optional logger name (None for root logger)
        """
        handler = logging.FileHandler(filename, encoding='utf-8')
        handler.setLevel(getattr(logging, self.config.log_level))
        
        formatter = logging.Formatter(
            fmt=self.config.log_format,
            datefmt=self.config.date_format
        )
        handler.setFormatter(formatter)
        
        logger = self.get_logger(logger_name) if logger_name else logging.getLogger()
        logger.addHandler(handler)
    
    def configure_from_dict(self, config_dict: Dict[str, Any]):
        """
        Configure logging from a dictionary (similar to logging.config.dictConfig).
        
        Args:
            config_dict: Dictionary with logging configuration
        """
        import logging.config
        logging.config.dictConfig(config_dict)


# Module-level convenience functions
_log_manager = LogManager()

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    This is the primary function that should be used throughout the application
    to obtain logger instances.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    return _log_manager.get_logger(name)


def configure_logging(config_dict: Optional[Dict[str, Any]] = None):
    """
    Configure the logging system.
    
    Args:
        config_dict: Optional dictionary configuration
    """
    if config_dict:
        _log_manager.configure_from_dict(config_dict)


def set_log_level(level: Union[str, int], logger_name: Optional[str] = None):
    """
    Set logging level for a specific logger or all loggers.
    
    Args:
        level: Logging level (string or integer)
        logger_name: Optional logger name (None for all loggers)
    """
    _log_manager.set_level(level, logger_name)


def add_log_file(filename: str, logger_name: Optional[str] = None):
    """
    Add an additional file handler to a specific logger.
    
    Args:
        filename: Path to log file
        logger_name: Optional logger name (None for root logger)
    """
    _log_manager.add_file_handler(filename, logger_name)


# Backward compatibility with print statements
def safe_log_print(message: str, level: str = "INFO", logger_name: str = "console"):
    """
    Safe print replacement that logs messages.
    Provides backward compatibility for code using print statements.
    
    Args:
        message: Message to log
        level: Log level (default: INFO)
        logger_name: Logger name (default: console)
    """
    logger = get_logger(logger_name)
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)