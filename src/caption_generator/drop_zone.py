# -*- coding: utf-8 -*-
"""
Drop Zone Widget for Caption Generator.

A dedicated drag-and-drop area for audio files with visual feedback.
"""

import os
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


# Supported file extensions
SUPPORTED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.aac'}
SUPPORTED_SUBTITLE_EXTENSIONS = {'.srt', '.vtt'}
SUPPORTED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_SUBTITLE_EXTENSIONS


class DropZoneWidget(QFrame):
    """
    Visual drop zone for audio files with hover feedback.

    Signals:
        files_dropped(list): Emitted when valid audio files are dropped,
                            contains list of file paths
    """

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None, accept_subtitles=False):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self._drag_active = False
        self._accept_subtitles = accept_subtitles

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Main label
        self.label = QLabel("Drop audio files here")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        # Subtitle label
        self.subtitle = QLabel("Supports WAV, MP3, FLAC, M4A, AAC")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("""
            QLabel {
                color: #606060;
                font-size: 11px;
            }
        """)

        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.subtitle)
        layout.addStretch()

        self.setMinimumHeight(100)

    def _apply_style(self):
        """Apply BEDROT dark theme styling."""
        self._update_style()

    def _update_style(self):
        """Update style based on drag state."""
        if self._drag_active:
            self.setStyleSheet("""
                QFrame#DropZone {
                    background-color: rgba(0, 255, 136, 0.1);
                    border: 2px solid #00ff88;
                    border-radius: 8px;
                }
            """)
            self.label.setStyleSheet("""
                QLabel {
                    color: #00ff88;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#DropZone {
                    background-color: #1a1a1a;
                    border: 2px dashed #404040;
                    border-radius: 8px;
                }
                QFrame#DropZone:hover {
                    border-color: #00ffff;
                    background-color: #1f1f1f;
                }
            """)
            self.label.setStyleSheet("""
                QLabel {
                    color: #808080;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

    def _validate_files(self, urls) -> list:
        """
        Filter URLs to only include supported files.

        Args:
            urls: List of QUrl objects from drop event

        Returns:
            List of valid file paths
        """
        valid_files = []

        # Determine which extensions to accept
        if self._accept_subtitles:
            accepted_extensions = SUPPORTED_EXTENSIONS
        else:
            accepted_extensions = SUPPORTED_AUDIO_EXTENSIONS

        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in accepted_extensions:
                        valid_files.append(file_path)

        return valid_files

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any files are valid
            valid_files = self._validate_files(event.mimeData().urls())
            if valid_files:
                event.acceptProposedAction()
                self._drag_active = True
                self._update_style()
                self.label.setText(f"Drop {len(valid_files)} file(s)")
                return

        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self._drag_active = False
        self._update_style()
        self.label.setText("Drop audio files here")

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        self._drag_active = False
        self._update_style()
        # Reset label text based on mode
        if self._accept_subtitles:
            self.label.setText("Drop audio or SRT files here")
        else:
            self.label.setText("Drop audio files here")

        if event.mimeData().hasUrls():
            valid_files = self._validate_files(event.mimeData().urls())
            if valid_files:
                event.acceptProposedAction()
                self.files_dropped.emit(valid_files)
                return

        event.ignore()

    def set_enabled_state(self, enabled: bool):
        """
        Enable or disable the drop zone.

        Args:
            enabled: Whether the drop zone should accept drops
        """
        self.setAcceptDrops(enabled)
        if enabled:
            self.label.setText("Drop audio files here")
            self.label.setStyleSheet("""
                QLabel {
                    color: #808080;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        else:
            self.label.setText("Processing... Please wait")
            self.label.setStyleSheet("""
                QLabel {
                    color: #606060;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
