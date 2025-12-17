# -*- coding: utf-8 -*-
"""
Drag and Drop Handler for Video Snippet Remixer.

Extracted from main_app.py to decouple drag-drop logic from application logic.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable, List, Optional, Set

# Import drag and drop support
try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    DND_AVAILABLE = False


if TYPE_CHECKING:
    import tkinter as tk


# Supported media extensions
VIDEO_EXTENSIONS: Set[str] = {
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.mpg', '.mpeg'
}
IMAGE_EXTENSIONS: Set[str] = {
    '.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'
}
MEDIA_EXTENSIONS: Set[str] = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


class DragDropHandler:
    """
    Handles drag and drop functionality for the video remixer.

    This class encapsulates all drag-drop related logic including:
    - Setting up drop targets
    - Visual feedback during drag operations
    - File validation and filtering
    - Placeholder hint management
    """

    def __init__(
        self,
        listbox: "tk.Listbox",
        root: "tk.Tk",
        on_files_added: Callable[[List[str]], None],
        on_browse_files: Callable[[], None],
        on_status_success: Callable[[str], None],
        on_status_warning: Callable[[str], None],
        on_status_error: Callable[[str], None],
    ):
        """
        Initialize the drag-drop handler.

        Args:
            listbox: The Tkinter Listbox widget to enable drag-drop on.
            root: The Tkinter root window.
            on_files_added: Callback when valid files are dropped.
            on_browse_files: Callback to open file browser.
            on_status_success: Callback for success status messages.
            on_status_warning: Callback for warning status messages.
            on_status_error: Callback for error status messages.
        """
        self.listbox = listbox
        self.root = root
        self.on_files_added = on_files_added
        self.on_browse_files = on_browse_files
        self.on_status_success = on_status_success
        self.on_status_warning = on_status_warning
        self.on_status_error = on_status_error

        self.original_listbox_bg: Optional[str] = None
        self._has_placeholder: bool = False
        self.dnd_available: bool = DND_AVAILABLE and hasattr(root, 'drop_target_register')

    def setup(self) -> bool:
        """
        Set up drag and drop functionality for the listbox.

        Returns:
            True if setup was successful, False otherwise.
        """
        if not self.dnd_available:
            return False

        try:
            # Register the listbox as a drop target for files
            self.listbox.drop_target_register(DND_FILES)

            # Bind the drop event
            self.listbox.dnd_bind('<<Drop>>', self._on_file_drop)

            # Visual feedback during drag operations
            self.listbox.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.listbox.dnd_bind('<<DragLeave>>', self._on_drag_leave)

            # Store original background color
            self.original_listbox_bg = self.listbox.cget('bg')

            # Add a subtle hint that drag and drop is supported
            self.add_hint()

            return True

        except Exception as e:
            print(f"[WARNING] Failed to setup drag and drop: {e}")
            return False

    def add_hint(self) -> None:
        """Add a visual hint that the listbox supports drag and drop."""
        if self.listbox.size() == 0:
            # Add a placeholder message when the listbox is empty
            self.listbox.insert(0, "Drag and drop video files here or use Browse Files...")
            self.listbox.configure(fg='#888888')  # Muted grey for placeholder
            self.listbox.bind('<Button-1>', self._on_listbox_click)
            self._has_placeholder = True
        else:
            self._has_placeholder = False

    def remove_hint(self) -> None:
        """Remove the drag and drop hint if present."""
        if self._has_placeholder:
            if self.listbox.size() > 0:
                first_item = self.listbox.get(0)
                if "Drag and drop" in first_item:
                    self.listbox.delete(0)
                    self.listbox.configure(fg='#e0e0e0')  # Normal text color
                    self._has_placeholder = False

    def _on_listbox_click(self, event) -> None:
        """Handle clicks on the listbox to remove placeholder and browse files."""
        if self._has_placeholder:
            self.remove_hint()
            # Automatically open file browser when clicking on empty listbox
            self.on_browse_files()

    def _on_file_drop(self, event) -> None:
        """Handle file drop events on the listbox."""
        try:
            # Get the list of dropped files
            files = self.root.tk.splitlist(event.data)

            # Filter for valid media files
            valid_files = self._filter_media_files(files)

            if valid_files:
                # Remove placeholder hint if present
                self.remove_hint()

                # Add the valid files via callback
                self.on_files_added(valid_files)

                # Show success message
                count = len(valid_files)
                self.on_status_success(f"Added {count} media file{'s' if count > 1 else ''} via drag and drop")
            else:
                self.on_status_warning("No valid media files found in dropped items")

        except Exception as e:
            print(f"[ERROR] Error processing dropped files: {e}")
            self.on_status_error(f"Error processing dropped files: {str(e)}")

    def _filter_media_files(self, files: List[str]) -> List[str]:
        """
        Filter a list of paths to include only valid media files.

        Args:
            files: List of file paths (may include directories).

        Returns:
            List of valid media file paths.
        """
        valid_files = []

        for file_path in files:
            # Clean up the file path (remove extra quotes/spaces)
            file_path = file_path.strip().strip('"').strip("'")

            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file_path.lower())
                if ext in MEDIA_EXTENSIONS:
                    valid_files.append(file_path)
                else:
                    print(f"[WARNING] Skipping unsupported file: {os.path.basename(file_path)}")
            elif os.path.isdir(file_path):
                # If a directory is dropped, scan for media files
                for root_dir, dirs, filenames in os.walk(file_path):
                    for filename in filenames:
                        _, ext = os.path.splitext(filename.lower())
                        if ext in MEDIA_EXTENSIONS:
                            valid_files.append(os.path.join(root_dir, filename))

        return valid_files

    def _on_drag_enter(self, event) -> None:
        """Visual feedback when files are dragged over the listbox."""
        if self.original_listbox_bg is not None:
            self.listbox.configure(bg='#252525')  # Slightly lighter dark for hover

    def _on_drag_leave(self, event) -> None:
        """Reset visual feedback when drag leaves the listbox."""
        if self.original_listbox_bg is not None:
            self.listbox.configure(bg='#1a1a1a')  # Back to normal dark
