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
import datetime
import threading
import time
# File locking imports with fallback
try:
    import fcntl  # For file locking on Unix-like systems
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import msvcrt  # For file locking on Windows
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QHeaderView, QLabel, QFrame, QItemDelegate,
    QMenuBar, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QCheckBox, QProgressBar, QStatusBar
)
# Explicit import to ensure availability even if list above changes
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon

from .config_manager import ConfigManager
from .media_randomizer import MediaRandomizerDialog
from .reel_dialog import ReelEntryDialog
from .bulk_edit_dialog import BulkEditDialog
from .default_metadata_dialog import DefaultMetadataDialog
from .file_organization_dialog import FileOrganizationDialog
from .backup_manager import BackupManager
from .custom_item_manager import CustomItemManagerDialog
from .utils import safe_print


class CSVProtectionManager:
    """
    Enhanced CSV protection manager with file locking, data validation, and auto-save debouncing.
    Prevents CSV corruption by ensuring atomic writes and validating data before saving.
    """
    
    def __init__(self, csv_path=None):
        self.csv_path = csv_path
        self.lock = threading.Lock()
        self.last_save_time = 0
        self.debounce_delay = 0.5  # 500ms debounce
        self.save_timer = None
        self.pending_save = False
        
    def lock_file(self, file_handle):
        """Cross-platform file locking with fallback."""
        try:
            if sys.platform == "win32" and HAS_MSVCRT:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            elif HAS_FCNTL:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            else:
                # File locking not available, proceed without locking
                safe_print("⚠️ File locking not available on this system")
                return True
        except (OSError, IOError):
            return False
    
    def unlock_file(self, file_handle):
        """Cross-platform file unlocking with fallback."""
        try:
            if sys.platform == "win32" and HAS_MSVCRT:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            elif HAS_FCNTL:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except (OSError, IOError):
            pass
    
    def validate_data(self, data, columns):
        """
        Validate data before saving to prevent empty or corrupted CSV writes.
        """
        if not data:
            return False, "Data is empty"
        
        if not columns:
            return False, "Columns are empty"
        
        if len(data) == 0:
            return False, "No rows to save"
        
        # Check if all rows have the correct number of columns
        expected_cols = len(columns)
        for i, row in enumerate(data):
            if len(row) != expected_cols:
                return False, f"Row {i} has {len(row)} columns, expected {expected_cols}"
        
        # Additional validation: ensure at least one row has meaningful data
        has_meaningful_data = False
        for row in data:
            if any(str(cell).strip() for cell in row):
                has_meaningful_data = True
                break
        
        if not has_meaningful_data:
            return False, "All rows appear to be empty"
        
        return True, "Data validation passed"
    
    def safe_csv_write(self, data, columns, csv_path, backup_manager=None):
        """
        Safely write CSV with file locking, validation, and backup protection.
        """
        with self.lock:
            # Validate data first
            is_valid, validation_msg = self.validate_data(data, columns)
            if not is_valid:
                safe_print(f"❌ CSV Write Blocked: {validation_msg}")
                return False, f"Data validation failed: {validation_msg}"
            
            # Create backup before writing if backup manager available
            if backup_manager and os.path.exists(csv_path):
                try:
                    backup_path = backup_manager.create_pre_save_backup()
                    if backup_path:
                        safe_print(f"🛡️ Backup created before save: {backup_path}")
                except Exception as e:
                    safe_print(f"❌ Backup creation failed: {e}")
                    return False, f"Backup creation failed: {e}"
            
            # Write CSV with file locking
            temp_path = csv_path + ".tmp"
            try:
                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)
                
                # Write to temporary file first
                with open(temp_path, 'w', newline='', encoding='utf-8') as temp_file:
                    if not self.lock_file(temp_file):
                        return False, "Could not acquire file lock"
                    
                    try:
                        df.to_csv(temp_file, index=False)
                        temp_file.flush()
                        os.fsync(temp_file.fileno())  # Force write to disk
                    finally:
                        self.unlock_file(temp_file)
                
                # Atomic move from temp to final location
                if os.path.exists(csv_path):
                    os.replace(temp_path, csv_path)
                else:
                    os.rename(temp_path, csv_path)
                
                safe_print(f"✅ CSV safely written: {len(data)} rows to {csv_path}")
                return True, f"Successfully saved {len(data)} rows"
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                safe_print(f"❌ CSV write failed: {e}")
                return False, f"Write operation failed: {e}"
    
    def debounced_save(self, data, columns, csv_path, backup_manager=None, callback=None):
        """
        Debounced save to prevent multiple rapid saves from corrupting the file.
        """
        def perform_save():
            success, message = self.safe_csv_write(data, columns, csv_path, backup_manager)
            if callback:
                callback(success, message)
            self.pending_save = False
        
        # Cancel any pending save
        if self.save_timer:
            self.save_timer.cancel()
        
        # Mark as pending and schedule new save
        self.pending_save = True
        self.save_timer = threading.Timer(self.debounce_delay, perform_save)
        self.save_timer.start()


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
        
        # Initialize backup manager for data protection
        self.backup_manager = None
        self.csv_path = None
        
        # Initialize CSV protection manager
        self.csv_protection = CSVProtectionManager()
        
        self.setWindowTitle("BEDROT REEL TRACKER // CYBERCORE CONTENT MANAGEMENT")
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
    
    def apply_bedrot_theme(self):
        """Apply BEDROT's cyberpunk dark theme to the application."""
        dark_theme = """
        QMainWindow {
            background-color: #121212;
            color: #e0e0e0;
        }
        
        QWidget {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }
        
        QTableWidget {
            background-color: #151515;
            color: #cccccc;
            gridline-color: #2a2a2a;
            selection-background-color: rgba(0, 255, 255, 0.3);
            selection-color: #ffffff;
            border: 1px solid #404040;
            border-radius: 4px;
            font-size: 12px;
            alternate-background-color: #1a1a1a;
        }
        
        QTableWidget::item {
            padding: 5px;
            border: none;
            background-color: #1a1a1a;
            color: #cccccc;
        }
        
        QTableWidget::item:alternate {
            background-color: #202020;
        }
        
        QTableWidget::item:selected {
            background-color: rgba(0, 255, 255, 0.2);
            color: #00ffff;
            border: 1px solid #00ffff;
        }
        
        QTableWidget::item:hover {
            background-color: #252525;
            color: #00ff88;
        }
        
        QHeaderView::section {
            background-color: #0f0f0f;
            color: #00ffff;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #00ffff;
            border-right: 1px solid #2a2a2a;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }
        
        QHeaderView::section:hover {
            background-color: #2a2a2a;
        }
        
        QPushButton {
            background-color: #2a2a2a;
            color: #00ff88;
            border: 1px solid #00ff88;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #3a3a3a;
            border: 1px solid #00ffff;
            color: #00ffff;
        }
        
        QPushButton:pressed {
            background-color: #1a1a1a;
        }
        
        QPushButton:disabled {
            background-color: #1a1a1a;
            color: #555555;
            border: 1px solid #333333;
        }
        
        QLabel {
            color: #ffffff;
            background-color: transparent;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 5px;
            font-family: 'Segoe UI', sans-serif;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QComboBox {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 5px;
            min-width: 100px;
        }
        
        QComboBox:hover {
            border: 1px solid #00ffff;
        }
        
        QComboBox:focus {
            border: 1px solid #ff00ff;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #00ff88;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #1a1a1a;
            color: #00ff88;
            border: 1px solid #00ffff;
            selection-background-color: #ff00ff;
            selection-color: #000000;
        }
        
        QMenuBar {
            background-color: #0a0a0a;
            color: #ffffff;
            border-bottom: 1px solid #333333;
        }
        
        QMenuBar::item:selected {
            background-color: #2a2a2a;
            color: #00ffff;
        }
        
        QMenu {
            background-color: #1a1a1a;
            color: #ffffff;
            border: 1px solid #00ffff;
        }
        
        QMenu::item:selected {
            background-color: #ff00ff;
            color: #000000;
        }
        
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
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        }
        
        QScrollBar::handle:vertical:pressed {
            background-color: #00cccc;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
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
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        }
        
        QScrollBar::handle:horizontal:pressed {
            background-color: #00cccc;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            background: none;
            width: 0px;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        
        QProgressBar {
            background-color: #1a1a1a;
            border: 1px solid #333333;
            border-radius: 4px;
            text-align: center;
            color: #ffffff;
        }
        
        QProgressBar::chunk {
            background-color: #00ff88;
            border-radius: 3px;
        }
        
        QStatusBar {
            background-color: #0a0a0a;
            color: #00ff88;
            border-top: 1px solid #333333;
        }
        
        QFrame[frameShape="4"] {
            color: #333333;
            max-height: 2px;
        }
        
        QFrame[frameShape="5"] {
            color: #333333;
            max-width: 2px;
        }
        """
        self.setStyleSheet(dark_theme)
        
    def init_ui(self):
        """Initialize the user interface components."""
        # Apply BEDROT dark theme
        self.apply_bedrot_theme()
        
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
        self.add_row_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 136, 0.8);
                color: #000000;
                font-weight: bold;
                padding: 6px 10px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 136, 0.9);
                box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
            }
            QPushButton:pressed {
                background-color: #00cc66;
            }
        """)
        button_layout.addWidget(self.add_row_button)
        
        self.randomize_reel_button = QPushButton("🎲 Random Reel")
        self.randomize_reel_button.clicked.connect(self.add_random_reel)
        self.randomize_reel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 255, 0.8);
                color: #000000;
                font-weight: bold;
                padding: 6px 10px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.9);
                box-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: #00cccc;
            }
        """)
        button_layout.addWidget(self.randomize_reel_button)
        
        self.manage_release_button = QPushButton("📋 Manage Release Values")
        self.manage_release_button.clicked.connect(self.manage_release_values)
        self.manage_release_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 255, 0.8);
                color: #000000;
                font-weight: bold;
                padding: 6px 8px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 255, 0.9);
                box-shadow: 0 0 8px rgba(255, 0, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: #cc00cc;
            }
        """)
        button_layout.addWidget(self.manage_release_button)
        
        self.default_metadata_button = QPushButton("🏷️ Default Metadata")
        self.default_metadata_button.clicked.connect(self.open_default_metadata)
        self.default_metadata_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 170, 0.8);
                color: #000000;
                font-weight: bold;
                padding: 6px 8px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 170, 0.9);
                box-shadow: 0 0 8px rgba(255, 0, 170, 0.3);
            }
            QPushButton:pressed {
                background-color: #cc0088;
            }
        """)
        button_layout.addWidget(self.default_metadata_button)
        
        self.file_organization_button = QPushButton("📁 Organize Files")
        self.file_organization_button.clicked.connect(self.open_file_organization)
        self.file_organization_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 136, 0, 0.8);
                color: #000000;
                font-weight: bold;
                padding: 6px 10px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 130px;
            }
            QPushButton:hover {
                background-color: rgba(255, 136, 0, 0.9);
                box-shadow: 0 0 8px rgba(255, 136, 0, 0.3);
            }
            QPushButton:pressed {
                background-color: #cc6600;
            }
        """)
        button_layout.addWidget(self.file_organization_button)
        
        self.edit_row_button = QPushButton("✏️ Edit Selected")
        self.edit_row_button.clicked.connect(self.edit_selected_reel)
        self.edit_row_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00ffff;
                border: 1px solid #00ffff;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.1);
                box-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(0, 255, 255, 0.2);
            }
        """)
        button_layout.addWidget(self.edit_row_button)
        
        self.duplicate_row_button = QPushButton("[COPY] Duplicate")
        self.duplicate_row_button.clicked.connect(self.duplicate_selected_reel)
        self.duplicate_row_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00ff88;
                border: 1px solid #00ff88;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 130px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 136, 0.1);
                box-shadow: 0 0 5px rgba(0, 255, 136, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(0, 255, 136, 0.2);
            }
        """)
        button_layout.addWidget(self.duplicate_row_button)
        
        self.delete_row_button = QPushButton("🗑️ Delete")
        self.delete_row_button.clicked.connect(self.delete_selected_reel)
        self.delete_row_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff0066;
                border: 1px solid #ff0066;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                text-transform: uppercase;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 102, 0.1);
                box-shadow: 0 0 5px rgba(255, 0, 102, 0.3);
                color: #ff3388;
            }
            QPushButton:pressed {
                background-color: rgba(255, 0, 102, 0.2);
            }
        """)
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
        
        # Add stretch to push buttons to the left
        button_layout.addStretch()
        
        # Row counter and stats
        self.row_count_label = QLabel("Rows: 0")
        self.row_count_label.setStyleSheet("font-weight: bold; color: #00ff88;")
        button_layout.addWidget(self.row_count_label)
        
        # Release reel counter (now a clickable button)
        self.release_counter_button = QPushButton("Reels: 0/124")
        self.release_counter_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                color: #00ffff;
                padding: 4px 8px;
                border: 1px solid #00ffff;
                border-radius: 4px;
                background: transparent;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.1);
                border: 1px solid #66ffff;
            }
        """)
        self.release_counter_button.clicked.connect(self.show_release_breakdown)
        button_layout.addWidget(self.release_counter_button)
        
        # Store current release filter
        self.current_release_filter = None
        
        # CSV path display
        self.csv_path_label = QLabel("No CSV loaded")
        self.csv_path_label.setStyleSheet("color: #888888; font-size: 10px; max-width: 300px;")
        self.csv_path_label.setWordWrap(True)
        button_layout.addWidget(self.csv_path_label)
        
        # Config status indicator
        self.config_status_label = QLabel("[CONFIG] Ready")
        self.config_status_label.setStyleSheet("color: #00ff88; font-size: 10px;")
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
            config_info += f"**{display_name}:** ({len(values)} values)\n"
            for value in values[:10]:  # Show first 10 values
                config_info += f"  • {value}\n" if value else "  • (empty)\n"
            if len(values) > 10:
                config_info += f"  ... and {len(values) - 10} more\n"
            config_info += "\n"
        
        last_csv = self.config_manager.get_last_csv_path()
        # Add default metadata info
        defaults = self.config_manager.get_default_metadata()
        config_info += f"**Default Metadata:**\n"
        config_info += f"  • Persona: {defaults.get('persona', 'None')}\n"
        config_info += f"  • Release: {defaults.get('release', 'None')}\n"
        config_info += f"  • Reel Type: {defaults.get('reel_type', 'None')}\n\n"
        
        config_info += f"**Last CSV:** {last_csv or 'None'}\n"
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
            f"Configuration file location:\n\n{config_path}\n\nYou can edit this file manually if needed."
        )

    def setup_table(self):
        """Setup the table widget with proper columns and drag-drop support."""
        # Set column count and headers
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        # Enable drag and drop
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.DropOnly)
        
        # Configure scrollbars
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Configure table appearance
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Enable alternating row colors
        self.table.setAlternatingRowColors(True)
        
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
        
        # Only apply goal achievement styling for individual releases, not global count
        if self.current_release_filter and reel_count >= goal:
            # Goal achieved for specific release - change styling and add achievement badge
            self.release_counter_button.setText(f"🎉 {counter_text} - GOAL ACHIEVED! 🎉")
            self.release_counter_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: #000000;
                    background-color: #00ff88;
                    padding: 4px 8px;
                    border: 2px solid #00ff88;
                    border-radius: 4px;
                    box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
                }
                QPushButton:hover {
                    background-color: #00ffaa;
                    box-shadow: 0 0 30px rgba(0, 255, 136, 0.7);
                }
            """)
        elif self.current_release_filter and reel_count >= goal * 0.9:  # 90% of goal for specific release
            # Close to goal - orange styling
            self.release_counter_button.setText(f"🔥 {counter_text}")
            self.release_counter_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: #000000;
                    background-color: #ff8800;
                    padding: 4px 8px;
                    border: 2px solid #ff8800;
                    border-radius: 4px;
                    box-shadow: 0 0 15px rgba(255, 136, 0, 0.5);
                }
                QPushButton:hover {
                    background-color: #ffaa00;
                    box-shadow: 0 0 20px rgba(255, 136, 0, 0.7);
                }
            """)
        elif self.current_release_filter and reel_count >= goal * 0.75:  # 75% of goal for specific release
            # Good progress - yellow styling
            self.release_counter_button.setText(f"⚡ {counter_text}")
            self.release_counter_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: #ffaa00;
                    padding: 4px 8px;
                    border: 1px solid #ffaa00;
                    border-radius: 4px;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(255, 170, 0, 0.1);
                    border: 1px solid #ffcc00;
                }
            """)
        else:
            # Normal progress - blue styling (for both global count and individual releases)
            self.release_counter_button.setText(counter_text)
            self.release_counter_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: #00ffff;
                    padding: 4px 8px;
                    border: 1px solid #00ffff;
                    border-radius: 4px;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(0, 255, 255, 0.1);
                    border: 1px solid #66ffff;
                }
            """)
    
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
        """
        Automatically save CSV with enhanced protection against corruption.
        Uses file locking, data validation, and debouncing to prevent issues.
        """
        if not self.config_manager:
            safe_print("❌ Auto-save skipped: No config manager")
            return False
            
        last_csv_path = self.config_manager.get_last_csv_path()
        if not last_csv_path:
            safe_print("❌ Auto-save skipped: No CSV path configured")
            return False
        
        # Enhanced validation: Check table state
        if self.table.rowCount() == 0:
            safe_print("❌ Auto-save skipped: Table is empty")
            return False
        
        # Prevent spam logging when a save is already pending
        if hasattr(self.csv_protection, 'pending_save') and self.csv_protection.pending_save:
            return True  # Save already pending, don't log again
        
        try:
            # Extract data from table with enhanced error handling
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    try:
                        item = self.table.item(row, col)
                        cell_value = item.text() if item and item.text() is not None else ""
                        row_data.append(str(cell_value))
                    except Exception as e:
                        safe_print(f"❌ Error reading cell [{row},{col}]: {e}")
                        row_data.append("")  # Use empty string as fallback
                data.append(row_data)
            
            # Additional validation before saving
            if not data:
                safe_print("❌ Auto-save skipped: No data extracted from table")
                return False
            
            # Use debounced protected save
            def save_callback(success, message):
                if success:
                    self.statusBar().showMessage(f"Auto-saved: {message}", 2000)
                else:
                    self.statusBar().showMessage(f"Auto-save failed: {message}", 3000)
                    safe_print(f"❌ Auto-save failed: {message}")
            
            self.csv_protection.debounced_save(
                data=data,
                columns=self.columns,
                csv_path=last_csv_path,
                backup_manager=self.backup_manager,
                callback=save_callback
            )
            
            safe_print(f"🔄 Auto-save queued: {len(data)} rows")
            return True
            
        except Exception as e:
            safe_print(f"❌ Auto-save failed with exception: {e}")
            self.statusBar().showMessage(f"Auto-save error: {str(e)}", 3000)
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
        
        dialog = FileOrganizationDialog(self, self.config_manager, reel_data_list, self.update_csv_after_organization)
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("File organization settings updated")
    
    def update_csv_after_organization(self, reel_id, new_filepath, new_filename):
        """Update CSV after successful file organization."""
        try:
            # Find the row with matching Reel ID
            reel_id_col = self.columns.index("Reel ID")
            filepath_col = self.columns.index("FilePath")
            filename_col = self.columns.index("Clip Filename")
            
            updated_rows = 0
            for row in range(self.table.rowCount()):
                reel_id_item = self.table.item(row, reel_id_col)
                if reel_id_item and reel_id_item.text().strip() == reel_id:
                    # Update FilePath
                    filepath_item = self.table.item(row, filepath_col)
                    if filepath_item:
                        filepath_item.setText(new_filepath)
                    else:
                        filepath_item = QTableWidgetItem(new_filepath)
                        filepath_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                        self.table.setItem(row, filepath_col, filepath_item)
                    
                    # Update Clip Filename
                    filename_item = self.table.item(row, filename_col)
                    if filename_item:
                        filename_item.setText(new_filename)
                    else:
                        filename_item = QTableWidgetItem(new_filename)
                        filename_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                        self.table.setItem(row, filename_col, filename_item)
                    
                    updated_rows += 1
                    safe_print(f"[CSV_UPDATE] Updated row for reel {reel_id}: {new_filename} at {new_filepath}")
            
            if updated_rows > 0:
                # Immediately save CSV after updates
                self.auto_save_csv()
                safe_print(f"[CSV_UPDATE] Successfully updated {updated_rows} row(s) for reel {reel_id}")
            else:
                safe_print(f"[CSV_UPDATE] Warning: No rows found for reel ID: {reel_id}")
                
        except Exception as e:
            safe_print(f"[CSV_UPDATE] Error updating CSV for reel {reel_id}: {e}")
    
    def manage_release_values(self):
        """Open the custom item manager dialog to manage release dropdown values."""
        dialog = CustomItemManagerDialog(self, "release", self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            # Refresh the table delegates to show updated dropdown values
            self.setup_dropdown_delegates()
            self.statusBar().showMessage("Release values updated successfully")
    
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
        
        # Auto-generate Reel ID with sequential numbering
        # Find the highest existing REEL_XXX number
        max_num = 0
        for row in range(self.table.rowCount()):
            if row == row_count:  # Skip the row we just added
                continue
            item = self.table.item(row, reel_id_col)
            if item:
                existing_id = item.text()
                # Extract number from patterns like REEL_001, RP_001, etc.
                import re
                match = re.search(r'_(\d+)$', existing_id)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)
        
        # Generate next ID
        next_num = max_num + 1
        reel_id = f"REEL_{next_num:03d}"
        self.table.item(row_count, reel_id_col).setText(reel_id)
        
        # Populate file path & name
        self.table.item(row_count, filepath_col).setText(file_path)
        filename = os.path.basename(file_path)
        self.table.item(row_count, filename_col).setText(filename)
        
        # Apply default metadata if available
        if self.config_manager:
            defaults = self.config_manager.get_default_metadata()
            safe_print(f"[DEBUG] Retrieved defaults: {defaults}")
            
            # Apply default persona (apply even if empty string)
            if "persona" in defaults:
                self.table.item(row_count, persona_col).setText(defaults["persona"])
                safe_print(f"[DEBUG] Applied persona: '{defaults['persona']}'")
            
            # Apply default release (apply even if empty string)
            if "release" in defaults:
                self.table.item(row_count, release_col).setText(defaults["release"])
                safe_print(f"[DEBUG] Applied release: '{defaults['release']}'")
            
            # Apply default reel type (apply even if empty string)
            if "reel_type" in defaults:
                self.table.item(row_count, reel_type_col).setText(defaults["reel_type"])
                safe_print(f"[DEBUG] Applied reel_type: '{defaults['reel_type']}'")
            
            # Apply default caption template
            if "caption_template" in defaults and defaults["caption_template"]:
                caption_template = defaults["caption_template"]
                # Replace {filename} placeholder with actual filename
                caption = caption_template.replace("{filename}", filename)
                self.table.item(row_count, caption_col).setText(caption)
                safe_print(f"[DEBUG] Applied caption: '{caption}'")
            
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
        """Clear all data from the table with CRITICAL backup protection."""
        if self.table.rowCount() == 0:
            return
        
        # CRITICAL: Create backup before clearing data
        backup_created = False
        if self.backup_manager and self.csv_path:
            try:
                backup_path = self.backup_manager.create_pre_clear_backup()
                if backup_path:
                    backup_created = True
                    safe_print(f"🛡️ CRITICAL BACKUP created before clear: {backup_path}")
            except Exception as e:
                safe_print(f"❌ Failed to create backup: {e}")
        
        # Enhanced warning message
        warning_msg = "⚠️ DANGER: This will permanently delete ALL reel data!\n\n"
        if backup_created:
            warning_msg += "✅ Backup created successfully.\n"
        else:
            warning_msg += "❌ Could not create backup! This is VERY DANGEROUS!\n"
        warning_msg += "\nAre you absolutely sure you want to clear all data?"
        
        reply = QMessageBox.question(
            self, "⚠️ CONFIRM CLEAR ALL DATA", 
            warning_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.table.setRowCount(0)
            self.update_row_count()
            # NEVER auto-save after clearing data - this would overwrite the CSV with empty data!
            # This was the bug that caused the original data loss
            self.statusBar().showMessage("All data cleared - CSV NOT auto-saved to prevent data loss")
    
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
                
                # Initialize backup manager for this CSV
                self.csv_path = file_path
                try:
                    self.backup_manager = BackupManager(file_path)
                    safe_print(f"🛡️ Backup protection activated for: {file_path}")
                except Exception as e:
                    safe_print(f"❌ Could not initialize backup manager: {e}")
                    self.backup_manager = None
                
                # Initialize CSV protection manager for this file
                self.csv_protection.csv_path = file_path
                
                # Update CSV path display
                self.update_csv_path_display(file_path)
                
                self.statusBar().showMessage(f"Loaded {len(filtered_df)} rows from CSV")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file:\n{str(e)}")
                
    def save_csv(self):
        """Save current table contents to CSV file with enhanced protection."""
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "No data to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Extract data from table with enhanced error handling
                data = []
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        try:
                            item = self.table.item(row, col)
                            cell_value = item.text() if item and item.text() is not None else ""
                            row_data.append(str(cell_value))
                        except Exception as e:
                            safe_print(f"❌ Error reading cell [{row},{col}]: {e}")
                            row_data.append("")  # Use empty string as fallback
                    data.append(row_data)
                
                # Use protected save mechanism
                success, message = self.csv_protection.safe_csv_write(
                    data=data,
                    columns=self.columns,
                    csv_path=file_path,
                    backup_manager=self.backup_manager
                )
                
                if success:
                    # Initialize/update backup manager for this CSV path
                    self.csv_path = file_path
                    try:
                        self.backup_manager = BackupManager(file_path)
                        safe_print(f"🛡️ Backup protection activated for: {file_path}")
                    except Exception as e:
                        safe_print(f"❌ Could not initialize backup manager: {e}")
                        self.backup_manager = None
                    
                    # Update CSV protection manager path
                    self.csv_protection.csv_path = file_path
                    
                    # Save as last loaded CSV if config manager is available
                    if self.config_manager:
                        self.config_manager.set_last_csv_path(file_path)
                    
                    # Update CSV path display
                    self.update_csv_path_display(file_path)
                    
                    self.statusBar().showMessage(f"Saved {len(data)} rows to CSV")
                    QMessageBox.information(self, "Success", f"CSV file saved successfully!\n{message}")
                else:
                    QMessageBox.critical(self, "Save Failed", f"Failed to save CSV file:\n{message}")
                
            except Exception as e:
                safe_print(f"❌ Save CSV failed with exception: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save CSV file:\n{str(e)}")
                
    def populate_table_from_dataframe(self, df):
        """Populate table widget from pandas DataFrame."""
        # Block signals during population to prevent infinite auto-save loop
        self.table.blockSignals(True)
        try:
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
        finally:
            # Always restore signals even if an exception occurs
            self.table.blockSignals(False)
    
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
                
                # Initialize backup manager for this CSV
                self.csv_path = last_csv_path
                try:
                    self.backup_manager = BackupManager(last_csv_path)
                    safe_print(f"🛡️ Backup protection activated for: {last_csv_path}")
                except Exception as e:
                    safe_print(f"❌ Could not initialize backup manager: {e}")
                    self.backup_manager = None
                
                # Initialize CSV protection manager for this file
                self.csv_protection.csv_path = last_csv_path
                
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