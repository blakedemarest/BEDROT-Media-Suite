# -*- coding: utf-8 -*-
"""
Preview Widget for Caption Generator.

Right panel showing a live preview of caption styling.
Uses PIL/Pillow for text rendering, updates on style changes.
"""

from typing import Optional, Dict
import io

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PreviewWidget(QWidget):
    """
    Right panel showing live preview of caption styling.

    Features:
    - Real-time preview of text with current style settings
    - Debounced updates (100ms delay) to prevent excessive re-rendering
    - Supports solid background or transparent checkerboard pattern
    - Scales preview to fit widget while maintaining aspect ratio
    """

    preview_error = pyqtSignal(str)  # Emitted on rendering errors

    def __init__(self, parent=None):
        super().__init__(parent)

        # Current settings
        self._settings: Dict = {
            "font_name": "Arial",
            "font_size": 56,
            "font_color": "#ffffff",
            "background_color": "#000000",
            "resolution": "1920x1080",
            "alignment": "center",
            "transparent": False,
        }
        self._current_text: str = "Preview Text"

        # Debounce timer
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_render)
        self._update_pending = False

        self._setup_ui()
        self._apply_theme()

        # Initial render
        self._schedule_update()

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

        # Preview frame
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(4, 4, 4, 4)

        # Preview image label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 150)
        self.preview_label.setStyleSheet("background-color: transparent;")
        preview_layout.addWidget(self.preview_label, 1)

        layout.addWidget(self.preview_frame, 1)

        # Status label
        self.status_label = QLabel("Ready")
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
        """)

    def _schedule_update(self):
        """Schedule a debounced update (100ms delay)."""
        self._update_pending = True
        self._update_timer.start(100)

    def _do_render(self):
        """Actually perform the rendering."""
        self._update_pending = False

        if not PIL_AVAILABLE:
            self.status_label.setText("PIL not available")
            self.preview_error.emit("PIL/Pillow not installed")
            return

        try:
            pixmap = self._render_preview()
            if pixmap:
                # Scale to fit the label while maintaining aspect ratio
                scaled = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)
                self.status_label.setText(f"{self._settings['resolution']} - {self._settings['alignment'].title()}")
            else:
                self.status_label.setText("Render failed")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)[:30]}")
            self.preview_error.emit(str(e))

    def _render_preview(self) -> Optional[QPixmap]:
        """
        Render the preview image using PIL.

        Returns:
            QPixmap of the rendered preview, or None on error
        """
        try:
            # Parse resolution
            resolution = self._settings.get("resolution", "1920x1080")
            width, height = map(int, resolution.split('x'))

            # Scale down for preview (max 800px wide)
            scale = min(800 / width, 600 / height, 1.0)
            preview_width = int(width * scale)
            preview_height = int(height * scale)

            # Create image
            if self._settings.get("transparent", False):
                # Create checkerboard pattern for transparent preview
                img = self._create_checkerboard(preview_width, preview_height)
            else:
                # Solid background
                bg_color = self._settings.get("background_color", "#000000")
                img = Image.new("RGB", (preview_width, preview_height), bg_color)

            draw = ImageDraw.Draw(img)

            # Get font
            font_name = self._settings.get("font_name", "Arial")
            font_size = int(self._settings.get("font_size", 56) * scale)
            font = self._get_font(font_name, font_size)

            # Get text color
            text_color = self._settings.get("font_color", "#ffffff")

            # Draw text with alignment
            self._draw_centered_text(
                draw, img, self._current_text, font, text_color,
                self._settings.get("alignment", "center")
            )

            # Convert PIL image to QPixmap
            return self._pil_to_pixmap(img)

        except Exception as e:
            print(f"[Preview] Render error: {e}")
            return None

    def _create_checkerboard(self, width: int, height: int, block_size: int = 16) -> Image.Image:
        """Create a checkerboard pattern to indicate transparency."""
        img = Image.new("RGB", (width, height))
        pixels = img.load()

        colors = [(40, 40, 40), (60, 60, 60)]  # Dark gray checkerboard

        for y in range(height):
            for x in range(width):
                color_idx = ((x // block_size) + (y // block_size)) % 2
                pixels[x, y] = colors[color_idx]

        return img

    def _get_font(self, font_name: str, font_size: int) -> ImageFont.FreeTypeFont:
        """
        Get a PIL font object.

        Tries system fonts, falls back to default if not found.
        """
        # Common Windows font paths
        font_paths = [
            f"C:/Windows/Fonts/{font_name}.ttf",
            f"C:/Windows/Fonts/{font_name.replace(' ', '')}.ttf",
            f"C:/Windows/Fonts/{font_name.lower()}.ttf",
            f"C:/Windows/Fonts/{font_name.lower().replace(' ', '')}.ttf",
        ]

        # Special mappings for common fonts
        font_mappings = {
            "Arial Narrow": "arialn.ttf",
            "Arial": "arial.ttf",
            "Helvetica": "arial.ttf",  # Fallback
            "Impact": "impact.ttf",
            "Verdana": "verdana.ttf",
            "Tahoma": "tahoma.ttf",
            "Segoe UI": "segoeui.ttf",
            "Consolas": "consola.ttf",
        }

        if font_name in font_mappings:
            font_paths.insert(0, f"C:/Windows/Fonts/{font_mappings[font_name]}")

        for path in font_paths:
            try:
                return ImageFont.truetype(path, font_size)
            except (OSError, IOError):
                continue

        # Fallback to default font
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            return ImageFont.load_default()

    def _draw_centered_text(
        self, draw: ImageDraw.Draw, img: Image.Image,
        text: str, font: ImageFont.FreeTypeFont, color: str, alignment: str
    ):
        """Draw text with the specified alignment."""
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        img_width, img_height = img.size

        # Horizontal: always centered
        x = (img_width - text_width) // 2

        # Vertical: based on alignment
        if alignment == "top":
            y = int(img_height * 0.1)  # 10% from top
        elif alignment == "bottom":
            y = int(img_height * 0.85) - text_height  # 15% from bottom
        else:  # center
            y = (img_height - text_height) // 2

        # Draw outline (black)
        outline_color = "#000000"
        outline_width = 2
        for ox in range(-outline_width, outline_width + 1):
            for oy in range(-outline_width, outline_width + 1):
                if ox != 0 or oy != 0:
                    draw.text((x + ox, y + oy), text, font=font, fill=outline_color)

        # Draw main text
        draw.text((x, y), text, font=font, fill=color)

    def _pil_to_pixmap(self, img: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap."""
        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Get image data
        data = img.tobytes("raw", "RGB")

        # Create QImage
        qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)

        # Convert to QPixmap
        return QPixmap.fromImage(qimg)

    # =========================================================================
    # Public API
    # =========================================================================

    def update_settings(self, settings: Dict):
        """
        Update style settings and schedule a preview update.

        Args:
            settings: Dictionary of style settings
        """
        self._settings.update(settings)
        self._schedule_update()

    def set_text(self, text: str):
        """
        Set the preview text.

        Args:
            text: Text to display in preview
        """
        if text and text.strip():
            self._current_text = text.strip()
        else:
            self._current_text = "Preview Text"
        self._schedule_update()

    def set_font(self, font_name: str, font_size: int):
        """Set font settings."""
        self._settings["font_name"] = font_name
        self._settings["font_size"] = font_size
        self._schedule_update()

    def set_colors(self, text_color: str, bg_color: str):
        """Set color settings."""
        self._settings["font_color"] = text_color
        self._settings["background_color"] = bg_color
        self._schedule_update()

    def set_alignment(self, alignment: str):
        """Set text alignment."""
        self._settings["alignment"] = alignment
        self._schedule_update()

    def set_resolution(self, resolution: str):
        """Set video resolution (affects preview aspect ratio)."""
        self._settings["resolution"] = resolution
        self._schedule_update()

    def set_transparent(self, transparent: bool):
        """Set transparent background mode."""
        self._settings["transparent"] = transparent
        self._schedule_update()

    def force_update(self):
        """Force an immediate preview update (bypasses debounce)."""
        self._update_timer.stop()
        self._do_render()

    def resizeEvent(self, event):
        """Handle resize to re-render preview at new size."""
        super().resizeEvent(event)
        self._schedule_update()

    def sizeHint(self) -> QSize:
        """Return preferred size."""
        return QSize(400, 300)
