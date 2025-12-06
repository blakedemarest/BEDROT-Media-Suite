# -*- coding: utf-8 -*-
"""
Raw SRT View for Caption Generator SRT Editor.

Provides a plain text editor for direct SRT/VTT file editing.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPlainTextEdit
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

from .srt_data_model import SRTDataModel


class RawSRTView(QWidget):
    """
    Plain text editor widget for raw SRT/VTT content.

    Displays the full SRT file contents in a monospace editor,
    allowing direct editing of text and timestamps.
    """

    # Emitted when text is edited by user
    text_changed = pyqtSignal()

    def __init__(self, model: SRTDataModel, parent=None):
        """
        Initialize the raw SRT view.

        Args:
            model: SRTDataModel instance to sync with
            parent: Parent widget
        """
        super().__init__(parent)
        self.model = model
        self._block_signals = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Info label
        info_label = QLabel("Edit raw SRT/VTT content below. Changes sync when switching views.")
        info_label.setStyleSheet("""
            color: #00ffff;
            font-size: 11px;
            padding: 4px;
            background-color: transparent;
        """)
        layout.addWidget(info_label)

        # Text editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0a0a0a;
                color: #00ff88;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: rgba(0, 255, 255, 0.3);
                selection-color: #ffffff;
            }
        """)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setTabStopDistance(40)  # 4 spaces worth

        # Connect text changed signal
        self.editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.editor)

    def _on_text_changed(self):
        """Handle text changes in the editor."""
        if not self._block_signals:
            self.text_changed.emit()

    def refresh_from_model(self):
        """Load content from the data model into the editor."""
        self._block_signals = True
        try:
            raw_text = self.model.to_raw_text()
            self.editor.setPlainText(raw_text)
        finally:
            self._block_signals = False

    def sync_to_model(self) -> tuple:
        """
        Parse editor content and update the data model.

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        raw_text = self.editor.toPlainText()
        return self.model.update_from_raw_text(raw_text)

    def get_text(self) -> str:
        """Get the current editor text content."""
        return self.editor.toPlainText()

    def set_text(self, text: str):
        """Set the editor text content without triggering signals."""
        self._block_signals = True
        try:
            self.editor.setPlainText(text)
        finally:
            self._block_signals = False

    def is_empty(self) -> bool:
        """Check if the editor is empty."""
        return len(self.editor.toPlainText().strip()) == 0
