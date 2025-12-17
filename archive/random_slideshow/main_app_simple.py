# -*- coding: utf-8 -*-
"""
Simple Main Application Module for Random Slideshow Generator.
No batch processing, just basic single generation functionality.
"""

import os
import sys
import glob
import subprocess
import platform

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
        QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox,
        QComboBox, QInputDialog
    )
    from PyQt5.QtCore import Qt
except ImportError as e:
    print(f"ERROR: Could not import PyQt5: {e}")
    print("Please install PyQt5: pip install PyQt5")
    sys.exit(1)

# Try to set up imports
try:
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from config_manager import ConfigManager
    from slideshow_worker import RandomSlideshowWorker
    from image_processor import ImageProcessor
    from preset_manager import PresetManager
    from preset_dialog import PresetDialog
except ImportError as e:
    print(f"ERROR: Could not import required modules: {e}")
    ConfigManager = None
    RandomSlideshowWorker = None
    ImageProcessor = None
    PresetManager = None
    PresetDialog = None


class RandomSlideshowEditor(QWidget):
    """Simple main application window for Random Slideshow Generator."""
    
    def __init__(self):
        super().__init__()
        print("Initializing RandomSlideshowEditor...")
        
        self.setWindowTitle("BEDROT RANDOM SLIDESHOW // CYBERCORE GENERATION")
        self.resize(700, 500)
        
        # Apply BEDROT theme
        self.apply_bedrot_theme()
        
        # Check if we have required modules
        if ConfigManager is None:
            self.show_error_ui()
            return
        
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager()
            self.total_generations = 0
            self.worker_thread = None
            
            # Initialize preset manager
            self.preset_manager = PresetManager() if PresetManager else None
            self.current_preset = None
            
            # Setup UI
            self.setup_ui()
            print("UI setup complete")
            
            # Load last used preset if available
            if self.preset_manager:
                last_preset = self.preset_manager.get_last_used_preset()
                if last_preset:
                    self.load_preset(last_preset)
            
        except Exception as e:
            print(f"ERROR during initialization: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_ui(str(e))
    
    def show_error_ui(self, error_msg="Required modules could not be imported"):
        """Show error UI when initialization fails."""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"<h2>Initialization Error</h2><p>{error_msg}</p>")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def apply_bedrot_theme(self):
        """Apply the BEDROT cyberpunk visual theme."""
        theme = """
        /* Main Widget Background */
        QWidget {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }
        
        /* Group Boxes */
        QGroupBox {
            background-color: #121212;
            border: 1px solid #00ffff;
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 10px;
            font-size: 10px;
            font-weight: bold;
            color: #00ffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #00ffff;
            background-color: #121212;
        }
        
        /* Labels */
        QLabel {
            color: #e0e0e0;
            background-color: transparent;
        }
        
        /* Line Edits */
        QLineEdit {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
            selection-background-color: #00ffff;
            selection-color: #000000;
        }
        
        QLineEdit:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QLineEdit:disabled {
            background-color: #0a0a0a;
            color: #666666;
        }
        
        /* Push Buttons */
        QPushButton {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 6px 10px;
            color: #e0e0e0;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #252525;
            border: 1px solid #00ff88;
            color: #00ff88;
        }
        
        QPushButton:pressed {
            background-color: #0a0a0a;
            border: 1px solid #00ffff;
            color: #00ffff;
        }
        
        QPushButton:disabled {
            background-color: #0a0a0a;
            border: 1px solid #2a2a2a;
            color: #666666;
        }
        
        /* Toggle Button (Start/Stop) */
        QPushButton:checked {
            background-color: #ff0066;
            border: none;
            color: #ffffff;
        }
        
        QPushButton:checked:hover {
            background-color: #ff3388;
        }
        
        QPushButton:checked:pressed {
            background-color: #cc0044;
        }
        
        QPushButton#startButton {
            background-color: #00ff88;
            border: none;
            color: #000000;
            min-width: 120px;
            font-size: 12px;
        }
        
        QPushButton#startButton:hover {
            background-color: #00ffaa;
        }
        
        QPushButton#startButton:pressed {
            background-color: #00cc66;
        }
        
        /* Browse Buttons */
        QPushButton#browseButton {
            background-color: #1a1a1a;
            border: 1px solid #00ffff;
            color: #00ffff;
            min-width: 80px;
        }
        
        QPushButton#browseButton:hover {
            background-color: #252525;
            border: 1px solid #66ffff;
            color: #66ffff;
        }
        
        /* Radio Buttons */
        QRadioButton {
            color: #e0e0e0;
            spacing: 5px;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #404040;
            border-radius: 8px;
            background-color: #1a1a1a;
        }
        
        QRadioButton::indicator:hover {
            border: 2px solid #00ff88;
        }
        
        QRadioButton::indicator:checked {
            background-color: #00ff88;
            border: 2px solid #00ff88;
        }
        
        QRadioButton::indicator:checked:hover {
            background-color: #00ffaa;
            border: 2px solid #00ffaa;
        }
        
        /* ComboBox */
        QComboBox {
            background-color: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: #e0e0e0;
            min-width: 100px;
        }
        
        QComboBox:hover {
            border: 1px solid #00ff88;
        }
        
        QComboBox:focus {
            border: 1px solid #00ffff;
            background-color: #222222;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #00ff88;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #1a1a1a;
            border: 1px solid #00ffff;
            selection-background-color: #00ffff;
            selection-color: #000000;
            color: #e0e0e0;
        }
        
        /* Scrollbars */
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
            height: 0px;
        }
        
        /* Message Boxes */
        QMessageBox {
            background-color: #121212;
        }
        
        QMessageBox QLabel {
            color: #e0e0e0;
        }
        
        QMessageBox QPushButton {
            min-width: 80px;
        }
        """
        self.setStyleSheet(theme)
    
    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("<h2 style='color: #00ffff;'>RANDOM SLIDESHOW GENERATOR</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Preset Management Section
        if self.preset_manager:
            preset_group = QGroupBox("Presets")
            preset_layout = QHBoxLayout()
            
            preset_layout.addWidget(QLabel("Preset:"))
            
            self.preset_combo = QComboBox()
            self.preset_combo.setMinimumWidth(200)
            self.update_preset_combo()
            self.preset_combo.currentTextChanged.connect(self.on_preset_selected)
            preset_layout.addWidget(self.preset_combo)
            
            self.save_preset_btn = QPushButton("SAVE")
            self.save_preset_btn.clicked.connect(self.save_preset)
            preset_layout.addWidget(self.save_preset_btn)
            
            self.save_as_btn = QPushButton("SAVE AS")
            self.save_as_btn.clicked.connect(self.save_preset_as)
            preset_layout.addWidget(self.save_as_btn)
            
            self.manage_presets_btn = QPushButton("MANAGE")
            self.manage_presets_btn.clicked.connect(self.open_preset_manager)
            preset_layout.addWidget(self.manage_presets_btn)
            
            preset_layout.addStretch()
            preset_group.setLayout(preset_layout)
            main_layout.addWidget(preset_group)
        
        # Folder Selection
        folders_group = QGroupBox("Folder Selection")
        folders_layout = QVBoxLayout()
        
        # Image folder
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("Image Folder:"))
        self.img_folder_input = QLineEdit()
        self.img_folder_input.setText(self.config_manager.get_image_folder())
        self.img_browse_btn = QPushButton("BROWSE")
        self.img_browse_btn.setObjectName("browseButton")
        self.img_browse_btn.clicked.connect(self.browse_image_folder)
        img_layout.addWidget(self.img_folder_input)
        img_layout.addWidget(self.img_browse_btn)
        folders_layout.addLayout(img_layout)
        
        # Output folder
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output Folder:"))
        self.out_folder_input = QLineEdit()
        self.out_folder_input.setText(self.config_manager.get_output_folder())
        self.out_browse_btn = QPushButton("BROWSE")
        self.out_browse_btn.setObjectName("browseButton")
        self.out_browse_btn.clicked.connect(self.browse_output_folder)
        out_layout.addWidget(self.out_folder_input)
        out_layout.addWidget(self.out_browse_btn)
        folders_layout.addLayout(out_layout)
        
        folders_group.setLayout(folders_layout)
        main_layout.addWidget(folders_group)
        
        # Aspect Ratio Selection
        aspect_group = QGroupBox("Aspect Ratio")
        aspect_layout = QHBoxLayout()
        
        self.radio_16_9 = QRadioButton("16:9 (Landscape)")
        self.radio_9_16 = QRadioButton("9:16 (Portrait)")
        
        # Set default
        if self.config_manager.get_aspect_ratio() == "16:9":
            self.radio_16_9.setChecked(True)
        else:
            self.radio_9_16.setChecked(True)
        
        aspect_layout.addWidget(self.radio_16_9)
        aspect_layout.addWidget(self.radio_9_16)
        aspect_group.setLayout(aspect_layout)
        main_layout.addWidget(aspect_group)
        
        # Status and Controls
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Ready")
        self.generation_label = QLabel("Total Generations: 0")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.generation_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Control Button
        self.toggle_button = QPushButton("START GENERATION")
        self.toggle_button.setObjectName("startButton")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_worker)
        main_layout.addWidget(self.toggle_button)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def browse_image_folder(self):
        """Browse for image folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Image Folder", 
            self.img_folder_input.text()
        )
        if folder:
            self.img_folder_input.setText(folder)
            self.config_manager.set_image_folder(folder)
    
    def browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", 
            self.out_folder_input.text()
        )
        if folder:
            self.out_folder_input.setText(folder)
            self.config_manager.set_output_folder(folder)
    
    def get_selected_aspect_ratio(self):
        """Get the selected aspect ratio."""
        if self.radio_16_9.isChecked():
            return "16:9"
        else:
            return "9:16"
    
    def toggle_worker(self):
        """Start or stop the worker thread."""
        if RandomSlideshowWorker is None:
            QMessageBox.critical(self, "Error", "Worker module not available!")
            self.toggle_button.setChecked(False)
            return
        
        if self.toggle_button.isChecked():
            # Start generation
            image_folder = self.img_folder_input.text()
            output_folder = self.out_folder_input.text()
            
            # Validate folders
            if not os.path.isdir(image_folder):
                QMessageBox.warning(self, "Error", "Image folder does not exist!")
                self.toggle_button.setChecked(False)
                return
            
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder, exist_ok=True)
            
            # Check for images
            if ImageProcessor:
                image_files = [f for f in glob.glob(os.path.join(image_folder, "*"))
                             if ImageProcessor.is_valid_image_file(f)]
                if not image_files:
                    QMessageBox.warning(self, "Error", "No valid images found!")
                    self.toggle_button.setChecked(False)
                    return
            
            # Create and start worker
            self.worker_thread = RandomSlideshowWorker(
                image_folder, output_folder, self.get_selected_aspect_ratio()
            )
            
            # Connect signals
            self.worker_thread.status_update.connect(self.update_status)
            self.worker_thread.error.connect(self.handle_error)
            self.worker_thread.generation_count_updated.connect(self.update_generation_count)
            self.worker_thread.finished.connect(self.on_worker_finished)
            
            # Start worker
            self.worker_thread.start()
            
            # Update UI
            self.toggle_button.setText("STOP GENERATION")
            self.set_controls_enabled(False)
            self.status_label.setText("Status: Starting generation...")
            
        else:
            # Stop generation
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.stop()
                self.status_label.setText("Status: Stopping...")
    
    def set_controls_enabled(self, enabled):
        """Enable/disable controls during generation."""
        self.img_folder_input.setEnabled(enabled)
        self.out_folder_input.setEnabled(enabled)
        self.img_browse_btn.setEnabled(enabled)
        self.out_browse_btn.setEnabled(enabled)
        self.radio_16_9.setEnabled(enabled)
        self.radio_9_16.setEnabled(enabled)
    
    def update_status(self, message):
        """Update status label."""
        self.status_label.setText(f"Status: {message}")
    
    def update_generation_count(self, count):
        """Update generation count."""
        self.total_generations = count
        self.generation_label.setText(f"Total Generations: {count}")
    
    def handle_error(self, error_message):
        """Handle worker error."""
        QMessageBox.critical(self, "Error", error_message)
        self.reset_ui()
    
    def on_worker_finished(self):
        """Handle worker finished."""
        self.reset_ui()
        self.worker_thread = None
    
    def reset_ui(self):
        """Reset UI after worker stops."""
        self.toggle_button.setChecked(False)
        self.toggle_button.setText("START GENERATION")
        self.set_controls_enabled(True)
        if "Error" not in self.status_label.text():
            self.status_label.setText("Status: Ready")
    
    def update_preset_combo(self):
        """Update the preset combo box with available presets."""
        if not self.preset_manager:
            return
        
        self.preset_combo.blockSignals(True)
        current_text = self.preset_combo.currentText()
        
        self.preset_combo.clear()
        self.preset_combo.addItem("-- No Preset --")
        
        presets = self.preset_manager.get_preset_names()
        for name in sorted(presets):
            self.preset_combo.addItem(name)
        
        # Restore selection
        if current_text and current_text != "-- No Preset --":
            index = self.preset_combo.findText(current_text)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)
        
        self.preset_combo.blockSignals(False)
    
    def on_preset_selected(self, preset_name):
        """Handle preset selection from combo box."""
        if preset_name == "-- No Preset --":
            self.current_preset = None
        else:
            self.load_preset(preset_name)
    
    def load_preset(self, preset_name):
        """Load a preset and apply its settings."""
        if not self.preset_manager:
            return
        
        if self.preset_manager.apply_preset_to_config(preset_name, self.config_manager):
            self.current_preset = preset_name
            
            # Update UI with preset values
            self.img_folder_input.setText(self.config_manager.get_image_folder())
            self.out_folder_input.setText(self.config_manager.get_output_folder())
            
            aspect_ratio = self.config_manager.get_aspect_ratio()
            if aspect_ratio == "16:9":
                self.radio_16_9.setChecked(True)
            else:
                self.radio_9_16.setChecked(True)
            
            QMessageBox.information(self, "Preset Loaded", f"Preset '{preset_name}' loaded successfully.")
    
    def save_preset(self):
        """Save current settings to the selected preset."""
        if not self.preset_manager:
            return
        
        if not self.current_preset or self.preset_combo.currentText() == "-- No Preset --":
            self.save_preset_as()
            return
        
        # Save current aspect ratio to config
        self.config_manager.set_aspect_ratio(self.get_selected_aspect_ratio())
        
        if self.preset_manager.create_preset_from_config(self.config_manager, self.current_preset):
            QMessageBox.information(self, "Preset Saved", f"Preset '{self.current_preset}' saved successfully.")
    
    def save_preset_as(self):
        """Save current settings as a new preset."""
        if not self.preset_manager:
            return
        
        name, ok = QInputDialog.getText(
            self, "Save Preset As",
            "Enter preset name:",
            text=self.current_preset or ""
        )
        
        if ok and name:
            # Save current aspect ratio to config
            self.config_manager.set_aspect_ratio(self.get_selected_aspect_ratio())
            
            description, ok = QInputDialog.getText(
                self, "Preset Description",
                "Enter description (optional):"
            )
            
            if self.preset_manager.create_preset_from_config(self.config_manager, name, description):
                self.current_preset = name
                self.update_preset_combo()
                self.preset_combo.setCurrentText(name)
                QMessageBox.information(self, "Preset Saved", f"Preset '{name}' saved successfully.")
    
    def open_preset_manager(self):
        """Open the preset management dialog."""
        if not self.preset_manager or not PresetDialog:
            return
        
        dialog = PresetDialog(self.preset_manager, self.current_preset, self)
        dialog.preset_selected.connect(self.load_preset)
        
        if dialog.exec_():
            self.update_preset_combo()
    
    def closeEvent(self, event):
        """Handle window close."""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Generation is in progress. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker_thread.stop()
                self.worker_thread.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = RandomSlideshowEditor()
    window.show()
    sys.exit(app.exec_())