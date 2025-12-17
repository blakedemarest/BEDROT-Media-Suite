# -*- coding: utf-8 -*-
"""
Unified safe printing module for the Bedrot Productions Media Tool Suite.

This module provides thread-safe, Unicode-safe printing capabilities with
optional logging, timestamps, and severity levels. It consolidates the best
features from existing implementations and adds enhanced functionality.

Features:
- Thread-safe printing using threading locks
- Unicode encoding error handling with multiple fallback strategies
- Optional timestamps with customizable format
- Severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Optional file logging with rotation support
- Multi-line message handling
- Context manager support for temporary log redirection
- Compatibility with both console and GUI applications
"""

import datetime
import logging
import logging.handlers
import os
import sys
import threading
from enum import IntEnum
from pathlib import Path
from typing import Optional, Union, TextIO, Any, Callable
from functools import wraps


class LogLevel(IntEnum):
    """Logging severity levels matching Python's logging module."""
    DEBUG = logging.DEBUG       # 10
    INFO = logging.INFO         # 20
    WARNING = logging.WARNING   # 30
    ERROR = logging.ERROR       # 40
    CRITICAL = logging.CRITICAL # 50


class SafePrinter:
    """
    Thread-safe printing class with Unicode support and optional logging.
    
    This class provides a robust printing mechanism that handles:
    - Thread safety through locking
    - Unicode encoding errors with fallback strategies
    - Optional file logging with rotation
    - Severity levels and filtering
    - Timestamps and formatting
    """
    
    # Class-level lock for thread safety
    _print_lock = threading.Lock()
    
    # Default encoding fallback chain
    ENCODING_FALLBACKS = ['utf-8', 'utf-8-sig', 'latin-1', 'ascii']
    
    def __init__(
        self,
        log_file: Optional[Union[str, Path]] = None,
        level: LogLevel = LogLevel.INFO,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        include_timestamps: bool = True,
        max_log_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        include_level: bool = True,
        include_thread_name: bool = False,
        file: Optional[TextIO] = None
    ):
        """
        Initialize the SafePrinter.
        
        Args:
            log_file: Optional path to log file for persistent logging
            level: Minimum severity level to print/log
            timestamp_format: strftime format for timestamps
            include_timestamps: Whether to include timestamps in output
            max_log_size: Maximum size of log file before rotation (bytes)
            backup_count: Number of backup files to keep
            include_level: Whether to include severity level in output
            include_thread_name: Whether to include thread name in output
            file: Output file object (defaults to sys.stdout)
        """
        self.level = level
        self.timestamp_format = timestamp_format
        self.include_timestamps = include_timestamps
        self.include_level = include_level
        self.include_thread_name = include_thread_name
        self.file = file or sys.stdout
        
        # Set up file logging if requested
        self.logger = None
        self.file_handler = None
        if log_file:
            self._setup_file_logging(log_file, max_log_size, backup_count)
    
    def _setup_file_logging(
        self,
        log_file: Union[str, Path],
        max_size: int,
        backup_count: int
    ) -> None:
        """Set up rotating file handler for persistent logging."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create logger with unique name
        logger_name = f"safe_print_{id(self)}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # Create rotating file handler
        self.file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Set formatter
        format_parts = []
        if self.include_timestamps:
            format_parts.append('%(asctime)s')
        if self.include_thread_name:
            format_parts.append('[%(threadName)s]')
        if self.include_level:
            format_parts.append('%(levelname)-8s')
        format_parts.append('%(message)s')
        
        formatter = logging.Formatter(
            ' '.join(format_parts),
            datefmt=self.timestamp_format
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)
    
    def _encode_message(self, message: str) -> bytes:
        """
        Encode message with fallback strategies for Unicode errors.
        
        Args:
            message: String message to encode
            
        Returns:
            Encoded bytes that can be safely written
        """
        # Try each encoding in order
        for encoding in self.ENCODING_FALLBACKS:
            try:
                return message.encode(encoding)
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        
        # Final fallback: replace problematic characters
        return message.encode('ascii', errors='replace')
    
    def _format_message(
        self,
        message: str,
        level: LogLevel,
        include_newline: bool = True
    ) -> str:
        """
        Format message with optional timestamp, level, and thread info.
        
        Args:
            message: The message to format
            level: Severity level
            include_newline: Whether to append newline
            
        Returns:
            Formatted message string
        """
        parts = []
        
        # Add timestamp
        if self.include_timestamps:
            timestamp = datetime.datetime.now().strftime(self.timestamp_format)
            parts.append(timestamp)
        
        # Add thread name
        if self.include_thread_name:
            thread_name = threading.current_thread().name
            parts.append(f"[{thread_name}]")
        
        # Add level
        if self.include_level:
            level_name = logging.getLevelName(level)
            parts.append(f"{level_name:<8}")
        
        # Add message
        parts.append(message)
        
        # Join parts
        formatted = ' '.join(parts)
        
        # Add newline if requested
        if include_newline and not formatted.endswith('\n'):
            formatted += '\n'
        
        return formatted
    
    def print(
        self,
        message: Any,
        level: LogLevel = LogLevel.INFO,
        end: str = '\n',
        flush: bool = True
    ) -> None:
        """
        Thread-safe print with Unicode handling.
        
        Args:
            message: Message to print (will be converted to string)
            level: Severity level of the message
            end: String to append after the message
            flush: Whether to flush the output buffer
        """
        # Check level threshold
        if level < self.level:
            return
        
        # Convert message to string
        msg_str = str(message)
        
        # Format message
        formatted_msg = self._format_message(
            msg_str,
            level,
            include_newline=(end == '\n')
        )
        
        # If end is not newline, append it
        if end != '\n':
            formatted_msg = formatted_msg.rstrip('\n') + end
        
        # Thread-safe printing
        with self._print_lock:
            try:
                # Try direct print first (use builtins to avoid recursion)
                import builtins
                builtins.print(formatted_msg, end='', file=self.file, flush=flush)
            except UnicodeEncodeError:
                # Fallback to encoded output
                encoded = self._encode_message(formatted_msg)
                
                if hasattr(self.file, 'buffer'):
                    # Write to binary buffer if available
                    self.file.buffer.write(encoded)
                    if flush:
                        self.file.buffer.flush()
                else:
                    # Decode with 'replace' for text mode
                    safe_text = encoded.decode('ascii', errors='replace')
                    import builtins
                    builtins.print(safe_text, end='', file=self.file, flush=flush)
        
        # Also log to file if configured
        if self.logger:
            self.logger.log(level, msg_str)
    
    def debug(self, message: Any, **kwargs) -> None:
        """Print debug message."""
        self.print(message, LogLevel.DEBUG, **kwargs)
    
    def info(self, message: Any, **kwargs) -> None:
        """Print info message."""
        self.print(message, LogLevel.INFO, **kwargs)
    
    def warning(self, message: Any, **kwargs) -> None:
        """Print warning message."""
        self.print(message, LogLevel.WARNING, **kwargs)
    
    def error(self, message: Any, **kwargs) -> None:
        """Print error message."""
        self.print(message, LogLevel.ERROR, **kwargs)
    
    def critical(self, message: Any, **kwargs) -> None:
        """Print critical message."""
        self.print(message, LogLevel.CRITICAL, **kwargs)
    
    def print_multiline(
        self,
        lines: Union[str, list],
        level: LogLevel = LogLevel.INFO,
        prefix: str = ""
    ) -> None:
        """
        Print multiple lines with consistent formatting.
        
        Args:
            lines: String with newlines or list of strings
            level: Severity level for all lines
            prefix: Optional prefix for each line
        """
        if isinstance(lines, str):
            lines = lines.splitlines()
        
        for line in lines:
            if prefix:
                line = prefix + line
            self.print(line, level)
    
    def close(self) -> None:
        """Close file handler if logging to file."""
        if self.file_handler:
            self.file_handler.close()
        if self.logger:
            self.logger.removeHandler(self.file_handler)


# Global default printer instance
_default_printer = SafePrinter()


def safe_print(
    message: Any,
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    **kwargs
) -> None:
    """
    Thread-safe, Unicode-safe print function.
    
    This is a convenience function that uses the global default printer.
    
    Args:
        message: Message to print
        level: Severity level (can be LogLevel, string name, or int)
        **kwargs: Additional arguments passed to printer.print()
    
    Examples:
        >>> safe_print("Hello, world!")
        >>> safe_print("Debug info", level="DEBUG")
        >>> safe_print("Error occurred", level=LogLevel.ERROR)
        >>> safe_print("No newline", end="")
    """
    # Convert level if needed
    if isinstance(level, str):
        level = getattr(LogLevel, level.upper(), LogLevel.INFO)
    elif isinstance(level, int):
        level = LogLevel(level)
    
    _default_printer.print(message, level, **kwargs)


def configure_safe_print(
    log_file: Optional[Union[str, Path]] = None,
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    **kwargs
) -> SafePrinter:
    """
    Configure the global safe_print settings.
    
    Args:
        log_file: Optional log file path
        level: Minimum severity level
        **kwargs: Additional arguments for SafePrinter
        
    Returns:
        The configured SafePrinter instance
    """
    global _default_printer
    
    # Convert level if needed
    if isinstance(level, str):
        level = getattr(LogLevel, level.upper(), LogLevel.INFO)
    elif isinstance(level, int):
        level = LogLevel(level)
    
    # Close existing printer if it has a file handler
    _default_printer.close()
    
    # Create new printer
    _default_printer = SafePrinter(log_file=log_file, level=level, **kwargs)
    return _default_printer


class SafePrintContext:
    """Context manager for temporary safe_print configuration."""
    
    def __init__(self, **kwargs):
        """Initialize with temporary configuration."""
        self.kwargs = kwargs
        self.original_printer = None
        self.temp_printer = None
    
    def __enter__(self) -> SafePrinter:
        """Enter context and set up temporary printer."""
        global _default_printer
        self.original_printer = _default_printer
        self.temp_printer = SafePrinter(**self.kwargs)
        _default_printer = self.temp_printer
        return self.temp_printer
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore original printer."""
        global _default_printer
        if self.temp_printer:
            self.temp_printer.close()
        _default_printer = self.original_printer


def safe_print_decorator(
    level: Union[LogLevel, str, int] = LogLevel.DEBUG,
    prefix: str = "",
    log_args: bool = True,
    log_result: bool = True,
    log_errors: bool = True
) -> Callable:
    """
    Decorator to add safe printing to function calls.
    
    Args:
        level: Severity level for logging
        prefix: Prefix for log messages
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_errors: Whether to log exceptions
        
    Returns:
        Decorator function
    """
    # Convert level if needed
    if isinstance(level, str):
        level = getattr(LogLevel, level.upper(), LogLevel.INFO)
    elif isinstance(level, int):
        level = LogLevel(level)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Log function call
            if log_args:
                args_str = ', '.join(repr(a) for a in args)
                kwargs_str = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
                all_args = ', '.join(filter(None, [args_str, kwargs_str]))
                safe_print(f"{prefix}Calling {func_name}({all_args})", level=level)
            else:
                safe_print(f"{prefix}Calling {func_name}()", level=level)
            
            try:
                # Call function
                result = func(*args, **kwargs)
                
                # Log result
                if log_result:
                    safe_print(f"{prefix}{func_name} returned: {result!r}", level=level)
                
                return result
                
            except Exception as e:
                # Log error
                if log_errors:
                    safe_print(
                        f"{prefix}Error in {func_name}: {type(e).__name__}: {e}",
                        level=LogLevel.ERROR
                    )
                raise
        
        return wrapper
    return decorator


# Convenience functions for compatibility
def safe_print_info(message: Any, **kwargs) -> None:
    """Print info message."""
    safe_print(message, LogLevel.INFO, **kwargs)


def safe_print_warning(message: Any, **kwargs) -> None:
    """Print warning message."""
    safe_print(message, LogLevel.WARNING, **kwargs)


def safe_print_error(message: Any, **kwargs) -> None:
    """Print error message."""
    safe_print(message, LogLevel.ERROR, **kwargs)


def safe_print_debug(message: Any, **kwargs) -> None:
    """Print debug message."""
    safe_print(message, LogLevel.DEBUG, **kwargs)


# For backward compatibility - matches existing safe_print signature
def _legacy_safe_print(text: str) -> None:
    """Legacy safe_print function for backward compatibility."""
    safe_print(text)


# For backward compatibility