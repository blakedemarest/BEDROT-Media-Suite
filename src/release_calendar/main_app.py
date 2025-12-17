"""
Main Application for Release Calendar Module

PyQt6-based GUI application for managing music release schedules.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QComboBox, QDateEdit, QSpinBox, QTextEdit,
    QMessageBox, QFileDialog, QHeaderView, QSplitter,
    QGroupBox, QGridLayout, QProgressBar, QStatusBar,
    QMenuBar, QMenu, QToolBar, QLineEdit
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFont, QAction

import pandas as pd

from .calendar_logic import BedrotReleaseCalendar
from .visual_calendar import VisualCalendarWidget
from .checklist_dialog import ReleaseChecklistDialog
from .config_manager import ConfigManager
from .data_manager import CalendarDataManager
from .utils import format_deliverable_name
from .utils import logger, format_date, days_until


class CalendarApp(QMainWindow):
    """Main application window for the release calendar."""
    
    def __init__(self):
        """Initialize the calendar application."""
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.data_manager = CalendarDataManager()
        self.calendar = BedrotReleaseCalendar(self.config_manager, self.data_manager)
        
        # Track signal connections for cleanup
        self.signal_connections = []
        
        # Set up UI
        self.setup_ui()
        
        # Load initial data
        self.load_initial_data()
        
        # Refresh views
        self.refresh_all_views()
        
    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("BEDROT RELEASE CALENDAR // CYBERCORE SCHEDULING")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply BEDROT theme
        self.apply_bedrot_theme()
        
        # Set up central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_calendar_tab()
        self.create_overview_tab()
        self.create_releases_tab()
        self.create_deliverables_tab()
        self.create_add_release_tab()
    
    def apply_bedrot_theme(self):
        """Apply comprehensive BEDROT cyberpunk visual theme."""
        theme = """
        /* Global Widget Styles */
        QWidget {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }
        
        /* Main Window */
        QMainWindow {
            background-color: #121212;
        }
        
        /* Tab Widget */
        QTabWidget::pane {
            background-color: #121212;
            border: 1px solid #00ffff;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #1a1a1a;
            color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #404040;
            border-bottom: none;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }
        
        QTabBar::tab:selected {
            background-color: #121212;
            color: #00ffff;
            border: 1px solid #00ffff;
            border-bottom: none;
        }
        
        QTabBar::tab:hover {
            background-color: #252525;
            color: #00ff88;
            border: 1px solid #00ff88;
        }
        
        /* Group Boxes */
        QGroupBox {
            background-color: #121212;
            border: 1px solid #00ffff;
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 10px;
            font-weight: bold;
            color: #00ffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #00ffff;
            background-color: #121212;
        }
        
        /* Labels */
        QLabel {
            color: #e0e0e0;
            background-color: transparent;
        }
        
        /* Push Buttons */
        QPushButton {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 6px 10px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #252525;
            border: 1px solid #00ff88;
            color: #00ff88;
        }
        
        QPushButton:pressed {
            background-color: #0a0a0a;
            border: 1px solid #00ffff;
            color: #00ffff;
        }
        
        QPushButton:disabled {
            background-color: #0a0a0a;
            border: 1px solid #2a2a2a;
            color: #666666;
        }
        
        /* Primary Action Buttons */
        QPushButton#primaryButton {
            background-color: #00ff88;
            border: none;
            color: #000000;
            min-width: 120px;
        }
        
        QPushButton#primaryButton:hover {
            background-color: #00ffaa;
        }
        
        QPushButton#primaryButton:pressed {
            background-color: #00cc66;
        }
        
        /* Line Edits */
        QLineEdit {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
            selection-background-color: #00ffff;
            selection-color: #000000;
        }
        
        QLineEdit:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QLineEdit:disabled {
            background-color: #0a0a0a;
            color: #666666;
        }
        
        /* Text Edit */
        QTextEdit {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
            selection-background-color: #00ffff;
            selection-color: #000000;
        }
        
        QTextEdit:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        /* ComboBox */
        QComboBox {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
            min-width: 100px;
        }
        
        QComboBox:hover {
            border: 1px solid #00ff88;
        }
        
        QComboBox:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #00ff88;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #1a1a1a;
            border: 1px solid #00ffff;
            selection-background-color: #00ffff;
            selection-color: #000000;
            color: #e0e0e0;
        }
        
        /* Spin Box */
        QSpinBox {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
        }
        
        QSpinBox:hover {
            border: 1px solid #00ff88;
        }
        
        QSpinBox:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: #252525;
            border: 1px solid #404040;
            width: 16px;
        }
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: #00ff88;
        }
        
        QSpinBox::up-arrow, QSpinBox::down-arrow {
            width: 7px;
            height: 7px;
        }
        
        /* Date Edit */
        QDateEdit {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
        }
        
        QDateEdit:hover {
            border: 1px solid #00ff88;
        }
        
        QDateEdit:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QDateEdit::drop-down {
            border: none;
            width: 20px;
        }
        
        QDateEdit::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #00ff88;
            margin-right: 5px;
        }
        
        /* Table Widget */
        QTableWidget {
            background-color: #1a1a1a;
            alternate-background-color: #202020;
            border: 1px solid #404040;
            gridline-color: #2a2a2a;
            color: #e0e0e0;
        }
        
        QTableWidget::item {
            padding: 5px;
            border: none;
        }
        
        QTableWidget::item:selected {
            background-color: rgba(0, 255, 255, 0.3);
            color: #ffffff;
        }
        
        QTableWidget::item:hover {
            background-color: rgba(0, 255, 136, 0.1);
        }
        
        QHeaderView::section {
            background-color: #0a0a0a;
            color: #00ffff;
            padding: 5px;
            border: 1px solid #404040;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        QHeaderView::section:hover {
            background-color: #1a1a1a;
        }
        
        /* Progress Bar */
        QProgressBar {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            text-align: center;
            color: #00ff88;
        }
        
        QProgressBar::chunk {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                            stop: 0 #00ff88, stop: 1 #00ffff);
            border-radius: 3px;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #0a0a0a;
            color: #e0e0e0;
            border-bottom: 1px solid #404040;
        }
        
        QMenuBar::item {
            padding: 5px 10px;
            background-color: transparent;
        }
        
        QMenuBar::item:selected {
            background-color: #1a1a1a;
            color: #00ff88;
        }
        
        QMenuBar::item:pressed {
            background-color: #252525;
            color: #00ffff;
        }
        
        /* Menus */
        QMenu {
            background-color: #1a1a1a;
            border: 1px solid #00ffff;
            color: #e0e0e0;
        }
        
        QMenu::item {
            padding: 5px 20px;
        }
        
        QMenu::item:selected {
            background-color: #252525;
            color: #00ff88;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #404040;
            margin: 5px 0;
        }
        
        /* Tool Bar */
        QToolBar {
            background-color: #0a0a0a;
            border: none;
            padding: 5px;
            spacing: 5px;
        }
        
        QToolBar::separator {
            background-color: #404040;
            width: 1px;
            margin: 0 10px;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #0a0a0a;
            color: #00ff88;
            border-top: 1px solid #404040;
        }
        
        /* Scroll Bars */
        QScrollBar:vertical {
            background-color: #0a0a0a;
            width: 14px;
            border: 1px solid #1a1a1a;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #00ff88;
            border-radius: 6px;
            min-height: 30px;
            margin: 1px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #00ffff;
        }
        
        QScrollBar::handle:vertical:pressed {
            background-color: #00cccc;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #0a0a0a;
            height: 14px;
            border: 1px solid #1a1a1a;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #00ff88;
            border-radius: 6px;
            min-width: 30px;
            margin: 1px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #00ffff;
        }
        
        QScrollBar::handle:horizontal:pressed {
            background-color: #00cccc;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #404040;
        }
        
        QSplitter::handle:hover {
            background-color: #00ff88;
        }
        
        /* Message Box */
        QMessageBox {
            background-color: #121212;
        }
        
        QMessageBox QLabel {
            color: #e0e0e0;
        }
        
        QMessageBox QPushButton {
            min-width: 80px;
        }
        """
        
        self.setStyleSheet(theme)
        
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_excel_action = QAction("Export to Excel", self)
        export_excel_action.triggered.connect(self.export_to_excel)
        file_menu.addAction(export_excel_action)
        
        export_ical_action = QAction("Export to iCal", self)
        export_ical_action.triggered.connect(self.export_to_ical)
        file_menu.addAction(export_ical_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh All", self)
        refresh_action.triggered.connect(self.refresh_all_views)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create application toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add release button
        add_release_btn = QPushButton("+ Add Release")
        add_release_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(4))
        toolbar.addWidget(add_release_btn)
        
        toolbar.addSeparator()
        
        # Artist filter
        toolbar.addWidget(QLabel("Artist:"))
        self.artist_filter = QComboBox()
        self.artist_filter.addItems(["All Artists"] + list(self.config_manager.get("artists", {}).keys()))
        self.artist_filter.currentTextChanged.connect(self.refresh_all_views)
        toolbar.addWidget(self.artist_filter)
        
        toolbar.addSeparator()
        
        # Quick stats
        self.stats_label = QLabel("Loading...")
        toolbar.addWidget(self.stats_label)
        
    def create_calendar_tab(self):
        """Create the visual calendar tab."""
        # Create visual calendar widget
        self.visual_calendar = VisualCalendarWidget()
        
        # Connect signals
        self.visual_calendar.release_moved.connect(self.on_release_moved)
        self.visual_calendar.release_clicked.connect(self.on_release_clicked)
        self.visual_calendar.release_deleted.connect(self.on_release_deleted)
        self.visual_calendar.release_added.connect(self.on_release_added)
        self.visual_calendar.artwork_updated.connect(self.on_artwork_updated)
        
        # Add to tabs
        self.tabs.addTab(self.visual_calendar, "Visual Calendar")
        
    def create_overview_tab(self):
        """Create overview tab with summary statistics."""
        overview_widget = QWidget()
        layout = QVBoxLayout(overview_widget)
        
        # Artists summary
        artists_group = QGroupBox("Artists Summary")
        artists_layout = QGridLayout(artists_group)
        
        # Artist stats will be populated dynamically
        self.artist_stats_labels = {}
        for i, (artist, config) in enumerate(self.config_manager.get("artists", {}).items()):
            emoji = config.get('emoji', '')
            label = QLabel(f"{emoji} {artist}")
            label.setStyleSheet("font-weight: bold;")
            artists_layout.addWidget(label, i, 0)
            
            stats_label = QLabel("Loading...")
            artists_layout.addWidget(stats_label, i, 1)
            self.artist_stats_labels[artist] = stats_label
            
        layout.addWidget(artists_group)
        
        # Upcoming releases
        upcoming_group = QGroupBox("Upcoming Releases (Next 30 Days)")
        upcoming_layout = QVBoxLayout(upcoming_group)
        
        self.upcoming_table = QTableWidget()
        self.upcoming_table.setColumnCount(4)
        self.upcoming_table.setHorizontalHeaderLabels(["Artist", "Title", "Release Date", "Status"])
        upcoming_layout.addWidget(self.upcoming_table)
        
        layout.addWidget(upcoming_group)
        
        # Overdue deliverables
        overdue_group = QGroupBox("Overdue Deliverables")
        overdue_layout = QVBoxLayout(overdue_group)
        
        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(5)
        self.overdue_table.setHorizontalHeaderLabels(["Artist", "Release", "Deliverable", "Due Date", "Days Overdue"])
        overdue_layout.addWidget(self.overdue_table)
        
        layout.addWidget(overdue_group)
        
        self.tabs.addTab(overview_widget, "Overview")
        
    def create_releases_tab(self):
        """Create releases management tab."""
        releases_widget = QWidget()
        layout = QVBoxLayout(releases_widget)
        
        # Releases table
        self.releases_table = QTableWidget()
        self.releases_table.setColumnCount(7)
        self.releases_table.setHorizontalHeaderLabels([
            "Artist", "Title", "Type", "Release Date", "Progress", "Notes", "Actions"
        ])
        
        # Enable sorting
        self.releases_table.setSortingEnabled(True)
        
        # Double-click to edit
        self.releases_table.itemDoubleClicked.connect(self.on_release_double_clicked)
        
        layout.addWidget(self.releases_table)
        
        self.tabs.addTab(releases_widget, "All Releases")
        
    def create_deliverables_tab(self):
        """Create deliverables tracking tab."""
        deliverables_widget = QWidget()
        layout = QVBoxLayout(deliverables_widget)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Show:"))
        self.deliverable_filter = QComboBox()
        self.deliverable_filter.addItems(["All", "Pending", "Overdue", "Completed"])
        self.deliverable_filter.currentTextChanged.connect(self.refresh_deliverables_view)
        filter_layout.addWidget(self.deliverable_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Deliverables table
        self.deliverables_table = QTableWidget()
        self.deliverables_table.setColumnCount(7)
        self.deliverables_table.setHorizontalHeaderLabels([
            "Artist", "Release", "Deliverable", "Due Date", "Status", "Notes", "Actions"
        ])
        
        layout.addWidget(self.deliverables_table)
        
        self.tabs.addTab(deliverables_widget, "Deliverables")
        
    def create_add_release_tab(self):
        """Create add release form tab."""
        add_widget = QWidget()
        layout = QVBoxLayout(add_widget)
        
        # Form layout
        form_group = QGroupBox("New Release Details")
        form_layout = QGridLayout(form_group)
        
        # Artist selection
        form_layout.addWidget(QLabel("Artist:"), 0, 0)
        self.artist_combo = QComboBox()
        self.artist_combo.addItems(list(self.config_manager.get("artists", {}).keys()))
        form_layout.addWidget(self.artist_combo, 0, 1)
        
        # Title
        form_layout.addWidget(QLabel("Title:"), 1, 0)
        self.title_input = QLineEdit()
        form_layout.addWidget(self.title_input, 1, 1)
        
        # Release type
        form_layout.addWidget(QLabel("Type:"), 2, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["single", "ep", "album"])
        form_layout.addWidget(self.type_combo, 2, 1)
        
        # Release date
        form_layout.addWidget(QLabel("Release Date:"), 3, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(21))  # Default 3 weeks out
        form_layout.addWidget(self.date_edit, 3, 1)
        
        # Notes
        form_layout.addWidget(QLabel("Notes:"), 4, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        form_layout.addWidget(self.notes_input, 4, 1)
        
        layout.addWidget(form_group)
        
        # Conflict check
        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: red;")
        layout.addWidget(self.conflict_label)
        
        # Add button
        add_btn = QPushButton("Add Release")
        add_btn.clicked.connect(self.add_release)
        layout.addWidget(add_btn)
        
        layout.addStretch()
        
        self.tabs.addTab(add_widget, "Add Release")
        
    def load_initial_data(self):
        """Load initial calendar data."""
        # Data is already loaded by the calendar from data_manager
        logger.info("Initial data loaded")
        
    def refresh_all_views(self):
        """Refresh all views with current data."""
        self.refresh_calendar_view()
        self.refresh_overview_view()
        self.refresh_releases_view()
        self.refresh_deliverables_view()
        self.update_stats()
        
    def refresh_calendar_view(self):
        """Refresh the visual calendar."""
        # Get current filter
        artist_filter = self.artist_filter.currentText()
        
        # Get releases data
        if artist_filter == "All Artists":
            releases_data = self.calendar.artists
        else:
            releases_data = {artist_filter: self.calendar.get_artist_releases(artist_filter)}
            
        # Update visual calendar
        self.visual_calendar.set_releases_data(releases_data, self.config_manager.config)
        
    def refresh_overview_view(self):
        """Refresh the overview tab."""
        # Update artist stats
        for artist, label in self.artist_stats_labels.items():
            releases = self.calendar.get_artist_releases(artist)
            total = len(releases)
            
            # Count by type
            singles = sum(1 for r in releases if r.get('type') == 'single')
            eps = sum(1 for r in releases if r.get('type') == 'ep')
            albums = sum(1 for r in releases if r.get('type') == 'album')
            
            # Calculate completion
            total_tasks = 0
            completed_tasks = 0
            for release in releases:
                checklist = release.get('checklist', {})
                total_tasks += len(checklist)
                completed_tasks += sum(1 for item in checklist.values() if item.get('completed', False))
                
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            label.setText(
                f"Releases: {total} ({singles}S/{eps}E/{albums}A) | "
                f"Completion: {completion_rate:.1f}%"
            )
            
        # Update upcoming releases
        self.refresh_upcoming_releases()
        
        # Update overdue deliverables
        self.refresh_overdue_deliverables()
        
    def refresh_upcoming_releases(self):
        """Refresh the upcoming releases table."""
        self.upcoming_table.setRowCount(0)
        
        today = datetime.now().date()
        cutoff = today + timedelta(days=30)
        
        upcoming = []
        for artist, releases in self.calendar.artists.items():
            for release in releases:
                release_date = release.get('release_date')
                if isinstance(release_date, str):
                    release_date = datetime.fromisoformat(release_date).date()
                else:
                    release_date = release_date.date()
                    
                if today <= release_date <= cutoff:
                    # Calculate progress
                    checklist = release.get('checklist', {})
                    completed = sum(1 for item in checklist.values() if item.get('completed', False))
                    total = len(checklist)
                    
                    upcoming.append({
                        'artist': artist,
                        'title': release.get('title', 'Untitled'),
                        'release_date': release_date,
                        'progress': f"{completed}/{total}"
                    })
                    
        # Sort by date
        upcoming.sort(key=lambda x: x['release_date'])
        
        # Populate table
        for item in upcoming:
            row = self.upcoming_table.rowCount()
            self.upcoming_table.insertRow(row)
            
            self.upcoming_table.setItem(row, 0, QTableWidgetItem(item['artist']))
            self.upcoming_table.setItem(row, 1, QTableWidgetItem(item['title']))
            self.upcoming_table.setItem(row, 2, QTableWidgetItem(item['release_date'].strftime('%Y-%m-%d')))
            self.upcoming_table.setItem(row, 3, QTableWidgetItem(item['progress']))
            
    def refresh_overdue_deliverables(self):
        """Refresh the overdue deliverables table."""
        self.overdue_table.setRowCount(0)
        
        today = datetime.now()
        
        overdue = []
        for artist, releases in self.calendar.artists.items():
            for release in releases:
                checklist = release.get('checklist', {})
                
                for deliverable, details in checklist.items():
                    if not details.get('completed', False):
                        due_date = details.get('due_date')
                        if isinstance(due_date, str):
                            due_date = datetime.fromisoformat(due_date)
                            
                        if due_date < today:
                            days_overdue = (today - due_date).days
                            overdue.append({
                                'artist': artist,
                                'release': release.get('title', 'Untitled'),
                                'deliverable': format_deliverable_name(deliverable),
                                'due_date': due_date,
                                'days_overdue': days_overdue
                            })
                            
        # Sort by days overdue
        overdue.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        # Populate table
        for item in overdue:
            row = self.overdue_table.rowCount()
            self.overdue_table.insertRow(row)
            
            self.overdue_table.setItem(row, 0, QTableWidgetItem(item['artist']))
            self.overdue_table.setItem(row, 1, QTableWidgetItem(item['release']))
            self.overdue_table.setItem(row, 2, QTableWidgetItem(item['deliverable']))
            self.overdue_table.setItem(row, 3, QTableWidgetItem(item['due_date'].strftime('%Y-%m-%d')))
            
            days_item = QTableWidgetItem(str(item['days_overdue']))
            days_item.setForeground(QColor("#f44336"))
            self.overdue_table.setItem(row, 4, days_item)
            
    def refresh_releases_view(self):
        """Refresh the releases table."""
        self.releases_table.setRowCount(0)
        
        # Get current filter
        artist_filter = self.artist_filter.currentText()
        
        # Get releases
        if artist_filter == "All Artists":
            all_releases = []
            for artist, releases in self.calendar.artists.items():
                for release in releases:
                    release_copy = release.copy()
                    release_copy['artist'] = artist
                    all_releases.append(release_copy)
            releases_to_show = all_releases
        else:
            releases_to_show = [
                {**r, 'artist': artist_filter} 
                for r in self.calendar.get_artist_releases(artist_filter)
            ]
            
        # Sort by date
        releases_to_show.sort(key=lambda x: x.get('release_date', ''), reverse=True)
        
        # Populate table
        for release in releases_to_show:
            row = self.releases_table.rowCount()
            self.releases_table.insertRow(row)
            
            # Artist
            self.releases_table.setItem(row, 0, QTableWidgetItem(release['artist']))
            
            # Title
            self.releases_table.setItem(row, 1, QTableWidgetItem(release.get('title', 'Untitled')))
            
            # Type
            self.releases_table.setItem(row, 2, QTableWidgetItem(release.get('type', 'single')))
            
            # Release date
            release_date = release.get('release_date')
            if isinstance(release_date, str):
                date_str = release_date[:10]  # Extract date part
            else:
                date_str = release_date.strftime('%Y-%m-%d')
            self.releases_table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # Progress
            checklist = release.get('checklist', {})
            completed = sum(1 for item in checklist.values() if item.get('completed', False))
            total = len(checklist)
            progress_str = f"{completed}/{total}"
            self.releases_table.setItem(row, 4, QTableWidgetItem(progress_str))
            
            # Notes
            notes = release.get('notes', '')
            self.releases_table.setItem(row, 5, QTableWidgetItem(notes))
            
            # Actions button
            actions_btn = QPushButton("Edit Checklist")
            actions_btn.clicked.connect(
                lambda checked, a=release['artist'], t=release.get('title'): 
                self.on_release_clicked(a, t)
            )
            self.releases_table.setCellWidget(row, 6, actions_btn)
            
    def refresh_deliverables_view(self):
        """Refresh the deliverables table."""
        self.deliverables_table.setRowCount(0)
        
        # Get filter
        deliverable_filter = self.deliverable_filter.currentText()
        artist_filter = self.artist_filter.currentText()
        
        # Collect all deliverables
        all_deliverables = []
        
        if artist_filter == "All Artists":
            artists_to_check = self.calendar.artists.items()
        else:
            artists_to_check = [(artist_filter, self.calendar.get_artist_releases(artist_filter))]
            
        for artist, releases in artists_to_check:
            for release in releases:
                checklist = release.get('checklist', {})
                
                for deliverable, details in checklist.items():
                    # Apply filter
                    is_completed = details.get('completed', False)
                    due_date = details.get('due_date')
                    if isinstance(due_date, str):
                        due_date = datetime.fromisoformat(due_date)
                        
                    is_overdue = due_date < datetime.now() and not is_completed
                    
                    if deliverable_filter == "All":
                        show = True
                    elif deliverable_filter == "Pending":
                        show = not is_completed
                    elif deliverable_filter == "Overdue":
                        show = is_overdue
                    elif deliverable_filter == "Completed":
                        show = is_completed
                    else:
                        show = True
                        
                    if show:
                        all_deliverables.append({
                            'artist': artist,
                            'release': release.get('title', 'Untitled'),
                            'deliverable': deliverable,
                            'details': details,
                            'due_date': due_date,
                            'is_overdue': is_overdue,
                            'is_completed': is_completed
                        })
                        
        # Sort by due date
        all_deliverables.sort(key=lambda x: x['due_date'])
        
        # Populate table
        for item in all_deliverables:
            row = self.deliverables_table.rowCount()
            self.deliverables_table.insertRow(row)
            
            self.deliverables_table.setItem(row, 0, QTableWidgetItem(item['artist']))
            self.deliverables_table.setItem(row, 1, QTableWidgetItem(item['release']))
            self.deliverables_table.setItem(row, 2, QTableWidgetItem(format_deliverable_name(item['deliverable'])))
            self.deliverables_table.setItem(row, 3, QTableWidgetItem(item['due_date'].strftime('%Y-%m-%d')))
            
            # Status
            if item['is_completed']:
                status = "✓ Complete"
                color = "#4caf50"
            elif item['is_overdue']:
                days = days_until(item['due_date'])
                status = f"⚠ {abs(days)} days overdue"
                color = "#f44336"
            else:
                days = days_until(item['due_date'])
                status = f"{days} days"
                color = "#666666"
                
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color))
            self.deliverables_table.setItem(row, 4, status_item)
            
            # Notes
            notes = item['details'].get('notes', '')
            self.deliverables_table.setItem(row, 5, QTableWidgetItem(notes))
            
            # Action button
            action_btn = QPushButton("Edit")
            action_btn.clicked.connect(
                lambda checked, a=item['artist'], t=item['release']: 
                self.on_release_clicked(a, t)
            )
            self.deliverables_table.setCellWidget(row, 6, action_btn)
            
    def update_stats(self):
        """Update the statistics label."""
        total_releases = sum(len(releases) for releases in self.calendar.artists.values())
        
        # Count pending deliverables
        pending = 0
        overdue = 0
        today = datetime.now()
        
        for releases in self.calendar.artists.values():
            for release in releases:
                checklist = release.get('checklist', {})
                for details in checklist.values():
                    if not details.get('completed', False):
                        pending += 1
                        due_date = details.get('due_date')
                        if isinstance(due_date, str):
                            due_date = datetime.fromisoformat(due_date)
                        if due_date < today:
                            overdue += 1
                            
        self.stats_label.setText(
            f"Total Releases: {total_releases} | "
            f"Pending Tasks: {pending} | "
            f"Overdue: {overdue}"
        )
        
    def add_release(self):
        """Add a new release from the form."""
        # Get form data
        artist = self.artist_combo.currentText()
        title = self.title_input.text().strip()
        release_type = self.type_combo.currentText()
        release_date = self.date_edit.date().toPyDate()
        notes = self.notes_input.toPlainText().strip()
        
        # Validate
        if not title:
            QMessageBox.warning(self, "Warning", "Please enter a release title.")
            return
            
        # Check for conflicts
        conflicts = self.calendar.check_release_conflicts(artist, release_date)
        if conflicts:
            conflict_text = "\n".join([
                f"- {c['artist']}: {c['title']} ({c['days_apart']} days apart)"
                for c in conflicts
            ])
            
            reply = QMessageBox.question(
                self,
                "Release Conflict",
                f"The following releases are scheduled near this date:\n\n{conflict_text}\n\n"
                "Do you want to add this release anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
                
        # Add release
        self.calendar.add_release(
            artist=artist,
            title=title,
            release_date=release_date,
            release_type=release_type,
            notes=notes
        )
        
        # Save data
        self.save_data()
        
        # Clear form
        self.title_input.clear()
        self.notes_input.clear()
        self.date_edit.setDate(QDate.currentDate().addDays(21))
        
        # Refresh views
        self.refresh_all_views()
        
        # Show success
        self.status_bar.showMessage(f"Added release: {artist} - {title}", 3000)
        
        # Switch to calendar tab
        self.tabs.setCurrentIndex(0)
        
    def on_release_clicked(self, artist: str, title: str):
        """Handle release click - open checklist dialog."""
        # Find release
        release = None
        for r in self.calendar.get_artist_releases(artist):
            if r.get('title') == title:
                release = r
                break
                
        if not release:
            return
            
        # Get artist config
        artist_config = self.config_manager.get_artist_config(artist)
        
        # Open checklist dialog
        dialog = ReleaseChecklistDialog(release, artist_config, self)
        dialog.checklist_updated.connect(
            lambda checklist: self.on_checklist_updated(artist, title, checklist)
        )
        dialog.exec()
        
    def on_checklist_updated(self, artist: str, title: str, checklist: Dict):
        """Handle checklist update from dialog."""
        # Update the release
        self.calendar.update_release(artist, title, {'checklist': checklist})
        
        # Save data
        self.save_data()
        
        # Refresh views
        self.refresh_all_views()
        
        self.status_bar.showMessage(f"Updated checklist for: {artist} - {title}", 3000)
        
    def on_release_moved(self, artist: str, title: str, new_date: datetime):
        """Handle release drag and drop."""
        # Update release date
        self.calendar.update_release(artist, title, {'release_date': new_date.isoformat()})
        
        # Recalculate checklist due dates
        release = None
        for r in self.calendar.get_artist_releases(artist):
            if r.get('title') == title:
                release = r
                break
                
        if release:
            # Update checklist due dates based on new release date
            deliverables = release.get('deliverables', {})
            checklist = release.get('checklist', {})
            
            for deliverable_name, days_offset in deliverables.items():
                if deliverable_name in checklist:
                    new_due_date = new_date + timedelta(days=days_offset)
                    checklist[deliverable_name]['due_date'] = new_due_date.isoformat()
                    
            self.calendar.update_release(artist, title, {'checklist': checklist})
            
        # Save data
        self.save_data()
        
        # Refresh views
        self.refresh_all_views()
        
        self.status_bar.showMessage(f"Moved release: {artist} - {title} to {new_date.strftime('%Y-%m-%d')}", 3000)
        
    def on_release_deleted(self, artist: str, title: str):
        """Handle release deletion."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete:\n{artist} - {title}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.calendar.delete_release(artist, title)
            self.save_data()
            self.refresh_all_views()
            self.status_bar.showMessage(f"Deleted release: {artist} - {title}", 3000)
            
    def on_artwork_updated(self, artist: str, title: str, file_path: str):
        """Handle artwork update from visual calendar."""
        # Update the release data
        releases = self.data_manager.get_artist_releases(artist)
        for release in releases:
            if release.get('title') == title:
                release['artwork_path'] = file_path
                # Save the updated data
                self.data_manager.save_data()
                # Log the update
                logger.info(f"Updated artwork for {artist} - {title}: {file_path}")
                # Refresh the visual calendar
                self.refresh_calendar_view()
                break
                
    def on_release_added(self, date: datetime, artist: str):
        """Handle quick add from calendar."""
        # Pre-fill the form
        self.date_edit.setDate(QDate(date.year, date.month, date.day))
        if artist and artist in self.config_manager.get("artists", {}):
            index = self.artist_combo.findText(artist)
            if index >= 0:
                self.artist_combo.setCurrentIndex(index)
                
        # Switch to add tab
        self.tabs.setCurrentIndex(4)
        
        # Focus on title input
        self.title_input.setFocus()
        
    def on_release_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click on releases table."""
        row = item.row()
        artist = self.releases_table.item(row, 0).text()
        title = self.releases_table.item(row, 1).text()
        self.on_release_clicked(artist, title)
        
    def save_data(self):
        """Save calendar data."""
        if self.calendar.save_to_data_manager():
            logger.info("Data saved successfully")
        else:
            QMessageBox.warning(self, "Warning", "Failed to save data.")
            
    def export_to_excel(self):
        """Export calendar to Excel file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Excel",
            "release_calendar.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                # Create Excel writer
                with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                    # Releases sheet
                    releases_data = []
                    for artist, releases in self.calendar.artists.items():
                        for release in releases:
                            releases_data.append({
                                'Artist': artist,
                                'Title': release.get('title', 'Untitled'),
                                'Type': release.get('type', 'single'),
                                'Release Date': release.get('release_date', '')[:10],
                                'Notes': release.get('notes', '')
                            })
                            
                    releases_df = pd.DataFrame(releases_data)
                    releases_df.to_excel(writer, sheet_name='Releases', index=False)
                    
                    # Deliverables sheet
                    deliverables_df = self.calendar.get_deliverables_calendar()
                    if not deliverables_df.empty:
                        deliverables_df.to_excel(writer, sheet_name='Deliverables', index=False)
                        
                QMessageBox.information(self, "Success", f"Exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
                
    def export_to_ical(self):
        """Export calendar to iCal file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to iCal",
            "release_calendar.ics",
            "iCal Files (*.ics)"
        )
        
        if filename:
            try:
                # Import icalendar if available
                try:
                    from icalendar import Calendar, Event
                    import pytz
                    
                    cal = Calendar()
                    cal.add('prodid', '-//BEDROT Productions Release Calendar//')
                    cal.add('version', '2.0')
                    
                    # Add events
                    for artist, releases in self.calendar.artists.items():
                        for release in releases:
                            # Release event
                            event = Event()
                            event.add('summary', f"{artist} - {release.get('title', 'Untitled')} Release")
                            
                            release_date = release.get('release_date')
                            if isinstance(release_date, str):
                                release_date = datetime.fromisoformat(release_date)
                                
                            event.add('dtstart', release_date.date())
                            event.add('dtend', release_date.date())
                            
                            if release.get('notes'):
                                event.add('description', release['notes'])
                                
                            cal.add_component(event)
                            
                            # Deliverable events
                            checklist = release.get('checklist', {})
                            for deliverable, details in checklist.items():
                                if not details.get('completed', False):
                                    due_date = details.get('due_date')
                                    if isinstance(due_date, str):
                                        due_date = datetime.fromisoformat(due_date)
                                        
                                    event = Event()
                                    event.add('summary', f"{artist} - {format_deliverable_name(deliverable)}")
                                    event.add('dtstart', due_date.date())
                                    event.add('dtend', due_date.date())
                                    event.add('description', f"Deliverable for {release.get('title')}")
                                    
                                    cal.add_component(event)
                                    
                    # Write to file
                    with open(filename, 'wb') as f:
                        f.write(cal.to_ical())
                        
                    QMessageBox.information(self, "Success", f"Exported to {filename}")
                    
                except ImportError:
                    QMessageBox.warning(
                        self, 
                        "Warning", 
                        "icalendar library not available. Please install it to export to iCal format."
                    )
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
                
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About",
            "BEDROT Productions Release Calendar\n\n"
            "A comprehensive release management system for\n"
            "coordinating music releases and deliverables.\n\n"
            "Version 1.0.0"
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Save data before closing
        self.save_data()
        event.accept()


def main():
    """Main entry point for the calendar application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = CalendarApp()
    window.show()
    
    sys.exit(app.exec())