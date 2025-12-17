# -*- coding: utf-8 -*-
"""
Video Preview Widget for Caption Generator.

Replaces the PIL-based PreviewWidget with full video/audio playback
using QMediaPlayer, with caption overlay and playback controls.
"""

import os
from typing import Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QStackedWidget
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from .caption_overlay import CaptionOverlay
from .playback_controls import PlaybackControlsWidget


class VideoPreviewWidget(QWidget):
    """
    Video/audio preview widget with caption overlay.

    Features:
    - Audio playback with solid color or video underlay
    - Real-time caption rendering over video
    - Playback controls (play/pause/seek)
    - Sync signals for timeline coordination

    Signals:
        position_changed(int): Emitted on playback position change (ms)
        playback_state_changed(bool): Emitted on play/pause state change
        playback_error(str): Emitted on playback errors
        duration_available(int): Emitted when duration is known (ms)
    """

    position_changed = pyqtSignal(int)
    playback_state_changed = pyqtSignal(bool)
    playback_error = pyqtSignal(str)
    duration_available = pyqtSignal(int)

    def __init__(self, parent=None):
        """Initialize video preview widget."""
        super().__init__(parent)

        # State
        self._audio_path: Optional[str] = None
        self._underlay_path: Optional[str] = None
        self._underlay_mode: str = "solid"  # "solid" or "video"
        self._background_color: str = "#000000"
        self._duration_ms: int = 0
        self._is_playing: bool = False

        # Style settings cache
        self._style_settings: Dict = {
            "font_name": "Arial",
            "font_size": 56,
            "font_color": "#ffffff",
            "background_color": "#000000",
            "alignment": "center",
            "outline_size": 2,
        }

        self._setup_ui()
        self._apply_theme()
        self._setup_media_players()

        # Sync timer for underlay video
        self._sync_timer = QTimer()
        self._sync_timer.setInterval(500)  # Sync every 500ms
        self._sync_timer.timeout.connect(self._sync_underlay)

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        title_label = QLabel("PREVIEW")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #00ffff;
            padding: 8px;
        """)
        layout.addWidget(title_label)

        # Preview container
        self.preview_container = QFrame()
        self.preview_container.setObjectName("PreviewContainer")
        self.preview_container.setMinimumSize(320, 200)
        container_layout = QVBoxLayout(self.preview_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget for solid color vs video underlay
        self.display_stack = QStackedWidget()

        # Option 1: Solid color background widget
        self.solid_bg_widget = QFrame()
        self.solid_bg_widget.setObjectName("SolidBackground")
        self.solid_bg_widget.setStyleSheet("background-color: #000000;")
        self.display_stack.addWidget(self.solid_bg_widget)

        # Option 2: Video widget for underlay
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #000000;")
        self.display_stack.addWidget(self.video_widget)

        # Default to solid background
        self.display_stack.setCurrentIndex(0)

        container_layout.addWidget(self.display_stack, 1)

        # Caption overlay (sits on top of display stack)
        self.caption_overlay = CaptionOverlay(self.display_stack)
        self.caption_overlay.raise_()

        layout.addWidget(self.preview_container, 1)

        # Playback controls
        self.playback_controls = PlaybackControlsWidget()
        self.playback_controls.play_clicked.connect(self.play)
        self.playback_controls.pause_clicked.connect(self.pause)
        self.playback_controls.seek_requested.connect(self.seek)
        layout.addWidget(self.playback_controls)

        # Status label
        self.status_label = QLabel("No audio loaded")
        self.status_label.setStyleSheet("color: #666666; padding: 4px 8px; font-size: 10px;")
        layout.addWidget(self.status_label)

    def _apply_theme(self):
        """Apply BEDROT dark theme."""
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#PreviewContainer {
                background-color: #0a0a0a;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)

    def _setup_media_players(self):
        """Set up QMediaPlayer instances."""
        # Primary audio player
        self.audio_player = QMediaPlayer()
        self.audio_player.positionChanged.connect(self._on_position_changed)
        self.audio_player.durationChanged.connect(self._on_duration_changed)
        self.audio_player.stateChanged.connect(self._on_state_changed)
        self.audio_player.error.connect(self._on_error)

        # Underlay video player (muted)
        self.underlay_player = QMediaPlayer()
        self.underlay_player.setVideoOutput(self.video_widget)
        self.underlay_player.setMuted(True)
        self.underlay_player.error.connect(self._on_underlay_error)

    # =========================================================================
    # Media Player Event Handlers
    # =========================================================================

    def _on_position_changed(self, position_ms: int):
        """Handle audio player position change."""
        self.playback_controls.set_position(position_ms)
        self.position_changed.emit(position_ms)

    def _on_duration_changed(self, duration_ms: int):
        """Handle duration change."""
        self._duration_ms = duration_ms
        self.playback_controls.set_duration(duration_ms)
        self.duration_available.emit(duration_ms)

    def _on_state_changed(self, state):
        """Handle playback state change."""
        is_playing = (state == QMediaPlayer.PlayingState)
        self._is_playing = is_playing
        self.playback_controls.set_playing(is_playing)
        self.playback_state_changed.emit(is_playing)

        # Start/stop underlay sync
        if is_playing and self._underlay_mode == "video" and self._underlay_path:
            self._sync_timer.start()
        else:
            self._sync_timer.stop()

    def _on_error(self, error):
        """Handle audio player error."""
        error_msg = self.audio_player.errorString()
        self.status_label.setText(f"Error: {error_msg[:40]}")
        self.playback_error.emit(error_msg)
        print(f"[VideoPreview] Audio player error: {error_msg}")

    def _on_underlay_error(self, error):
        """Handle underlay player error."""
        error_msg = self.underlay_player.errorString()
        print(f"[VideoPreview] Underlay player error: {error_msg}")
        # Fall back to solid color
        self.set_underlay_mode("solid")

    def _sync_underlay(self):
        """Sync underlay video position to audio position."""
        if not self._is_playing or self._underlay_mode != "video":
            return

        audio_pos = self.audio_player.position()
        underlay_pos = self.underlay_player.position()

        # Correct if drift exceeds 100ms
        drift = abs(audio_pos - underlay_pos)
        if drift > 100:
            self.underlay_player.setPosition(audio_pos)

    # =========================================================================
    # Public API - Media Loading
    # =========================================================================

    def load_audio(self, path: str):
        """
        Load an audio file for playback.

        Args:
            path: Path to audio file (WAV, MP3, FLAC, M4A, AAC)
        """
        if not path or not os.path.exists(path):
            self.status_label.setText("Audio file not found")
            return

        self._audio_path = path
        self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.playback_controls.set_enabled_state(True)

        filename = os.path.basename(path)
        self.status_label.setText(f"Loaded: {filename}")
        print(f"[VideoPreview] Loaded audio: {path}")

    def load_underlay_video(self, path: str):
        """
        Load a video file as background underlay.

        Args:
            path: Path to video file (MP4, MOV, AVI)
        """
        if not path or not os.path.exists(path):
            self._underlay_path = None
            return

        self._underlay_path = path
        self.underlay_player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))

        # Switch to video mode
        if self._underlay_mode == "video":
            self.display_stack.setCurrentIndex(1)

        filename = os.path.basename(path)
        print(f"[VideoPreview] Loaded underlay video: {filename}")

    def clear_underlay_video(self):
        """Clear the underlay video and switch to solid color."""
        self._underlay_path = None
        self.underlay_player.stop()
        self.underlay_player.setMedia(QMediaContent())
        self.set_underlay_mode("solid")

    def set_underlay_mode(self, mode: str):
        """
        Set the underlay display mode.

        Args:
            mode: "solid" for solid color, "video" for video underlay
        """
        self._underlay_mode = mode

        if mode == "solid":
            self.display_stack.setCurrentIndex(0)
            self._sync_timer.stop()
            if self.underlay_player.state() == QMediaPlayer.PlayingState:
                self.underlay_player.pause()
        else:  # video
            if self._underlay_path:
                self.display_stack.setCurrentIndex(1)
                # Sync underlay to current audio position if playing
                if self._is_playing:
                    self.underlay_player.setPosition(self.audio_player.position())
                    self.underlay_player.play()
                    self._sync_timer.start()
            else:
                # No underlay loaded, stay on solid
                self.display_stack.setCurrentIndex(0)

    def set_background_color(self, color: str):
        """
        Set the solid background color.

        Args:
            color: Hex color string (e.g., "#000000")
        """
        self._background_color = color
        self.solid_bg_widget.setStyleSheet(f"background-color: {color};")
        self._style_settings["background_color"] = color

    # =========================================================================
    # Public API - Playback Control
    # =========================================================================

    def play(self):
        """Start playback."""
        if self._audio_path:
            self.audio_player.play()

            # Also play underlay if in video mode
            if self._underlay_mode == "video" and self._underlay_path:
                self.underlay_player.setPosition(self.audio_player.position())
                self.underlay_player.play()

    def pause(self):
        """Pause playback."""
        self.audio_player.pause()

        if self._underlay_mode == "video":
            self.underlay_player.pause()

    def stop(self):
        """Stop playback and reset position."""
        self.audio_player.stop()
        self.underlay_player.stop()

    def seek(self, position_ms: int):
        """
        Seek to a position in milliseconds.

        Args:
            position_ms: Target position in milliseconds
        """
        self.audio_player.setPosition(position_ms)

        if self._underlay_mode == "video" and self._underlay_path:
            self.underlay_player.setPosition(position_ms)

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._is_playing

    def get_position(self) -> int:
        """Get current playback position in milliseconds."""
        return self.audio_player.position()

    def get_duration(self) -> int:
        """Get total duration in milliseconds."""
        return self._duration_ms

    # =========================================================================
    # Public API - Caption Control
    # =========================================================================

    def set_caption_text(self, text: str):
        """
        Set the caption text to display.

        Args:
            text: Caption text (can include newlines)
        """
        self.caption_overlay.set_caption_text(text)

    def set_caption_style(self, settings: Dict):
        """
        Update caption style from settings dictionary.

        Args:
            settings: Dictionary with font_name, font_size, font_color,
                     alignment, outline_size keys
        """
        self._style_settings.update(settings)
        self.caption_overlay.update_from_settings(settings)

        # Also update background color if provided
        if "background_color" in settings:
            self.set_background_color(settings["background_color"])

    def clear_caption(self):
        """Clear the current caption."""
        self.caption_overlay.clear()

    # =========================================================================
    # Geometry
    # =========================================================================

    def resizeEvent(self, event):
        """Handle resize to keep overlay sized correctly."""
        super().resizeEvent(event)

        # Resize caption overlay to match display stack
        if hasattr(self, 'caption_overlay') and hasattr(self, 'display_stack'):
            self.caption_overlay.setGeometry(self.display_stack.geometry())

    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Ensure overlay is properly sized
        if hasattr(self, 'caption_overlay') and hasattr(self, 'display_stack'):
            self.caption_overlay.setGeometry(self.display_stack.geometry())

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(self):
        """Clean up resources before closing."""
        self._sync_timer.stop()
        self.audio_player.stop()
        self.underlay_player.stop()
