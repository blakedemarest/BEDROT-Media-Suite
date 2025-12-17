# -*- coding: utf-8 -*-
"""
BEDROT theme configuration for PyQt5.

Extracted from main_app.py to decouple theme/styling from application logic.
"""

from __future__ import annotations


BEDROT_COLORS = {
    "bg": "#121212",
    "bg_secondary": "#1a1a1a",
    "bg_tertiary": "#202020",
    "bg_hover": "#252525",
    "bg_dark": "#0a0a0a",
    "bg_table": "#151515",
    "fg": "#e0e0e0",
    "fg_secondary": "#cccccc",
    "fg_muted": "#888888",
    "accent_green": "#00ff88",
    "accent_cyan": "#00ffff",
    "accent_magenta": "#ff00ff",
    "border": "#333333",
    "border_dark": "#2a2a2a",
    "border_light": "#404040",
}


def get_bedrot_stylesheet() -> str:
    """
    Return the complete BEDROT cyberpunk dark theme stylesheet for PyQt5.

    Returns:
        Complete stylesheet string for QApplication.setStyleSheet()
    """
    return """
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


def apply_bedrot_theme(window) -> dict:
    """
    Apply the BEDROT cyberpunk visual theme to a PyQt5 window.

    Args:
        window: The QMainWindow or QWidget to apply the theme to.

    Returns:
        Dictionary of color values for use in widget configuration.
    """
    window.setStyleSheet(get_bedrot_stylesheet())
    return BEDROT_COLORS.copy()
