"""
Release Checklist Dialog for Release Calendar Module

Interactive checklist for tracking release deliverables with PyQt6.
"""

from datetime import datetime
from typing import Dict, Optional, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QTextEdit, QProgressBar, QScrollArea, QWidget,
    QFrame, QGridLayout, QGroupBox, QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from .utils import format_deliverable_name, days_until


class ChecklistItem(QFrame):
    """Individual checklist item with checkbox and details."""
    
    state_changed = pyqtSignal(str, dict)  # deliverable_name, new_state
    
    def __init__(self, deliverable_name: str, state: dict, release_date: datetime, parent=None):
        """Initialize a checklist item.
        
        Args:
            deliverable_name: Name of the deliverable
            state: Current state dictionary
            release_date: Release date for calculating deadlines
            parent: Parent widget
        """
        super().__init__(parent)
        self.deliverable_name = deliverable_name
        self.state = state.copy()
        self.release_date = release_date
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the checklist item UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            ChecklistItem {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.state.get('completed', False))
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox)
        
        # Task details
        details_layout = QVBoxLayout()
        
        # Task name
        task_label = QLabel(format_deliverable_name(self.deliverable_name))
        task_font = QFont()
        task_font.setBold(True)
        task_label.setFont(task_font)
        details_layout.addWidget(task_label)
        
        # Due date and status
        status_layout = QHBoxLayout()
        
        # Parse due date
        due_date = self.state.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
            
        due_date_str = due_date.strftime('%B %d, %Y')
        due_label = QLabel(f"Due: {due_date_str}")
        
        # Calculate status
        status_text, status_color = self.calculate_status(due_date)
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        
        status_layout.addWidget(due_label)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        details_layout.addLayout(status_layout)
        
        # Completion info
        if self.state.get('completed') and self.state.get('completed_date'):
            completed_date = self.state['completed_date']
            if isinstance(completed_date, str):
                try:
                    completed_date = datetime.fromisoformat(completed_date)
                    completed_label = QLabel(f"Completed: {completed_date.strftime('%Y-%m-%d')}")
                except:
                    completed_label = QLabel(f"Completed: {completed_date}")
            else:
                completed_label = QLabel(f"Completed: {completed_date.strftime('%Y-%m-%d')}")
                
            completed_label.setStyleSheet("color: #4caf50; font-size: 10px;")
            details_layout.addWidget(completed_label)
            
        layout.addLayout(details_layout, 1)
        
        # Notes field
        self.notes_field = QTextEdit()
        self.notes_field.setPlaceholderText("Add notes...")
        self.notes_field.setMaximumHeight(50)
        self.notes_field.setText(self.state.get('notes', ''))
        self.notes_field.textChanged.connect(self.on_notes_changed)
        layout.addWidget(self.notes_field)
        
        # Apply styling based on completion
        self.update_styling()
        
    def calculate_status(self, due_date: datetime) -> tuple[str, str]:
        """Calculate the status of this deliverable.
        
        Args:
            due_date: Due date for the deliverable
            
        Returns:
            Tuple of (status_text, status_color)
        """
        if self.state.get('completed'):
            return ("✓ Complete", "#4caf50")
            
        days = days_until(due_date)
        
        if days < 0:
            return (f"⚠ {abs(days)} days overdue", "#f44336")
        elif days == 0:
            return ("⏰ Due today", "#ff9800")
        elif days <= 3:
            return (f"⏰ Due in {days} days", "#ff9800")
        elif days <= 7:
            return (f"Due in {days} days", "#ffc107")
        else:
            return (f"Due in {days} days", "#666666")
            
    def update_styling(self):
        """Update the visual styling based on completion status."""
        if self.state.get('completed'):
            self.setStyleSheet("""
                ChecklistItem {
                    background-color: #f0f8f0;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
        else:
            due_date = self.state.get('due_date')
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
                
            days = days_until(due_date)
            if days < 0:
                # Overdue
                self.setStyleSheet("""
                    ChecklistItem {
                        background-color: #fff5f5;
                        border: 1px solid #f44336;
                        border-radius: 4px;
                        padding: 5px;
                    }
                """)
            elif days <= 3:
                # Urgent
                self.setStyleSheet("""
                    ChecklistItem {
                        background-color: #fffaf0;
                        border: 1px solid #ff9800;
                        border-radius: 4px;
                        padding: 5px;
                    }
                """)
                
    def on_checkbox_changed(self, state):
        """Handle checkbox state change."""
        self.state['completed'] = bool(state)
        if self.state['completed']:
            self.state['completed_date'] = datetime.now().isoformat()
        else:
            self.state['completed_date'] = None
            
        self.update_styling()
        self.state_changed.emit(self.deliverable_name, self.state)
        
    def on_notes_changed(self):
        """Handle notes text change."""
        self.state['notes'] = self.notes_field.toPlainText()
        self.state_changed.emit(self.deliverable_name, self.state)


class ReleaseChecklistDialog(QDialog):
    """Dialog for managing release checklist."""
    
    checklist_updated = pyqtSignal(dict)  # Updated checklist data
    
    def __init__(self, release_data: Dict[str, Any], artist_config: Dict[str, Any], parent=None):
        """Initialize the checklist dialog.
        
        Args:
            release_data: Release data dictionary
            artist_config: Artist configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.release_data = release_data
        self.artist_config = artist_config
        self.checklist = release_data.get('checklist', {}).copy()
        self.checklist_items = {}
        
        self.setWindowTitle(f"Release Checklist - {release_data.get('title', 'Untitled')}")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Checklist items in scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.checklist_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area, 1)
        
        # Populate checklist
        self.populate_checklist()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Update progress
        self.update_progress()
        
    def create_header(self) -> QWidget:
        """Create the dialog header."""
        header = QGroupBox()
        layout = QGridLayout(header)
        
        # Artist and title
        artist_label = QLabel(f"Artist: {self.release_data.get('artist', 'Unknown')}")
        artist_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(artist_label, 0, 0)
        
        title_label = QLabel(f"Title: {self.release_data.get('title', 'Untitled')}")
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label, 0, 1)
        
        # Release date
        release_date = self.release_data.get('release_date')
        if isinstance(release_date, str):
            release_date = datetime.fromisoformat(release_date)
            
        date_label = QLabel(f"Release Date: {release_date.strftime('%B %d, %Y')}")
        layout.addWidget(date_label, 1, 0)
        
        # Type
        type_label = QLabel(f"Type: {self.release_data.get('type', 'single').capitalize()}")
        layout.addWidget(type_label, 1, 1)
        
        # Notes
        if self.release_data.get('notes'):
            notes_label = QLabel(f"Notes: {self.release_data['notes']}")
            notes_label.setWordWrap(True)
            layout.addWidget(notes_label, 2, 0, 1, 2)
            
        return header
        
    def populate_checklist(self):
        """Populate the checklist with items."""
        release_date = self.release_data.get('release_date')
        if isinstance(release_date, str):
            release_date = datetime.fromisoformat(release_date)
            
        # Group items by category
        categories = {
            'Pre-Production': ['final_master', 'album_artwork', 'spotify_canvas'],
            'Distribution': ['distributor_submission'],
            'Content Creation': [],
            'Marketing': [],
            'Release Day': ['release_day_campaign']
        }
        
        # Categorize deliverables
        for deliverable in self.checklist:
            categorized = False
            for category, items in categories.items():
                if deliverable in items:
                    categorized = True
                    break
                    
            if not categorized:
                if 'reel' in deliverable:
                    categories['Content Creation'].append(deliverable)
                elif 'carousel' in deliverable or 'ad_creative' in deliverable:
                    categories['Marketing'].append(deliverable)
                else:
                    categories['Marketing'].append(deliverable)
                    
        # Create sections
        for category, deliverables in categories.items():
            if not deliverables:
                continue
                
            # Category header
            category_label = QLabel(category)
            category_font = QFont()
            category_font.setPointSize(12)
            category_font.setBold(True)
            category_label.setFont(category_font)
            self.checklist_layout.addWidget(category_label)
            
            # Add items
            for deliverable in deliverables:
                if deliverable in self.checklist:
                    item = ChecklistItem(
                        deliverable,
                        self.checklist[deliverable],
                        release_date
                    )
                    item.state_changed.connect(self.on_item_changed)
                    self.checklist_items[deliverable] = item
                    self.checklist_layout.addWidget(item)
                    
            # Add spacing
            self.checklist_layout.addSpacing(10)
            
    def on_item_changed(self, deliverable_name: str, new_state: dict):
        """Handle checklist item state change."""
        self.checklist[deliverable_name] = new_state
        self.update_progress()
        
    def update_progress(self):
        """Update the progress bar."""
        total = len(self.checklist)
        completed = sum(1 for item in self.checklist.values() if item.get('completed', False))
        
        if total > 0:
            progress = int((completed / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{completed}/{total} tasks completed ({progress}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("No tasks")
            
    def save_and_close(self):
        """Save changes and close dialog."""
        self.checklist_updated.emit(self.checklist)
        self.accept()
        
    def get_updated_checklist(self) -> Dict[str, Dict]:
        """Get the updated checklist data."""
        return self.checklist.copy()