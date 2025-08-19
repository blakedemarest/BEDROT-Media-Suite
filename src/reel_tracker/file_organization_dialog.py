# -*- coding: utf-8 -*-
"""
File Organization Dialog Module for Reel Tracker.

Provides functionality for:
- Master export folder configuration
- File organization settings management
- Batch file organization with progress tracking
- Preview functionality
- Safe testing mode controls
"""

import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QTextEdit, 
    QDialogButtonBox, QFileDialog, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QSplitter, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from .config_manager import ConfigManager
from .file_organizer import FileOrganizer
from .utils import safe_print
from .ui_styles import apply_dialog_theme, style_button, style_header_label, get_dialog_button_box_style


class FileOrganizationThread(QThread):
    """Thread for handling file organization operations."""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_completed = pyqtSignal(dict)  # results
    csv_update_requested = pyqtSignal(str, str, str)  # reel_id, new_filepath, new_filename
    
    def __init__(self, file_organizer, reel_data_list, enable_csv_updates=False):
        super().__init__()
        self.file_organizer = file_organizer
        self.reel_data_list = reel_data_list
        self.enable_csv_updates = enable_csv_updates
        self.results = {}
    
    def progress_callback(self, current, total, reel_data):
        """Callback for progress updates."""
        # Get filepath index based on data length (7 for old format, 8 for new with Aspect Ratio)
        filepath_index = 6 if len(reel_data) == 7 else 7
        message = f"Processing: {reel_data[0]} - {os.path.basename(reel_data[filepath_index])}"
        self.progress_updated.emit(current, total, message)
    
    def csv_update_callback(self, reel_id, new_filepath, new_filename):
        """Callback for CSV updates after successful file organization."""
        if self.enable_csv_updates:
            self.csv_update_requested.emit(reel_id, new_filepath, new_filename)
    
    def run(self):
        """Run the file organization process."""
        try:
            self.results = self.file_organizer.organize_batch(
                self.reel_data_list, 
                self.progress_callback,
                self.csv_update_callback if self.enable_csv_updates else None
            )
            self.operation_completed.emit(self.results)
        except Exception as e:
            self.results = {"success": False, "message": f"Thread error: {e}"}
            self.operation_completed.emit(self.results)


class FileOrganizationDialog(QDialog):
    """
    Dialog for managing file organization settings and operations.
    """
    
    def __init__(self, parent=None, config_manager=None, reel_data_list=None, csv_update_callback=None):
        super().__init__(parent)
        self.setWindowTitle("File Organization Pipeline")
        self.setModal(True)
        self.resize(900, 700)
        
        # Apply BEDROT theme
        apply_dialog_theme(self)
        
        # Initialize components
        self.config_manager = config_manager or ConfigManager()
        self.file_organizer = FileOrganizer(self.config_manager)
        self.reel_data_list = reel_data_list or []
        self.csv_update_callback = csv_update_callback
        self.organization_thread = None
        
        self.setup_ui()
        self.load_current_settings()
        
        # Generate preview if reel data is provided
        if self.reel_data_list:
            self.update_preview()
    
    def setup_ui(self):
        """Setup the dialog UI with tabs for different functions."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("FILE ORGANIZATION PIPELINE")
        style_header_label(header_label)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_settings_tab()
        self.setup_preview_tab()
        self.setup_organize_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.setStyleSheet(get_dialog_button_box_style())
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def setup_settings_tab(self):
        """Setup the settings configuration tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Master Export Folder Section
        export_group = QGroupBox("MASTER EXPORT FOLDER")
        export_layout = QFormLayout()
        
        # Export folder path
        folder_layout = QHBoxLayout()
        self.export_folder_edit = QLineEdit()
        self.export_folder_edit.setPlaceholderText("Select the master folder where organized files will be stored...")
        self.browse_folder_btn = QPushButton("Browse...")
        style_button(self.browse_folder_btn, 'primary')
        self.browse_folder_btn.clicked.connect(self.browse_export_folder)
        folder_layout.addWidget(self.export_folder_edit)
        folder_layout.addWidget(self.browse_folder_btn)
        export_layout.addRow("Export Folder:", folder_layout)
        
        # Export folder info
        self.folder_info_label = QLabel("No folder selected")
        from .ui_styles import style_status_label
        style_status_label(self.folder_info_label, 'info')
        export_layout.addRow("Status:", self.folder_info_label)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # File Organization Settings
        settings_group = QGroupBox("ORGANIZATION SETTINGS")
        settings_layout = QFormLayout()
        
        # Safe testing mode
        self.safe_mode_checkbox = QCheckBox("Safe Testing Mode (Copy files instead of moving)")
        self.safe_mode_checkbox.setToolTip("When enabled, files are copied to the destination, preserving originals")
        settings_layout.addRow("", self.safe_mode_checkbox)
        
        # Overwrite protection
        self.overwrite_protection_checkbox = QCheckBox("Overwrite Protection (Skip if file exists)")
        self.overwrite_protection_checkbox.setToolTip("When enabled, existing files are skipped to prevent overwrites")
        settings_layout.addRow("", self.overwrite_protection_checkbox)
        
        # Auto-organize enabled
        self.auto_organize_checkbox = QCheckBox("Enable Auto-Organization")
        self.auto_organize_checkbox.setToolTip("When enabled, files can be automatically organized")
        settings_layout.addRow("", self.auto_organize_checkbox)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Naming Convention Info
        naming_group = QGroupBox("NAMING CONVENTION")
        naming_layout = QVBoxLayout()
        
        naming_info = QLabel(
            "Files will be renamed using the format: <b>PERSONA_RELEASE_REELID</b><br><br>"
            "Examples:<br>"
            "• <code>ZONEA0_RENEGADEPIPELINE_045.mp4</code><br>"
            "• <code>FITNESSGURU_THESCALE_001.jpg</code><br><br>"
            "Folders will be created using: <b>PERSONA_RELEASE</b><br>"
            "Example: <code>ZONEA0_RENEGADEPIPELINE/</code><br><br>"
            "<b>🛡️ Duplicate Protection:</b> Files with identical names are automatically skipped (no overwrites)<br>"
            "<b>📊 CSV Updates:</b> FilePath and Clip Filename columns are automatically updated after organization"
        )
        naming_info.setWordWrap(True)
        naming_info.setStyleSheet("background: #1a1a1a; padding: 10px; border: 1px solid #404040; border-radius: 4px; color: #cccccc;")
        naming_layout.addWidget(naming_info)
        
        naming_group.setLayout(naming_layout)
        layout.addWidget(naming_group)
        
        layout.addStretch()
        self.tab_widget.addTab(settings_widget, "Settings")
    
    def setup_preview_tab(self):
        """Setup the preview tab showing what will happen."""
        preview_widget = QWidget()
        layout = QVBoxLayout(preview_widget)
        
        # Preview info
        preview_info = QLabel("Preview shows how files will be organized without actually moving them.")
        preview_info.setStyleSheet("color: #888888; font-style: italic; margin: 5px;")
        layout.addWidget(preview_info)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels([
            "Reel ID", "Original File", "New Filename", "Target Folder", "Status", "Notes"
        ])
        
        # Configure table
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Reel ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Original File
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # New Filename
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Target Folder
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Notes
        
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSortingEnabled(True)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Select entire rows
        self.preview_table.setSelectionMode(QAbstractItemView.MultiSelection)  # Allow multiple row selection
        
        layout.addWidget(self.preview_table)
        
        # Preview actions
        preview_actions = QHBoxLayout()
        
        self.refresh_preview_btn = QPushButton("🔄 Refresh Preview")
        self.refresh_preview_btn.clicked.connect(self.update_preview)
        preview_actions.addWidget(self.refresh_preview_btn)
        
        self.delete_selected_btn = QPushButton("🗑️ Delete Selected")
        self.delete_selected_btn.clicked.connect(self.delete_selected_rows)
        self.delete_selected_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 5px;")
        self.delete_selected_btn.setToolTip("Delete selected rows from the organization list")
        preview_actions.addWidget(self.delete_selected_btn)
        
        preview_actions.addStretch()
        
        self.preview_count_label = QLabel("No files to preview")
        preview_actions.addWidget(self.preview_count_label)
        
        layout.addLayout(preview_actions)
        
        self.tab_widget.addTab(preview_widget, "Preview")
    
    def setup_organize_tab(self):
        """Setup the file organization execution tab."""
        organize_widget = QWidget()
        layout = QVBoxLayout(organize_widget)
        
        # Organization controls
        controls_group = QGroupBox("🚀 File Organization")
        controls_layout = QVBoxLayout()
        
        # Status info
        status_text = "Ready to organize files"
        if self.csv_update_callback:
            status_text += " (CSV updates enabled)"
        self.organize_status_label = QLabel(status_text)
        self.organize_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        controls_layout.addWidget(self.organize_status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        controls_layout.addWidget(self.progress_bar)
        
        # Progress details
        self.progress_details_label = QLabel("")
        self.progress_details_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        controls_layout.addWidget(self.progress_details_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.organize_btn = QPushButton("📁 Organize Files")
        self.organize_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        self.organize_btn.clicked.connect(self.start_organization)
        action_layout.addWidget(self.organize_btn)
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_organization)
        action_layout.addWidget(self.cancel_btn)
        
        action_layout.addStretch()
        
        controls_layout.addLayout(action_layout)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results display
        results_group = QGroupBox("📊 Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setStyleSheet("background: #f8f9fa; font-family: monospace; font-size: 11px;")
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(organize_widget, "Organize")
    
    def load_current_settings(self):
        """Load current settings from config."""
        if not self.config_manager:
            return
        
        settings = self.config_manager.get_file_organization_settings()
        
        # Load export folder
        export_folder = settings.get("master_export_folder", "")
        self.export_folder_edit.setText(export_folder)
        self.update_folder_info()
        
        # Load checkboxes
        self.safe_mode_checkbox.setChecked(settings.get("safe_testing_mode", True))
        self.overwrite_protection_checkbox.setChecked(settings.get("overwrite_protection", True))
        self.auto_organize_checkbox.setChecked(settings.get("auto_organize_enabled", True))
    
    def browse_export_folder(self):
        """Browse for export folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Master Export Folder", self.export_folder_edit.text()
        )
        if folder:
            self.export_folder_edit.setText(folder)
            self.update_folder_info()
    
    def update_folder_info(self):
        """Update the folder info display."""
        folder_path = self.export_folder_edit.text()
        
        if not folder_path:
            self.folder_info_label.setText("No folder selected")
            self.folder_info_label.setStyleSheet("color: #e74c3c;")
            return
        
        try:
            folder = Path(folder_path)
            if folder.exists():
                if folder.is_dir():
                    self.folder_info_label.setText(f"✅ Valid directory: {folder_path}")
                    self.folder_info_label.setStyleSheet("color: #27ae60;")
                else:
                    self.folder_info_label.setText("❌ Path is not a directory")
                    self.folder_info_label.setStyleSheet("color: #e74c3c;")
            else:
                self.folder_info_label.setText("⚠️ Directory will be created")
                self.folder_info_label.setStyleSheet("color: #f39c12;")
        except Exception as e:
            self.folder_info_label.setText(f"❌ Invalid path: {e}")
            self.folder_info_label.setStyleSheet("color: #e74c3c;")
    
    def update_preview(self):
        """Update the preview table with current data."""
        if not self.reel_data_list:
            self.preview_count_label.setText("No files to preview")
            self.preview_table.setRowCount(0)
            return
        
        # Save current settings temporarily
        self.save_current_settings()
        
        # Generate preview
        preview_data = self.file_organizer.preview_organization(self.reel_data_list)
        
        # Populate table
        self.preview_table.setRowCount(len(preview_data))
        
        for row, data in enumerate(preview_data):
            # Reel ID
            reel_id_item = QTableWidgetItem(data["reel_id"])
            self.preview_table.setItem(row, 0, reel_id_item)
            
            # Original file
            orig_file_item = QTableWidgetItem(data["original_filename"])
            self.preview_table.setItem(row, 1, orig_file_item)
            
            # New filename
            new_file_item = QTableWidgetItem(data["new_filename"])
            self.preview_table.setItem(row, 2, new_file_item)
            
            # Target folder
            target_folder_item = QTableWidgetItem(os.path.basename(data["target_folder"]))
            target_folder_item.setToolTip(data["target_folder"])
            self.preview_table.setItem(row, 3, target_folder_item)
            
            # Status
            status = data.get("status", "unknown")
            if status == "ready":
                status_item = QTableWidgetItem("✅ Ready")
                status_item.setBackground(Qt.green)
            elif status == "duplicate":
                status_item = QTableWidgetItem("⚠️ Duplicate")
                status_item.setBackground(QColor(72, 201, 176))  # Light teal
                status_item.setToolTip("Duplicate detected—this file will be skipped.")
            elif status == "invalid_source":
                status_item = QTableWidgetItem("❌ Error")
                status_item.setBackground(Qt.red)
            else:
                status_item = QTableWidgetItem("❓ Unknown")
                status_item.setBackground(Qt.gray)
            self.preview_table.setItem(row, 4, status_item)
            
            # Notes
            notes_item = QTableWidgetItem(data.get("status_message", "No information"))
            self.preview_table.setItem(row, 5, notes_item)
        
        # Update count
        ready_count = sum(1 for d in preview_data if d.get("status") == "ready")
        duplicate_count = sum(1 for d in preview_data if d.get("status") == "duplicate")
        error_count = sum(1 for d in preview_data if d.get("status") == "invalid_source")
        total_count = len(preview_data)
        
        count_text = f"{ready_count}/{total_count} files ready"
        if duplicate_count > 0:
            count_text += f", {duplicate_count} duplicates"
        if error_count > 0:
            count_text += f", {error_count} errors"
        
        self.preview_count_label.setText(count_text)
    
    def delete_selected_rows(self):
        """Delete selected rows from the preview table and reel data list."""
        if not self.reel_data_list:
            QMessageBox.information(self, "No Data", "No files are available to delete.")
            return
        
        # Get selected rows
        selected_rows = set()
        for item in self.preview_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select one or more rows to delete.")
            return
        
        # Confirm deletion
        row_count = len(selected_rows)
        message = f"Are you sure you want to delete {row_count} selected file(s) from the organization list?\n\n"
        message += "This will remove them from the current session only - original files will not be affected."
        
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Sort rows in descending order to avoid index shifting issues
        sorted_rows = sorted(selected_rows, reverse=True)
        
        # Remove corresponding entries from reel_data_list
        for row_index in sorted_rows:
            if 0 <= row_index < len(self.reel_data_list):
                removed_item = self.reel_data_list.pop(row_index)
                safe_print(f"[FILE_ORG] Removed reel from organization list: {removed_item[0]}")
        
        # Refresh the preview to show updated list
        self.update_preview()
        
        # Show result message
        remaining_count = len(self.reel_data_list)
        QMessageBox.information(
            self, "Files Removed",
            f"Successfully removed {row_count} file(s) from the organization list.\n"
            f"{remaining_count} file(s) remaining."
        )
    
    def save_current_settings(self):
        """Save current settings to config."""
        if not self.config_manager:
            return
        
        # Save export folder
        export_folder = self.export_folder_edit.text().strip()
        self.config_manager.set_master_export_folder(export_folder)
        
        # Save other settings
        self.config_manager.update_file_organization_setting("safe_testing_mode", self.safe_mode_checkbox.isChecked())
        self.config_manager.update_file_organization_setting("overwrite_protection", self.overwrite_protection_checkbox.isChecked())
        self.config_manager.update_file_organization_setting("auto_organize_enabled", self.auto_organize_checkbox.isChecked())
    
    def start_organization(self):
        """Start the file organization process."""
        if not self.reel_data_list:
            QMessageBox.warning(self, "No Files", "No files selected for organization.")
            return
        
        # Save current settings
        self.save_current_settings()
        
        # Validate export folder
        export_folder = self.export_folder_edit.text().strip()
        if not export_folder:
            QMessageBox.warning(self, "No Export Folder", "Please select a master export folder first.")
            self.tab_widget.setCurrentIndex(0)  # Switch to settings tab
            return
        
        # Confirm operation
        safe_mode = self.safe_mode_checkbox.isChecked()
        operation_type = "copy" if safe_mode else "move"
        
        # Get preview to count files that will actually be moved
        preview_data = self.file_organizer.preview_organization(self.reel_data_list)
        ready_count = sum(1 for d in preview_data if d.get("status") == "ready")
        duplicate_count = sum(1 for d in preview_data if d.get("status") == "duplicate")
        
        # Create confirmation message
        if duplicate_count > 0:
            message = f"This will {operation_type} {ready_count} files to the export folder (skipping {duplicate_count} duplicates).\n\n"
        else:
            message = f"This will {operation_type} {ready_count} files to the export folder.\n\n"
        
        message += f"Safe mode: {'Enabled' if safe_mode else 'Disabled'}\n"
        message += f"Export folder: {export_folder}\n\n"
        message += "Continue?"
        
        reply = QMessageBox.question(
            self, "Confirm Organization",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Setup UI for operation
        self.organize_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.reel_data_list))
        self.progress_bar.setValue(0)
        self.organize_status_label.setText("Organizing files...")
        self.organize_status_label.setStyleSheet("color: #3498db; font-weight: bold;")
        self.results_text.clear()
        
        # Start organization thread
        enable_csv_updates = self.csv_update_callback is not None
        self.organization_thread = FileOrganizationThread(self.file_organizer, self.reel_data_list, enable_csv_updates)
        self.organization_thread.progress_updated.connect(self.on_progress_updated)
        self.organization_thread.operation_completed.connect(self.on_organization_completed)
        
        # Connect CSV update signal if callback is available
        if self.csv_update_callback:
            self.organization_thread.csv_update_requested.connect(self.on_csv_update_requested)
        
        self.organization_thread.start()
    
    def cancel_organization(self):
        """Cancel the ongoing organization process."""
        if self.organization_thread and self.organization_thread.isRunning():
            self.organization_thread.terminate()
            self.organization_thread.wait()
        
        self.reset_organize_ui()
        self.organize_status_label.setText("Organization cancelled")
        self.organize_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def on_progress_updated(self, current, total, message):
        """Handle progress updates from the organization thread."""
        self.progress_bar.setValue(current)
        self.progress_details_label.setText(message)
    
    def on_csv_update_requested(self, reel_id, new_filepath, new_filename):
        """Handle CSV update requests from the organization thread."""
        if self.csv_update_callback:
            try:
                self.csv_update_callback(reel_id, new_filepath, new_filename)
                safe_print(f"[FILE_ORG] CSV updated for reel: {reel_id}")
            except Exception as e:
                safe_print(f"[FILE_ORG] Error updating CSV for reel {reel_id}: {e}")
    
    def on_organization_completed(self, results):
        """Handle completion of the organization process."""
        self.reset_organize_ui()
        
        # Update status
        if results["success"]:
            self.organize_status_label.setText("✅ Organization completed successfully!")
            self.organize_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.organize_status_label.setText("❌ Organization completed with errors")
            self.organize_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # Display results
        self.display_results(results)
    
    def reset_organize_ui(self):
        """Reset the organize UI to ready state."""
        self.organize_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_details_label.setText("")
    
    def display_results(self, results):
        """Display organization results in the results text area."""
        result_text = []
        
        # Summary
        result_text.append("=== FILE ORGANIZATION RESULTS ===\n")
        result_text.append(f"Total files processed: {results.get('total_files', 0)}")
        result_text.append(f"Successfully organized: {results.get('successful_count', 0)}")
        result_text.append(f"Skipped (duplicates): {results.get('skipped_count', 0)}")
        result_text.append(f"Failed: {results.get('failed_count', 0)}")
        
        if self.csv_update_callback and results.get('successful_count', 0) > 0:
            result_text.append(f"CSV automatically updated for {results.get('successful_count', 0)} file(s)")
        
        result_text.append("")
        
        # Successful files
        if results.get("successful_files"):
            result_text.append("✅ SUCCESSFULLY ORGANIZED:")
            for file_info in results["successful_files"]:
                result_text.append(f"  • {file_info['reel_id']}: {os.path.basename(file_info['new_path'])}")
        
        # Skipped files
        if results.get("skipped_files"):
            result_text.append("\n⚠️ SKIPPED (DUPLICATES):")
            for file_info in results["skipped_files"]:
                result_text.append(f"  • {file_info['reel_id']}: {file_info['reason']}")
        
        # Failed files
        if results.get("failed_files"):
            result_text.append("\n❌ FAILED FILES:")
            for file_info in results["failed_files"]:
                result_text.append(f"  • {file_info['reel_id']}: {file_info['error']}")
        
        self.results_text.setPlainText("\\n".join(result_text))
    
    def accept(self):
        """Save settings and close dialog."""
        self.save_current_settings()
        super().accept()