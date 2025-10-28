# -*- coding: utf-8 -*-
"""
Slideshow Worker Module for Random Slideshow Generator.

Provides functionality for:
- Background slideshow generation threading
- Video processing and concatenation
- Progress reporting and error handling
"""

import os
import random
import math
import glob
import numpy as np
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from moviepy.editor import ImageClip, concatenate_videoclips

from image_processor import ImageProcessor

# Handle both relative and absolute imports for ClipManager
try:
    from ..core.moviepy_utils import ClipManager, safe_close_clip
except (ImportError, ValueError):
    # Fallback for when module is run directly or imported locally
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.moviepy_utils import ClipManager, safe_close_clip


class RandomSlideshowWorker(QThread):
    """
    Worker thread for generating random slideshow videos.
    """
    
    # Signals
    status_update = pyqtSignal(str)
    error = pyqtSignal(str)
    generation_count_updated = pyqtSignal(int)

    def __init__(self, image_folder, output_folder, aspect_ratio):
        super().__init__()
        self.image_folder = image_folder
        self.output_folder = output_folder
        self.aspect_ratio = aspect_ratio  # "9:16" or "16:9"
        self._is_running = True
        self.generation_count = 0

    def run(self):
        """Main loop for generating slideshow videos."""
        try:
            # Determine target dimensions based on selected aspect ratio
            target_width, target_height, processing_mode = ImageProcessor.get_target_dimensions(self.aspect_ratio)
        except ValueError as e:
            self.error.emit(str(e))
            return

        while self._is_running:
            # Use ClipManager for automatic resource cleanup
            with ClipManager() as clip_manager:
                try:
                    # Add small delay between generations to prevent CPU overload
                    if self.generation_count > 0:
                        self.msleep(100)  # 100ms delay between videos
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
                        num_images = 1  # Ensure at least one image

                    # 4. Gather valid image paths
                    image_paths = [
                        f for f in glob.glob(os.path.join(self.image_folder, "*"))
                        if ImageProcessor.is_valid_image_file(f)
                    ]
                    if not image_paths:
                        self.error.emit("No valid, non-empty images found in the selected image folder.")
                        self._is_running = False  # Stop if no images
                        return

                    # 5. Randomly select required images
                    if num_images <= len(image_paths):
                        chosen_images = random.sample(image_paths, num_images)
                    else:
                        # Allow replacement if more images are needed than available
                        chosen_images = [random.choice(image_paths) for _ in range(num_images)]

                    # 6. Build list of moviepy ImageClips based on aspect ratio mode
                    clips = []  # List to track clips for concatenation
                    self.status_update.emit(f"Processing {len(chosen_images)} images for {self.aspect_ratio} video...")
                    processed_count = 0
                    
                    for img_path in chosen_images:
                        if not self._is_running:  # Check if stopped during processing
                            self.status_update.emit("Stopping...")
                            return  # ClipManager will handle cleanup automatically

                        try:
                            if processing_mode == "scale_crop":
                                # Use the scale & crop method (for 9:16)
                                final_pil = ImageProcessor.scale_and_crop_to_portrait(
                                    img_path, target_width, target_height
                                )
                                final_array = np.array(final_pil)  # Convert PIL to NumPy array
                                clip = clip_manager.add(
                                    ImageClip(final_array).set_duration(duration_per_image).set_fps(30)
                                )
                            else:  # processing_mode == "letterbox" (for 16:9)
                                # Use the letterbox/pillarbox method
                                clip = clip_manager.add(
                                    ImageClip(img_path).set_duration(duration_per_image).set_fps(30).on_color(
                                        size=(target_width, target_height),
                                        color=(0, 0, 0),  # Black background
                                        col_opacity=1.0,
                                        pos=('center', 'center')
                                    )
                                )
                            clips.append(clip)
                            processed_count += 1
                            if processed_count % 10 == 0:  # Update status periodically for long videos
                                self.status_update.emit(f"Processed {processed_count}/{len(chosen_images)} images...")

                        except Exception as img_e:
                            print(f"Skipping image {os.path.basename(img_path)} due to error: {img_e}")
                            # Optionally emit a non-critical warning or just log it

                    if not clips:
                        self.error.emit("No images could be processed successfully.")
                        # Decide whether to stop or try again
                        continue  # Try next loop iteration

                    # 7. Concatenate clips
                    self.status_update.emit("Concatenating clips...")
                    final_clip = clip_manager.add(concatenate_videoclips(clips, method="compose"))
                    actual_duration = final_clip.duration
                    
                    # Check if we should stop before writing
                    if not self._is_running:
                        self.status_update.emit("Stopping...")
                        return  # ClipManager will handle cleanup

                    # 8. Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    aspect_ratio_tag = self.aspect_ratio.replace(":", "x")  # e.g., 9x16 or 16x9
                    output_filename = f"random_slideshow_{aspect_ratio_tag}_{timestamp}.mp4"
                    output_path = os.path.join(self.output_folder, output_filename)

                    # 9. Write the video file
                    self.status_update.emit(f"Writing video: {output_filename}...")
                    # Use logger=None to reduce console output noise
                    # Use threads=os.cpu_count() or a fixed number like 4 for potential speedup
                    num_threads = os.cpu_count() if os.cpu_count() else 4  # Use available cores or default to 4
                    final_clip.write_videofile(output_path, fps=30, logger=None, threads=num_threads)

                    # Update generation count and status
                    self.generation_count += 1
                    self.generation_count_updated.emit(self.generation_count)
                    self.status_update.emit(
                        f"Created: {output_filename}\nAspect Ratio: {self.aspect_ratio} | "
                        f"Length: {actual_duration:.2f}s | "
                        f"Duration/Img: {duration_per_image:.2f}s | Images: {processed_count}"
                    )

                except Exception as e:
                    # Emit error and stop the current worker run
                    self.error.emit(f"An error occurred during generation: {e}")
                    self._is_running = False  # Stop worker on major error
                    return  # Exit run method
                # ClipManager automatically handles cleanup when exiting the with block

        # This message is shown when the loop exits gracefully (stop called)
        self.status_update.emit("Worker stopped.")

    def stop(self):
        """Signals the worker thread to stop looping."""
        self.status_update.emit("Stop requested. Finishing current task...")
        self._is_running = False