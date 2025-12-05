# -*- coding: utf-8 -*-
"""
Main Application Module for Caption Generator.

A PyQt5 application for creating caption/lyric videos from SRT/VTT files.
"""

import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QGroupBox,
    QTextEdit, QFileDialog, QRadioButton, QButtonGroup, QColorDialog,
    QMessageBox, QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from .config_manager import get_config
from .video_generator import generate_caption_video, get_audio_duration


class GeneratorWorker(QThread):
    """Background worker thread for video generation."""

    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, srt_path, audio_path, output_path, settings, transparent=False):
        super().__init__()
        self.srt_path = srt_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.settings = settings
        self.transparent = transparent

    def run(self):
        """Run the video generation."""
        format_type = "WebM (transparent)" if self.transparent else "MP4"
        self.log_signal.emit(f"[Caption Generator] Starting {format_type} video generation...")

        success, message = generate_caption_video(
            self.srt_path,
            self.audio_path,
            self.output_path,
            self.settings,
            progress_callback=lambda msg: self.log_signal.emit(msg),
            transparent=self.transparent
        )

        self.finished_signal.emit(success, message)


class CaptionGeneratorApp(QMainWindow):
    """Main Caption Generator application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BEDROT Caption Generator")
        self.setMinimumSize(700, 650)
        self.config = get_config()

        self._setup_ui()
        self._apply_theme()
        self._load_settings()

        self.worker = None

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Title
        title_label = QLabel("CAPTION GENERATOR")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ffff; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Input Files Section
        input_group = QGroupBox("Input Files")
        input_layout = QVBoxLayout()

        # Subtitle file
        srt_layout = QHBoxLayout()
        srt_label = QLabel("Subtitle File:")
        srt_label.setFixedWidth(100)
        self.srt_input = QLineEdit()
        self.srt_input.setPlaceholderText("Select SRT or VTT file...")
        srt_browse = QPushButton("Browse")
        srt_browse.clicked.connect(self._browse_srt)
        srt_layout.addWidget(srt_label)
        srt_layout.addWidget(self.srt_input)
        srt_layout.addWidget(srt_browse)
        input_layout.addLayout(srt_layout)

        # Audio file
        audio_layout = QHBoxLayout()
        audio_label = QLabel("Audio File:")
        audio_label.setFixedWidth(100)
        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText("Select WAV, MP3, or FLAC file...")
        audio_browse = QPushButton("Browse")
        audio_browse.clicked.connect(self._browse_audio)
        audio_layout.addWidget(audio_label)
        audio_layout.addWidget(self.audio_input)
        audio_layout.addWidget(audio_browse)
        input_layout.addLayout(audio_layout)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Style Settings Section
        style_group = QGroupBox("Style Settings")
        style_layout = QVBoxLayout()

        # Font row
        font_row = QHBoxLayout()
        font_label = QLabel("Font:")
        font_label.setFixedWidth(100)
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Arial Narrow", "Arial", "Helvetica", "Impact",
            "Verdana", "Tahoma", "Segoe UI", "Consolas"
        ])
        size_label = QLabel("Size:")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(12, 120)
        self.size_spin.setValue(56)
        font_row.addWidget(font_label)
        font_row.addWidget(self.font_combo)
        font_row.addWidget(size_label)
        font_row.addWidget(self.size_spin)
        font_row.addStretch()
        style_layout.addLayout(font_row)

        # Color row
        color_row = QHBoxLayout()
        text_color_label = QLabel("Text Color:")
        text_color_label.setFixedWidth(100)
        self.text_color_input = QLineEdit("#ffffff")
        self.text_color_input.setFixedWidth(80)
        text_color_btn = QPushButton("Pick")
        text_color_btn.clicked.connect(lambda: self._pick_color(self.text_color_input))
        bg_color_label = QLabel("Background:")
        self.bg_color_input = QLineEdit("#000000")
        self.bg_color_input.setFixedWidth(80)
        bg_color_btn = QPushButton("Pick")
        bg_color_btn.clicked.connect(lambda: self._pick_color(self.bg_color_input))
        color_row.addWidget(text_color_label)
        color_row.addWidget(self.text_color_input)
        color_row.addWidget(text_color_btn)
        color_row.addSpacing(20)
        color_row.addWidget(bg_color_label)
        color_row.addWidget(self.bg_color_input)
        color_row.addWidget(bg_color_btn)
        color_row.addStretch()
        style_layout.addLayout(color_row)

        # Store references for toggling
        self.bg_color_label = bg_color_label
        self.bg_color_btn = bg_color_btn

        # Transparent background row
        transparent_row = QHBoxLayout()
        transparent_label = QLabel("")
        transparent_label.setFixedWidth(100)
        self.transparent_checkbox = QCheckBox("Transparent Background (WebM)")
        self.transparent_checkbox.stateChanged.connect(self._on_transparent_changed)
        transparent_row.addWidget(transparent_label)
        transparent_row.addWidget(self.transparent_checkbox)
        transparent_row.addStretch()
        style_layout.addLayout(transparent_row)

        # Alignment row
        align_row = QHBoxLayout()
        align_label = QLabel("Alignment:")
        align_label.setFixedWidth(100)
        self.align_group = QButtonGroup()
        self.align_top = QRadioButton("Top")
        self.align_center = QRadioButton("Center")
        self.align_bottom = QRadioButton("Bottom")
        self.align_center.setChecked(True)
        self.align_group.addButton(self.align_top, 0)
        self.align_group.addButton(self.align_center, 1)
        self.align_group.addButton(self.align_bottom, 2)
        align_row.addWidget(align_label)
        align_row.addWidget(self.align_top)
        align_row.addWidget(self.align_center)
        align_row.addWidget(self.align_bottom)
        align_row.addStretch()
        style_layout.addLayout(align_row)

        style_group.setLayout(style_layout)
        main_layout.addWidget(style_group)

        # Video Settings Section
        video_group = QGroupBox("Video Settings")
        video_layout = QHBoxLayout()

        res_label = QLabel("Resolution:")
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080", "1280x720", "3840x2160", "1080x1920"])
        fps_label = QLabel("FPS:")
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(24, 60)
        self.fps_spin.setValue(30)

        video_layout.addWidget(res_label)
        video_layout.addWidget(self.res_combo)
        video_layout.addSpacing(20)
        video_layout.addWidget(fps_label)
        video_layout.addWidget(self.fps_spin)
        video_layout.addStretch()

        video_group.setLayout(video_layout)
        main_layout.addWidget(video_group)

        # Output Section
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()

        # Output folder
        folder_row = QHBoxLayout()
        folder_label = QLabel("Folder:")
        folder_label.setFixedWidth(100)
        self.output_folder = QLineEdit()
        self.output_folder.setText(self.config.get_output_folder())
        folder_browse = QPushButton("Browse")
        folder_browse.clicked.connect(self._browse_output)
        folder_open = QPushButton("Open")
        folder_open.clicked.connect(self._open_output_folder)
        folder_row.addWidget(folder_label)
        folder_row.addWidget(self.output_folder)
        folder_row.addWidget(folder_browse)
        folder_row.addWidget(folder_open)
        output_layout.addLayout(folder_row)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # Generate Button
        self.generate_btn = QPushButton("GENERATE VIDEO")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ff88;
                color: #000000;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00cc6a;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.generate_btn.clicked.connect(self._generate_video)
        main_layout.addWidget(self.generate_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log Output
        log_label = QLabel("Log Output:")
        main_layout.addWidget(log_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(150)
        main_layout.addWidget(self.log_box)

        self._log("[Caption Generator] Ready. Select subtitle and audio files to begin.")

    def _apply_theme(self):
        """Apply BEDROT dark theme."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #404040;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #00ffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 6px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 1px solid #00ffff;
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
            QComboBox {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 6px;
                color: #e0e0e0;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #e0e0e0;
                selection-background-color: #00ffff;
                selection-color: #000000;
            }
            QSpinBox {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 6px;
                color: #e0e0e0;
            }
            QRadioButton {
                color: #e0e0e0;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #404040;
                border-radius: 7px;
                background-color: #1a1a1a;
            }
            QRadioButton::indicator:checked {
                background-color: #00ff88;
                border: 1px solid #00ff88;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #404040;
                border-radius: 3px;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                background-color: #00ff88;
                border: 1px solid #00ff88;
            }
            QCheckBox:disabled {
                color: #606060;
            }
            QTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #404040;
                border-radius: 3px;
                color: #00ff88;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00ff88;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def _load_settings(self):
        """Load saved settings into UI."""
        self.font_combo.setCurrentText(self.config.get("font_name", "Arial Narrow"))
        self.size_spin.setValue(self.config.get("font_size", 56))
        self.text_color_input.setText(self.config.get("font_color", "#ffffff"))
        self.bg_color_input.setText(self.config.get("background_color", "#000000"))
        self.res_combo.setCurrentText(self.config.get("resolution", "1920x1080"))
        self.fps_spin.setValue(self.config.get("fps", 30))

        # Load transparent background setting
        is_transparent = self.config.get("transparent_background", False)
        self.transparent_checkbox.setChecked(is_transparent)
        self._on_transparent_changed(Qt.Checked if is_transparent else Qt.Unchecked)

        alignment = self.config.get("alignment", "center")
        if alignment == "top":
            self.align_top.setChecked(True)
        elif alignment == "bottom":
            self.align_bottom.setChecked(True)
        else:
            self.align_center.setChecked(True)

    def _save_settings(self):
        """Save current UI settings to config."""
        alignment = "center"
        if self.align_top.isChecked():
            alignment = "top"
        elif self.align_bottom.isChecked():
            alignment = "bottom"

        self.config.set("font_name", self.font_combo.currentText(), autosave=False)
        self.config.set("font_size", self.size_spin.value(), autosave=False)
        self.config.set("font_color", self.text_color_input.text(), autosave=False)
        self.config.set("background_color", self.bg_color_input.text(), autosave=False)
        self.config.set("transparent_background", self.transparent_checkbox.isChecked(), autosave=False)
        self.config.set("resolution", self.res_combo.currentText(), autosave=False)
        self.config.set("fps", self.fps_spin.value(), autosave=False)
        self.config.set("alignment", alignment, autosave=False)
        self.config.set("output_folder", self.output_folder.text(), autosave=False)
        self.config.save_config()

    def _log(self, message):
        """Add message to log box."""
        self.log_box.append(message)

    def _browse_srt(self):
        """Browse for subtitle file."""
        last_folder = self.config.get("last_srt_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", last_folder,
            "Subtitle Files (*.srt *.vtt);;All Files (*.*)"
        )
        if file_path:
            self.srt_input.setText(file_path)
            self.config.set("last_srt_folder", os.path.dirname(file_path))
            self._log(f"[Caption Generator] Subtitle file selected: {os.path.basename(file_path)}")

    def _browse_audio(self):
        """Browse for audio file."""
        last_folder = self.config.get("last_audio_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", last_folder,
            "Audio Files (*.wav *.mp3 *.flac *.m4a *.aac);;All Files (*.*)"
        )
        if file_path:
            self.audio_input.setText(file_path)
            self.config.set("last_audio_folder", os.path.dirname(file_path))

            # Get duration
            duration = get_audio_duration(file_path)
            if duration:
                mins = int(duration // 60)
                secs = int(duration % 60)
                self._log(f"[Caption Generator] Audio file selected: {os.path.basename(file_path)} ({mins}:{secs:02d})")
            else:
                self._log(f"[Caption Generator] Audio file selected: {os.path.basename(file_path)}")

    def _browse_output(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.output_folder.text()
        )
        if folder:
            self.output_folder.setText(folder)
            self._log(f"[Caption Generator] Output folder set: {folder}")

    def _open_output_folder(self):
        """Open output folder in file explorer."""
        folder = self.output_folder.text()
        if folder and os.path.exists(folder):
            os.startfile(folder)
        else:
            self._log("[Caption Generator] Output folder does not exist")

    def _pick_color(self, line_edit):
        """Open color picker dialog."""
        current = QColor(line_edit.text())
        color = QColorDialog.getColor(current, self, "Select Color")
        if color.isValid():
            line_edit.setText(color.name())

    def _on_transparent_changed(self, state):
        """Toggle background color widgets when transparent checkbox changes."""
        is_transparent = state == Qt.Checked
        self.bg_color_label.setEnabled(not is_transparent)
        self.bg_color_input.setEnabled(not is_transparent)
        self.bg_color_btn.setEnabled(not is_transparent)

    def _get_settings(self):
        """Get current settings as dictionary."""
        alignment = "center"
        if self.align_top.isChecked():
            alignment = "top"
        elif self.align_bottom.isChecked():
            alignment = "bottom"

        return {
            "font_name": self.font_combo.currentText(),
            "font_size": self.size_spin.value(),
            "font_color": self.text_color_input.text(),
            "background_color": self.bg_color_input.text(),
            "resolution": self.res_combo.currentText(),
            "fps": self.fps_spin.value(),
            "alignment": alignment,
            "outline_size": 2
        }

    def _generate_video(self):
        """Start video generation."""
        srt_path = self.srt_input.text().strip()
        audio_path = self.audio_input.text().strip()
        output_folder = self.output_folder.text().strip()

        # Validate inputs
        if not srt_path:
            QMessageBox.warning(self, "Missing Input", "Please select a subtitle file.")
            return

        if not audio_path:
            QMessageBox.warning(self, "Missing Input", "Please select an audio file.")
            return

        if not os.path.exists(srt_path):
            QMessageBox.warning(self, "File Not Found", f"Subtitle file not found:\n{srt_path}")
            return

        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "File Not Found", f"Audio file not found:\n{audio_path}")
            return

        # Check if transparent mode is enabled
        is_transparent = self.transparent_checkbox.isChecked()

        # Generate output filename with appropriate extension
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        extension = ".webm" if is_transparent else ".mp4"
        output_path = os.path.join(output_folder, f"{base_name}_captions{extension}")

        # Save settings
        self._save_settings()

        # Disable generate button
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("GENERATING...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Start worker thread
        settings = self._get_settings()
        self.worker = GeneratorWorker(srt_path, audio_path, output_path, settings, is_transparent)
        self.worker.log_signal.connect(self._log)
        self.worker.finished_signal.connect(self._on_generation_finished)
        self.worker.start()

    def _on_generation_finished(self, success, message):
        """Handle generation completion."""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("GENERATE VIDEO")
        self.progress_bar.setVisible(False)

        if success:
            self._log(f"[Caption Generator] [OK] {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self._log(f"[Caption Generator] [ERROR] {message}")
            QMessageBox.critical(self, "Error", message)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("BEDROT Caption Generator")
    app.setOrganizationName("BEDROT Productions")

    window = CaptionGeneratorApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
