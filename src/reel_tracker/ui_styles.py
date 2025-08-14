# -*- coding: utf-8 -*-
"""
BEDROT UI Styles Module for Reel Tracker.

Centralized styling for all reel tracker dialogs to ensure consistent
BEDROT cyberpunk aesthetic across the application.
"""

# BEDROT Color Palette
COLORS = {
    # Backgrounds
    'bg_primary': '#121212',        # Main background
    'bg_secondary': '#1a1a1a',      # Panels, cards
    'bg_tertiary': '#202020',       # Alternate rows
    'bg_hover': '#252525',          # Hover states
    'bg_active': '#2a2a2a',         # Active/selected background
    'bg_darker': '#0a0a0a',         # Darker sections
    
    # Text
    'text_primary': '#e0e0e0',      # Main content
    'text_secondary': '#cccccc',    # Body text, tables
    'text_muted': '#888888',        # Disabled, hints
    'text_black': '#000000',        # For buttons with bright bg
    
    # Borders
    'border_primary': '#404040',    # Main borders
    'border_subtle': '#2a2a2a',     # Table gridlines
    'border_highlight': '#333333',  # Separators
    
    # Neon Accents
    'accent_green': '#00ff88',      # Primary actions, success
    'accent_cyan': '#00ffff',       # Highlights, active states
    'accent_magenta': '#ff00ff',    # Special actions
    'accent_pink': '#ff00aa',       # Secondary special actions
    'accent_orange': '#ff8800',     # Warnings, important
    'accent_red': '#ff0066',        # Danger, stop actions
    
    # Hover Variants
    'accent_green_hover': '#00ffaa',
    'accent_cyan_hover': '#66ffff',
    'accent_magenta_hover': '#ff66ff',
    'accent_pink_hover': '#ff44cc',
    'accent_orange_hover': '#ffaa00',
    'accent_red_hover': '#ff3388',
}

# Dialog Style Sheet
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    /* Labels */
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
        font-size: 12px;
    }}
    
    /* Group Boxes */
    QGroupBox {{
        border: 1px solid {COLORS['border_primary']};
        border-radius: 4px;
        margin-top: 6px;
        padding-top: 10px;
        font-weight: bold;
        font-size: 11px;
        color: {COLORS['accent_cyan']};
        background-color: {COLORS['bg_secondary']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        color: {COLORS['accent_cyan']};
        background-color: {COLORS['bg_primary']};
    }}
    
    /* Input Fields */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_highlight']};
        border-radius: 4px;
        padding: 5px;
        font-size: 12px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {COLORS['accent_cyan']};
        background-color: {COLORS['bg_active']};
    }}
    
    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_muted']};
    }}
    
    /* Combo Boxes */
    QComboBox {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_highlight']};
        border-radius: 4px;
        padding: 5px;
        min-width: 100px;
        font-size: 12px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {COLORS['accent_cyan']};
    }}
    
    QComboBox:focus {{
        border: 1px solid {COLORS['accent_magenta']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS['accent_green']};
        margin-right: 5px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['accent_green']};
        border: 1px solid {COLORS['accent_cyan']};
        selection-background-color: {COLORS['accent_magenta']};
        selection-color: {COLORS['text_black']};
    }}
    
    /* Check Boxes */
    QCheckBox {{
        color: {COLORS['text_primary']};
        spacing: 5px;
        font-size: 12px;
    }}
    
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS['border_primary']};
        border-radius: 3px;
        background-color: {COLORS['bg_secondary']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_green']};
        border: 1px solid {COLORS['accent_green']};
    }}
    
    QCheckBox::indicator:checked:hover {{
        background-color: {COLORS['accent_green_hover']};
    }}
    
    QCheckBox::indicator:unchecked:hover {{
        border: 1px solid {COLORS['accent_cyan']};
    }}
    
    /* Progress Bars */
    QProgressBar {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border_highlight']};
        border-radius: 4px;
        text-align: center;
        color: {COLORS['text_primary']};
        font-size: 11px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['accent_green']};
        border-radius: 3px;
    }}
    
    /* Tables */
    QTableWidget {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_secondary']};
        gridline-color: {COLORS['border_subtle']};
        selection-background-color: rgba(0, 255, 255, 0.3);
        selection-color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_primary']};
        border-radius: 4px;
        font-size: 11px;
        alternate-background-color: {COLORS['bg_secondary']};
    }}
    
    QTableWidget::item {{
        padding: 3px;
        border: none;
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_secondary']};
    }}
    
    QTableWidget::item:alternate {{
        background-color: {COLORS['bg_tertiary']};
    }}
    
    QTableWidget::item:selected {{
        background-color: rgba(0, 255, 255, 0.2);
        color: {COLORS['accent_cyan']};
    }}
    
    QTableWidget::item:hover {{
        background-color: {COLORS['bg_hover']};
        color: {COLORS['accent_green']};
    }}
    
    QHeaderView::section {{
        background-color: {COLORS['bg_darker']};
        color: {COLORS['accent_cyan']};
        padding: 6px;
        border: none;
        border-bottom: 2px solid {COLORS['accent_cyan']};
        border-right: 1px solid {COLORS['border_subtle']};
        font-weight: bold;
        font-size: 10px;
        text-transform: uppercase;
    }}
    
    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border_primary']};
        background-color: {COLORS['bg_secondary']};
        border-radius: 4px;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_muted']};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['accent_cyan']};
        border-bottom: 2px solid {COLORS['accent_cyan']};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['bg_active']};
        color: {COLORS['accent_green']};
    }}
    
    /* Scroll Bars */
    QScrollBar:vertical {{
        background-color: {COLORS['bg_darker']};
        width: 14px;
        border: 1px solid {COLORS['bg_secondary']};
        border-radius: 7px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['accent_green']};
        border-radius: 6px;
        min-height: 30px;
        margin: 1px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_cyan']};
        box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }}
    
    QScrollBar:horizontal {{
        background-color: {COLORS['bg_darker']};
        height: 14px;
        border: 1px solid {COLORS['bg_secondary']};
        border-radius: 7px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {COLORS['accent_green']};
        border-radius: 6px;
        min-width: 30px;
        margin: 1px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['accent_cyan']};
        box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        background: none;
        height: 0px;
        width: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    
    /* Splitters */
    QSplitter::handle {{
        background-color: {COLORS['border_primary']};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    /* Frame Separators */
    QFrame[frameShape="4"] {{
        color: {COLORS['border_highlight']};
        max-height: 2px;
    }}
    
    QFrame[frameShape="5"] {{
        color: {COLORS['border_highlight']};
        max-width: 2px;
    }}
"""

# Button Styles
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: rgba(0, 255, 136, 0.8);
            color: {COLORS['text_black']};
            font-weight: bold;
            padding: 6px 10px;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 255, 136, 0.9);
            box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
        }}
        QPushButton:pressed {{
            background-color: #00cc66;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
        }}
    """,
    
    'secondary': f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['accent_cyan']};
            border: 1px solid {COLORS['accent_cyan']};
            padding: 6px 10px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 255, 255, 0.1);
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
        }}
        QPushButton:pressed {{
            background-color: rgba(0, 255, 255, 0.2);
        }}
    """,
    
    'danger': f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['accent_red']};
            border: 1px solid {COLORS['accent_red']};
            padding: 6px 10px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 0, 102, 0.1);
            box-shadow: 0 0 5px rgba(255, 0, 102, 0.3);
            color: {COLORS['accent_red_hover']};
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 0, 102, 0.2);
        }}
    """,
    
    'special': f"""
        QPushButton {{
            background-color: rgba(255, 0, 255, 0.8);
            color: {COLORS['text_black']};
            font-weight: bold;
            padding: 6px 10px;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 0, 255, 0.9);
            box-shadow: 0 0 8px rgba(255, 0, 255, 0.3);
        }}
        QPushButton:pressed {{
            background-color: #cc00cc;
        }}
    """,
}

def apply_dialog_theme(dialog):
    """
    Apply BEDROT theme to a dialog.
    
    Args:
        dialog: QDialog instance to theme
    """
    dialog.setStyleSheet(DIALOG_STYLE)


def style_button(button, style_type='secondary'):
    """
    Apply BEDROT style to a button.
    
    Args:
        button: QPushButton instance
        style_type: One of 'primary', 'secondary', 'danger', 'special'
    """
    if style_type in BUTTON_STYLES:
        button.setStyleSheet(BUTTON_STYLES[style_type])


def style_header_label(label, size=16):
    """
    Style a header label with BEDROT theme.
    
    Args:
        label: QLabel instance
        size: Font size in pixels
    """
    label.setStyleSheet(f"""
        font-size: {size}px;
        font-weight: bold;
        color: {COLORS['accent_cyan']};
        background-color: transparent;
        padding: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    """)


def style_status_label(label, status='info'):
    """
    Style a status label based on status type.
    
    Args:
        label: QLabel instance
        status: One of 'info', 'success', 'warning', 'error'
    """
    color_map = {
        'info': COLORS['text_secondary'],
        'success': COLORS['accent_green'],
        'warning': COLORS['accent_orange'],
        'error': COLORS['accent_red']
    }
    
    color = color_map.get(status, COLORS['text_secondary'])
    label.setStyleSheet(f"""
        color: {color};
        font-size: 11px;
        padding: 2px;
        background-color: transparent;
    """)


def get_dialog_button_box_style():
    """
    Get style for QDialogButtonBox buttons.
    
    Returns:
        str: Style sheet for dialog button boxes
    """
    return f"""
        QDialogButtonBox QPushButton {{
            background-color: transparent;
            color: {COLORS['accent_cyan']};
            border: 1px solid {COLORS['accent_cyan']};
            padding: 6px 20px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 80px;
        }}
        
        QDialogButtonBox QPushButton:hover {{
            background-color: rgba(0, 255, 255, 0.1);
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
        }}
        
        QDialogButtonBox QPushButton:pressed {{
            background-color: rgba(0, 255, 255, 0.2);
        }}
        
        QDialogButtonBox QPushButton:default {{
            background-color: rgba(0, 255, 136, 0.8);
            color: {COLORS['text_black']};
            border: none;
        }}
        
        QDialogButtonBox QPushButton:default:hover {{
            background-color: rgba(0, 255, 136, 0.9);
            box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
        }}
    """