"""Dialog windows for MV Maker."""

import sys
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QColorDialog,
    QGroupBox, QFormLayout, QDialogButtonBox, QTextEdit,
    QProgressBar, QListWidget, QCheckBox, QSlider, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette

# Import from absolute path to handle direct script execution
try:
    from .utils import get_available_languages
    from .config_manager import get_mv_maker_config
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import get_available_languages
    from mv_maker.config_manager import get_mv_maker_config

class SettingsDialog(QDialog):
    """Settings dialog for caption generator configuration."""
    
    def __init__(self, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)
        self.config = get_mv_maker_config()
        self.setWindowTitle("Caption Generator Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        
        # Transcription Service Settings
        service_group = QGroupBox("Transcription Service")
        service_layout = QFormLayout()
        
        self.service_combo = QComboBox()
        self.service_combo.addItems(['elevenlabs', 'whisper'])
        self.service_combo.currentTextChanged.connect(self.on_service_changed)
        service_layout.addRow("Service:", self.service_combo)
        
        # ElevenLabs settings
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter your ElevenLabs API key")
        service_layout.addRow("ElevenLabs API Key:", self.api_key_edit)
        
        self.el_model_combo = QComboBox()
        self.el_model_combo.addItems(['scribe_v1', 'scribe_v1_experimental'])
        service_layout.addRow("ElevenLabs Model:", self.el_model_combo)
        
        # Whisper settings
        self.model_combo = QComboBox()
        self.model_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
        service_layout.addRow("Whisper Model:", self.model_combo)
        
        self.device_combo = QComboBox()
        self.device_combo.addItems(['auto', 'cpu', 'cuda'])
        service_layout.addRow("Device:", self.device_combo)
        
        service_group.setLayout(service_layout)
        layout.addWidget(service_group)
        
        # Speaker diarization settings
        speaker_group = QGroupBox("Speaker Settings")
        speaker_layout = QFormLayout()
        
        self.diarize_check = QCheckBox("Enable speaker diarization")
        speaker_layout.addRow(self.diarize_check)
        
        self.audio_events_check = QCheckBox("Tag audio events (laughter, applause, etc.)")
        speaker_layout.addRow(self.audio_events_check)
        
        speaker_group.setLayout(speaker_layout)
        layout.addWidget(speaker_group)
        
        # Language Settings
        lang_group = QGroupBox("Language Settings")
        lang_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        languages = get_available_languages()
        for code, name in languages.items():
            self.language_combo.addItem(name, code)
        lang_layout.addRow("Language:", self.language_combo)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Caption Settings
        caption_group = QGroupBox("Caption Settings")
        caption_layout = QFormLayout()
        
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(20, 80)
        caption_layout.addRow("Max Characters per Line:", self.max_length_spin)
        
        self.max_duration_spin = QDoubleSpinBox()
        self.max_duration_spin.setRange(1.0, 15.0)
        self.max_duration_spin.setSingleStep(0.5)
        caption_layout.addRow("Max Duration (seconds):", self.max_duration_spin)
        
        caption_group.setLayout(caption_layout)
        layout.addWidget(caption_group)
        
        # Styling Settings
        style_group = QGroupBox("Caption Styling")
        style_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 48)
        style_layout.addRow("Font Size:", self.font_size_spin)
        
        # Font color button
        self.font_color_button = QPushButton()
        self.font_color_button.clicked.connect(self.choose_font_color)
        style_layout.addRow("Font Color:", self.font_color_button)
        
        # Background color button
        self.bg_color_button = QPushButton()
        self.bg_color_button.clicked.connect(self.choose_bg_color)
        style_layout.addRow("Background Color:", self.bg_color_button)
        
        # Background opacity
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.opacity_label = QLabel()
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        style_layout.addRow("Background Opacity:", opacity_layout)
        
        # Position
        self.position_combo = QComboBox()
        self.position_combo.addItems(['bottom', 'top', 'middle'])
        style_layout.addRow("Position:", self.position_combo)
        
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)
        
        # Output Settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        self.srt_check = QCheckBox("SRT Format")
        self.vtt_check = QCheckBox("WebVTT Format")
        self.json_check = QCheckBox("JSON Format (for debugging)")
        self.preview_check = QCheckBox("Generate HTML Preview")
        self.mp4_check = QCheckBox("MP4 with Burned-in Captions")
        
        output_layout.addWidget(self.srt_check)
        output_layout.addWidget(self.vtt_check)
        output_layout.addWidget(self.json_check)
        output_layout.addWidget(self.preview_check)
        output_layout.addWidget(self.mp4_check)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current settings from config."""
        # Service settings
        self.service_combo.setCurrentText(self.config.get('transcription_service', 'elevenlabs'))
        self.api_key_edit.setText(self.config.get('elevenlabs_api_key', ''))
        self.el_model_combo.setCurrentText(self.config.get('elevenlabs_model', 'scribe_v1'))
        self.model_combo.setCurrentText(self.config.get('whisper_model', 'base'))
        self.device_combo.setCurrentText(self.config.get('device', 'auto'))
        
        # Speaker settings
        self.diarize_check.setChecked(self.config.get('diarize_speakers', True))
        self.audio_events_check.setChecked(self.config.get('audio_events', False))
        
        # Set language
        lang_code = self.config.get('language', 'auto')
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == lang_code:
                self.language_combo.setCurrentIndex(i)
                break
        
        self.max_length_spin.setValue(self.config.get('caption_max_length', 42))
        self.max_duration_spin.setValue(self.config.get('caption_max_duration', 7.0))
        
        self.font_size_spin.setValue(self.config.get('font_size', 24))
        
        # Set colors
        self.font_color = self.config.get('font_color', '#FFFFFF')
        self.update_color_button(self.font_color_button, self.font_color)
        
        self.bg_color = self.config.get('background_color', '#000000')
        self.update_color_button(self.bg_color_button, self.bg_color)
        
        opacity = int(self.config.get('background_opacity', 0.7) * 100)
        self.opacity_slider.setValue(opacity)
        
        self.position_combo.setCurrentText(self.config.get('position', 'bottom'))
        
        # Output formats
        formats = self.config.get('output_formats', ['srt', 'vtt'])
        self.srt_check.setChecked('srt' in formats)
        self.vtt_check.setChecked('vtt' in formats)
        self.json_check.setChecked('json' in formats)
        self.preview_check.setChecked('preview' in formats)
        self.mp4_check.setChecked('mp4' in formats)
        
        # Update UI visibility
        self.on_service_changed(self.service_combo.currentText())
    
    def save_settings(self):
        """Save settings to config."""
        updates = {
            'transcription_service': self.service_combo.currentText(),
            'elevenlabs_api_key': self.api_key_edit.text(),
            'elevenlabs_model': self.el_model_combo.currentText(),
            'whisper_model': self.model_combo.currentText(),
            'device': self.device_combo.currentText(),
            'diarize_speakers': self.diarize_check.isChecked(),
            'audio_events': self.audio_events_check.isChecked(),
            'language': self.language_combo.currentData(),
            'caption_max_length': self.max_length_spin.value(),
            'caption_max_duration': self.max_duration_spin.value(),
            'font_size': self.font_size_spin.value(),
            'font_color': self.font_color,
            'background_color': self.bg_color,
            'background_opacity': self.opacity_slider.value() / 100.0,
            'position': self.position_combo.currentText()
        }
        
        # Output formats
        formats = []
        if self.srt_check.isChecked():
            formats.append('srt')
        if self.vtt_check.isChecked():
            formats.append('vtt')
        if self.json_check.isChecked():
            formats.append('json')
        if self.preview_check.isChecked():
            formats.append('preview')
        if self.mp4_check.isChecked():
            formats.append('mp4')
        
        updates['output_formats'] = formats
        
        self.config.update(updates)
    
    def choose_font_color(self):
        """Open color picker for font color."""
        color = QColorDialog.getColor(QColor(self.font_color), self)
        if color.isValid():
            self.font_color = color.name()
            self.update_color_button(self.font_color_button, self.font_color)
    
    def choose_bg_color(self):
        """Open color picker for background color."""
        color = QColorDialog.getColor(QColor(self.bg_color), self)
        if color.isValid():
            self.bg_color = color.name()
            self.update_color_button(self.bg_color_button, self.bg_color)
    
    def update_color_button(self, button, color):
        """Update button to show selected color."""
        button.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
        button.setText(color)
    
    def update_opacity_label(self, value):
        """Update opacity label."""
        self.opacity_label.setText(f"{value}%")
    
    def on_service_changed(self, service):
        """Handle service selection change."""
        is_elevenlabs = service == 'elevenlabs'
        
        # Show/hide relevant fields
        self.api_key_edit.setVisible(is_elevenlabs)
        self.el_model_combo.setVisible(is_elevenlabs)
        self.model_combo.setVisible(not is_elevenlabs)
        self.device_combo.setVisible(not is_elevenlabs)
        
        # Update labels
        for i in range(self.findChild(QFormLayout).rowCount()):
            label_item = self.findChild(QFormLayout).itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget():
                label_text = label_item.widget().text()
                if "ElevenLabs" in label_text:
                    label_item.widget().setVisible(is_elevenlabs)
                elif "Whisper" in label_text or "Device:" in label_text:
                    label_item.widget().setVisible(not is_elevenlabs)
    
    def accept(self):
        """Accept and save settings."""
        # Validate ElevenLabs API key if selected
        if self.service_combo.currentText() == 'elevenlabs' and not self.api_key_edit.text().strip():
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please enter your ElevenLabs API key to use the ElevenLabs service.\n\n"
                "You can get an API key from https://elevenlabs.io"
            )
            return
        
        self.save_settings()
        super().accept()


class ProgressDialog(QDialog):
    """Progress dialog for long-running operations."""
    
    cancelled = pyqtSignal()
    
    def __init__(self, title="Processing", parent=None):
        """Initialize progress dialog."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        layout.addWidget(self.details_text)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
    
    def update_progress(self, current, total, message):
        """Update progress display."""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        self.add_detail(f"[{percentage}%] {message}")
    
    def add_detail(self, text):
        """Add detail text to the log."""
        self.details_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling...")
        self.cancelled.emit()
    
    def set_completed(self):
        """Set dialog to completed state."""
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)


class BatchSelectionDialog(QDialog):
    """Dialog for selecting multiple video files for batch processing."""
    
    def __init__(self, video_files, parent=None):
        """Initialize batch selection dialog."""
        super().__init__(parent)
        self.setWindowTitle("Select Videos for Batch Processing")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        self.video_files = video_files
        self.selected_files = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Select the videos you want to process. "
            "Caption files will be created in the same location as each video."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        
        for file_path in self.video_files:
            self.file_list.addItem(file_path)
        
        layout.addWidget(self.file_list)
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_none_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def select_all(self):
        """Select all items."""
        self.file_list.selectAll()
    
    def select_none(self):
        """Clear selection."""
        self.file_list.clearSelection()
    
    def get_selected_files(self):
        """Get list of selected files."""
        selected = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.isSelected():
                selected.append(item.text())
        return selected