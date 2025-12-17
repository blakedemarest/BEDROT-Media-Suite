# -*- coding: utf-8 -*-
"""
Settings Dialog for Caption Generator.

Provides configuration options for the Caption Generator application.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDialogButtonBox, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):
    """Settings dialog for Caption Generator configuration."""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Caption Generator Settings")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header = QLabel("SETTINGS")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffff;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Video Generation Settings Group
        video_group = QGroupBox("Video Generation")
        video_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00ffff;
                border: 1px solid #404040;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        video_layout = QVBoxLayout(video_group)

        # Safe Area Mode checkbox
        safe_area_row = QHBoxLayout()
        self.safe_area_checkbox = QCheckBox("Safe Area Mode")
        self.safe_area_checkbox.setToolTip(
            "Adds margins and auto-scales font for portrait videos\n"
            "to prevent text from overflowing the visible frame."
        )
        self.safe_area_checkbox.setChecked(self.config.get("safe_area_mode", True))
        safe_area_row.addWidget(self.safe_area_checkbox)
        safe_area_row.addStretch()
        video_layout.addLayout(safe_area_row)

        # Description label
        desc = QLabel(
            "When enabled, applies safe margins and reduces font size\n"
            "for portrait videos to keep text within visible bounds."
        )
        desc.setStyleSheet("color: #808080; font-size: 11px;")
        video_layout.addWidget(desc)

        layout.addWidget(video_group)
        layout.addStretch()

        # Dialog buttons (Save + Close)
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Close
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _save_and_close(self):
        """Save settings and close dialog."""
        self.config.set("safe_area_mode", self.safe_area_checkbox.isChecked())
        self.accept()

    def _apply_theme(self):
        """Apply BEDROT dark theme."""
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #00ffff;
                border-radius: 3px;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                background-color: #00ffff;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #00ffff;
                border-radius: 3px;
                padding: 6px 12px;
                color: #00ffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #252525;
            }
        """)
