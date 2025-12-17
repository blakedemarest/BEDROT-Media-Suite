# -*- coding: utf-8 -*-
"""
Phrase List Widget for Caption Generator.

Center panel displaying SRT phrases with inline editing and selection.
Synchronizes with timeline selection and emits signals for preview updates.
"""

from typing import Optional, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QFrame, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from .srt_data_model import SRTDataModel, WordBlock, ms_to_srt_timestamp


class PhraseItemWidget(QFrame):
    """Custom widget for displaying a single phrase in the list."""

    edit_requested = pyqtSignal(int)  # index
    timing_clicked = pyqtSignal(int)  # index

    def __init__(self, block: WordBlock, index: int, parent=None):
        super().__init__(parent)
        self.block = block
        self.index = index
        self._setup_ui()

    def _setup_ui(self):
        """Set up the item widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Index number
        index_label = QLabel(f"{self.index + 1:03d}")
        index_label.setFixedWidth(35)
        index_label.setStyleSheet("color: #888888; font-family: Consolas;")
        layout.addWidget(index_label)

        # Color indicator bar
        color_bar = QFrame()
        color_bar.setFixedWidth(4)
        color_bar.setStyleSheet(f"background-color: {self.block.color}; border-radius: 2px;")
        layout.addWidget(color_bar)

        # Main content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # Text display
        self.text_label = QLabel(self.block.text.replace('\n', ' '))
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        content_layout.addWidget(self.text_label)

        # Timing display
        timing_text = f"{self.block.start_time_str} --> {self.block.end_time_str}"
        duration_ms = self.block.end_ms - self.block.start_ms
        duration_sec = duration_ms / 1000.0
        timing_text += f" ({duration_sec:.2f}s)"

        self.timing_label = QLabel(timing_text)
        self.timing_label.setStyleSheet("color: #00ffff; font-size: 10px; font-family: Consolas;")
        content_layout.addWidget(self.timing_label)

        layout.addLayout(content_layout, 1)

        # Set frame style
        self.setStyleSheet("""
            PhraseItemWidget {
                background-color: #1a1a1a;
                border: 1px solid #303030;
                border-radius: 4px;
            }
            PhraseItemWidget:hover {
                border-color: #00ffff;
                background-color: #202020;
            }
        """)

    def update_from_block(self, block: WordBlock):
        """Update display from block data."""
        self.block = block
        self.text_label.setText(block.text.replace('\n', ' '))

        timing_text = f"{block.start_time_str} --> {block.end_time_str}"
        duration_ms = block.end_ms - block.start_ms
        duration_sec = duration_ms / 1000.0
        timing_text += f" ({duration_sec:.2f}s)"
        self.timing_label.setText(timing_text)


class PhraseListWidget(QWidget):
    """
    Center panel displaying phrases from SRT file.

    Features:
    - List of phrase items with timing info
    - Selection syncs with timeline
    - Inline text editing
    - Signals for preview updates
    """

    # Signals
    phrase_selected = pyqtSignal(int)  # Emitted when user selects a phrase
    phrase_text_changed = pyqtSignal(int, str)  # index, new_text
    phrase_timing_changed = pyqtSignal(int, int, int)  # index, start_ms, end_ms
    srt_loaded = pyqtSignal(str)  # Emitted when SRT file is loaded

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model: Optional[SRTDataModel] = None
        self.selected_index: int = -1
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("PHRASES")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #00ffff;
            padding: 8px;
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Phrase count
        self.count_label = QLabel("0 phrases")
        self.count_label.setStyleSheet("color: #888888; padding: 8px;")
        header_layout.addWidget(self.count_label)

        layout.addLayout(header_layout)

        # SRT file info bar
        file_bar = QHBoxLayout()

        self.file_label = QLabel("No SRT loaded")
        self.file_label.setStyleSheet("color: #666666; padding: 4px 8px;")
        file_bar.addWidget(self.file_label, 1)

        self.browse_srt_btn = QPushButton("Load SRT")
        self.browse_srt_btn.setFixedWidth(80)
        self.browse_srt_btn.clicked.connect(self._browse_srt)
        file_bar.addWidget(self.browse_srt_btn)

        layout.addLayout(file_bar)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(4)
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.list_widget, 1)

        # Edit controls (shown when phrase is selected)
        self.edit_frame = QFrame()
        self.edit_frame.setVisible(False)
        edit_layout = QVBoxLayout(self.edit_frame)
        edit_layout.setContentsMargins(8, 8, 8, 8)
        edit_layout.setSpacing(6)

        edit_header = QLabel("Edit Phrase:")
        edit_header.setStyleSheet("color: #00ff88; font-weight: bold;")
        edit_layout.addWidget(edit_header)

        self.edit_input = QLineEdit()
        self.edit_input.setPlaceholderText("Edit phrase text...")
        self.edit_input.returnPressed.connect(self._apply_edit)
        edit_layout.addWidget(self.edit_input)

        edit_btn_row = QHBoxLayout()
        self.apply_edit_btn = QPushButton("Apply")
        self.apply_edit_btn.clicked.connect(self._apply_edit)
        self.cancel_edit_btn = QPushButton("Cancel")
        self.cancel_edit_btn.clicked.connect(self._cancel_edit)
        edit_btn_row.addStretch()
        edit_btn_row.addWidget(self.apply_edit_btn)
        edit_btn_row.addWidget(self.cancel_edit_btn)
        edit_layout.addLayout(edit_btn_row)

        layout.addWidget(self.edit_frame)

    def _apply_theme(self):
        """Apply BEDROT dark theme."""
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QListWidget {
                background-color: #151515;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 2px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 14px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #00ff88;
                min-height: 30px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00ffff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 8px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 1px solid #00ffff;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #00ffff;
                border-radius: 3px;
                padding: 6px 16px;
                color: #00ffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #252525;
            }
            QFrame#edit_frame {
                background-color: #1a1a1a;
                border: 1px solid #00ff88;
                border-radius: 4px;
            }
        """)

        self.edit_frame.setObjectName("edit_frame")
        self.edit_frame.setStyleSheet("""
            QFrame#edit_frame {
                background-color: #1a1a1a;
                border: 1px solid #00ff88;
                border-radius: 4px;
            }
        """)

    def _browse_srt(self):
        """Open file dialog to select SRT file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", "",
            "Subtitle Files (*.srt *.vtt);;All Files (*.*)"
        )
        if file_path:
            self.load_srt(file_path)

    def load_srt(self, srt_path: str) -> bool:
        """
        Load an SRT file into the phrase list.

        Args:
            srt_path: Path to SRT/VTT file

        Returns:
            True if successful
        """
        self.model = SRTDataModel(srt_path)

        if not self.model.blocks:
            self.file_label.setText("Error loading SRT")
            self.file_label.setStyleSheet("color: #ff4444; padding: 4px 8px;")
            return False

        self._refresh_list()

        # Update UI
        import os
        filename = os.path.basename(srt_path)
        self.file_label.setText(filename)
        self.file_label.setStyleSheet("color: #00ff88; padding: 4px 8px;")
        self.file_label.setToolTip(srt_path)

        self.srt_loaded.emit(srt_path)
        return True

    def set_model(self, model: SRTDataModel):
        """
        Set the data model directly.

        Args:
            model: SRTDataModel instance
        """
        self.model = model
        self._refresh_list()

        if model.file_path:
            import os
            filename = os.path.basename(model.file_path)
            self.file_label.setText(filename)
            self.file_label.setStyleSheet("color: #00ff88; padding: 4px 8px;")
            self.file_label.setToolTip(model.file_path)

    def _refresh_list(self):
        """Refresh the list widget from the model."""
        self.list_widget.clear()
        self.selected_index = -1

        if not self.model:
            self.count_label.setText("0 phrases")
            return

        for i, block in enumerate(self.model.blocks):
            item = QListWidgetItem()
            widget = PhraseItemWidget(block, i)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        self.count_label.setText(f"{len(self.model.blocks)} phrases")

    def _on_selection_changed(self, current_row: int):
        """Handle selection change in the list."""
        if current_row < 0:
            self.selected_index = -1
            self.edit_frame.setVisible(False)
            return

        self.selected_index = current_row

        # Highlight selected item
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                if i == current_row:
                    widget.setStyleSheet("""
                        PhraseItemWidget {
                            background-color: rgba(0, 255, 255, 0.15);
                            border: 1px solid #00ffff;
                            border-radius: 4px;
                        }
                    """)
                else:
                    widget.setStyleSheet("""
                        PhraseItemWidget {
                            background-color: #1a1a1a;
                            border: 1px solid #303030;
                            border-radius: 4px;
                        }
                        PhraseItemWidget:hover {
                            border-color: #00ffff;
                            background-color: #202020;
                        }
                    """)

        # Show edit frame with current text
        if self.model and 0 <= current_row < len(self.model.blocks):
            block = self.model.blocks[current_row]
            self.edit_input.setText(block.text)
            self.edit_frame.setVisible(True)

        # Emit selection signal
        self.phrase_selected.emit(current_row)

    def select_phrase(self, index: int):
        """
        Programmatically select a phrase.

        Args:
            index: Phrase index to select
        """
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)
            self.list_widget.scrollToItem(self.list_widget.item(index))

    def _apply_edit(self):
        """Apply the text edit to the current phrase."""
        if self.selected_index < 0 or not self.model:
            return

        new_text = self.edit_input.text().strip()
        if not new_text:
            return

        # Update model
        block = self.model.blocks[self.selected_index]
        old_text = block.text
        block.text = new_text

        # Update widget display
        item = self.list_widget.item(self.selected_index)
        widget = self.list_widget.itemWidget(item)
        if isinstance(widget, PhraseItemWidget):
            widget.update_from_block(block)

        # Emit signal
        self.phrase_text_changed.emit(self.selected_index, new_text)

    def _cancel_edit(self):
        """Cancel the text edit."""
        if self.selected_index >= 0 and self.model:
            block = self.model.blocks[self.selected_index]
            self.edit_input.setText(block.text)

    def update_phrase_timing(self, index: int, start_ms: int, end_ms: int):
        """
        Update the timing of a phrase (called from timeline).

        Args:
            index: Phrase index
            start_ms: New start time in milliseconds
            end_ms: New end time in milliseconds
        """
        if not self.model or index < 0 or index >= len(self.model.blocks):
            return

        block = self.model.blocks[index]
        block.start_ms = start_ms
        block.end_ms = end_ms

        # Update widget display
        item = self.list_widget.item(index)
        widget = self.list_widget.itemWidget(item)
        if isinstance(widget, PhraseItemWidget):
            widget.update_from_block(block)

    def get_selected_phrase(self) -> Optional[WordBlock]:
        """
        Get the currently selected phrase.

        Returns:
            WordBlock if a phrase is selected, None otherwise
        """
        if self.selected_index < 0 or not self.model:
            return None

        if 0 <= self.selected_index < len(self.model.blocks):
            return self.model.blocks[self.selected_index]

        return None

    def get_phrase_at(self, time_ms: int) -> Optional[int]:
        """
        Get the phrase index at a specific time.

        Args:
            time_ms: Time in milliseconds

        Returns:
            Phrase index or None if no phrase at that time
        """
        if not self.model:
            return None

        for i, block in enumerate(self.model.blocks):
            if block.start_ms <= time_ms <= block.end_ms:
                return i

        return None

    def get_model(self) -> Optional[SRTDataModel]:
        """Get the current data model."""
        return self.model

    def clear(self):
        """Clear the phrase list."""
        self.list_widget.clear()
        self.model = None
        self.selected_index = -1
        self.count_label.setText("0 phrases")
        self.file_label.setText("No SRT loaded")
        self.file_label.setStyleSheet("color: #666666; padding: 4px 8px;")
        self.edit_frame.setVisible(False)
