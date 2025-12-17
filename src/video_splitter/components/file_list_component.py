# -*- coding: utf-8 -*-
"""
File List Component for Video Splitter.

Listbox with scrollbar, action buttons, and drag-drop support.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional


class FileListComponent:
    """File list panel with drag-drop support and action buttons."""

    def __init__(
        self,
        parent,
        colors: dict,
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove_selected: Callable[[], None],
        on_clear: Callable[[], None],
    ):
        """
        Initialize the file list component.

        Args:
            parent: Parent Tkinter widget.
            colors: BEDROT color dictionary.
            on_add_files: Callback for Add Files button.
            on_add_folder: Callback for Add Folder button.
            on_remove_selected: Callback for Remove Selected button.
            on_clear: Callback for Clear List button.
        """
        self.colors = colors
        self._on_add_files = on_add_files
        self._on_add_folder = on_add_folder
        self._on_remove_selected = on_remove_selected
        self._on_clear = on_clear

        # Internal file list
        self._files: List[str] = []
        self._list_var = tk.StringVar(value=[])

        # Create the LabelFrame container
        self.frame = ttk.LabelFrame(parent, text="SOURCE VIDEOS")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the file list UI elements."""
        colors = self.colors

        # Listbox
        self._listbox = tk.Listbox(
            self.frame,
            listvariable=self._list_var,
            selectmode=tk.EXTENDED,
            height=8,
            activestyle="none",
            font=("Segoe UI", 10),
            highlightthickness=1,
            relief=tk.FLAT,
            borderwidth=1,
        )
        self._listbox.grid(row=0, column=0, sticky="nsew")
        self._listbox.configure(
            bg=colors["bg_secondary"],
            fg=colors["fg"],
            selectbackground=colors["accent_cyan"],
            selectforeground="#000000",
            highlightbackground=colors["border"],
            highlightcolor=colors["accent_cyan"],
        )

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.frame,
            orient="vertical",
            command=self._listbox.yview,
            style="Bedrot.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._listbox.config(yscrollcommand=scrollbar.set)

        # Hint label
        self._hint_label = ttk.Label(
            self.frame,
            text="Drag + drop files or folders here",
            style="Hint.TLabel",
        )
        self._hint_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Buttons frame
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        for idx in range(4):
            buttons_frame.columnconfigure(idx, weight=1)

        # Action buttons
        self._btn_add_files = ttk.Button(
            buttons_frame,
            text="ADD FILES",
            command=self._on_add_files,
            style="Secondary.TButton",
        )
        self._btn_add_files.grid(row=0, column=0, padx=2, sticky="ew")

        self._btn_add_folder = ttk.Button(
            buttons_frame,
            text="ADD FOLDER",
            command=self._on_add_folder,
            style="Secondary.TButton",
        )
        self._btn_add_folder.grid(row=0, column=1, padx=2, sticky="ew")

        self._btn_remove_selected = ttk.Button(
            buttons_frame,
            text="REMOVE SELECTED",
            command=self._on_remove_selected,
            style="Secondary.TButton",
        )
        self._btn_remove_selected.grid(row=0, column=2, padx=2, sticky="ew")

        self._btn_clear_list = ttk.Button(
            buttons_frame,
            text="CLEAR LIST",
            command=self._on_clear,
            style="Secondary.TButton",
        )
        self._btn_clear_list.grid(row=0, column=3, padx=2, sticky="ew")

    @property
    def listbox(self) -> tk.Listbox:
        """Get the internal listbox widget (for drag-drop setup)."""
        return self._listbox

    def get_files(self) -> List[str]:
        """Get a copy of the current file list."""
        return self._files.copy()

    def set_files(self, files: List[str]) -> None:
        """
        Set the file list.

        Args:
            files: List of file paths.
        """
        self._files = list(files)
        self._refresh_display()

    def add_file(self, file_path: str) -> bool:
        """
        Add a single file if not already present.

        Args:
            file_path: Path to add.

        Returns:
            True if file was added, False if already present.
        """
        if file_path not in self._files:
            self._files.append(file_path)
            self._refresh_display()
            return True
        return False

    def add_files(self, file_paths: List[str]) -> int:
        """
        Add multiple files, skipping duplicates.

        Args:
            file_paths: List of paths to add.

        Returns:
            Number of files actually added.
        """
        added = 0
        for path in file_paths:
            if path not in self._files:
                self._files.append(path)
                added += 1
        if added:
            self._refresh_display()
        return added

    def remove_selected(self) -> List[str]:
        """
        Remove selected items from the list.

        Returns:
            List of removed file paths.
        """
        selected = list(self._listbox.curselection())
        if not selected:
            return []

        removed = []
        for index in reversed(selected):
            removed.append(self._files.pop(index))
        self._refresh_display()
        return removed

    def clear(self) -> None:
        """Clear all files from the list."""
        self._files.clear()
        self._refresh_display()

    def get_selection(self) -> List[int]:
        """Get indices of currently selected items."""
        return list(self._listbox.curselection())

    def _refresh_display(self) -> None:
        """Update the listbox display."""
        self._list_var.set(self._files)

    def set_hint_text(self, text: str) -> None:
        """
        Update the hint label text.

        Args:
            text: New hint text.
        """
        self._hint_label.config(text=text)

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the component.

        Args:
            enabled: True to enable, False to disable.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self._listbox.config(state=state)
        self._btn_add_files.config(state=state)
        self._btn_add_folder.config(state=state)
        self._btn_remove_selected.config(state=state)
        self._btn_clear_list.config(state=state)

    def file_count(self) -> int:
        """Get the number of files in the list."""
        return len(self._files)

    def grid(self, **kwargs) -> None:
        """Grid the component's frame."""
        self.frame.grid(**kwargs)

    def pack(self, **kwargs) -> None:
        """Pack the component's frame."""
        self.frame.pack(**kwargs)
