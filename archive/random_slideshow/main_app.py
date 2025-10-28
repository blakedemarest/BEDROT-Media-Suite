# -*- coding: utf-8 -*-
"""
Main Application Module for Random Slideshow Generator.

This module contains the main application window and GUI functionality for:
- Folder selection and configuration
- Aspect ratio selection
- Worker thread management
- Status display and controls
"""

import os
import glob
import subprocess
import platform
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox,
    QTabWidget
)
from PyQt5.QtCore import Qt

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

# Use relative imports within the module with error handling
import_errors = []

try:
    from config_manager import ConfigManager
except ImportError as e:
    import_errors.append(f"ConfigManager: {e}")
    ConfigManager = None

try:
    from slideshow_worker import RandomSlideshowWorker
except ImportError as e:
    import_errors.append(f"RandomSlideshowWorker: {e}")
    RandomSlideshowWorker = None

try:
    from image_processor import ImageProcessor
except ImportError as e:
    import_errors.append(f"ImageProcessor: {e}")
    ImageProcessor = None

try:
    from batch_manager_widget import BatchManagerWidget
except ImportError as e:
    import_errors.append(f"BatchManagerWidget: {e}")
    BatchManagerWidget = None

if import_errors:
    print("Import errors detected:")
    for error in import_errors:
        print(f"  - {error}")


class RandomSlideshowEditor(QWidget):
    """
    Main application window for the Random Slideshow Generator.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Slideshow Generator")
        self.resize(700, 500)  # Larger for tab widget
        
        # Flag to track initialization errors
        self.initialization_error = None
        
        # Check for critical imports
        if import_errors and ConfigManager is None:
            self.initialization_error = "Critical modules could not be imported. Please install dependencies."
            self.setup_error_ui()
            return
        
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager()
            self.total_generations = 0
            self.worker_thread = None

            # Load saved preferences or defaults
            default_image_folder = self.config_manager.get_image_folder()
            default_output_folder = self.config_manager.get_output_folder()
            # Ensure default output exists
            os.makedirs(default_output_folder, exist_ok=True)
            default_aspect_ratio = self.config_manager.get_aspect_ratio()

            # Setup main UI with tabs
            self.setup_main_ui(default_image_folder, default_output_folder, default_aspect_ratio)
            
        except Exception as e:
            print(f"Error during RandomSlideshowEditor initialization: {e}")
            import traceback
            traceback.print_exc()
            self.initialization_error = str(e)
            self.setup_error_ui()

    def setup_main_ui(self, default_image_folder, default_output_folder, default_aspect_ratio):
        """Setup the main UI with tab widget."""
        main_layout = QVBoxLayout()
        
        try:
            # Create tab widget
            self.tab_widget = QTabWidget()
            
            # Create single generation tab
            self.single_gen_widget = QWidget()
            self.setup_single_generation_tab(self.single_gen_widget, default_image_folder, 
                                           default_output_folder, default_aspect_ratio)
            self.tab_widget.addTab(self.single_gen_widget, "Single Generation")
            
            # Create batch processing tab with error handling
            try:
                self.batch_widget = BatchManagerWidget(self.config_manager)
                self.tab_widget.addTab(self.batch_widget, "Batch Processing")
            except Exception as e:
                print(f"Error creating batch processing tab: {e}")
                import traceback
                traceback.print_exc()
                # Create error tab instead
                error_widget = QWidget()
                error_layout = QVBoxLayout()
                error_label = QLabel(f"<h3>Batch Processing Error</h3>\n<p>Failed to initialize batch processing: {e}</p>")
                error_label.setWordWrap(True)
                error_layout.addWidget(error_label)
                error_widget.setLayout(error_layout)
                self.tab_widget.addTab(error_widget, "Batch Processing (Error)")
            
            main_layout.addWidget(self.tab_widget)
            self.setLayout(main_layout)
            
        except Exception as e:
            print(f"Critical error setting up main UI: {e}")
            import traceback
            traceback.print_exc()
            # Create minimal error UI
            error_label = QLabel(f"<h2>Initialization Error</h2>\n<p>{e}</p>\n<p>Please check the console for details.</p>")
            error_label.setWordWrap(True)
            error_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(error_label)
            self.setLayout(main_layout)
    
    def setup_error_ui(self):
        """Setup an error UI when initialization fails."""
        layout = QVBoxLayout()
        
        # Error message
        error_label = QLabel(f"<h2>Random Slideshow Generator - Initialization Error</h2>")
        error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_label)
        
        # Detailed error
        details_label = QLabel(f"<p><b>Error:</b> {self.initialization_error}</p>")
        details_label.setWordWrap(True)
        layout.addWidget(details_label)
        
        # Import errors if any
        if import_errors:
            import_label = QLabel("<p><b>Import Errors:</b></p>")
            layout.addWidget(import_label)
            for error in import_errors:
                error_item = QLabel(f"  • {error}")
                error_item.setWordWrap(True)
                layout.addWidget(error_item)
        
        # Instructions
        instructions = QLabel(
            "<p><b>To fix this issue:</b></p>"
            "<p>1. Make sure all dependencies are installed:</p>"
            "<pre>   pip install -r requirements.txt</pre>"
            "<p>2. Check that FFmpeg is installed and in your PATH</p>"
            "<p>3. Restart the application</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def setup_single_generation_tab(self, parent_widget, default_image_folder, 
                                   default_output_folder, default_aspect_ratio):
        """Setup the single generation tab interface."""
        # Layout Setup
        main_layout = QVBoxLayout()

        # --- Folder Selection ---
        # Image Folder
        img_folder_layout = QHBoxLayout()
        img_folder_label = QLabel("Image Folder:")
        self.img_folder_input = QLineEdit()
        self.img_folder_input.setText(default_image_folder)
        self.img_folder_browse_button = QPushButton("Browse")
        self.img_folder_browse_button.clicked.connect(self.browse_image_folder)
        self.img_folder_open_button = QPushButton("📁 Open")
        self.img_folder_open_button.clicked.connect(self.open_image_folder)
        self.img_folder_open_button.setToolTip("Open image folder in file explorer")
        img_folder_layout.addWidget(img_folder_label)
        img_folder_layout.addWidget(self.img_folder_input)
        img_folder_layout.addWidget(self.img_folder_browse_button)
        img_folder_layout.addWidget(self.img_folder_open_button)
        main_layout.addLayout(img_folder_layout)

        # Output Folder
        out_folder_layout = QHBoxLayout()
        out_folder_label = QLabel("Output Folder:")
        self.out_folder_input = QLineEdit()
        self.out_folder_input.setText(default_output_folder)
        self.out_folder_browse_button = QPushButton("Browse")
        self.out_folder_browse_button.clicked.connect(self.browse_output_folder)
        self.out_folder_open_button = QPushButton("📁 Open")
        self.out_folder_open_button.clicked.connect(self.open_output_folder)
        self.out_folder_open_button.setToolTip("Open output folder in file explorer")
        out_folder_layout.addWidget(out_folder_label)
        out_folder_layout.addWidget(self.out_folder_input)
        out_folder_layout.addWidget(self.out_folder_browse_button)
        out_folder_layout.addWidget(self.out_folder_open_button)
        main_layout.addLayout(out_folder_layout)

        # --- Aspect Ratio Selection ---
        aspect_group_box = QGroupBox("Output Aspect Ratio")
        aspect_layout = QHBoxLayout()

        self.radio_16_9 = QRadioButton("16:9 (Landscape - 2912x1632)")
        self.radio_9_16 = QRadioButton("9:16 (Portrait - 1632x2912)")

        if default_aspect_ratio == "9:16":
            self.radio_9_16.setChecked(True)
        else:
            self.radio_16_9.setChecked(True)  # Default to 16:9 if config is missing/invalid

        aspect_layout.addWidget(self.radio_16_9)
        aspect_layout.addWidget(self.radio_9_16)
        aspect_group_box.setLayout(aspect_layout)
        main_layout.addWidget(aspect_group_box)

        # Connect signals for saving preference
        self.radio_16_9.toggled.connect(self.save_aspect_ratio_preference)
        self.radio_9_16.toggled.connect(self.save_aspect_ratio_preference)

        # --- Status and Controls ---
        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)  # Allow wrapping for longer messages
        main_layout.addWidget(self.status_label)

        # Generation Count Label
        self.generation_label = QLabel("Total Generations: 0")
        self.generation_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.generation_label)

        # Start/Stop Button
        self.toggle_button = QPushButton("Start Generation")
        self.toggle_button.setCheckable(True)  # Make it a toggle button
        self.toggle_button.clicked.connect(self.toggle_worker)
        main_layout.addWidget(self.toggle_button)

        parent_widget.setLayout(main_layout)

    def browse_image_folder(self):
        """Opens a dialog to select the image input folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder", self.img_folder_input.text())
        if folder:
            self.img_folder_input.setText(folder)
            self.config_manager.set_image_folder(folder)

    def browse_output_folder(self):
        """Opens a dialog to select the video output folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.out_folder_input.text())
        if folder:
            self.out_folder_input.setText(folder)
            self.config_manager.set_output_folder(folder)
        elif not os.path.isdir(self.out_folder_input.text()):
            # If user cancelled and current path is invalid, try creating it or default
            try:
                os.makedirs(self.out_folder_input.text(), exist_ok=True)
                self.config_manager.set_output_folder(self.out_folder_input.text())
            except Exception as e:
                print(f"Error creating specified output folder: {e}")
                fallback_folder = os.path.join(os.path.expanduser("~"), "Videos", "RandomSlideshows")
                os.makedirs(fallback_folder, exist_ok=True)
                self.out_folder_input.setText(fallback_folder)
                QMessageBox.information(self, "Output Folder Created", f"Output folder created at: {fallback_folder}")
                self.config_manager.set_output_folder(fallback_folder)

    def save_aspect_ratio_preference(self):
        """Saves the selected aspect ratio when a radio button is toggled."""
        # This signal fires for both the unchecked and checked button,
        # so we only save when the sender (the button itself) becomes checked.
        sender = self.sender()
        if sender and sender.isChecked():  # Add check if sender exists
            if sender == self.radio_16_9:
                self.config_manager.set_aspect_ratio("16:9")
            elif sender == self.radio_9_16:
                self.config_manager.set_aspect_ratio("9:16")

    def get_selected_aspect_ratio(self):
        """Returns the string '16:9' or '9:16' based on radio button selection."""
        if self.radio_16_9.isChecked():
            return "16:9"
        else:  # Assumes 9:16 is checked if 16:9 is not
            return "9:16"

    def open_image_folder(self):
        """Opens the image folder in the system file explorer."""
        folder_path = self.img_folder_input.text()
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Error", f"Image folder does not exist:\n{folder_path}")
            return
        
        try:
            self._open_folder_in_explorer(folder_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open image folder:\n{str(e)}")

    def open_output_folder(self):
        """Opens the output folder in the system file explorer."""
        folder_path = self.out_folder_input.text()
        if not os.path.isdir(folder_path):
            # Try to create the folder if it doesn't exist
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.config_manager.set_output_folder(folder_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Output folder does not exist and could not be created:\n{folder_path}\n\nError: {str(e)}")
                return
        
        try:
            self._open_folder_in_explorer(folder_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open output folder:\n{str(e)}")

    def _open_folder_in_explorer(self, folder_path):
        """Opens a folder in the system file explorer (cross-platform)."""
        system = platform.system()
        
        # Normalize the path to handle different path separators
        normalized_path = os.path.normpath(folder_path)
        
        if system == "Windows":
            # Windows - use os.startfile() which is more reliable for opening folders
            try:
                os.startfile(normalized_path)
            except (OSError, AttributeError):
                # Fallback to explorer command if os.startfile() fails
                windows_path = normalized_path.replace('/', '\\')
                subprocess.run(f'explorer "{windows_path}"', shell=True, check=True)
        elif system == "Darwin":
            # macOS Finder
            subprocess.run(["open", normalized_path], check=True)
        elif system == "Linux":
            # Linux file manager (try common ones)
            try:
                subprocess.run(["xdg-open", normalized_path], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to common Linux file managers
                for file_manager in ["nautilus", "thunar", "dolphin", "pcmanfm"]:
                    try:
                        subprocess.run([file_manager, normalized_path], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    raise Exception("No suitable file manager found on Linux system")
        else:
            raise Exception(f"Unsupported operating system: {system}")

    def toggle_worker(self):
        """Starts or stops the background worker thread."""
        # Check if worker is available
        if RandomSlideshowWorker is None:
            QMessageBox.critical(self, "Import Error", 
                               "Cannot start slideshow generation.\n\n"
                               "The RandomSlideshowWorker module could not be imported.\n"
                               "Please check that all dependencies are installed.")
            self.toggle_button.setChecked(False)
            return
            
        if self.toggle_button.isChecked():  # User wants to start
            # --- Pre-flight checks ---
            image_folder = self.img_folder_input.text()
            output_folder = self.out_folder_input.text()

            if not os.path.isdir(image_folder):
                QMessageBox.warning(self, "Error", "The selected Image Folder does not exist or is not a directory.")
                self.toggle_button.setChecked(False)  # Untoggle the button
                return
                
            if not os.path.isdir(output_folder):
                reply = QMessageBox.question(self, "Create Folder?",
                                           f"The Output Folder '{output_folder}' does not exist.\nDo you want to create it?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    try:
                        os.makedirs(output_folder, exist_ok=True)
                        self.config_manager.set_output_folder(output_folder)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Could not create output folder: {e}")
                        self.toggle_button.setChecked(False)
                        return
                else:
                    self.toggle_button.setChecked(False)
                    return

            # Check for images in the input folder before starting
            image_files = [f for f in glob.glob(os.path.join(image_folder, "*"))
                          if ImageProcessor.is_valid_image_file(f)]
            if not image_files:
                QMessageBox.warning(self, "Warning", "No valid, non-empty image files (.png, .jpg, .jpeg, .bmp, .gif) were found in the selected image folder.")
                self.toggle_button.setChecked(False)
                return

            # --- Start the worker ---
            self.toggle_button.setText("Stop Generation")
            self.set_controls_enabled(False)  # Disable controls while running
            self.status_label.setText("Status: Starting...")
            selected_aspect_ratio = self.get_selected_aspect_ratio()

            # Reset generation count for this run
            self.total_generations = 0
            self.generation_label.setText("Total Generations: 0")

            self.worker_thread = RandomSlideshowWorker(image_folder, output_folder, selected_aspect_ratio)
            # Connect signals
            self.worker_thread.status_update.connect(self.update_status)
            self.worker_thread.error.connect(self.handle_error)
            self.worker_thread.generation_count_updated.connect(self.update_generation_count)
            self.worker_thread.finished.connect(self.on_worker_finished)  # Signal when thread actually stops
            self.worker_thread.start()

        else:  # User wants to stop
            if self.worker_thread and self.worker_thread.isRunning():
                self.toggle_button.setText("Stopping...")
                self.toggle_button.setEnabled(False)  # Disable button until worker fully stops
                self.worker_thread.stop()
            else:
                # If worker wasn't running or already stopped, just reset button state
                self.reset_ui_after_stop()

    def set_controls_enabled(self, enabled):
        """Enable/disable input fields, radio buttons, and browse buttons."""
        self.img_folder_input.setEnabled(enabled)
        self.out_folder_input.setEnabled(enabled)
        self.radio_16_9.setEnabled(enabled)
        self.radio_9_16.setEnabled(enabled)
        self.img_folder_browse_button.setEnabled(enabled)
        self.out_folder_browse_button.setEnabled(enabled)

    def update_status(self, message):
        """Updates the status label."""
        self.status_label.setText(f"Status: {message}")

    def update_generation_count(self, count):
        """Updates the generation count label."""
        self.total_generations = count
        self.generation_label.setText(f"Total Generations: {self.total_generations}")

    def handle_error(self, error_message):
        """Displays an error message and resets the UI."""
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText(f"Status: Error occurred. Stopped. ({error_message[:50]}...)")  # Show part of error
        # Ensure UI resets even if thread errors out
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()  # Try to signal stop if still running
        # Reset UI immediately on error, potentially before 'finished' signal
        self.reset_ui_after_stop()

    def on_worker_finished(self):
        """Called when the worker thread has completely finished execution."""
        # Disconnect signals before clearing thread reference
        if self.worker_thread:
            try:
                self.worker_thread.status_update.disconnect()
                self.worker_thread.error.disconnect()
                self.worker_thread.generation_count_updated.disconnect()
                self.worker_thread.finished.disconnect()
            except:
                pass  # Ignore errors if signals already disconnected
        
        # This ensures UI resets cleanly after stop or normal completion
        self.reset_ui_after_stop()
        self.worker_thread = None  # Clear the thread reference

    def reset_ui_after_stop(self):
        """Resets the UI elements to the 'idle' state."""
        self.toggle_button.setChecked(False)  # Ensure button is untoggled
        self.toggle_button.setText("Start Generation")
        self.toggle_button.setEnabled(True)  # Re-enable button
        self.set_controls_enabled(True)  # Re-enable other controls
        # Check current status - don't overwrite error message if that was the last state
        if "Error" not in self.status_label.text():
            self.status_label.setText("Status: Idle")

    def closeEvent(self, event):
        """Ensure worker threads are stopped when closing the window."""
        try:
            # Check single generation worker
            if self.worker_thread and self.worker_thread.isRunning():
                reply = QMessageBox.question(self, 'Confirm Exit',
                                           "Slideshow generation is in progress. Stop and exit?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.worker_thread.stop()
                    self.worker_thread.wait(5000)  # Wait up to 5 seconds for thread to finish gracefully
                    if self.worker_thread.isRunning():
                        # Force terminate if still running
                        self.worker_thread.terminate()
                        self.worker_thread.wait(1000)
                else:
                    event.ignore()
                    return
            
            # Check batch processing
            if hasattr(self, 'batch_widget') and self.batch_widget:
                try:
                    active_workers = self.batch_widget.processor.get_active_worker_count()
                    if active_workers > 0:
                        reply = QMessageBox.question(self, 'Confirm Exit',
                                                   f"Batch processing is active ({active_workers} jobs running). Stop and exit?",
                                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            self.batch_widget.processor.stop(wait=True)
                        else:
                            event.ignore()
                            return
                except Exception as e:
                    print(f"Error checking batch processing status: {e}")
                    # Continue with shutdown even if we can't check batch status
            
            # Clean up resource manager
            try:
                from resource_manager import get_resource_manager
                resource_manager = get_resource_manager()
                resource_manager.cleanup()
            except:
                pass  # Ignore cleanup errors
                
            event.accept()
            
        except Exception as e:
            print(f"Error during closeEvent: {e}")
            # Force close on error to prevent hanging
            event.accept()