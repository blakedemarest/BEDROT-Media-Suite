import sys
import os
import random
import math
import glob
import json
import numpy as np  # Ensure NumPy is imported
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image

# Patch PIL for compatibility (if needed)
# Check if ANTIALIAS attribute exists, if not, assign LANCZOS from Resampling
if not hasattr(Image, "ANTIALIAS"):
    # Modern PIL uses Resampling enum
    if hasattr(Image, "Resampling") and hasattr(Image.Resampling, "LANCZOS"):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    else:
        # Fallback if even Resampling is somehow missing (very unlikely)
        # You might need to install a specific Pillow version if this happens
        print("Warning: Could not find appropriate ANTIALIAS/LANCZOS resampling filter in PIL/Pillow.")
        # Assign a default or handle the error appropriately
        # For now, we'll let it potentially fail later if ANTIALIAS is strictly needed
        pass # Or assign a default like Image.BILINEAR if available


# -----------------------
# Config Utility
# -----------------------
CONFIG_FILE = "combined_random_config.json" # Use a new config file name

def load_config():
    """Loads configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file {CONFIG_FILE}. Error: {e}")
            return {}
    return {}

def save_config(config_data):
    """Saves configuration to JSON file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save config file {CONFIG_FILE}. Error: {e}")

# ------------------------------------------------
# Helper: Scale and crop an image for 9:16 (Portrait)
# (Adapted from original Script 1)
# ------------------------------------------------
def scale_and_crop_to_portrait(image_path, target_w=1632, target_h=2912):
    """
    Open the given image, scale it so the final height matches target_h,
    and then center-crop (or letterbox width) to target_w.
    Returns a PIL Image object (RGB) of size target_w x target_h.
    """
    try:
        # Open image
        with Image.open(image_path) as im:
            im = im.convert("RGB")  # Ensure 3-channel RGB
            orig_w, orig_h = im.size

            if orig_h == 0: # Avoid division by zero
                raise ValueError(f"Image has zero height: {image_path}")

            # 1) Scale so the final height matches target_h
            scale_factor = target_h / orig_h
            new_w = int(orig_w * scale_factor)
            new_h = target_h  # exactly target_h

            # Use LANCZOS for resizing (handle potential PIL version differences)
            resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
            scaled_img = im.resize((new_w, new_h), resample_filter)

            # 2) Center-crop horizontally if needed
            if new_w >= target_w:
                # Crop to target_w wide
                left = (new_w - target_w) // 2
                right = left + target_w
                final_img = scaled_img.crop((left, 0, right, new_h))
            else:
                # If the scaled width is too small, letterbox
                final_img = Image.new("RGB", (target_w, target_h), "black")
                x_offset = (target_w - new_w) // 2
                final_img.paste(scaled_img, (x_offset, 0))

            return final_img
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        # Return a black placeholder image on error
        return Image.new("RGB", (target_w, target_h), "black")


# -----------------------
# Worker Thread for Random Slideshows
# -----------------------
class RandomSlideshowWorker(QThread):
    # Signals
    status_update = pyqtSignal(str)
    error = pyqtSignal(str)
    generation_count_updated = pyqtSignal(int)

    def __init__(self, image_folder, output_folder, aspect_ratio):
        super().__init__()
        self.image_folder = image_folder
        self.output_folder = output_folder
        self.aspect_ratio = aspect_ratio # "9:16" or "16:9"
        self._is_running = True
        self.generation_count = 0

    def run(self):
        """Main loop for generating slideshow videos."""
        # Determine target dimensions based on selected aspect ratio
        if self.aspect_ratio == "9:16":
            target_width = 1632
            target_height = 2912
            processing_mode = "scale_crop"
        elif self.aspect_ratio == "16:9":
            target_width = 2912
            target_height = 1632
            processing_mode = "letterbox"
        else:
            self.error.emit(f"Invalid aspect ratio selected: {self.aspect_ratio}")
            return # Should not happen with radio buttons, but good practice

        while self._is_running:
            try:
                # 1. Randomly select total slideshow length (12.0 - 17.8 seconds)
                total_slideshow_length = random.uniform(12.0, 17.8)
                # 2. Randomly select duration per image (0.05 - 0.45 seconds)
                duration_per_image = random.uniform(0.05, 0.45)
                # 3. Calculate number of images needed
                # Avoid division by zero if duration_per_image is somehow zero
                if duration_per_image <= 0:
                    duration_per_image = 0.05
                num_images = math.ceil(total_slideshow_length / duration_per_image)
                if num_images <= 0:
                    num_images = 1 # Ensure at least one image

                # 4. Gather valid image paths
                image_paths = [
                    f for f in glob.glob(os.path.join(self.image_folder, "*"))
                    if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
                       and os.path.getsize(f) > 0 # Ensure file is not empty
                ]
                if not image_paths:
                    self.error.emit("No valid, non-empty images found in the selected image folder.")
                    self._is_running = False # Stop if no images
                    return

                # 5. Randomly select required images
                if num_images <= len(image_paths):
                    chosen_images = random.sample(image_paths, num_images)
                else:
                    # Allow replacement if more images are needed than available
                    chosen_images = [random.choice(image_paths) for _ in range(num_images)]

                # ------------------------------------------------------
                # 6. Build list of moviepy ImageClips based on aspect ratio mode
                # ------------------------------------------------------
                clips = []
                self.status_update.emit(f"Processing {len(chosen_images)} images for {self.aspect_ratio} video...")
                processed_count = 0
                for img_path in chosen_images:
                    if not self._is_running: # Check if stopped during processing
                        self.status_update.emit("Stopping...")
                        # Clean up any clips created so far in this iteration
                        for clip in clips:
                            clip.close()
                        return

                    try:
                        if processing_mode == "scale_crop":
                            # Use the scale & crop method (for 9:16)
                            final_pil = scale_and_crop_to_portrait(img_path, target_width, target_height)
                            final_array = np.array(final_pil) # Convert PIL to NumPy array
                            clip = ImageClip(final_array).set_duration(duration_per_image)
                        else: # processing_mode == "letterbox" (for 16:9)
                            # Use the letterbox/pillarbox method
                            clip = ImageClip(img_path).set_duration(duration_per_image).on_color(
                                size=(target_width, target_height),
                                color=(0, 0, 0), # Black background
                                col_opacity=1.0,
                                pos=('center', 'center')
                            )
                        clips.append(clip)
                        processed_count += 1
                        if processed_count % 10 == 0: # Update status periodically for long videos
                             self.status_update.emit(f"Processed {processed_count}/{len(chosen_images)} images...")

                    except Exception as img_e:
                        print(f"Skipping image {os.path.basename(img_path)} due to error: {img_e}")
                        # Optionally emit a non-critical warning or just log it

                if not clips:
                    self.error.emit("No images could be processed successfully.")
                    # Decide whether to stop or try again
                    continue # Try next loop iteration

                # 7. Concatenate clips
                self.status_update.emit("Concatenating clips...")
                final_clip = concatenate_videoclips(clips, method="compose")
                actual_duration = final_clip.duration

                # 8. Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                aspect_ratio_tag = self.aspect_ratio.replace(":", "x") # e.g., 9x16 or 16x9
                output_filename = f"random_slideshow_{aspect_ratio_tag}_{timestamp}.mp4"
                output_path = os.path.join(self.output_folder, output_filename)

                # 9. Write the video file
                self.status_update.emit(f"Writing video: {output_filename}...")
                # Use logger=None to reduce console output noise
                # Use threads=os.cpu_count() or a fixed number like 4 for potential speedup
                num_threads = os.cpu_count() if os.cpu_count() else 4 # Use available cores or default to 4
                final_clip.write_videofile(output_path, fps=24, logger=None, threads=num_threads)

                # Close clips to release resources (MoviePy recommendation)
                final_clip.close()
                for clip in clips:
                    clip.close()
                clips = [] # Clear the list for the next iteration

                # Update generation count and status
                self.generation_count += 1
                self.generation_count_updated.emit(self.generation_count)
                self.status_update.emit(
                    f"Created: {output_filename}\nAspect Ratio: {self.aspect_ratio} | "
                    f"Length: {actual_duration:.2f}s | "
                    f"Duration/Img: {duration_per_image:.2f}s | Images: {processed_count}" # Use processed_count here
                )

            except Exception as e:
                # Emit error and stop the current worker run
                self.error.emit(f"An error occurred during generation: {e}")
                # Clean up potentially open clips from the failed iteration
                if 'final_clip' in locals() and final_clip:
                    final_clip.close()
                for clip in clips:
                    clip.close()
                self._is_running = False # Stop worker on major error
                return # Exit run method

        # This message is shown when the loop exits gracefully (stop called)
        self.status_update.emit("Worker stopped.")

    def stop(self):
        """Signals the worker thread to stop looping."""
        self.status_update.emit("Stop requested. Finishing current task...")
        self._is_running = False

# -----------------------
# Main UI
# -----------------------
class RandomSlideshowEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Slideshow Generator")
        self.resize(550, 400) # Slightly larger for the new option
        self.config_data = load_config()
        self.total_generations = 0
        self.worker_thread = None

        # Load saved preferences or defaults
        default_image_folder = self.config_data.get("image_folder", os.getcwd())
        # Safer default output folder within user's Videos directory
        default_output_folder = self.config_data.get("output_folder", os.path.join(os.path.expanduser("~"), "Videos", "RandomSlideshows"))
        os.makedirs(default_output_folder, exist_ok=True) # Ensure default output exists
        default_aspect_ratio = self.config_data.get("aspect_ratio", "16:9") # Default to 16:9

        # Layout Setup
        main_layout = QVBoxLayout()

        # --- Folder Selection ---
        # Image Folder
        img_folder_layout = QHBoxLayout()
        img_folder_label = QLabel("Image Folder:")
        self.img_folder_input = QLineEdit()
        self.img_folder_input.setText(default_image_folder)
        # --- FIX: Store reference to the button ---
        self.img_folder_browse_button = QPushButton("Browse")
        self.img_folder_browse_button.clicked.connect(self.browse_image_folder)
        # --- END FIX ---
        img_folder_layout.addWidget(img_folder_label)
        img_folder_layout.addWidget(self.img_folder_input)
        # --- FIX: Add the referenced button ---
        img_folder_layout.addWidget(self.img_folder_browse_button)
        # --- END FIX ---
        main_layout.addLayout(img_folder_layout)

        # Output Folder
        out_folder_layout = QHBoxLayout()
        out_folder_label = QLabel("Output Folder:")
        self.out_folder_input = QLineEdit()
        self.out_folder_input.setText(default_output_folder)
        # --- FIX: Store reference to the button ---
        self.out_folder_browse_button = QPushButton("Browse")
        self.out_folder_browse_button.clicked.connect(self.browse_output_folder)
        # --- END FIX ---
        out_folder_layout.addWidget(out_folder_label)
        out_folder_layout.addWidget(self.out_folder_input)
        # --- FIX: Add the referenced button ---
        out_folder_layout.addWidget(self.out_folder_browse_button)
        # --- END FIX ---
        main_layout.addLayout(out_folder_layout)

        # --- Aspect Ratio Selection ---
        aspect_group_box = QGroupBox("Output Aspect Ratio")
        aspect_layout = QHBoxLayout()

        self.radio_16_9 = QRadioButton("16:9 (Landscape - 2912x1632)")
        self.radio_9_16 = QRadioButton("9:16 (Portrait - 1632x2912)")

        if default_aspect_ratio == "9:16":
            self.radio_9_16.setChecked(True)
        else:
            self.radio_16_9.setChecked(True) # Default to 16:9 if config is missing/invalid

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
        self.status_label.setWordWrap(True) # Allow wrapping for longer messages
        main_layout.addWidget(self.status_label)

        # Generation Count Label
        self.generation_label = QLabel("Total Generations: 0")
        self.generation_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.generation_label)

        # Start/Stop Button
        self.toggle_button = QPushButton("Start Generation")
        self.toggle_button.setCheckable(True) # Make it a toggle button
        self.toggle_button.clicked.connect(self.toggle_worker)
        main_layout.addWidget(self.toggle_button)

        self.setLayout(main_layout)

    def browse_image_folder(self):
        """Opens a dialog to select the image input folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder", self.img_folder_input.text())
        if folder:
            self.img_folder_input.setText(folder)
            self.config_data["image_folder"] = folder
            save_config(self.config_data)

    def browse_output_folder(self):
        """Opens a dialog to select the video output folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.out_folder_input.text())
        if folder:
            self.out_folder_input.setText(folder)
            self.config_data["output_folder"] = folder
            save_config(self.config_data)
        elif not os.path.isdir(self.out_folder_input.text()):
            # If user cancelled and current path is invalid, try creating it or default
             try:
                 os.makedirs(self.out_folder_input.text(), exist_ok=True)
                 self.config_data["output_folder"] = self.out_folder_input.text()
                 save_config(self.config_data)
             except Exception as e:
                 print(f"Error creating specified output folder: {e}")
                 fallback_folder = os.path.join(os.path.expanduser("~"), "Videos", "RandomSlideshows")
                 os.makedirs(fallback_folder, exist_ok=True)
                 self.out_folder_input.setText(fallback_folder)
                 QMessageBox.information(self, "Output Folder Created", f"Output folder created at: {fallback_folder}")
                 self.config_data["output_folder"] = fallback_folder
                 save_config(self.config_data)

    def save_aspect_ratio_preference(self):
        """Saves the selected aspect ratio when a radio button is toggled."""
        # This signal fires for both the unchecked and checked button,
        # so we only save when the sender (the button itself) becomes checked.
        sender = self.sender()
        if sender and sender.isChecked(): # Add check if sender exists
             if sender == self.radio_16_9:
                 self.config_data["aspect_ratio"] = "16:9"
             elif sender == self.radio_9_16:
                 self.config_data["aspect_ratio"] = "9:16"
             save_config(self.config_data)


    def get_selected_aspect_ratio(self):
        """Returns the string '16:9' or '9:16' based on radio button selection."""
        if self.radio_16_9.isChecked():
            return "16:9"
        else: # Assumes 9:16 is checked if 16:9 is not
            return "9:16"

    def toggle_worker(self):
        """Starts or stops the background worker thread."""
        if self.toggle_button.isChecked(): # User wants to start
             # --- Pre-flight checks ---
            image_folder = self.img_folder_input.text()
            output_folder = self.out_folder_input.text()

            if not os.path.isdir(image_folder):
                QMessageBox.warning(self, "Error", "The selected Image Folder does not exist or is not a directory.")
                self.toggle_button.setChecked(False) # Untoggle the button
                return
            if not os.path.isdir(output_folder):
                 reply = QMessageBox.question(self, "Create Folder?",
                                              f"The Output Folder '{output_folder}' does not exist.\nDo you want to create it?",
                                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                 if reply == QMessageBox.Yes:
                     try:
                         os.makedirs(output_folder, exist_ok=True)
                         self.config_data["output_folder"] = output_folder # Save if created
                         save_config(self.config_data)
                     except Exception as e:
                         QMessageBox.critical(self, "Error", f"Could not create output folder: {e}")
                         self.toggle_button.setChecked(False)
                         return
                 else:
                     self.toggle_button.setChecked(False)
                     return


            # Check for images in the input folder before starting
            image_files = [f for f in glob.glob(os.path.join(image_folder, "*"))
                           if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
                           and os.path.getsize(f) > 0]
            if not image_files:
                 QMessageBox.warning(self, "Warning", "No valid, non-empty image files (.png, .jpg, .jpeg, .bmp, .gif) were found in the selected image folder.")
                 self.toggle_button.setChecked(False)
                 return

            # --- Start the worker ---
            self.toggle_button.setText("Stop Generation")
            self.set_controls_enabled(False) # Disable controls while running
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
            self.worker_thread.finished.connect(self.on_worker_finished) # Signal when thread actually stops
            self.worker_thread.start()

        else: # User wants to stop
            if self.worker_thread and self.worker_thread.isRunning():
                self.toggle_button.setText("Stopping...")
                self.toggle_button.setEnabled(False) # Disable button until worker fully stops
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
        # --- FIX: Use direct references to buttons ---
        self.img_folder_browse_button.setEnabled(enabled)
        self.out_folder_browse_button.setEnabled(enabled)
        # --- END FIX ---


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
        self.status_label.setText(f"Status: Error occurred. Stopped. ({error_message[:50]}...)") # Show part of error
        # Ensure UI resets even if thread errors out
        if self.worker_thread and self.worker_thread.isRunning():
             self.worker_thread.stop() # Try to signal stop if still running
        # Reset UI immediately on error, potentially before 'finished' signal
        self.reset_ui_after_stop()


    def on_worker_finished(self):
        """Called when the worker thread has completely finished execution."""
        # This ensures UI resets cleanly after stop or normal completion
        self.reset_ui_after_stop()
        self.worker_thread = None # Clear the thread reference


    def reset_ui_after_stop(self):
         """Resets the UI elements to the 'idle' state."""
         self.toggle_button.setChecked(False) # Ensure button is untoggled
         self.toggle_button.setText("Start Generation")
         self.toggle_button.setEnabled(True) # Re-enable button
         self.set_controls_enabled(True) # Re-enable other controls
         # Check current status - don't overwrite error message if that was the last state
         if "Error" not in self.status_label.text():
             self.status_label.setText("Status: Idle")


    def closeEvent(self, event):
        """Ensure worker thread is stopped when closing the window."""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirm Exit',
                                         "Slideshow generation is in progress. Stop and exit?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                 self.worker_thread.stop()
                 self.worker_thread.wait(5000) # Wait up to 5 seconds for thread to finish gracefully
                 event.accept()
            else:
                 event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Set a style (optional, makes it look a bit more modern)
    # app.setStyle("Fusion")
    editor = RandomSlideshowEditor()
    editor.show()
    sys.exit(app.exec_())
