# -*- coding: utf-8 -*-
"""
Playback Controls Widget for Caption Generator.

Compact control bar for video/audio playback with play/pause, seek, and time display.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, QFrame
)


def format_time(ms: int) -> str:
    """
    Format milliseconds as MM:SS.

    Args:
        ms: Time in milliseconds

    Returns:
        Formatted time string
    """
    if ms < 0:
        ms = 0
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


class PlaybackControlsWidget(QFrame):
    """
    Compact control bar for video/audio playback.

    Features:
    - Play/Pause toggle button
    - Seek slider with position tracking
    - Current time display (MM:SS)
    - Duration display (MM:SS)

    Signals:
        play_clicked(): Emitted when play button is clicked while paused
        pause_clicked(): Emitted when pause button is clicked while playing
        seek_requested(int): Emitted when user seeks to position (ms)
    """

    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        """Initialize playback controls."""
        super().__init__(parent)
        self.setObjectName("PlaybackControls")

        self._is_playing: bool = False
        self._duration_ms: int = 0
        self._seeking: bool = False  # Flag to prevent feedback loop

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Play/Pause button
        self.play_btn = QPushButton("PLAY")
        self.play_btn.setFixedWidth(70)
        self.play_btn.setFixedHeight(28)
        self.play_btn.clicked.connect(self._on_play_clicked)
        layout.addWidget(self.play_btn)

        # Current time label
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setFixedWidth(45)
        self.current_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.current_time_label)

        # Seek slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)  # Use 0-1000 for precision
        self.seek_slider.setValue(0)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        layout.addWidget(self.seek_slider, 1)

        # Duration label
        self.duration_label = QLabel("00:00")
        self.duration_label.setFixedWidth(45)
        self.duration_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.duration_label)

    def _apply_theme(self):
        """Apply BEDROT dark theme styling."""
        self.setStyleSheet("""
            QFrame#PlaybackControls {
                background-color: #1a1a1a;
                border: 1px solid #303030;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 2px solid #00ffff;
                border-radius: 4px;
                color: #00ffff;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #252525;
                border-color: #00ff88;
                color: #00ff88;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                border-color: #404040;
                color: #404040;
            }
            QLabel {
                color: #888888;
                font-family: Consolas;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #404040;
                height: 6px;
                background: #252525;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00ff88;
                border: none;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #00ffff;
            }
            QSlider::sub-page:horizontal {
                background: #00ff88;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #252525;
                border-radius: 3px;
            }
        """)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_play_clicked(self):
        """Handle play/pause button click."""
        if self._is_playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

    def _on_slider_pressed(self):
        """Handle slider press (start seeking)."""
        self._seeking = True

    def _on_slider_released(self):
        """Handle slider release (finish seeking)."""
        self._seeking = False
        if self._duration_ms > 0:
            position_ms = int((self.seek_slider.value() / 1000) * self._duration_ms)
            self.seek_requested.emit(position_ms)

    def _on_slider_moved(self, value: int):
        """Handle slider move (update time display during drag)."""
        if self._duration_ms > 0:
            position_ms = int((value / 1000) * self._duration_ms)
            self.current_time_label.setText(format_time(position_ms))

    # =========================================================================
    # Public API
    # =========================================================================

    def set_playing(self, is_playing: bool):
        """
        Update the play/pause button state.

        Args:
            is_playing: True if media is currently playing
        """
        self._is_playing = is_playing
        if is_playing:
            self.play_btn.setText("PAUSE")
        else:
            self.play_btn.setText("PLAY")

    def set_duration(self, duration_ms: int):
        """
        Set the total duration of the media.

        Args:
            duration_ms: Duration in milliseconds
        """
        self._duration_ms = duration_ms
        self.duration_label.setText(format_time(duration_ms))

    def set_position(self, position_ms: int):
        """
        Update the current playback position.

        Args:
            position_ms: Current position in milliseconds
        """
        # Don't update if user is currently seeking
        if self._seeking:
            return

        self.current_time_label.setText(format_time(position_ms))

        if self._duration_ms > 0:
            slider_value = int((position_ms / self._duration_ms) * 1000)
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(slider_value)
            self.seek_slider.blockSignals(False)

    def set_enabled_state(self, enabled: bool):
        """
        Enable or disable the controls.

        Args:
            enabled: Whether controls should be enabled
        """
        self.play_btn.setEnabled(enabled)
        self.seek_slider.setEnabled(enabled)

    def reset(self):
        """Reset controls to initial state."""
        self._is_playing = False
        self._duration_ms = 0
        self._seeking = False
        self.play_btn.setText("PLAY")
        self.current_time_label.setText("00:00")
        self.duration_label.setText("00:00")
        self.seek_slider.setValue(0)
