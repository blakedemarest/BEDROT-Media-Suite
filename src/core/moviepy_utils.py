# -*- coding: utf-8 -*-
"""
MoviePy Resource Management Utilities.

Provides context managers and utilities for proper MoviePy clip resource management
to prevent memory leaks and ensure cleanup even in error conditions.
"""

import contextlib
import gc
from typing import List, Optional, Union, Iterator
from moviepy.editor import VideoClip, AudioClip, ImageClip, VideoFileClip, AudioFileClip


class ClipManager:
    """
    Context manager for MoviePy clips that ensures proper cleanup.
    
    Usage:
        with ClipManager() as manager:
            clip1 = manager.add(VideoFileClip("video.mp4"))
            clip2 = manager.add(ImageClip("image.png"))
            # Use clips...
        # All clips are automatically closed
    """
    
    def __init__(self):
        self.clips: List[Union[VideoClip, AudioClip]] = []
        self._entered = False
    
    def add(self, clip: Union[VideoClip, AudioClip]) -> Union[VideoClip, AudioClip]:
        """
        Add a clip to be managed.
        
        Args:
            clip: The MoviePy clip to manage
            
        Returns:
            The same clip for chaining
        """
        if not self._entered:
            raise RuntimeError("ClipManager must be used within a context (with statement)")
        self.clips.append(clip)
        return clip
    
    def __enter__(self):
        self._entered = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._entered = False
        self.cleanup()
        # Force garbage collection after cleanup
        gc.collect()
        return False  # Don't suppress exceptions
    
    def cleanup(self):
        """Close all managed clips."""
        for clip in self.clips:
            try:
                if hasattr(clip, 'close') and callable(clip.close):
                    clip.close()
            except Exception:
                pass  # Ignore errors during cleanup
        self.clips.clear()


@contextlib.contextmanager
def managed_clip(clip_factory, *args, **kwargs):
    """
    Context manager for a single MoviePy clip.
    
    Args:
        clip_factory: A callable that creates a MoviePy clip (e.g., VideoFileClip)
        *args, **kwargs: Arguments to pass to the clip factory
        
    Yields:
        The created clip
        
    Example:
        with managed_clip(VideoFileClip, "video.mp4") as clip:
            # Use clip...
        # Clip is automatically closed
    """
    clip = None
    try:
        clip = clip_factory(*args, **kwargs)
        yield clip
    finally:
        if clip is not None:
            try:
                if hasattr(clip, 'close') and callable(clip.close):
                    clip.close()
            except Exception:
                pass
        gc.collect()


@contextlib.contextmanager
def managed_clips(*clips: Union[VideoClip, AudioClip]) -> Iterator[List[Union[VideoClip, AudioClip]]]:
    """
    Context manager for multiple MoviePy clips.
    
    Args:
        *clips: MoviePy clips to manage
        
    Yields:
        List of the clips
        
    Example:
        clip1 = VideoFileClip("video1.mp4")
        clip2 = VideoFileClip("video2.mp4")
        with managed_clips(clip1, clip2) as clips:
            # Use clips...
        # All clips are automatically closed
    """
    try:
        yield list(clips)
    finally:
        for clip in clips:
            try:
                if hasattr(clip, 'close') and callable(clip.close):
                    clip.close()
            except Exception:
                pass
        gc.collect()


def safe_close_clip(clip: Optional[Union[VideoClip, AudioClip]]) -> None:
    """
    Safely close a MoviePy clip, ignoring any errors.
    
    Args:
        clip: The clip to close (can be None)
    """
    if clip is not None:
        try:
            if hasattr(clip, 'close') and callable(clip.close):
                clip.close()
        except Exception:
            pass


def safe_close_clips(clips: List[Optional[Union[VideoClip, AudioClip]]]) -> None:
    """
    Safely close multiple MoviePy clips.
    
    Args:
        clips: List of clips to close (can contain None values)
    """
    for clip in clips:
        safe_close_clip(clip)
    gc.collect()


class BatchClipProcessor:
    """
    Helper class for processing multiple clips with automatic resource management.
    
    Example:
        processor = BatchClipProcessor()
        try:
            for path in image_paths:
                clip = processor.create_clip(ImageClip, path)
                clip = clip.set_duration(2.0)
                processor.processed_clips.append(clip)
            
            final = concatenate_videoclips(processor.processed_clips)
            # Use final clip...
        finally:
            processor.cleanup()
    """
    
    def __init__(self):
        self.source_clips: List[Union[VideoClip, AudioClip]] = []
        self.processed_clips: List[Union[VideoClip, AudioClip]] = []
        self.temp_clips: List[Union[VideoClip, AudioClip]] = []
    
    def create_clip(self, clip_factory, *args, **kwargs) -> Union[VideoClip, AudioClip]:
        """
        Create a clip and add it to source clips for tracking.
        
        Args:
            clip_factory: Clip creation function
            *args, **kwargs: Arguments for clip creation
            
        Returns:
            The created clip
        """
        clip = clip_factory(*args, **kwargs)
        self.source_clips.append(clip)
        return clip
    
    def add_temp_clip(self, clip: Union[VideoClip, AudioClip]) -> Union[VideoClip, AudioClip]:
        """
        Add a temporary/intermediate clip for tracking.
        
        Args:
            clip: The clip to track
            
        Returns:
            The same clip for chaining
        """
        self.temp_clips.append(clip)
        return clip
    
    def cleanup(self):
        """Clean up all tracked clips."""
        # Close in reverse order (processed -> temp -> source)
        safe_close_clips(self.processed_clips)
        safe_close_clips(self.temp_clips)
        safe_close_clips(self.source_clips)
        
        # Clear all lists
        self.processed_clips.clear()
        self.temp_clips.clear()
        self.source_clips.clear()
        
        # Force garbage collection
        gc.collect()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


# Convenience functions for common clip types
@contextlib.contextmanager
def video_file_clip(path: str, **kwargs):
    """Context manager for VideoFileClip."""
    with managed_clip(VideoFileClip, path, **kwargs) as clip:
        yield clip


@contextlib.contextmanager
def audio_file_clip(path: str, **kwargs):
    """Context manager for AudioFileClip."""
    with managed_clip(AudioFileClip, path, **kwargs) as clip:
        yield clip


@contextlib.contextmanager
def image_clip(path_or_array, **kwargs):
    """Context manager for ImageClip."""
    with managed_clip(ImageClip, path_or_array, **kwargs) as clip:
        yield clip