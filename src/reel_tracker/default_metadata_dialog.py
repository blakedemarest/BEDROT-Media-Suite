# -*- coding: utf-8 -*-
"""
Default Metadata Dialog Module for Reel Tracker.

Provides functionality for:
- Setting and managing default metadata values
- Auto-population of reel fields on drag-and-drop
- Persistence of defaults to config file with version tracking
"""

import os
import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QTextEdit, 
    QDialogButtonBox, QMessageBox, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtCore import Qt
from .config_manager import ConfigManager
from .utils import safe_print
from .ui_styles import apply_dialog_theme, style_button, get_dialog_button_box_style


class DefaultMetadataDialog(QDialog):
    """
    Dialog for managing default metadata values that will be auto-populated
    when dragging and dropping media files.
    """
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Default Metadata Settings")
        self.setModal(True)
        self.resize(600, 500)
        
        # Apply BEDROT theme
        apply_dialog_theme(self)
        
        # Use config manager or create one
        self.config_manager = config_manager or ConfigManager()
        
        # Get dropdown options from config
        if self.config_manager:
            self.persona_options = self.config_manager.get_dropdown_values("persona")
            self.reel_type_options = self.config_manager.get_dropdown_values("reel_type")
            self.release_options = self.config_manager.get_dropdown_values("release")
        else:
            # Fallback options if config manager failed
            self.persona_options = ["", "Fitness Influencer", "Tech Reviewer", "Lifestyle Blogger"]
            self.reel_type_options = ["", "Tutorial", "Product Review", "Behind the Scenes"]
            self.release_options = ["", "RENEGADE PIPELINE", "THE STATE OF THE WORLD", "THE SCALE"]
        
        self.setup_ui()
        self.load_current_defaults()
    
    def setup_ui(self):
        """Setup the dialog UI with default metadata inputs."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("🏷️ Default Metadata Settings")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Info label
        info_label = QLabel("These values will be automatically applied when dragging and dropping media files.")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Dropdown Management Section
        manage_group = QGroupBox("Manage Dropdown Values")
        manage_layout = QVBoxLayout()
        
        # Manage buttons
        manage_buttons_layout = QHBoxLayout()
        
        self.manage_personas_btn = QPushButton("Manage Personas")
        self.manage_personas_btn.clicked.connect(lambda: self.manage_dropdown_values("persona"))
        manage_buttons_layout.addWidget(self.manage_personas_btn)
        
        self.manage_releases_btn = QPushButton("Manage Releases")
        self.manage_releases_btn.clicked.connect(lambda: self.manage_dropdown_values("release"))
        manage_buttons_layout.addWidget(self.manage_releases_btn)
        
        self.manage_reel_types_btn = QPushButton("Manage Reel Types")
        self.manage_reel_types_btn.clicked.connect(lambda: self.manage_dropdown_values("reel_type"))
        manage_buttons_layout.addWidget(self.manage_reel_types_btn)
        
        manage_layout.addLayout(manage_buttons_layout)
        manage_group.setLayout(manage_layout)
        layout.addWidget(manage_group)
        
        # Default Values Section
        defaults_group = QGroupBox("Default Values")
        defaults_layout = QFormLayout()
        
        # Default Persona
        self.persona_combo = QComboBox()
        self.persona_combo.setEditable(True)
        self.persona_combo.addItems(self.persona_options)
        defaults_layout.addRow("Default Persona:", self.persona_combo)
        
        # Default Release
        self.release_combo = QComboBox()
        self.release_combo.setEditable(True)
        self.release_combo.addItems(self.release_options)
        defaults_layout.addRow("Default Release:", self.release_combo)
        
        # Default Reel Type
        self.reel_type_combo = QComboBox()
        self.reel_type_combo.setEditable(True)
        self.reel_type_combo.addItems(self.reel_type_options)
        defaults_layout.addRow("Default Reel Type:", self.reel_type_combo)
        
        # Default Caption Template
        self.caption_template_edit = QTextEdit()
        self.caption_template_edit.setPlaceholderText("Enter default caption template...\n\nUse {filename} to insert the filename automatically.")
        self.caption_template_edit.setMaximumHeight(100)
        defaults_layout.addRow("Default Caption Template:", self.caption_template_edit)
        
        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)
        
        # Reset to System Defaults Section
        reset_group = QGroupBox("Reset Options")
        reset_layout = QVBoxLayout()
        
        reset_button = QPushButton("Reset to System Defaults")
        reset_button.clicked.connect(self.reset_to_system_defaults)
        reset_button.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        reset_layout.addWidget(reset_button)
        
        reset_group.setLayout(reset_layout)
        layout.addWidget(reset_group)
        
        # Version History Section
        history_group = QGroupBox("Recent Changes")
        history_layout = QVBoxLayout()
        
        self.view_history_btn = QPushButton("View Change History")
        self.view_history_btn.clicked.connect(self.view_change_history)
        history_layout.addWidget(self.view_history_btn)
        
        self.export_audit_btn = QPushButton("Export Audit Log")
        self.export_audit_btn.clicked.connect(self.export_audit_log)
        history_layout.addWidget(self.export_audit_btn)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Current Config Info
        self.config_info_label = QLabel()
        self.update_config_info()
        layout.addWidget(self.config_info_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_current_defaults(self):
        """Load current default values from config."""
        if not self.config_manager:
            return
            
        defaults = self.config_manager.get_default_metadata()
        
        # Set combo box values
        self.set_combo_value(self.persona_combo, defaults.get("persona", ""))
        self.set_combo_value(self.release_combo, defaults.get("release", "RENEGADE PIPELINE"))
        self.set_combo_value(self.reel_type_combo, defaults.get("reel_type", ""))
        
        # Set caption template
        self.caption_template_edit.setPlainText(defaults.get("caption_template", ""))
    
    def set_combo_value(self, combo_box, value):
        """Set combo box value, add to list if not present."""
        index = combo_box.findText(value)
        if index >= 0:
            combo_box.setCurrentIndex(index)
        else:
            if value:  # Only add non-empty values
                combo_box.addItem(value)
                combo_box.setCurrentText(value)
    
    def reset_to_system_defaults(self):
        """Reset all default values to system defaults."""
        # Set system defaults without confirmation
        self.persona_combo.setCurrentText("")
        self.release_combo.setCurrentText("RENEGADE PIPELINE")
        self.reel_type_combo.setCurrentText("")
        self.caption_template_edit.setPlainText("")
        
        safe_print("[CONFIG] Default metadata reset to system defaults")
    
    def update_config_info(self):
        """Update the configuration info display."""
        if not self.config_manager:
            self.config_info_label.setText("Configuration manager not available.")
            return
            
        config_path = os.path.abspath(self.config_manager.config_file)
        last_modified = ""
        
        try:
            if os.path.exists(config_path):
                mtime = os.path.getmtime(config_path)
                last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            last_modified = "Unknown"
        
        info_text = f"Config file: {os.path.basename(config_path)}\nLast modified: {last_modified}"
        self.config_info_label.setText(info_text)
        self.config_info_label.setStyleSheet("color: #7f8c8d; font-size: 10px; margin: 5px;")
    
    def accept(self):
        """Save the default metadata and close dialog."""
        try:
            # Get values from form
            defaults = {
                "persona": self.persona_combo.currentText().strip(),
                "release": self.release_combo.currentText().strip(),
                "reel_type": self.reel_type_combo.currentText().strip(),
                "caption_template": self.caption_template_edit.toPlainText().strip()
            }
            
            # Save new dropdown values to config if they don't exist
            if self.config_manager:
                # Add new values to dropdown lists if they don't exist
                if defaults["persona"]:
                    self.config_manager.add_dropdown_value("persona", defaults["persona"])
                if defaults["release"]:
                    self.config_manager.add_dropdown_value("release", defaults["release"])
                if defaults["reel_type"]:
                    self.config_manager.add_dropdown_value("reel_type", defaults["reel_type"])
                
                # Save default metadata with version tracking
                success = self.config_manager.set_default_metadata(defaults)
                if success:
                    safe_print(f"[CONFIG] Default metadata updated: {defaults}")
                    # No success popup - just silent success
                else:
                    safe_print(f"[CONFIG] Failed to save default metadata: {defaults}")
                    # No warning popup - just log the failure
            
        except Exception as e:
            safe_print(f"Error saving default metadata: {e}")
            # No error popup - just log the error
            return
        
        # Call parent accept
        super().accept()
    
    def manage_dropdown_values(self, dropdown_type):
        """Open a dialog to manage dropdown values for a specific type."""
        if not self.config_manager:
            safe_print("[CONFIG] Configuration manager not available for dropdown management")
            return
        
        # Create management dialog
        dialog = DropdownManagementDialog(self, dropdown_type, self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            # Refresh the current combo boxes with updated values
            self.refresh_combo_boxes()
            safe_print(f"[CONFIG] {dropdown_type.title()} values updated")
    
    def refresh_combo_boxes(self):
        """Refresh all combo box contents from config."""
        if not self.config_manager:
            return
        
        # Store current values
        current_persona = self.persona_combo.currentText()
        current_release = self.release_combo.currentText()
        current_reel_type = self.reel_type_combo.currentText()
        
        # Update options from config
        self.persona_options = self.config_manager.get_dropdown_values("persona")
        self.release_options = self.config_manager.get_dropdown_values("release")
        self.reel_type_options = self.config_manager.get_dropdown_values("reel_type")
        
        # Refresh combo boxes
        self.persona_combo.clear()
        self.persona_combo.addItems(self.persona_options)
        self.persona_combo.setCurrentText(current_persona)
        
        self.release_combo.clear()
        self.release_combo.addItems(self.release_options)
        self.release_combo.setCurrentText(current_release)
        
        self.reel_type_combo.clear()
        self.reel_type_combo.addItems(self.reel_type_options)
        self.reel_type_combo.setCurrentText(current_reel_type)
    
    def view_change_history(self):
        """Show a dialog with recent change history."""
        if not self.config_manager:
            safe_print("[CONFIG] Configuration manager not available for history view")
            return
        
        # Get recent changes
        history = self.config_manager.get_version_history(limit=20)
        dropdown_history = self.config_manager.get_dropdown_change_history(limit=20)
        
        # Create history dialog
        dialog = ChangeHistoryDialog(self, history, dropdown_history)
        dialog.exec_()
    
    def export_audit_log(self):
        """Export comprehensive audit log."""
        if not self.config_manager:
            safe_print("[CONFIG] Configuration manager not available for audit export")
            return
        
        try:
            output_file = self.config_manager.export_dropdown_audit()
            if output_file:
                safe_print(f"[CONFIG] Audit log exported to: {output_file}")
                # Show simple success message in console only
            else:
                safe_print(f"[CONFIG] Failed to export audit log")
        except Exception as e:
            safe_print(f"[CONFIG] Error exporting audit log: {e}")


class DropdownManagementDialog(QDialog):
    """Dialog for managing individual dropdown value lists."""
    
    def __init__(self, parent, dropdown_type, config_manager):
        super().__init__(parent)
        self.dropdown_type = dropdown_type
        self.config_manager = config_manager
        
        self.setWindowTitle(f"Manage {dropdown_type.replace('_', ' ').title()} Values")
        self.setModal(True)
        self.resize(400, 500)
        
        self.setup_ui()
        self.load_values()
    
    def setup_ui(self):
        """Setup the management dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel(f"📝 Manage {self.dropdown_type.replace('_', ' ').title()} Values")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Instructions
        info_label = QLabel("Add, edit, or remove values. Changes are saved automatically.")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Values list with multi-selection enabled
        self.values_list = QListWidget()
        self.values_list.setSelectionMode(QListWidget.ExtendedSelection)  # Enable multi-selection
        layout.addWidget(self.values_list)
        
        # Error message label (initially hidden)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 11px; margin: 2px; padding: 2px;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Management buttons
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self.add_value)
        buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_value)
        buttons_layout.addWidget(self.edit_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_values)
        buttons_layout.addWidget(self.remove_btn)
        
        layout.addLayout(buttons_layout)
        
        # Special actions for releases
        if self.dropdown_type == "release":
            special_layout = QHBoxLayout()
            
            self.add_project_btn = QPushButton("Quick Add Project")
            self.add_project_btn.clicked.connect(self.quick_add_project)
            self.add_project_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
            special_layout.addWidget(self.add_project_btn)
            
            layout.addLayout(special_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect list selection
        self.values_list.itemSelectionChanged.connect(self.update_button_states)
        self.values_list.itemSelectionChanged.connect(self.hide_error)  # Hide errors when selection changes
        self.update_button_states()
    
    def load_values(self):
        """Load current values from config."""
        values = self.config_manager.get_dropdown_values(self.dropdown_type)
        self.values_list.clear()
        
        for value in values:
            if value:  # Skip empty values
                item = QListWidgetItem(value)
                self.values_list.addItem(item)
    
    def update_button_states(self):
        """Update button enabled states based on selection."""
        selected_items = self.values_list.selectedItems()
        has_selection = bool(selected_items)
        single_selection = len(selected_items) == 1
        
        # Edit only enabled for single selection
        self.edit_btn.setEnabled(single_selection)
        # Remove enabled for any selection
        self.remove_btn.setEnabled(has_selection)
        
        # Update button text to show count
        if has_selection:
            count = len(selected_items)
            if count == 1:
                self.remove_btn.setText("Remove Selected")
            else:
                self.remove_btn.setText(f"Remove Selected ({count})")
        else:
            self.remove_btn.setText("Remove Selected")
    
    def show_error(self, message):
        """Show error message below the list."""
        self.error_label.setText(f"⚠ {message}")
        self.error_label.show()
    
    def hide_error(self):
        """Hide error message."""
        self.error_label.hide()
    
    def add_value(self):
        """Add a new value to the list."""
        self.hide_error()  # Clear any previous errors
        
        text, ok = QInputDialog.getText(
            self, f"Add {self.dropdown_type.replace('_', ' ').title()}",
            f"Enter new {self.dropdown_type.replace('_', ' ')}:"
        )
        
        if ok and text.strip():
            value = text.strip()
            
            # Check if value already exists
            existing_values = [self.values_list.item(i).text() for i in range(self.values_list.count())]
            if value in existing_values:
                self.show_error(f"'{value}' already exists")
                return
            
            # Add to list and config
            success = self.config_manager.add_dropdown_value(self.dropdown_type, value)
            if success:
                item = QListWidgetItem(value)
                self.values_list.addItem(item)
                self.values_list.setCurrentItem(item)
                safe_print(f"[CONFIG] Added {self.dropdown_type}: {value}")
            else:
                self.show_error(f"Failed to add '{value}'")
    
    def edit_value(self):
        """Edit the selected value."""
        self.hide_error()  # Clear any previous errors
        
        current_item = self.values_list.currentItem()
        if not current_item:
            return
        
        old_value = current_item.text()
        text, ok = QInputDialog.getText(
            self, f"Edit {self.dropdown_type.replace('_', ' ').title()}",
            f"Edit {self.dropdown_type.replace('_', ' ')}:",
            text=old_value
        )
        
        if ok and text.strip() and text.strip() != old_value:
            new_value = text.strip()
            
            # Check if new value already exists
            existing_values = [self.values_list.item(i).text() for i in range(self.values_list.count())]
            if new_value in existing_values:
                self.show_error(f"'{new_value}' already exists")
                return
            
            # Update in config
            removed = self.config_manager.remove_dropdown_value(self.dropdown_type, old_value)
            added = self.config_manager.add_dropdown_value(self.dropdown_type, new_value)
            
            if removed and added:
                # Update in list
                current_item.setText(new_value)
                safe_print(f"[CONFIG] Updated {self.dropdown_type}: {old_value} → {new_value}")
            else:
                self.show_error(f"Failed to update '{old_value}'")
    
    def remove_selected_values(self):
        """Remove all selected values without confirmation."""
        self.hide_error()  # Clear any previous errors
        
        selected_items = self.values_list.selectedItems()
        if not selected_items:
            return
        
        # Track failures for error reporting
        failed_removals = []
        successful_removals = []
        
        # Remove items in reverse order to maintain indices
        for item in reversed(selected_items):
            value = item.text()
            
            # Remove from config
            success = self.config_manager.remove_dropdown_value(self.dropdown_type, value)
            
            if success:
                # Remove from list
                row = self.values_list.row(item)
                self.values_list.takeItem(row)
                successful_removals.append(value)
                safe_print(f"[CONFIG] Removed {self.dropdown_type}: {value}")
            else:
                failed_removals.append(value)
        
        # Show subtle error message if any failed
        if failed_removals:
            if len(failed_removals) == 1:
                self.show_error(f"Failed to remove '{failed_removals[0]}'")
            else:
                self.show_error(f"Failed to remove {len(failed_removals)} items")
        
        # Update button states after removal
        self.update_button_states()
    
    def quick_add_project(self):
        """Quick add for music projects with common naming patterns."""
        self.hide_error()  # Clear any previous errors
        
        text, ok = QInputDialog.getText(
            self, "Quick Add Project",
            "Enter project name (will be converted to UPPERCASE):"
        )
        
        if ok and text.strip():
            value = text.strip().upper()
            
            # Check if value already exists
            existing_values = [self.values_list.item(i).text() for i in range(self.values_list.count())]
            if value in existing_values:
                self.show_error(f"'{value}' already exists")
                return
            
            # Add to list and config
            success = self.config_manager.add_dropdown_value(self.dropdown_type, value)
            if success:
                item = QListWidgetItem(value)
                self.values_list.addItem(item)
                self.values_list.setCurrentItem(item)
                safe_print(f"[CONFIG] Quick-added release: {value}")
            else:
                self.show_error(f"Failed to add project '{value}'")


class ChangeHistoryDialog(QDialog):
    """Dialog for viewing change history and audit information."""
    
    def __init__(self, parent, general_history, dropdown_history):
        super().__init__(parent)
        self.general_history = general_history
        self.dropdown_history = dropdown_history
        
        self.setWindowTitle("Change History & Audit Log")
        self.setModal(True)
        self.resize(700, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the history dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("📈 Configuration Change History")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # History display
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("background: #f8f9fa; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.history_text)
        
        # Load history content
        self.load_history_content()
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_history_content(self):
        """Load and format history content."""
        content = []
        
        # Add dropdown changes section
        if self.dropdown_history:
            content.append("📝 DROPDOWN VALUE CHANGES\n" + "="*50)
            for entry in reversed(self.dropdown_history):  # Most recent first
                timestamp = entry.get("timestamp", "Unknown")
                action = entry.get("action", "").replace("dropdown_", "").title()
                dropdown_type = entry.get("dropdown_type", "Unknown").replace("_", " ").title()
                changed_value = entry.get("changed_value", "")
                
                content.append(f"[{timestamp}] {action} {dropdown_type}: '{changed_value}'")
            content.append("")
        
        # Add general changes section
        if self.general_history:
            content.append("⚙️ METADATA & CONFIGURATION CHANGES\n" + "="*50)
            for entry in reversed(self.general_history):  # Most recent first
                timestamp = entry.get("timestamp", "Unknown")
                action = entry.get("action", "").replace("_", " ").title()
                
                if action.startswith("Default Metadata"):
                    # Show metadata changes
                    new_data = entry.get("new", {})
                    previous_data = entry.get("previous", {})
                    
                    content.append(f"[{timestamp}] {action}:")
                    for key, value in new_data.items():
                        old_value = previous_data.get(key, "")
                        if old_value != value:
                            content.append(f"  • {key.title()}: '{old_value}' → '{value}'")
                else:
                    content.append(f"[{timestamp}] {action}")
            content.append("")
        
        # Summary statistics
        content.append("📈 SUMMARY STATISTICS\n" + "="*50)
        content.append(f"Total dropdown changes: {len(self.dropdown_history)}")
        content.append(f"Total metadata changes: {len([e for e in self.general_history if 'metadata' in e.get('action', '')])}")
        content.append(f"Total configuration entries: {len(self.general_history)}")
        
        if not content:
            content = ["No change history available."]
        
        self.history_text.setPlainText("\n".join(content))
    
    def statusBar(self):
        """Dummy statusBar method for compatibility."""
        class DummyStatusBar:
            def showMessage(self, msg):
                pass
        return DummyStatusBar()
    
    def get_defaults(self):
        """Get the current default values from the form."""
        return {
            "persona": self.persona_combo.currentText().strip(),
            "release": self.release_combo.currentText().strip(),
            "reel_type": self.reel_type_combo.currentText().strip(),
            "caption_template": self.caption_template_edit.toPlainText().strip()
        }