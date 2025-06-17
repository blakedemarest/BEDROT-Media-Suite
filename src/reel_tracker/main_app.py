# -*- coding: utf-8 -*-
"""
Main Application Module for Reel Tracker.

This module contains the main application window and core functionality for:
- CSV import/export
- Table management with dropdown delegates
- Drag-and-drop file handling
- Configuration management integration
"""

import sys
import os
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QHeaderView, QLabel, QFrame, QItemDelegate
)
# Explicit import to ensure availability even if list above changes
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .config_manager import ConfigManager
from .media_randomizer import MediaRandomizerDialog
from .reel_dialog import ReelEntryDialog
from .bulk_edit_dialog import BulkEditDialog
from .default_metadata_dialog import DefaultMetadataDialog
from .file_organization_dialog import FileOrganizationDialog
from .utils import safe_print


class DropdownDelegate(QItemDelegate):
    """
    Custom delegate for dropdown editing in table cells.
    """
    
    def __init__(self, parent, dropdown_type, config_manager):
        super().__init__(parent)
        self.dropdown_type = dropdown_type
        self.config_manager = config_manager
        self.current_editor = None
    
    def createEditor(self, parent, option, index):
        """Create dropdown editor for the cell."""
        try:
            from PyQt5.QtWidgets import QComboBox
            editor = QComboBox(parent)
            editor.setEditable(True)
            
            # Get values from config
            values = self.config_manager.get_dropdown_values(self.dropdown_type)
            editor.addItems(values if values else [""])
            
            # Store reference to prevent crashes
            self.current_editor = editor
            
            return editor
        except Exception as e:
            safe_print(f"Error creating dropdown editor: {e}")
            return None
    
    def setEditorData(self, editor, index):
        """Set the current value in the editor."""
        try:
            if editor is None:
                return
                
            value = index.model().data(index, Qt.EditRole)
            if value is not None:
                editor.setCurrentText(str(value))
        except Exception as e:
            safe_print(f"Error setting editor data: {e}")
    
    def setModelData(self, editor, model, index):
        """Set the value from editor back to model."""
        try:
            if editor is None:
                return
                
            value = editor.currentText()
            model.setData(index, value, Qt.EditRole)
            
            # Add to config if it's a new value (safely)
            if value and value.strip():
                try:
                    if self.config_manager.add_dropdown_value(self.dropdown_type, value.strip()):
                        safe_print(f"[OK] Added new {self.dropdown_type}: {value.strip()}")
                except Exception as e:
                    safe_print(f"Warning: Could not save new dropdown value: {e}")
                    
        except Exception as e:
            safe_print(f"Error setting model data: {e}")
    
    def updateEditorGeometry(self, editor, option, index):
        """Update editor geometry."""
        try:
            if editor is not None:
                editor.setGeometry(option.rect)
        except Exception as e:
            safe_print(f"Error updating editor geometry: {e}")


class ReelTrackerApp(QMainWindow):
    """
    PyQt5 application for tracking reels with CSV import/export and drag-drop functionality.
    Enhanced with robust manual data entry methods, media randomization support, and configuration management.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration manager with error handling
        try:
            self.config_manager = ConfigManager()
        except Exception as e:
            safe_print(f"Error initializing config manager: {e}")
            # Create a minimal config manager with defaults
            self.config_manager = None
        
        self.setWindowTitle("Reel Tracker - Enhanced with Configuration Management")
        self.setGeometry(100, 100, 1600, 800)
        
        # Define exact column order as required (Visual Template removed)
        self.columns = [
            "Reel ID", "Persona", "Release", "Reel Type", 
            "Clip Filename", "Caption", "FilePath"
        ]
        
        # Column indices for dropdowns
        self.dropdown_columns = {
            "Persona": 1,
            "Release": 2,
            "Reel Type": 3
        }
        
        # Store dropdown delegates for refreshing
        self.persona_delegate = None
        self.release_delegate = None
        self.reel_type_delegate = None
        
        # Store last-used values for autofill
        self.last_autofill = {"Persona": "", "Release": "RENEGADE PIPELINE", "Reel Type": ""}

        self.init_ui()
        
        # Auto-load last CSV if enabled and config manager is available
        if self.config_manager:
            self.auto_load_last_csv()
        
    def init_ui(self):
        """Initialize the user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Top button layout
        button_layout = QHBoxLayout()
        
        # File operations
        self.load_button = QPushButton("📂 Load CSV")
        self.load_button.clicked.connect(self.load_csv)
        button_layout.addWidget(self.load_button)
        
        self.save_button = QPushButton("💾 Save CSV")
        self.save_button.clicked.connect(self.save_csv)
        button_layout.addWidget(self.save_button)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        button_layout.addWidget(separator1)
        
        # Row operations
        self.add_row_button = QPushButton("➕ Add New Reel")
        self.add_row_button.clicked.connect(self.add_new_reel)
        self.add_row_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        button_layout.addWidget(self.add_row_button)
        
        self.randomize_reel_button = QPushButton("🎲 Random Reel")
        self.randomize_reel_button.clicked.connect(self.add_random_reel)
        self.randomize_reel_button.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        button_layout.addWidget(self.randomize_reel_button)
        
        self.edit_row_button = QPushButton("✏️ Edit Selected")
        self.edit_row_button.clicked.connect(self.edit_selected_reel)
        button_layout.addWidget(self.edit_row_button)
        
        self.default_metadata_button = QPushButton("🏷️ Default Metadata")
        self.default_metadata_button.clicked.connect(self.open_default_metadata)
        self.default_metadata_button.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        button_layout.addWidget(self.default_metadata_button)
        
        self.file_organization_button = QPushButton("📁 Organize Files")
        self.file_organization_button.clicked.connect(self.open_file_organization)
        self.file_organization_button.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        button_layout.addWidget(self.file_organization_button)
        
        self.duplicate_row_button = QPushButton("[COPY] Duplicate")
        self.duplicate_row_button.clicked.connect(self.duplicate_selected_reel)
        button_layout.addWidget(self.duplicate_row_button)
        
        self.delete_row_button = QPushButton("🗑️ Delete")
        self.delete_row_button.clicked.connect(self.delete_selected_reel)
        button_layout.addWidget(self.delete_row_button)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        button_layout.addWidget(separator2)
        
        # Bulk operations
        self.add_empty_row_button = QPushButton("📄 Add Empty Row")
        self.add_empty_row_button.clicked.connect(self.add_empty_row)
        button_layout.addWidget(self.add_empty_row_button)
        
        self.clear_table_button = QPushButton("🗑️ Clear All")
        self.clear_table_button.clicked.connect(self.clear_all_data)
        button_layout.addWidget(self.clear_table_button)
        
        # Add stretch to push buttons to the left
        button_layout.addStretch()
        
        # Row counter and stats
        self.row_count_label = QLabel("Rows: 0")
        self.row_count_label.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(self.row_count_label)
        
        # Release reel counter (now a clickable button)
        self.release_counter_button = QPushButton("Reels: 0/124")
        self.release_counter_button.setStyleSheet("font-weight: bold; color: #3498db; padding: 4px 8px; border: 1px solid #3498db; border-radius: 4px; background: transparent;")
        self.release_counter_button.clicked.connect(self.show_release_breakdown)
        button_layout.addWidget(self.release_counter_button)
        
        # Store current release filter
        self.current_release_filter = None
        
        # CSV path display
        self.csv_path_label = QLabel("No CSV loaded")
        self.csv_path_label.setStyleSheet("color: #7f8c8d; font-size: 10px; max-width: 300px;")
        self.csv_path_label.setWordWrap(True)
        button_layout.addWidget(self.csv_path_label)
        
        # Config status indicator
        self.config_status_label = QLabel("[CONFIG] Ready")
        self.config_status_label.setStyleSheet("color: green; font-size: 10px;")
        button_layout.addWidget(self.config_status_label)
        
        main_layout.addLayout(button_layout)
        
        # Create table widget
        self.table = QTableWidget()
        self.setup_table()
        self.setup_dropdown_delegates()
        main_layout.addWidget(self.table)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Update row count initially
        self.update_row_count()
        
        # Status bar with enhanced information
        self.statusBar().showMessage("Ready - Dropdowns auto-save new values. CSV auto-loads on startup.")
    
    def create_menu_bar(self):
        """Create menu bar with configuration options."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Configuration menu
        config_menu = menubar.addMenu('Configuration')
        
        # View dropdown values action
        view_dropdowns_action = config_menu.addAction('View Dropdown Values')
        view_dropdowns_action.triggered.connect(self.show_dropdown_config)
        
        # Reset dropdowns action
        reset_dropdowns_action = config_menu.addAction('Reset Dropdown Values')
        reset_dropdowns_action.triggered.connect(self.reset_dropdown_config)
        
        # Toggle auto-load CSV
        toggle_auto_load_action = config_menu.addAction('Toggle Auto-load CSV')
        toggle_auto_load_action.triggered.connect(self.toggle_auto_load_csv)
        
        # Show config file location
        show_config_location_action = config_menu.addAction('Show Config File Location')
        show_config_location_action.triggered.connect(self.show_config_location)
        
        config_menu.addSeparator()
        
        # File organization settings
        file_org_action = config_menu.addAction('File Organization Settings')
        file_org_action.triggered.connect(self.open_file_organization)
    
    def show_dropdown_config(self):
        """Show current dropdown configuration."""
        if not self.config_manager:
            QMessageBox.warning(self, "Configuration Unavailable", "Configuration manager is not available.")
            return
            
        config_info = ""
        for dropdown_type in ["persona", "release", "reel_type"]:
            values = self.config_manager.get_dropdown_values(dropdown_type)
            display_name = dropdown_type.replace('_', ' ').title()
            config_info += f"**{display_name}:** ({len(values)} values)\\n"
            for value in values[:10]:  # Show first 10 values
                config_info += f"  • {value}\\n" if value else "  • (empty)\\n"
            if len(values) > 10:
                config_info += f"  ... and {len(values) - 10} more\\n"
            config_info += "\\n"
        
        last_csv = self.config_manager.get_last_csv_path()
        # Add default metadata info
        defaults = self.config_manager.get_default_metadata()
        config_info += f"**Default Metadata:**\\n"
        config_info += f"  • Persona: {defaults.get('persona', 'None')}\\n"
        config_info += f"  • Release: {defaults.get('release', 'None')}\\n"
        config_info += f"  • Reel Type: {defaults.get('reel_type', 'None')}\\n\\n"
        
        config_info += f"**Last CSV:** {last_csv or 'None'}\\n"
        config_info += f"**Auto-load CSV:** {'Yes' if self.config_manager.should_auto_load_csv() else 'No'}"
        
        QMessageBox.information(self, "Dropdown Configuration", config_info)
    
    def reset_dropdown_config(self):
        """Reset dropdown values to defaults."""
        if not self.config_manager:
            QMessageBox.warning(self, "Configuration Unavailable", "Configuration manager is not available.")
            return
            
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "This will reset all dropdown values to defaults. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to default values
            default_config = self.config_manager.get_default_config()
            self.config_manager.config["dropdown_values"] = default_config["dropdown_values"]
            self.config_manager.save_config()
            
            # Refresh dropdown delegates safely
            try:
                self.setup_dropdown_delegates()
            except Exception as e:
                safe_print(f"Error refreshing dropdown delegates: {e}")
            
            QMessageBox.information(self, "Reset Complete", "Dropdown values have been reset to defaults.")
            self.statusBar().showMessage("Dropdown configuration reset to defaults")
    
    def toggle_auto_load_csv(self):
        """Toggle auto-load CSV setting."""
        if not self.config_manager:
            QMessageBox.warning(self, "Configuration Unavailable", "Configuration manager is not available.")
            return
            
        current_setting = self.config_manager.should_auto_load_csv()
        new_setting = not current_setting
        
        self.config_manager.config["app_settings"]["auto_load_last_csv"] = new_setting
        self.config_manager.save_config()
        
        status = "enabled" if new_setting else "disabled"
        QMessageBox.information(self, "Auto-load CSV", f"Auto-load CSV is now {status}.")
        self.statusBar().showMessage(f"Auto-load CSV {status}")
    
    def show_config_location(self):
        """Show the location of the configuration file."""
        if not self.config_manager:
            QMessageBox.warning(self, "Configuration Unavailable", "Configuration manager is not available.")
            return
            
        config_path = os.path.abspath(self.config_manager.config_file)
        QMessageBox.information(
            self, "Configuration File Location",
            f"Configuration file location:\\n\\n{config_path}\\n\\nYou can edit this file manually if needed."
        )

    def setup_table(self):
        """Setup the table widget with proper columns and drag-drop support."""
        # Set column count and headers
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        # Enable drag and drop
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.DropOnly)
        
        # Configure table appearance
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Set specific column widths for better media display (Visual Template removed)
        self.table.setColumnWidth(0, 140)  # Reel ID
        self.table.setColumnWidth(1, 130)  # Persona
        self.table.setColumnWidth(2, 100)  # Release
        self.table.setColumnWidth(3, 130)  # Reel Type
        self.table.setColumnWidth(4, 180)  # Clip Filename
        self.table.setColumnWidth(5, 280)  # Caption (wider since Visual Template removed)
        self.table.setColumnWidth(6, 350)  # FilePath
        
        # Set font for better readability
        font = QFont()
        font.setPointSize(9)
        self.table.setFont(font)
        
        # Enable sorting and selection
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        # Connect double-click to edit
        self.table.itemDoubleClicked.connect(self.edit_selected_reel)
        
        # Connect selection change to update buttons and release filter
        self.table.itemSelectionChanged.connect(self.update_button_states)
        self.table.itemSelectionChanged.connect(self.update_release_filter)
        
        # Connect item changes to auto-save
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Override drag and drop events
        self.table.dragEnterEvent = self.drag_enter_event
        self.table.dragMoveEvent = self.drag_move_event
        self.table.dropEvent = self.drop_event
    
    def setup_dropdown_delegates(self):
        """Setup dropdown delegates for specific columns."""
        try:
            # Only setup delegates if config manager is available
            if self.config_manager:
                # Store delegates as instance variables to prevent garbage collection
                self.persona_delegate = DropdownDelegate(self.table, "persona", self.config_manager)
                self.release_delegate = DropdownDelegate(self.table, "release", self.config_manager)
                self.reel_type_delegate = DropdownDelegate(self.table, "reel_type", self.config_manager)
                
                # Apply delegates to specific columns
                self.table.setItemDelegateForColumn(self.dropdown_columns["Persona"], self.persona_delegate)
                self.table.setItemDelegateForColumn(self.dropdown_columns["Release"], self.release_delegate)
                self.table.setItemDelegateForColumn(self.dropdown_columns["Reel Type"], self.reel_type_delegate)
                
                safe_print("[OK] Dropdown delegates setup successfully")
            else:
                safe_print("[WARNING] Dropdown delegates skipped - config manager not available")
        except Exception as e:
            safe_print(f"[ERROR] Error setting up dropdown delegates: {e}")
            # Continue without delegates if there's an error
            self.statusBar().showMessage("Warning: Dropdown functionality disabled due to setup error")
        
    def update_button_states(self):
        """Update button enabled states based on selection."""
        has_selection = bool(self.table.selectedItems())
        self.edit_row_button.setEnabled(has_selection)
        self.duplicate_row_button.setEnabled(has_selection)
        self.delete_row_button.setEnabled(has_selection)
        
    def update_row_count(self):
        """Update the row count display with statistics."""
        count = self.table.rowCount()
        
        # Count different types of media
        video_count = 0
        image_count = 0
        
        for row in range(count):
            filename_item = self.table.item(row, self.columns.index("Clip Filename"))
            if filename_item:
                filename = filename_item.text().lower()
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
                
                file_ext = Path(filename).suffix.lower()
                if file_ext in video_extensions:
                    video_count += 1
                elif file_ext in image_extensions:
                    image_count += 1
        
        stats_text = f"Rows: {count}"
        if video_count > 0 or image_count > 0:
            stats_text += f" (🎥{video_count} 🖼️{image_count})"
            
        self.row_count_label.setText(stats_text)
        
        # Update release counter
        self.update_release_counter(count)
    
    def update_release_counter(self, total_count=None):
        """Update the release counter display with goal achievement acknowledgement."""
        goal = 124
        
        # Get count for current release filter
        if self.current_release_filter:
            reel_count = self.count_reels_by_release(self.current_release_filter)
            counter_text = f"{self.current_release_filter}: {reel_count}/{goal}"
        else:
            reel_count = total_count if total_count is not None else self.table.rowCount()
            counter_text = f"All Reels: {reel_count}"
        
        if reel_count >= goal:
            # Goal achieved - change styling and add achievement badge
            self.release_counter_button.setText(f"🎉 {counter_text} - GOAL ACHIEVED! 🎉")
            self.release_counter_button.setStyleSheet(
                "font-weight: bold; color: white; background-color: #27ae60; "
                "padding: 4px 8px; border: 2px solid #27ae60; border-radius: 4px;"
            )
        elif reel_count >= goal * 0.9:  # 90% of goal
            # Close to goal - orange styling
            self.release_counter_button.setText(f"🔥 {counter_text}")
            self.release_counter_button.setStyleSheet(
                "font-weight: bold; color: white; background-color: #f39c12; "
                "padding: 4px 8px; border: 1px solid #f39c12; border-radius: 4px;"
            )
        elif reel_count >= goal * 0.75:  # 75% of goal
            # Good progress - yellow styling
            self.release_counter_button.setText(f"⚡ {counter_text}")
            self.release_counter_button.setStyleSheet(
                "font-weight: bold; color: #f39c12; "
                "padding: 4px 8px; border: 1px solid #f39c12; border-radius: 4px; background: transparent;"
            )
        else:
            # Normal progress - blue styling
            self.release_counter_button.setText(counter_text)
            self.release_counter_button.setStyleSheet(
                "font-weight: bold; color: #3498db; "
                "padding: 4px 8px; border: 1px solid #3498db; border-radius: 4px; background: transparent;"
            )
    
    def update_release_filter(self):
        """Update the current release filter based on selected row."""
        selected_items = self.table.selectedItems()
        if selected_items:
            # Get the release from the first selected row
            current_row = selected_items[0].row()
            release_col = self.columns.index("Release")
            release_item = self.table.item(current_row, release_col)
            if release_item and release_item.text().strip():
                self.current_release_filter = release_item.text().strip()
            else:
                self.current_release_filter = None
        else:
            self.current_release_filter = None
        
        # Update the counter with the new filter
        self.update_release_counter()
    
    def on_item_changed(self, item):
        """Handle direct cell edits and trigger auto-save."""
        # Update autofill memory for the changed row
        self.update_autofill_memory(item.row())
        
        # Auto-save the changes
        self.auto_save_csv()
        
        # Update counters if release column was changed
        if item.column() == self.columns.index("Release"):
            self.update_release_counter()
    
    def count_reels_by_release(self, release_name):
        """Count reels for a specific release."""
        count = 0
        release_col = self.columns.index("Release")
        
        for row in range(self.table.rowCount()):
            release_item = self.table.item(row, release_col)
            if release_item and release_item.text().strip() == release_name:
                count += 1
        
        return count
    
    def get_all_releases_with_counts(self):
        """Get all unique releases with their reel counts."""
        release_counts = {}
        release_col = self.columns.index("Release")
        
        for row in range(self.table.rowCount()):
            release_item = self.table.item(row, release_col)
            if release_item:
                release_name = release_item.text().strip()
                if release_name:  # Only count non-empty releases
                    release_counts[release_name] = release_counts.get(release_name, 0) + 1
        
        return release_counts
    
    def show_release_breakdown(self):
        """Show dialog with breakdown of reels by release."""
        release_counts = self.get_all_releases_with_counts()
        
        if not release_counts:
            QMessageBox.information(self, "Release Breakdown", "No releases found in the current data.")
            return
        
        # Create and show breakdown dialog
        dialog = ReleaseBreakdownDialog(self, release_counts)
        dialog.exec_()
    
    def auto_save_csv(self):
        """Automatically save CSV if a file path is available."""
        if not self.config_manager:
            return False
            
        last_csv_path = self.config_manager.get_last_csv_path()
        if not last_csv_path or self.table.rowCount() == 0:
            return False
        
        try:
            # Extract data from table
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data, columns=self.columns)
            df.to_csv(last_csv_path, index=False)
            
            self.statusBar().showMessage(f"Auto-saved {len(data)} rows to CSV", 2000)  # Show for 2 seconds
            return True
            
        except Exception as e:
            safe_print(f"Auto-save failed: {e}")
            return False
        
    def add_random_reel(self):
        """Add a new reel using the media randomizer."""
        # Open randomizer dialog first
        randomizer = MediaRandomizerDialog(self)
        if randomizer.exec_() == QDialog.Accepted:
            selected_file = randomizer.get_selected_file()
            if selected_file:
                # Open reel entry dialog with pre-filled file information
                dialog = ReelEntryDialog(self, config_manager=self.config_manager)
                
                # Pre-fill file information
                dialog.filepath_edit.setText(selected_file)
                dialog.filename_edit.setText(os.path.basename(selected_file))
                dialog.update_file_info(selected_file)
                # Auto-suggest template removed (Visual Template column removed)
                
                # Auto-fill release
                dialog.auto_fill_release(selected_file)
                
                # Generate auto ID
                dialog.generate_reel_id()
                
                # Show the dialog for user to complete
                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_data()
                    self.add_reel_to_table(data)
                    self.update_row_count()
                    self.auto_save_csv()
                    self.statusBar().showMessage("Random reel added successfully!")
        
    def drag_enter_event(self, event):
        """Handle drag enter events for file drops."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def drag_move_event(self, event):
        """Handle drag move events for file drops."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def drop_event(self, event):
        """Handle file drop events and add new rows to the table."""
        if event.mimeData().hasUrls():
            files_added = 0
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    self.add_file_row(file_path)
                    files_added += 1
            
            if files_added > 0:
                self.statusBar().showMessage(f"Added {files_added} file(s) to table")
                self.update_row_count()
            
            event.accept()
        else:
            event.ignore()
            
    def open_default_metadata(self):
        """Open the default metadata settings dialog."""
        dialog = DefaultMetadataDialog(self, self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("Default metadata settings updated")
    
    def open_file_organization(self):
        """Open the file organization dialog."""
        # Get current table data
        reel_data_list = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            
            # Only include rows with valid file paths
            if len(row_data) >= 7 and row_data[6].strip():  # FilePath column
                reel_data_list.append(row_data)
        
        if not reel_data_list:
            QMessageBox.information(self, "No Files", "No files with valid paths found to organize.")
            return
        
        dialog = FileOrganizationDialog(self, self.config_manager, reel_data_list)
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("File organization settings updated")
    
    def add_file_row(self, file_path):
        """Add a new row to the table with file information and default metadata."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        # Create empty items for all columns
        for col in range(len(self.columns)):
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.table.setItem(row_count, col, item)
        
        # Column indices for convenience
        reel_id_col = self.columns.index("Reel ID")
        filepath_col = self.columns.index("FilePath")
        filename_col = self.columns.index("Clip Filename")
        persona_col = self.columns.index("Persona")
        release_col = self.columns.index("Release")
        reel_type_col = self.columns.index("Reel Type")
        caption_col = self.columns.index("Caption")
        
        # Auto-generate Reel ID
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        reel_id = f"REEL_{timestamp}_{row_count:03d}"
        self.table.item(row_count, reel_id_col).setText(reel_id)
        
        # Populate file path & name
        self.table.item(row_count, filepath_col).setText(file_path)
        filename = os.path.basename(file_path)
        self.table.item(row_count, filename_col).setText(filename)
        
        # Apply default metadata if available
        if self.config_manager:
            defaults = self.config_manager.get_default_metadata()
            
            # Apply default persona
            if defaults.get("persona"):
                self.table.item(row_count, persona_col).setText(defaults["persona"])
            
            # Apply default release
            if defaults.get("release"):
                self.table.item(row_count, release_col).setText(defaults["release"])
            
            # Apply default reel type
            if defaults.get("reel_type"):
                self.table.item(row_count, reel_type_col).setText(defaults["reel_type"])
            
            # Apply default caption template
            if defaults.get("caption_template"):
                caption_template = defaults["caption_template"]
                # Replace {filename} placeholder with actual filename
                caption = caption_template.replace("{filename}", filename)
                self.table.item(row_count, caption_col).setText(caption)
            
            safe_print(f"[OK] Applied default metadata to drag-dropped file: {filename}")
        
        # Update autofill memory
        self.update_autofill_memory(row_count)
        
        # Auto-save after adding file
        self.auto_save_csv()
        
    def add_new_reel(self):
        """Open dialog to add a new reel with all data."""
        dialog = ReelEntryDialog(self, config_manager=self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.add_reel_to_table(data)
            self.update_row_count()
            self.auto_save_csv()
            self.statusBar().showMessage("New reel added successfully")
    
    def edit_selected_reel(self):
        """Edit one or many selected reels."""
        selected_rows = {item.row() for item in self.table.selectedItems()}
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select row(s) to edit.")
            return

        # Handle multi-row bulk edit
        if len(selected_rows) > 1:
            dialog = BulkEditDialog(self, config_manager=self.config_manager)
            if dialog.exec_() == QDialog.Accepted:
                updates = dialog.get_updates()
                if updates:
                    for row in selected_rows:
                        for col_name, value in updates.items():
                            col_idx = self.columns.index(col_name)
                            self.table.item(row, col_idx).setText(value)
                        self.update_autofill_memory(row)
                    self.auto_save_csv()
                    self.statusBar().showMessage(f"Bulk updated {len(selected_rows)} row(s)")
            return

        # Single row – open standard reel entry dialog
        current_row = next(iter(selected_rows))
        current_data = []
        for col in range(self.table.columnCount()):
            item = self.table.item(current_row, col)
            current_data.append(item.text() if item else "")

        dialog = ReelEntryDialog(self, current_data, self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.update_reel_in_table(current_row, data)
            self.auto_save_csv()
            self.statusBar().showMessage("Reel updated successfully")
    
    def duplicate_selected_reel(self):
        """Duplicate the selected reel."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to duplicate.")
            return
        
        # Get current row data
        current_data = []
        for col in range(self.table.columnCount()):
            item = self.table.item(current_row, col)
            current_data.append(item.text() if item else "")
        
        # Modify the Reel ID to indicate it's a duplicate
        if current_data[0]:  # If there's a Reel ID
            current_data[0] = current_data[0] + "_COPY"
        
        # Add the duplicated row
        self.add_reel_to_table(current_data)
        self.update_row_count()
        self.auto_save_csv()
        self.statusBar().showMessage("Reel duplicated successfully")
    
    def delete_selected_reel(self):
        """Delete the selected reel(s)."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select row(s) to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete {len(selected_rows)} row(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete rows in reverse order to maintain indices
            for row in sorted(selected_rows, reverse=True):
                self.table.removeRow(row)
            
            self.update_row_count()
            self.auto_save_csv()
            self.statusBar().showMessage(f"Deleted {len(selected_rows)} row(s)")
    
    def add_empty_row(self):
        """Add an empty row to the table."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        # Create empty items for all columns
        for col in range(len(self.columns)):
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.table.setItem(row_count, col, item)
        
        self.update_row_count()
        self.auto_save_csv()
        self.statusBar().showMessage("Empty row added")
    
    def clear_all_data(self):
        """Clear all data from the table."""
        if self.table.rowCount() == 0:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Clear", 
            "Are you sure you want to clear all data?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.table.setRowCount(0)
            self.update_row_count()
            self.auto_save_csv()
            self.statusBar().showMessage("All data cleared")
    
    def update_autofill_memory(self, row_index):
        """Remember last used Persona/Release/Reel Type values from a given row"""
        try:
            for key in ("Persona", "Release", "Reel Type"):
                col = self.columns.index(key)
                item = self.table.item(row_index, col)
                if item and item.text().strip():
                    self.last_autofill[key] = item.text().strip()
        except Exception:
            pass

    def add_reel_to_table(self, data):
        """Add a reel to the table with the provided data."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.table.setItem(row_count, col, item)

        # Remember autofill values from this newly added row
        self.update_autofill_memory(row_count)
        """Add a reel to the table with the provided data."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.table.setItem(row_count, col, item)
    
    def update_reel_in_table(self, row, data):
        """Update a specific row in the table with new data."""
        for col, value in enumerate(data):
            item = self.table.item(row, col)
            if item:
                item.setText(str(value))
            else:
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.table.setItem(row, col, item)
        # Update autofill memory after change
        self.update_autofill_memory(row)
            
    def load_csv(self):
        """Load CSV file and populate the table."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load CSV File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Read CSV using pandas
                df = pd.read_csv(file_path)
                
                # Filter to only include defined columns, add missing ones as empty
                filtered_df = pd.DataFrame()
                for col in self.columns:
                    if col in df.columns:
                        filtered_df[col] = df[col]
                    else:
                        filtered_df[col] = ""
                
                # Populate table
                self.populate_table_from_dataframe(filtered_df)
                self.update_row_count()
                
                # Save as last loaded CSV if config manager is available
                if self.config_manager:
                    self.config_manager.set_last_csv_path(file_path)
                
                # Update CSV path display
                self.update_csv_path_display(file_path)
                
                self.statusBar().showMessage(f"Loaded {len(filtered_df)} rows from CSV")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file:\\n{str(e)}")
                
    def save_csv(self):
        """Save current table contents to CSV file."""
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "No data to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Extract data from table
                data = []
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
                
                # Create DataFrame and save to CSV
                df = pd.DataFrame(data, columns=self.columns)
                df.to_csv(file_path, index=False)
                
                # Save as last loaded CSV if config manager is available
                if self.config_manager:
                    self.config_manager.set_last_csv_path(file_path)
                
                # Update CSV path display
                self.update_csv_path_display(file_path)
                
                self.statusBar().showMessage(f"Saved {len(data)} rows to CSV")
                QMessageBox.information(self, "Success", "CSV file saved successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save CSV file:\\n{str(e)}")
                
    def populate_table_from_dataframe(self, df):
        """Populate table widget from pandas DataFrame."""
        # Clear existing data
        self.table.setRowCount(0)
        
        # Set number of rows
        self.table.setRowCount(len(df))
        
        # Populate data
        for row_idx, (_, row_data) in enumerate(df.iterrows()):
            for col_idx, col_name in enumerate(self.columns):
                value = str(row_data[col_name]) if pd.notna(row_data[col_name]) else ""
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)
    
    def auto_load_last_csv(self):
        """Auto-load the last CSV file if enabled and file exists."""
        if not self.config_manager or not self.config_manager.should_auto_load_csv():
            return
            
        last_csv_path = self.config_manager.get_last_csv_path()
        if last_csv_path and os.path.exists(last_csv_path):
            try:
                # Read CSV using pandas
                df = pd.read_csv(last_csv_path)
                
                # Filter to only include defined columns, add missing ones as empty
                filtered_df = pd.DataFrame()
                for col in self.columns:
                    if col in df.columns:
                        filtered_df[col] = df[col]
                    else:
                        filtered_df[col] = ""
                
                # Populate table
                self.populate_table_from_dataframe(filtered_df)
                self.update_row_count()
                
                # Update CSV path display
                self.update_csv_path_display(last_csv_path)
                
                self.statusBar().showMessage(f"Auto-loaded {len(filtered_df)} rows from: {os.path.basename(last_csv_path)}")
                
            except Exception as e:
                self.statusBar().showMessage(f"Could not auto-load CSV: {str(e)}")
                safe_print(f"Auto-load error: {e}")


    def update_csv_path_display(self, csv_path):
        """Update the CSV path display label."""
        if csv_path:
            display_path = os.path.abspath(csv_path)
            # Truncate long paths for display
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            self.csv_path_label.setText(f"CSV: {display_path}")
            self.csv_path_label.setToolTip(f"Full path: {os.path.abspath(csv_path)}")
        else:
            self.csv_path_label.setText("No CSV loaded")
            self.csv_path_label.setToolTip("")


class ReleaseBreakdownDialog(QDialog):
    """Dialog showing breakdown of reels by release."""
    
    def __init__(self, parent, release_counts):
        super().__init__(parent)
        self.release_counts = release_counts
        self.setWindowTitle("Release Breakdown")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the breakdown dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("📊 Release Breakdown")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Summary info
        total_reels = sum(self.release_counts.values())
        total_releases = len(self.release_counts)
        summary_label = QLabel(f"Total: {total_reels} reels across {total_releases} releases")
        summary_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 5px;")
        summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(summary_label)
        
        # Release breakdown table
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(3)
        self.breakdown_table.setHorizontalHeaderLabels(["Release", "Count", "Progress"])
        
        # Populate table
        sorted_releases = sorted(self.release_counts.items(), key=lambda x: x[1], reverse=True)
        self.breakdown_table.setRowCount(len(sorted_releases))
        
        goal = 124
        for row, (release_name, count) in enumerate(sorted_releases):
            # Release name
            name_item = QTableWidgetItem(release_name)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.breakdown_table.setItem(row, 0, name_item)
            
            # Count
            count_item = QTableWidgetItem(f"{count}")
            count_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.breakdown_table.setItem(row, 1, count_item)
            
            # Progress
            progress_percent = (count / goal) * 100
            if count >= goal:
                progress_text = f"🎉 {progress_percent:.1f}% - COMPLETE!"
                count_item.setBackground(Qt.green)
            elif count >= goal * 0.9:
                progress_text = f"🔥 {progress_percent:.1f}% - Almost there!"
                count_item.setBackground(Qt.yellow)
            elif count >= goal * 0.75:
                progress_text = f"⚡ {progress_percent:.1f}% - Good progress"
                count_item.setBackground(Qt.cyan)
            else:
                progress_text = f"{progress_percent:.1f}%"
            
            progress_item = QTableWidgetItem(progress_text)
            progress_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.breakdown_table.setItem(row, 2, progress_item)
        
        # Configure table appearance
        header = self.breakdown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Release name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Count fits content
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Progress stretches
        
        self.breakdown_table.setAlternatingRowColors(True)
        self.breakdown_table.setSortingEnabled(True)
        
        layout.addWidget(self.breakdown_table)
        
        # Goal info
        goal_info = QLabel(f"🎯 Goal: {goal} reels per release")
        goal_info.setStyleSheet("color: #34495e; font-weight: bold; margin: 5px;")
        goal_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(goal_info)
        
        # Close button
        from PyQt5.QtWidgets import QDialogButtonBox
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Reel Tracker Enhanced")
    app.setApplicationVersion("3.0")
    
    # Create and show main window
    window = ReelTrackerApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()