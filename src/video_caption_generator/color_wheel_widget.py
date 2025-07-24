"""Color wheel widget for advanced color selection."""

import sys
import math
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QPen, QConicalGradient,
    QRadialGradient, QPainterPath, QLinearGradient
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QLineEdit, QPushButton, QGridLayout,
    QFrame
)


class ColorWheelWidget(QWidget):
    """Custom color wheel widget for intuitive color selection."""
    
    # Signal emitted when color changes
    colorChanged = pyqtSignal(str)  # Emits hex color string
    
    def __init__(self, parent=None):
        """Initialize color wheel widget."""
        super().__init__(parent)
        
        # Current color
        self.current_color = QColor('#FFFFFF')
        
        # Wheel parameters
        self.wheel_radius = 100
        self.inner_radius = 80
        self.selector_radius = 8
        
        # Current HSV values
        self.hue = 0
        self.saturation = 0
        self.value = 100
        self.alpha = 255
        
        # Dragging state
        self.dragging_wheel = False
        self.dragging_square = False
        
        # Update timer for smooth color transitions
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._emit_color_change)
        self.update_timer.setSingleShot(True)
        
        self.init_ui()
        self.setMinimumSize(300, 400)
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Color wheel area
        self.wheel_widget = QWidget()
        self.wheel_widget.setMinimumHeight(220)
        layout.addWidget(self.wheel_widget)
        
        # Value (brightness) slider
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_layout.addWidget(self.brightness_slider)
        
        self.brightness_label = QLabel("100%")
        self.brightness_label.setMinimumWidth(40)
        brightness_layout.addWidget(self.brightness_label)
        
        layout.addLayout(brightness_layout)
        
        # Alpha (opacity) slider
        alpha_layout = QHBoxLayout()
        alpha_layout.addWidget(QLabel("Opacity:"))
        
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(100)
        self.alpha_slider.valueChanged.connect(self._on_alpha_changed)
        alpha_layout.addWidget(self.alpha_slider)
        
        self.alpha_label = QLabel("100%")
        self.alpha_label.setMinimumWidth(40)
        alpha_layout.addWidget(self.alpha_label)
        
        layout.addLayout(alpha_layout)
        
        # Color display and hex input
        color_info_layout = QHBoxLayout()
        
        # Color preview
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(60, 30)
        self.color_preview.setFrameStyle(QFrame.Box)
        self.color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")
        color_info_layout.addWidget(self.color_preview)
        
        # Hex input
        self.hex_input = QLineEdit("#FFFFFF")
        self.hex_input.setMaxLength(7)
        self.hex_input.textChanged.connect(self._on_hex_changed)
        color_info_layout.addWidget(self.hex_input)
        
        # RGB display
        self.rgb_label = QLabel("RGB: 255, 255, 255")
        color_info_layout.addWidget(self.rgb_label)
        
        layout.addLayout(color_info_layout)
        
        # Preset colors
        preset_layout = QGridLayout()
        preset_colors = [
            '#FFFFFF', '#000000', '#FF0000', '#00FF00', '#0000FF',
            '#FFFF00', '#FF00FF', '#00FFFF', '#808080', '#C0C0C0',
            '#800000', '#808000', '#008000', '#800080', '#008080',
            '#000080', '#FFA500', '#A52A2A', '#DDA0DD', '#90EE90'
        ]
        
        for i, color in enumerate(preset_colors):
            btn = QPushButton()
            btn.setFixedSize(25, 25)
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
            btn.clicked.connect(lambda checked, c=color: self.set_color(c))
            preset_layout.addWidget(btn, i // 5, i % 5)
        
        layout.addLayout(preset_layout)
        
        # Recent colors (placeholder)
        recent_label = QLabel("Recent Colors:")
        layout.addWidget(recent_label)
        
        self.recent_layout = QHBoxLayout()
        layout.addLayout(self.recent_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def paintEvent(self, event):
        """Paint the color wheel."""
        super().paintEvent(event)
        
        painter = QPainter(self.wheel_widget)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate center
        center_x = self.wheel_widget.width() // 2
        center_y = self.wheel_widget.height() // 2
        center = QPointF(center_x, center_y)
        
        # Draw HSV color wheel
        self._draw_color_wheel(painter, center)
        
        # Draw brightness square in center
        self._draw_brightness_square(painter, center)
        
        # Draw selector
        self._draw_selector(painter, center)
    
    def _draw_color_wheel(self, painter: QPainter, center: QPointF):
        """Draw the HSV color wheel."""
        # Create conical gradient for hue
        hue_gradient = QConicalGradient(center, 0)
        
        # Add color stops for full hue range
        for angle in range(0, 360, 30):
            color = QColor.fromHsv(angle, 255, 255)
            hue_gradient.setColorAt(angle / 360.0, color)
        
        # Draw outer circle
        painter.setBrush(QBrush(hue_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, self.wheel_radius, self.wheel_radius)
        
        # Create radial gradient for saturation (white to transparent)
        sat_gradient = QRadialGradient(center, self.wheel_radius)
        sat_gradient.setColorAt(0, QColor(255, 255, 255, 255))
        sat_gradient.setColorAt(0.7, QColor(255, 255, 255, 0))
        sat_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        # Draw saturation overlay
        painter.setBrush(QBrush(sat_gradient))
        painter.drawEllipse(center, self.wheel_radius, self.wheel_radius)
        
        # Draw inner circle (cut out center)
        painter.setBrush(QBrush(self.palette().window().color()))
        painter.drawEllipse(center, self.inner_radius, self.inner_radius)
    
    def _draw_brightness_square(self, painter: QPainter, center: QPointF):
        """Draw brightness/value square in center."""
        square_size = self.inner_radius * 1.4
        square_rect = QRectF(
            center.x() - square_size/2,
            center.y() - square_size/2,
            square_size,
            square_size
        )
        
        # Draw gradient from selected color to black
        color_at_full = QColor.fromHsv(int(self.hue), int(self.saturation * 255), 255)
        
        # Horizontal gradient (white to color)
        h_gradient = QLinearGradient(square_rect.topLeft(), square_rect.topRight())
        h_gradient.setColorAt(0, Qt.white)
        h_gradient.setColorAt(1, color_at_full)
        
        painter.fillRect(square_rect, h_gradient)
        
        # Vertical gradient (transparent to black)
        v_gradient = QLinearGradient(square_rect.topLeft(), square_rect.bottomLeft())
        v_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        v_gradient.setColorAt(1, Qt.black)
        
        painter.fillRect(square_rect, v_gradient)
        
        # Draw border
        painter.setPen(QPen(Qt.gray, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(square_rect)
    
    def _draw_selector(self, painter: QPainter, center: QPointF):
        """Draw the color selector."""
        # Calculate selector position on wheel
        if self.saturation > 0:
            angle = math.radians(self.hue)
            radius = self.inner_radius + (self.wheel_radius - self.inner_radius) * self.saturation
            wheel_x = center.x() + radius * math.cos(angle)
            wheel_y = center.y() + radius * math.sin(angle)
            
            # Draw wheel selector
            painter.setPen(QPen(Qt.white, 2))
            painter.setBrush(QBrush(self.current_color))
            painter.drawEllipse(QPointF(wheel_x, wheel_y), self.selector_radius, self.selector_radius)
        
        # Calculate selector position in square
        square_size = self.inner_radius * 1.4
        square_x = center.x() - square_size/2 + square_size * (self.saturation if self.saturation > 0 else 0.5)
        square_y = center.y() - square_size/2 + square_size * (1 - self.value / 100.0)
        
        # Draw square selector
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(QBrush(self.current_color))
        painter.drawEllipse(QPointF(square_x, square_y), self.selector_radius/2, self.selector_radius/2)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() != Qt.LeftButton:
            return
        
        # Check if click is in wheel or square
        center_x = self.wheel_widget.width() // 2
        center_y = self.wheel_widget.height() // 2
        
        # Map click to wheel widget coordinates
        click_x = event.x()
        click_y = event.y() - self.wheel_widget.y()
        
        dx = click_x - center_x
        dy = click_y - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Check if in color wheel
        if self.inner_radius <= distance <= self.wheel_radius:
            self.dragging_wheel = True
            self._update_from_wheel(click_x, click_y)
        
        # Check if in brightness square
        square_size = self.inner_radius * 1.4
        if (abs(dx) <= square_size/2 and abs(dy) <= square_size/2):
            self.dragging_square = True
            self._update_from_square(click_x, click_y)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if not (self.dragging_wheel or self.dragging_square):
            return
        
        # Map to wheel widget coordinates
        click_x = event.x()
        click_y = event.y() - self.wheel_widget.y()
        
        if self.dragging_wheel:
            self._update_from_wheel(click_x, click_y)
        elif self.dragging_square:
            self._update_from_square(click_x, click_y)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        self.dragging_wheel = False
        self.dragging_square = False
    
    def _update_from_wheel(self, x: int, y: int):
        """Update color from wheel position."""
        center_x = self.wheel_widget.width() // 2
        center_y = self.wheel_widget.height() // 2
        
        dx = x - center_x
        dy = y - center_y
        
        # Calculate angle (hue)
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        self.hue = angle
        
        # Calculate distance (saturation)
        distance = math.sqrt(dx*dx + dy*dy)
        distance = max(self.inner_radius, min(distance, self.wheel_radius))
        self.saturation = (distance - self.inner_radius) / (self.wheel_radius - self.inner_radius)
        
        self._update_color()
    
    def _update_from_square(self, x: int, y: int):
        """Update color from square position."""
        center_x = self.wheel_widget.width() // 2
        center_y = self.wheel_widget.height() // 2
        square_size = self.inner_radius * 1.4
        
        # Normalize to 0-1 range
        norm_x = (x - (center_x - square_size/2)) / square_size
        norm_y = (y - (center_y - square_size/2)) / square_size
        
        norm_x = max(0, min(1, norm_x))
        norm_y = max(0, min(1, norm_y))
        
        # Update saturation and value
        self.saturation = norm_x
        self.value = int((1 - norm_y) * 100)
        
        self._update_color()
    
    def _update_color(self):
        """Update the current color from HSV values."""
        self.current_color = QColor.fromHsv(
            int(self.hue),
            int(self.saturation * 255),
            int(self.value * 2.55)
        )
        self.current_color.setAlpha(self.alpha)
        
        # Update UI elements
        self._update_ui()
        
        # Schedule color change signal
        self.update_timer.stop()
        self.update_timer.start(50)  # 50ms debounce
        
        # Trigger repaint
        self.update()
    
    def _update_ui(self):
        """Update UI elements to reflect current color."""
        # Update color preview
        self.color_preview.setStyleSheet(
            f"background-color: {self.current_color.name()}; border: 1px solid #ccc;"
        )
        
        # Update hex input
        self.hex_input.blockSignals(True)
        self.hex_input.setText(self.current_color.name())
        self.hex_input.blockSignals(False)
        
        # Update RGB label
        self.rgb_label.setText(
            f"RGB: {self.current_color.red()}, "
            f"{self.current_color.green()}, "
            f"{self.current_color.blue()}"
        )
        
        # Update brightness label
        self.brightness_label.setText(f"{self.value}%")
        
        # Update alpha label
        alpha_percent = int((self.alpha / 255) * 100)
        self.alpha_label.setText(f"{alpha_percent}%")
    
    def _emit_color_change(self):
        """Emit color change signal."""
        self.colorChanged.emit(self.current_color.name())
    
    def _on_brightness_changed(self, value: int):
        """Handle brightness slider change."""
        self.value = value
        self._update_color()
    
    def _on_alpha_changed(self, value: int):
        """Handle alpha slider change."""
        self.alpha = int((value / 100) * 255)
        self._update_color()
    
    def _on_hex_changed(self, text: str):
        """Handle hex input change."""
        if len(text) == 7 and text.startswith('#'):
            try:
                color = QColor(text)
                if color.isValid():
                    self.set_color(text)
            except:
                pass
    
    def set_color(self, color: str):
        """Set the current color."""
        qcolor = QColor(color)
        if not qcolor.isValid():
            return
        
        # Convert to HSV
        self.hue = qcolor.hue() if qcolor.hue() >= 0 else 0
        self.saturation = qcolor.saturation() / 255.0
        self.value = int((qcolor.value() / 255.0) * 100)
        self.alpha = qcolor.alpha()
        
        # Update sliders
        self.brightness_slider.blockSignals(True)
        self.brightness_slider.setValue(self.value)
        self.brightness_slider.blockSignals(False)
        
        alpha_percent = int((self.alpha / 255) * 100)
        self.alpha_slider.blockSignals(True)
        self.alpha_slider.setValue(alpha_percent)
        self.alpha_slider.blockSignals(False)
        
        self._update_color()
    
    def get_color(self) -> str:
        """Get the current color as hex string."""
        return self.current_color.name()
    
    def get_color_with_alpha(self) -> str:
        """Get the current color with alpha as RGBA string."""
        return (f"rgba({self.current_color.red()}, "
                f"{self.current_color.green()}, "
                f"{self.current_color.blue()}, "
                f"{self.current_color.alphaF():.2f})")
    
    def add_to_recent(self, color: str):
        """Add color to recent colors (placeholder for now)."""
        # This could be implemented to show recent color selections
        pass