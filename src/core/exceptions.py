"""
Custom exception system for the Slideshow Editor project.

This module provides domain-specific exceptions with rich error information,
including error codes, user-friendly messages, technical details, and
recovery suggestions.
"""

import traceback
from typing import Optional, Dict, Any, List
from enum import Enum
import sys


class ErrorCode(Enum):
    """Error codes for categorizing exceptions."""
    # Configuration errors (1xxx)
    CONFIG_FILE_NOT_FOUND = 1001
    CONFIG_PARSE_ERROR = 1002
    CONFIG_VALIDATION_ERROR = 1003
    CONFIG_PERMISSION_ERROR = 1004
    CONFIG_VERSION_MISMATCH = 1005
    
    # Path validation errors (2xxx)
    PATH_TRAVERSAL_ATTEMPT = 2001
    PATH_INVALID_EXTENSION = 2002
    PATH_NOT_FOUND = 2003
    PATH_ACCESS_DENIED = 2004
    PATH_OUTSIDE_PROJECT = 2005
    
    # Media processing errors (3xxx)
    FFMPEG_NOT_FOUND = 3001
    FFMPEG_EXECUTION_ERROR = 3002
    VIDEO_CODEC_ERROR = 3003
    AUDIO_CODEC_ERROR = 3004
    MEDIA_FORMAT_UNSUPPORTED = 3005
    MEDIA_CORRUPTED = 3006
    MEDIA_DURATION_ERROR = 3007
    
    # Dependency errors (4xxx)
    DEPENDENCY_NOT_FOUND = 4001
    DEPENDENCY_VERSION_ERROR = 4002
    DEPENDENCY_IMPORT_ERROR = 4003
    
    # Resource errors (5xxx)
    RESOURCE_NOT_FOUND = 5001
    RESOURCE_BUSY = 5002
    MEMORY_ERROR = 5003
    DISK_SPACE_ERROR = 5004
    FILE_SIZE_LIMIT_EXCEEDED = 5005
    
    # Threading errors (6xxx)
    THREAD_CREATION_ERROR = 6001
    THREAD_SYNCHRONIZATION_ERROR = 6002
    THREAD_TIMEOUT = 6003
    THREAD_INTERRUPTED = 6004
    
    # Network errors (7xxx)
    NETWORK_CONNECTION_ERROR = 7001
    NETWORK_TIMEOUT = 7002
    NETWORK_DNS_ERROR = 7003
    NETWORK_DOWNLOAD_FAILED = 7004
    NETWORK_RATE_LIMITED = 7005
    NETWORK_AUTHENTICATION_ERROR = 7006
    NETWORK_SSL_ERROR = 7007
    NETWORK_PROXY_ERROR = 7008


class SlideshowEditorError(Exception):
    """
    Base exception class for all slideshow editor exceptions.
    
    Attributes:
        message: User-friendly error message
        error_code: ErrorCode enum value for categorization
        details: Technical details about the error
        recovery: Suggested recovery actions
        context: Additional context information
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[ErrorCode] = None,
        details: Optional[str] = None,
        recovery: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception with rich error information.
        
        Args:
            message: User-friendly error message
            error_code: ErrorCode enum value for categorization
            details: Technical details about the error
            recovery: List of suggested recovery actions
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
        self.recovery = recovery or []
        self.context = context or {}
        
        # Capture the current traceback
        self.tb_str = traceback.format_exc()
    
    def __str__(self) -> str:
        """Return a formatted string representation of the exception."""
        parts = [f"{self.__class__.__name__}: {self.message}"]
        
        if self.error_code:
            parts.append(f"Error Code: {self.error_code.name} ({self.error_code.value})")
        
        if self.details:
            parts.append(f"Details: {self.details}")
        
        if self.recovery:
            parts.append("Recovery suggestions:")
            for i, suggestion in enumerate(self.recovery, 1):
                parts.append(f"  {i}. {suggestion}")
        
        if self.context:
            parts.append("Context:")
            for key, value in self.context.items():
                parts.append(f"  {key}: {value}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for logging or serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code.name if self.error_code else None,
            "error_code_value": self.error_code.value if self.error_code else None,
            "details": self.details,
            "recovery": self.recovery,
            "context": self.context,
            "traceback": self.tb_str
        }


class ConfigurationError(SlideshowEditorError):
    """
    Exception raised for configuration-related errors.
    
    This includes missing config files, parse errors, validation failures,
    and permission issues.
    """
    
    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        error_code: Optional[ErrorCode] = ErrorCode.CONFIG_PARSE_ERROR,
        **kwargs
    ):
        """Initialize a configuration error with file context."""
        if config_file:
            kwargs.setdefault('context', {})['config_file'] = config_file
        
        # Add default recovery suggestions if not provided
        if 'recovery' not in kwargs:
            kwargs['recovery'] = [
                "Check if the configuration file exists and is readable",
                "Verify the JSON syntax is correct",
                "Restore from a backup configuration",
                "Delete the config file to use defaults"
            ]
        
        super().__init__(message, error_code=error_code, **kwargs)


class PathValidationError(SlideshowEditorError):
    """
    Exception raised for path validation failures.
    
    This includes directory traversal attempts, invalid extensions,
    and access permission issues.
    """
    
    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        error_code: Optional[ErrorCode] = ErrorCode.PATH_INVALID_EXTENSION,
        **kwargs
    ):
        """Initialize a path validation error with path context."""
        if path:
            kwargs.setdefault('context', {})['path'] = path
        
        # Add default recovery suggestions if not provided
        if 'recovery' not in kwargs:
            kwargs['recovery'] = [
                "Ensure the path is within the project directory",
                "Check file/directory permissions",
                "Verify the file extension is allowed",
                "Use absolute paths to avoid ambiguity"
            ]
        
        super().__init__(message, error_code=error_code, **kwargs)


class MediaProcessingError(SlideshowEditorError):
    """
    Exception raised for media processing failures.
    
    This includes FFmpeg errors, codec issues, format problems,
    and corrupted media files.
    """
    
    def __init__(
        self,
        message: str,
        media_file: Optional[str] = None,
        ffmpeg_output: Optional[str] = None,
        error_code: Optional[ErrorCode] = ErrorCode.FFMPEG_EXECUTION_ERROR,
        **kwargs
    ):
        """Initialize a media processing error with media context."""
        context = kwargs.setdefault('context', {})
        if media_file:
            context['media_file'] = media_file
        if ffmpeg_output:
            context['ffmpeg_output'] = ffmpeg_output
        
        # Add default recovery suggestions if not provided
        if 'recovery' not in kwargs:
            kwargs['recovery'] = [
                "Ensure FFmpeg is installed and in PATH",
                "Check if the media file is corrupted",
                "Try converting the file to a different format",
                "Update FFmpeg to the latest version",
                "Check available disk space"
            ]
        
        super().__init__(message, error_code=error_code, **kwargs)


class DependencyError(SlideshowEditorError):
    """
    Exception raised for missing or incompatible dependencies.
    
    This includes missing tools like FFmpeg, yt-dlp, or Python packages.
    """
    
    def __init__(
        self,
        message: str,
        dependency: Optional[str] = None,
        required_version: Optional[str] = None,
        current_version: Optional[str] = None,
        error_code: Optional[ErrorCode] = ErrorCode.DEPENDENCY_NOT_FOUND,
        **kwargs
    ):
        """Initialize a dependency error with version context."""
        context = kwargs.setdefault('context', {})
        if dependency:
            context['dependency'] = dependency
        if required_version:
            context['required_version'] = required_version
        if current_version:
            context['current_version'] = current_version
        
        # Add default recovery suggestions if not provided
        if 'recovery' not in kwargs:
            recovery = []
            if dependency == 'ffmpeg':
                recovery.extend([
                    "Install FFmpeg from https://ffmpeg.org/download.html",
                    "Add FFmpeg to your system PATH",
                    "On Windows: Use 'winget install ffmpeg' or download manually",
                    "On macOS: Use 'brew install ffmpeg'",
                    "On Linux: Use your package manager (apt, yum, etc.)"
                ])
            elif dependency == 'yt-dlp':
                recovery.extend([
                    "Install yt-dlp with: pip install yt-dlp",
                    "Update yt-dlp with: pip install --upgrade yt-dlp",
                    "Check if yt-dlp is in your Python environment"
                ])
            else:
                recovery.extend([
                    f"Install {dependency} using pip or your package manager",
                    "Check if you're in the correct virtual environment",
                    "Reinstall dependencies with: pip install -r requirements.txt"
                ])
            kwargs['recovery'] = recovery
        
        super().__init__(message, error_code=error_code, **kwargs)


class ResourceError(SlideshowEditorError):
    """
    Exception raised for resource-related issues.
    
    This includes file not found, insufficient memory, disk space issues,
    and file size limits.
    """
    
    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        resource_type: Optional[str] = None,
        error_code: Optional[ErrorCode] = ErrorCode.RESOURCE_NOT_FOUND,
        **kwargs
    ):
        """Initialize a resource error with resource context."""
        context = kwargs.setdefault('context', {})
        if resource:
            context['resource'] = resource
        if resource_type:
            context['resource_type'] = resource_type
        
        # Add default recovery suggestions if not provided
        if 'recovery' not in kwargs:
            recovery = []
            if error_code == ErrorCode.MEMORY_ERROR:
                recovery.extend([
                    "Close other applications to free memory",
                    "Process smaller batches of files",
                    "Reduce video resolution or quality settings",
                    "Increase system virtual memory"
                ])
            elif error_code == ErrorCode.DISK_SPACE_ERROR:
                recovery.extend([
                    "Free up disk space by deleting temporary files",
                    "Change output directory to a drive with more space",
                    "Reduce output quality to save space",
                    "Clean up old generated files"
                ])
            else:
                recovery.extend([
                    "Verify the file or resource exists",
                    "Check file permissions",
                    "Ensure the resource is not in use by another process",
                    "Try again after a short delay"
                ])
            kwargs['recovery'] = recovery
        
        super().__init__(message, error_code=error_code, **kwargs)


class ThreadingError(SlideshowEditorError):
    """
    Exception raised for threading and concurrency issues.
    
    This includes thread creation failures, synchronization problems,
    timeouts, and interruptions.
    """
    
    def __init__(
        self,
        message: str,
        thread_name: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[ErrorCode] = ErrorCode.THREAD_CREATION_ERROR,
        **kwargs
    ):
        """Initialize a threading error with thread context."""
        context = kwargs.setdefault('context', {})
        if thread_name:
            context['thread_name'] = thread_name
        if operation:
            context['operation'] = operation
        
        # Add default recovery suggestions if not provided
        if 'recovery' not in kwargs:
            kwargs['recovery'] = [
                "Restart the application",
                "Reduce the number of concurrent operations",
                "Check system resources (CPU, memory)",
                "Disable multi-threading in settings if available",
                "Report the issue if it persists"
            ]
        
        super().__init__(message, error_code=error_code, **kwargs)


class NetworkError(SlideshowEditorError):
    """
    Exception raised for network-related failures.
    
    This includes connection failures, timeouts, DNS resolution errors,
    download failures, rate limiting, and authentication issues.
    """
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        error_code: Optional[ErrorCode] = ErrorCode.NETWORK_CONNECTION_ERROR,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        """Initialize a network error with connection context."""
        context = kwargs.setdefault('context', {})
        if url:
            context['url'] = url
        if status_code:
            context['status_code'] = status_code
        if retry_after:
            context['retry_after_seconds'] = retry_after
        
        # Add default recovery suggestions based on error code
        if 'recovery' not in kwargs:
            recovery = []
            if error_code == ErrorCode.NETWORK_TIMEOUT:
                recovery.extend([
                    "Check your internet connection",
                    "Try again with a longer timeout setting",
                    "The server may be slow or overloaded",
                    "Try downloading during off-peak hours"
                ])
            elif error_code == ErrorCode.NETWORK_DNS_ERROR:
                recovery.extend([
                    "Check your internet connection",
                    "Verify the URL is correct",
                    "Try using a different DNS server (e.g., 8.8.8.8)",
                    "Check if the website is down"
                ])
            elif error_code == ErrorCode.NETWORK_RATE_LIMITED:
                recovery.extend([
                    f"Wait {retry_after} seconds before retrying" if retry_after else "Wait before retrying",
                    "Use authentication if available",
                    "Reduce the frequency of requests",
                    "Contact the service for higher rate limits"
                ])
            elif error_code == ErrorCode.NETWORK_AUTHENTICATION_ERROR:
                recovery.extend([
                    "Check your credentials",
                    "Verify API keys or tokens are valid",
                    "Ensure authentication headers are correct",
                    "Check if your account has the required permissions"
                ])
            elif error_code == ErrorCode.NETWORK_SSL_ERROR:
                recovery.extend([
                    "Check if the website's SSL certificate is valid",
                    "Update your system's certificate store",
                    "Try disabling SSL verification (not recommended for production)",
                    "Check system date and time settings"
                ])
            elif error_code == ErrorCode.NETWORK_PROXY_ERROR:
                recovery.extend([
                    "Check proxy settings",
                    "Verify proxy authentication if required",
                    "Try connecting without a proxy",
                    "Contact your network administrator"
                ])
            else:
                recovery.extend([
                    "Check your internet connection",
                    "Verify the URL is accessible",
                    "Try again later",
                    "Check if a firewall is blocking the connection"
                ])
            kwargs['recovery'] = recovery
        
        super().__init__(message, error_code=error_code, **kwargs)


# Utility functions for common error scenarios

def handle_config_error(e: Exception, config_file: str) -> ConfigurationError:
    """Convert a generic exception to a ConfigurationError with context."""
    if isinstance(e, FileNotFoundError):
        return ConfigurationError(
            f"Configuration file not found: {config_file}",
            config_file=config_file,
            error_code=ErrorCode.CONFIG_FILE_NOT_FOUND,
            details=str(e)
        )
    elif isinstance(e, PermissionError):
        return ConfigurationError(
            f"Permission denied accessing config file: {config_file}",
            config_file=config_file,
            error_code=ErrorCode.CONFIG_PERMISSION_ERROR,
            details=str(e)
        )
    elif isinstance(e, (json.JSONDecodeError, ValueError)):
        return ConfigurationError(
            f"Failed to parse configuration file: {config_file}",
            config_file=config_file,
            error_code=ErrorCode.CONFIG_PARSE_ERROR,
            details=str(e),
            recovery=[
                "Check JSON syntax with a validator",
                "Look for missing commas or quotes",
                "Ensure all strings are properly escaped",
                "Restore from backup or delete to use defaults"
            ]
        )
    else:
        return ConfigurationError(
            f"Unexpected error loading configuration: {config_file}",
            config_file=config_file,
            error_code=ErrorCode.CONFIG_PARSE_ERROR,
            details=str(e)
        )


def handle_media_error(e: Exception, media_file: str, operation: str = "processing") -> MediaProcessingError:
    """Convert a generic exception to a MediaProcessingError with context."""
    error_str = str(e).lower()
    
    if "codec" in error_str or "encoder" in error_str:
        error_code = ErrorCode.VIDEO_CODEC_ERROR if "video" in error_str else ErrorCode.AUDIO_CODEC_ERROR
        message = f"Codec error while {operation} {media_file}"
    elif "format" in error_str or "container" in error_str:
        error_code = ErrorCode.MEDIA_FORMAT_UNSUPPORTED
        message = f"Unsupported media format: {media_file}"
    elif "corrupt" in error_str or "invalid" in error_str:
        error_code = ErrorCode.MEDIA_CORRUPTED
        message = f"Media file appears to be corrupted: {media_file}"
    else:
        error_code = ErrorCode.FFMPEG_EXECUTION_ERROR
        message = f"Error {operation} media file: {media_file}"
    
    return MediaProcessingError(
        message,
        media_file=media_file,
        error_code=error_code,
        details=str(e),
        context={"operation": operation}
    )


def handle_network_error(e: Exception, url: str, operation: str = "downloading") -> NetworkError:
    """Convert a generic exception to a NetworkError with context."""
    error_str = str(e).lower()
    
    # Determine error code based on exception type and message
    if isinstance(e, TimeoutError) or "timeout" in error_str:
        error_code = ErrorCode.NETWORK_TIMEOUT
        message = f"Connection timeout while {operation} from {url}"
    elif "dns" in error_str or "resolve" in error_str or "getaddrinfo" in error_str:
        error_code = ErrorCode.NETWORK_DNS_ERROR
        message = f"Failed to resolve domain name for {url}"
    elif "429" in error_str or "rate" in error_str and "limit" in error_str:
        error_code = ErrorCode.NETWORK_RATE_LIMITED
        message = f"Rate limited while {operation} from {url}"
        # Try to extract retry-after from error message
        retry_match = re.search(r'retry.{0,10}(\d+)', error_str)
        retry_after = int(retry_match.group(1)) if retry_match else None
        return NetworkError(message, url=url, error_code=error_code, 
                          details=str(e), retry_after=retry_after,
                          context={"operation": operation})
    elif "401" in error_str or "403" in error_str or "auth" in error_str:
        error_code = ErrorCode.NETWORK_AUTHENTICATION_ERROR
        message = f"Authentication failed while {operation} from {url}"
    elif "ssl" in error_str or "certificate" in error_str:
        error_code = ErrorCode.NETWORK_SSL_ERROR
        message = f"SSL/TLS error while {operation} from {url}"
    elif "proxy" in error_str:
        error_code = ErrorCode.NETWORK_PROXY_ERROR
        message = f"Proxy error while {operation} from {url}"
    else:
        error_code = ErrorCode.NETWORK_CONNECTION_ERROR
        message = f"Network error while {operation} from {url}"
    
    # Extract status code if available
    status_match = re.search(r'(\d{3})', error_str)
    status_code = int(status_match.group(1)) if status_match and len(status_match.group(1)) == 3 else None
    
    return NetworkError(
        message,
        url=url,
        status_code=status_code,
        error_code=error_code,
        details=str(e),
        context={"operation": operation}
    )


# Import json and re for the utility functions
import json
import re