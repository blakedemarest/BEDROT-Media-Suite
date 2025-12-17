# -*- coding: utf-8 -*-
"""BulkEditDialog - apply the same changes to multiple selected rows.

The dialog shows only the fields that make sense to batch-edit.
If the user leaves a field blank it is ignored; otherwise the value
will be applied to every selected row.
"""

from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt
from .ui_styles import apply_dialog_theme, get_dialog_button_box_style


class BulkEditDialog(QDialog):
    """Dialog for batch-editing common reel fields."""

    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Edit Reels")
        self.setModal(True)
        self.config_manager = config_manager
        
        # Apply BEDROT theme
        apply_dialog_theme(self)

        layout = QFormLayout(self)
        self.setLayout(layout)

        # Helper to fetch values from config (fallback empty)
        def _opts(key):
            if self.config_manager:
                return self.config_manager.get_dropdown_values(key)
            return [""]

        # Widgets – we store them as attrs for later retrieval
        self.persona_combo = QComboBox()
        self.persona_combo.addItems(_opts("persona"))
        self.persona_combo.setEditable(True)
        layout.addRow("Persona:", self.persona_combo)

        self.release_combo = QComboBox()
        self.release_combo.addItems(_opts("release"))
        self.release_combo.setEditable(True)
        layout.addRow("Release:", self.release_combo)

        self.reel_type_combo = QComboBox()
        self.reel_type_combo.addItems(_opts("reel_type"))
        self.reel_type_combo.setEditable(True)
        layout.addRow("Reel Type:", self.reel_type_combo)

        # Visual Template removed from schema

        self.caption_edit = QLineEdit()
        layout.addRow("Caption:", self.caption_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get_updates(self):
        """Return a dict {column_name: value} for non-empty fields."""
        updates = {}
        if self.persona_combo.currentText().strip():
            updates["Persona"] = self.persona_combo.currentText().strip()
        if self.release_combo.currentText().strip():
            updates["Release"] = self.release_combo.currentText().strip()
        if self.reel_type_combo.currentText().strip():
            updates["Reel Type"] = self.reel_type_combo.currentText().strip()
        # Visual Template removed from schema
        if self.caption_edit.text().strip():
            updates["Caption"] = self.caption_edit.text().strip()
        return updates
