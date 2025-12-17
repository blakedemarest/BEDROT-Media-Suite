# -*- coding: utf-8 -*-
"""
Progress Component for Video Splitter.

Progress bar, status label, and Start/Stop buttons.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ProgressComponent:
    """Progress display with status and action buttons."""

    def __init__(
        self,
        parent,
        colors: dict,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ):
        """
        Initialize the progress component.

        Args:
            parent: Parent Tkinter widget.
            colors: BEDROT color dictionary.
            on_start: Callback when Start button is clicked.
            on_stop: Callback when Stop button is clicked.
        """
        self.colors = colors
        self._on_start = on_start
        self._on_stop = on_stop

        # Tkinter variables
        self._progress_var = tk.DoubleVar(value=0.0)
        self._status_var = tk.StringVar(value="[INFO] Ready")

        # Create the main frame
        self.frame = ttk.Frame(parent)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the progress UI elements."""
        # Progress frame (bar + status)
        progress_frame = ttk.Frame(self.frame)
        progress_frame.grid(row=0, column=0, sticky="ew", padx=10)
        progress_frame.columnconfigure(0, weight=1)

        # Progress bar
        ttk.Progressbar(
            progress_frame,
            variable=self._progress_var,
            maximum=100,
            style="Bedrot.Horizontal.TProgressbar",
        ).grid(row=0, column=0, sticky="ew")

        # Status label
        ttk.Label(
            progress_frame,
            textvariable=self._status_var,
            style="Status.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=4)

        # Actions frame (Start/Stop buttons)
        actions_frame = ttk.Frame(self.frame)
        actions_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        # Start button
        self._start_button = ttk.Button(
            actions_frame,
            text="START SPLITTING",
            command=self._on_start,
            style="Primary.TButton",
        )
        self._start_button.grid(row=0, column=0, sticky="ew", padx=4)

        # Stop button
        self._stop_button = ttk.Button(
            actions_frame,
            text="STOP",
            command=self._on_stop,
            state=tk.DISABLED,
            style="Danger.TButton",
        )
        self._stop_button.grid(row=0, column=1, sticky="ew", padx=4)

    @property
    def progress_var(self) -> tk.DoubleVar:
        """Get the progress variable for external binding."""
        return self._progress_var

    @property
    def status_var(self) -> tk.StringVar:
        """Get the status variable for external binding."""
        return self._status_var

    def set_progress(self, percent: float) -> None:
        """
        Set the progress bar value.

        Args:
            percent: Progress percentage (0-100).
        """
        self._progress_var.set(min(100, max(0, percent)))

    def set_status(self, message: str) -> None:
        """
        Set the status message.

        Args:
            message: Status text to display.
        """
        self._status_var.set(message)

    def set_running_state(self, is_running: bool) -> None:
        """
        Update button states based on running status.

        Args:
            is_running: True if processing is active.
        """
        self._start_button.config(state=tk.DISABLED if is_running else tk.NORMAL)
        self._stop_button.config(state=tk.NORMAL if is_running else tk.DISABLED)

    def grid(self, **kwargs) -> None:
        """Grid the component's frame."""
        self.frame.grid(**kwargs)

    def pack(self, **kwargs) -> None:
        """Pack the component's frame."""
        self.frame.pack(**kwargs)
