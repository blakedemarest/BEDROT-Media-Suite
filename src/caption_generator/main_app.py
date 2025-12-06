# -*- coding: utf-8 -*-
"""
Main Application Module for Caption Generator.

A PyQt5 application for creating caption/lyric videos from SRT files.
Supports drag-and-drop, bulk processing, and auto-transcription.
"""

import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QGroupBox,
    QTextEdit, QFileDialog, QRadioButton, QButtonGroup, QColorDialog,
    QMessageBox, QProgressBar, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from .config_manager import get_config
from .video_generator import generate_caption_video, get_audio_duration
from .drop_zone import DropZoneWidget
from .pairing_history import PairingHistory
from .batch_worker import BatchCaptionWorker
from .srt_editor_dialog import SRTEditorDialog


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
        self.setMinimumSize(800, 850)
        self.config = get_config()

        # Initialize pairing history
        self.pairing_history = PairingHistory(self.config.get_history_db_path())

        # Queue for batch processing: list of dicts with audio_path, srt_path, needs_transcription
        self.queue = []

        self._setup_ui()
        self._apply_theme()
        self._load_settings()

        self.worker = None
        self.batch_worker = None

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

        # Drop Zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        input_layout.addWidget(self.drop_zone)

        # Manual input row (subtitle + audio)
        manual_layout = QHBoxLayout()

        # Subtitle file
        srt_label = QLabel("SRT:")
        srt_label.setFixedWidth(35)
        self.srt_input = QLineEdit()
        self.srt_input.setPlaceholderText("Select SRT file...")
        srt_browse = QPushButton("Browse")
        srt_browse.clicked.connect(self._browse_srt)

        # Audio file
        audio_label = QLabel("Audio:")
        audio_label.setFixedWidth(45)
        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText("Select audio file...")
        audio_browse = QPushButton("Browse")
        audio_browse.clicked.connect(self._browse_audio)

        # Add to queue button
        add_btn = QPushButton("Add")
        add_btn.setToolTip("Add to queue")
        add_btn.clicked.connect(self._add_manual_to_queue)

        manual_layout.addWidget(srt_label)
        manual_layout.addWidget(self.srt_input, 2)
        manual_layout.addWidget(srt_browse)
        manual_layout.addWidget(audio_label)
        manual_layout.addWidget(self.audio_input, 2)
        manual_layout.addWidget(audio_browse)
        manual_layout.addWidget(add_btn)
        input_layout.addLayout(manual_layout)

        # Queue Table
        queue_label = QLabel("Processing Queue:")
        queue_label.setStyleSheet("color: #00ffff; font-weight: bold; margin-top: 10px;")
        input_layout.addWidget(queue_label)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(["Audio File", "SRT Status", "SRT File", "Actions"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.queue_table.setColumnWidth(1, 120)
        self.queue_table.setColumnWidth(3, 195)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setMinimumHeight(120)
        self.queue_table.setMaximumHeight(180)
        self.queue_table.verticalHeader().setVisible(False)
        input_layout.addWidget(self.queue_table)

        # Queue action buttons
        queue_btn_layout = QHBoxLayout()
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        queue_btn_layout.addStretch()
        queue_btn_layout.addWidget(self.clear_queue_btn)
        input_layout.addLayout(queue_btn_layout)

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

        # Text transformation row
        transform_row = QHBoxLayout()
        transform_label = QLabel("Text Options:")
        transform_label.setFixedWidth(100)
        self.all_caps_checkbox = QCheckBox("ALL CAPS")
        self.all_caps_checkbox.setToolTip("Convert all text to uppercase in the video output")
        self.ignore_grammar_checkbox = QCheckBox("Ignore Grammar (. , -)")
        self.ignore_grammar_checkbox.setToolTip("Remove punctuation characters from the video output")
        transform_row.addWidget(transform_label)
        transform_row.addWidget(self.all_caps_checkbox)
        transform_row.addSpacing(20)
        transform_row.addWidget(self.ignore_grammar_checkbox)
        transform_row.addStretch()
        style_layout.addLayout(transform_row)

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

        # Generate Buttons
        btn_layout = QHBoxLayout()

        self.generate_btn = QPushButton("GENERATE VIDEO")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ff88;
                color: #000000;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
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
        self.generate_btn.setToolTip("Generate video for manually selected files")

        self.generate_all_btn = QPushButton("GENERATE ALL VIDEOS")
        self.generate_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffff;
                color: #000000;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00cccc;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.generate_all_btn.clicked.connect(self._generate_all_videos)
        self.generate_all_btn.setToolTip("Process all files in the queue")

        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.generate_all_btn)
        main_layout.addLayout(btn_layout)

        # Progress bar and status
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #00ff88;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)
        main_layout.addLayout(progress_layout)

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
            QTableWidget {
                background-color: #151515;
                color: #cccccc;
                gridline-color: #2a2a2a;
                selection-background-color: rgba(0, 255, 255, 0.3);
                border: 1px solid #404040;
                border-radius: 4px;
                alternate-background-color: #1a1a1a;
            }
            QTableWidget::item {
                padding: 5px;
                background-color: #1a1a1a;
            }
            QTableWidget::item:alternate {
                background-color: #202020;
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 255, 255, 0.2);
                color: #00ffff;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #00ffff;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #404040;
                font-weight: bold;
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

        # Load text transformation settings
        self.all_caps_checkbox.setChecked(self.config.get("all_caps", False))
        self.ignore_grammar_checkbox.setChecked(self.config.get("ignore_grammar", False))

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
        self.config.set("all_caps", self.all_caps_checkbox.isChecked(), autosave=False)
        self.config.set("ignore_grammar", self.ignore_grammar_checkbox.isChecked(), autosave=False)
        self.config.save_config()

    def _log(self, message):
        """Add message to log box."""
        self.log_box.append(message)

    def _browse_srt(self):
        """Browse for subtitle file."""
        last_folder = self.config.get("last_srt_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", last_folder,
            "Subtitle Files (*.srt);;All Files (*.*)"
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
            self.config.set("output_folder", folder)
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
            "outline_size": 2,
            "all_caps": self.all_caps_checkbox.isChecked(),
            "ignore_grammar": self.ignore_grammar_checkbox.isChecked()
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

    # =========================================================================
    # Queue Management Methods
    # =========================================================================

    def _on_files_dropped(self, file_paths):
        """Handle files dropped onto the drop zone."""
        self._log(f"[DROP] Received {len(file_paths)} file(s)")

        for file_path in file_paths:
            self._add_to_queue(file_path)

    def _add_manual_to_queue(self):
        """Add manually selected files to the queue."""
        audio_path = self.audio_input.text().strip()

        if not audio_path:
            QMessageBox.warning(self, "Missing Input", "Please select an audio file first.")
            return

        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "File Not Found", f"Audio file not found:\n{audio_path}")
            return

        # Use the SRT input if provided
        srt_path = self.srt_input.text().strip() if self.srt_input.text().strip() else None

        self._add_to_queue(audio_path, srt_path)

        # Clear inputs after adding
        self.audio_input.clear()
        self.srt_input.clear()

    def _add_to_queue(self, audio_path, srt_path=None):
        """
        Add an audio file to the processing queue.

        Args:
            audio_path: Path to audio file
            srt_path: Optional path to SRT file (if None, will check history or transcribe)
        """
        filename = os.path.basename(audio_path)

        # Check if already in queue
        for item in self.queue:
            if item['audio_path'] == audio_path:
                self._log(f"[QUEUE] {filename} already in queue")
                return

        # Determine SRT status
        needs_transcription = False
        status_text = ""
        status_color = ""

        if srt_path and os.path.exists(srt_path):
            # Manual SRT provided
            status_text = "[OK] Paired"
            status_color = "#00ffff"
            # Save to history
            self.pairing_history.add_pairing(audio_path, srt_path, source='user_provided')
        else:
            # Check history for existing pairing
            pairing = self.pairing_history.find_pairing(audio_path)

            if pairing and pairing.get('srt_path') and os.path.exists(pairing['srt_path']):
                srt_path = pairing['srt_path']
                status_text = "[AUTO] History"
                status_color = "#00ff88"
                self._log(f"[QUEUE] Found existing SRT for {filename}")
            else:
                # Need to transcribe
                srt_path = None
                needs_transcription = True
                status_text = "[!] Will Transcribe"
                status_color = "#ffaa00"
                self._log(f"[QUEUE] {filename} will be transcribed")

        # Add to queue data
        self.queue.append({
            'audio_path': audio_path,
            'srt_path': srt_path,
            'needs_transcription': needs_transcription
        })

        # Add row to table
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        # Audio file cell
        audio_item = QTableWidgetItem(filename)
        audio_item.setToolTip(audio_path)
        audio_item.setFlags(audio_item.flags() & ~Qt.ItemIsEditable)
        self.queue_table.setItem(row, 0, audio_item)

        # Status cell
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QColor(status_color))
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.queue_table.setItem(row, 1, status_item)

        # SRT file cell
        srt_display = os.path.basename(srt_path) if srt_path else "(none)"
        srt_item = QTableWidgetItem(srt_display)
        if srt_path:
            srt_item.setToolTip(srt_path)
        srt_item.setFlags(srt_item.flags() & ~Qt.ItemIsEditable)
        self.queue_table.setItem(row, 2, srt_item)

        # Actions cell with buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)
        actions_layout.setSpacing(4)

        browse_btn = QPushButton("SRT")
        browse_btn.setFixedWidth(40)
        browse_btn.setToolTip("Browse for SRT file")
        browse_btn.clicked.connect(lambda checked, r=row: self._browse_srt_for_row(r))

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(40)
        edit_btn.setToolTip("Edit SRT file")
        edit_btn.setEnabled(bool(srt_path and os.path.exists(srt_path)))
        edit_btn.clicked.connect(lambda checked, r=row: self._edit_srt_for_row(r))

        regen_btn = QPushButton("Re")
        regen_btn.setFixedWidth(30)
        regen_btn.setToolTip("Regenerate transcription")
        regen_btn.clicked.connect(lambda checked, r=row: self._regenerate_srt_for_row(r))

        remove_btn = QPushButton("X")
        remove_btn.setFixedWidth(25)
        remove_btn.setToolTip("Remove from queue")
        remove_btn.setStyleSheet("color: #ff4444; font-weight: bold;")
        remove_btn.clicked.connect(lambda checked, r=row: self._remove_from_queue(r))

        actions_layout.addWidget(browse_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(regen_btn)
        actions_layout.addWidget(remove_btn)
        actions_layout.addStretch()

        self.queue_table.setCellWidget(row, 3, actions_widget)

        self._log(f"[QUEUE] Added: {filename}")

    def _browse_srt_for_row(self, row):
        """Browse for SRT file for a specific queue row."""
        if row >= len(self.queue):
            return

        last_folder = self.config.get("last_srt_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", last_folder,
            "Subtitle Files (*.srt);;All Files (*.*)"
        )

        if file_path:
            self.config.set("last_srt_folder", os.path.dirname(file_path))

            # Update queue data
            audio_path = self.queue[row]['audio_path']
            self.queue[row]['srt_path'] = file_path
            self.queue[row]['needs_transcription'] = False

            # Save to history
            self.pairing_history.add_pairing(audio_path, file_path, source='user_provided')

            # Update table
            status_item = self.queue_table.item(row, 1)
            status_item.setText("[OK] Paired")
            status_item.setForeground(QColor("#00ffff"))

            srt_item = self.queue_table.item(row, 2)
            srt_item.setText(os.path.basename(file_path))
            srt_item.setToolTip(file_path)

            # Enable Edit button
            actions_widget = self.queue_table.cellWidget(row, 3)
            if actions_widget:
                layout = actions_widget.layout()
                if layout and layout.count() >= 2:
                    edit_btn = layout.itemAt(1).widget()
                    if edit_btn:
                        edit_btn.setEnabled(True)

            self._log(f"[QUEUE] SRT updated for row {row + 1}: {os.path.basename(file_path)}")

    def _edit_srt_for_row(self, row):
        """Open SRT editor for a specific queue row."""
        if row >= len(self.queue):
            return

        srt_path = self.queue[row].get('srt_path')

        if not srt_path or not os.path.exists(srt_path):
            QMessageBox.warning(
                self, "No SRT File",
                "No SRT file is associated with this audio file.\n"
                "Please assign an SRT file first."
            )
            return

        # Open SRT editor dialog
        dialog = SRTEditorDialog(srt_path, self)
        dialog.exec_()

        # Log the action
        filename = os.path.basename(srt_path)
        self._log(f"[QUEUE] SRT editor closed for: {filename}")

    def _regenerate_srt_for_row(self, row):
        """Mark a queue item to regenerate its transcription."""
        if row >= len(self.queue):
            return

        self.queue[row]['srt_path'] = None
        self.queue[row]['needs_transcription'] = True

        # Update table
        status_item = self.queue_table.item(row, 1)
        status_item.setText("[!] Will Transcribe")
        status_item.setForeground(QColor("#ffaa00"))

        srt_item = self.queue_table.item(row, 2)
        srt_item.setText("(pending)")
        srt_item.setToolTip("")

        filename = os.path.basename(self.queue[row]['audio_path'])
        self._log(f"[QUEUE] {filename} marked for re-transcription")

    def _remove_from_queue(self, row):
        """Remove item from queue."""
        if row >= len(self.queue):
            return

        filename = os.path.basename(self.queue[row]['audio_path'])

        # Remove from data
        self.queue.pop(row)

        # Remove from table
        self.queue_table.removeRow(row)

        # Update button connections for remaining rows
        self._update_queue_button_connections()

        self._log(f"[QUEUE] Removed: {filename}")

    def _update_queue_button_connections(self):
        """Update button connections after row removal."""
        for row in range(self.queue_table.rowCount()):
            actions_widget = self.queue_table.cellWidget(row, 3)
            if actions_widget:
                layout = actions_widget.layout()
                if layout and layout.count() >= 4:
                    # Browse button (index 0)
                    browse_btn = layout.itemAt(0).widget()
                    if browse_btn:
                        browse_btn.clicked.disconnect()
                        browse_btn.clicked.connect(lambda checked, r=row: self._browse_srt_for_row(r))

                    # Edit button (index 1)
                    edit_btn = layout.itemAt(1).widget()
                    if edit_btn:
                        edit_btn.clicked.disconnect()
                        edit_btn.clicked.connect(lambda checked, r=row: self._edit_srt_for_row(r))
                        # Update enabled state based on SRT existence
                        srt_path = self.queue[row].get('srt_path') if row < len(self.queue) else None
                        edit_btn.setEnabled(bool(srt_path and os.path.exists(srt_path)))

                    # Regen button (index 2)
                    regen_btn = layout.itemAt(2).widget()
                    if regen_btn:
                        regen_btn.clicked.disconnect()
                        regen_btn.clicked.connect(lambda checked, r=row: self._regenerate_srt_for_row(r))

                    # Remove button (index 3)
                    remove_btn = layout.itemAt(3).widget()
                    if remove_btn:
                        remove_btn.clicked.disconnect()
                        remove_btn.clicked.connect(lambda checked, r=row: self._remove_from_queue(r))

    def _clear_queue(self):
        """Clear all items from the queue."""
        if not self.queue:
            return

        reply = QMessageBox.question(
            self, "Clear Queue",
            f"Remove all {len(self.queue)} items from the queue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.queue.clear()
            self.queue_table.setRowCount(0)
            self._log("[QUEUE] Queue cleared")

    # =========================================================================
    # Batch Processing Methods
    # =========================================================================

    def _generate_all_videos(self):
        """Start batch video generation for all items in queue."""
        if not self.queue:
            QMessageBox.warning(self, "Empty Queue", "No files in the processing queue.")
            return

        # Check for items that need transcription but API key might be missing
        needs_transcription = any(item['needs_transcription'] for item in self.queue)

        if needs_transcription:
            # Quick check for API key
            from core.env_loader import load_environment, get_env_var
            load_environment()
            api_key = get_env_var("ELEVENLABS_API_KEY")

            if not api_key:
                reply = QMessageBox.warning(
                    self, "API Key Missing",
                    "Some files need transcription but ELEVENLABS_API_KEY is not set.\n\n"
                    "Files without existing SRT pairings will fail.\n\n"
                    "Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

        # Save settings
        self._save_settings()

        # Disable UI during processing
        self._set_batch_processing_state(True)

        # Get settings
        settings = self._get_settings()
        settings['transparent_background'] = self.transparent_checkbox.isChecked()

        # Create and start batch worker
        self.batch_worker = BatchCaptionWorker(
            queue_items=self.queue.copy(),
            settings=settings,
            output_folder=self.output_folder.text().strip(),
            transcript_folder=self.config.get_transcript_folder(),
            pairing_history=self.pairing_history,
            continue_on_error=self.config.get("batch_continue_on_error", True)
        )

        # Connect signals
        self.batch_worker.log_signal.connect(self._log)
        self.batch_worker.batch_started.connect(self._on_batch_started)
        self.batch_worker.progress_signal.connect(self._on_batch_progress)
        self.batch_worker.transcription_completed.connect(self._on_transcription_completed)
        self.batch_worker.generation_completed.connect(self._on_video_generated)
        self.batch_worker.batch_summary.connect(self._on_batch_summary)
        self.batch_worker.finished.connect(self._on_batch_finished)

        self.batch_worker.start()

    def _set_batch_processing_state(self, processing):
        """Enable/disable UI elements during batch processing."""
        self.generate_btn.setEnabled(not processing)
        self.generate_all_btn.setEnabled(not processing)
        self.clear_queue_btn.setEnabled(not processing)
        self.drop_zone.set_enabled_state(not processing)

        if processing:
            self.generate_all_btn.setText("PROCESSING...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        else:
            self.generate_all_btn.setText("GENERATE ALL VIDEOS")
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")

    def _on_batch_started(self, total):
        """Handle batch processing start."""
        self._log(f"[BATCH] Starting batch processing: {total} files")
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)

    def _on_batch_progress(self, current, total, filename):
        """Handle batch progress update."""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Processing {current}/{total}: {filename}")

    def _on_transcription_completed(self, filename, srt_path):
        """Handle transcription completion for a file."""
        # Update queue table if file is still there
        for row, item in enumerate(self.queue):
            if os.path.basename(item['audio_path']) == filename:
                # Update data
                item['srt_path'] = srt_path
                item['needs_transcription'] = False

                # Update table
                status_item = self.queue_table.item(row, 1)
                if status_item:
                    status_item.setText("[AUTO] Transcribed")
                    status_item.setForeground(QColor("#00ff88"))

                srt_item = self.queue_table.item(row, 2)
                if srt_item:
                    srt_item.setText(os.path.basename(srt_path))
                    srt_item.setToolTip(srt_path)

                # Enable Edit button
                actions_widget = self.queue_table.cellWidget(row, 3)
                if actions_widget:
                    layout = actions_widget.layout()
                    if layout and layout.count() >= 2:
                        edit_btn = layout.itemAt(1).widget()
                        if edit_btn:
                            edit_btn.setEnabled(True)
                break

    def _on_video_generated(self, filename, success, message):
        """Handle video generation completion for a file."""
        if success:
            # Mark row as complete (could add visual indicator)
            for row, item in enumerate(self.queue):
                if os.path.basename(item['audio_path']) == filename:
                    status_item = self.queue_table.item(row, 1)
                    if status_item:
                        status_item.setText("[DONE]")
                        status_item.setForeground(QColor("#00ff88"))
                    break

    def _on_batch_summary(self, stats):
        """Handle batch summary."""
        duration = stats.get('duration_seconds', 0)
        duration_str = f"{duration:.1f}s" if duration < 60 else f"{duration / 60:.1f}m"

        summary = (
            f"Batch Processing Complete\n\n"
            f"Total Files: {stats['total_files']}\n"
            f"Successful Transcriptions: {stats['successful_transcriptions']}\n"
            f"Successful Videos: {stats['successful_generations']}\n"
            f"Failures: {stats['transcription_failures'] + stats['generation_failures']}\n"
            f"Processing Time: {duration_str}"
        )

        if stats['successful_generations'] == stats['total_files']:
            QMessageBox.information(self, "Batch Complete - All Successful!", summary)
        elif stats['successful_generations'] > 0:
            QMessageBox.information(self, "Batch Complete - Partial Success", summary)
        else:
            QMessageBox.warning(self, "Batch Complete - All Failed", summary)

    def _on_batch_finished(self):
        """Handle batch processing completion."""
        self._set_batch_processing_state(False)
        self._log("[BATCH] Batch processing complete")


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
