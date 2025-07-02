# -*- coding: utf-8 -*-
"""
Logging Configuration for Video Snippet Remixer.

Provides centralized logging configuration with:
- Structured logging with detailed formatting
- File and console handlers with different levels
- Thread-safe logging for concurrent operations
- Performance metrics and timing information
- Aspect ratio debugging capabilities
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


class VideoProcessingFormatter(logging.Formatter):
    """Custom formatter that adds video processing context to log messages."""
    
    def __init__(self, include_thread=True):
        """
        Initialize the formatter.
        
        Args:
            include_thread (bool): Whether to include thread information
        """
        self.include_thread = include_thread
        super().__init__()
    
    def format(self, record):
        """Format the log record with video processing context."""
        # Base format with timestamp, level, and logger name
        base_format = "%(asctime)s [%(levelname)-8s] %(name)-20s"
        
        # Add thread info if enabled
        if self.include_thread:
            base_format += " [%(threadName)-10s]"
        
        # Add file context
        base_format += " %(filename)s:%(lineno)d"
        
        # Add video context if available
        if hasattr(record, 'video_file'):
            base_format += f" [{record.video_file}]"
        if hasattr(record, 'dimensions'):
            base_format += f" [{record.dimensions}]"
        if hasattr(record, 'aspect_ratio'):
            base_format += f" [AR: {record.aspect_ratio}]"
        
        # Add the actual message
        base_format += " - %(message)s"
        
        # Set the format and call parent
        self._style._fmt = base_format
        formatted = super().format(record)
        
        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted


class VideoProcessingFilter(logging.Filter):
    """Filter to add video processing context to log records."""
    
    def __init__(self, name=""):
        super().__init__(name)
        self.current_video = None
        self.current_dimensions = None
        self.current_aspect_ratio = None
    
    def set_video_context(self, video_file=None, dimensions=None, aspect_ratio=None):
        """Set the current video processing context."""
        if video_file is not None:
            self.current_video = os.path.basename(video_file)
        if dimensions is not None:
            self.current_dimensions = dimensions
        if aspect_ratio is not None:
            self.current_aspect_ratio = aspect_ratio
    
    def clear_context(self):
        """Clear the current video processing context."""
        self.current_video = None
        self.current_dimensions = None
        self.current_aspect_ratio = None
    
    def filter(self, record):
        """Add video context to the log record."""
        if self.current_video:
            record.video_file = self.current_video
        if self.current_dimensions:
            record.dimensions = self.current_dimensions
        if self.current_aspect_ratio:
            record.aspect_ratio = self.current_aspect_ratio
        return True


def setup_logging(log_dir=None, log_level=logging.INFO, console_level=logging.INFO, 
                  enable_file_logging=True, max_bytes=10*1024*1024, backup_count=5):
    """
    Set up comprehensive logging for the video processing pipeline.
    
    Args:
        log_dir (str): Directory for log files. If None, uses script directory
        log_level (int): Logging level for file handler
        console_level (int): Logging level for console handler
        enable_file_logging (bool): Whether to enable file logging
        max_bytes (int): Maximum size of log file before rotation
        backup_count (int): Number of backup files to keep
    
    Returns:
        tuple: (logger, video_filter) - Main logger and video context filter
    """
    # Create logger
    logger = logging.getLogger("snippet_remixer")
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = VideoProcessingFormatter(include_thread=True)
    simple_formatter = VideoProcessingFormatter(include_thread=False)
    
    # Create video context filter
    video_filter = VideoProcessingFilter()
    
    # Console handler - less verbose
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(simple_formatter)
    console_handler.addFilter(video_filter)
    logger.addHandler(console_handler)
    
    # File handler - detailed logging with rotation
    if enable_file_logging:
        if log_dir is None:
            log_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_path / f"video_processor_{timestamp}.log"
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        file_handler.addFilter(video_filter)
        logger.addHandler(file_handler)
        
        # Also create a separate error log
        error_log_file = log_path / f"video_processor_errors_{timestamp}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        error_handler.addFilter(video_filter)
        logger.addHandler(error_handler)
    
    # Log the logging configuration
    logger.info("="*80)
    logger.info("Video Snippet Remixer - Logging Initialized")
    logger.info(f"Log Level: {logging.getLevelName(log_level)}")
    logger.info(f"Console Level: {logging.getLevelName(console_level)}")
    if enable_file_logging:
        logger.info(f"Log Directory: {log_dir}")
        logger.info(f"Log File: {log_file}")
    logger.info("="*80)
    
    return logger, video_filter


def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name (str): Logger name. If None, returns the main snippet_remixer logger
    
    Returns:
        logging.Logger: Logger instance
    """
    if name is None:
        return logging.getLogger("snippet_remixer")
    else:
        return logging.getLogger(f"snippet_remixer.{name}")


class LoggingContext:
    """Context manager for temporary video processing context."""
    
    def __init__(self, video_filter, video_file=None, dimensions=None, aspect_ratio=None):
        self.video_filter = video_filter
        self.video_file = video_file
        self.dimensions = dimensions
        self.aspect_ratio = aspect_ratio
        self.previous_context = None
    
    def __enter__(self):
        # Save current context
        if self.video_filter:
            self.previous_context = (
                getattr(self.video_filter, 'current_video', None),
                getattr(self.video_filter, 'current_dimensions', None),
                getattr(self.video_filter, 'current_aspect_ratio', None)
            )
            # Set new context
            self.video_filter.set_video_context(
                self.video_file, 
                self.dimensions, 
                self.aspect_ratio
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self.video_filter and self.previous_context:
            self.video_filter.set_video_context(
                self.previous_context[0],
                self.previous_context[1],
                self.previous_context[2]
            )
        return False


def log_ffmpeg_command(logger, command, level=logging.DEBUG):
    """
    Log an FFmpeg command in a readable format.
    
    Args:
        logger: Logger instance
        command: List of command arguments
        level: Logging level
    """
    if isinstance(command, list):
        # Format the command nicely
        cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in command)
        logger.log(level, f"FFmpeg Command: {cmd_str}")
    else:
        logger.log(level, f"FFmpeg Command: {command}")


def log_video_info(logger, filepath, width, height, duration, level=logging.INFO):
    """
    Log video information in a structured format.
    
    Args:
        logger: Logger instance
        filepath: Path to video file
        width: Video width
        height: Video height
        duration: Video duration in seconds
        level: Logging level
    """
    filename = os.path.basename(filepath)
    if width and height:
        aspect_ratio = width / height
        logger.log(level, 
            f"Video Info: {filename} | "
            f"Dimensions: {width}x{height} | "
            f"Aspect Ratio: {aspect_ratio:.3f} ({width}:{height}) | "
            f"Duration: {duration:.2f}s"
        )
    else:
        logger.log(level, f"Video Info: {filename} | Unable to read dimensions/duration")


def log_processing_summary(logger, input_count, output_file, total_duration, 
                          processing_time, level=logging.INFO):
    """
    Log a processing summary.
    
    Args:
        logger: Logger instance
        input_count: Number of input videos processed
        output_file: Output file path
        total_duration: Total duration of output video
        processing_time: Time taken to process
        level: Logging level
    """
    logger.log(level, "="*60)
    logger.log(level, "PROCESSING SUMMARY")
    logger.log(level, f"Input Videos: {input_count}")
    logger.log(level, f"Output File: {os.path.basename(output_file)}")
    logger.log(level, f"Output Duration: {total_duration:.2f}s")
    logger.log(level, f"Processing Time: {processing_time:.2f}s")
    logger.log(level, f"Processing Speed: {total_duration/processing_time:.2f}x realtime")
    logger.log(level, "="*60)