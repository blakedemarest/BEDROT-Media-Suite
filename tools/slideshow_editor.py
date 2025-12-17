import sys
import os
import random
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QHBoxLayout,
    QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image

# Patch PIL to support ANTIALIAS if missing (newer Pillow uses Resampling.LANCZOS)
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# ------------------------------------------------------------
# Config Utility
# ------------------------------------------------------------
CONFIG_FILE = "config.json"

def load_config():
    """Load config from a local JSON file if it exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config_data):
    """Save config to a local JSON file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)

# ------------------------------------------------------------
# Thread Worker
# ------------------------------------------------------------
class SlideshowWorker(QThread):
    # Define custom signals to communicate with the UI
    progress_updated = pyqtSignal(int)
    completed = pyqtSignal(str)    # Will emit the output path if successful
    error = pyqtSignal(str)

    def __init__(self, image_files, duration, ratio, output_folder):
        super().__init__()
        self.image_files = image_files
        self.duration = duration
        self.ratio = ratio
        self.output_folder = output_folder

    def run(self):
        try:
            # Shuffle images randomly
            random.shuffle(self.image_files)

            # Determine target aspect ratio
            target_width = 1080  # e.g., 1080 for base width
            target_height = int(target_width * self.ratio[1] / self.ratio[0])

            clips = []
            total_images = len(self.image_files)
            for idx, img_path in enumerate(self.image_files):
                clip = ImageClip(img_path).set_duration(self.duration)

                # 1) Determine the image's aspect ratio
                image_ratio = clip.w / clip.h
                target_ratio = target_width / target_height

                # 2) Uniformly scale the clip so it fits within the target size
                #    without cropping (letterbox/pillarbox).
                if image_ratio > target_ratio:
                    # Image is "wider" => limit by width
                    clip = clip.resize(width=target_width)
                else:
                    # Image is "taller" => limit by height
                    clip = clip.resize(height=target_height)

                # 3) Place the scaled clip on a black background
                #    so final size is exactly (target_width x target_height).
                clip = clip.on_color(
                    size=(target_width, target_height),
                    color=(0, 0, 0),  # black background
                    col_opacity=1.0,
                    pos=('center', 'center')
                )

                clips.append(clip)
                # Update progress (first ~50% dedicated to reading/resizing images)
                progress_percent = int(((idx + 1) / total_images) * 50)
                self.progress_updated.emit(progress_percent)

            # Concatenate all image clips into one video
            final_clip = concatenate_videoclips(clips, method="compose")

            # Check output folder
            if not os.path.isdir(self.output_folder):
                raise Exception("The output folder does not exist.")

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"slideshow_video_{timestamp}.mp4"
            output_path = os.path.join(self.output_folder, output_filename)

            # Write the video
            final_clip.write_videofile(output_path, fps=30, logger=None)
            self.progress_updated.emit(100)

            self.completed.emit(output_path)

        except Exception as e:
            self.error.emit(str(e))

# ------------------------------------------------------------
# Main GUI
# ------------------------------------------------------------
class DragDropWidget(QLabel):
    def __init__(self, parent=None):
        super(DragDropWidget, self).__init__(parent)
        self.setText("Drag and drop images here")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QLabel { border: 2px dashed #aaa; padding: 20px; }")
        self.setAcceptDrops(True)
        self.image_paths = []

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                filepath = str(url.toLocalFile())
                if os.path.splitext(filepath)[1].lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                    self.image_paths.append(filepath)
        self.setText(f"{len(self.image_paths)} images loaded")

    def clear_images(self):
        self.image_paths.clear()
        self.setText("Drag and drop images here")


class SlideshowEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slideshow Editor")
        self.resize(450, 450)
        self.config_data = load_config()  # Load any saved config

        main_layout = QVBoxLayout()

        # Drag and drop area for images
        self.dragDropWidget = DragDropWidget()
        main_layout.addWidget(self.dragDropWidget)

        # Button row: Clear images
        btn_row_layout = QHBoxLayout()
        self.clearButton = QPushButton("Clear Images")
        self.clearButton.clicked.connect(self.clear_images)
        btn_row_layout.addWidget(self.clearButton)
        main_layout.addLayout(btn_row_layout)

        # Input for duration (macro)
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Enter duration per image (in seconds)")
        main_layout.addWidget(self.duration_input)

        # Dropdown for aspect ratio options
        self.aspect_ratio_combo = QComboBox()
        self.aspect_ratio_combo.addItem("9:16 (Vertical)", (9, 16))
        self.aspect_ratio_combo.addItem("1:1", (1, 1))
        self.aspect_ratio_combo.addItem("16:19", (16, 19))
        self.aspect_ratio_combo.addItem("4:3", (4, 3))
        main_layout.addWidget(self.aspect_ratio_combo)

        # Output folder selection
        folder_layout = QHBoxLayout()
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Output folder")
        # Default to last used folder or current directory
        default_folder = self.config_data.get("output_folder", os.getcwd())
        self.output_folder_input.setText(default_folder)
        folder_layout.addWidget(self.output_folder_input)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_button)
        main_layout.addLayout(folder_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Button to create slideshow
        self.createButton = QPushButton("Create Slideshow")
        self.createButton.clicked.connect(self.create_slideshow)
        main_layout.addWidget(self.createButton)

        self.setLayout(main_layout)

        # Worker thread placeholder
        self.worker_thread = None

    def clear_images(self):
        """Clear all loaded images."""
        self.dragDropWidget.clear_images()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_folder_input.text())
        if folder:
            self.output_folder_input.setText(folder)
            # Update config immediately
            self.config_data["output_folder"] = folder
            save_config(self.config_data)

    def create_slideshow(self):
        # Validate duration input
        try:
            duration = float(self.duration_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid number for duration.")
            return

        if not self.dragDropWidget.image_paths:
            QMessageBox.warning(self, "No Images", "Please drag and drop some images.")
            return

        # Get ratio
        ratio = self.aspect_ratio_combo.currentData()
        # Output folder
        output_folder = self.output_folder_input.text()

        # Update config with the latest folder
        self.config_data["output_folder"] = output_folder
        save_config(self.config_data)

        # Reset progress bar
        self.progress_bar.setValue(0)

        # Disable UI elements while processing
        self.createButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.duration_input.setEnabled(False)
        self.aspect_ratio_combo.setEnabled(False)

        # Start a worker thread to handle video creation
        self.worker_thread = SlideshowWorker(
            image_files=self.dragDropWidget.image_paths.copy(),
            duration=duration,
            ratio=ratio,
            output_folder=output_folder
        )
        self.worker_thread.progress_updated.connect(self.on_progress_updated)
        self.worker_thread.completed.connect(self.on_completed)
        self.worker_thread.error.connect(self.on_error)
        self.worker_thread.start()

    def on_progress_updated(self, value):
        self.progress_bar.setValue(value)

    def on_completed(self, output_path):
        self.reset_ui()
        QMessageBox.information(self, "Success", f"Slideshow created successfully at:\n{output_path}")

    def on_error(self, error_msg):
        self.reset_ui()
        QMessageBox.critical(self, "Error", f"An error occurred while creating the video:\n{error_msg}")

    def reset_ui(self):
        """Re-enable UI elements after the worker finishes or errors out."""
        self.progress_bar.setValue(0)
        self.createButton.setEnabled(True)
        self.clearButton.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.duration_input.setEnabled(True)
        self.aspect_ratio_combo.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = SlideshowEditor()
    editor.show()
    sys.exit(app.exec_())
