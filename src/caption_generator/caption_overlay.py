# -*- coding: utf-8 -*-
"""
Caption Overlay Widget for Caption Generator.

A transparent overlay widget for rendering captions over video content.
Uses QPainter for text rendering with outline support.
"""

from typing import Dict, Optional

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QFont, QColor, QPen, QPainterPath, QFontMetrics
from PyQt5.QtWidgets import QWidget


class CaptionOverlay(QWidget):
    """
    Transparent overlay widget for rendering captions over video.

    Features:
    - Transparent background (WA_TranslucentBackground)
    - Mouse events pass through (WA_TransparentForMouseEvents)
    - Text outline rendering via QPainterPath
    - Position alignment (top/center/bottom)
    - Font and color settings from style controls
    """

    def __init__(self, parent=None):
        """Initialize caption overlay."""
        super().__init__(parent)

        # Make overlay transparent
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Caption properties
        self._caption_text: str = ""
        self._font_name: str = "Arial"
        self._font_size: int = 56
        self._font_color: QColor = QColor("#ffffff")
        self._outline_color: QColor = QColor("#000000")
        self._outline_width: int = 2
        self._alignment: str = "center"  # top, center, bottom (vertical)

        # Margin from edges (percentage of height)
        self._margin_percent: float = 0.10  # 10% margin from top/bottom

    # =========================================================================
    # Public API - Setters
    # =========================================================================

    def set_caption_text(self, text: str):
        """Set the caption text to display."""
        if self._caption_text != text:
            self._caption_text = text
            self.update()

    def set_font_name(self, font_name: str):
        """Set the font family."""
        if self._font_name != font_name:
            self._font_name = font_name
            self.update()

    def set_font_size(self, size: int):
        """Set the font size in pixels."""
        if self._font_size != size:
            self._font_size = size
            self.update()

    def set_font_color(self, color: str):
        """Set the font color (hex string)."""
        self._font_color = QColor(color)
        self.update()

    def set_outline_color(self, color: str):
        """Set the outline color (hex string)."""
        self._outline_color = QColor(color)
        self.update()

    def set_outline_width(self, width: int):
        """Set the outline width in pixels."""
        self._outline_width = width
        self.update()

    def set_alignment(self, alignment: str):
        """Set vertical alignment (top, center, bottom)."""
        if alignment in ("top", "center", "bottom"):
            self._alignment = alignment
            self.update()

    def update_from_settings(self, settings: Dict):
        """
        Update caption style from a settings dictionary.

        Args:
            settings: Dictionary with keys like font_name, font_size,
                     font_color, alignment, outline_size
        """
        if "font_name" in settings:
            self._font_name = settings["font_name"]
        if "font_size" in settings:
            self._font_size = settings["font_size"]
        if "font_color" in settings:
            self._font_color = QColor(settings["font_color"])
        if "alignment" in settings:
            self._alignment = settings["alignment"]
        if "outline_size" in settings:
            self._outline_width = settings["outline_size"]
        self.update()

    def clear(self):
        """Clear the caption text."""
        self._caption_text = ""
        self.update()

    # =========================================================================
    # Rendering
    # =========================================================================

    def paintEvent(self, event):
        """Paint the caption overlay."""
        if not self._caption_text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Get widget dimensions
        width = self.width()
        height = self.height()

        if width < 10 or height < 10:
            return

        # Set up font
        font = self._get_font()
        painter.setFont(font)

        # Calculate text metrics
        metrics = QFontMetrics(font)

        # Handle multi-line text
        lines = self._caption_text.split('\n')
        line_height = metrics.height()
        total_text_height = line_height * len(lines)

        # Calculate vertical position based on alignment
        if self._alignment == "top":
            base_y = int(height * self._margin_percent) + metrics.ascent()
        elif self._alignment == "bottom":
            base_y = int(height * (1 - self._margin_percent)) - total_text_height + metrics.ascent()
        else:  # center
            base_y = (height - total_text_height) // 2 + metrics.ascent()

        # Draw each line
        for i, line in enumerate(lines):
            if not line.strip():
                continue

            # Calculate horizontal position (always centered)
            text_width = metrics.horizontalAdvance(line)
            x_pos = (width - text_width) // 2
            y_pos = base_y + (i * line_height)

            # Draw outline using QPainterPath
            if self._outline_width > 0:
                path = QPainterPath()
                path.addText(QPointF(x_pos, y_pos), font, line)

                outline_pen = QPen(self._outline_color, self._outline_width * 2)
                outline_pen.setJoinStyle(Qt.RoundJoin)
                outline_pen.setCapStyle(Qt.RoundCap)
                painter.strokePath(path, outline_pen)

            # Draw main text
            painter.setPen(self._font_color)
            painter.drawText(QPointF(x_pos, y_pos), line)

        painter.end()

    def _get_font(self) -> QFont:
        """Get the configured QFont object."""
        font = QFont()

        # Map font names to system fonts
        font_mappings = {
            "Arial Narrow": "Arial Narrow",
            "Arial": "Arial",
            "Impact": "Impact",
            "Verdana": "Verdana",
            "Tahoma": "Tahoma",
            "Segoe UI": "Segoe UI",
            "Consolas": "Consolas",
            "Helvetica": "Arial",  # Fallback on Windows
        }

        font_family = font_mappings.get(self._font_name, self._font_name)
        font.setFamily(font_family)
        font.setPixelSize(self._font_size)

        # Impact is typically bold
        if self._font_name.lower() == "impact":
            font.setBold(True)

        return font

    # =========================================================================
    # Geometry
    # =========================================================================

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update()
