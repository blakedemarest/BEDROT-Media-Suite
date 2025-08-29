"""Live preview widget for real-time caption rendering."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF, QUrl
from PyQt5.QtGui import QPainter, QFont, QColor, QBrush, QPen, QFontMetrics, QImage, QPainterPath
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

try:
    from .utils import safe_print
    from .font_manager import get_font_manager
except ImportError:
    from mv_maker.utils import safe_print
    from mv_maker.font_manager import get_font_manager


class CaptionOverlay(QWidget):
    """Transparent overlay widget for rendering captions."""
    
    def __init__(self, parent=None):
        """Initialize caption overlay."""
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Caption properties
        self.caption_text = "Preview Caption Text"
        self.font_family = 'arial'
        self.font_size = 24
        self.font_color = QColor('#FFFFFF')
        self.background_color = QColor('#000000')
        self.background_opacity = 0.7
        self.position_x = 50  # Percentage
        self.position_y = 85  # Percentage
        self.text_align = 'center'
        self.vertical_align = 'bottom'
        self.shadow_enabled = True
        self.border_width = 2
        
        # Font manager
        self.font_manager = get_font_manager()
        
        # Update timer for smooth animations
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(33)  # ~30 FPS
        
    def set_caption_text(self, text: str):
        """Set the caption text to display."""
        if self.caption_text != text:
            self.caption_text = text
            self.update()
    
    def set_font_family(self, font_key: str):
        """Set the font family."""
        if self.font_family != font_key:
            self.font_family = font_key
            self.update()
    
    def set_font_size(self, size: int):
        """Set the font size."""
        if self.font_size != size:
            self.font_size = size
            self.update()
    
    def set_font_color(self, color: str):
        """Set the font color."""
        self.font_color = QColor(color)
        self.update()
    
    def set_background_color(self, color: str):
        """Set the background color."""
        self.background_color = QColor(color)
        self.update()
    
    def set_background_opacity(self, opacity: float):
        """Set the background opacity (0.0 to 1.0)."""
        self.background_opacity = opacity
        self.update()
    
    def set_position(self, x: float, y: float):
        """Set the caption position as percentage."""
        self.position_x = x
        self.position_y = y
        self.update()
    
    def set_alignment(self, horizontal: str, vertical: str):
        """Set text alignment."""
        self.text_align = horizontal
        self.vertical_align = vertical
        self.update()
    
    def set_shadow_enabled(self, enabled: bool):
        """Enable or disable text shadow."""
        self.shadow_enabled = enabled
        self.update()
    
    def set_border_width(self, width: int):
        """Set the border width."""
        self.border_width = width
        self.update()
    
    def paintEvent(self, event):
        """Paint the caption overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        if not self.caption_text:
            return
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Set up font
        font = QFont()
        
        # Get appropriate font name for the platform
        font_display_name = self.font_manager.FONT_MAPPINGS.get(
            self.font_family, {}
        ).get('display_name', 'Arial')
        
        font.setFamily(font_display_name)
        font.setPixelSize(self.font_size)
        font.setBold(self.font_family == 'impact')
        painter.setFont(font)
        
        # Calculate text metrics
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(self.caption_text)
        
        # Calculate position based on percentage
        x_pos = (width * self.position_x / 100)
        y_pos = (height * self.position_y / 100)
        
        # Adjust for alignment
        if self.text_align == 'center':
            x_pos -= text_rect.width() / 2
        elif self.text_align == 'right':
            x_pos -= text_rect.width()
        
        if self.vertical_align == 'middle':
            y_pos -= text_rect.height() / 2
        elif self.vertical_align == 'top':
            y_pos += text_rect.height()
        
        # Create text rectangle with padding
        padding = 10
        bg_rect = QRectF(
            x_pos - padding,
            y_pos - text_rect.height() - padding,
            text_rect.width() + 2 * padding,
            text_rect.height() + 2 * padding
        )
        
        # Draw background
        bg_color = QColor(self.background_color)
        bg_color.setAlphaF(self.background_opacity)
        painter.fillRect(bg_rect, bg_color)
        
        # Draw shadow if enabled
        if self.shadow_enabled:
            shadow_color = QColor(0, 0, 0, 180)
            painter.setPen(shadow_color)
            painter.drawText(QPointF(x_pos + 2, y_pos + 2), self.caption_text)
        
        # Draw border/outline if enabled
        if self.border_width > 0:
            # Create text path for border
            path = QPainterPath()
            path.addText(QPointF(x_pos, y_pos), font, self.caption_text)
            
            # Draw border
            border_pen = QPen(QColor(0, 0, 0), self.border_width)
            border_pen.setJoinStyle(Qt.RoundJoin)
            painter.strokePath(path, border_pen)
        
        # Draw main text
        painter.setPen(self.font_color)
        painter.drawText(QPointF(x_pos, y_pos), self.caption_text)


class LivePreviewWidget(QWidget):
    """Widget for live video preview with caption overlay."""
    
    # Signals
    position_clicked = pyqtSignal(float, float)  # x%, y%
    
    def __init__(self, parent=None):
        """Initialize live preview widget."""
        super().__init__(parent)
        
        self.video_path = None
        self.is_audio_only = False
        self.background_image = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 360)
        self.video_widget.setStyleSheet("background-color: black;")
        
        # Create media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
        # Create caption overlay
        self.caption_overlay = CaptionOverlay(self.video_widget)
        
        # Add video widget to layout
        layout.addWidget(self.video_widget)
        
        # Info label
        self.info_label = QLabel("Drop a video or audio file to preview")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
        
        # Connect media player signals
        self.media_player.stateChanged.connect(self.on_state_changed)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        
        # Enable click position detection
        self.video_widget.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """Filter events to detect clicks on video widget."""
        if obj == self.video_widget and event.type() == event.MouseButtonPress:
            # Calculate click position as percentage
            x_percent = (event.x() / self.video_widget.width()) * 100
            y_percent = (event.y() / self.video_widget.height()) * 100
            self.position_clicked.emit(x_percent, y_percent)
            return True
        return super().eventFilter(obj, event)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        # Resize overlay to match video widget
        if hasattr(self, 'caption_overlay'):
            self.caption_overlay.resize(self.video_widget.size())
    
    def load_media(self, file_path: str):
        """Load media file for preview."""
        self.video_path = file_path
        file_ext = Path(file_path).suffix.lower()
        
        # Check if audio file
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma']
        self.is_audio_only = file_ext in audio_extensions
        
        if self.is_audio_only:
            # For audio files, show static background
            self.show_audio_visualization()
            self.info_label.setText(f"Audio: {Path(file_path).name}")
        else:
            # Load video
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.media_player.play()
            self.media_player.pause()  # Pause immediately to show first frame
            self.info_label.setText(f"Video: {Path(file_path).name}")
    
    def show_audio_visualization(self):
        """Show visualization for audio-only files."""
        # Create a simple waveform or static image
        # For now, just show a black background with text
        self.video_widget.setStyleSheet("""
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #1a1a1a, stop: 1 #2d2d2d
            );
        """)
    
    def play_pause(self):
        """Toggle play/pause."""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def seek(self, position: int):
        """Seek to position in milliseconds."""
        self.media_player.setPosition(position)
    
    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        self.media_player.setVolume(volume)
    
    def on_state_changed(self, state):
        """Handle media player state changes."""
        pass
    
    def on_position_changed(self, position):
        """Handle position changes."""
        pass
    
    def on_duration_changed(self, duration):
        """Handle duration changes."""
        pass
    
    # Caption control methods
    def update_caption_text(self, text: str):
        """Update preview caption text."""
        self.caption_overlay.set_caption_text(text)
    
    def update_caption_style(self, style_dict: Dict):
        """Update caption style from dictionary."""
        if 'font_family' in style_dict:
            self.caption_overlay.set_font_family(style_dict['font_family'])
        if 'font_size' in style_dict:
            self.caption_overlay.set_font_size(style_dict['font_size'])
        if 'font_color' in style_dict:
            self.caption_overlay.set_font_color(style_dict['font_color'])
        if 'background_color' in style_dict:
            self.caption_overlay.set_background_color(style_dict['background_color'])
        if 'background_opacity' in style_dict:
            self.caption_overlay.set_background_opacity(style_dict['background_opacity'])
        if 'shadow_enabled' in style_dict:
            self.caption_overlay.set_shadow_enabled(style_dict['shadow_enabled'])
        if 'border_width' in style_dict:
            self.caption_overlay.set_border_width(style_dict['border_width'])
    
    def update_caption_position(self, x: float, y: float):
        """Update caption position."""
        self.caption_overlay.set_position(x, y)
    
    def update_caption_alignment(self, horizontal: str, vertical: str):
        """Update caption alignment."""
        self.caption_overlay.set_alignment(horizontal, vertical)
    
    def get_current_frame(self) -> Optional[QImage]:
        """Get current video frame as QImage."""
        # This would require more complex implementation with QVideoProbe
        # For now, return None
        return None
    
    def set_background_for_audio(self, bg_type: str, bg_value: str):
        """Set background for audio-only preview."""
        if bg_type == 'solid':
            self.video_widget.setStyleSheet(f"background-color: {bg_value};")
        elif bg_type == 'gradient':
            # Parse gradient colors
            colors = bg_value.split(',')
            if len(colors) == 2:
                self.video_widget.setStyleSheet(f"""
                    background-color: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 {colors[0]}, stop: 1 {colors[1]}
                    );
                """)
        elif bg_type == 'image' and os.path.exists(bg_value):
            # Would need to implement image background
            pass