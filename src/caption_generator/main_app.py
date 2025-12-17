# -*- coding: utf-8 -*-
"""
Main Application Module for Caption Generator.

A PyQt5 application for creating caption/lyric videos from SRT files.
Features a three-panel layout with style controls, phrase editing, live preview,
and an interactive waveform timeline.
"""

import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QTextEdit, QFileDialog,
    QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSplitter, QFrame, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from .config_manager import get_config
from .video_generator import generate_caption_video, get_audio_duration
from .drop_zone import DropZoneWidget
from .pairing_history import PairingHistory
from .batch_worker import BatchCaptionWorker
from .srt_editor_dialog import SRTEditorDialog
from .settings_dialog import SettingsDialog
from .srt_data_model import SRTDataModel

# New panel widgets
from .style_controls_panel import StyleControlsPanel
from .phrase_list_widget import PhraseListWidget
from .video_preview_widget import VideoPreviewWidget
from .timeline_widget import TimelineWidget
from .transcription_service import TranscriptionService


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
    """Main Caption Generator application window with three-panel layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BEDROT Caption Generator")
        self.setMinimumSize(1200, 800)
        self.config = get_config()

        # Initialize pairing history
        self.pairing_history = PairingHistory(self.config.get_history_db_path())

        # Queue for batch processing
        self.queue = []

        # Current working files
        self.current_audio_path = None
        self.current_srt_path = None

        self._setup_ui()
        self._apply_theme()
        self._load_settings()
        self._connect_signals()

        self.worker = None
        self.batch_worker = None
        self.transcription_worker = None

    def _setup_ui(self):
        """Set up the user interface with three-panel layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Title row with settings button
        title_row = QHBoxLayout()

        title_label = QLabel("CAPTION GENERATOR")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ffff; padding: 5px;")
        title_row.addWidget(title_label)

        title_row.addStretch()

        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setFixedWidth(80)
        self.settings_btn.setToolTip("Open settings")
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        title_row.addWidget(self.settings_btn)

        main_layout.addLayout(title_row)

        # Tab widget for Editor and Queue views
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #121212;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #e0e0e0;
                padding: 8px 20px;
                border: 1px solid #404040;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #252525;
                color: #00ffff;
                border-color: #00ffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #202020;
            }
        """)

        # === EDITOR TAB ===
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(8, 8, 8, 8)
        editor_layout.setSpacing(8)

        # Drop zone for Editor tab (accepts both audio and SRT files)
        self.editor_drop_zone = DropZoneWidget(accept_subtitles=True)
        self.editor_drop_zone.setMaximumHeight(80)
        self.editor_drop_zone.label.setText("Drop audio or SRT files here")
        self.editor_drop_zone.subtitle.setText("Supports WAV, MP3, FLAC, M4A, AAC and SRT files")
        self.editor_drop_zone.files_dropped.connect(self._on_editor_files_dropped)
        editor_layout.addWidget(self.editor_drop_zone)

        # Three-panel splitter (horizontal)
        self.panel_splitter = QSplitter(Qt.Horizontal)
        self.panel_splitter.setHandleWidth(4)
        self.panel_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #404040;
            }
            QSplitter::handle:hover {
                background-color: #00ffff;
            }
        """)

        # Left panel: Style Controls
        self.style_panel = StyleControlsPanel()
        self.style_panel.setMinimumWidth(220)
        self.style_panel.setMaximumWidth(350)
        self.panel_splitter.addWidget(self.style_panel)

        # Center panel: Phrase List
        self.phrase_panel = PhraseListWidget()
        self.phrase_panel.setMinimumWidth(300)
        self.panel_splitter.addWidget(self.phrase_panel)

        # Right panel: Video Preview
        self.preview_panel = VideoPreviewWidget()
        self.preview_panel.setMinimumWidth(300)
        self.panel_splitter.addWidget(self.preview_panel)

        # Set initial splitter sizes (left: 250, center: 400, right: 350)
        self.panel_splitter.setSizes([250, 400, 350])

        editor_layout.addWidget(self.panel_splitter, 1)

        # Timeline at bottom
        self.timeline = TimelineWidget()
        self.timeline.setMaximumHeight(160)
        editor_layout.addWidget(self.timeline)

        # File selection row
        file_frame = QFrame()
        file_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        file_layout = QHBoxLayout(file_frame)
        file_layout.setSpacing(8)

        # Audio file
        audio_label = QLabel("Audio:")
        audio_label.setStyleSheet("color: #00ffff; font-weight: bold;")
        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText("Select audio file...")
        self.audio_input.setReadOnly(True)
        audio_browse = QPushButton("Browse")
        audio_browse.clicked.connect(self._browse_audio)

        # SRT file
        srt_label = QLabel("SRT:")
        srt_label.setStyleSheet("color: #00ffff; font-weight: bold;")
        self.srt_input = QLineEdit()
        self.srt_input.setPlaceholderText("Select SRT file...")
        self.srt_input.setReadOnly(True)
        srt_browse = QPushButton("Browse")
        srt_browse.clicked.connect(self._browse_srt)

        file_layout.addWidget(audio_label)
        file_layout.addWidget(self.audio_input, 2)
        file_layout.addWidget(audio_browse)
        file_layout.addSpacing(16)
        file_layout.addWidget(srt_label)
        file_layout.addWidget(self.srt_input, 2)
        file_layout.addWidget(srt_browse)

        editor_layout.addWidget(file_frame)

        # Generate button and output folder row
        gen_row = QHBoxLayout()

        # Output folder
        folder_label = QLabel("Output:")
        folder_label.setStyleSheet("color: #888888;")
        self.output_folder = QLineEdit()
        self.output_folder.setText(self.config.get_output_folder())
        self.output_folder.setFixedWidth(250)
        folder_browse = QPushButton("...")
        folder_browse.setFixedWidth(30)
        folder_browse.clicked.connect(self._browse_output)

        gen_row.addWidget(folder_label)
        gen_row.addWidget(self.output_folder)
        gen_row.addWidget(folder_browse)
        gen_row.addStretch()

        # Generate Captions button (transcription)
        self.generate_captions_btn = QPushButton("GENERATE CAPTIONS")
        self.generate_captions_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffff;
                color: #000000;
                font-size: 13px;
                font-weight: bold;
                padding: 12px 24px;
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
        self.generate_captions_btn.setToolTip("Generate SRT captions from audio using ElevenLabs")
        self.generate_captions_btn.clicked.connect(self._generate_captions)
        gen_row.addWidget(self.generate_captions_btn)

        gen_row.addSpacing(8)

        # Generate Video button
        self.generate_btn = QPushButton("GENERATE VIDEO")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ff88;
                color: #000000;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 32px;
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
        gen_row.addWidget(self.generate_btn)

        editor_layout.addLayout(gen_row)

        self.tab_widget.addTab(editor_widget, "Editor")

        # === QUEUE TAB ===
        queue_widget = QWidget()
        queue_layout = QVBoxLayout(queue_widget)
        queue_layout.setContentsMargins(8, 8, 8, 8)
        queue_layout.setSpacing(8)

        # Drop Zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        self.drop_zone.setMaximumHeight(100)
        queue_layout.addWidget(self.drop_zone)

        # Manual input row
        manual_layout = QHBoxLayout()
        queue_srt_label = QLabel("SRT:")
        queue_srt_label.setFixedWidth(35)
        self.queue_srt_input = QLineEdit()
        self.queue_srt_input.setPlaceholderText("Select SRT file...")
        queue_srt_browse = QPushButton("Browse")
        queue_srt_browse.clicked.connect(self._browse_queue_srt)

        queue_audio_label = QLabel("Audio:")
        queue_audio_label.setFixedWidth(45)
        self.queue_audio_input = QLineEdit()
        self.queue_audio_input.setPlaceholderText("Select audio file...")
        queue_audio_browse = QPushButton("Browse")
        queue_audio_browse.clicked.connect(self._browse_queue_audio)

        add_btn = QPushButton("Add to Queue")
        add_btn.clicked.connect(self._add_manual_to_queue)

        manual_layout.addWidget(queue_srt_label)
        manual_layout.addWidget(self.queue_srt_input, 2)
        manual_layout.addWidget(queue_srt_browse)
        manual_layout.addWidget(queue_audio_label)
        manual_layout.addWidget(self.queue_audio_input, 2)
        manual_layout.addWidget(queue_audio_browse)
        manual_layout.addWidget(add_btn)
        queue_layout.addLayout(manual_layout)

        # Queue Table
        queue_label = QLabel("Processing Queue:")
        queue_label.setStyleSheet("color: #00ffff; font-weight: bold; margin-top: 10px;")
        queue_layout.addWidget(queue_label)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(["Audio File", "SRT Status", "SRT File", "Actions"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.queue_table.setColumnWidth(1, 120)
        self.queue_table.setColumnWidth(3, 220)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.verticalHeader().setVisible(False)
        queue_layout.addWidget(self.queue_table, 1)

        # Queue action buttons row
        queue_btn_layout = QHBoxLayout()

        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self._clear_queue)

        self.generate_all_btn = QPushButton("GENERATE ALL VIDEOS")
        self.generate_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffff;
                color: #000000;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 32px;
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

        queue_btn_layout.addWidget(self.clear_queue_btn)
        queue_btn_layout.addStretch()
        queue_btn_layout.addWidget(self.generate_all_btn)
        queue_layout.addLayout(queue_btn_layout)

        self.tab_widget.addTab(queue_widget, "Batch Queue")

        main_layout.addWidget(self.tab_widget, 1)

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
        self.log_box.setMaximumHeight(100)
        main_layout.addWidget(self.log_box)

        self._log("[Caption Generator] Ready. Use the Editor tab to create videos or Queue tab for batch processing.")

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
            QTableWidget QPushButton {
                background-color: #252525;
                border: 1px solid #00ffff;
                border-radius: 3px;
                padding: 4px 6px;
                color: #00ffff;
                font-weight: bold;
                font-size: 11px;
                min-width: 35px;
                min-height: 24px;
            }
            QTableWidget QPushButton:hover {
                background-color: #303030;
                border-color: #00ff88;
                color: #00ff88;
            }
        """)

    def _connect_signals(self):
        """Connect signals between panels."""
        # Style panel -> Preview
        self.style_panel.style_changed.connect(self._on_style_changed)

        # Style panel -> Underlay controls
        self.style_panel.underlay_mode_changed.connect(self.preview_panel.set_underlay_mode)
        self.style_panel.underlay_video_selected.connect(self._on_underlay_video_selected)
        self.style_panel.color_changed.connect(
            lambda text_color, bg_color: self.preview_panel.set_background_color(bg_color)
        )

        # Phrase panel -> Preview, Timeline
        self.phrase_panel.phrase_selected.connect(self._on_phrase_selected)
        self.phrase_panel.srt_loaded.connect(self._on_srt_loaded)

        # Timeline -> Phrase panel, Preview
        self.timeline.phrase_selected.connect(self.phrase_panel.select_phrase)
        self.timeline.timing_changed.connect(self._on_timeline_timing_changed)
        self.timeline.position_changed.connect(self._on_playback_position_changed)

        # Preview playback -> Timeline sync
        self.preview_panel.position_changed.connect(self._on_playback_position_changed)
        self.preview_panel.playback_state_changed.connect(self._on_playback_state_changed)

    def _load_settings(self):
        """Load saved settings into UI."""
        self.style_panel.load_settings(self.config)

    def _save_settings(self):
        """Save current UI settings to config."""
        self.style_panel.save_settings(self.config)
        self.config.set("output_folder", self.output_folder.text(), autosave=True)

    def _log(self, message):
        """Add message to log box."""
        self.log_box.append(message)

    def _browse_srt(self):
        """Browse for subtitle file (Editor tab)."""
        last_folder = self.config.get("last_srt_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", last_folder,
            "Subtitle Files (*.srt *.vtt);;All Files (*.*)"
        )
        if file_path:
            self._load_srt_file(file_path)

    def _load_srt_file(self, file_path: str):
        """Load an SRT file into the editor."""
        self.srt_input.setText(file_path)
        self.config.set("last_srt_folder", os.path.dirname(file_path))
        self.current_srt_path = file_path
        self._log(f"[Caption Generator] Subtitle file selected: {os.path.basename(file_path)}")

        # Load into phrase panel and timeline
        self.phrase_panel.load_srt(file_path)
        if self.phrase_panel.model:
            self.timeline.set_model(self.phrase_panel.model)

        # Save pairing if we have an audio file loaded
        if self.current_audio_path:
            self.pairing_history.add_pairing(self.current_audio_path, file_path, source='user_provided')

    def _on_editor_files_dropped(self, file_paths):
        """Handle files dropped onto the Editor tab drop zone."""
        audio_files = []
        srt_files = []

        for fp in file_paths:
            ext = os.path.splitext(fp)[1].lower()
            if ext in {'.wav', '.mp3', '.flac', '.m4a', '.aac'}:
                audio_files.append(fp)
            elif ext in {'.srt', '.vtt'}:
                srt_files.append(fp)

        # Load first audio file found
        if audio_files:
            self._load_audio_file(audio_files[0])
            if len(audio_files) > 1:
                self._log(f"[Caption Generator] Note: Only loaded first audio file. Use Queue tab for multiple files.")

        # Load first SRT file found (if not already auto-detected from audio)
        if srt_files and not self.current_srt_path:
            self._load_srt_file(srt_files[0])
        elif srt_files and self.current_srt_path:
            # Replace the current SRT with the dropped one
            self._load_srt_file(srt_files[0])

    def _browse_audio(self):
        """Browse for audio file (Editor tab)."""
        last_folder = self.config.get("last_audio_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", last_folder,
            "Audio Files (*.wav *.mp3 *.flac *.m4a *.aac);;All Files (*.*)"
        )
        if file_path:
            self._load_audio_file(file_path)

    def _load_audio_file(self, file_path: str):
        """Load an audio file and auto-detect associated SRT."""
        self.audio_input.setText(file_path)
        self.config.set("last_audio_folder", os.path.dirname(file_path))
        self.current_audio_path = file_path

        # Get duration
        duration = get_audio_duration(file_path)
        if duration:
            mins = int(duration // 60)
            secs = int(duration % 60)
            self._log(f"[Caption Generator] Audio file selected: {os.path.basename(file_path)} ({mins}:{secs:02d})")
        else:
            self._log(f"[Caption Generator] Audio file selected: {os.path.basename(file_path)}")

        # Load into timeline
        self.timeline.load_audio(file_path)

        # Load into preview panel for playback
        self.preview_panel.load_audio(file_path)

        # Apply current style settings to preview
        self._on_style_changed()

        # Auto-detect associated SRT from pairing history
        pairing = self.pairing_history.find_pairing(file_path)
        if pairing and pairing.get('srt_path') and os.path.exists(pairing['srt_path']):
            srt_path = pairing['srt_path']
            self._log(f"[Caption Generator] Auto-detected SRT: {os.path.basename(srt_path)}")
            self._load_srt_file(srt_path)
        else:
            # Try to find SRT with same name in same directory
            base_name = os.path.splitext(file_path)[0]
            for ext in ['.srt', '.vtt']:
                potential_srt = base_name + ext
                if os.path.exists(potential_srt):
                    self._log(f"[Caption Generator] Found matching SRT: {os.path.basename(potential_srt)}")
                    self._load_srt_file(potential_srt)
                    # Save pairing for future
                    self.pairing_history.add_pairing(file_path, potential_srt, source='auto_detected')
                    break

    def _browse_output(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.output_folder.text()
        )
        if folder:
            self.output_folder.setText(folder)
            self.config.set("output_folder", folder)
            self._log(f"[Caption Generator] Output folder set: {folder}")

    def _open_settings_dialog(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self, self.config)
        dialog.exec_()

    def _on_style_changed(self):
        """Handle style change from style panel."""
        settings = self.style_panel.get_settings()
        self.preview_panel.set_caption_style(settings)

    def _on_underlay_video_selected(self, video_path: str):
        """Handle underlay video selection from style panel."""
        if video_path:
            self.preview_panel.load_underlay_video(video_path)
            self._log(f"[Caption Generator] Underlay video loaded: {os.path.basename(video_path)}")
        else:
            self.preview_panel.clear_underlay_video()
            self._log("[Caption Generator] Underlay video cleared")

    def _on_playback_position_changed(self, position_ms: int):
        """Handle playback position change - sync caption display."""
        # Find phrase at current position
        phrase_index = self.phrase_panel.get_phrase_at(position_ms)

        if phrase_index is not None:
            # Get the phrase text
            model = self.phrase_panel.get_model()
            if model and 0 <= phrase_index < len(model.blocks):
                block = model.blocks[phrase_index]
                self.preview_panel.set_caption_text(block.text)

                # Select the phrase (without triggering a loop)
                if self.phrase_panel.selected_index != phrase_index:
                    self.phrase_panel.select_phrase(phrase_index)
                    self.timeline.select_phrase(phrase_index)
        else:
            # No phrase at this position
            self.preview_panel.clear_caption()

    def _on_playback_state_changed(self, is_playing: bool):
        """Handle playback state change."""
        status = "Playing" if is_playing else "Paused"
        self._log(f"[Caption Generator] Playback: {status}")

    def _on_phrase_selected(self, index: int):
        """Handle phrase selection."""
        # Update preview with selected phrase text
        block = self.phrase_panel.get_selected_phrase()
        if block:
            self.preview_panel.set_caption_text(block.text)

        # Update timeline selection
        self.timeline.select_phrase(index)

    def _on_srt_loaded(self, srt_path: str):
        """Handle SRT file loaded in phrase panel."""
        self.srt_input.setText(srt_path)
        self.current_srt_path = srt_path

        # Update timeline with model
        if self.phrase_panel.model:
            self.timeline.set_model(self.phrase_panel.model)

    def _on_timeline_timing_changed(self, index: int, start_ms: int, end_ms: int):
        """Handle timing change from timeline drag."""
        # Update phrase panel
        self.phrase_panel.update_phrase_timing(index, start_ms, end_ms)

        # Update model if it exists
        model = self.phrase_panel.get_model()
        if model and 0 <= index < len(model.blocks):
            model.blocks[index].start_ms = start_ms
            model.blocks[index].end_ms = end_ms

    def _get_settings(self):
        """Get current settings as dictionary."""
        settings = self.style_panel.get_settings()
        settings["safe_area_mode"] = self.config.get("safe_area_mode", True)
        return settings

    def _generate_video(self):
        """Start video generation (Editor tab)."""
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

        # Save modified SRT if changes were made
        model = self.phrase_panel.get_model()
        if model and model.file_path:
            model.save_to_file()
            self._log("[Caption Generator] Saved SRT changes")

        # Check if transparent mode is enabled
        is_transparent = self.style_panel.is_transparent()

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
        self.progress_bar.setRange(0, 0)

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
    # Transcription Methods (Generate Captions)
    # =========================================================================

    def _generate_captions(self):
        """Generate captions from audio using ElevenLabs transcription."""
        audio_path = self.audio_input.text().strip()

        if not audio_path:
            QMessageBox.warning(self, "Missing Input", "Please select an audio file first.")
            return

        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "File Not Found", f"Audio file not found:\n{audio_path}")
            return

        # Get transcript output folder
        transcript_folder = self.config.get_transcript_folder()
        max_words = self.style_panel.get_words_per_segment()

        # Disable button during transcription
        self.generate_captions_btn.setEnabled(False)
        self.generate_captions_btn.setText("GENERATING...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Start transcription service
        self.transcription_worker = TranscriptionService(
            audio_path=audio_path,
            output_folder=transcript_folder,
            max_words_per_segment=max_words
        )
        self.transcription_worker.log_signal.connect(self._log)
        self.transcription_worker.transcription_completed.connect(self._on_editor_transcription_completed)
        self.transcription_worker.transcription_failed.connect(self._on_editor_transcription_failed)
        self.transcription_worker.start()

    def _on_editor_transcription_completed(self, audio_path: str, srt_path: str):
        """Handle successful transcription in Editor tab."""
        self.generate_captions_btn.setEnabled(True)
        self.generate_captions_btn.setText("GENERATE CAPTIONS")
        self.progress_bar.setVisible(False)

        # Load the generated SRT
        self._load_srt_file(srt_path)

        # Save pairing to history
        self.pairing_history.add_pairing(audio_path, srt_path, source='auto_transcribed')

        self._log(f"[Caption Generator] [OK] Captions generated: {os.path.basename(srt_path)}")
        QMessageBox.information(
            self, "Transcription Complete",
            f"Captions generated successfully!\n\nSaved to:\n{os.path.basename(srt_path)}"
        )

    def _on_editor_transcription_failed(self, audio_path: str, error_msg: str):
        """Handle failed transcription in Editor tab."""
        self.generate_captions_btn.setEnabled(True)
        self.generate_captions_btn.setText("GENERATE CAPTIONS")
        self.progress_bar.setVisible(False)

        self._log(f"[Caption Generator] [ERROR] Transcription failed: {error_msg}")
        QMessageBox.critical(
            self, "Transcription Failed",
            f"Failed to generate captions.\n\nError: {error_msg}"
        )

    # =========================================================================
    # Queue Tab Methods
    # =========================================================================

    def _browse_queue_srt(self):
        """Browse for SRT file (Queue tab)."""
        last_folder = self.config.get("last_srt_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", last_folder,
            "Subtitle Files (*.srt);;All Files (*.*)"
        )
        if file_path:
            self.queue_srt_input.setText(file_path)
            self.config.set("last_srt_folder", os.path.dirname(file_path))

    def _browse_queue_audio(self):
        """Browse for audio file (Queue tab)."""
        last_folder = self.config.get("last_audio_folder", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", last_folder,
            "Audio Files (*.wav *.mp3 *.flac *.m4a *.aac);;All Files (*.*)"
        )
        if file_path:
            self.queue_audio_input.setText(file_path)
            self.config.set("last_audio_folder", os.path.dirname(file_path))

    def _on_files_dropped(self, file_paths):
        """Handle files dropped onto the drop zone."""
        self._log(f"[DROP] Received {len(file_paths)} file(s)")
        for file_path in file_paths:
            self._add_to_queue(file_path)

    def _add_manual_to_queue(self):
        """Add manually selected files to the queue."""
        audio_path = self.queue_audio_input.text().strip()

        if not audio_path:
            QMessageBox.warning(self, "Missing Input", "Please select an audio file first.")
            return

        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "File Not Found", f"Audio file not found:\n{audio_path}")
            return

        srt_path = self.queue_srt_input.text().strip() if self.queue_srt_input.text().strip() else None

        self._add_to_queue(audio_path, srt_path)

        self.queue_audio_input.clear()
        self.queue_srt_input.clear()

    def _add_to_queue(self, audio_path, srt_path=None):
        """Add an audio file to the processing queue."""
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
            status_text = "[OK] Paired"
            status_color = "#00ffff"
            self.pairing_history.add_pairing(audio_path, srt_path, source='user_provided')
        else:
            pairing = self.pairing_history.find_pairing(audio_path)

            if pairing and pairing.get('srt_path') and os.path.exists(pairing['srt_path']):
                srt_path = pairing['srt_path']
                status_text = "[AUTO] History"
                status_color = "#00ff88"
                self._log(f"[QUEUE] Found existing SRT for {filename}")
            else:
                srt_path = None
                needs_transcription = True
                status_text = "[!] Will Transcribe"
                status_color = "#ffaa00"
                self._log(f"[QUEUE] {filename} will be transcribed")

        self.queue.append({
            'audio_path': audio_path,
            'srt_path': srt_path,
            'needs_transcription': needs_transcription
        })

        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        self.queue_table.setRowHeight(row, 40)

        audio_item = QTableWidgetItem(filename)
        audio_item.setToolTip(audio_path)
        audio_item.setFlags(audio_item.flags() & ~Qt.ItemIsEditable)
        self.queue_table.setItem(row, 0, audio_item)

        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QColor(status_color))
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.queue_table.setItem(row, 1, status_item)

        srt_display = os.path.basename(srt_path) if srt_path else "(none)"
        srt_item = QTableWidgetItem(srt_display)
        if srt_path:
            srt_item.setToolTip(srt_path)
        srt_item.setFlags(srt_item.flags() & ~Qt.ItemIsEditable)
        self.queue_table.setItem(row, 2, srt_item)

        # Actions cell with buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)

        browse_btn = QPushButton("SRT")
        browse_btn.setMinimumSize(45, 26)
        browse_btn.setToolTip("Browse for SRT file")
        browse_btn.clicked.connect(lambda checked, r=row: self._browse_srt_for_row(r))

        edit_btn = QPushButton("Edit")
        edit_btn.setMinimumSize(45, 26)
        edit_btn.setToolTip("Edit SRT file")
        edit_btn.setEnabled(bool(srt_path and os.path.exists(srt_path)))
        edit_btn.clicked.connect(lambda checked, r=row: self._edit_srt_for_row(r))

        regen_btn = QPushButton("Re")
        regen_btn.setMinimumSize(35, 26)
        regen_btn.setToolTip("Regenerate transcription")
        regen_btn.clicked.connect(lambda checked, r=row: self._regenerate_srt_for_row(r))

        remove_btn = QPushButton("X")
        remove_btn.setMinimumSize(30, 26)
        remove_btn.setToolTip("Remove from queue")
        remove_btn.setStyleSheet("""
            QPushButton {
                color: #ff4444;
                font-weight: bold;
                background-color: #252525;
                border: 1px solid #ff4444;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #402020;
                border-color: #ff6666;
                color: #ff6666;
            }
        """)
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

            audio_path = self.queue[row]['audio_path']
            self.queue[row]['srt_path'] = file_path
            self.queue[row]['needs_transcription'] = False

            self.pairing_history.add_pairing(audio_path, file_path, source='user_provided')

            status_item = self.queue_table.item(row, 1)
            status_item.setText("[OK] Paired")
            status_item.setForeground(QColor("#00ffff"))

            srt_item = self.queue_table.item(row, 2)
            srt_item.setText(os.path.basename(file_path))
            srt_item.setToolTip(file_path)

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

        dialog = SRTEditorDialog(srt_path, self)
        dialog.exec_()

        filename = os.path.basename(srt_path)
        self._log(f"[QUEUE] SRT editor closed for: {filename}")

    def _regenerate_srt_for_row(self, row):
        """Mark a queue item to regenerate its transcription."""
        if row >= len(self.queue):
            return

        self.queue[row]['srt_path'] = None
        self.queue[row]['needs_transcription'] = True

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
        self.queue.pop(row)
        self.queue_table.removeRow(row)
        self._update_queue_button_connections()
        self._log(f"[QUEUE] Removed: {filename}")

    def _update_queue_button_connections(self):
        """Update button connections after row removal."""
        for row in range(self.queue_table.rowCount()):
            actions_widget = self.queue_table.cellWidget(row, 3)
            if actions_widget:
                layout = actions_widget.layout()
                if layout and layout.count() >= 4:
                    browse_btn = layout.itemAt(0).widget()
                    if browse_btn:
                        browse_btn.clicked.disconnect()
                        browse_btn.clicked.connect(lambda checked, r=row: self._browse_srt_for_row(r))

                    edit_btn = layout.itemAt(1).widget()
                    if edit_btn:
                        edit_btn.clicked.disconnect()
                        edit_btn.clicked.connect(lambda checked, r=row: self._edit_srt_for_row(r))
                        srt_path = self.queue[row].get('srt_path') if row < len(self.queue) else None
                        edit_btn.setEnabled(bool(srt_path and os.path.exists(srt_path)))

                    regen_btn = layout.itemAt(2).widget()
                    if regen_btn:
                        regen_btn.clicked.disconnect()
                        regen_btn.clicked.connect(lambda checked, r=row: self._regenerate_srt_for_row(r))

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

    def _generate_all_videos(self):
        """Start batch video generation for all items in queue."""
        if not self.queue:
            QMessageBox.warning(self, "Empty Queue", "No files in the processing queue.")
            return

        needs_transcription = any(item['needs_transcription'] for item in self.queue)

        if needs_transcription:
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

        self._save_settings()
        self._set_batch_processing_state(True)

        settings = self._get_settings()
        settings['transparent_background'] = self.style_panel.is_transparent()

        self.batch_worker = BatchCaptionWorker(
            queue_items=self.queue.copy(),
            settings=settings,
            output_folder=self.output_folder.text().strip(),
            transcript_folder=self.config.get_transcript_folder(),
            pairing_history=self.pairing_history,
            continue_on_error=self.config.get("batch_continue_on_error", True),
            max_words_per_segment=self.style_panel.get_words_per_segment()
        )

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
        for row, item in enumerate(self.queue):
            if os.path.basename(item['audio_path']) == filename:
                item['srt_path'] = srt_path
                item['needs_transcription'] = False

                status_item = self.queue_table.item(row, 1)
                if status_item:
                    status_item.setText("[AUTO] Transcribed")
                    status_item.setForeground(QColor("#00ff88"))

                srt_item = self.queue_table.item(row, 2)
                if srt_item:
                    srt_item.setText(os.path.basename(srt_path))
                    srt_item.setToolTip(srt_path)

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
