# -*- coding: utf-8 -*-
"""
Modern UI Theme System for Video Snippet Remixer.

Provides a comprehensive theming system using CustomTkinter for modern, 
creative UI design with dark theme, vibrant accents, and professional styling.

Features:
- CustomTkinter integration for modern widgets
- Dark theme with creative color palette
- Consistent styling across all components
- Icon integration and visual hierarchy
- Responsive design elements
"""

import customtkinter as ctk
import tkinter as tk
from typing import Dict, Any, Optional, Tuple
import os

# Set global CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModernTheme:
    """
    Modern UI theme configuration for the Snippet Remixer.
    Provides a dark, creative theme with vibrant accents.
    """
    
    # Color Palette - Creative & Professional
    COLORS = {
        # Background Colors
        'bg_primary': '#1a1a1a',      # Main background
        'bg_secondary': '#2d2d30',    # Card/panel background
        'bg_tertiary': '#3e3e42',     # Input backgrounds
        'bg_accent': '#404040',       # Hover states
        
        # Creative Accent Colors
        'accent_primary': '#bb86fc',   # Purple - main accent
        'accent_secondary': '#03dac6', # Cyan - secondary accent
        'accent_gradient_start': '#bb86fc',
        'accent_gradient_end': '#03dac6',
        
        # Status Colors
        'success': '#4caf50',         # Green for success
        'warning': '#ff9800',         # Orange for warnings
        'error': '#f44336',           # Red for errors
        'info': '#2196f3',            # Blue for info
        
        # Text Colors
        'text_primary': '#ffffff',    # Main text
        'text_secondary': '#b3b3b3',  # Secondary text
        'text_muted': '#808080',      # Muted text
        'text_accent': '#bb86fc',     # Accent text
        
        # Border & Outline
        'border_primary': '#404040',
        'border_accent': '#bb86fc',
        'border_light': '#606060',
    }
    
    # Typography
    FONTS = {
        'heading_large': ("Segoe UI", 24, "bold"),
        'heading_medium': ("Segoe UI", 18, "bold"),
        'heading_small': ("Segoe UI", 14, "bold"),
        'body_large': ("Segoe UI", 12),
        'body_medium': ("Segoe UI", 11),
        'body_small': ("Segoe UI", 10),
        'caption': ("Segoe UI", 9),
        'monospace': ("Consolas", 10),
    }
    
    # Spacing & Layout
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48,
    }
    
    # Component Dimensions
    DIMENSIONS = {
        'button_height': 40,
        'input_height': 36,
        'card_padding': 20,
        'section_padding': 16,
        'border_radius': 8,
        'border_width': 2,
    }


class ThemedWidgets:
    """
    Factory class for creating consistently themed UI components.
    """
    
    @staticmethod
    def create_window(title: str = "Snippet Remixer", 
                     width: int = 900, 
                     height: int = 700) -> ctk.CTk:
        """Create a themed main window."""
        window = ctk.CTk()
        window.title(title)
        window.geometry(f"{width}x{height}")
        window.configure(fg_color=ModernTheme.COLORS['bg_primary'])
        
        # Center window on screen
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        return window
    
    @staticmethod
    def create_card(parent, title: str = "", padding: int = None) -> ctk.CTkFrame:
        """Create a themed card/panel with optional title."""
        padding = padding or ModernTheme.DIMENSIONS['card_padding']
        
        card = ctk.CTkFrame(
            parent,
            fg_color=ModernTheme.COLORS['bg_secondary'],
            border_color=ModernTheme.COLORS['border_primary'],
            border_width=1,
            corner_radius=ModernTheme.DIMENSIONS['border_radius']
        )
        
        if title:
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ModernTheme.FONTS['heading_medium'],
                text_color=ModernTheme.COLORS['text_primary']
            )
            title_label.pack(pady=(padding//2, padding//4), padx=padding, anchor="w")
        
        return card
    
    @staticmethod
    def create_button(parent, text: str, command=None, 
                     style: str = "primary", width: int = 140) -> ctk.CTkButton:
        """Create a themed button with different styles."""
        styles = {
            'primary': {
                'fg_color': ModernTheme.COLORS['accent_primary'],
                'hover_color': '#9c5fd8',
                'text_color': ModernTheme.COLORS['text_primary']
            },
            'secondary': {
                'fg_color': ModernTheme.COLORS['bg_tertiary'],
                'hover_color': ModernTheme.COLORS['bg_accent'],
                'text_color': ModernTheme.COLORS['text_primary']
            },
            'accent': {
                'fg_color': ModernTheme.COLORS['accent_secondary'],
                'hover_color': '#02b8a3',
                'text_color': ModernTheme.COLORS['bg_primary']
            },
            'success': {
                'fg_color': ModernTheme.COLORS['success'],
                'hover_color': '#45a049',
                'text_color': ModernTheme.COLORS['text_primary']
            },
            'warning': {
                'fg_color': ModernTheme.COLORS['warning'],
                'hover_color': '#e68900',
                'text_color': ModernTheme.COLORS['text_primary']
            }
        }
        
        style_config = styles.get(style, styles['primary'])
        
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=ModernTheme.DIMENSIONS['button_height'],
            font=ModernTheme.FONTS['body_medium'],
            corner_radius=ModernTheme.DIMENSIONS['border_radius'],
            **style_config
        )
        return button
    
    @staticmethod
    def create_entry(parent, placeholder: str = "", width: int = 200) -> ctk.CTkEntry:
        """Create a themed entry widget."""
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=width,
            height=ModernTheme.DIMENSIONS['input_height'],
            font=ModernTheme.FONTS['body_medium'],
            fg_color=ModernTheme.COLORS['bg_tertiary'],
            border_color=ModernTheme.COLORS['border_primary'],
            corner_radius=ModernTheme.DIMENSIONS['border_radius']
        )
        return entry
    
    @staticmethod
    def create_combobox(parent, values: list, width: int = 200) -> ctk.CTkComboBox:
        """Create a themed combobox."""
        combobox = ctk.CTkComboBox(
            parent,
            values=values,
            width=width,
            height=ModernTheme.DIMENSIONS['input_height'],
            font=ModernTheme.FONTS['body_medium'],
            fg_color=ModernTheme.COLORS['bg_tertiary'],
            border_color=ModernTheme.COLORS['border_primary'],
            corner_radius=ModernTheme.DIMENSIONS['border_radius']
        )
        return combobox
    
    @staticmethod
    def create_label(parent, text: str, style: str = "body") -> ctk.CTkLabel:
        """Create a themed label with different typography styles."""
        styles = {
            'heading_large': {
                'font': ModernTheme.FONTS['heading_large'],
                'text_color': ModernTheme.COLORS['text_primary']
            },
            'heading_medium': {
                'font': ModernTheme.FONTS['heading_medium'],
                'text_color': ModernTheme.COLORS['text_primary']
            },
            'heading_small': {
                'font': ModernTheme.FONTS['heading_small'],
                'text_color': ModernTheme.COLORS['text_primary']
            },
            'body': {
                'font': ModernTheme.FONTS['body_medium'],
                'text_color': ModernTheme.COLORS['text_secondary']
            },
            'body_accent': {
                'font': ModernTheme.FONTS['body_medium'],
                'text_color': ModernTheme.COLORS['accent_primary']
            },
            'caption': {
                'font': ModernTheme.FONTS['caption'],
                'text_color': ModernTheme.COLORS['text_muted']
            },
            'success': {
                'font': ModernTheme.FONTS['body_medium'],
                'text_color': ModernTheme.COLORS['success']
            },
            'warning': {
                'font': ModernTheme.FONTS['body_medium'],
                'text_color': ModernTheme.COLORS['warning']
            },
            'error': {
                'font': ModernTheme.FONTS['body_medium'],
                'text_color': ModernTheme.COLORS['error']
            }
        }
        
        style_config = styles.get(style, styles['body'])
        
        label = ctk.CTkLabel(
            parent,
            text=text,
            **style_config
        )
        return label
    
    @staticmethod
    def create_progress_bar(parent, width: int = 300) -> ctk.CTkProgressBar:
        """Create a themed progress bar."""
        progress = ctk.CTkProgressBar(
            parent,
            width=width,
            height=8,
            corner_radius=4,
            fg_color=ModernTheme.COLORS['bg_tertiary'],
            progress_color=ModernTheme.COLORS['accent_primary']
        )
        return progress
    
    @staticmethod
    def create_switch(parent, text: str) -> ctk.CTkSwitch:
        """Create a themed switch/toggle."""
        switch = ctk.CTkSwitch(
            parent,
            text=text,
            font=ModernTheme.FONTS['body_medium'],
            text_color=ModernTheme.COLORS['text_secondary'],
            fg_color=ModernTheme.COLORS['bg_tertiary'],
            progress_color=ModernTheme.COLORS['accent_primary']
        )
        return switch
    
    @staticmethod
    def create_slider(parent, from_: float, to: float, width: int = 200) -> ctk.CTkSlider:
        """Create a themed slider."""
        slider = ctk.CTkSlider(
            parent,
            from_=from_,
            to=to,
            width=width,
            height=20,
            fg_color=ModernTheme.COLORS['bg_tertiary'],
            progress_color=ModernTheme.COLORS['accent_primary'],
            button_color=ModernTheme.COLORS['accent_secondary'],
            button_hover_color='#02b8a3'
        )
        return slider


class AnimationHelper:
    """
    Helper class for creating smooth animations and transitions.
    """
    
    @staticmethod
    def fade_in(widget, duration: int = 300):
        """Fade in animation for widgets."""
        # Note: CustomTkinter doesn't have built-in animations
        # This is a placeholder for future animation implementation
        widget.configure(fg_color=ModernTheme.COLORS['bg_secondary'])
    
    @staticmethod
    def hover_effect(widget, enter_color: str, leave_color: str):
        """Add hover effects to widgets."""
        def on_enter(event):
            widget.configure(fg_color=enter_color)
        
        def on_leave(event):
            widget.configure(fg_color=leave_color)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


class LayoutHelper:
    """
    Helper class for consistent layouts and spacing.
    """
    
    @staticmethod
    def create_section_header(parent, title: str, subtitle: str = "") -> ctk.CTkFrame:
        """Create a standardized section header."""
        header_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        
        title_label = ThemedWidgets.create_label(header_frame, title, "heading_medium")
        title_label.pack(anchor="w")
        
        if subtitle:
            subtitle_label = ThemedWidgets.create_label(header_frame, subtitle, "caption")
            subtitle_label.pack(anchor="w", pady=(2, 0))
        
        return header_frame
    
    @staticmethod
    def create_form_row(parent, label_text: str, widget) -> ctk.CTkFrame:
        """Create a standardized form row with label and widget."""
        row_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        row_frame.columnconfigure(1, weight=1)
        
        label = ThemedWidgets.create_label(row_frame, label_text, "body")
        label.grid(row=0, column=0, sticky="w", padx=(0, ModernTheme.SPACING['md']))
        
        widget.configure(master=row_frame)
        widget.grid(row=0, column=1, sticky="ew")
        
        return row_frame
    
    @staticmethod
    def add_spacing(parent, size: str = "md"):
        """Add consistent spacing between elements."""
        spacing = ModernTheme.SPACING.get(size, ModernTheme.SPACING['md'])
        spacer = ctk.CTkFrame(parent, height=spacing, fg_color="transparent")
        spacer.pack(fill="x")
        return spacer


class StatusIndicator:
    """
    Utility class for creating status indicators and notifications.
    """
    
    @staticmethod
    def create_status_badge(parent, text: str, status: str = "info") -> ctk.CTkFrame:
        """Create a status badge with appropriate coloring."""
        colors = {
            'info': ModernTheme.COLORS['info'],
            'success': ModernTheme.COLORS['success'],
            'warning': ModernTheme.COLORS['warning'],
            'error': ModernTheme.COLORS['error'],
            'accent': ModernTheme.COLORS['accent_primary']
        }
        
        badge = ctk.CTkFrame(
            parent,
            fg_color=colors.get(status, colors['info']),
            corner_radius=12,
            height=24
        )
        
        label = ctk.CTkLabel(
            badge,
            text=text,
            font=ModernTheme.FONTS['caption'],
            text_color=ModernTheme.COLORS['text_primary']
        )
        label.pack(padx=8, pady=2)
        
        return badge


# Global theme instance
theme = ModernTheme()
widgets = ThemedWidgets()
layout = LayoutHelper()
animations = AnimationHelper()
status = StatusIndicator()