"""
Visual Calendar Widget for Release Calendar Module

A custom calendar widget with drag-and-drop support and visual release cards.
Uses PyQt6 for the GUI components.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import calendar

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGraphicsDropShadowEffect, QSizePolicy,
    QMenu, QFileDialog, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate, QRect, QPoint, QSize, pyqtSignal, QMimeData, QPropertyAnimation, QEasingCurve, QUrl
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPalette,
    QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent,
    QPixmap, QDrag, QPainterPath, QAction
)

from .utils import logger, format_deliverable_name, days_until


class ArtworkLabel(QLabel):
    """A label that accepts artwork file drops and displays images."""
    
    artwork_dropped = pyqtSignal(str, str, str)  # artist, title, file_path
    
    def __init__(self, release: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.release = release
        self.setAcceptDrops(True)
        self.setScaledContents(True)
        self.setMinimumSize(40, 40)
        self.setMaximumSize(60, 60)
        
        # Initial display
        artwork_path = release.get('artwork_path')
        if artwork_path and Path(artwork_path).exists():
            self.set_artwork(artwork_path)
        else:
            # Show emoji if no artwork
            artist_config = release.get('artist_config', {})
            emoji = artist_config.get('emoji', '[?]')
            self.setText(emoji)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        # Visual feedback style
        self.setStyleSheet("""
            ArtworkLabel {
                border: 2px dashed transparent;
                border-radius: 4px;
                padding: 2px;
                font-size: 14px;
            }
            ArtworkLabel:hover {
                border-color: #00ffff;
                background-color: rgba(0, 255, 255, 0.1);
            }
        """)
        
    def set_artwork(self, file_path: str):
        """Set and display artwork image."""
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.setToolTip(f"Artwork: {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Failed to load artwork: {e}")
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for file drops."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                # Accept image files
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        ArtworkLabel {
                            border: 2px solid #00ff88;
                            background-color: rgba(0, 255, 136, 0.2);
                            border-radius: 4px;
                            padding: 2px;
                        }
                    """)
                    return
        event.ignore()
        
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self.setStyleSheet("""
            ArtworkLabel {
                border: 2px dashed transparent;
                border-radius: 4px;
                padding: 2px;
                font-size: 14px;
            }
            ArtworkLabel:hover {
                border-color: #00ffff;
                background-color: rgba(0, 255, 255, 0.1);
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for artwork files."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    self.set_artwork(file_path)
                    # Emit signal with artist, title, and file path
                    artist = self.release.get('artist', '')
                    title = self.release.get('title', '')
                    self.artwork_dropped.emit(artist, title, file_path)
                    event.acceptProposedAction()
                    
                    # Reset style
                    self.setStyleSheet("""
                        ArtworkLabel {
                            border: 2px dashed transparent;
                            border-radius: 4px;
                            padding: 2px;
                        }
                        ArtworkLabel:hover {
                            border-color: #00ffff;
                            background-color: rgba(0, 255, 255, 0.1);
                        }
                    """)
                    return
        event.ignore()


class DayCell(QFrame):
    """A single day cell in the calendar grid."""
    
    # Signals
    release_moved = pyqtSignal(str, str, datetime)  # artist, title, new_date
    release_added = pyqtSignal(datetime, str)  # date, artist
    artwork_updated = pyqtSignal(str, str, str)  # artist, title, path
    release_clicked = pyqtSignal(str, str)  # artist, title
    release_deleted = pyqtSignal(str, str)  # artist, title
    
    def __init__(self, date: datetime, parent=None):
        """Initialize a day cell.
        
        Args:
            date: The date this cell represents
            parent: Parent widget
        """
        super().__init__(parent)
        self.date = date
        self.releases = []
        self.deadlines = []
        self.is_current_month = True
        self.is_today = False
        self.is_friday = date.weekday() == 4
        
        self.setAcceptDrops(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the day cell UI."""
        self.setMinimumSize(180, 120)
        self.setMaximumSize(250, 200)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Header with date
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Date number
        self.date_label = QLabel(str(self.date.day))
        date_font = QFont()
        date_font.setPointSize(12)
        date_font.setBold(True)
        self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(self.date_label)
        
        # Deadline badges container
        self.deadline_layout = QHBoxLayout()
        self.deadline_layout.setSpacing(2)
        header_layout.addLayout(self.deadline_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Releases container
        self.releases_layout = QVBoxLayout()
        self.releases_layout.setSpacing(2)
        layout.addLayout(self.releases_layout)
        
        layout.addStretch()
        self.apply_style()
        
    def apply_style(self):
        """Apply BEDROT cyberpunk styling based on day type."""
        if not self.is_current_month:
            # Gray out days from other months
            self.setStyleSheet("""
                DayCell {
                    background-color: #0a0a0a;
                    border: 1px solid #2a2a2a;
                    color: #404040;
                }
            """)
            self.date_label.setStyleSheet("color: #404040;")
        elif self.is_today:
            # Highlight today with cyan glow
            self.setStyleSheet("""
                DayCell {
                    background-color: #1a1a1a;
                    border: 2px solid #00ffff;
                    box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
                }
            """)
            self.date_label.setStyleSheet("color: #00ffff; font-weight: bold;")
        elif self.is_friday:
            # Highlight Fridays (release days) with green accent
            self.setStyleSheet("""
                DayCell {
                    background-color: #1a2a1a;
                    border: 1px solid #00ff88;
                }
            """)
            self.date_label.setStyleSheet("color: #00ff88; font-weight: bold;")
        else:
            # Normal day
            self.setStyleSheet("""
                DayCell {
                    background-color: #1a1a1a;
                    border: 1px solid #404040;
                }
                DayCell:hover {
                    border: 1px solid #00ff88;
                    background-color: #222222;
                }
            """)
            
    def add_release(self, release_data: Dict[str, Any]):
        """Add a release to this day."""
        self.releases.append(release_data)
        self.update_releases_display()
        
    def on_artwork_dropped(self, artist: str, title: str, file_path: str):
        """Handle artwork drop event from ArtworkLabel."""
        # Update the release data
        for release in self.releases:
            if release.get('artist') == artist and release.get('title') == title:
                release['artwork_path'] = file_path
                break
        # Emit signal to notify parent
        self.artwork_updated.emit(artist, title, file_path)
        
    def add_deadline(self, deadline_data: Dict[str, Any]):
        """Add a deadline badge to this day."""
        self.deadlines.append(deadline_data)
        self.update_deadlines_display()
        
    def update_releases_display(self):
        """Update the visual display of releases."""
        # Clear existing release widgets
        while self.releases_layout.count():
            child = self.releases_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add release cards
        for release in self.releases[:2]:  # Show max 2 releases
            card = self.create_release_card(release)
            self.releases_layout.addWidget(card)
            
        # Add "more" indicator if needed
        if len(self.releases) > 2:
            more_label = QLabel(f"+{len(self.releases) - 2} more")
            more_label.setStyleSheet("color: #00ff88; font-size: 10px; font-weight: bold;")
            self.releases_layout.addWidget(more_label)
            
    def update_deadlines_display(self):
        """Update the deadline badges display."""
        # Clear existing deadline badges
        while self.deadline_layout.count():
            child = self.deadline_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add deadline badges (show first 3)
        for deadline in self.deadlines[:3]:
            badge = self.create_deadline_badge(deadline)
            self.deadline_layout.addWidget(badge)
            
    def create_release_card(self, release: Dict[str, Any]) -> QFrame:
        """Create a visual card for a release with BEDROT styling."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #00ffff;
                border-radius: 4px;
                padding: 4px;
            }
            QFrame:hover {
                background-color: #2a2a2a;
                border-color: #00ff88;
                box-shadow: 0 0 5px rgba(0, 255, 136, 0.3);
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Artist emoji/icon with artwork drop support
        artwork_label = ArtworkLabel(release)
        # Connect to parent's artwork update handler if available
        if hasattr(self, 'on_artwork_dropped'):
            artwork_label.artwork_dropped.connect(self.on_artwork_dropped)
        layout.addWidget(artwork_label)
        
        # Title
        title = release.get('title', 'Untitled')
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label, 1)
        
        # Progress indicator
        checklist = release.get('checklist', {})
        completed = sum(1 for item in checklist.values() if item.get('completed', False))
        total = len(checklist)
        progress_label = QLabel(f"{completed}/{total}")
        progress_label.setStyleSheet("font-size: 10px; color: #00ff88; font-weight: bold;")
        layout.addWidget(progress_label)
        
        # Store release data
        card.release_data = release
        
        # Make draggable
        card.mousePressEvent = lambda e: self.start_drag(e, release)
        card.mouseDoubleClickEvent = lambda e: self.release_clicked.emit(
            release['artist'], release['title']
        )
        
        return card
        
    def create_deadline_badge(self, deadline: Dict[str, Any]) -> QLabel:
        """Create a deadline badge with BEDROT styling."""
        days = deadline.get('days_until', 0)
        name = deadline.get('name', '')
        
        # Color based on urgency - cyberpunk style
        if days < 0:
            color = "#ff0066"  # Magenta - overdue
            text = "!"
        elif days <= 3:
            color = "#ff6600"  # Orange - urgent
            text = str(days)
        elif days <= 7:
            color = "#ffff00"  # Yellow - soon
            text = str(days)
        else:
            color = "#00ff88"  # Green - ok
            text = str(days)
            
        badge = QLabel(text)
        badge.setToolTip(f"{name}: {days} days")
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: #000000;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        return badge
        
    def start_drag(self, event: QMouseEvent, release: Dict[str, Any]):
        """Start dragging a release."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Store release data
        import json
        mime_data.setText(json.dumps({
            'artist': release['artist'],
            'title': release['title']
        }))
        
        drag.setMimeData(mime_data)
        
        # Create drag pixmap with BEDROT styling
        pixmap = QPixmap(150, 40)
        pixmap.fill(QColor("#1a1a1a"))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("#00ffff"), 2))
        painter.drawRect(0, 0, 149, 39)
        painter.setPen(QColor("#e0e0e0"))
        painter.drawText(5, 25, f"{release['artist']} - {release['title']}")
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.exec(Qt.DropAction.MoveAction)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + """
                DayCell {
                    background-color: #e8f5e9;
                    border: 2px dashed #4caf50;
                }
            """)
            
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self.apply_style()
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        if event.mimeData().hasText():
            import json
            try:
                data = json.loads(event.mimeData().text())
                artist = data.get('artist')
                title = data.get('title')
                
                if artist and title:
                    self.release_moved.emit(artist, title, self.date)
                    event.acceptProposedAction()
            except:
                pass
                
        self.apply_style()
        
    def contextMenuEvent(self, event):
        """Show context menu."""
        menu = QMenu(self)
        
        # Add release action
        add_action = QAction("Add Release", self)
        add_action.triggered.connect(lambda: self.release_added.emit(self.date, ""))
        menu.addAction(add_action)
        
        # Release-specific actions
        pos = event.pos()
        for i in range(self.releases_layout.count()):
            widget = self.releases_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'release_data'):
                if widget.geometry().contains(pos):
                    release = widget.release_data
                    menu.addSeparator()
                    
                    # Edit action
                    edit_action = QAction(f"Edit '{release['title']}'", self)
                    edit_action.triggered.connect(
                        lambda: self.release_clicked.emit(release['artist'], release['title'])
                    )
                    menu.addAction(edit_action)
                    
                    # Delete action
                    delete_action = QAction(f"Delete '{release['title']}'", self)
                    delete_action.triggered.connect(
                        lambda: self.release_deleted.emit(release['artist'], release['title'])
                    )
                    menu.addAction(delete_action)
                    break
                    
        menu.exec(event.globalPos())


class VisualCalendarWidget(QWidget):
    """Main visual calendar widget."""
    
    # Signals
    release_moved = pyqtSignal(str, str, datetime)
    release_clicked = pyqtSignal(str, str)
    release_deleted = pyqtSignal(str, str)
    release_added = pyqtSignal(datetime, str)
    artwork_updated = pyqtSignal(str, str, str)  # artist, title, file_path
    month_changed = pyqtSignal(int, int)  # year, month
    
    def __init__(self, parent=None):
        """Initialize the visual calendar widget."""
        super().__init__(parent)
        self.current_date = datetime.now()
        self.day_cells = {}  # date -> DayCell mapping
        self.releases_data = {}  # artist -> releases mapping
        self.config = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the calendar UI."""
        layout = QVBoxLayout(self)
        
        # Header with navigation
        header = self.create_header()
        layout.addWidget(header)
        
        # Calendar grid
        self.calendar_widget = QWidget()
        self.calendar_layout = QGridLayout(self.calendar_widget)
        self.calendar_layout.setSpacing(2)
        
        # Add day headers with BEDROT styling
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            label = QLabel(day[:3].upper())
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i == 4:  # Friday - release day
                label.setStyleSheet("font-weight: bold; padding: 5px; color: #00ff88; background-color: #0a0a0a; text-transform: uppercase;")
            else:
                label.setStyleSheet("font-weight: bold; padding: 5px; color: #00ffff; background-color: #0a0a0a; text-transform: uppercase;")
            self.calendar_layout.addWidget(label, 0, i)
            
        # Scroll area for calendar
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.calendar_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area, 1)
        
        # Initial calendar display
        self.update_calendar()
        
    def create_header(self) -> QWidget:
        """Create the calendar header with navigation."""
        header = QWidget()
        layout = QHBoxLayout(header)
        
        # Previous month button
        prev_btn = QPushButton("◀ PREV")
        prev_btn.clicked.connect(self.previous_month)
        layout.addWidget(prev_btn)
        
        # Month/Year label
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setStyleSheet("color: #00ffff; font-size: 18px; font-weight: bold; text-transform: uppercase;")
        layout.addWidget(self.month_label, 1)
        
        # Next month button
        next_btn = QPushButton("NEXT ▶")
        next_btn.clicked.connect(self.next_month)
        layout.addWidget(next_btn)
        
        # Today button
        today_btn = QPushButton("TODAY")
        today_btn.setObjectName("primaryButton")
        today_btn.clicked.connect(self.go_to_today)
        layout.addWidget(today_btn)
        
        return header
        
    def previous_month(self):
        """Navigate to previous month."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(
                year=self.current_date.year - 1, month=12
            )
        else:
            self.current_date = self.current_date.replace(
                month=self.current_date.month - 1
            )
        self.update_calendar()
        self.month_changed.emit(self.current_date.year, self.current_date.month)
        
    def next_month(self):
        """Navigate to next month."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(
                year=self.current_date.year + 1, month=1
            )
        else:
            self.current_date = self.current_date.replace(
                month=self.current_date.month + 1
            )
        self.update_calendar()
        self.month_changed.emit(self.current_date.year, self.current_date.month)
        
    def go_to_today(self):
        """Navigate to current month."""
        self.current_date = datetime.now()
        self.update_calendar()
        self.month_changed.emit(self.current_date.year, self.current_date.month)
        
    def update_calendar(self):
        """Update the calendar display."""
        # Clear existing cells
        self.day_cells.clear()
        for i in reversed(range(self.calendar_layout.count())):
            widget = self.calendar_layout.itemAt(i).widget()
            if widget and not isinstance(widget, QLabel):
                widget.deleteLater()
                
        # Update month label
        self.month_label.setText(
            self.current_date.strftime("%B %Y")
        )
        
        # Get calendar info
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        today = datetime.now().date()
        
        # Create day cells
        for week_num, week in enumerate(cal, start=1):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Empty cell for days from other months
                    continue
                    
                # Create date object
                date = datetime(self.current_date.year, self.current_date.month, day)
                
                # Create day cell
                cell = DayCell(date)
                cell.is_current_month = True
                cell.is_today = date.date() == today
                cell.apply_style()
                
                # Connect signals
                cell.release_moved.connect(self.release_moved)
                cell.release_clicked.connect(self.release_clicked)
                cell.release_deleted.connect(self.release_deleted)
                cell.release_added.connect(self.release_added)
                cell.artwork_updated.connect(self.on_artwork_updated)
                
                # Add to grid
                self.calendar_layout.addWidget(cell, week_num, day_num)
                self.day_cells[date.date()] = cell
                
        # Populate with release data
        self.populate_releases()
        
    def on_artwork_updated(self, artist: str, title: str, file_path: str):
        """Handle artwork update from day cell."""
        # Forward the signal to parent
        self.artwork_updated.emit(artist, title, file_path)
        
    def populate_releases(self):
        """Populate the calendar with release data."""
        for artist, releases in self.releases_data.items():
            artist_config = self.config.get('artists', {}).get(artist, {})
            
            for release in releases:
                # Parse release date
                release_date = release.get('release_date')
                if isinstance(release_date, str):
                    release_date = datetime.fromisoformat(release_date)
                    
                # Add to appropriate day cell
                if release_date.date() in self.day_cells:
                    release_with_config = release.copy()
                    release_with_config['artist'] = artist  # Add the artist name
                    release_with_config['artist_config'] = artist_config
                    self.day_cells[release_date.date()].add_release(release_with_config)
                    
                # Add deadline badges
                checklist = release.get('checklist', {})
                for deliverable, details in checklist.items():
                    if not details.get('completed', False):
                        due_date = details.get('due_date')
                        if isinstance(due_date, str):
                            due_date = datetime.fromisoformat(due_date)
                            
                        if due_date.date() in self.day_cells:
                            days = days_until(due_date)
                            self.day_cells[due_date.date()].add_deadline({
                                'name': format_deliverable_name(deliverable),
                                'days_until': days,
                                'artist': artist,
                                'release': release.get('title')
                            })
                            
    def set_releases_data(self, releases_data: Dict[str, List[Dict]], config: Dict):
        """Set the release data to display."""
        self.releases_data = releases_data
        self.config = config
        self.update_calendar()