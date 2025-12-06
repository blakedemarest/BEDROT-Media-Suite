# -*- coding: utf-8 -*-
"""
Word Editor View for Caption Generator SRT Editor.

Provides a visual word-block editor with color-coded blocks for each SRT entry.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QDialog, QLineEdit, QFormLayout, QMessageBox,
    QSizePolicy, QLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect
from PyQt5.QtGui import QFont

from .srt_data_model import SRTDataModel, WordBlock, srt_timestamp_to_ms, ms_to_srt_timestamp


class FlowLayout(QLayout):
    """
    Custom layout that arranges widgets in a flowing manner, wrapping to next row
    when the current row is full (like text wrapping in a paragraph).
    """

    def __init__(self, parent=None, margin=0, h_spacing=6, v_spacing=6):
        """
        Initialize the flow layout.

        Args:
            parent: Parent widget
            margin: Layout margin
            h_spacing: Horizontal spacing between items
            v_spacing: Vertical spacing between rows
        """
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []

    def __del__(self):
        """Clean up layout items on deletion."""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """Add item to layout."""
        self._items.append(item)

    def horizontalSpacing(self):
        """Get horizontal spacing."""
        return self._h_spacing

    def verticalSpacing(self):
        """Get vertical spacing."""
        return self._v_spacing

    def count(self):
        """Return number of items."""
        return len(self._items)

    def itemAt(self, index):
        """Get item at index."""
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        """Remove and return item at index."""
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        """Return expanding directions (none)."""
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        """This layout has height depending on width."""
        return True

    def heightForWidth(self, width):
        """Calculate height needed for given width."""
        height = self._do_layout(QRect(0, 0, width, 0), test_only=True)
        return height

    def setGeometry(self, rect):
        """Set the geometry of the layout."""
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        """Return size hint."""
        return self.minimumSize()

    def minimumSize(self):
        """Return minimum size."""
        size = QSize()

        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                     margins.top() + margins.bottom())

        return size

    def _do_layout(self, rect, test_only):
        """
        Perform the actual layout calculation.

        Args:
            rect: Available rectangle
            test_only: If True, only calculate height without moving widgets

        Returns:
            Total height needed
        """
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._items:
            widget = item.widget()
            h_space = self._h_spacing
            v_space = self._v_spacing

            next_x = x + item.sizeHint().width() + h_space

            if next_x - h_space > effective_rect.right() and line_height > 0:
                # Wrap to next line
                x = effective_rect.x()
                y = y + line_height + v_space
                next_x = x + item.sizeHint().width() + h_space
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom


class WordBlockWidget(QPushButton):
    """
    Single colored block representing one SRT entry.

    Displays the text with a colored background that cycles through
    the color palette for visual distinction.
    """

    # Emitted when the block is clicked for editing
    edit_requested = pyqtSignal(int)  # Emits block index

    def __init__(self, block: WordBlock, block_index: int, parent=None):
        """
        Initialize the word block widget.

        Args:
            block: WordBlock data object
            block_index: Index in the blocks list
            parent: Parent widget
        """
        super().__init__(parent)

        self.block = block
        self.block_index = block_index

        # Display text (truncate if too long, show first line only)
        display_text = block.text.split('\n')[0]
        if len(display_text) > 30:
            display_text = display_text[:27] + "..."

        self.setText(display_text)
        self.setToolTip(
            f"[{block.index}] {block.start_time_str} --> {block.end_time_str}\n"
            f"{block.text}"
        )

        # Apply styling with the block's color
        self._apply_style()

        # Connect click signal
        self.clicked.connect(self._on_clicked)

    def _apply_style(self):
        """Apply the colored button style."""
        bg_color = self.block.color

        # Calculate contrasting text color (use black for light colors)
        # Simple heuristic: yellow and green variants get black text
        text_color = '#000000' if self.block.index % 7 in [2, 3] else '#000000'

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font-weight: bold;
                font-size: 13px;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                border: 2px solid #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {bg_color};
                opacity: 0.8;
            }}
        """)

        self.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)

    def _on_clicked(self):
        """Handle click event."""
        self.edit_requested.emit(self.block_index)

    def update_block(self, block: WordBlock):
        """Update the displayed block data."""
        self.block = block

        display_text = block.text.split('\n')[0]
        if len(display_text) > 30:
            display_text = display_text[:27] + "..."

        self.setText(display_text)
        self.setToolTip(
            f"[{block.index}] {block.start_time_str} --> {block.end_time_str}\n"
            f"{block.text}"
        )


class WordBlockEditDialog(QDialog):
    """
    Modal dialog for editing a single word block.

    Allows editing of text content and start/end timestamps.
    """

    def __init__(self, block: WordBlock, parent=None):
        """
        Initialize the edit dialog.

        Args:
            block: WordBlock to edit
            parent: Parent widget
        """
        super().__init__(parent)

        self.block = block
        self.result_data = None

        self.setWindowTitle(f"Edit Block #{block.index}")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QFormLayout(self)
        layout.setSpacing(12)

        # Text input
        self.text_edit = QLineEdit(self.block.text)
        self.text_edit.setPlaceholderText("Enter subtitle text...")
        layout.addRow("Text:", self.text_edit)

        # Start time input
        self.start_edit = QLineEdit(self.block.start_time_str)
        self.start_edit.setPlaceholderText("HH:MM:SS,mmm")
        layout.addRow("Start Time:", self.start_edit)

        # End time input
        self.end_edit = QLineEdit(self.block.end_time_str)
        self.end_edit.setPlaceholderText("HH:MM:SS,mmm")
        layout.addRow("End Time:", self.end_edit)

        # Info label
        info_label = QLabel("Format: HH:MM:SS,mmm (e.g., 00:01:23,456)")
        info_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addRow("", info_label)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("SAVE")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 136, 0.8);
                color: #000000;
                font-weight: bold;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 136, 0.9);
            }
        """)
        save_btn.clicked.connect(self._on_save)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff0066;
                border: 1px solid #ff0066;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 102, 0.1);
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

    def _apply_theme(self):
        """Apply BEDROT dark theme."""
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #00ffff;
            }
        """)

    def _on_save(self):
        """Validate and save the edited block."""
        text = self.text_edit.text().strip()
        start_str = self.start_edit.text().strip()
        end_str = self.end_edit.text().strip()

        # Validate text
        if not text:
            QMessageBox.warning(self, "Invalid Input", "Text cannot be empty.")
            return

        # Validate timestamps
        try:
            start_ms = srt_timestamp_to_ms(start_str)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Start Time", str(e))
            return

        try:
            end_ms = srt_timestamp_to_ms(end_str)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid End Time", str(e))
            return

        # Store result and accept
        self.result_data = {
            'text': text,
            'start_ms': start_ms,
            'end_ms': end_ms
        }
        self.accept()

    def get_result(self) -> dict:
        """Get the edited block data (or None if cancelled)."""
        return self.result_data


class WordEditorView(QScrollArea):
    """
    Scrollable container for all word blocks.

    Displays SRT entries as colored, clickable blocks in a flowing layout.
    """

    # Emitted when any block is edited
    data_changed = pyqtSignal()

    def __init__(self, model: SRTDataModel, parent=None):
        """
        Initialize the word editor view.

        Args:
            model: SRTDataModel instance to display
            parent: Parent widget
        """
        super().__init__(parent)

        self.model = model
        self._block_widgets = []

        self._setup_ui()
        self.refresh_blocks()

    def _setup_ui(self):
        """Set up the scroll area and container."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Apply scroll bar styling
        self.setStyleSheet("""
            QScrollArea {
                background-color: #121212;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #0a0a0a;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #00ff88;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00ffff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Create container widget with flow layout
        self._container = QWidget()
        self._container.setStyleSheet("background-color: #121212;")

        self._layout = FlowLayout(self._container, margin=12, h_spacing=8, v_spacing=8)

        self.setWidget(self._container)

    def refresh_blocks(self):
        """Rebuild all word block widgets from the model."""
        # Clear existing widgets
        for widget in self._block_widgets:
            widget.deleteLater()
        self._block_widgets = []

        # Clear layout
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create new block widgets
        for idx, block in enumerate(self.model.blocks):
            widget = WordBlockWidget(block, idx)
            widget.edit_requested.connect(self._on_edit_block)
            self._layout.addWidget(widget)
            self._block_widgets.append(widget)

        # Update container size
        self._container.adjustSize()

    def _on_edit_block(self, block_index: int):
        """Handle block edit request."""
        if block_index >= len(self.model.blocks):
            return

        block = self.model.blocks[block_index]

        # Open edit dialog
        dialog = WordBlockEditDialog(block, self)

        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()

            if result:
                # Update model
                self.model.update_block(
                    block_index,
                    result['text'],
                    result['start_ms'],
                    result['end_ms']
                )

                # Update widget
                if block_index < len(self._block_widgets):
                    self._block_widgets[block_index].update_block(
                        self.model.blocks[block_index]
                    )

                # Emit change signal
                self.data_changed.emit()

    def sync_from_model(self):
        """Refresh view from model (alias for refresh_blocks)."""
        self.refresh_blocks()
