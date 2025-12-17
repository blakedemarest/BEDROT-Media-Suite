# -*- coding: utf-8 -*-
"""
Settings Panel Component for Video Splitter.

Output directory, clip length, jitter, and checkbox settings.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..models import SplitterSettings


class SettingsPanelComponent:
    """Settings panel for clip configuration."""

    def __init__(
        self,
        parent,
        colors: dict,
        initial_settings: SplitterSettings,
        on_browse_output: Callable[[], None],
        on_setting_changed: Optional[Callable[[str, any], None]] = None,
    ):
        """
        Initialize the settings panel.

        Args:
            parent: Parent Tkinter widget.
            colors: BEDROT color dictionary.
            initial_settings: Initial settings values.
            on_browse_output: Callback for Browse button.
            on_setting_changed: Optional callback when any setting changes.
                                Called with (setting_name, new_value).
        """
        self.colors = colors
        self._on_browse_output = on_browse_output
        self._on_setting_changed = on_setting_changed

        # Tkinter variables
        self._output_dir_var = tk.StringVar(value=initial_settings.output_dir)
        self._clip_length_var = tk.DoubleVar(value=initial_settings.clip_length_seconds)
        self._jitter_var = tk.IntVar(value=int(initial_settings.jitter_percent))
        self._min_clip_var = tk.DoubleVar(value=initial_settings.min_clip_length)
        self._per_clip_var = tk.BooleanVar(value=initial_settings.per_clip_jitter)
        self._reset_ts_var = tk.BooleanVar(value=initial_settings.reset_timestamps)
        self._overwrite_var = tk.BooleanVar(value=initial_settings.overwrite_existing)

        # Create the LabelFrame container
        self.frame = ttk.LabelFrame(parent, text="OUTPUT & CLIP SETTINGS")
        self.frame.columnconfigure(1, weight=1)

        self._build_ui()
        self._bind_traces()

    def _build_ui(self) -> None:
        """Build the settings UI elements."""
        # Output folder row
        ttk.Label(self.frame, text="Output Folder").grid(
            row=0, column=0, sticky="w", pady=2, padx=2
        )
        output_entry = ttk.Entry(self.frame, textvariable=self._output_dir_var)
        output_entry.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(
            self.frame,
            text="BROWSE",
            command=self._on_browse_output,
            style="Secondary.TButton",
        ).grid(row=0, column=2, padx=2, pady=2)

        # Controls frame (spinners and slider)
        controls_frame = ttk.Frame(self.frame)
        controls_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        for idx in range(4):
            controls_frame.columnconfigure(idx, weight=1)

        # Clip Length
        ttk.Label(controls_frame, text="Clip Length (s)").grid(row=0, column=0, sticky="w")
        clip_entry = ttk.Spinbox(
            controls_frame,
            from_=1.0,
            to=600.0,
            increment=0.5,
            textvariable=self._clip_length_var,
            width=10,
        )
        clip_entry.grid(row=1, column=0, sticky="ew", padx=2)

        # Min Clip
        ttk.Label(controls_frame, text="Min Clip (s)").grid(row=0, column=1, sticky="w")
        min_entry = ttk.Spinbox(
            controls_frame,
            from_=0.5,
            to=120.0,
            increment=0.5,
            textvariable=self._min_clip_var,
            width=10,
        )
        min_entry.grid(row=1, column=1, sticky="ew", padx=2)

        # Jitter slider
        ttk.Label(controls_frame, text="Jitter (%)").grid(row=0, column=2, sticky="w")
        jitter_slider = ttk.Scale(
            controls_frame,
            from_=0,
            to=50,
            variable=self._jitter_var,
            command=lambda _evt=None: self._update_jitter_label(),
            style="Bedrot.Horizontal.TScale",
        )
        jitter_slider.grid(row=1, column=2, sticky="ew", padx=2)
        self._jitter_label = ttk.Label(controls_frame, text="", style="Accent.TLabel")
        self._jitter_label.grid(row=2, column=2, sticky="w")
        self._update_jitter_label()

        # Checkbox frame
        checkbox_frame = ttk.Frame(self.frame)
        checkbox_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        ttk.Checkbutton(
            checkbox_frame,
            text="Randomize each clip",
            variable=self._per_clip_var,
            style="Bedrot.TCheckbutton",
        ).grid(row=0, column=0, sticky="w")

        ttk.Checkbutton(
            checkbox_frame,
            text="Reset timestamps",
            variable=self._reset_ts_var,
            style="Bedrot.TCheckbutton",
        ).grid(row=0, column=1, sticky="w", padx=10)

        ttk.Checkbutton(
            checkbox_frame,
            text="Overwrite existing files",
            variable=self._overwrite_var,
            style="Bedrot.TCheckbutton",
        ).grid(row=0, column=2, sticky="w")

    def _bind_traces(self) -> None:
        """Bind variable traces for change notifications."""
        if not self._on_setting_changed:
            return

        self._output_dir_var.trace_add(
            "write", lambda *_: self._notify_change("output_dir", self._output_dir_var.get())
        )
        self._clip_length_var.trace_add(
            "write", lambda *_: self._notify_change("clip_length_seconds", float(self._clip_length_var.get()))
        )
        self._min_clip_var.trace_add(
            "write", lambda *_: self._notify_change("min_clip_length", float(self._min_clip_var.get()))
        )
        self._jitter_var.trace_add(
            "write", lambda *_: self._notify_change("jitter_percent", float(self._jitter_var.get()))
        )
        self._per_clip_var.trace_add(
            "write", lambda *_: self._notify_change("per_clip_jitter", bool(self._per_clip_var.get()))
        )
        self._reset_ts_var.trace_add(
            "write", lambda *_: self._notify_change("reset_timestamps", bool(self._reset_ts_var.get()))
        )
        self._overwrite_var.trace_add(
            "write", lambda *_: self._notify_change("overwrite_existing", bool(self._overwrite_var.get()))
        )

    def _notify_change(self, setting_name: str, value: any) -> None:
        """Notify of a setting change."""
        if self._on_setting_changed:
            self._on_setting_changed(setting_name, value)

    def _update_jitter_label(self) -> None:
        """Update the jitter percentage label."""
        value = float(self._jitter_var.get())
        self._jitter_label.config(text=f"+/- {value:.0f}%")

    # Property accessors for variables (for external binding if needed)
    @property
    def output_dir_var(self) -> tk.StringVar:
        return self._output_dir_var

    @property
    def clip_length_var(self) -> tk.DoubleVar:
        return self._clip_length_var

    @property
    def jitter_var(self) -> tk.IntVar:
        return self._jitter_var

    @property
    def min_clip_var(self) -> tk.DoubleVar:
        return self._min_clip_var

    @property
    def per_clip_var(self) -> tk.BooleanVar:
        return self._per_clip_var

    @property
    def reset_ts_var(self) -> tk.BooleanVar:
        return self._reset_ts_var

    @property
    def overwrite_var(self) -> tk.BooleanVar:
        return self._overwrite_var

    def get_settings(self) -> SplitterSettings:
        """
        Get current settings as a dataclass.

        Returns:
            SplitterSettings with current values.
        """
        return SplitterSettings(
            output_dir=self._output_dir_var.get(),
            clip_length_seconds=float(self._clip_length_var.get()),
            jitter_percent=float(self._jitter_var.get()),
            min_clip_length=float(self._min_clip_var.get()),
            per_clip_jitter=bool(self._per_clip_var.get()),
            reset_timestamps=bool(self._reset_ts_var.get()),
            overwrite_existing=bool(self._overwrite_var.get()),
        )

    def set_output_dir(self, path: str) -> None:
        """
        Set the output directory.

        Args:
            path: Directory path.
        """
        self._output_dir_var.set(path)

    def grid(self, **kwargs) -> None:
        """Grid the component's frame."""
        self.frame.grid(**kwargs)

    def pack(self, **kwargs) -> None:
        """Pack the component's frame."""
        self.frame.pack(**kwargs)
