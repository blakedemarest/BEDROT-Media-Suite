# -*- coding: utf-8 -*-
"""
Custom Item Manager for Reel Tracker.

Provides dialogs for managing custom dropdown items:
- Add new items
- Remove existing items
- Reorder items
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt
from .utils import safe_print
from .ui_styles import apply_dialog_theme, style_button, style_header_label, get_dialog_button_box_style


class CustomItemManagerDialog(QDialog):
    """
    Dialog for managing custom items in dropdown lists.
    """
    
    def __init__(self, parent=None, item_type="", config_manager=None):
        super().__init__(parent)
        self.item_type = item_type
        self.config_manager = config_manager
        
        self.setWindowTitle(f"Manage {item_type.title()} Items")
        self.setModal(True)
        self.resize(400, 500)
        
        # Apply BEDROT theme
        apply_dialog_theme(self)
        
        # Get current items
        self.items = self.config_manager.get_dropdown_values(item_type) if config_manager else []
        
        self.setup_ui()
        self.populate_list()
        
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel(f"MANAGE {self.item_type.upper()} ITEMS")
        style_header_label(header_label)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Instructions
        instructions = QLabel(f"Add, remove, or reorder {self.item_type} items. Empty items will be preserved.")
        instructions.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # List widget
        self.item_list = QListWidget()
        self.item_list.setDragDropMode(QListWidget.InternalMove)
        layout.addWidget(self.item_list)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Item")
        self.add_button.clicked.connect(self.add_item)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.clicked.connect(self.edit_item)
        button_layout.addWidget(self.edit_button)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_item)
        button_layout.addWidget(self.remove_button)
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_item_up)
        button_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_item_down)
        button_layout.addWidget(self.move_down_button)
        
        layout.addLayout(button_layout)
        
        # Info label
        self.info_label = QLabel("Select an item to edit, remove, or move")
        self.info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # Dialog buttons
        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        dialog_buttons.accepted.connect(self.save_and_accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)
        
        # Connect selection change
        self.item_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()
    
    def populate_list(self):
        """Populate the list with current items."""
        self.item_list.clear()
        for item in self.items:
            list_item = QListWidgetItem(item if item else "(empty)")
            if not item:
                list_item.setForeground(Qt.gray)
            self.item_list.addItem(list_item)
    
    def update_button_states(self):
        """Update button states based on selection."""
        has_selection = bool(self.item_list.selectedItems())
        current_row = self.item_list.currentRow()
        
        self.edit_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection and current_row > 0)  # Can't remove first (empty) item
        self.move_up_button.setEnabled(has_selection and current_row > 1)  # Can't move first two items
        self.move_down_button.setEnabled(has_selection and current_row >= 0 and current_row < self.item_list.count() - 1)
    
    def add_item(self):
        """Add a new item to the list."""
        text, ok = QInputDialog.getText(
            self, f"Add {self.item_type.title()}", 
            f"Enter new {self.item_type} name:"
        )
        if ok and text.strip():
            # Check for duplicates
            if text.strip() in self.items:
                QMessageBox.warning(self, "Duplicate Item", f"'{text.strip()}' already exists in the list.")
                return
            
            # Add to list
            self.items.append(text.strip())
            self.populate_list()
            
            # Select the new item
            self.item_list.setCurrentRow(len(self.items) - 1)
            self.info_label.setText(f"Added '{text.strip()}'")
    
    def edit_item(self):
        """Edit the selected item."""
        current_row = self.item_list.currentRow()
        if current_row < 0:
            return
            
        current_text = self.items[current_row]
        text, ok = QInputDialog.getText(
            self, f"Edit {self.item_type.title()}", 
            f"Edit {self.item_type} name:",
            text=current_text
        )
        if ok:
            # Allow empty text for the first item
            if current_row == 0 or text.strip():
                # Check for duplicates (excluding current item)
                if text.strip() != current_text and text.strip() in self.items:
                    QMessageBox.warning(self, "Duplicate Item", f"'{text.strip()}' already exists in the list.")
                    return
                
                self.items[current_row] = text.strip() if current_row > 0 else text
                self.populate_list()
                self.item_list.setCurrentRow(current_row)
                self.info_label.setText(f"Updated item at position {current_row + 1}")
    
    def remove_item(self):
        """Remove the selected item."""
        current_row = self.item_list.currentRow()
        if current_row <= 0:  # Can't remove first (empty) item
            QMessageBox.information(self, "Cannot Remove", "The first (empty) item cannot be removed.")
            return
            
        item_text = self.items[current_row]
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove '{item_text}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.items.pop(current_row)
            self.populate_list()
            
            # Select previous item or first available
            new_row = min(current_row, len(self.items) - 1)
            if new_row >= 0:
                self.item_list.setCurrentRow(new_row)
                
            self.info_label.setText(f"Removed '{item_text}'")
    
    def move_item_up(self):
        """Move the selected item up in the list."""
        current_row = self.item_list.currentRow()
        if current_row <= 1:  # Can't move first two items
            return
            
        # Swap items
        self.items[current_row], self.items[current_row - 1] = self.items[current_row - 1], self.items[current_row]
        self.populate_list()
        self.item_list.setCurrentRow(current_row - 1)
        self.info_label.setText(f"Moved item up to position {current_row}")
    
    def move_item_down(self):
        """Move the selected item down in the list."""
        current_row = self.item_list.currentRow()
        if current_row < 0 or current_row >= len(self.items) - 1:
            return
            
        # Don't allow moving empty item down
        if current_row == 0:
            return
            
        # Swap items
        self.items[current_row], self.items[current_row + 1] = self.items[current_row + 1], self.items[current_row]
        self.populate_list()
        self.item_list.setCurrentRow(current_row + 1)
        self.info_label.setText(f"Moved item down to position {current_row + 2}")
    
    def save_and_accept(self):
        """Save changes and close dialog."""
        if self.config_manager:
            try:
                # Update configuration
                self.config_manager.config["dropdown_values"][self.item_type] = self.items
                self.config_manager.save_config()
                safe_print(f"[OK] Updated {self.item_type} items: {len(self.items)} total")
            except Exception as e:
                safe_print(f"Error saving {self.item_type} items: {e}")
                QMessageBox.critical(self, "Save Error", f"Failed to save changes: {str(e)}")
                return
        
        self.accept()
    
    def get_items(self):
        """Get the current list of items."""
        return self.items.copy()