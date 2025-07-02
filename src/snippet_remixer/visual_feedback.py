# -*- coding: utf-8 -*-
"""
Visual Feedback and Progress System for Video Snippet Remixer.

Provides comprehensive visual feedback including:
- Animated progress indicators
- Real-time status updates
- Visual processing stages
- Success/error feedback
- Estimation and time remaining
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional, Dict, Any
import time
import threading
from datetime import datetime, timedelta

from .ui_theme import theme, widgets, layout


class ProgressVisualization:
    """
    Advanced progress visualization with animations and status updates.
    """
    
    def __init__(self, parent, title: str = "Processing"):
        self.parent = parent
        self.title = title
        self.start_time = None
        self.current_stage = 0
        self.total_stages = 6
        self.estimated_total_time = 0
        
        # Progress tracking
        self.stage_progress = {}
        self.overall_progress = 0.0
        
        # UI components
        self.main_frame = None
        self.progress_bar = None
        self.stage_indicators = []
        self.status_label = None
        self.time_label = None
        self.detail_label = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the progress visualization UI."""
        self.main_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        self.main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = widgets.create_label(
            self.main_frame,
            self.title,
            "heading_medium"
        )
        title_label.pack(pady=(0, 20))
        
        # Main progress bar
        progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 30))
        
        self.progress_bar = widgets.create_progress_bar(progress_frame, 400)
        self.progress_bar.pack()
        self.progress_bar.set(0)
        
        # Progress percentage
        self.progress_label = widgets.create_label(
            progress_frame,
            "0%",
            "heading_small"
        )
        self.progress_label.pack(pady=(10, 0))
        
        # Stage indicators
        self.create_stage_indicators()
        
        # Status information
        self.create_status_section()
        
        # Time information
        self.create_time_section()
    
    def create_stage_indicators(self):
        """Create visual indicators for each processing stage."""
        stages_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        stages_frame.pack(fill="x", pady=(0, 30))
        
        stages = [
            ("🔍", "Analyzing", "Scanning input videos"),
            ("📏", "Measuring", "Getting video information"),
            ("🎯", "Planning", "Generating snippet plan"),
            ("✂️", "Cutting", "Extracting video segments"),
            ("🔗", "Joining", "Combining segments"),
            ("🎨", "Finalizing", "Applying final touches")
        ]
        
        # Create grid layout for stages
        for i, (icon, title, description) in enumerate(stages):
            stage_container = self.create_stage_indicator(
                stages_frame, icon, title, description
            )
            
            # Calculate grid position
            row = i // 3
            col = i % 3
            stage_container.grid(
                row=row, column=col,
                padx=15, pady=10,
                sticky="ew"
            )
            
            # Configure column weights for equal distribution
            stages_frame.columnconfigure(col, weight=1)
    
    def create_stage_indicator(self, parent, icon: str, title: str, description: str) -> ctk.CTkFrame:
        """Create a single stage indicator."""
        container = ctk.CTkFrame(
            parent,
            fg_color=theme.COLORS['bg_tertiary'],
            corner_radius=8,
            border_width=1,
            border_color=theme.COLORS['border_primary']
        )
        
        # Icon circle
        icon_frame = ctk.CTkFrame(
            container,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=theme.COLORS['bg_secondary']
        )
        icon_frame.pack(pady=(15, 10))
        icon_frame.pack_propagate(False)
        
        icon_label = widgets.create_label(icon_frame, icon, "body_large")
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        title_label = widgets.create_label(container, title, "heading_small")
        title_label.pack()
        
        # Description
        desc_label = widgets.create_label(container, description, "caption")
        desc_label.pack(pady=(2, 15))
        
        # Store references
        indicator_data = {
            'container': container,
            'icon_frame': icon_frame,
            'icon_label': icon_label,
            'title_label': title_label,
            'desc_label': desc_label,
            'active': False
        }
        
        self.stage_indicators.append(indicator_data)
        return container
    
    def create_status_section(self):
        """Create status information section."""
        status_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=theme.COLORS['bg_secondary'],
            corner_radius=8
        )
        status_frame.pack(fill="x", pady=(0, 20))
        
        # Current status
        status_header = widgets.create_label(
            status_frame,
            "📊 Current Status",
            "heading_small"
        )
        status_header.pack(pady=(15, 5), padx=20, anchor="w")
        
        self.status_label = widgets.create_label(
            status_frame,
            "Initializing...",
            "body"
        )
        self.status_label.pack(padx=20, anchor="w")
        
        # Detail information
        self.detail_label = widgets.create_label(
            status_frame,
            "",
            "caption"
        )
        self.detail_label.pack(padx=20, pady=(5, 15), anchor="w")
    
    def create_time_section(self):
        """Create time estimation section."""
        time_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=theme.COLORS['bg_secondary'],
            corner_radius=8
        )
        time_frame.pack(fill="x")
        
        # Time header
        time_header = widgets.create_label(
            time_frame,
            "⏱️ Time Information",
            "heading_small"
        )
        time_header.pack(pady=(15, 5), padx=20, anchor="w")
        
        # Time details container
        time_details = ctk.CTkFrame(time_frame, fg_color="transparent")
        time_details.pack(fill="x", padx=20, pady=(0, 15))
        
        # Configure grid
        time_details.columnconfigure(0, weight=1)
        time_details.columnconfigure(1, weight=1)
        time_details.columnconfigure(2, weight=1)
        
        # Elapsed time
        self.elapsed_label = widgets.create_label(time_details, "Elapsed: --", "body")
        self.elapsed_label.grid(row=0, column=0, sticky="w")
        
        # Remaining time
        self.remaining_label = widgets.create_label(time_details, "Remaining: --", "body")
        self.remaining_label.grid(row=0, column=1, sticky="w")
        
        # Total estimated
        self.total_label = widgets.create_label(time_details, "Total: --", "body")
        self.total_label.grid(row=0, column=2, sticky="w")
    
    def start_processing(self, estimated_duration: Optional[float] = None):
        """Start the processing with optional time estimation."""
        self.start_time = time.time()
        self.estimated_total_time = estimated_duration or 60  # Default 60 seconds
        
        # Start time update thread
        self.update_time_display()
    
    def update_progress(self, stage: int, stage_progress: float, 
                       status: str, detail: str = ""):
        """Update progress for a specific stage."""
        self.current_stage = max(stage, self.current_stage)
        self.stage_progress[stage] = stage_progress
        
        # Calculate overall progress
        completed_stages = sum(1 for s in range(stage) if self.stage_progress.get(s, 0) >= 1.0)
        current_stage_contribution = stage_progress / self.total_stages
        self.overall_progress = (completed_stages + current_stage_contribution) / self.total_stages
        
        # Update UI
        self.progress_bar.set(self.overall_progress)
        self.progress_label.configure(text=f"{int(self.overall_progress * 100)}%")
        
        # Update stage indicators
        self.update_stage_indicators(stage)
        
        # Update status
        self.status_label.configure(text=status)
        if detail:
            self.detail_label.configure(text=detail)
    
    def update_stage_indicators(self, current_stage: int):
        """Update visual stage indicators."""
        for i, indicator in enumerate(self.stage_indicators):
            if i < current_stage:
                # Completed stage
                indicator['icon_frame'].configure(fg_color=theme.COLORS['success'])
                indicator['title_label'].configure(text_color=theme.COLORS['success'])
                indicator['container'].configure(border_color=theme.COLORS['success'])
            elif i == current_stage:
                # Active stage
                indicator['icon_frame'].configure(fg_color=theme.COLORS['accent_primary'])
                indicator['title_label'].configure(text_color=theme.COLORS['accent_primary'])
                indicator['container'].configure(border_color=theme.COLORS['accent_primary'])
                indicator['active'] = True
            else:
                # Future stage
                indicator['icon_frame'].configure(fg_color=theme.COLORS['bg_secondary'])
                indicator['title_label'].configure(text_color=theme.COLORS['text_muted'])
                indicator['container'].configure(border_color=theme.COLORS['border_primary'])
                indicator['active'] = False
    
    def update_time_display(self):
        """Update time display labels."""
        if not self.start_time:
            return
        
        def update():
            while self.overall_progress < 1.0 and self.start_time:
                elapsed = time.time() - self.start_time
                
                # Calculate remaining time
                if self.overall_progress > 0:
                    estimated_total = elapsed / self.overall_progress
                    remaining = max(0, estimated_total - elapsed)
                else:
                    remaining = self.estimated_total_time
                    estimated_total = self.estimated_total_time
                
                # Format times
                elapsed_str = self.format_time(elapsed)
                remaining_str = self.format_time(remaining)
                total_str = self.format_time(estimated_total)
                
                # Update labels on main thread
                self.parent.after(0, lambda: self.elapsed_label.configure(text=f"Elapsed: {elapsed_str}"))
                self.parent.after(0, lambda: self.remaining_label.configure(text=f"Remaining: {remaining_str}"))
                self.parent.after(0, lambda: self.total_label.configure(text=f"Total: {total_str}"))
                
                time.sleep(1)
        
        thread = threading.Thread(target=update, daemon=True)
        thread.start()
    
    def format_time(self, seconds: float) -> str:
        """Format time in human-readable format."""
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
    
    def complete_processing(self, success: bool = True):
        """Mark processing as complete."""
        if success:
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="100%")
            self.status_label.configure(text="✅ Processing Complete!")
            self.detail_label.configure(text="Your remix is ready!")
            
            # Mark all stages as complete
            for indicator in self.stage_indicators:
                indicator['icon_frame'].configure(fg_color=theme.COLORS['success'])
                indicator['title_label'].configure(text_color=theme.COLORS['success'])
                indicator['container'].configure(border_color=theme.COLORS['success'])
        else:
            self.status_label.configure(text="❌ Processing Failed")
            self.detail_label.configure(text="Check the details for more information")


class NotificationSystem:
    """
    System for showing toast notifications and feedback messages.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
    
    def show_toast(self, message: str, notification_type: str = "info", 
                   duration: int = 3000):
        """Show a toast notification."""
        # Create notification frame
        notification = ctk.CTkFrame(
            self.parent,
            fg_color=self.get_notification_color(notification_type),
            corner_radius=8,
            border_width=1,
            border_color=theme.COLORS['border_light']
        )
        
        # Position at top-right
        notification.place(relx=0.98, rely=0.02, anchor="ne")
        
        # Content
        content_frame = ctk.CTkFrame(notification, fg_color="transparent")
        content_frame.pack(padx=15, pady=10)
        
        # Icon
        icon = self.get_notification_icon(notification_type)
        icon_label = widgets.create_label(content_frame, icon, "body_large")
        icon_label.pack(side="left", padx=(0, 10))
        
        # Message
        message_label = widgets.create_label(content_frame, message, "body")
        message_label.pack(side="left")
        
        # Auto-hide after duration
        self.parent.after(duration, lambda: self.hide_notification(notification))
        
        self.notifications.append(notification)
        return notification
    
    def get_notification_color(self, notification_type: str) -> str:
        """Get color for notification type."""
        colors = {
            'info': theme.COLORS['info'],
            'success': theme.COLORS['success'],
            'warning': theme.COLORS['warning'],
            'error': theme.COLORS['error'],
            'accent': theme.COLORS['accent_primary']
        }
        return colors.get(notification_type, colors['info'])
    
    def get_notification_icon(self, notification_type: str) -> str:
        """Get icon for notification type."""
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'accent': '🎨'
        }
        return icons.get(notification_type, icons['info'])
    
    def hide_notification(self, notification):
        """Hide a notification with fade out effect."""
        if notification in self.notifications:
            self.notifications.remove(notification)
        notification.destroy()


class LoadingSpinner:
    """
    Animated loading spinner widget.
    """
    
    def __init__(self, parent, size: int = 40):
        self.parent = parent
        self.size = size
        self.frame = None
        self.canvas = None
        self.spinning = False
        self.angle = 0
        
        self.create_spinner()
    
    def create_spinner(self):
        """Create the spinner widget."""
        self.frame = ctk.CTkFrame(
            self.parent,
            width=self.size + 10,
            height=self.size + 10,
            fg_color="transparent"
        )
        
        # Create canvas for custom drawing
        self.canvas = tk.Canvas(
            self.frame,
            width=self.size,
            height=self.size,
            bg=theme.COLORS['bg_primary'],
            highlightthickness=0
        )
        self.canvas.pack(expand=True)
    
    def start(self):
        """Start the spinning animation."""
        self.spinning = True
        self.animate()
    
    def stop(self):
        """Stop the spinning animation."""
        self.spinning = False
    
    def animate(self):
        """Animate the spinner."""
        if not self.spinning:
            return
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw spinner arcs
        center = self.size // 2
        radius = center - 5
        
        # Draw multiple arcs with different opacities
        for i in range(8):
            start_angle = (self.angle + i * 45) % 360
            opacity = 1.0 - (i * 0.1)
            
            # Convert hex color to RGB and apply opacity
            color = self.apply_opacity_to_color(theme.COLORS['accent_primary'], opacity)
            
            self.canvas.create_arc(
                center - radius, center - radius,
                center + radius, center + radius,
                start=start_angle, extent=30,
                outline=color, width=3,
                style="arc"
            )
        
        # Update angle
        self.angle = (self.angle + 10) % 360
        
        # Schedule next frame
        self.parent.after(50, self.animate)
    
    def apply_opacity_to_color(self, hex_color: str, opacity: float) -> str:
        """Apply opacity to a hex color."""
        # Simple opacity simulation by blending with background
        # This is a simplified version - in a real implementation,
        # you might want more sophisticated color blending
        if opacity >= 0.8:
            return hex_color
        elif opacity >= 0.6:
            return theme.COLORS['accent_secondary']
        elif opacity >= 0.4:
            return theme.COLORS['bg_accent']
        else:
            return theme.COLORS['bg_tertiary']
    
    def pack(self, **kwargs):
        """Pack the spinner frame."""
        self.frame.pack(**kwargs)
    
    def place(self, **kwargs):
        """Place the spinner frame."""
        self.frame.place(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the spinner frame."""
        self.frame.grid(**kwargs)


class SuccessAnimation:
    """
    Success animation widget with celebratory effects.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = None
        self.create_animation()
    
    def create_animation(self):
        """Create the success animation."""
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent"
        )
        
        # Success icon with glow effect
        icon_frame = ctk.CTkFrame(
            self.frame,
            width=80,
            height=80,
            corner_radius=40,
            fg_color=theme.COLORS['success'],
            border_width=3,
            border_color=theme.COLORS['accent_secondary']
        )
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        
        # Success icon
        success_icon = widgets.create_label(icon_frame, "✨", "heading_large")
        success_icon.place(relx=0.5, rely=0.5, anchor="center")
        
        # Celebration text
        celebration_text = widgets.create_label(
            self.frame,
            "🎉 Amazing work! 🎉",
            "heading_medium"
        )
        celebration_text.pack(pady=(20, 10))
        
        # Start animation
        self.animate_success()
    
    def animate_success(self):
        """Animate the success display."""
        # Simple pulse animation
        def pulse():
            original_color = theme.COLORS['success']
            bright_color = theme.COLORS['accent_primary']
            
            # Pulse effect (simplified)
            self.parent.after(200, lambda: None)  # Placeholder for animation
        
        pulse()
    
    def pack(self, **kwargs):
        """Pack the animation frame."""
        self.frame.pack(**kwargs)


# Factory class for creating feedback components
class FeedbackFactory:
    """
    Factory class for creating various feedback components.
    """
    
    @staticmethod
    def create_progress_visualization(parent, title: str = "Processing") -> ProgressVisualization:
        """Create a progress visualization component."""
        return ProgressVisualization(parent, title)
    
    @staticmethod
    def create_notification_system(parent) -> NotificationSystem:
        """Create a notification system."""
        return NotificationSystem(parent)
    
    @staticmethod
    def create_loading_spinner(parent, size: int = 40) -> LoadingSpinner:
        """Create a loading spinner."""
        return LoadingSpinner(parent, size)
    
    @staticmethod
    def create_success_animation(parent) -> SuccessAnimation:
        """Create a success animation."""
        return SuccessAnimation(parent)


# Global feedback factory instance
feedback = FeedbackFactory()