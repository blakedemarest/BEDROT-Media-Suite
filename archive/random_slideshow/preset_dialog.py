# -*- coding: utf-8 -*-
"""
Preset Management Dialog for Random Slideshow Generator.

Provides a comprehensive dialog for managing presets including:
- Viewing all presets with details
- Creating, editing, and deleting presets
- Importing and exporting presets
- Renaming and duplicating presets
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QTextEdit, QLineEdit, QMessageBox,
    QFileDialog, QGroupBox, QSplitter, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime


class PresetDialog(QDialog):
    """
    Dialog for managing slideshow presets.
    """
    
    preset_selected = pyqtSignal(str)  # Emitted when a preset is selected
    
    def __init__(self, preset_manager, current_preset=None, parent=None):
        super().__init__(parent)
        self.preset_manager = preset_manager
        self.current_preset = current_preset
        self.selected_preset = None
        
        self.setWindowTitle("Preset Manager")
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_presets()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>Manage Slideshow Presets</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Preset list
        left_widget = QGroupBox("Presets")
        left_layout = QVBoxLayout()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search presets...")
        self.search_input.textChanged.connect(self.filter_presets)
        left_layout.addWidget(self.search_input)
        
        # Preset list
        self.preset_list = QListWidget()
        self.preset_list.currentItemChanged.connect(self.on_preset_selected)
        left_layout.addWidget(self.preset_list)
        
        # List buttons
        list_buttons = QHBoxLayout()
        
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self.create_new_preset)
        list_buttons.addWidget(self.new_btn)
        
        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.clicked.connect(self.duplicate_preset)
        self.duplicate_btn.setEnabled(False)
        list_buttons.addWidget(self.duplicate_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_preset)
        self.delete_btn.setEnabled(False)
        list_buttons.addWidget(self.delete_btn)
        
        left_layout.addLayout(list_buttons)
        left_widget.setLayout(left_layout)
        
        # Right side - Preset details
        right_widget = QGroupBox("Preset Details")
        right_layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setEnabled(False)
        name_layout.addWidget(self.name_input)
        
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_preset)
        self.rename_btn.setEnabled(False)
        name_layout.addWidget(self.rename_btn)
        
        right_layout.addLayout(name_layout)
        
        # Description
        right_layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setEnabled(False)
        right_layout.addWidget(self.description_input)
        
        # Save description button
        self.save_desc_btn = QPushButton("Save Description")
        self.save_desc_btn.clicked.connect(self.save_description)
        self.save_desc_btn.setEnabled(False)
        right_layout.addWidget(self.save_desc_btn)
        
        # Preset info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        right_layout.addWidget(self.info_label)
        
        # Export/Import buttons
        io_buttons = QHBoxLayout()
        
        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.export_preset)
        self.export_btn.setEnabled(False)
        io_buttons.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import...")
        self.import_btn.clicked.connect(self.import_preset)
        io_buttons.addWidget(self.import_btn)
        
        right_layout.addLayout(io_buttons)
        
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Dialog buttons
        button_box = QDialogButtonBox()
        
        self.apply_btn = button_box.addButton("Apply Preset", QDialogButtonBox.AcceptRole)
        self.apply_btn.setEnabled(False)
        
        close_btn = button_box.addButton(QDialogButtonBox.Close)
        
        button_box.accepted.connect(self.apply_preset)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_presets(self):
        """Load all presets into the list."""
        self.preset_list.clear()
        presets = self.preset_manager.get_all_presets()
        
        for name, preset in sorted(presets.items()):
            item = QListWidgetItem(name)
            
            # Add icon or special formatting for default presets
            if preset.get("is_default", False):
                item.setText(f"📌 {name}")
            
            # Highlight current preset
            if name == self.current_preset:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setText(f"{item.text()} (Current)")
            
            self.preset_list.addItem(item)
    
    def filter_presets(self, text):
        """Filter presets based on search text."""
        for i in range(self.preset_list.count()):
            item = self.preset_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def on_preset_selected(self, current, previous):
        """Handle preset selection."""
        if not current:
            self.selected_preset = None
            self.update_details(None)
            return
        
        # Extract preset name (remove decorations)
        preset_name = current.text()
        preset_name = preset_name.replace("📌 ", "").replace(" (Current)", "")
        
        self.selected_preset = preset_name
        preset = self.preset_manager.get_preset(preset_name)
        self.update_details(preset)
    
    def update_details(self, preset):
        """Update the details panel with preset information."""
        if not preset:
            self.name_input.clear()
            self.description_input.clear()
            self.info_label.clear()
            self.name_input.setEnabled(False)
            self.description_input.setEnabled(False)
            self.save_desc_btn.setEnabled(False)
            self.rename_btn.setEnabled(False)
            self.duplicate_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.apply_btn.setEnabled(False)
            return
        
        # Enable controls
        is_default = preset.get("is_default", False)
        self.name_input.setEnabled(not is_default)
        self.description_input.setEnabled(True)
        self.save_desc_btn.setEnabled(True)
        self.rename_btn.setEnabled(not is_default)
        self.duplicate_btn.setEnabled(True)
        self.delete_btn.setEnabled(not is_default)
        self.export_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)
        
        # Update fields
        self.name_input.setText(preset.get("name", ""))
        self.description_input.setPlainText(preset.get("description", ""))
        
        # Build info text
        info_parts = []
        
        if preset.get("image_folder"):
            info_parts.append(f"<b>Image Folder:</b> {preset['image_folder']}")
        
        if preset.get("output_folder"):
            info_parts.append(f"<b>Output Folder:</b> {preset['output_folder']}")
        
        if preset.get("aspect_ratio"):
            info_parts.append(f"<b>Aspect Ratio:</b> {preset['aspect_ratio']}")
        
        if preset.get("batch_settings"):
            batch = preset["batch_settings"]
            info_parts.append(f"<b>Max Workers:</b> {batch.get('max_workers', 'N/A')}")
            if batch.get("auto_start"):
                info_parts.append("<b>Auto Start:</b> Enabled")
        
        if preset.get("created_at"):
            created = datetime.fromisoformat(preset["created_at"]).strftime("%Y-%m-%d %H:%M")
            info_parts.append(f"<b>Created:</b> {created}")
        
        if preset.get("modified_at"):
            modified = datetime.fromisoformat(preset["modified_at"]).strftime("%Y-%m-%d %H:%M")
            info_parts.append(f"<b>Modified:</b> {modified}")
        
        if is_default:
            info_parts.append("<b>Type:</b> Default Preset (Read-only)")
        
        self.info_label.setText("<br>".join(info_parts))
    
    def create_new_preset(self):
        """Create a new preset from current settings."""
        name, ok = self.get_preset_name("New Preset")
        if ok and name:
            # Create empty preset
            config = {
                "image_folder": "",
                "output_folder": "",
                "aspect_ratio": "16:9",
                "batch_settings": {
                    "max_workers": 2,
                    "auto_start": False
                }
            }
            
            if self.preset_manager.save_preset(name, config, "New preset"):
                self.load_presets()
                # Select the new preset
                for i in range(self.preset_list.count()):
                    if name in self.preset_list.item(i).text():
                        self.preset_list.setCurrentRow(i)
                        break
    
    def duplicate_preset(self):
        """Duplicate the selected preset."""
        if not self.selected_preset:
            return
        
        name, ok = self.get_preset_name(f"{self.selected_preset} (Copy)")
        if ok and name:
            if self.preset_manager.duplicate_preset(self.selected_preset, name):
                self.load_presets()
                # Select the new preset
                for i in range(self.preset_list.count()):
                    if name in self.preset_list.item(i).text():
                        self.preset_list.setCurrentRow(i)
                        break
    
    def delete_preset(self):
        """Delete the selected preset."""
        if not self.selected_preset:
            return
        
        reply = QMessageBox.question(
            self, "Delete Preset",
            f"Are you sure you want to delete the preset '{self.selected_preset}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.preset_manager.delete_preset(self.selected_preset):
                self.load_presets()
            else:
                QMessageBox.warning(self, "Error", "Could not delete preset. Default presets cannot be deleted.")
    
    def rename_preset(self):
        """Rename the selected preset."""
        if not self.selected_preset:
            return
        
        new_name = self.name_input.text().strip()
        if new_name and new_name != self.selected_preset:
            if self.preset_manager.rename_preset(self.selected_preset, new_name):
                self.load_presets()
                # Select the renamed preset
                for i in range(self.preset_list.count()):
                    if new_name in self.preset_list.item(i).text():
                        self.preset_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.warning(self, "Error", "Could not rename preset. Name may already exist.")
    
    def save_description(self):
        """Save the updated description."""
        if not self.selected_preset:
            return
        
        preset = self.preset_manager.get_preset(self.selected_preset)
        if preset:
            preset["description"] = self.description_input.toPlainText()
            preset["modified_at"] = datetime.now().isoformat()
            self.preset_manager.save_preset(self.selected_preset, preset, preset["description"])
            QMessageBox.information(self, "Success", "Description saved.")
    
    def export_preset(self):
        """Export the selected preset."""
        if not self.selected_preset:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Preset",
            f"{self.selected_preset}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.preset_manager.export_preset(self.selected_preset, file_path):
                QMessageBox.information(self, "Success", f"Preset exported to {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Could not export preset.")
    
    def import_preset(self):
        """Import a preset from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Preset",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            imported_name = self.preset_manager.import_preset(file_path)
            if imported_name:
                self.load_presets()
                QMessageBox.information(self, "Success", f"Preset '{imported_name}' imported successfully.")
                # Select the imported preset
                for i in range(self.preset_list.count()):
                    if imported_name in self.preset_list.item(i).text():
                        self.preset_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.warning(self, "Error", "Could not import preset. File may be invalid.")
    
    def apply_preset(self):
        """Apply the selected preset."""
        if self.selected_preset:
            self.preset_selected.emit(self.selected_preset)
            self.accept()
    
    def get_preset_name(self, default=""):
        """Get a preset name from the user."""
        from PyQt5.QtWidgets import QInputDialog
        
        while True:
            name, ok = QInputDialog.getText(
                self, "Preset Name",
                "Enter preset name:",
                text=default
            )
            
            if not ok:
                return "", False
            
            name = name.strip()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Preset name cannot be empty.")
                continue
            
            # Check if name already exists
            if name in self.preset_manager.get_preset_names():
                reply = QMessageBox.question(
                    self, "Name Exists",
                    f"A preset named '{name}' already exists. Overwrite it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    continue
            
            return name, True