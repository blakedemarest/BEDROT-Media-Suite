# -*- coding: utf-8 -*-
"""
Thread Safety Utilities for Slideshow Editor.

This module provides thread-safe utilities and patterns to prevent race conditions
and ensure proper synchronization across the application.
"""

import threading
import functools
import weakref
from typing import Callable, Any, TypeVar, Generic, Optional, Dict
from collections import OrderedDict
import time

T = TypeVar('T')


class ThreadSafeSingleton(type):
    """
    Thread-safe singleton metaclass.
    
    This metaclass ensures that only one instance of a class exists
    and handles concurrent access during instantiation.
    """
    _instances: Dict[type, Any] = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        # Fast path: check if instance already exists without lock
        if cls in cls._instances:
            return cls._instances[cls]
        
        # Slow path: acquire lock and create instance if needed
        with cls._lock:
            if cls not in cls._instances:
                instance = super(ThreadSafeSingleton, cls).__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]


class ThreadSafeLRUCache(Generic[T]):
    """
    Thread-safe LRU (Least Recently Used) cache implementation.
    
    This cache provides thread-safe access to cached items with automatic
    eviction of least recently used items when capacity is reached.
    """
    
    def __init__(self, max_size: int = 100, ttl: Optional[float] = None):
        """
        Initialize the thread-safe LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
            ttl: Time to live for cached items in seconds (None = no expiry)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[Any, tuple[T, float]] = OrderedDict()
        self._lock = threading.RLock()  # RLock allows recursive locking
        self._hits = 0
        self._misses = 0
    
    def get(self, key: Any, default: Optional[T] = None) -> Optional[T]:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            # Check TTL if enabled
            value, timestamp = self._cache[key]
            if self.ttl and time.time() - timestamp > self.ttl:
                del self._cache[key]
                self._misses += 1
                return default
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value
    
    def put(self, key: Any, value: T) -> None:
        """
        Add or update an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        with self._lock:
            # Remove old value if exists
            if key in self._cache:
                del self._cache[key]
            
            # Evict LRU items if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            # Add new item
            self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total
            }


class ThreadSafeCounter:
    """Thread-safe counter implementation."""
    
    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()
    
    def increment(self, delta: int = 1) -> int:
        """Increment counter and return new value."""
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        """Decrement counter and return new value."""
        with self._lock:
            self._value -= delta
            return self._value
    
    def get(self) -> int:
        """Get current value."""
        with self._lock:
            return self._value
    
    def set(self, value: int) -> None:
        """Set counter value."""
        with self._lock:
            self._value = value


class ThreadSafeDict(dict):
    """Thread-safe dictionary implementation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()
    
    def __getitem__(self, key):
        with self._lock:
            return super().__getitem__(key)
    
    def __setitem__(self, key, value):
        with self._lock:
            return super().__setitem__(key, value)
    
    def __delitem__(self, key):
        with self._lock:
            return super().__delitem__(key)
    
    def __contains__(self, key):
        with self._lock:
            return super().__contains__(key)
    
    def get(self, key, default=None):
        with self._lock:
            return super().get(key, default)
    
    def pop(self, key, *args):
        with self._lock:
            return super().pop(key, *args)
    
    def popitem(self):
        with self._lock:
            return super().popitem()
    
    def clear(self):
        with self._lock:
            return super().clear()
    
    def update(self, *args, **kwargs):
        with self._lock:
            return super().update(*args, **kwargs)
    
    def setdefault(self, key, default=None):
        with self._lock:
            return super().setdefault(key, default)
    
    def items(self):
        with self._lock:
            return list(super().items())
    
    def keys(self):
        with self._lock:
            return list(super().keys())
    
    def values(self):
        with self._lock:
            return list(super().values())


def synchronized(lock_attr: str = '_lock'):
    """
    Decorator to synchronize method access using an object's lock.
    
    Args:
        lock_attr: Name of the lock attribute on the object
        
    Usage:
        class MyClass:
            def __init__(self):
                self._lock = threading.Lock()
            
            @synchronized()
            def my_method(self):
                # This method is now thread-safe
                pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_attr, None)
            if lock is None:
                raise AttributeError(f"Object has no attribute '{lock_attr}'")
            with lock:
                return func(self, *args, **kwargs)
        return wrapper
    return decorator


def thread_safe_property(func: Callable) -> property:
    """
    Create a thread-safe property.
    
    This decorator creates a property that acquires the object's
    _lock attribute before accessing the underlying value.
    
    Usage:
        class MyClass:
            def __init__(self):
                self._lock = threading.Lock()
                self._value = 0
            
            @thread_safe_property
            def value(self):
                return self._value
    """
    lock_attr = '_lock'
    
    @functools.wraps(func)
    def getter(self):
        lock = getattr(self, lock_attr, None)
        if lock is None:
            raise AttributeError(f"Object has no attribute '{lock_attr}'")
        with lock:
            return func(self)
    
    return property(getter)


class ResourcePool(Generic[T]):
    """
    Thread-safe resource pool for managing reusable resources.
    
    This pool ensures thread-safe acquisition and release of resources
    with automatic cleanup of idle resources.
    """
    
    def __init__(self, 
                 factory: Callable[[], T],
                 max_size: int = 10,
                 max_idle_time: float = 300.0):
        """
        Initialize the resource pool.
        
        Args:
            factory: Function to create new resources
            max_size: Maximum pool size
            max_idle_time: Time before idle resources are cleaned up
        """
        self._factory = factory
        self._max_size = max_size
        self._max_idle_time = max_idle_time
        self._available: list[tuple[T, float]] = []
        self._in_use: weakref.WeakSet = weakref.WeakSet()
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._running = True
        self._start_cleanup_thread()
    
    def acquire(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Acquire a resource from the pool.
        
        Args:
            timeout: Maximum time to wait for a resource
            
        Returns:
            Resource instance or None if timeout
        """
        deadline = time.time() + timeout if timeout else None
        
        while True:
            with self._lock:
                # Try to get an available resource
                while self._available:
                    resource, _ = self._available.pop()
                    if self._is_resource_valid(resource):
                        self._in_use.add(resource)
                        return resource
                
                # Create new resource if under limit
                if len(self._in_use) < self._max_size:
                    try:
                        resource = self._factory()
                        self._in_use.add(resource)
                        return resource
                    except Exception:
                        return None
            
            # Check timeout
            if deadline and time.time() >= deadline:
                return None
            
            # Wait briefly before retrying
            time.sleep(0.01)
    
    def release(self, resource: T) -> None:
        """
        Release a resource back to the pool.
        
        Args:
            resource: The resource to release
        """
        with self._lock:
            if resource in self._in_use:
                self._in_use.discard(resource)
                self._available.append((resource, time.time()))
    
    def _is_resource_valid(self, resource: T) -> bool:
        """Check if a resource is still valid."""
        # Override in subclasses for custom validation
        return True
    
    def _cleanup_idle_resources(self) -> None:
        """Remove idle resources that have exceeded max idle time."""
        while self._running:
            time.sleep(30)  # Check every 30 seconds
            
            with self._lock:
                current_time = time.time()
                self._available = [
                    (res, ts) for res, ts in self._available
                    if current_time - ts < self._max_idle_time
                ]
    
    def _start_cleanup_thread(self) -> None:
        """Start the cleanup thread."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_idle_resources,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def close(self) -> None:
        """Close the resource pool and clean up resources."""
        self._running = False
        with self._lock:
            self._available.clear()
            self._in_use.clear()


class ThreadLocalStorage:
    """
    Thread-local storage utility.
    
    Provides a simple interface for thread-local data storage.
    """
    
    def __init__(self):
        self._local = threading.local()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get thread-local value."""
        return getattr(self._local, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set thread-local value."""
        setattr(self._local, key, value)
    
    def delete(self, key: str) -> None:
        """Delete thread-local value."""
        if hasattr(self._local, key):
            delattr(self._local, key)
    
    def clear(self) -> None:
        """Clear all thread-local data."""
        self._local = threading.local()


# Global thread-local storage instance
thread_local = ThreadLocalStorage()