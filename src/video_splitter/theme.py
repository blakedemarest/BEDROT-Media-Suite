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
    "bg_active": "#2a2a2a",
    "fg": "#e0e0e0",
    "fg_secondary": "#cccccc",
    "text_muted": "#888888",
    "border": "#404040",
    "accent_green": "#00ff88",
    "accent_cyan": "#00ffff",
    "accent_red": "#ff0066",
    "accent_green_hover": "#00ffaa",
    "accent_green_pressed": "#00cc66",
    "accent_red_hover": "#ff3388",
    "accent_red_pressed": "#cc0044",
}


def apply_bedrot_theme(root: tk.Tk) -> dict:
    """
    Configure Tkinter styles according to the BEDROT visual guidelines.

    Args:
        root: The Tkinter root window to apply the theme to.

    Returns:
        Dictionary of color values for use in widget configuration.
    """
    colors = BEDROT_COLORS.copy()

    style = ttk.Style()
    style.theme_use("clam")

    root.configure(bg=colors["bg"])
    root.option_add("*Font", "{Segoe UI} 10")

    style.configure("TFrame", background=colors["bg"], borderwidth=0)
    style.configure(
        "TLabelFrame",
        background=colors["bg"],
        foreground=colors["accent_cyan"],
        bordercolor=colors["accent_cyan"],
        labelmargins=10,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TLabelFrame.Label",
        background=colors["bg"],
        foreground=colors["accent_cyan"],
        font=("Segoe UI", 10, "bold"),
    )

    style.configure("TLabel", background=colors["bg"], foreground=colors["fg"], font=("Segoe UI", 10))
    style.configure(
        "Hint.TLabel",
        background=colors["bg"],
        foreground=colors["text_muted"],
        font=("Segoe UI", 9, "italic"),
    )
    style.configure(
        "Status.TLabel", background=colors["bg"], foreground=colors["accent_green"], font=("Segoe UI", 9, "bold")
    )
    style.configure(
        "Accent.TLabel",
        background=colors["bg"],
        foreground=colors["accent_cyan"],
        font=("Segoe UI", 9, "bold"),
    )

    style.configure(
        "TEntry",
        fieldbackground=colors["bg_secondary"],
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        insertcolor=colors["accent_cyan"],
        borderwidth=1,
        relief="solid",
    )
    style.map("TEntry", fieldbackground=[("focus", colors["bg_tertiary"])])

    style.configure(
        "TSpinbox",
        fieldbackground=colors["bg_secondary"],
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        arrowsize=14,
        insertcolor=colors["accent_cyan"],
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Secondary.TButton",
        background=colors["bg_secondary"],
        foreground=colors["fg"],
        borderwidth=1,
        relief="solid",
        padding=(8, 8),
        font=("Segoe UI", 11, "bold"),
        focuscolor=colors["bg_active"],
    )
    style.map(
        "Secondary.TButton",
        background=[("active", colors["bg_hover"]), ("pressed", colors["bg_active"])],
        foreground=[("disabled", colors["text_muted"])],
    )

    style.configure(
        "Primary.TButton",
        background=colors["accent_green"],
        foreground="#000000",
        borderwidth=0,
        padding=(10, 8),
        font=("Segoe UI", 11, "bold"),
    )
    style.map(
        "Primary.TButton",
        background=[("active", colors["accent_green_hover"]), ("pressed", colors["accent_green_pressed"])],
        foreground=[("disabled", "#444444"), ("pressed", "#000000")],
    )

    style.configure(
        "Danger.TButton",
        background=colors["accent_red"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(10, 8),
        font=("Segoe UI", 11, "bold"),
    )
    style.map(
        "Danger.TButton",
        background=[("active", colors["accent_red_hover"]), ("pressed", colors["accent_red_pressed"])],
        foreground=[("disabled", "#555555"), ("pressed", "#ffffff")],
    )

    style.configure(
        "Bedrot.TCheckbutton",
        background=colors["bg"],
        foreground=colors["fg_secondary"],
        font=("Segoe UI", 10),
    )
    style.map("Bedrot.TCheckbutton", foreground=[("active", colors["fg"])])

    style.configure(
        "Bedrot.Horizontal.TProgressbar",
        troughcolor=colors["bg_secondary"],
        background=colors["accent_cyan"],
        bordercolor=colors["border"],
        lightcolor=colors["accent_cyan"],
        darkcolor=colors["bg_active"],
        thickness=16,
    )

    style.configure(
        "Bedrot.Horizontal.TScale",
        background=colors["bg"],
        troughcolor=colors["bg_secondary"],
        bordercolor=colors["border"],
        sliderlength=18,
        sliderthickness=12,
    )

    style.configure(
        "Bedrot.Vertical.TScrollbar",
        background=colors["bg_secondary"],
        troughcolor=colors["bg"],
        bordercolor=colors["border"],
        arrowcolor=colors["accent_cyan"],
    )
    style.map(
        "Bedrot.Vertical.TScrollbar",
        background=[("active", colors["bg_hover"])],
        arrowcolor=[("active", colors["accent_green"])],
    )

    return colors
