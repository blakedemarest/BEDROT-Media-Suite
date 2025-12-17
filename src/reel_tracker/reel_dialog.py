# -*- coding: utf-8 -*-
"""
Reel Entry Dialog Module for Reel Tracker.

Provides functionality for:
- Manual reel data entry and editing
- File browsing and media selection
- Auto-generation of captions and templates
- Integration with media randomizer
"""

import os
import datetime
import random
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QTextEdit, 
    QDialogButtonBox, QFileDialog, QMessageBox, QMenuBar, QAction
)
from PyQt5.QtCore import Qt
from .config_manager import ConfigManager
from .media_randomizer import MediaRandomizerDialog
from .custom_item_manager import CustomItemManagerDialog
from .utils import safe_print
from .ui_styles import apply_dialog_theme, style_button, get_dialog_button_box_style


class ReelEntryDialog(QDialog):
    """
    Dialog for manually entering/editing reel data with robust input methods.
    Enhanced with media randomization support and configuration management.
    """
    
    def __init__(self, parent=None, reel_data=None, config_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Reel Entry")
        self.setModal(True)
        self.resize(700, 600)
        
        # Apply BEDROT theme
        apply_dialog_theme(self)
        
        # Use config manager or create one
        self.config_manager = config_manager or ConfigManager()
        
        # Get dropdown options from config with fallbacks
        if self.config_manager:
            self.persona_options = self.config_manager.get_dropdown_values("persona")
            self.reel_type_options = self.config_manager.get_dropdown_values("reel_type")
            self.release_options = self.config_manager.get_dropdown_values("release")
            # Visual template removed from schema
        else:
            # Fallback options if config manager failed
            self.persona_options = [
                "", "Fitness Influencer", "Tech Reviewer", "Lifestyle Blogger", 
                "Food Creator", "Travel Vlogger", "Educational", "Entertainment",
                "Business", "Music Artist", "Fashion", "Gaming", "Comedy"
            ]
            self.reel_type_options = [
                "", "Tutorial", "Product Review", "Behind the Scenes", "Q&A",
                "Transformation", "Day in Life", "Tips & Tricks", "Unboxing",
                "Comparison", "Story Time", "Challenge", "Trend", "Educational"
            ]
            self.release_options = [
                "", "RENEGADE PIPELINE", "THE STATE OF THE WORLD", "THE SCALE"
            ]
            # Visual template removed from schema
        
        self.setup_ui()
        
        # Populate with existing data if provided
        if reel_data:
            self.populate_fields(reel_data)
    
    def setup_ui(self):
        """Setup the dialog UI with organized input sections."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create menu bar
        self.create_menu_bar(layout)
        
        # Create scrollable area for form
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Section
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        # Reel ID - Auto-generate option
        reel_id_layout = QHBoxLayout()
        self.reel_id_edit = QLineEdit()
        self.reel_id_edit.setPlaceholderText("e.g., REEL_001, or leave blank to auto-generate")
        self.auto_id_btn = QPushButton("Auto-Generate ID")
        self.auto_id_btn.clicked.connect(self.generate_reel_id)
        reel_id_layout.addWidget(self.reel_id_edit)
        reel_id_layout.addWidget(self.auto_id_btn)
        basic_layout.addRow("Reel ID:", reel_id_layout)
        
        # Persona dropdown with custom option
        persona_layout = QHBoxLayout()
        self.persona_combo = QComboBox()
        self.persona_combo.setEditable(True)
        self.persona_combo.addItems(self.persona_options)
        persona_layout.addWidget(self.persona_combo)
        basic_layout.addRow("Persona:", persona_layout)
        
        # Release status dropdown
        self.release_combo = QComboBox()
        self.release_combo.setEditable(True)
        self.release_combo.addItems(self.release_options)
        basic_layout.addRow("Release:", self.release_combo)
        
        # Reel Type dropdown with custom option
        self.reel_type_combo = QComboBox()
        self.reel_type_combo.setEditable(True)
        self.reel_type_combo.addItems(self.reel_type_options)
        basic_layout.addRow("Reel Type:", self.reel_type_combo)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # File Information Section - Enhanced with randomization
        file_group = QGroupBox("📁 File Information & Media Selection")
        file_layout = QFormLayout()
        
        # Clip Filename with browse and randomize buttons
        filename_layout = QHBoxLayout()
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("video.mp4, audio.wav, image.jpg, etc.")
        self.browse_file_btn = QPushButton("Browse...")
        self.browse_file_btn.clicked.connect(self.browse_for_file)
        self.randomize_btn = QPushButton("🎲 Randomize")
        self.randomize_btn.clicked.connect(self.randomize_media)
        self.randomize_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        filename_layout.addWidget(self.filename_edit)
        filename_layout.addWidget(self.browse_file_btn)
        filename_layout.addWidget(self.randomize_btn)
        file_layout.addRow("Clip Filename:", filename_layout)
        
        # FilePath with browse button
        filepath_layout = QHBoxLayout()
        self.filepath_edit = QLineEdit()
        self.filepath_edit.setPlaceholderText("Full path to the media file")
        self.browse_path_btn = QPushButton("Browse...")
        self.browse_path_btn.clicked.connect(self.browse_for_path)
        filepath_layout.addWidget(self.filepath_edit)
        filepath_layout.addWidget(self.browse_path_btn)
        file_layout.addRow("File Path:", filepath_layout)
        
        # File info display
        self.file_info_display = QLabel("No file selected")
        self.file_info_display.setStyleSheet("background: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.file_info_display.setWordWrap(True)
        file_layout.addRow("File Info:", self.file_info_display)
        
        file_group.setLayout(file_layout)
        scroll_layout.addWidget(file_group)
        
        # Visual Template Section removed from schema
        
        # Caption Section
        caption_group = QGroupBox("📝 Caption & Content")
        caption_layout = QVBoxLayout()
        
        caption_label = QLabel("Caption:")
        self.caption_edit = QTextEdit()
        self.caption_edit.setPlaceholderText("Enter your reel caption here...\n\nTips:\n- Use hashtags\n- Include call-to-action\n- Keep it engaging")
        self.caption_edit.setMaximumHeight(120)
        
        # Caption helpers
        caption_tools_layout = QHBoxLayout()
        self.char_count_label = QLabel("Characters: 0")
        self.add_hashtags_btn = QPushButton("Add Popular Hashtags")
        self.add_hashtags_btn.clicked.connect(self.add_sample_hashtags)
        self.generate_caption_btn = QPushButton("🤖 Generate Caption")
        self.generate_caption_btn.clicked.connect(self.generate_caption_ideas)
        caption_tools_layout.addWidget(self.char_count_label)
        caption_tools_layout.addStretch()
        caption_tools_layout.addWidget(self.generate_caption_btn)
        caption_tools_layout.addWidget(self.add_hashtags_btn)
        
        # Connect character counter
        self.caption_edit.textChanged.connect(self.update_char_count)
        
        caption_layout.addWidget(caption_label)
        caption_layout.addWidget(self.caption_edit)
        caption_layout.addLayout(caption_tools_layout)
        
        caption_group.setLayout(caption_layout)
        scroll_layout.addWidget(caption_group)
        
        layout.addWidget(scroll_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_menu_bar(self, layout):
        """Create menu bar for custom item management."""
        menubar = QMenuBar()
        layout.addWidget(menubar)
        
        # Manage menu
        manage_menu = menubar.addMenu('Manage Items')
        
        # Personas submenu
        personas_action = QAction('Manage Personas', self)
        personas_action.triggered.connect(lambda: self.manage_custom_items('persona'))
        manage_menu.addAction(personas_action)
        
        # Reel Types submenu
        reel_types_action = QAction('Manage Reel Types', self)
        reel_types_action.triggered.connect(lambda: self.manage_custom_items('reel_type'))
        manage_menu.addAction(reel_types_action)
        
        # Template Types submenu removed from schema
        
        manage_menu.addSeparator()
        
        # Release states submenu
        release_action = QAction('Manage Release States', self)
        release_action.triggered.connect(lambda: self.manage_custom_items('release'))
        manage_menu.addAction(release_action)
    
    def manage_custom_items(self, item_type):
        """Open custom item management dialog."""
        if not self.config_manager:
            QMessageBox.warning(self, "Configuration Unavailable", "Configuration manager is not available.")
            return
            
        dialog = CustomItemManagerDialog(self, item_type, self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            # Refresh the appropriate combo box
            self.refresh_dropdown_options(item_type)
            QMessageBox.information(self, "Items Updated", f"{item_type.replace('_', ' ').title()} items have been updated.")
    
    def refresh_dropdown_options(self, item_type):
        """Refresh dropdown options after custom item management."""
        if not self.config_manager:
            return
            
        # Get updated options
        updated_options = self.config_manager.get_dropdown_values(item_type)
        
        # Update the appropriate combo box
        if item_type == 'persona':
            current_text = self.persona_combo.currentText()
            self.persona_combo.clear()
            self.persona_combo.addItems(updated_options)
            self.persona_combo.setCurrentText(current_text)
            self.persona_options = updated_options
            
        elif item_type == 'reel_type':
            current_text = self.reel_type_combo.currentText()
            self.reel_type_combo.clear()
            self.reel_type_combo.addItems(updated_options)
            self.reel_type_combo.setCurrentText(current_text)
            self.reel_type_options = updated_options
            
        # visual_template removed from schema
            
        elif item_type == 'release':
            current_text = self.release_combo.currentText()
            self.release_combo.clear()
            self.release_combo.addItems(updated_options)
            self.release_combo.setCurrentText(current_text)
            self.release_options = updated_options
    
    def generate_reel_id(self):
        """Generate a unique reel ID with sequential numbering."""
        # Get the parent window if available to check existing IDs
        parent = self.parent()
        if hasattr(parent, 'table'):
            # Find the highest existing REEL_XXX number
            max_num = 0
            reel_id_col = 0  # Reel ID is first column
            
            for row in range(parent.table.rowCount()):
                item = parent.table.item(row, reel_id_col)
                if item:
                    reel_id = item.text()
                    # Extract number from patterns like REEL_001, RP_001, etc.
                    import re
                    match = re.search(r'_(\d+)$', reel_id)
                    if match:
                        num = int(match.group(1))
                        max_num = max(max_num, num)
            
            # Generate next ID
            next_num = max_num + 1
            reel_id = f"REEL_{next_num:03d}"
        else:
            # Fallback: use simple counter or timestamp
            # For safety, still use timestamp but shorter format
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            reel_id = f"REEL_{timestamp}"
        
        self.reel_id_edit.setText(reel_id)
    
    def randomize_media(self):
        """Open media randomizer dialog."""
        randomizer = MediaRandomizerDialog(self)
        if randomizer.exec_() == QDialog.Accepted:
            selected_file = randomizer.get_selected_file()
            if selected_file:
                self.filepath_edit.setText(selected_file)
                self.filename_edit.setText(os.path.basename(selected_file))
                self.update_file_info(selected_file)
                
                # Auto-suggest template based on file type
                # Auto-suggest template removed (Visual Template column removed)
                
                # Auto-fill release with default value
                self.auto_fill_release(selected_file)
    
    def browse_for_file(self):
        """Browse for a media file and auto-fill filename and path."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", "", 
            "Media Files (*.mp4 *.avi *.mov *.mkv *.mp3 *.wav *.jpg *.jpeg *.png *.gif *.bmp);;All Files (*)"
        )
        if file_path:
            self.filepath_edit.setText(file_path)
            self.filename_edit.setText(os.path.basename(file_path))
            self.update_file_info(file_path)
            
            # Auto-fill release with default value when file is selected
            self.auto_fill_release(file_path)
    
    def browse_for_path(self):
        """Browse for file path only."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File Path", "", "All Files (*)"
        )
        if file_path:
            self.filepath_edit.setText(file_path)
            if not self.filename_edit.text():
                self.filename_edit.setText(os.path.basename(file_path))
            self.update_file_info(file_path)
            
            # Auto-fill release with default value when file is selected
            self.auto_fill_release(file_path)
    
    def update_file_info(self, file_path):
        """Update file information display."""
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_ext = Path(file_path).suffix.lower()
                
                # Format file size
                size_str = self.format_file_size(file_size)
                
                # Determine file type
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
                
                if file_ext in video_extensions:
                    file_type = "[VIDEO]"
                elif file_ext in image_extensions:
                    file_type = "[IMAGE]"
                else:
                    file_type = "[FILE]"
                
                info_text = f"{file_type} • {file_ext.upper()} • {size_str}"
                self.file_info_display.setText(info_text)
            else:
                self.file_info_display.setText("[ERROR] File not found")
        except Exception as e:
            self.file_info_display.setText(f"[ERROR] Error: {str(e)}")
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0B"
        import math
        size_names = ["B", "KB", "MB", "GB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s}{size_names[i]}"
    
    def auto_fill_release(self, file_path):
        """Auto-fill release with default value when a file is selected."""
        # Only auto-fill if release is currently empty
        if not self.release_combo.currentText().strip():
            # Set default release for video/media files
            if file_path and os.path.exists(file_path):
                file_ext = Path(file_path).suffix.lower()
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
                
                if file_ext in video_extensions or file_ext in image_extensions:
                    # Set to "RENEGADE PIPELINE" as default release for media files
                    default_release = "RENEGADE PIPELINE"
                    if default_release in self.release_options:
                        self.release_combo.setCurrentText(default_release)
                        safe_print(f"[OK] Auto-filled release: {default_release}")
    
    # auto_suggest_template method removed (Visual Template column removed from schema)
    
    def generate_caption_ideas(self):
        """Generate caption ideas based on reel type and persona."""
        reel_type = self.reel_type_combo.currentText()
        persona = self.persona_combo.currentText()
        
        # Caption templates based on type and persona
        caption_templates = {
            "Tutorial": [
                "Here's how to {action} in just a few simple steps! 💡",
                "Tutorial time! Let me show you the easiest way to {action} ✨",
                "Step-by-step guide to {action} - save this for later! 📌"
            ],
            "Product Review": [
                "Honest review of {product} - is it worth the hype? 🤔",
                "Testing {product} so you don't have to! Here's what I found... 👀",
                "My thoughts on {product} after using it for [time period] 📝"
            ],
            "Behind the Scenes": [
                "Behind the scenes of creating {content} 🎬",
                "The process behind {content} - it's more work than you think! 😅",
                "Take a peek behind the curtain of {content} creation ✨"
            ],
            "Tips & Tricks": [
                "Pro tip that will change your {topic} game forever! 🔥",
                "This {topic} hack will save you so much time ⏰",
                "Secret {topic} tip that nobody talks about 🤫"
            ]
        }
        
        # Get template suggestions
        if reel_type in caption_templates:
            templates = caption_templates[reel_type]
            selected_template = random.choice(templates)
            
            # Add persona-specific touches
            if persona == "Fitness Influencer":
                selected_template += "\n\n#fitness #workout #motivation #fitlife"
            elif persona == "Tech Reviewer":
                selected_template += "\n\n#tech #review #gadgets #technology"
            elif persona == "Food Creator":
                selected_template += "\n\n#food #recipe #cooking #foodie"
            else:
                selected_template += "\n\n#content #creator #viral #trending"
        else:
            selected_template = "Amazing content coming your way! What do you think? 🔥\n\n#content #creator #viral #trending"
        
        # Set the generated caption
        current_text = self.caption_edit.toPlainText()
        if current_text.strip():
            self.caption_edit.setPlainText(current_text + "\n\n---\n\nGenerated idea:\n" + selected_template)
        else:
            self.caption_edit.setPlainText(selected_template)
    
    def add_sample_hashtags(self):
        """Add sample hashtags to caption."""
        persona = self.persona_combo.currentText()
        reel_type = self.reel_type_combo.currentText()
        
        # Hashtag sets based on persona and type
        hashtag_sets = {
            "Fitness Influencer": ["#fitness", "#workout", "#motivation", "#fitlife", "#gym"],
            "Tech Reviewer": ["#tech", "#review", "#gadgets", "#technology", "#innovation"],
            "Food Creator": ["#food", "#recipe", "#cooking", "#foodie", "#delicious"],
            "Travel Vlogger": ["#travel", "#wanderlust", "#explore", "#adventure", "#vacation"],
            "Gaming": ["#gaming", "#gamer", "#gameplay", "#streamer", "#esports"]
        }
        
        # Get relevant hashtags
        if persona in hashtag_sets:
            hashtags = hashtag_sets[persona]
        else:
            hashtags = ["#reels", "#viral", "#trending", "#content", "#creator"]
        
        # Add type-specific hashtags
        if reel_type == "Tutorial":
            hashtags.extend(["#tutorial", "#howto", "#learn"])
        elif reel_type == "Tips & Tricks":
            hashtags.extend(["#tips", "#tricks", "#hacks"])
        
        current_text = self.caption_edit.toPlainText()
        if current_text and not current_text.endswith('\n'):
            current_text += '\n\n'
        elif not current_text:
            current_text = ""
        
        hashtag_text = " ".join(hashtags[:8])  # Limit to 8 hashtags
        self.caption_edit.setPlainText(current_text + hashtag_text)
    
    def update_char_count(self):
        """Update character count for caption."""
        text = self.caption_edit.toPlainText()
        char_count = len(text)
        self.char_count_label.setText(f"Characters: {char_count}")
        
        # Color coding for Instagram limits
        if char_count > 2200:
            self.char_count_label.setStyleSheet("color: red;")
        elif char_count > 2000:
            self.char_count_label.setStyleSheet("color: orange;")
        else:
            self.char_count_label.setStyleSheet("color: green;")
    
    def accept(self):
        """Override accept to save new dropdown values before closing."""
        try:
            # Save any new dropdown values when dialog is accepted
            persona_value = self.persona_combo.currentText().strip()
            release_value = self.release_combo.currentText().strip()
            reel_type_value = self.reel_type_combo.currentText().strip()
            
            if self.config_manager:
                if persona_value:
                    self.config_manager.add_dropdown_value("persona", persona_value)
                if release_value:
                    self.config_manager.add_dropdown_value("release", release_value)
                if reel_type_value:
                    self.config_manager.add_dropdown_value("reel_type", reel_type_value)
                
        except Exception as e:
            safe_print(f"Warning: Could not save dropdown values: {e}")
        
        # Call parent accept
        super().accept()
    
    def populate_fields(self, reel_data):
        """Populate dialog fields with existing reel data."""
        # Handle both old 8-column format and new 7-column format (Visual Template removed)
        if len(reel_data) >= 7:
            self.reel_id_edit.setText(str(reel_data[0]))
            
            # Set combo box values (handle custom values)
            self.set_combo_value(self.persona_combo, str(reel_data[1]))
            self.set_combo_value(self.release_combo, str(reel_data[2]))
            self.set_combo_value(self.reel_type_combo, str(reel_data[3]))
            
            self.filename_edit.setText(str(reel_data[4]))
            
            # Handle both old format (with visual template) and new format (without)
            if len(reel_data) >= 8:  # Old format with visual template
                # Skip reel_data[5] (visual template)
                self.caption_edit.setPlainText(str(reel_data[6]))
                file_path = str(reel_data[7])
            else:  # New format without visual template
                self.caption_edit.setPlainText(str(reel_data[5]))
                file_path = str(reel_data[6])
            
            self.filepath_edit.setText(file_path)
            if file_path:
                self.update_file_info(file_path)
    
    def set_combo_value(self, combo_box, value):
        """Set combo box value, add to list if not present."""
        index = combo_box.findText(value)
        if index >= 0:
            combo_box.setCurrentIndex(index)
        else:
            combo_box.addItem(value)
            combo_box.setCurrentText(value)
    
    def get_data(self):
        """Extract data from dialog fields (Visual Template removed)."""
        return [
            self.reel_id_edit.text().strip(),
            self.persona_combo.currentText().strip(),
            self.release_combo.currentText().strip(),
            self.reel_type_combo.currentText().strip(),
            self.filename_edit.text().strip(),
            self.caption_edit.toPlainText().strip(),
            self.filepath_edit.text().strip()
        ]