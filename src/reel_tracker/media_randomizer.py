# -*- coding: utf-8 -*-
"""
Media Randomizer Module for Reel Tracker.

Provides functionality for:
- Background scanning of media files
- Video and image randomization
- User interface for media selection
"""

import os
import random
import math
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, 
    QGridLayout, QListWidget, QListWidgetItem, QCheckBox, QSlider, 
    QProgressBar, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from .utils import safe_print
from .ui_styles import apply_dialog_theme, style_button, style_header_label


class MediaRandomizerWorker(QThread):
    """
    Background worker for media file randomization and processing.
    """
    progress_updated = pyqtSignal(int)
    file_found = pyqtSignal(str, str, str)  # file_path, file_type, file_info
    finished_scanning = pyqtSignal(int)  # total_files_found
    
    def __init__(self, folder_paths, file_types, max_files=50):
        super().__init__()
        self.folder_paths = folder_paths
        self.file_types = file_types
        self.max_files = max_files
        self._is_running = True
        
    def run(self):
        """Scan folders for media files and emit findings."""
        all_files = []
        
        # Define supported formats
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        
        for folder_path in self.folder_paths:
            if not self._is_running:
                break
                
            try:
                for root, dirs, files in os.walk(folder_path):
                    if not self._is_running:
                        break
                        
                    for file in files:
                        if not self._is_running:
                            break
                            
                        file_path = os.path.join(root, file)
                        file_ext = Path(file).suffix.lower()
                        
                        # Determine file type
                        file_type = None
                        if 'video' in self.file_types and file_ext in video_extensions:
                            file_type = 'video'
                        elif 'image' in self.file_types and file_ext in image_extensions:
                            file_type = 'image'
                            
                        if file_type:
                            file_size = os.path.getsize(file_path)
                            file_info = f"{file_ext.upper()} • {self.format_file_size(file_size)}"
                            
                            all_files.append((file_path, file_type, file_info))
                            self.file_found.emit(file_path, file_type, file_info)
                            
                            if len(all_files) >= self.max_files:
                                break
                                
            except Exception as e:
                safe_print(f"Error scanning {folder_path}: {e}")
                
        # Randomize the results
        if all_files and self._is_running:
            random.shuffle(all_files)
            
        self.finished_scanning.emit(len(all_files))
        
    def format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s}{size_names[i]}"
        
    def stop(self):
        """Stop the scanning process."""
        self._is_running = False


class MediaRandomizerDialog(QDialog):
    """
    Dialog for randomizing and selecting video clips and images.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Media Randomizer - Video & Image Selection")
        self.setModal(True)
        self.resize(800, 600)
        
        # Apply BEDROT theme
        apply_dialog_theme(self)
        
        # Store randomized results
        self.randomized_files = []
        self.selected_file = None
        self.worker = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the randomizer dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("MEDIA RANDOMIZER")
        style_header_label(header_label)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()
        
        # Folder selection
        config_layout.addWidget(QLabel("Source Folders:"), 0, 0)
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(100)
        config_layout.addWidget(self.folder_list, 0, 1, 2, 1)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_source_folder)
        config_layout.addWidget(add_folder_btn, 0, 2)
        
        remove_folder_btn = QPushButton("Remove")
        remove_folder_btn.clicked.connect(self.remove_selected_folder)
        config_layout.addWidget(remove_folder_btn, 1, 2)
        
        # File type selection
        config_layout.addWidget(QLabel("File Types:"), 2, 0)
        file_type_layout = QHBoxLayout()
        self.video_checkbox = QCheckBox("Videos")
        self.video_checkbox.setChecked(True)
        self.image_checkbox = QCheckBox("Images") 
        self.image_checkbox.setChecked(True)
        file_type_layout.addWidget(self.video_checkbox)
        file_type_layout.addWidget(self.image_checkbox)
        file_type_layout.addStretch()
        config_layout.addLayout(file_type_layout, 2, 1)
        
        # Max files slider
        config_layout.addWidget(QLabel("Max Files:"), 3, 0)
        self.max_files_slider = QSlider(Qt.Horizontal)
        self.max_files_slider.setRange(10, 200)
        self.max_files_slider.setValue(50)
        self.max_files_slider.valueChanged.connect(self.update_max_files_label)
        config_layout.addWidget(self.max_files_slider, 3, 1)
        
        self.max_files_label = QLabel("50 files")
        config_layout.addWidget(self.max_files_label, 3, 2)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🔍 Scan & Randomize")
        self.scan_btn.clicked.connect(self.start_randomization)
        action_layout.addWidget(self.scan_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_randomization)
        self.stop_btn.setEnabled(False)
        action_layout.addWidget(self.stop_btn)
        
        self.shuffle_btn = QPushButton("🎲 Re-shuffle")
        self.shuffle_btn.clicked.connect(self.reshuffle_results)
        self.shuffle_btn.setEnabled(False)
        action_layout.addWidget(self.shuffle_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results section
        results_group = QGroupBox("Randomized Results")
        results_layout = QVBoxLayout()
        
        # Results info
        self.results_info_label = QLabel("Click 'Scan & Randomize' to find media files")
        self.results_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        results_layout.addWidget(self.results_info_label)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_file_selected)
        self.results_list.itemDoubleClicked.connect(self.accept_selected_file)
        results_layout.addWidget(self.results_list)
        
        # File preview/info
        self.file_info_label = QLabel("Select a file to see details")
        self.file_info_label.setStyleSheet("background: #ecf0f1; padding: 10px; border-radius: 5px;")
        self.file_info_label.setWordWrap(True)
        results_layout.addWidget(self.file_info_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.use_selected_btn = QPushButton("Use Selected File")
        self.use_selected_btn.clicked.connect(self.accept_selected_file)
        self.use_selected_btn.setEnabled(False)
        button_layout.addWidget(self.use_selected_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def add_source_folder(self):
        """Add a source folder for scanning."""
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder")
        if folder:
            # Check if folder already exists
            for i in range(self.folder_list.count()):
                if self.folder_list.item(i).text() == folder:
                    QMessageBox.information(self, "Folder Exists", "This folder is already in the list.")
                    return
                    
            self.folder_list.addItem(folder)
            
    def remove_selected_folder(self):
        """Remove selected folder from the list."""
        current_row = self.folder_list.currentRow()
        if current_row >= 0:
            self.folder_list.takeItem(current_row)
            
    def update_max_files_label(self, value):
        """Update the max files label."""
        self.max_files_label.setText(f"{value} files")
        
    def start_randomization(self):
        """Start the media randomization process."""
        # Validate inputs
        if self.folder_list.count() == 0:
            QMessageBox.warning(self, "No Folders", "Please add at least one source folder.")
            return
            
        if not self.video_checkbox.isChecked() and not self.image_checkbox.isChecked():
            QMessageBox.warning(self, "No File Types", "Please select at least one file type (Videos or Images).")
            return
            
        # Prepare scan parameters
        folder_paths = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
        file_types = []
        if self.video_checkbox.isChecked():
            file_types.append('video')
        if self.image_checkbox.isChecked():
            file_types.append('image')
            
        max_files = self.max_files_slider.value()
        
        # Clear previous results
        self.results_list.clear()
        self.randomized_files.clear()
        self.selected_file = None
        
        # Update UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.shuffle_btn.setEnabled(False)
        self.use_selected_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.results_info_label.setText("Scanning folders...")
        
        # Start worker thread
        self.worker = MediaRandomizerWorker(folder_paths, file_types, max_files)
        self.worker.file_found.connect(self.on_file_found)
        self.worker.finished_scanning.connect(self.on_scanning_finished)
        self.worker.start()
        
    def stop_randomization(self):
        """Stop the randomization process."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            
        self.reset_ui_after_scan()
        
    def on_file_found(self, file_path, file_type, file_info):
        """Handle when a file is found during scanning."""
        item = QListWidgetItem()
        
        # Create display text with icon
        icon = "🎥" if file_type == 'video' else "🖼️"
        filename = os.path.basename(file_path)
        display_text = f"{icon} {filename}"
        
        item.setText(display_text)
        item.setData(Qt.UserRole, {
            'path': file_path,
            'type': file_type,
            'info': file_info,
            'filename': filename
        })
        
        self.results_list.addItem(item)
        self.randomized_files.append(file_path)
        
    def on_scanning_finished(self, total_files):
        """Handle when scanning is finished."""
        self.reset_ui_after_scan()
        
        if total_files > 0:
            self.results_info_label.setText(f"Found {total_files} randomized media files. Double-click to select.")
            self.shuffle_btn.setEnabled(True)
        else:
            self.results_info_label.setText("No media files found in the selected folders.")
            
    def reset_ui_after_scan(self):
        """Reset UI state after scanning."""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
    def reshuffle_results(self):
        """Re-shuffle the current results."""
        if self.randomized_files:
            random.shuffle(self.randomized_files)
            
            # Re-populate the list in new order
            self.results_list.clear()
            for file_path in self.randomized_files:
                # Determine file type
                file_ext = Path(file_path).suffix.lower()
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                file_type = 'video' if file_ext in video_extensions else 'image'
                
                try:
                    file_size = os.path.getsize(file_path)
                    file_info = f"{file_ext.upper()} • {MediaRandomizerWorker([], []).format_file_size(file_size)}"
                except:
                    file_info = file_ext.upper()
                
                self.on_file_found(file_path, file_type, file_info)
                
            self.results_info_label.setText(f"Re-shuffled {len(self.randomized_files)} files.")
            
    def on_file_selected(self, item):
        """Handle when a file is selected from the list."""
        file_data = item.data(Qt.UserRole)
        if file_data:
            self.selected_file = file_data['path']
            
            # Update file info display
            info_text = f"""
<b>📁 File:</b> {file_data['filename']}<br>
<b>📍 Path:</b> {file_data['path']}<br>
<b>🏷️ Type:</b> {file_data['type'].title()}<br>
<b>ℹ️ Info:</b> {file_data['info']}
            """.strip()
            
            self.file_info_label.setText(info_text)
            self.use_selected_btn.setEnabled(True)
            
    def accept_selected_file(self):
        """Accept the selected file and close dialog."""
        if self.selected_file:
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a file first.")
            
    def get_selected_file(self):
        """Get the selected file path."""
        return self.selected_file