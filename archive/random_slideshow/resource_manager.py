# -*- coding: utf-8 -*-
"""
Resource Management for Random Slideshow Generator.

This module provides resource management and caching functionality to improve
performance during batch slideshow generation.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

import os
import threading
import time
from typing import Dict, Optional, Tuple, List
from collections import OrderedDict
from PIL import Image
import gc

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Resource monitoring will be limited.")


class ImageCache:
    """
    Thread-safe LRU (Least Recently Used) cache for frequently used images.
    
    This cache helps reduce disk I/O by keeping frequently accessed images
    in memory, significantly improving performance for batch operations.
    """
    
    def __init__(self, max_size: int = 100, max_memory_mb: int = 1024, ttl: int = 300):
        """
        Initialize the image cache.
        
        Args:
            max_size: Maximum number of images to cache
            max_memory_mb: Maximum memory usage in MB
            ttl: Time to live for cached images in seconds
        """
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.ttl = ttl
        
        # Use OrderedDict for LRU implementation
        self._cache: OrderedDict[str, Tuple[Image.Image, float, int]] = OrderedDict()
        self._lock = threading.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._current_memory_usage = 0
    
    def get(self, path: str) -> Optional[Image.Image]:
        """
        Get image from cache.
        
        Args:
            path: Path to the image file
            
        Returns:
            PIL Image object if cached and valid, None otherwise
        """
        with self._lock:
            if path in self._cache:
                try:
                    img, timestamp, size = self._cache[path]
                    
                    # Check if image has expired
                    if time.time() - timestamp > self.ttl:
                        # Remove expired image
                        del self._cache[path]
                        self._current_memory_usage -= size
                        self._misses += 1
                        return None
                    
                    # Move to end (most recently used)
                    self._cache.move_to_end(path)
                    self._hits += 1
                    
                    # Return a copy to prevent modifications to cached image
                    try:
                        img.load()
                    except Exception:
                        pass
                    return img.copy()
                except KeyError:
                    # Handle case where key was deleted between check and access
                    self._misses += 1
                    return None
            
            self._misses += 1
            return None
    
    def put(self, path: str, image: Image.Image) -> bool:
        """
        Add image to cache.
        
        Args:
            path: Path to the image file
            image: PIL Image object to cache
            
        Returns:
            True if image was cached, False if it exceeds memory limits
        """
        # Estimate image memory usage (rough approximation)
        image_size = self._estimate_image_size(image)
        
        # Check if single image exceeds memory limit
        if image_size > self.max_memory_mb * 1024 * 1024:
            return False
        
        with self._lock:
            # Remove image if already cached
            if path in self._cache:
                old_img, _, old_size = self._cache[path]
                try:
                    if hasattr(old_img, 'close'):
                        old_img.close()
                except Exception:
                    pass
                self._current_memory_usage -= old_size
                del self._cache[path]
            
            # Evict images if necessary
            while (len(self._cache) >= self.max_size or 
                   self._current_memory_usage + image_size > self.max_memory_mb * 1024 * 1024):
                if not self._cache:
                    break
                
                try:
                    # Remove least recently used (first item)
                    oldest_path, (old_img, _, old_size) = self._cache.popitem(last=False)
                    try:
                        if hasattr(old_img, 'close'):
                            old_img.close()
                    except Exception:
                        pass
                    self._current_memory_usage -= old_size
                except KeyError:
                    # Cache became empty while we were evicting
                    break
            
            # Add new image
            try:
                image.load()
            except Exception:
                pass  # If load fails we still store the image; PIL will lazily load on demand
            cached_image = image.copy()
            self._cache[path] = (cached_image, time.time(), image_size)
            self._current_memory_usage += image_size
            
            return True
    
    def clear(self):
        """Clear all cached images."""
        with self._lock:
            # Explicitly close all cached images
            for path, (img, _, _) in self._cache.items():
                try:
                    if hasattr(img, 'close'):
                        img.close()
                except:
                    pass
            
            self._cache.clear()
            self._current_memory_usage = 0
            gc.collect()  # Force garbage collection
    
    def get_statistics(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'cache_size': len(self._cache),
                'memory_usage_mb': self._current_memory_usage / (1024 * 1024),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }
    
    def _estimate_image_size(self, image: Image.Image) -> int:
        """
        Estimate memory usage of an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Estimated size in bytes
        """
        # Rough estimation: width * height * channels * bytes_per_channel
        width, height = image.size
        
        # Estimate channels based on mode
        channels = {
            'L': 1,      # Grayscale
            'LA': 2,     # Grayscale + Alpha
            'RGB': 3,    # RGB
            'RGBA': 4,   # RGB + Alpha
            'CMYK': 4,   # CMYK
            'YCbCr': 3,  # YCbCr
            'LAB': 3,    # LAB
            'HSV': 3,    # HSV
            'I': 4,      # 32-bit integer
            'F': 4       # 32-bit float
        }.get(image.mode, 3)
        
        # Assume 1 byte per channel for most modes
        bytes_per_pixel = channels
        
        # Add some overhead for PIL object structure
        overhead = 1024  # 1KB overhead estimate
        
        return width * height * bytes_per_pixel + overhead


class ResourceMonitor:
    """
    Monitor system resources to prevent overload during batch processing.
    """
    
    def __init__(self, max_memory_percent: float = 80.0, max_cpu_percent: float = 90.0):
        """
        Initialize resource monitor.
        
        Args:
            max_memory_percent: Maximum memory usage percentage
            max_cpu_percent: Maximum CPU usage percentage
        """
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent
        
        # Get system info
        if PSUTIL_AVAILABLE:
            self.total_memory = psutil.virtual_memory().total
            self.cpu_count = psutil.cpu_count()
        else:
            self.total_memory = 4 * 1024 * 1024 * 1024  # Default 4GB
            self.cpu_count = 4  # Default 4 cores
    
    def check_resources(self) -> Tuple[bool, str]:
        """
        Check if system resources are within acceptable limits.
        
        Returns:
            Tuple of (resources_ok, message)
        """
        if not PSUTIL_AVAILABLE:
            return True, "Resource monitoring not available"
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > self.max_memory_percent:
            return False, f"Memory usage too high: {memory_percent:.1f}%"
        
        # Check CPU (non-blocking)
        cpu_percent = psutil.cpu_percent(interval=0)
        
        if cpu_percent > self.max_cpu_percent:
            return False, f"CPU usage too high: {cpu_percent:.1f}%"
        
        return True, "Resources within limits"
    
    def get_resource_stats(self) -> Dict:
        """
        Get current resource statistics.
        
        Returns:
            Dictionary with resource statistics
        """
        if not PSUTIL_AVAILABLE:
            return {
                'memory_used_mb': 0,
                'memory_available_mb': self.total_memory / (1024 * 1024),
                'memory_percent': 0,
                'cpu_percent': 0,
                'cpu_count': self.cpu_count
            }
        
        memory = psutil.virtual_memory()
        
        return {
            'memory_used_mb': memory.used / (1024 * 1024),
            'memory_available_mb': memory.available / (1024 * 1024),
            'memory_percent': memory.percent,
            'cpu_percent': psutil.cpu_percent(interval=0),
            'cpu_count': self.cpu_count
        }
    
    def get_recommended_workers(self) -> int:
        """
        Get recommended number of worker threads based on system resources.
        
        Returns:
            Recommended worker count
        """
        if not PSUTIL_AVAILABLE:
            return 2  # Safe default
        
        # Base recommendation on CPU cores
        cpu_count = psutil.cpu_count(logical=False) or 2
        
        # Adjust based on available memory (assume ~512MB per worker)
        memory = psutil.virtual_memory()
        memory_based_workers = int(memory.available / (512 * 1024 * 1024))
        
        # Take minimum of CPU and memory based recommendations
        recommended = min(cpu_count, memory_based_workers)
        
        # Ensure at least 1 worker, max 8
        return max(1, min(recommended, 8))


class ResourceManager:
    """
    Central resource management for batch slideshow generation.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Initialize here to ensure it happens only once
                    cls._instance._initialize()
        return cls._instance
    
    def __init__(self):
        """Initialize resource manager (called multiple times, but does nothing after first)."""
        pass
    
    def _initialize(self):
        """Actual initialization logic (called only once)."""
        try:
            self.image_cache = ImageCache()
            self.resource_monitor = ResourceMonitor()
            self._initialized = True
        except Exception as e:
            print(f"Warning: Resource manager initialization error: {e}")
            # Create minimal fallback objects
            self.image_cache = None
            self.resource_monitor = None
            self._initialized = True
    
    def get_image(self, path: str) -> Optional[Image.Image]:
        """
        Get image with caching support.
        
        Args:
            path: Path to image file
            
        Returns:
            PIL Image object or None if loading fails
        """
        # Try cache first if available
        if self.image_cache:
            img = self.image_cache.get(path)
            if img:
                return img
        
        # Load from disk with explicit context to ensure file handles close promptly
        try:
            with Image.open(path) as source_image:
                working_image = source_image.convert("RGB")  # Ensure consistent format
                working_image.load()  # Force data read so we can close the source handle quickly

            img = working_image
            
            # Add to cache if available
            if self.image_cache:
                self.image_cache.put(path, img)
            
            return img
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    
    def check_resources_available(self) -> Tuple[bool, str]:
        """
        Check if resources are available for processing.
        
        Returns:
            Tuple of (available, message)
        """
        if self.resource_monitor:
            return self.resource_monitor.check_resources()
        else:
            return True, "Resource monitoring not available"
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive resource statistics.
        
        Returns:
            Dictionary with all resource statistics
        """
        stats = {}
        
        if self.image_cache:
            stats['cache'] = self.image_cache.get_statistics()
        else:
            stats['cache'] = {'cache_size': 0, 'memory_usage_mb': 0, 'hits': 0, 'misses': 0, 'hit_rate': 0, 'total_requests': 0}
        
        if self.resource_monitor:
            stats['system'] = self.resource_monitor.get_resource_stats()
            stats['recommended_workers'] = self.resource_monitor.get_recommended_workers()
        else:
            stats['system'] = {'memory_used_mb': 0, 'memory_available_mb': 0, 'memory_percent': 0, 'cpu_percent': 0, 'cpu_count': 4}
            stats['recommended_workers'] = 2
        
        return stats
    
    def cleanup(self):
        """Cleanup resources."""
        if self.image_cache:
            self.image_cache.clear()
        gc.collect()


# Global resource manager instance
_resource_manager = None


def get_resource_manager() -> ResourceManager:
    """
    Get the global resource manager instance.
    
    Returns:
        ResourceManager instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
