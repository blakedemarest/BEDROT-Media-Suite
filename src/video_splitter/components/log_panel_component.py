# -*- coding: utf-8 -*-
"""
Log Panel Component for Video Splitter.

A scrollable log output display panel.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk


class LogPanelComponent:
    """Scrollable log output panel with BEDROT styling."""

    def __init__(self, parent, colors: dict):
        """
        Initialize the log panel.

        Args:
            parent: Parent Tkinter widget.
            colors: BEDROT color dictionary.
        """
        self.colors = colors

        # Create the LabelFrame container
        self.frame = ttk.LabelFrame(parent, text="LOG OUTPUT")

        # Configure grid weights for expansion
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # Create the ScrolledText widget
        self._log_widget = scrolledtext.ScrolledText(
            self.frame,
            height=10,
            state=tk.DISABLED,
            font=("Consolas", 10),
            background=colors["bg_secondary"],
            foreground=colors["accent_green"],
            insertbackground=colors["accent_cyan"],
            borderwidth=1,
            relief=tk.FLAT,
        )
        self._log_widget.grid(row=0, column=0, sticky="nsew")

    def log(self, message: str) -> None:
        """
        Append a message to the log.

        Args:
            message: The message to log.
        """
        self._log_widget.config(state=tk.NORMAL)
        self._log_widget.insert(tk.END, message + "\n")
        self._log_widget.see(tk.END)
        self._log_widget.config(state=tk.DISABLED)

    def clear(self) -> None:
        """Clear all log contents."""
        self._log_widget.config(state=tk.NORMAL)
        self._log_widget.delete("1.0", tk.END)
        self._log_widget.config(state=tk.DISABLED)

    def grid(self, **kwargs) -> None:
        """Grid the component's frame."""
        self.frame.grid(**kwargs)

    def pack(self, **kwargs) -> None:
        """Pack the component's frame."""
        self.frame.pack(**kwargs)
