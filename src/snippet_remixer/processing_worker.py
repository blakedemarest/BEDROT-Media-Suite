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
import time
from .video_processor import VideoProcessor
from .utils import safe_print, generate_unique_suffix
from .logging_config import get_logger, setup_logging, log_processing_summary


class ProcessingWorker:
    """
    Worker class for handling video processing in a separate thread.
    """
    
    def __init__(self, script_dir, video_filter=None):
        self.script_dir = script_dir
        self.logger = get_logger("processing_worker")
        self.video_filter = video_filter
        self.video_processor = VideoProcessor(script_dir, video_filter)
        self.processing_active = False
        self.abort_requested = False
        self.thread = None

    @staticmethod
    def build_linear_modulation_schedule(start_bpm, end_bpm, total_duration_sec, unit_beats, min_duration=0.1):
        """
        Build a list of snippet durations that linearly ramp BPM over the clip.
        
        Args:
            start_bpm (float): Starting BPM
            end_bpm (float): Ending BPM
            total_duration_sec (float): Target clip duration in seconds
            unit_beats (float): Number of beats per snippet unit
            min_duration (float): Minimum snippet duration safeguard
            
        Returns:
            list: Durations for each snippet in seconds
        """
        if total_duration_sec <= 0 or unit_beats <= 0 or start_bpm <= 0 or end_bpm <= 0:
            return []
        
        schedule = []
        elapsed = 0.0
        total_duration_sec = float(total_duration_sec)
        max_iterations = 20000  # Prevent runaway in extreme settings
        
        while elapsed < total_duration_sec - 1e-6 and len(schedule) < max_iterations:
            progress = elapsed / total_duration_sec if total_duration_sec > 0 else 0.0
            current_bpm = start_bpm + (end_bpm - start_bpm) * progress
            current_bpm = max(current_bpm, 0.001)
            
            seconds_per_beat = 60.0 / current_bpm
            snippet_duration = max(min_duration, seconds_per_beat * unit_beats)
            
            # Clamp final snippet to end exactly at target duration
            if elapsed + snippet_duration > total_duration_sec:
                snippet_duration = total_duration_sec - elapsed
            
            if snippet_duration <= 0:
                break
            
            schedule.append(snippet_duration)
            elapsed += snippet_duration
        
        if elapsed < total_duration_sec and len(schedule) < max_iterations:
            # Pad final micro-portion if floating point left a tiny remainder
            remainder = total_duration_sec - elapsed
            if remainder > 1e-6:
                schedule.append(remainder)
        
        return schedule

    @staticmethod
    def build_graph_modulation_schedule(points, unit_beats, min_duration=0.1):
        """
        Build a snippet schedule from an arbitrary tempo automation curve.
        
        Args:
            points (list): List of dicts with 'time' and 'bpm'
            unit_beats (float): Beats per snippet unit
            min_duration (float): Minimum snippet duration
            
        Returns:
            list: Durations for each snippet
        """
        if not points or len(points) < 2 or unit_beats <= 0:
            return []
        # Sanitize and sort
        sanitized = []
        for p in points:
            try:
                t = float(p.get("time", 0.0))
                bpm_val = float(p.get("bpm", 0.0))
            except (TypeError, ValueError):
                continue
            if t < 0 or bpm_val <= 0:
                continue
            sanitized.append({"time": t, "bpm": bpm_val})
        if len(sanitized) < 2:
            return []
        sanitized.sort(key=lambda x: x["time"])
        end_time = sanitized[-1]["time"]
        if end_time <= 0:
            return []

        def interp_bpm(t):
            # Find segment containing t
            for i in range(len(sanitized) - 1):
                p1 = sanitized[i]
                p2 = sanitized[i + 1]
                if t <= p2["time"]:
                    span = max(1e-6, p2["time"] - p1["time"])
                    alpha = max(0.0, min(1.0, (t - p1["time"]) / span))
                    return p1["bpm"] + (p2["bpm"] - p1["bpm"]) * alpha
            return sanitized[-1]["bpm"]

        schedule = []
        elapsed = 0.0
        max_iter = 20000
        while elapsed < end_time - 1e-6 and len(schedule) < max_iter:
            bpm_val = interp_bpm(elapsed)
            bpm_val = max(0.001, bpm_val)
            seconds_per_beat = 60.0 / bpm_val
            snippet_duration = max(min_duration, seconds_per_beat * unit_beats)
            if elapsed + snippet_duration > end_time:
                snippet_duration = end_time - elapsed
            if snippet_duration <= 0:
                break
            schedule.append(snippet_duration)
            elapsed += snippet_duration

        if elapsed < end_time and len(schedule) < max_iter:
            remainder = end_time - elapsed
            if remainder > 1e-6:
                schedule.append(remainder)
        return schedule
    
    def calculate_durations(self, length_mode, settings):
        """
        Calculate target duration and snippet duration based on settings.
        
        Args:
            length_mode (str): "Seconds" or "BPM"
            settings (dict): Settings containing duration/BPM parameters
            
        Returns:
            tuple: (target_total_duration_sec, snippet_duration_spec)
                   snippet_duration_spec is either a float (fixed) or a list (variable)
        """
        tempo_mod_enabled = settings.get("tempo_mod_enabled", False) and length_mode == "BPM"
        
        if length_mode == "Seconds":
            target_total_duration_sec = float(settings["duration_seconds"])
            if target_total_duration_sec <= 0:
                raise ValueError("Duration (s) must be positive.")
            snippet_duration_spec = max(0.1, target_total_duration_sec / 30.0)
            if snippet_duration_spec <= 0:
                raise ValueError("Calculated snippet duration invalid.")
                
        elif length_mode == "BPM":
            # Import BPM_UNITS from config_manager
            from .config_manager import BPM_UNITS
            
            if tempo_mod_enabled:
                start_bpm = float(settings.get("tempo_mod_start_bpm", settings.get("bpm", 0)))
                end_bpm = float(settings.get("tempo_mod_end_bpm", start_bpm))
                clip_duration = float(settings.get("tempo_mod_duration_seconds", settings.get("duration_seconds", 0)))
                bpm_unit_name = settings.get("bpm_unit")
                
                if start_bpm <= 0 or end_bpm <= 0:
                    raise ValueError("Tempo modulation BPM values must be positive.")
                if clip_duration <= 0:
                    raise ValueError("Tempo modulation duration must be positive.")
                if bpm_unit_name not in BPM_UNITS:
                    raise ValueError("Invalid BPM unit.")
                
                unit_beats = BPM_UNITS[bpm_unit_name]
                mod_points = settings.get("tempo_mod_points")
                snippet_schedule = []
                if mod_points:
                    snippet_schedule = self.build_graph_modulation_schedule(mod_points, unit_beats)
                if not snippet_schedule:
                    snippet_schedule = self.build_linear_modulation_schedule(
                        start_bpm, end_bpm, clip_duration, unit_beats
                    )
                if not snippet_schedule:
                    raise ValueError("Tempo modulation produced no snippet schedule.")
                
                target_total_duration_sec = sum(snippet_schedule)
                snippet_duration_spec = snippet_schedule
            else:
                bpm = float(settings["bpm"])
                num_units = int(settings["num_units"])
                bpm_unit_name = settings["bpm_unit"]
                
                if bpm <= 0:
                    raise ValueError("BPM must be positive.")
                if num_units <= 0:
                    raise ValueError("Units must be positive.")
                if bpm_unit_name not in BPM_UNITS:
                    raise ValueError("Invalid BPM unit.")
                    
                seconds_per_beat = 60.0 / bpm
                snippet_duration_spec = seconds_per_beat * BPM_UNITS[bpm_unit_name]
                target_total_duration_sec = snippet_duration_spec * num_units
                
                if snippet_duration_spec <= 0:
                    raise ValueError("Calculated snippet duration invalid.")
        else:
            raise ValueError("Invalid length mode selected.")
            
        if target_total_duration_sec <= 0:
            raise ValueError("Calculated total duration is invalid.")
            
        return target_total_duration_sec, snippet_duration_spec
    
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
                      snippet_duration_spec, aspect_ratio_selection, 
                      export_settings=None,
                      progress_callback=None, error_callback=None, 
                      completion_callback=None):
        """
        Main video processing method.
        
        Args:
            input_files (list): List of input video file paths
            final_output_path (str): Path for final output file
            target_total_duration_sec (float): Target total duration
            snippet_duration_spec (float or list): Fixed snippet duration or per-snippet schedule
            aspect_ratio_selection (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Progress update callback
            error_callback (callable): Error callback
            completion_callback (callable): Completion callback
        """
        processing_failed = False
        start_time = time.time()
        
        self.logger.info("="*80)
        self.logger.info("Starting video processing")
        self.logger.info(f"Input files: {len(input_files)}")
        self.logger.info(f"Output path: {final_output_path}")
        self.logger.info(f"Target duration: {target_total_duration_sec:.2f}s")
        self.logger.info(f"Aspect ratio: {aspect_ratio_selection}")
        self.logger.info("="*80)
        
        # Determine snippet characteristics (fixed or modulated)
        if isinstance(snippet_duration_spec, (list, tuple)):
            if len(snippet_duration_spec) == 0:
                raise ValueError("Snippet schedule is empty.")
            max_snippet_duration = max(snippet_duration_spec)
            avg_snippet_duration = sum(snippet_duration_spec) / len(snippet_duration_spec)
            snippet_count_estimate = len(snippet_duration_spec)
            self.logger.info(f"Snippet schedule: {snippet_count_estimate} segments "
                             f"(avg {avg_snippet_duration:.2f}s, max {max_snippet_duration:.2f}s)")
        else:
            max_snippet_duration = snippet_duration_spec
            snippet_count_estimate = math.ceil(target_total_duration_sec / snippet_duration_spec)
            self.logger.info(f"Snippet duration: {snippet_duration_spec:.2f}s "
                             f"(~{snippet_count_estimate} segments)")

        # Pre-compute jitter impact so file validation uses worst case duration
        jitter_settings = None
        jitter_multiplier = 1.0
        if export_settings:
            jitter_settings = {
                "jitter_enabled": export_settings.get("jitter_enabled", False),
                "jitter_intensity": export_settings.get("jitter_intensity", 50)
            }
            if jitter_settings["jitter_enabled"]:
                jitter_multiplier += (jitter_settings["jitter_intensity"] / 100.0) * 0.5
        max_snippet_duration *= jitter_multiplier
        
        try:
            # Check tools availability
            ffmpeg_found, ffprobe_found = self.video_processor.are_tools_available()
            if not ffmpeg_found or not ffprobe_found:
                self.logger.error("FFmpeg/FFprobe not found in system PATH")
                raise Exception("FFmpeg/FFprobe not found")
            
            # Stage 1: Analyze Durations
            if self.abort_requested:
                raise Exception("Processing aborted by user")
                
            if progress_callback:
                progress_callback("Analyzing input video durations...")
                
            valid_inputs, files_too_short = self.video_processor.analyze_video_durations(
                input_files, max_snippet_duration, progress_callback
            )
            
            if files_too_short and error_callback:
                error_callback("warning", "Files Skipped", 
                             f"Skipped files (duration < {max_snippet_duration:.2f}s):\\n" + 
                             "\\n".join(files_too_short))
            
            if not valid_inputs:
                self.logger.error(f"No valid input videos found with duration >= {max_snippet_duration:.2f}s")
                raise Exception("No valid input videos found or none are long enough.")
            
            # Stage 2: Generate Snippet List
            if self.abort_requested:
                raise Exception("Processing aborted by user")
                
            if progress_callback:
                progress_callback("Generating random snippet list...")
            
            snippet_definitions = self.video_processor.generate_snippet_definitions(
                valid_inputs, target_total_duration_sec, snippet_duration_spec, jitter_settings
            )
            
            # Stage 3: Create Temp Dir & Cut Snippets
            if self.abort_requested:
                raise Exception("Processing aborted by user")
                
            if not self.video_processor.prepare_temp_directory():
                raise Exception("Temp dir creation failed.")
            
            # Get aspect ratio mode from export_settings
            aspect_ratio_mode = export_settings.get("aspect_ratio_mode", "crop") if export_settings else "crop"
            
            snippet_files = self.video_processor.cut_video_snippets(
                snippet_definitions, aspect_ratio_selection, export_settings, progress_callback, aspect_ratio_mode
            )
            
            if not snippet_files:
                raise Exception("No snippets were successfully cut.")
            
            # Stage 4: Concatenate Snippets
            if self.abort_requested:
                raise Exception("Processing aborted by user")
                
            temp_concat_path = self.video_processor.concatenate_snippets(
                snippet_files, progress_callback
            )
            
            # Stage 5: Aspect Ratio Adjustment and Final Output
            if self.abort_requested:
                raise Exception("Processing aborted by user")
                
            success = self.video_processor.adjust_aspect_ratio(
                temp_concat_path, final_output_path, aspect_ratio_selection, export_settings, progress_callback, aspect_ratio_mode
            )
            
            if not success:
                raise Exception("Aspect ratio adjustment failed")
            
            # Stage 6: Verify Output Dimensions
            if os.path.exists(final_output_path):
                # Calculate expected dimensions based on aspect ratio
                expected_width, expected_height = self.video_processor.calculate_intermediate_resolution(
                    aspect_ratio_selection, export_settings
                )
                
                # Verify dimensions and optionally check for black bars
                check_black_bars = export_settings.get("check_black_bars", False) if export_settings else False
                actual_width, actual_height, has_black_bars = self.video_processor.verify_output_dimensions(
                    final_output_path, expected_width, expected_height, check_black_bars
                )
                
                if has_black_bars:
                    self.logger.warning("Black bars detected in final output!")
                    safe_print(f"Warning: Black bars detected in final output!")
                    if error_callback:
                        error_callback("warning", "Black Bars Detected", 
                                     "The output video contains black bars. This may indicate an issue with aspect ratio processing.")
            
            # Calculate processing time and log summary
            elapsed_time = time.time() - start_time
            
            # Get final video info for summary
            final_width, final_height, final_duration = self.video_processor.get_video_info(final_output_path)
            if final_width and final_height and final_duration:
                log_processing_summary(
                    self.logger,
                    len(input_files),
                    final_output_path,
                    final_duration,
                    elapsed_time
                )
            
            # Final success message
            if progress_callback:
                progress_callback(f"Success! Remix saved: {os.path.basename(final_output_path)}")
                
        except Exception as e:
            self.logger.error(f"Processing failed: {e}", exc_info=True)
            safe_print(f"Processing stopped due to error: {e}")
            processing_failed = True
            
            if error_callback:
                error_callback("error", "Processing Error", str(e))
            
            # Clean up potentially failed final output file
            if processing_failed and os.path.exists(final_output_path):
                try:
                    os.remove(final_output_path)
                    self.logger.info(f"Cleaned up failed output file: {final_output_path}")
                    safe_print(f"Cleaned up potentially failed final output file: {final_output_path}")
                except OSError as e:
                    self.logger.warning(f"Could not delete failed output file: {e}")
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
                               snippet_duration_spec, aspect_ratio_selection,
                               export_settings=None,
                               progress_callback=None, error_callback=None, 
                               completion_callback=None):
        """
        Start processing in a separate thread.
        
        Args:
            input_files (list): List of input video file paths
            final_output_path (str): Path for final output file
            target_total_duration_sec (float): Target total duration
            snippet_duration_spec (float or list): Duration per snippet (fixed) or schedule (list)
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
        self.abort_requested = False  # Reset abort flag
        self.video_processor.abort_requested = False  # Reset video processor's abort flag
        
        self.thread = threading.Thread(
            target=self.process_videos,
            args=(input_files, final_output_path, target_total_duration_sec, 
                  snippet_duration_spec, aspect_ratio_selection),
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
    
    def abort_processing(self):
        """
        Request abort of current processing operation.
        """
        if self.processing_active:
            self.logger.info("Abort requested by user")
            self.abort_requested = True
            # Also signal the video processor to abort if it has subprocesses running
            if hasattr(self.video_processor, 'abort_processing'):
                self.video_processor.abort_processing()
    
    def get_video_processor(self):
        """
        Get the underlying video processor instance.
        
        Returns:
            VideoProcessor: The video processor instance
        """
        return self.video_processor
