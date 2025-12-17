# -*- coding: utf-8 -*-
"""
Timeline Widget for Caption Generator.

Bottom panel with waveform visualization and draggable subtitle segments.
Uses QGraphicsView/Scene for interactive timeline display.
"""

import os
import wave
import struct
from typing import Optional, List, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPolygonItem,
    QGraphicsLineItem, QSlider, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainter, QPolygonF, QLinearGradient
)

from .srt_data_model import SRTDataModel, WordBlock


class DraggableSegment(QGraphicsRectItem):
    """
    A draggable rectangle representing a subtitle segment on the timeline.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        block_index: int,
        color: str,
        parent=None
    ):
        super().__init__(x, y, width, height, parent)
        self.block_index = block_index
        self.base_color = QColor(color)
        self.is_selected = False

        # Enable interaction
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        # Set appearance
        self._update_appearance()

    def _update_appearance(self):
        """Update the visual appearance based on selection state."""
        if self.is_selected:
            pen = QPen(QColor("#00ffff"), 2)
            brush = QBrush(QColor(self.base_color.red(), self.base_color.green(),
                                  self.base_color.blue(), 200))
        else:
            pen = QPen(QColor("#404040"), 1)
            brush = QBrush(QColor(self.base_color.red(), self.base_color.green(),
                                  self.base_color.blue(), 150))

        self.setPen(pen)
        self.setBrush(brush)

    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self._update_appearance()

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        if not self.is_selected:
            pen = QPen(QColor("#00ff88"), 2)
            self.setPen(pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Remove highlight on hover exit."""
        self._update_appearance()
        super().hoverLeaveEvent(event)


class TimelineView(QGraphicsView):
    """Custom graphics view with mouse tracking for timeline interaction."""

    position_clicked = pyqtSignal(float)  # Emits position in seconds
    segment_selected = pyqtSignal(int)  # Emits segment index
    segment_timing_changed = pyqtSignal(int, float, float)  # index, start_sec, end_sec

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)

        # Timeline parameters
        self.duration_sec = 60.0  # Total duration in seconds
        self.pixels_per_second = 50.0  # Zoom level

        # Drag state
        self._dragging = False
        self._drag_segment: Optional[DraggableSegment] = None
        self._drag_edge: str = ""  # "left", "right", or "move"
        self._drag_start_x = 0.0

    def mousePressEvent(self, event):
        """Handle mouse press for segment interaction."""
        pos = self.mapToScene(event.pos())

        # Check if clicking on a segment
        item = self.scene().itemAt(pos, self.transform())

        if isinstance(item, DraggableSegment):
            self._drag_segment = item
            self._drag_start_x = pos.x()

            # Determine which edge (or center for move)
            rect = item.rect()
            item_pos = item.pos()
            local_x = pos.x() - item_pos.x()

            if local_x < 10:
                self._drag_edge = "left"
                self.setCursor(Qt.SizeHorCursor)
            elif local_x > rect.width() - 10:
                self._drag_edge = "right"
                self.setCursor(Qt.SizeHorCursor)
            else:
                self._drag_edge = "move"
                self.setCursor(Qt.ClosedHandCursor)

            self._dragging = True
            self.segment_selected.emit(item.block_index)
        else:
            # Click on empty space - jump to position
            time_sec = pos.x() / self.pixels_per_second
            if 0 <= time_sec <= self.duration_sec:
                self.position_clicked.emit(time_sec)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for segment dragging."""
        if self._dragging and self._drag_segment:
            pos = self.mapToScene(event.pos())
            delta_x = pos.x() - self._drag_start_x

            rect = self._drag_segment.rect()
            item_pos = self._drag_segment.pos()

            if self._drag_edge == "left":
                # Resize from left edge
                new_x = item_pos.x() + delta_x
                new_width = rect.width() - delta_x
                if new_width > 10 and new_x >= 0:  # Minimum width
                    self._drag_segment.setPos(new_x, item_pos.y())
                    self._drag_segment.setRect(0, 0, new_width, rect.height())
                    self._drag_start_x = pos.x()

            elif self._drag_edge == "right":
                # Resize from right edge
                new_width = rect.width() + delta_x
                if new_width > 10:  # Minimum width
                    self._drag_segment.setRect(0, 0, new_width, rect.height())
                    self._drag_start_x = pos.x()

            elif self._drag_edge == "move":
                # Move entire segment
                new_x = item_pos.x() + delta_x
                if new_x >= 0:
                    self._drag_segment.setPos(new_x, item_pos.y())
                    self._drag_start_x = pos.x()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize segment changes."""
        if self._dragging and self._drag_segment:
            # Calculate new timing
            rect = self._drag_segment.rect()
            item_pos = self._drag_segment.pos()

            start_sec = item_pos.x() / self.pixels_per_second
            end_sec = (item_pos.x() + rect.width()) / self.pixels_per_second

            # Emit timing change signal
            self.segment_timing_changed.emit(
                self._drag_segment.block_index,
                start_sec,
                end_sec
            )

            self._dragging = False
            self._drag_segment = None
            self._drag_edge = ""
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel for horizontal scrolling."""
        # Horizontal scroll with wheel
        delta = event.angleDelta().y()
        scroll_bar = self.horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() - delta)


class TimelineWidget(QWidget):
    """
    Bottom panel with waveform visualization and segment timeline.

    Features:
    - Waveform display from audio file
    - Draggable segment handles for timing adjustment
    - Zoom in/out controls
    - Click to select phrase
    - Visual markers for phrase boundaries
    """

    # Signals
    phrase_selected = pyqtSignal(int)  # Emits phrase index when clicked
    timing_changed = pyqtSignal(int, int, int)  # index, start_ms, end_ms
    position_changed = pyqtSignal(int)  # playhead position in ms

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model: Optional[SRTDataModel] = None
        self.audio_path: Optional[str] = None
        self.duration_ms: int = 0
        self.waveform_data: List[float] = []
        self.segments: List[DraggableSegment] = []
        self.selected_index: int = -1
        self.pixels_per_second: float = 50.0

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header with controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("TIMELINE")
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #00ffff;
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Zoom controls
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(24, 24)
        zoom_out_btn.setToolTip("Zoom out")
        zoom_out_btn.clicked.connect(self._zoom_out)
        header_layout.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("50 px/s")
        self.zoom_label.setStyleSheet("color: #888888; font-size: 10px;")
        self.zoom_label.setFixedWidth(60)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(24, 24)
        zoom_in_btn.setToolTip("Zoom in")
        zoom_in_btn.clicked.connect(self._zoom_in)
        header_layout.addWidget(zoom_in_btn)

        # Duration display
        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet("color: #666666; padding-left: 16px;")
        header_layout.addWidget(self.duration_label)

        layout.addLayout(header_layout)

        # Graphics scene and view
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor("#0a0a0a")))

        self.view = TimelineView(self.scene)
        self.view.setMinimumHeight(100)
        self.view.setMaximumHeight(150)
        self.view.segment_selected.connect(self._on_segment_selected)
        self.view.segment_timing_changed.connect(self._on_segment_timing_changed)
        self.view.position_clicked.connect(self._on_position_clicked)

        layout.addWidget(self.view)

        # Playhead line
        self.playhead = QGraphicsLineItem()
        self.playhead.setPen(QPen(QColor("#ff0066"), 2))
        self.playhead.setZValue(100)  # On top of everything
        self.scene.addItem(self.playhead)

    def _apply_theme(self):
        """Apply BEDROT dark theme."""
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 3px;
                color: #00ffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #252525;
                border-color: #00ffff;
            }
            QGraphicsView {
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QScrollBar:horizontal {
                background-color: #1a1a1a;
                height: 14px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #00ff88;
                min-width: 30px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #00ffff;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)

    def _zoom_in(self):
        """Increase zoom level."""
        self.pixels_per_second = min(200.0, self.pixels_per_second * 1.5)
        self.view.pixels_per_second = self.pixels_per_second
        self.zoom_label.setText(f"{int(self.pixels_per_second)} px/s")
        self._refresh_display()

    def _zoom_out(self):
        """Decrease zoom level."""
        self.pixels_per_second = max(10.0, self.pixels_per_second / 1.5)
        self.view.pixels_per_second = self.pixels_per_second
        self.zoom_label.setText(f"{int(self.pixels_per_second)} px/s")
        self._refresh_display()

    def load_audio(self, audio_path: str) -> bool:
        """
        Load audio file and extract waveform data.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            True if successful
        """
        self.audio_path = audio_path

        # Try to get duration using ffprobe
        try:
            from .video_generator import get_audio_duration
            duration = get_audio_duration(audio_path)
            if duration:
                self.duration_ms = int(duration * 1000)
                self.view.duration_sec = duration
        except Exception:
            self.duration_ms = 60000  # Default 60 seconds

        # Update duration display
        mins = self.duration_ms // 60000
        secs = (self.duration_ms % 60000) // 1000
        self.duration_label.setText(f"{mins}:{secs:02d}")

        # Extract waveform (simplified - just visual representation)
        self.waveform_data = self._extract_waveform(audio_path)

        self._refresh_display()
        return True

    def _extract_waveform(self, audio_path: str) -> List[float]:
        """
        Extract waveform data from audio file for visualization.

        Returns normalized amplitude values for display.
        """
        waveform = []

        # Try to read WAV file directly
        if audio_path.lower().endswith('.wav'):
            try:
                with wave.open(audio_path, 'rb') as wav:
                    n_channels = wav.getnchannels()
                    sample_width = wav.getsampwidth()
                    n_frames = wav.getnframes()
                    framerate = wav.getframerate()

                    # Read all frames
                    frames = wav.readframes(n_frames)

                    # Determine sample format
                    if sample_width == 1:
                        fmt = f"{n_frames * n_channels}B"
                        samples = struct.unpack(fmt, frames)
                        samples = [s - 128 for s in samples]  # Convert to signed
                        max_val = 128
                    elif sample_width == 2:
                        fmt = f"<{n_frames * n_channels}h"
                        samples = struct.unpack(fmt, frames)
                        max_val = 32768
                    else:
                        return self._generate_placeholder_waveform()

                    # Downsample for display (target ~1000 points)
                    target_points = min(2000, n_frames // 100)
                    chunk_size = max(1, len(samples) // target_points)

                    for i in range(0, len(samples), chunk_size * n_channels):
                        chunk = samples[i:i + chunk_size * n_channels]
                        if chunk:
                            # Take max absolute value in chunk
                            max_amp = max(abs(s) for s in chunk) / max_val
                            waveform.append(max_amp)

                    return waveform

            except Exception as e:
                print(f"[Timeline] Error reading WAV: {e}")

        # For non-WAV files or on error, generate placeholder
        return self._generate_placeholder_waveform()

    def _generate_placeholder_waveform(self) -> List[float]:
        """Generate a placeholder waveform pattern."""
        import math
        waveform = []
        points = 1000

        for i in range(points):
            # Create a varied pattern
            t = i / points
            amp = (
                0.3 * abs(math.sin(t * 10 * math.pi)) +
                0.2 * abs(math.sin(t * 23 * math.pi)) +
                0.1 * abs(math.sin(t * 47 * math.pi)) +
                0.2  # Base level
            )
            waveform.append(min(1.0, amp))

        return waveform

    def set_model(self, model: SRTDataModel):
        """
        Set the SRT data model.

        Args:
            model: SRTDataModel with phrase data
        """
        self.model = model
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the timeline display."""
        # Clear existing items (except playhead)
        for item in self.scene.items():
            if item != self.playhead:
                self.scene.removeItem(item)
        self.segments.clear()

        # Calculate scene dimensions
        duration_sec = self.duration_ms / 1000.0
        scene_width = duration_sec * self.pixels_per_second
        scene_height = 120

        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        # Draw waveform
        self._draw_waveform(scene_width, scene_height)

        # Draw time markers
        self._draw_time_markers(scene_width, scene_height)

        # Draw segments
        if self.model:
            self._draw_segments(scene_height)

        # Update playhead
        self.playhead.setLine(0, 0, 0, scene_height)

    def _draw_waveform(self, width: float, height: float):
        """Draw the waveform visualization."""
        if not self.waveform_data:
            return

        # Waveform area (middle 60% of height)
        wave_top = height * 0.2
        wave_height = height * 0.4
        wave_center = wave_top + wave_height / 2

        # Create polygon points
        points = []
        n_points = len(self.waveform_data)

        # Top edge (going right)
        for i, amp in enumerate(self.waveform_data):
            x = (i / n_points) * width
            y = wave_center - amp * (wave_height / 2)
            points.append(QPointF(x, y))

        # Bottom edge (going left)
        for i in range(n_points - 1, -1, -1):
            x = (i / n_points) * width
            amp = self.waveform_data[i]
            y = wave_center + amp * (wave_height / 2)
            points.append(QPointF(x, y))

        # Create polygon item
        polygon = QPolygonF(points)
        waveform_item = QGraphicsPolygonItem(polygon)

        # Gradient fill (cyan)
        gradient = QLinearGradient(0, wave_top, 0, wave_top + wave_height)
        gradient.setColorAt(0, QColor(0, 255, 255, 100))
        gradient.setColorAt(0.5, QColor(0, 255, 255, 150))
        gradient.setColorAt(1, QColor(0, 255, 255, 100))

        waveform_item.setBrush(QBrush(gradient))
        waveform_item.setPen(QPen(Qt.NoPen))
        waveform_item.setZValue(1)

        self.scene.addItem(waveform_item)

    def _draw_time_markers(self, width: float, height: float):
        """Draw time scale markers."""
        # Determine marker interval based on zoom
        if self.pixels_per_second >= 100:
            interval = 1.0  # 1 second
        elif self.pixels_per_second >= 50:
            interval = 2.0  # 2 seconds
        elif self.pixels_per_second >= 25:
            interval = 5.0  # 5 seconds
        else:
            interval = 10.0  # 10 seconds

        duration_sec = self.duration_ms / 1000.0
        t = 0.0

        while t <= duration_sec:
            x = t * self.pixels_per_second

            # Marker line
            line = QGraphicsLineItem(x, height - 20, x, height - 10)
            line.setPen(QPen(QColor("#404040"), 1))
            line.setZValue(2)
            self.scene.addItem(line)

            # Time label
            mins = int(t // 60)
            secs = int(t % 60)
            label_text = f"{mins}:{secs:02d}"

            from PyQt5.QtWidgets import QGraphicsTextItem
            label = QGraphicsTextItem(label_text)
            label.setDefaultTextColor(QColor("#666666"))
            label.setPos(x - 15, height - 20)
            label.setZValue(2)
            self.scene.addItem(label)

            t += interval

    def _draw_segments(self, height: float):
        """Draw subtitle segments."""
        if not self.model:
            return

        segment_height = 25
        segment_y = height * 0.65

        for i, block in enumerate(self.model.blocks):
            start_x = (block.start_ms / 1000.0) * self.pixels_per_second
            end_x = (block.end_ms / 1000.0) * self.pixels_per_second
            width = end_x - start_x

            segment = DraggableSegment(
                0, 0, width, segment_height,
                block_index=i,
                color=block.color
            )
            segment.setPos(start_x, segment_y)
            segment.setZValue(10)

            if i == self.selected_index:
                segment.set_selected(True)

            self.scene.addItem(segment)
            self.segments.append(segment)

    def _on_segment_selected(self, index: int):
        """Handle segment selection."""
        self.select_phrase(index)
        self.phrase_selected.emit(index)

    def _on_segment_timing_changed(self, index: int, start_sec: float, end_sec: float):
        """Handle segment timing change from drag."""
        start_ms = int(start_sec * 1000)
        end_ms = int(end_sec * 1000)
        self.timing_changed.emit(index, start_ms, end_ms)

    def _on_position_clicked(self, position_sec: float):
        """Handle click on timeline position."""
        position_ms = int(position_sec * 1000)
        self.position_changed.emit(position_ms)

    def select_phrase(self, index: int):
        """
        Select a phrase on the timeline.

        Args:
            index: Phrase index to select
        """
        self.selected_index = index

        # Update segment selection visuals
        for i, segment in enumerate(self.segments):
            segment.set_selected(i == index)

        # Scroll to selected segment
        if 0 <= index < len(self.segments):
            segment = self.segments[index]
            self.view.centerOn(segment)

    def set_playhead_position(self, position_ms: int):
        """
        Set the playhead position.

        Args:
            position_ms: Position in milliseconds
        """
        x = (position_ms / 1000.0) * self.pixels_per_second
        scene_height = self.scene.height()
        self.playhead.setLine(x, 0, x, scene_height)

    def clear(self):
        """Clear the timeline."""
        self.model = None
        self.audio_path = None
        self.duration_ms = 0
        self.waveform_data = []
        self.segments.clear()
        self.selected_index = -1

        for item in self.scene.items():
            if item != self.playhead:
                self.scene.removeItem(item)

        self.duration_label.setText("0:00")
