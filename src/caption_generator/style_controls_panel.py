# -*- coding: utf-8 -*-
"""
Style Controls Panel for Caption Generator.

A collapsible panel containing font, color, alignment, and video settings
for the three-panel layout.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QRadioButton, QButtonGroup, QCheckBox,
    QColorDialog, QGroupBox, QScrollArea, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class CollapsibleSection(QWidget):
    """A collapsible section widget with header and content."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.is_collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.header_btn = QPushButton(f"[-] {title}")
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(True)
        self.header_btn.clicked.connect(self._toggle)
        self.header_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #00ffff;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 8px 12px;
                text-align: left;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #252525;
                border-color: #00ffff;
            }
            QPushButton:checked {
                background-color: #1a1a1a;
            }
        """)
        layout.addWidget(self.header_btn)

        # Content frame
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: #151515;
                border: 1px solid #303030;
                border-top: none;
                border-radius: 0 0 3px 3px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        layout.addWidget(self.content_frame)

        self.title = title

    def _toggle(self):
        """Toggle the collapsed state."""
        self.is_collapsed = not self.is_collapsed
        self.content_frame.setVisible(not self.is_collapsed)
        prefix = "[+]" if self.is_collapsed else "[-]"
        self.header_btn.setText(f"{prefix} {self.title}")

    def add_widget(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to the content area."""
        self.content_layout.addLayout(layout)


class StyleControlsPanel(QWidget):
    """
    Left panel containing all style controls for the Caption Generator.

    Emits signals when settings change to allow live preview updates.
    """

    # Signals emitted when style settings change
    style_changed = pyqtSignal()  # Generic signal for any style change
    font_changed = pyqtSignal(str, int)  # font_name, font_size
    color_changed = pyqtSignal(str, str)  # text_color, bg_color
    alignment_changed = pyqtSignal(str)  # alignment: top/center/bottom
    video_settings_changed = pyqtSignal(str, int)  # resolution, fps
    transparent_changed = pyqtSignal(bool)  # transparent background
    underlay_mode_changed = pyqtSignal(str)  # "solid" or "video"
    underlay_video_selected = pyqtSignal(str)  # video path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the panel UI."""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for the controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #121212;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 14px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #00ff88;
                min-height: 30px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00ffff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        # Container widget for scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(8)

        # Panel title
        title_label = QLabel("STYLE CONTROLS")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #00ffff;
            padding: 8px 4px;
        """)
        container_layout.addWidget(title_label)

        # === Font Section ===
        font_section = CollapsibleSection("Font Settings")
        self._setup_font_section(font_section)
        container_layout.addWidget(font_section)

        # === Color Section ===
        color_section = CollapsibleSection("Colors")
        self._setup_color_section(color_section)
        container_layout.addWidget(color_section)

        # === Background/Underlay Section ===
        underlay_section = CollapsibleSection("Background")
        self._setup_underlay_section(underlay_section)
        container_layout.addWidget(underlay_section)

        # === Text Options Section ===
        text_section = CollapsibleSection("Text Options")
        self._setup_text_section(text_section)
        container_layout.addWidget(text_section)

        # === Alignment Section ===
        align_section = CollapsibleSection("Alignment")
        self._setup_alignment_section(align_section)
        container_layout.addWidget(align_section)

        # === Video Settings Section ===
        video_section = CollapsibleSection("Video Settings")
        self._setup_video_section(video_section)
        container_layout.addWidget(video_section)

        # Stretch at bottom
        container_layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self._apply_theme()

    def _setup_font_section(self, section: CollapsibleSection):
        """Set up font settings controls."""
        # Font family
        font_row = QHBoxLayout()
        font_label = QLabel("Font:")
        font_label.setFixedWidth(60)
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Arial Narrow", "Arial", "Helvetica", "Impact",
            "Verdana", "Tahoma", "Segoe UI", "Consolas"
        ])
        font_row.addWidget(font_label)
        font_row.addWidget(self.font_combo, 1)
        section.add_layout(font_row)

        # Font size
        size_row = QHBoxLayout()
        size_label = QLabel("Size:")
        size_label.setFixedWidth(60)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(12, 120)
        self.size_spin.setValue(56)
        size_row.addWidget(size_label)
        size_row.addWidget(self.size_spin)
        size_row.addStretch()
        section.add_layout(size_row)

    def _setup_color_section(self, section: CollapsibleSection):
        """Set up color controls."""
        # Text color
        text_row = QHBoxLayout()
        text_label = QLabel("Text:")
        text_label.setFixedWidth(60)
        self.text_color_input = QLineEdit("#ffffff")
        self.text_color_input.setFixedWidth(80)
        self.text_color_btn = QPushButton("Pick")
        self.text_color_btn.setFixedWidth(50)
        self.text_color_btn.clicked.connect(lambda: self._pick_color(self.text_color_input))
        text_row.addWidget(text_label)
        text_row.addWidget(self.text_color_input)
        text_row.addWidget(self.text_color_btn)
        text_row.addStretch()
        section.add_layout(text_row)

        # Background color
        bg_row = QHBoxLayout()
        self.bg_color_label = QLabel("Background:")
        self.bg_color_label.setFixedWidth(60)
        self.bg_color_input = QLineEdit("#000000")
        self.bg_color_input.setFixedWidth(80)
        self.bg_color_btn = QPushButton("Pick")
        self.bg_color_btn.setFixedWidth(50)
        self.bg_color_btn.clicked.connect(lambda: self._pick_color(self.bg_color_input))
        bg_row.addWidget(self.bg_color_label)
        bg_row.addWidget(self.bg_color_input)
        bg_row.addWidget(self.bg_color_btn)
        bg_row.addStretch()
        section.add_layout(bg_row)

        # Transparent checkbox
        self.transparent_checkbox = QCheckBox("Transparent Background (WebM)")
        self.transparent_checkbox.stateChanged.connect(self._on_transparent_changed)
        section.add_widget(self.transparent_checkbox)

    def _setup_underlay_section(self, section: CollapsibleSection):
        """Set up background/underlay controls."""
        # Underlay mode radio buttons
        self.underlay_mode_group = QButtonGroup(self)

        self.solid_bg_radio = QRadioButton("Solid Color")
        self.video_underlay_radio = QRadioButton("Video Underlay")
        self.solid_bg_radio.setChecked(True)

        self.underlay_mode_group.addButton(self.solid_bg_radio, 0)
        self.underlay_mode_group.addButton(self.video_underlay_radio, 1)
        self.underlay_mode_group.buttonClicked.connect(self._on_underlay_mode_changed)

        mode_row = QHBoxLayout()
        mode_row.addWidget(self.solid_bg_radio)
        mode_row.addWidget(self.video_underlay_radio)
        mode_row.addStretch()
        section.add_layout(mode_row)

        # Video underlay controls (initially hidden)
        self.underlay_controls_frame = QFrame()
        underlay_layout = QVBoxLayout(self.underlay_controls_frame)
        underlay_layout.setContentsMargins(0, 4, 0, 0)
        underlay_layout.setSpacing(4)

        # File selection row
        file_row = QHBoxLayout()
        self.underlay_browse_btn = QPushButton("Browse...")
        self.underlay_browse_btn.setFixedWidth(80)
        self.underlay_browse_btn.clicked.connect(self._browse_underlay_video)
        self.underlay_clear_btn = QPushButton("Clear")
        self.underlay_clear_btn.setFixedWidth(50)
        self.underlay_clear_btn.clicked.connect(self._clear_underlay_video)
        file_row.addWidget(self.underlay_browse_btn)
        file_row.addWidget(self.underlay_clear_btn)
        file_row.addStretch()
        underlay_layout.addLayout(file_row)

        # File name display
        self.underlay_file_label = QLabel("No video selected")
        self.underlay_file_label.setStyleSheet("color: #888888; font-size: 10px;")
        self.underlay_file_label.setWordWrap(True)
        underlay_layout.addWidget(self.underlay_file_label)

        section.add_widget(self.underlay_controls_frame)
        self.underlay_controls_frame.setVisible(False)

        # Store the current underlay video path
        self._underlay_video_path = ""

    def _setup_text_section(self, section: CollapsibleSection):
        """Set up text transformation options."""
        self.all_caps_checkbox = QCheckBox("ALL CAPS")
        self.all_caps_checkbox.setToolTip("Convert all text to uppercase in the video output")
        section.add_widget(self.all_caps_checkbox)

        self.ignore_grammar_checkbox = QCheckBox("Ignore Grammar (. , -)")
        self.ignore_grammar_checkbox.setToolTip("Remove punctuation characters from the video output")
        section.add_widget(self.ignore_grammar_checkbox)

        # Words per segment (for transcription)
        words_row = QHBoxLayout()
        words_label = QLabel("Words/Seg:")
        words_label.setFixedWidth(60)
        self.words_per_segment_spin = QSpinBox()
        self.words_per_segment_spin.setRange(1, 20)
        self.words_per_segment_spin.setValue(1)
        self.words_per_segment_spin.setToolTip(
            "Maximum words per subtitle segment when transcribing.\n"
            "1 = one word at a time (karaoke style)\n"
            "3-5 = readable phrases\n"
            "8+ = full sentences"
        )
        words_hint = QLabel("(transcription)")
        words_hint.setStyleSheet("color: #888888; font-size: 10px;")
        words_row.addWidget(words_label)
        words_row.addWidget(self.words_per_segment_spin)
        words_row.addWidget(words_hint)
        words_row.addStretch()
        section.add_layout(words_row)

    def _setup_alignment_section(self, section: CollapsibleSection):
        """Set up alignment controls."""
        self.align_group = QButtonGroup(self)

        self.align_top = QRadioButton("Top")
        self.align_center = QRadioButton("Center")
        self.align_bottom = QRadioButton("Bottom")
        self.align_center.setChecked(True)

        self.align_group.addButton(self.align_top, 0)
        self.align_group.addButton(self.align_center, 1)
        self.align_group.addButton(self.align_bottom, 2)

        align_row = QHBoxLayout()
        align_row.addWidget(self.align_top)
        align_row.addWidget(self.align_center)
        align_row.addWidget(self.align_bottom)
        align_row.addStretch()
        section.add_layout(align_row)

    def _setup_video_section(self, section: CollapsibleSection):
        """Set up video settings controls."""
        # Resolution
        res_row = QHBoxLayout()
        res_label = QLabel("Resolution:")
        res_label.setFixedWidth(60)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080", "1280x720", "3840x2160", "1080x1920"])
        res_row.addWidget(res_label)
        res_row.addWidget(self.res_combo, 1)
        section.add_layout(res_row)

        # FPS
        fps_row = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setFixedWidth(60)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(24, 60)
        self.fps_spin.setValue(30)
        fps_row.addWidget(fps_label)
        fps_row.addWidget(self.fps_spin)
        fps_row.addStretch()
        section.add_layout(fps_row)

    def _apply_theme(self):
        """Apply BEDROT dark theme to the panel."""
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #e0e0e0;
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
        """)

    def _connect_signals(self):
        """Connect internal signals to emit style_changed."""
        # Font changes
        self.font_combo.currentTextChanged.connect(self._emit_font_changed)
        self.size_spin.valueChanged.connect(self._emit_font_changed)

        # Color changes
        self.text_color_input.textChanged.connect(self._emit_color_changed)
        self.bg_color_input.textChanged.connect(self._emit_color_changed)

        # Alignment changes
        self.align_group.buttonClicked.connect(self._emit_alignment_changed)

        # Video settings changes
        self.res_combo.currentTextChanged.connect(self._emit_video_changed)
        self.fps_spin.valueChanged.connect(self._emit_video_changed)

        # Text option changes
        self.all_caps_checkbox.stateChanged.connect(lambda: self.style_changed.emit())
        self.ignore_grammar_checkbox.stateChanged.connect(lambda: self.style_changed.emit())

    def _emit_font_changed(self):
        """Emit font changed signal."""
        self.font_changed.emit(self.font_combo.currentText(), self.size_spin.value())
        self.style_changed.emit()

    def _emit_color_changed(self):
        """Emit color changed signal."""
        self.color_changed.emit(self.text_color_input.text(), self.bg_color_input.text())
        self.style_changed.emit()

    def _emit_alignment_changed(self):
        """Emit alignment changed signal."""
        alignment = self.get_alignment()
        self.alignment_changed.emit(alignment)
        self.style_changed.emit()

    def _emit_video_changed(self):
        """Emit video settings changed signal."""
        self.video_settings_changed.emit(self.res_combo.currentText(), self.fps_spin.value())
        self.style_changed.emit()

    def _pick_color(self, line_edit: QLineEdit):
        """Open color picker dialog."""
        current = QColor(line_edit.text())
        color = QColorDialog.getColor(current, self, "Select Color")
        if color.isValid():
            line_edit.setText(color.name())

    def _on_transparent_changed(self, state):
        """Handle transparent checkbox state change."""
        is_transparent = state == Qt.Checked
        self.bg_color_label.setEnabled(not is_transparent)
        self.bg_color_input.setEnabled(not is_transparent)
        self.bg_color_btn.setEnabled(not is_transparent)
        self.transparent_changed.emit(is_transparent)
        self.style_changed.emit()

    def _on_underlay_mode_changed(self):
        """Handle underlay mode radio button change."""
        if self.solid_bg_radio.isChecked():
            mode = "solid"
            self.underlay_controls_frame.setVisible(False)
        else:
            mode = "video"
            self.underlay_controls_frame.setVisible(True)

        self.underlay_mode_changed.emit(mode)
        self.style_changed.emit()

    def _browse_underlay_video(self):
        """Open file dialog to select underlay video."""
        import os
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Underlay Video", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv);;All Files (*.*)"
        )
        if file_path:
            self._underlay_video_path = file_path
            filename = os.path.basename(file_path)
            self.underlay_file_label.setText(filename)
            self.underlay_file_label.setStyleSheet("color: #00ff88; font-size: 10px;")
            self.underlay_video_selected.emit(file_path)
            self.style_changed.emit()

    def _clear_underlay_video(self):
        """Clear the selected underlay video."""
        self._underlay_video_path = ""
        self.underlay_file_label.setText("No video selected")
        self.underlay_file_label.setStyleSheet("color: #888888; font-size: 10px;")
        self.underlay_video_selected.emit("")
        self.style_changed.emit()

    # =========================================================================
    # Public API for getting/setting values
    # =========================================================================

    def get_settings(self) -> dict:
        """Get all current settings as a dictionary."""
        return {
            "font_name": self.font_combo.currentText(),
            "font_size": self.size_spin.value(),
            "font_color": self.text_color_input.text(),
            "background_color": self.bg_color_input.text(),
            "resolution": self.res_combo.currentText(),
            "fps": self.fps_spin.value(),
            "alignment": self.get_alignment(),
            "outline_size": 2,
            "all_caps": self.all_caps_checkbox.isChecked(),
            "ignore_grammar": self.ignore_grammar_checkbox.isChecked(),
            "transparent_background": self.transparent_checkbox.isChecked(),
            "underlay_mode": self.get_underlay_mode(),
            "underlay_video_path": self._underlay_video_path,
        }

    def get_alignment(self) -> str:
        """Get current alignment setting."""
        if self.align_top.isChecked():
            return "top"
        elif self.align_bottom.isChecked():
            return "bottom"
        return "center"

    def get_underlay_mode(self) -> str:
        """Get current underlay mode (solid or video)."""
        if self.video_underlay_radio.isChecked():
            return "video"
        return "solid"

    def get_underlay_video_path(self) -> str:
        """Get current underlay video path."""
        return self._underlay_video_path

    def get_words_per_segment(self) -> int:
        """Get words per segment value."""
        return self.words_per_segment_spin.value()

    def is_transparent(self) -> bool:
        """Check if transparent background is enabled."""
        return self.transparent_checkbox.isChecked()

    def load_settings(self, config):
        """
        Load settings from config manager.

        Args:
            config: ConfigManager instance
        """
        self.font_combo.setCurrentText(config.get("font_name", "Arial Narrow"))
        self.size_spin.setValue(config.get("font_size", 56))
        self.text_color_input.setText(config.get("font_color", "#ffffff"))
        self.bg_color_input.setText(config.get("background_color", "#000000"))
        self.res_combo.setCurrentText(config.get("resolution", "1920x1080"))
        self.fps_spin.setValue(config.get("fps", 30))

        # Load transparent background setting
        is_transparent = config.get("transparent_background", False)
        self.transparent_checkbox.setChecked(is_transparent)
        self._on_transparent_changed(Qt.Checked if is_transparent else Qt.Unchecked)

        alignment = config.get("alignment", "center")
        if alignment == "top":
            self.align_top.setChecked(True)
        elif alignment == "bottom":
            self.align_bottom.setChecked(True)
        else:
            self.align_center.setChecked(True)

        # Load text transformation settings
        self.all_caps_checkbox.setChecked(config.get("all_caps", False))
        self.ignore_grammar_checkbox.setChecked(config.get("ignore_grammar", False))

        # Load words per segment setting
        self.words_per_segment_spin.setValue(config.get("max_words_per_segment", 1))

        # Load underlay settings
        import os
        underlay_mode = config.get("underlay_mode", "solid")
        if underlay_mode == "video":
            self.video_underlay_radio.setChecked(True)
            self.underlay_controls_frame.setVisible(True)
        else:
            self.solid_bg_radio.setChecked(True)
            self.underlay_controls_frame.setVisible(False)

        underlay_path = config.get("underlay_video_path", "")
        if underlay_path and os.path.exists(underlay_path):
            self._underlay_video_path = underlay_path
            filename = os.path.basename(underlay_path)
            self.underlay_file_label.setText(filename)
            self.underlay_file_label.setStyleSheet("color: #00ff88; font-size: 10px;")
        else:
            self._underlay_video_path = ""
            self.underlay_file_label.setText("No video selected")
            self.underlay_file_label.setStyleSheet("color: #888888; font-size: 10px;")

    def save_settings(self, config):
        """
        Save settings to config manager.

        Args:
            config: ConfigManager instance
        """
        config.set("font_name", self.font_combo.currentText(), autosave=False)
        config.set("font_size", self.size_spin.value(), autosave=False)
        config.set("font_color", self.text_color_input.text(), autosave=False)
        config.set("background_color", self.bg_color_input.text(), autosave=False)
        config.set("transparent_background", self.transparent_checkbox.isChecked(), autosave=False)
        config.set("resolution", self.res_combo.currentText(), autosave=False)
        config.set("fps", self.fps_spin.value(), autosave=False)
        config.set("alignment", self.get_alignment(), autosave=False)
        config.set("all_caps", self.all_caps_checkbox.isChecked(), autosave=False)
        config.set("ignore_grammar", self.ignore_grammar_checkbox.isChecked(), autosave=False)
        config.set("max_words_per_segment", self.words_per_segment_spin.value(), autosave=False)
        config.set("underlay_mode", self.get_underlay_mode(), autosave=False)
        config.set("underlay_video_path", self._underlay_video_path, autosave=False)
        config.save_config()
