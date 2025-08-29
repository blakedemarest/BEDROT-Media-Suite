"""Main application GUI for MV Maker."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
    QMessageBox, QGroupBox, QComboBox, QApplication,
    QStyle, QSplitter, QFrame, QSlider, QTabWidget,
    QRadioButton, QButtonGroup, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QUrl
from PyQt5.QtGui import QIcon, QFont, QPixmap, QDragEnterEvent, QDropEvent

# Import from absolute path to handle direct script execution
try:
    from .config_manager import get_mv_maker_config
    from .worker_threads import TranscriptionWorker, BatchProcessingWorker
    from .dialogs import SettingsDialog, ProgressDialog, BatchSelectionDialog
    from .utils import safe_print, get_available_languages, sanitize_filename
    from .audio_extractor import AudioExtractor
    from .live_preview_widget import LivePreviewWidget
    from .color_wheel_widget import ColorWheelWidget
    from .font_manager import get_font_manager
except ImportError:
    # Fallback for direct script execution
    from mv_maker.config_manager import get_mv_maker_config
    from mv_maker.worker_threads import TranscriptionWorker, BatchProcessingWorker
    from mv_maker.dialogs import SettingsDialog, ProgressDialog, BatchSelectionDialog
    from mv_maker.utils import safe_print, get_available_languages, sanitize_filename
    from mv_maker.audio_extractor import AudioExtractor
    from mv_maker.live_preview_widget import LivePreviewWidget
    from mv_maker.color_wheel_widget import ColorWheelWidget
    from mv_maker.font_manager import get_font_manager

class MVMaker(QMainWindow):
    """Main application window for MV Maker."""
    
    def __init__(self):
        """Initialize main application."""
        super().__init__()
        self.config = get_mv_maker_config()
        self.current_video = None
        self.worker = None
        
        self.setWindowTitle("MV Maker - Bedrot Productions")
        self.setMinimumSize(1200, 800)
        
        # Initialize font manager
        self.font_manager = get_font_manager()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        self.init_ui()
        self.load_last_paths()
        
        # Center window
        self.center_window()
    
    def init_ui(self):
        """Initialize user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set style for drag and drop visual feedback
        central_widget.setStyleSheet("""
            QWidget {
                border: 2px dashed transparent;
            }
            QWidget[dragActive="true"] {
                border: 2px dashed #007ACC;
                background-color: rgba(0, 122, 204, 0.1);
            }
        """)
        
        # Main layout - horizontal split
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Preview
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview title
        preview_title = QLabel("Live Caption Preview")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_font = QFont()
        preview_font.setPointSize(12)
        preview_font.setBold(True)
        preview_title.setFont(preview_font)
        left_layout.addWidget(preview_title)
        
        # Live preview widget
        self.preview_widget = LivePreviewWidget()
        self.preview_widget.position_clicked.connect(self.on_preview_position_clicked)
        left_layout.addWidget(self.preview_widget)
        
        # Preview controls
        preview_controls = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.preview_widget.play_pause)
        preview_controls.addWidget(self.play_button)
        
        self.preview_slider = QSlider(Qt.Horizontal)
        self.preview_slider.setEnabled(False)
        preview_controls.addWidget(self.preview_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        preview_controls.addWidget(self.time_label)
        
        left_layout.addLayout(preview_controls)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right panel - Controls
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Title for right panel
        title_label = QLabel("Caption Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(title_label)
        
        # File selection group
        file_group = QGroupBox("Media Selection")
        file_layout = QVBoxLayout()
        
        # Video path
        video_layout = QHBoxLayout()
        video_layout.addWidget(QLabel("Media File:"))
        
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select a video or audio file... (or drag & drop here)")
        self.video_path_edit.textChanged.connect(self.on_video_path_changed)
        video_layout.addWidget(self.video_path_edit)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.browse_button.clicked.connect(self.browse_video)
        video_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(video_layout)
        
        # Output path
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Path:"))
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Output directory for caption files (will be auto-generated)...")
        output_layout.addWidget(self.output_path_edit)
        
        self.output_browse_button = QPushButton("Browse")
        self.output_browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.output_browse_button.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_browse_button)
        
        file_layout.addLayout(output_layout)
        
        file_group.setLayout(file_layout)
        right_layout.addWidget(file_group)
        
        # Create tab widget for settings
        settings_tabs = QTabWidget()
        
        # Basic settings tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        
        # Model and language row
        model_lang_layout = QHBoxLayout()
        
        # Model selection
        model_lang_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
        self.model_combo.setCurrentText(self.config.get('whisper_model', 'base'))
        self.model_combo.setToolTip(
            "Model size affects accuracy and speed:\n"
            "- tiny: Fastest, least accurate\n"
            "- base: Good balance\n"
            "- small: Better accuracy\n"
            "- medium: High accuracy\n"
            "- large: Best accuracy, slowest"
        )
        model_lang_layout.addWidget(self.model_combo)
        
        model_lang_layout.addSpacing(20)
        
        # Language selection
        model_lang_layout.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        languages = get_available_languages()
        for code, name in languages.items():
            self.language_combo.addItem(name, code)
        self.language_combo.setCurrentText("Auto-detect")
        model_lang_layout.addWidget(self.language_combo)
        
        model_lang_layout.addStretch()
        basic_layout.addLayout(model_lang_layout)
        
        # Font selection with real-time preview
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        
        self.font_combo = QComboBox()
        # Get available fonts from font manager
        available_fonts = self.font_manager.get_font_list()
        for font_key, display_name in available_fonts:
            self.font_combo.addItem(display_name, font_key)
        
        # Set current font
        current_font = self.config.get('font_family', 'arial')
        for i in range(self.font_combo.count()):
            if self.font_combo.itemData(i) == current_font:
                self.font_combo.setCurrentIndex(i)
                break
        
        # Connect for real-time updates
        self.font_combo.currentIndexChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.font_combo)
        
        # Font size
        font_layout.addSpacing(20)
        font_layout.addWidget(QLabel("Size:"))
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(12, 72)
        self.font_size_slider.setValue(self.config.get('font_size', 24))
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        font_layout.addWidget(self.font_size_slider)
        
        self.font_size_label = QLabel(str(self.font_size_slider.value()) + "px")
        self.font_size_label.setMinimumWidth(40)
        font_layout.addWidget(self.font_size_label)
        
        font_layout.addStretch()
        basic_layout.addLayout(font_layout)
        
        # Color selection with color wheel
        color_group = QGroupBox("Caption Colors")
        color_layout = QHBoxLayout()
        
        # Font color
        font_color_layout = QVBoxLayout()
        font_color_layout.addWidget(QLabel("Font Color:"))
        self.font_color_button = QPushButton()
        self.font_color_button.setFixedSize(60, 30)
        font_color = self.config.get('font_color', '#FFFFFF')
        self.font_color_button.setStyleSheet(f"background-color: {font_color}; border: 1px solid #ccc;")
        self.font_color_button.clicked.connect(self.show_font_color_picker)
        font_color_layout.addWidget(self.font_color_button)
        font_color_layout.addStretch()
        color_layout.addLayout(font_color_layout)
        
        # Background color
        bg_color_layout = QVBoxLayout()
        bg_color_layout.addWidget(QLabel("Background:"))
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(60, 30)
        bg_color = self.config.get('background_color', '#000000')
        self.bg_color_button.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #ccc;")
        self.bg_color_button.clicked.connect(self.show_bg_color_picker)
        bg_color_layout.addWidget(self.bg_color_button)
        bg_color_layout.addStretch()
        color_layout.addLayout(bg_color_layout)
        
        # Background opacity
        opacity_layout = QVBoxLayout()
        opacity_layout.addWidget(QLabel("BG Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.config.get('background_opacity', 0.7) * 100))
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        opacity_layout.addWidget(self.opacity_label)
        color_layout.addLayout(opacity_layout)
        
        color_layout.addStretch()
        color_group.setLayout(color_layout)
        basic_layout.addWidget(color_group)
        
        basic_layout.addStretch()
        basic_tab.setLayout(basic_layout)
        settings_tabs.addTab(basic_tab, "Basic")
        
        # Advanced settings tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout()
        
        # Position controls
        position_group = QGroupBox("Caption Position")
        position_layout = QVBoxLayout()
        
        # Position sliders
        pos_x_layout = QHBoxLayout()
        pos_x_layout.addWidget(QLabel("X Position:"))
        self.pos_x_slider = QSlider(Qt.Horizontal)
        self.pos_x_slider.setRange(0, 100)
        self.pos_x_slider.setValue(self.config.get('position_x', 50))
        self.pos_x_slider.valueChanged.connect(self.on_position_changed)
        pos_x_layout.addWidget(self.pos_x_slider)
        self.pos_x_label = QLabel(f"{self.pos_x_slider.value()}%")
        self.pos_x_label.setMinimumWidth(40)
        pos_x_layout.addWidget(self.pos_x_label)
        position_layout.addLayout(pos_x_layout)
        
        pos_y_layout = QHBoxLayout()
        pos_y_layout.addWidget(QLabel("Y Position:"))
        self.pos_y_slider = QSlider(Qt.Horizontal)
        self.pos_y_slider.setRange(0, 100)
        self.pos_y_slider.setValue(self.config.get('position_y', 85))
        self.pos_y_slider.valueChanged.connect(self.on_position_changed)
        pos_y_layout.addWidget(self.pos_y_slider)
        self.pos_y_label = QLabel(f"{self.pos_y_slider.value()}%")
        self.pos_y_label.setMinimumWidth(40)
        pos_y_layout.addWidget(self.pos_y_label)
        position_layout.addLayout(pos_y_layout)
        
        # Alignment controls
        align_layout = QHBoxLayout()
        align_layout.addWidget(QLabel("Alignment:"))
        
        self.align_group = QButtonGroup()
        self.align_left = QRadioButton("Left")
        self.align_center = QRadioButton("Center")
        self.align_right = QRadioButton("Right")
        
        self.align_group.addButton(self.align_left)
        self.align_group.addButton(self.align_center)
        self.align_group.addButton(self.align_right)
        
        # Set default alignment
        text_align = self.config.get('text_align', 'center')
        if text_align == 'left':
            self.align_left.setChecked(True)
        elif text_align == 'right':
            self.align_right.setChecked(True)
        else:
            self.align_center.setChecked(True)
        
        self.align_group.buttonClicked.connect(self.on_alignment_changed)
        
        align_layout.addWidget(self.align_left)
        align_layout.addWidget(self.align_center)
        align_layout.addWidget(self.align_right)
        align_layout.addStretch()
        position_layout.addLayout(align_layout)
        
        position_group.setLayout(position_layout)
        advanced_layout.addWidget(position_group)
        
        # Audio-to-video settings
        audio_group = QGroupBox("Audio-to-Video Settings")
        audio_layout = QVBoxLayout()
        
        # Aspect ratio
        aspect_layout = QHBoxLayout()
        aspect_layout.addWidget(QLabel("Aspect Ratio:"))
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(['16:9', '9:16', '1:1', '4:3'])
        self.aspect_combo.setCurrentText(self.config.get('aspect_ratio', '16:9'))
        self.aspect_combo.currentTextChanged.connect(self.on_aspect_changed)
        aspect_layout.addWidget(self.aspect_combo)
        
        # Resolution
        aspect_layout.addSpacing(20)
        aspect_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['720p', '1080p', '4k'])
        self.resolution_combo.setCurrentText(self.config.get('video_resolution', '1080p'))
        aspect_layout.addWidget(self.resolution_combo)
        
        aspect_layout.addStretch()
        audio_layout.addLayout(aspect_layout)
        
        # Background type
        bg_type_layout = QHBoxLayout()
        bg_type_layout.addWidget(QLabel("Background:"))
        
        self.bg_type_group = QButtonGroup()
        self.bg_solid = QRadioButton("Solid Color")
        self.bg_gradient = QRadioButton("Gradient")
        self.bg_image = QRadioButton("Image")
        
        self.bg_type_group.addButton(self.bg_solid)
        self.bg_type_group.addButton(self.bg_gradient)
        self.bg_type_group.addButton(self.bg_image)
        
        bg_type = self.config.get('background_type', 'solid')
        if bg_type == 'gradient':
            self.bg_gradient.setChecked(True)
        elif bg_type == 'image':
            self.bg_image.setChecked(True)
        else:
            self.bg_solid.setChecked(True)
        
        bg_type_layout.addWidget(self.bg_solid)
        bg_type_layout.addWidget(self.bg_gradient)
        bg_type_layout.addWidget(self.bg_image)
        bg_type_layout.addStretch()
        audio_layout.addLayout(bg_type_layout)
        
        audio_group.setLayout(audio_layout)
        advanced_layout.addWidget(audio_group)
        
        # Settings button
        self.settings_button = QPushButton("More Settings...")
        self.settings_button.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.settings_button.clicked.connect(self.show_settings)
        advanced_layout.addWidget(self.settings_button)
        
        advanced_layout.addStretch()
        advanced_tab.setLayout(advanced_layout)
        settings_tabs.addTab(advanced_tab, "Advanced")
        
        right_layout.addWidget(settings_tabs)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # Set splitter sizes (60% preview, 40% controls)
        splitter.setSizes([700, 500])
        
        main_layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.process_button = QPushButton("Generate Captions")
        self.process_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.process_button.clicked.connect(self.process_video)
        self.process_button.setEnabled(False)
        self.process_button.setMinimumHeight(40)
        button_layout.addWidget(self.process_button)
        
        self.batch_button = QPushButton("Batch Process")
        self.batch_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.batch_button.clicked.connect(self.batch_process)
        self.batch_button.setMinimumHeight(40)
        button_layout.addWidget(self.batch_button)
        
        main_layout.addLayout(button_layout)
        
        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText(
            "Processing results will appear here...\n\n"
            "💡 Tip: You can drag & drop media files directly onto this window!\n\n"
            "Generated caption files will be listed with their paths."
        )
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        central_widget.setLayout(main_layout)
    
    def center_window(self):
        """Center window on screen."""
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def browse_video(self):
        """Browse for video or audio file."""
        file_filter = "Media Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma);;Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v);;Audio Files (*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            self.config.get('last_video_path', ''),
            file_filter
        )
        
        if file_path:
            self.video_path_edit.setText(file_path)
            self.config.set('last_video_path', os.path.dirname(file_path))
            
            # Auto-generate output path
            base_name = Path(file_path).stem
            output_base = os.path.join(
                os.path.dirname(file_path),
                sanitize_filename(base_name)
            )
            self.output_path_edit.setText(output_base)
    
    def browse_output(self):
        """Browse for output directory."""
        current_path = self.output_path_edit.text()
        if current_path:
            if os.path.isfile(current_path):
                default_dir = os.path.dirname(current_path)
            elif os.path.isdir(current_path):
                default_dir = current_path
            else:
                default_dir = os.path.dirname(current_path) if current_path else ''
        else:
            default_dir = self.config.get('last_output_path', '')
        
        # Use directory selection dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory for Caption Files",
            default_dir
        )
        
        if directory:
            # If we have a video file selected, create a base name from it
            video_path = self.video_path_edit.text()
            if video_path and os.path.exists(video_path):
                base_name = Path(video_path).stem
                output_base = os.path.join(directory, sanitize_filename(base_name))
                self.output_path_edit.setText(output_base)
            else:
                # Just set the directory
                self.output_path_edit.setText(directory)
            
            self.config.set('last_output_path', directory)
    
    def on_video_path_changed(self, text):
        """Handle video path change."""
        if text and os.path.exists(text):
            self.process_button.setEnabled(True)
            
            # Load media into preview
            self.preview_widget.load_media(text)
            
            # Check if file has audio
            extractor = AudioExtractor()
            file_ext = Path(text).suffix.lower()
            
            if extractor.is_audio_file(text):
                self.statusBar().showMessage("Audio file loaded - ready to process")
                # Initialize audio preview with current settings
                self._update_audio_preview()
            elif extractor.is_video_file(text):
                if extractor.has_audio_stream(text):
                    self.statusBar().showMessage("Video file loaded - ready to process")
                else:
                    self.statusBar().showMessage("Warning: Video may not have audio track")
            else:
                self.statusBar().showMessage("Unsupported file format")
                self.process_button.setEnabled(False)
        else:
            self.process_button.setEnabled(False)
            self.statusBar().showMessage("Select a media file")
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # Reload config
            self.config = get_mv_maker_config()
            # Update UI with new settings
            self.model_combo.setCurrentText(self.config.get('whisper_model', 'base'))
            
            lang_code = self.config.get('language', 'auto')
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == lang_code:
                    self.language_combo.setCurrentIndex(i)
                    break
    
    def process_video(self):
        """Process single video file."""
        video_path = self.video_path_edit.text()
        output_path = self.output_path_edit.text()
        
        if not video_path or not os.path.exists(video_path):
            QMessageBox.warning(self, "Error", "Please select a valid video file")
            return
        
        if not output_path:
            QMessageBox.warning(self, "Error", "Please specify an output path")
            return
        
        # Clear previous results
        self.results_text.clear()
        
        # Create progress dialog
        progress_dialog = ProgressDialog("Processing Video", self)
        progress_dialog.show()
        
        # Get output formats including MP4 overlay
        output_formats = self.config.get('output_formats', ['srt', 'vtt']).copy()
        # Convert 'mp4' to 'mp4_overlay' for the worker thread
        if 'mp4' in output_formats:
            output_formats.remove('mp4')
            # Only add MP4 overlay for video files (not audio files)
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
            if any(video_path.lower().endswith(ext) for ext in video_extensions):
                output_formats.append('mp4_overlay')
        
        # Create worker thread
        self.worker = TranscriptionWorker()
        self.worker.setup(
            video_path=video_path,
            output_path=output_path,
            model_size=self.model_combo.currentText(),
            language=self.language_combo.currentData(),
            output_formats=output_formats,
            device=self.config.get('device', 'auto'),
            font_family=self.font_combo.currentData(),
            config=self.config
        )
        
        # Connect signals
        self.worker.progress_updated.connect(progress_dialog.update_progress)
        self.worker.operation_completed.connect(self.on_process_completed)
        self.worker.error_occurred.connect(self.on_process_error)
        
        progress_dialog.cancelled.connect(self.worker.cancel)
        
        # Start processing
        self.worker.start()
        
        # Save config
        self.config.set('whisper_model', self.model_combo.currentText())
        self.config.set('language', self.language_combo.currentData())
        self.config.set('font_family', self.font_combo.currentData())
        self.config.save_config()
    
    @pyqtSlot(dict)
    def on_process_completed(self, result):
        """Handle processing completion."""
        # Find and close progress dialog
        for widget in self.findChildren(ProgressDialog):
            widget.set_completed()
        
        # Display results
        self.results_text.append("✅ Caption generation completed!\n")
        self.results_text.append(f"Video: {Path(result['video_path']).name}")
        self.results_text.append(f"Language: {result['language']}")
        self.results_text.append(f"Captions generated: {result['caption_count']}\n")
        
        # List output files
        self.results_text.append("📄 Generated files:")
        for fmt, path in result['output_files'].items():
            if fmt == 'mp4_overlay':
                display_name = "MP4 (with captions)"
            elif fmt == 'mp4_overlay_error':
                continue  # Skip error entries
            else:
                display_name = fmt.upper()
            self.results_text.append(f"  • {display_name}: {path}")
        
        # Show statistics
        stats = result['statistics']
        self.results_text.append(f"\n📊 Statistics:")
        self.results_text.append(f"  • Total duration: {stats['total_duration']:.1f} seconds")
        self.results_text.append(f"  • Average caption duration: {stats['average_duration']:.1f} seconds")
        self.results_text.append(f"  • Total words: {stats['total_words']}")
        
        self.results_text.append("\n" + "="*50 + "\n")
        
        self.statusBar().showMessage("Processing completed successfully!")
        
        # Show success message
        QMessageBox.information(
            self,
            "Success",
            f"Captions generated successfully!\n\n"
            f"{len(result['output_files'])} files created."
        )
    
    @pyqtSlot(str)
    def on_process_error(self, error_message):
        """Handle processing error."""
        # Find and close progress dialog
        for widget in self.findChildren(ProgressDialog):
            widget.close()
        
        self.results_text.append(f"❌ Error: {error_message}\n")
        self.statusBar().showMessage("Processing failed")
        
        QMessageBox.critical(
            self,
            "Processing Error",
            f"An error occurred during processing:\n\n{error_message}"
        )
    
    def batch_process(self):
        """Process multiple video files."""
        # Get directory with video files
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with Videos",
            self.config.get('last_video_path', '')
        )
        
        if not directory:
            return
        
        # Find all video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        video_files = []
        
        for file in Path(directory).iterdir():
            if file.suffix.lower() in video_extensions:
                video_files.append(str(file))
        
        if not video_files:
            QMessageBox.information(
                self,
                "No Videos Found",
                "No video files found in the selected directory."
            )
            return
        
        # Show selection dialog
        selection_dialog = BatchSelectionDialog(video_files, self)
        if selection_dialog.exec_():
            selected_files = selection_dialog.get_selected_files()
            
            if not selected_files:
                return
            
            # Clear results
            self.results_text.clear()
            self.results_text.append(f"Starting batch processing of {len(selected_files)} videos...\n")
            
            # Create progress dialog
            progress_dialog = ProgressDialog("Batch Processing", self)
            progress_dialog.show()
            
            # Create batch worker
            batch_worker = BatchProcessingWorker()
            batch_worker.setup(
                video_files=selected_files,
                model_size=self.model_combo.currentText(),
                language=self.language_combo.currentData(),
                output_formats=self.config.get('output_formats', ['srt', 'vtt']),
                device=self.config.get('device', 'auto')
            )
            
            # Connect signals
            batch_worker.progress_updated.connect(progress_dialog.update_progress)
            batch_worker.file_completed.connect(self.on_batch_file_completed)
            batch_worker.batch_completed.connect(self.on_batch_completed)
            
            progress_dialog.cancelled.connect(batch_worker.cancel)
            
            # Start processing
            batch_worker.start()
    
    @pyqtSlot(str, bool, str)
    def on_batch_file_completed(self, file_path, success, message):
        """Handle completion of single file in batch."""
        status = "✅" if success else "❌"
        self.results_text.append(f"{status} {Path(file_path).name}: {message}")
    
    @pyqtSlot(int, int)
    def on_batch_completed(self, successful, failed):
        """Handle batch processing completion."""
        # Find and close progress dialog
        for widget in self.findChildren(ProgressDialog):
            widget.set_completed()
        
        self.results_text.append(f"\n{'='*50}")
        self.results_text.append(f"Batch processing completed:")
        self.results_text.append(f"  • Successful: {successful}")
        self.results_text.append(f"  • Failed: {failed}")
        self.results_text.append(f"  • Total: {successful + failed}")
        
        QMessageBox.information(
            self,
            "Batch Processing Complete",
            f"Batch processing completed!\n\n"
            f"Successful: {successful}\n"
            f"Failed: {failed}"
        )
    
    def load_last_paths(self):
        """Load last used paths from config."""
        last_video = self.config.get('last_video_path', '')
        if last_video and os.path.exists(last_video):
            self.video_path_edit.setText(last_video)
        
        last_output = self.config.get('last_output_path', '')
        if last_output and os.path.exists(os.path.dirname(last_output)):
            self.output_path_edit.setText(last_output)
    
    # Real-time update event handlers
    def on_font_changed(self, index):
        """Handle font selection change."""
        font_key = self.font_combo.itemData(index)
        if font_key:
            self.preview_widget.update_caption_style({'font_family': font_key})
            self.config.set('font_family', font_key)
    
    def on_font_size_changed(self, value):
        """Handle font size change."""
        self.font_size_label.setText(f"{value}px")
        self.preview_widget.update_caption_style({'font_size': value})
        self.config.set('font_size', value)
    
    def on_opacity_changed(self, value):
        """Handle opacity change."""
        self.opacity_label.setText(f"{value}%")
        opacity = value / 100.0
        self.preview_widget.update_caption_style({'background_opacity': opacity})
        self.config.set('background_opacity', opacity)
    
    def on_position_changed(self):
        """Handle position slider changes."""
        x = self.pos_x_slider.value()
        y = self.pos_y_slider.value()
        self.pos_x_label.setText(f"{x}%")
        self.pos_y_label.setText(f"{y}%")
        self.preview_widget.update_caption_position(x, y)
        self.config.set('position_x', x)
        self.config.set('position_y', y)
    
    def on_alignment_changed(self, button):
        """Handle alignment change."""
        if button == self.align_left:
            align = 'left'
        elif button == self.align_right:
            align = 'right'
        else:
            align = 'center'
        
        self.preview_widget.update_caption_alignment(align, 'bottom')
        self.config.set('text_align', align)
    
    def on_aspect_changed(self, aspect):
        """Handle aspect ratio change."""
        self.config.set('aspect_ratio', aspect)
        # Update preview if audio file
        if hasattr(self, 'preview_widget') and self.preview_widget.is_audio_only:
            self._update_audio_preview()
    
    def on_preview_position_clicked(self, x_percent, y_percent):
        """Handle click on preview to set position."""
        self.pos_x_slider.setValue(int(x_percent))
        self.pos_y_slider.setValue(int(y_percent))
        self.on_position_changed()
    
    def show_font_color_picker(self):
        """Show color picker for font color."""
        # Create color wheel dialog
        dialog = QWidget()
        dialog.setWindowTitle("Select Font Color")
        dialog.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout()
        color_wheel = ColorWheelWidget()
        color_wheel.set_color(self.config.get('font_color', '#FFFFFF'))
        color_wheel.colorChanged.connect(lambda color: self._update_font_color(color))
        
        layout.addWidget(color_wheel)
        
        # OK/Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.close)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.close)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.resize(350, 500)
        dialog.show()
    
    def show_bg_color_picker(self):
        """Show color picker for background color."""
        # Create color wheel dialog
        dialog = QWidget()
        dialog.setWindowTitle("Select Background Color")
        dialog.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout()
        color_wheel = ColorWheelWidget()
        color_wheel.set_color(self.config.get('background_color', '#000000'))
        color_wheel.colorChanged.connect(lambda color: self._update_bg_color(color))
        
        layout.addWidget(color_wheel)
        
        # OK/Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.close)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.close)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.resize(350, 500)
        dialog.show()
    
    def _update_font_color(self, color):
        """Update font color from color picker."""
        self.font_color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
        self.preview_widget.update_caption_style({'font_color': color})
        self.config.set('font_color', color)
    
    def _update_bg_color(self, color):
        """Update background color from color picker."""
        self.bg_color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
        self.preview_widget.update_caption_style({'background_color': color})
        self.config.set('background_color', color)
    
    def _update_audio_preview(self):
        """Update preview for audio files with selected background."""
        bg_type = self.config.get('background_type', 'solid')
        if bg_type == 'solid':
            bg_value = self.config.get('background_color', '#000000')
        elif bg_type == 'gradient':
            # For gradient, combine two colors
            bg_value = f"{self.config.get('background_color', '#000000')},{self.config.get('font_color', '#FFFFFF')}"
        else:
            bg_value = ''
        
        self.preview_widget.set_background_for_audio(bg_type, bg_value)
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Save last paths
        self.config['last_video_path'] = self.video_path_edit.text()
        self.config['last_output_path'] = self.output_path_edit.text()
        
        # Cancel any running worker
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)  # Wait up to 3 seconds
        
        event.accept()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files are supported
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Check if file has supported extension
                    try:
                        from .audio_extractor import AudioExtractor
                    except ImportError:
                        from mv_maker.audio_extractor import AudioExtractor
                    
                    extractor = AudioExtractor()
                    if extractor.is_supported_format(file_path):
                        event.acceptProposedAction()
                        # Add visual feedback
                        self.centralWidget().setProperty("dragActive", True)
                        self.centralWidget().style().unpolish(self.centralWidget())
                        self.centralWidget().style().polish(self.centralWidget())
                        return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        # Remove visual feedback
        self.centralWidget().setProperty("dragActive", False)
        self.centralWidget().style().unpolish(self.centralWidget())
        self.centralWidget().style().polish(self.centralWidget())
        event.accept()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        # Remove visual feedback first
        self.centralWidget().setProperty("dragActive", False)
        self.centralWidget().style().unpolish(self.centralWidget())
        self.centralWidget().style().polish(self.centralWidget())
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            
            # Get the first supported file
            try:
                from .audio_extractor import AudioExtractor
            except ImportError:
                from mv_maker.audio_extractor import AudioExtractor
            
            extractor = AudioExtractor()
            
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if extractor.is_supported_format(file_path):
                        # Set the file path
                        self.video_path_edit.setText(file_path)
                        
                        # Auto-set output path if not already set
                        if not self.output_path_edit.text():
                            from pathlib import Path
                            base_name = Path(file_path).stem
                            output_dir = str(Path(file_path).parent)
                            output_base = os.path.join(output_dir, sanitize_filename(base_name))
                            self.output_path_edit.setText(output_base)
                        
                        # Show success message
                        from pathlib import Path
                        file_name = Path(file_path).name
                        file_type = "audio" if extractor.is_audio_file(file_path) else "video"
                        self.results_text.append(f"✓ Dropped {file_type} file: {file_name}")
                        
                        event.acceptProposedAction()
                        return
            
            # If we get here, no supported files were found
            QMessageBox.warning(
                self,
                "Unsupported File",
                "Please drop a supported video or audio file.\n\n"
                "Supported formats:\n"
                "• Video: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm, .m4v\n"
                "• Audio: .mp3, .wav, .flac, .m4a, .aac, .ogg, .wma"
            )
        
        event.ignore()


def main():
    """Main entry point for standalone execution."""
    app = QApplication(sys.argv)
    app.setApplicationName("MV Maker")
    app.setOrganizationName("Bedrot Productions")
    
    window = MVMaker()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()