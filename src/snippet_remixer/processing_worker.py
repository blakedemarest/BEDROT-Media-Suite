# -*- coding: utf-8 -*-
"""
Processing Worker Thread for Video Snippet Remixer.

Handles background video processing operations including:
- Video analysis and validation
- Snippet cutting and concatenation
- Aspect ratio adjustment
- Progress reporting and error handling
"""

import threading
import os
import math
from .video_processor import VideoProcessor
from .utils import safe_print, generate_unique_suffix


class ProcessingWorker:
    """
    Worker class for handling video processing in a separate thread.
    """
    
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.video_processor = VideoProcessor(script_dir)
        self.processing_active = False
        self.thread = None
    
    def calculate_durations(self, length_mode, settings):
        """
        Calculate target duration and snippet duration based on settings.
        
        Args:
            length_mode (str): "Seconds" or "BPM"
            settings (dict): Settings containing duration/BPM parameters
            
        Returns:
            tuple: (target_total_duration_sec, snippet_duration_sec)
        """
        if length_mode == "Seconds":
            target_total_duration_sec = float(settings["duration_seconds"])
            if target_total_duration_sec <= 0:
                raise ValueError("Duration (s) must be positive.")
            snippet_duration_sec = max(0.1, target_total_duration_sec / 30.0)
            if snippet_duration_sec <= 0:
                raise ValueError("Calculated snippet duration invalid.")
                
        elif length_mode == "BPM":
            bpm = float(settings["bpm"])
            num_units = int(settings["num_units"])
            bpm_unit_name = settings["bpm_unit"]
            
            if bpm <= 0:
                raise ValueError("BPM must be positive.")
            if num_units <= 0:
                raise ValueError("Units must be positive.")
                
            # Import BPM_UNITS from config_manager
            from .config_manager import BPM_UNITS
            if bpm_unit_name not in BPM_UNITS:
                raise ValueError("Invalid BPM unit.")
                
            seconds_per_beat = 60.0 / bpm
            snippet_duration_sec = seconds_per_beat * BPM_UNITS[bpm_unit_name]
            target_total_duration_sec = snippet_duration_sec * num_units
            
            if snippet_duration_sec <= 0:
                raise ValueError("Calculated snippet duration invalid.")
        else:
            raise ValueError("Invalid length mode selected.")
            
        if target_total_duration_sec <= 0:
            raise ValueError("Calculated total duration is invalid.")
            
        return target_total_duration_sec, snippet_duration_sec
    
    def generate_output_filename(self, aspect_ratio_selection, output_folder):
        """
        Generate unique output filename.
        
        Args:
            aspect_ratio_selection (str): Selected aspect ratio
            output_folder (str): Output directory path
            
        Returns:
            str: Full path to output file
        """
        unique_suffix = generate_unique_suffix()
        ar_tag = ""
        if aspect_ratio_selection != "Original":
            ar_tag = f"_AR_{aspect_ratio_selection.replace(':', 'x').replace('.', '_')}"
        
        final_extension = ".mp4"
        output_filename_generated = f"remix{ar_tag}{unique_suffix}{final_extension}"
        return os.path.join(output_folder, output_filename_generated)
    
    def process_videos(self, input_files, final_output_path, target_total_duration_sec, 
                      snippet_duration_sec, aspect_ratio_selection, 
                      export_settings=None,
                      progress_callback=None, error_callback=None, 
                      completion_callback=None):
        """
        Main video processing method.
        
        Args:
            input_files (list): List of input video file paths
            final_output_path (str): Path for final output file
            target_total_duration_sec (float): Target total duration
            snippet_duration_sec (float): Duration per snippet
            aspect_ratio_selection (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Progress update callback
            error_callback (callable): Error callback
            completion_callback (callable): Completion callback
        """
        processing_failed = False
        
        try:
            # Check tools availability
            ffmpeg_found, ffprobe_found = self.video_processor.are_tools_available()
            if not ffmpeg_found or not ffprobe_found:
                raise Exception("FFmpeg/FFprobe not found")
            
            # Stage 1: Analyze Durations
            if progress_callback:
                progress_callback("Analyzing input video durations...")
                
            valid_inputs, files_too_short = self.video_processor.analyze_video_durations(
                input_files, snippet_duration_sec, progress_callback
            )
            
            if files_too_short and error_callback:
                error_callback("warning", "Files Skipped", 
                             f"Skipped files (duration < {snippet_duration_sec:.2f}s):\\n" + 
                             "\\n".join(files_too_short))
            
            if not valid_inputs:
                raise Exception("No valid input videos found or none are long enough.")
            
            # Stage 2: Generate Snippet List
            if progress_callback:
                progress_callback("Generating random snippet list...")
            
            # Extract jitter settings from export_settings
            jitter_settings = None
            if export_settings:
                jitter_settings = {
                    "jitter_enabled": export_settings.get("jitter_enabled", False),
                    "jitter_intensity": export_settings.get("jitter_intensity", 50)
                }
                
            snippet_definitions = self.video_processor.generate_snippet_definitions(
                valid_inputs, target_total_duration_sec, snippet_duration_sec, jitter_settings
            )
            
            # Stage 3: Create Temp Dir & Cut Snippets
            if not self.video_processor.prepare_temp_directory():
                raise Exception("Temp dir creation failed.")
            
            snippet_files = self.video_processor.cut_video_snippets(
                snippet_definitions, aspect_ratio_selection, export_settings, progress_callback
            )
            
            if not snippet_files:
                raise Exception("No snippets were successfully cut.")
            
            # Stage 4: Concatenate Snippets
            temp_concat_path = self.video_processor.concatenate_snippets(
                snippet_files, progress_callback
            )
            
            # Stage 5: Aspect Ratio Adjustment and Final Output
            success = self.video_processor.adjust_aspect_ratio(
                temp_concat_path, final_output_path, aspect_ratio_selection, export_settings, progress_callback
            )
            
            if not success:
                raise Exception("Aspect ratio adjustment failed")
            
            # Final success message
            if progress_callback:
                progress_callback(f"Success! Remix saved: {os.path.basename(final_output_path)}")
                
        except Exception as e:
            safe_print(f"Processing stopped due to error: {e}")
            processing_failed = True
            
            if error_callback:
                error_callback("error", "Processing Error", str(e))
            
            # Clean up potentially failed final output file
            if processing_failed and os.path.exists(final_output_path):
                try:
                    os.remove(final_output_path)
                    safe_print(f"Cleaned up potentially failed final output file: {final_output_path}")
                except OSError as e:
                    safe_print(f"Warning: Could not delete potentially failed final output file: {e}")
        
        finally:
            # Cleanup
            status_before_cleanup = "Processing completed"
            if progress_callback:
                if processing_failed:
                    progress_callback(status_before_cleanup + " | Attempting cleanup...")
                else:
                    progress_callback(status_before_cleanup + " | Cleaning up...")
            
            cleanup_success = self.video_processor.cleanup_temp_directory()
            
            if progress_callback:
                if not processing_failed and cleanup_success:
                    progress_callback(f"Saved: {os.path.basename(final_output_path)} | Cleanup done.")
                elif not cleanup_success:
                    progress_callback(status_before_cleanup + " | Cleanup failed (check console).")
                else:
                    progress_callback(status_before_cleanup + " | No temp files to clean.")
            
            self.processing_active = False
            
            if completion_callback:
                completion_callback(not processing_failed, final_output_path)
    
    def start_processing_thread(self, input_files, final_output_path, target_total_duration_sec,
                               snippet_duration_sec, aspect_ratio_selection,
                               export_settings=None,
                               progress_callback=None, error_callback=None, 
                               completion_callback=None):
        """
        Start processing in a separate thread.
        
        Args:
            input_files (list): List of input video file paths
            final_output_path (str): Path for final output file
            target_total_duration_sec (float): Target total duration
            snippet_duration_sec (float): Duration per snippet
            aspect_ratio_selection (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Progress update callback
            error_callback (callable): Error callback
            completion_callback (callable): Completion callback
        """
        if self.processing_active:
            if error_callback:
                error_callback("warning", "Busy", "Processing is already in progress.")
            return
        
        self.processing_active = True
        
        self.thread = threading.Thread(
            target=self.process_videos,
            args=(input_files, final_output_path, target_total_duration_sec, 
                  snippet_duration_sec, aspect_ratio_selection),
            kwargs={
                'export_settings': export_settings,
                'progress_callback': progress_callback,
                'error_callback': error_callback,
                'completion_callback': completion_callback
            },
            daemon=True
        )
        self.thread.start()
    
    def is_processing(self):
        """
        Check if processing is currently active.
        
        Returns:
            bool: True if processing is active
        """
        return self.processing_active
    
    def get_video_processor(self):
        """
        Get the underlying video processor instance.
        
        Returns:
            VideoProcessor: The video processor instance
        """
        return self.video_processor