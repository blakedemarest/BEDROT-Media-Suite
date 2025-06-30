# -*- coding: utf-8 -*-
"""
Video Thumbnail and Preview Generation System.

Provides thumbnail generation, preview creation, and visual feedback
for video files in the Snippet Remixer application.

Features:
- Video thumbnail extraction
- Aspect ratio visualization
- File format detection
- Duration estimation display
- Smart caching system
- Error handling for corrupted files
"""

import os
import subprocess
import tempfile
import threading
from typing import Optional, Tuple, List, Dict, Callable
from pathlib import Path
import tkinter as tk
from tkinter import PhotoImage
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import time

from .ui_theme import theme, widgets
from .utils import safe_print


class ThumbnailGenerator:
    """
    Generates thumbnails from video files using FFmpeg.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "snippet_remixer_thumbnails")
        self.ensure_cache_dir()
        self.generation_cache = {}  # In-memory cache for recent thumbnails
        
    def ensure_cache_dir(self):
        """Ensure cache directory exists."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            safe_print(f"Warning: Could not create thumbnail cache directory: {e}")
            self.cache_dir = None
    
    def get_cache_path(self, video_path: str, timestamp: float = 5.0) -> str:
        """Generate cache file path for a video thumbnail."""
        if not self.cache_dir:
            return None
        
        # Create cache filename based on video path and timestamp
        video_name = os.path.basename(video_path)
        cache_name = f"{hash(video_path)}_{timestamp}_{os.path.getmtime(video_path)}.png"
        return os.path.join(self.cache_dir, cache_name)
    
    def generate_thumbnail(self, video_path: str, 
                          timestamp: float = 5.0,
                          width: int = 160,
                          height: int = 90) -> Optional[str]:
        """
        Generate a thumbnail from a video file.
        
        Args:
            video_path: Path to the video file
            timestamp: Time in seconds to extract thumbnail from
            width: Thumbnail width
            height: Thumbnail height
            
        Returns:
            Path to generated thumbnail image or None if failed
        """
        if not os.path.exists(video_path):
            return None
        
        # Check cache first
        cache_path = self.get_cache_path(video_path, timestamp)
        if cache_path and os.path.exists(cache_path):
            return cache_path
        
        # Generate new thumbnail
        try:
            # Create temporary output file
            output_path = cache_path or os.path.join(
                tempfile.gettempdir(),
                f"thumb_{int(time.time())}_{os.getpid()}.png"
            )
            
            # FFmpeg command to extract thumbnail
            cmd = [
                "ffmpeg",
                "-ss", str(timestamp),  # Seek to timestamp
                "-i", video_path,       # Input video
                "-vframes", "1",        # Extract 1 frame
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                       f"pad={width}:{height}:-1:-1:color=black",  # Scale and pad
                "-y",                   # Overwrite output
                output_path
            ]
            
            # Execute FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                safe_print(f"Thumbnail generation failed for {video_path}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            safe_print(f"Thumbnail generation timed out for {video_path}")
            return None
        except Exception as e:
            safe_print(f"Error generating thumbnail for {video_path}: {e}")
            return None
    
    def generate_thumbnail_async(self, video_path: str,
                                callback: Callable[[str, Optional[str]], None],
                                timestamp: float = 5.0,
                                width: int = 160,
                                height: int = 90):
        """
        Generate thumbnail asynchronously and call callback with result.
        
        Args:
            video_path: Path to the video file
            callback: Function to call with (video_path, thumbnail_path)
            timestamp: Time in seconds to extract thumbnail from
            width: Thumbnail width
            height: Thumbnail height
        """
        def generate():
            thumbnail_path = self.generate_thumbnail(video_path, timestamp, width, height)
            callback(video_path, thumbnail_path)
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """Clean up old thumbnail cache files."""
        if not self.cache_dir or not os.path.exists(self.cache_dir):
            return
        
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass  # Ignore errors removing cache files
        except Exception as e:
            safe_print(f"Error cleaning thumbnail cache: {e}")


class VideoInfoExtractor:
    """
    Extracts video information for preview generation.
    """
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, any]:
        """
        Extract comprehensive video information.
        
        Returns:
            Dictionary with video information or empty dict on failure
        """
        if not os.path.exists(video_path):
            return {}
        
        try:
            # Use ffprobe to get video information
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                return {}
            
            import json
            data = json.loads(result.stdout)
            
            # Extract relevant information
            info = {
                'duration': 0,
                'width': 0,
                'height': 0,
                'fps': 0,
                'bitrate': 0,
                'codec': 'unknown',
                'format': 'unknown',
                'file_size': 0
            }
            
            # Get format information
            if 'format' in data:
                format_info = data['format']
                info['duration'] = float(format_info.get('duration', 0))
                info['bitrate'] = int(format_info.get('bit_rate', 0))
                info['format'] = format_info.get('format_name', 'unknown')
                info['file_size'] = int(format_info.get('size', 0))
            
            # Get video stream information
            if 'streams' in data:
                for stream in data['streams']:
                    if stream.get('codec_type') == 'video':
                        info['width'] = int(stream.get('width', 0))
                        info['height'] = int(stream.get('height', 0))
                        info['codec'] = stream.get('codec_name', 'unknown')
                        
                        # Calculate FPS
                        fps_str = stream.get('r_frame_rate', '0/1')
                        if '/' in fps_str:
                            num, den = fps_str.split('/')
                            info['fps'] = float(num) / float(den) if float(den) != 0 else 0
                        break
            
            return info
            
        except subprocess.TimeoutExpired:
            safe_print(f"Video info extraction timed out for {video_path}")
            return {}
        except Exception as e:
            safe_print(f"Error extracting video info for {video_path}: {e}")
            return {}


class PreviewWidget(ctk.CTkFrame):
    """
    Widget for displaying video previews with thumbnails and information.
    """
    
    def __init__(self, parent, video_path: str, thumbnail_generator: ThumbnailGenerator):
        super().__init__(
            parent,
            fg_color=theme.COLORS['bg_secondary'],
            corner_radius=8,
            border_width=1,
            border_color=theme.COLORS['border_primary']
        )
        
        self.video_path = video_path
        self.thumbnail_generator = thumbnail_generator
        self.video_info = {}
        self.thumbnail_image = None
        
        # UI components
        self.thumbnail_label = None
        self.info_frame = None
        self.loading_indicator = None
        
        self.create_ui()
        self.load_video_info()
        self.load_thumbnail()
    
    def create_ui(self):
        """Create the preview widget UI."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Thumbnail section
        thumbnail_frame = ctk.CTkFrame(
            main_frame,
            width=160,
            height=90,
            fg_color=theme.COLORS['bg_tertiary'],
            corner_radius=6
        )
        thumbnail_frame.pack(side="left", padx=(0, 10))
        thumbnail_frame.pack_propagate(False)
        
        # Thumbnail placeholder
        self.thumbnail_label = ctk.CTkLabel(
            thumbnail_frame,
            text="🎬",
            font=theme.FONTS['heading_large'],
            text_color=theme.COLORS['text_muted']
        )
        self.thumbnail_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Loading indicator
        self.loading_indicator = ctk.CTkLabel(
            thumbnail_frame,
            text="⏳",
            font=theme.FONTS['body_medium'],
            text_color=theme.COLORS['accent_primary']
        )
        self.loading_indicator.place(relx=0.9, rely=0.1, anchor="center")
        
        # Info section
        self.info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.info_frame.pack(side="left", fill="both", expand=True)
        
        # File name
        filename = os.path.basename(self.video_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        name_label = widgets.create_label(self.info_frame, filename, "heading_small")
        name_label.pack(anchor="w")
        
        # Create info placeholders
        self.duration_label = widgets.create_label(self.info_frame, "Duration: --", "body")
        self.duration_label.pack(anchor="w", pady=(5, 0))
        
        self.resolution_label = widgets.create_label(self.info_frame, "Resolution: --", "body")
        self.resolution_label.pack(anchor="w")
        
        self.size_label = widgets.create_label(self.info_frame, "Size: --", "body")
        self.size_label.pack(anchor="w")
        
        # Aspect ratio visualization
        self.aspect_ratio_frame = ctk.CTkFrame(
            self.info_frame,
            height=20,
            fg_color="transparent"
        )
        self.aspect_ratio_frame.pack(fill="x", pady=(5, 0))
    
    def load_video_info(self):
        """Load video information asynchronously."""
        def load_info():
            self.video_info = VideoInfoExtractor.get_video_info(self.video_path)
            # Update UI on main thread
            self.after(0, self.update_info_display)
        
        thread = threading.Thread(target=load_info, daemon=True)
        thread.start()
    
    def load_thumbnail(self):
        """Load video thumbnail asynchronously."""
        def thumbnail_callback(video_path: str, thumbnail_path: Optional[str]):
            if thumbnail_path and os.path.exists(thumbnail_path):
                # Load and display thumbnail on main thread
                self.after(0, lambda: self.display_thumbnail(thumbnail_path))
            else:
                # Hide loading indicator
                self.after(0, self.hide_loading_indicator)
        
        self.thumbnail_generator.generate_thumbnail_async(
            self.video_path,
            thumbnail_callback,
            timestamp=min(5.0, self.video_info.get('duration', 10) / 2),  # Middle of video or 5s
            width=160,
            height=90
        )
    
    def display_thumbnail(self, thumbnail_path: str):
        """Display the loaded thumbnail."""
        try:
            # Load image with PIL
            image = Image.open(thumbnail_path)
            
            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Update label
            self.thumbnail_label.configure(
                image=photo,
                text=""
            )
            
            # Keep reference to prevent garbage collection
            self.thumbnail_image = photo
            
        except Exception as e:
            safe_print(f"Error displaying thumbnail: {e}")
        finally:
            self.hide_loading_indicator()
    
    def hide_loading_indicator(self):
        """Hide the loading indicator."""
        self.loading_indicator.place_forget()
    
    def update_info_display(self):
        """Update the information display with loaded video info."""
        if not self.video_info:
            return
        
        # Update duration
        duration = self.video_info.get('duration', 0)
        if duration > 0:
            duration_str = self.format_duration(duration)
            self.duration_label.configure(text=f"⏱️ {duration_str}")
        
        # Update resolution
        width = self.video_info.get('width', 0)
        height = self.video_info.get('height', 0)
        if width > 0 and height > 0:
            self.resolution_label.configure(text=f"📐 {width}×{height}")
            self.create_aspect_ratio_visualization(width, height)
        
        # Update file size
        file_size = self.video_info.get('file_size', 0)
        if file_size > 0:
            size_str = self.format_file_size(file_size)
            self.size_label.configure(text=f"💾 {size_str}")
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def format_file_size(self, bytes_size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"
    
    def create_aspect_ratio_visualization(self, width: int, height: int):
        """Create a visual representation of the aspect ratio."""
        # Calculate aspect ratio
        aspect_ratio = width / height
        
        # Create visual representation
        ar_visual = ctk.CTkFrame(
            self.aspect_ratio_frame,
            height=16,
            fg_color=theme.COLORS['accent_primary'],
            corner_radius=2
        )
        
        # Set width based on aspect ratio (normalized to container)
        if aspect_ratio > 2:
            # Very wide
            ar_visual.configure(width=80)
        elif aspect_ratio > 1.5:
            # Wide (16:9, etc.)
            ar_visual.configure(width=60)
        elif aspect_ratio > 0.8:
            # Square-ish
            ar_visual.configure(width=40)
        else:
            # Tall (9:16, etc.)
            ar_visual.configure(width=20)
        
        ar_visual.pack(side="left")
        
        # Add ratio text
        ratio_text = f"{aspect_ratio:.2f}:1"
        if abs(aspect_ratio - 16/9) < 0.1:
            ratio_text = "16:9"
        elif abs(aspect_ratio - 9/16) < 0.1:
            ratio_text = "9:16"
        elif abs(aspect_ratio - 1) < 0.1:
            ratio_text = "1:1"
        elif abs(aspect_ratio - 4/3) < 0.1:
            ratio_text = "4:3"
        
        ratio_label = widgets.create_label(
            self.aspect_ratio_frame,
            ratio_text,
            "caption"
        )
        ratio_label.pack(side="left", padx=(10, 0))


class AspectRatioPreview(ctk.CTkFrame):
    """
    Widget for previewing different aspect ratios.
    """
    
    def __init__(self, parent, current_ratio: str = "16:9"):
        super().__init__(
            parent,
            fg_color=theme.COLORS['bg_secondary'],
            corner_radius=8
        )
        
        self.current_ratio = current_ratio
        self.create_ui()
    
    def create_ui(self):
        """Create the aspect ratio preview UI."""
        # Title
        title = widgets.create_label(self, "📐 Output Preview", "heading_small")
        title.pack(pady=(15, 10))
        
        # Preview container
        preview_container = ctk.CTkFrame(
            self,
            fg_color=theme.COLORS['bg_tertiary'],
            corner_radius=6
        )
        preview_container.pack(padx=20, pady=(0, 15))
        
        # Create preview rectangle
        self.create_preview_rectangle(preview_container)
        
        # Ratio info
        ratio_info = widgets.create_label(
            self,
            f"Aspect Ratio: {self.current_ratio}",
            "body"
        )
        ratio_info.pack(pady=(0, 15))
    
    def create_preview_rectangle(self, parent):
        """Create a visual preview rectangle."""
        # Parse aspect ratio
        ratio_parts = self.current_ratio.split('x')
        if len(ratio_parts) == 2:
            try:
                width_part = ratio_parts[0].strip()
                height_part = ratio_parts[1].split()[0].strip()  # Remove description
                width = int(width_part)
                height = int(height_part)
                aspect_ratio = width / height
            except (ValueError, ZeroDivisionError):
                aspect_ratio = 16 / 9  # Default
        else:
            aspect_ratio = 16 / 9  # Default
        
        # Calculate preview dimensions (max 200px width)
        max_width = 200
        if aspect_ratio >= 1:
            # Landscape or square
            preview_width = max_width
            preview_height = int(max_width / aspect_ratio)
        else:
            # Portrait
            preview_height = max_width
            preview_width = int(max_width * aspect_ratio)
        
        # Create preview frame
        preview_frame = ctk.CTkFrame(
            parent,
            width=preview_width,
            height=preview_height,
            fg_color=theme.COLORS['accent_primary'],
            corner_radius=4,
            border_width=2,
            border_color=theme.COLORS['accent_secondary']
        )
        preview_frame.pack(padx=20, pady=20)
        preview_frame.pack_propagate(False)
        
        # Add preview content
        preview_label = widgets.create_label(
            preview_frame,
            "🎬",
            "heading_medium"
        )
        preview_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def update_ratio(self, new_ratio: str):
        """Update the preview with a new aspect ratio."""
        self.current_ratio = new_ratio
        # Clear and recreate UI
        for widget in self.winfo_children():
            widget.destroy()
        self.create_ui()


# Global thumbnail generator instance
thumbnail_generator = ThumbnailGenerator()
video_info_extractor = VideoInfoExtractor()