# -*- coding: utf-8 -*-
"""
BEDROT theme configuration for Tkinter.

Extracted from main_app.py to decouple theme/styling from application logic.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


BEDROT_COLORS = {
    "bg": "#121212",
    "bg_secondary": "#1a1a1a",
    "bg_tertiary": "#202020",
    "bg_hover": "#252525",
    "fg": "#e0e0e0",
    "fg_secondary": "#cccccc",
    "accent_green": "#00ff88",
    "accent_cyan": "#00ffff",
    "accent_magenta": "#ff00ff",
    "accent_pink": "#ff00aa",
    "accent_red": "#ff0066",
    "accent_orange": "#ff8800",
    "border": "#404040",
}


def apply_bedrot_theme(root: tk.Tk) -> dict:
    """
    Apply the BEDROT cyberpunk visual theme to the application.

    Args:
        root: The Tkinter root window to apply the theme to.

    Returns:
        Dictionary of color values for use in widget configuration.
    """
    colors = BEDROT_COLORS.copy()

    # Configure root window
    root.configure(bg=colors["bg"])

    # Configure ttk styles
    style = ttk.Style()
    style.theme_use("clam")  # Use clam as base for better customization

    # Configure Frame styles
    style.configure("TFrame", background=colors["bg"], borderwidth=0)

    # Configure LabelFrame with cyberpunk border
    style.configure(
        "TLabelFrame",
        background=colors["bg"],
        foreground=colors["accent_cyan"],
        bordercolor=colors["accent_cyan"],
        darkcolor=colors["accent_cyan"],
        lightcolor=colors["accent_cyan"],
        borderwidth=1,
        relief="flat",
        labelmargins=10,
    )
    style.configure(
        "TLabelFrame.Label",
        background=colors["bg"],
        foreground=colors["accent_cyan"],
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "TLabelFrame",
        bordercolor=[("focus", colors["accent_green"])],
        darkcolor=[("focus", colors["accent_green"])],
        lightcolor=[("focus", colors["accent_green"])],
    )

    # Configure Labels
    style.configure(
        "TLabel",
        background=colors["bg"],
        foreground=colors["fg"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "Status.TLabel",
        background=colors["bg"],
        foreground=colors["accent_green"],
        font=("Segoe UI", 9),
    )
    style.configure(
        "Blue.TLabel",
        background=colors["bg"],
        foreground=colors["accent_cyan"],
        font=("Segoe UI", 9),
    )

    # Configure Entry widgets
    style.configure(
        "TEntry",
        fieldbackground=colors["bg_secondary"],
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        insertcolor=colors["accent_cyan"],
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "TEntry",
        fieldbackground=[("focus", colors["bg_tertiary"])],
        bordercolor=[("focus", colors["accent_cyan"])],
    )

    # Configure Combobox
    style.configure(
        "TCombobox",
        fieldbackground=colors["bg_secondary"],
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        selectbackground=colors["accent_cyan"],
        selectforeground="#000000",
        borderwidth=1,
        arrowcolor=colors["accent_green"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("focus", colors["bg_tertiary"])],
        bordercolor=[("focus", colors["accent_cyan"])],
    )

    # Configure Spinbox
    style.configure(
        "TSpinbox",
        fieldbackground=colors["bg_secondary"],
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        insertcolor=colors["accent_cyan"],
        borderwidth=1,
        arrowcolor=colors["accent_green"],
        arrowsize=12,
    )
    style.map(
        "TSpinbox",
        fieldbackground=[("focus", colors["bg_tertiary"])],
        bordercolor=[("focus", colors["accent_cyan"])],
    )

    # Configure Buttons with BEDROT style
    style.configure(
        "TButton",
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        borderwidth=1,
        focuscolor="none",
        font=("Segoe UI", 11, "bold"),
        relief="solid",
    )
    style.map(
        "TButton",
        background=[("active", colors["bg_hover"]), ("pressed", colors["bg"])],
        foreground=[("active", colors["accent_green"]), ("pressed", colors["accent_cyan"])],
    )

    # Generate button (green accent)
    style.configure(
        "Generate.TButton",
        background=colors["accent_green"],
        foreground="#000000",
        borderwidth=0,
        focuscolor="none",
        font=("Segoe UI", 11, "bold"),
    )
    style.map(
        "Generate.TButton",
        background=[("active", "#00ffaa"), ("pressed", "#00cc66")],
        foreground=[("active", "#000000"), ("pressed", "#000000")],
    )

    # Stop/Abort buttons (red accent)
    style.configure(
        "Stop.TButton",
        background=colors["accent_red"],
        foreground="#ffffff",
        borderwidth=0,
        focuscolor="none",
        font=("Segoe UI", 11, "bold"),
    )
    style.map(
        "Stop.TButton",
        background=[("active", "#ff3388"), ("pressed", "#cc0044")],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )

    # Browse buttons (cyan border)
    style.configure(
        "Browse.TButton",
        background=colors["bg_secondary"],
        foreground=colors["accent_cyan"],
        borderwidth=1,
        relief="solid",
        focuscolor="none",
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Browse.TButton",
        background=[("active", colors["bg_hover"]), ("pressed", colors["bg"])],
        foreground=[("active", "#66ffff"), ("pressed", colors["accent_cyan"])],
    )

    # Configure Radiobuttons
    style.configure(
        "TRadiobutton",
        background=colors["bg"],
        foreground=colors["fg"],
        focuscolor="none",
        font=("Segoe UI", 10),
    )
    style.map(
        "TRadiobutton",
        background=[("active", colors["bg"])],
        foreground=[("active", colors["accent_green"]), ("selected", colors["accent_cyan"])],
    )

    # Configure Checkbuttons
    style.configure(
        "TCheckbutton",
        background=colors["bg"],
        foreground=colors["fg"],
        focuscolor="none",
        font=("Segoe UI", 10),
    )
    style.map(
        "TCheckbutton",
        background=[("active", colors["bg"])],
        foreground=[("active", colors["accent_green"]), ("selected", colors["accent_cyan"])],
    )

    # Configure Scale (slider)
    style.configure(
        "Horizontal.TScale",
        background=colors["bg"],
        troughcolor=colors["bg_secondary"],
        borderwidth=1,
        lightcolor=colors["bg"],
        darkcolor=colors["bg"],
        bordercolor=colors["border"],
        sliderrelief="flat",
    )
    style.map("Horizontal.TScale", troughcolor=[("active", colors["bg_tertiary"])])

    # Configure Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=colors["bg_secondary"],
        troughcolor="#0a0a0a",
        borderwidth=1,
        arrowcolor=colors["accent_green"],
        width=14,
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", colors["accent_green"]), ("pressed", colors["accent_cyan"])],
    )

    return colors
