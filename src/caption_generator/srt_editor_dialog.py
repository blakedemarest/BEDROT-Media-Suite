# -*- coding: utf-8 -*-
"""
SRT Editor Dialog for Caption Generator.

Main dialog window containing the Word Editor and Raw SRT views
with synchronized editing and save/cancel functionality.
"""

import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt

from .srt_data_model import SRTDataModel
from .word_editor_view import WordEditorView
from .raw_srt_view import RawSRTView


class SRTEditorDialog(QDialog):
    """
    Modal dialog for editing SRT/VTT files.

    Provides two synchronized views:
    - Word Editor: Color-coded word blocks for visual editing
    - Raw SRT: Plain text editor for direct file editing

    Changes in one view sync to the other when switching.
    """

    VIEW_WORD_EDITOR = 0
    VIEW_RAW_SRT = 1

    def __init__(self, srt_path: str, parent=None):
        """
        Initialize the SRT editor dialog.

        Args:
            srt_path: Path to SRT/VTT file to edit
            parent: Parent widget
        """
        super().__init__(parent)

        self.srt_path = srt_path
        self.filename = os.path.basename(srt_path)
        self.has_unsaved_changes = False
        self.current_view = self.VIEW_WORD_EDITOR

        # Initialize data model
        self.model = SRTDataModel(srt_path)

        self._setup_ui()
        self._apply_theme()
        self._connect_signals()

        # Set initial title
        self._update_title()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(f"Editing: {self.filename}")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header with filename
        header_label = QLabel(f"Editing: {self.filename}")
        header_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #00ffff;
            padding: 8px 0;
        """)
        layout.addWidget(header_label)

        # View toggle buttons
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(8)

        self.word_editor_btn = QPushButton("WORD EDITOR")
        self.word_editor_btn.setCheckable(True)
        self.word_editor_btn.setChecked(True)
        self.word_editor_btn.clicked.connect(lambda: self._switch_view(self.VIEW_WORD_EDITOR))

        self.raw_srt_btn = QPushButton("RAW SRT")
        self.raw_srt_btn.setCheckable(True)
        self.raw_srt_btn.clicked.connect(lambda: self._switch_view(self.VIEW_RAW_SRT))

        toggle_layout.addWidget(self.word_editor_btn)
        toggle_layout.addWidget(self.raw_srt_btn)
        toggle_layout.addStretch()

        layout.addLayout(toggle_layout)

        # Stacked widget for views
        self.stack = QStackedWidget()

        # Create views
        self.word_editor_view = WordEditorView(self.model)
        self.raw_srt_view = RawSRTView(self.model)

        # Initialize raw view with model data
        self.raw_srt_view.refresh_from_model()

        self.stack.addWidget(self.word_editor_view)
        self.stack.addWidget(self.raw_srt_view)

        layout.addWidget(self.stack, 1)  # Stretch factor 1

        # Bottom button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_layout.addStretch()

        self.save_btn = QPushButton("SAVE")
        self.save_btn.setMinimumWidth(120)
        self.save_btn.clicked.connect(self._on_save)

        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.clicked.connect(self._on_cancel)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # Update toggle button styles
        self._update_toggle_styles()

    def _apply_theme(self):
        """Apply BEDROT dark theme to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

        # Save button style
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 136, 0.8);
                color: #000000;
                font-weight: bold;
                font-size: 12px;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 136, 0.9);
            }
            QPushButton:pressed {
                background-color: #00cc66;
            }
        """)

        # Cancel button style
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff0066;
                border: 1px solid #ff0066;
                font-weight: bold;
                font-size: 12px;
                padding: 10px 24px;
                border-radius: 4px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 102, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 0, 102, 0.2);
            }
        """)

    def _update_toggle_styles(self):
        """Update toggle button styles based on current view."""
        # Active button style (primary)
        active_style = """
            QPushButton {
                background-color: rgba(0, 255, 136, 0.8);
                color: #000000;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 136, 0.9);
            }
        """

        # Inactive button style (secondary)
        inactive_style = """
            QPushButton {
                background-color: transparent;
                color: #00ffff;
                border: 1px solid #00ffff;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                border-radius: 4px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.1);
            }
        """

        if self.current_view == self.VIEW_WORD_EDITOR:
            self.word_editor_btn.setStyleSheet(active_style)
            self.word_editor_btn.setChecked(True)
            self.raw_srt_btn.setStyleSheet(inactive_style)
            self.raw_srt_btn.setChecked(False)
        else:
            self.word_editor_btn.setStyleSheet(inactive_style)
            self.word_editor_btn.setChecked(False)
            self.raw_srt_btn.setStyleSheet(active_style)
            self.raw_srt_btn.setChecked(True)

    def _connect_signals(self):
        """Connect view signals."""
        self.word_editor_view.data_changed.connect(self._mark_unsaved)
        self.raw_srt_view.text_changed.connect(self._mark_unsaved)

    def _switch_view(self, view_index: int):
        """
        Switch between Word Editor and Raw SRT views.

        Syncs data between views when switching.

        Args:
            view_index: VIEW_WORD_EDITOR or VIEW_RAW_SRT
        """
        if view_index == self.current_view:
            return

        # Sync data from current view to model
        if self.current_view == self.VIEW_RAW_SRT:
            # Parse raw text and update model
            success, error = self.raw_srt_view.sync_to_model()

            if not success:
                QMessageBox.warning(
                    self, "Parse Error",
                    f"Could not parse SRT content:\n\n{error}\n\n"
                    "Please fix the format before switching views."
                )
                # Reset toggle buttons
                self._update_toggle_styles()
                return

            # Refresh word editor from updated model
            self.word_editor_view.refresh_blocks()

        elif self.current_view == self.VIEW_WORD_EDITOR:
            # Generate raw text from model and update raw view
            self.raw_srt_view.refresh_from_model()

        # Switch view
        self.current_view = view_index
        self.stack.setCurrentIndex(view_index)

        # Update toggle button styles
        self._update_toggle_styles()

    def _mark_unsaved(self):
        """Mark that there are unsaved changes."""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self._update_title()

    def _update_title(self):
        """Update dialog title with unsaved indicator."""
        if self.has_unsaved_changes:
            self.setWindowTitle(f"Editing: {self.filename} *")
        else:
            self.setWindowTitle(f"Editing: {self.filename}")

    def _on_save(self):
        """Save changes to file."""
        # Sync current view to model first
        if self.current_view == self.VIEW_RAW_SRT:
            success, error = self.raw_srt_view.sync_to_model()

            if not success:
                QMessageBox.warning(
                    self, "Parse Error",
                    f"Could not parse SRT content:\n\n{error}\n\n"
                    "Please fix the format before saving."
                )
                return

        # Save model to file
        success, message = self.model.save_to_file()

        if success:
            self.has_unsaved_changes = False
            self._update_title()
            QMessageBox.information(self, "Saved", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Save Error", message)

    def _on_cancel(self):
        """Cancel and close dialog."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to discard them?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

        self.reject()

    def closeEvent(self, event):
        """Handle window close button."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to discard them?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                event.ignore()
                return

        event.accept()
