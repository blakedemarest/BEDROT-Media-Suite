# -*- coding: utf-8 -*-
"""
Batch Slideshow Worker for Random Slideshow Generator.

This module provides a worker adapted for batch job processing that generates
slideshows based on job configuration.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

import os
import random
import math
import glob
import numpy as np
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from moviepy.editor import ImageClip, concatenate_videoclips

from models import SlideshowJob, JobStatus
from job_queue import JobQueue
from image_processor import ImageProcessor
from resource_manager import get_resource_manager


class BatchSlideshowWorker(QObject):
    """Worker adapted for batch job processing of slideshow generation."""
    
    # Signals
    progress_updated = pyqtSignal(float)  # Overall job progress (0-100)
    video_completed = pyqtSignal(str)  # Path to generated video
    status_message = pyqtSignal(str)  # Status message
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, job: SlideshowJob, job_queue: JobQueue):
        """
        Initialize the batch slideshow worker.
        
        Args:
            job: The slideshow job to process
            job_queue: Reference to the job queue for progress updates
        """
        super().__init__()
        self.job = job
        self.job_queue = job_queue
        self._is_running = True
        
        # Determine target dimensions based on aspect ratio
        try:
            self.target_width, self.target_height, self.processing_mode = \
                ImageProcessor.get_target_dimensions(job.aspect_ratio)
        except ValueError as e:
            self.error_occurred.emit(str(e))
            self.target_width = 1920
            self.target_height = 1080
            self.processing_mode = "letterbox"
    
    def run(self) -> bool:
        """
        Execute the slideshow generation job.
        
        Returns:
            True if job completed successfully, False otherwise
        """
        try:
            # Validate job configuration
            if not self._validate_job():
                return False
            
            # Generate the requested number of videos
            for video_index in range(self.job.num_videos):
                # Add small delay between videos to prevent CPU overload
                if video_index > 0:
                    import time
                    time.sleep(0.1)  # 100ms delay between videos
                    
                if not self._is_running:
                    self.status_message.emit("Job cancelled")
                    return False
                
                # Check if job was cancelled
                current_job = self.job_queue.get_job(self.job.id)
                if current_job and current_job.status == JobStatus.CANCELLED:
                    self.status_message.emit("Job cancelled")
                    return False
                
                # Update current video being processed
                self.job_queue.update_job_progress(
                    self.job.id, 0.0, 
                    f"Video {video_index + 1} of {self.job.num_videos}"
                )
                
                # Generate single slideshow
                success = self._generate_single_slideshow(video_index + 1)
                
                if not success:
                    self.error_occurred.emit(
                        f"Failed to generate video {video_index + 1}"
                    )
                    return False
                
                # Update job progress
                overall_progress = ((video_index + 1) / self.job.num_videos) * 100
                self.progress_updated.emit(overall_progress)
            
            self.status_message.emit(
                f"Successfully generated {self.job.num_videos} videos"
            )
            return True
            
        except Exception as e:
            error_msg = f"Job failed: {str(e)}"
            self.error_occurred.emit(error_msg)
            print(f"Error in batch slideshow worker: {e}")
            return False
    
    def stop(self):
        """Stop the worker."""
        self._is_running = False
    
    def _validate_job(self) -> bool:
        """
        Validate job configuration.
        
        Returns:
            True if job is valid, False otherwise
        """
        # Validate job parameters
        if self.job.num_videos <= 0:
            self.error_occurred.emit("Number of videos must be greater than 0")
            return False
        
        if self.job.duration_range[0] > self.job.duration_range[1]:
            self.error_occurred.emit("Invalid duration range: minimum > maximum")
            return False
        
        if self.job.image_duration_range[0] > self.job.image_duration_range[1]:
            self.error_occurred.emit("Invalid image duration range: minimum > maximum")
            return False
        
        # Check image folder exists
        if not os.path.exists(self.job.image_folder):
            self.error_occurred.emit(f"Image folder not found: {self.job.image_folder}")
            return False
        
        # Check output folder exists or create it
        if not os.path.exists(self.job.output_folder):
            try:
                os.makedirs(self.job.output_folder, exist_ok=True)
            except PermissionError:
                self.error_occurred.emit(f"Permission denied creating output folder: {self.job.output_folder}")
                return False
            except OSError as e:
                self.error_occurred.emit(f"Cannot create output folder: {e}")
                return False
        
        # Check write permission on output folder
        try:
            test_file = os.path.join(self.job.output_folder, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            self.error_occurred.emit(f"Cannot write to output folder: {e}")
            return False
        
        # Check for valid images
        image_paths = self._get_valid_images()
        if not image_paths:
            self.error_occurred.emit("No valid images found in the selected folder")
            return False
        
        return True
    
    def _get_valid_images(self) -> list:
        """
        Get list of valid image paths from the job's image folder.
        
        Returns:
            List of valid image file paths
        """
        image_paths = [
            f for f in glob.glob(os.path.join(self.job.image_folder, "*"))
            if ImageProcessor.is_valid_image_file(f)
        ]
        return image_paths
    
    def _generate_single_slideshow(self, video_number: int) -> bool:
        """
        Generate a single slideshow video.
        
        Args:
            video_number: The video number (1-based)
            
        Returns:
            True if successful, False otherwise
        """
        # Initialize resources outside try block for proper cleanup
        clips = []
        final_clip = None
        
        try:
            # 1. Randomly select total slideshow length from job's duration range
            total_slideshow_length = random.uniform(*self.job.duration_range)
            
            # 2. Randomly select duration per image from job's range
            duration_per_image = random.uniform(*self.job.image_duration_range)
            
            # Ensure valid values
            if duration_per_image <= 0:
                duration_per_image = 0.05
            
            # 3. Calculate number of images needed
            num_images = math.ceil(total_slideshow_length / duration_per_image)
            if num_images <= 0:
                num_images = 1
            
            # 4. Get valid image paths
            image_paths = self._get_valid_images()
            if not image_paths:
                return False
            
            # 5. Randomly select required images
            if num_images <= len(image_paths):
                chosen_images = random.sample(image_paths, num_images)
            else:
                # Allow replacement if more images are needed than available
                chosen_images = [random.choice(image_paths) for _ in range(num_images)]
            
            # 6. Build list of moviepy ImageClips
            clips = []  # Ensure clips is reset for this video
            processed_count = 0
            
            for i, img_path in enumerate(chosen_images):
                if not self._is_running:
                    # Clean up clips if cancelled
                    for clip in clips:
                        clip.close()
                    return False
                
                try:
                    # Process image based on aspect ratio mode
                    if self.processing_mode == "scale_crop":
                        # Process image
                        final_pil = ImageProcessor.scale_and_crop_to_portrait(
                            img_path, self.target_width, self.target_height
                        )
                        
                        # Cache the result for future use
                        try:
                            resource_manager = get_resource_manager()
                            if resource_manager.image_cache:
                                resource_manager.image_cache.put(img_path, final_pil)
                        except:
                            pass  # Ignore cache errors
                        
                        final_array = np.array(final_pil)
                        clip = ImageClip(final_array).set_duration(duration_per_image).set_fps(self.job.fps)
                    else:  # processing_mode == "letterbox" (for 16:9)
                        # Use the letterbox/pillarbox method
                        clip = ImageClip(img_path).set_duration(duration_per_image).set_fps(self.job.fps).on_color(
                            size=(self.target_width, self.target_height),
                            color=(0, 0, 0),  # Black background
                            col_opacity=1.0,
                            pos=('center', 'center')
                        )
                    
                    clips.append(clip)
                    processed_count += 1
                    
                    # Update progress for current video
                    video_progress = (processed_count / len(chosen_images)) * 100
                    self.job_queue.update_job_progress(self.job.id, video_progress)
                    
                except Exception as img_e:
                    print(f"Skipping image {os.path.basename(img_path)} due to error: {img_e}")
                    # Continue with other images
            
            if not clips:
                self.error_occurred.emit("No images could be processed successfully")
                return False
            
            # 7. Concatenate clips
            self.status_message.emit("Concatenating clips...")
            final_clip = concatenate_videoclips(clips, method="compose")
            actual_duration = final_clip.duration
            
            # Check if we should stop before writing
            if not self._is_running:
                # Clean up and return
                if final_clip:
                    final_clip.close()
                for clip in clips:
                    clip.close()
                return False
            
            # 8. Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            aspect_ratio_tag = self.job.aspect_ratio.replace(":", "x")
            
            # Include job name in filename if provided
            if self.job.name:
                safe_name = "".join(c for c in self.job.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
                output_filename = f"{safe_name}_{aspect_ratio_tag}_{video_number:03d}_{timestamp}.mp4"
            else:
                output_filename = f"slideshow_{aspect_ratio_tag}_{video_number:03d}_{timestamp}.mp4"
            
            output_path = os.path.join(self.job.output_folder, output_filename)
            
            # 9. Write the video file
            self.status_message.emit(f"Writing video {video_number}/{self.job.num_videos}: {output_filename}")
            
            # Determine quality settings
            if self.job.video_quality == "low":
                bitrate = "1M"
            elif self.job.video_quality == "medium":
                bitrate = "5M"
            else:  # high
                bitrate = "10M"
            
            # Use multiple threads for encoding
            num_threads = os.cpu_count() if os.cpu_count() else 4
            
            # Write video with specified quality
            final_clip.write_videofile(
                output_path, 
                fps=self.job.fps, 
                bitrate=bitrate,
                logger=None,  # Suppress moviepy output
                threads=num_threads
            )
            
            # Close clips to release resources
            if final_clip:
                final_clip.close()
                final_clip = None
            
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass  # Ignore errors during cleanup
            
            clips = []  # Clear the list
            
            # Force garbage collection to free memory
            import gc
            gc.collect()
            
            # Update job with generated file
            self.job_queue.increment_videos_completed(self.job.id, output_path)
            self.video_completed.emit(output_path)
            
            self.status_message.emit(
                f"Created video {video_number}: {output_filename} "
                f"(Length: {actual_duration:.2f}s, Images: {processed_count})"
            )
            
            return True
            
        except Exception as e:
            print(f"Error generating slideshow: {e}")
            self.error_occurred.emit(f"Error generating video {video_number}: {str(e)}")
            
            # Clean up any open clips
            try:
                if final_clip:
                    final_clip.close()
                    final_clip = None
            except:
                pass
                
            try:
                for clip in clips:
                    clip.close()
            except:
                pass
                
            clips = []  # Reset clips list
            
            # Force garbage collection
            import gc
            gc.collect()
            
            return False