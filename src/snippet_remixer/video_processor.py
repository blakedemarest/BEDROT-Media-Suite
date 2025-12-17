# -*- coding: utf-8 -*-
"""
Video Processing Core for Video Snippet Remixer.

Handles core video processing functionality including:
- FFmpeg tool detection and validation
- Video information extraction (dimensions, duration)
- Video snippet cutting and concatenation
- Aspect ratio adjustment
- File management and cleanup
"""

import os
import subprocess
import math
import random
import shutil
import time
import logging
from .utils import safe_print, parse_aspect_ratio
from .logging_config import get_logger, log_ffmpeg_command, log_video_info, LoggingContext

# Constants
DEFAULT_INTERMEDIATE_FPS = "30"
INTERMEDIATE_EXTENSION = ".ts"
TEMP_CONCAT_FILENAME = "_temp_concat.mp4"
TEMP_DIR_NAME = "remixer_temp_snippets"

# Supported image extensions for static image-to-video conversion
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'}

# HD resolutions for aspect ratio presets (Width x Height format)
ASPECT_RATIO_RESOLUTIONS = {
    "1920x1080 (16:9 Landscape)": (1920, 1080),
    "1080x1920 (9:16 Portrait)": (1080, 1920),
    "1080x1080 (1:1 Square)": (1080, 1080),
    "1440x1080 (4:3 Classic)": (1440, 1080),
    "2560x1080 (21:9 Ultrawide)": (2560, 1080),
    "1920x817 (2.35:1 Cinema)": (1920, 817),
    "1920x1038 (1.85:1 Film)": (1920, 1038),
    # Legacy format support for backward compatibility
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:3": (1440, 1080),
    "21:9": (2560, 1080),
    "2.35:1": (1920, 817),
    "1.85:1": (1920, 1038)
}


class VideoProcessor:
    """
    Core video processing functionality for the Video Snippet Remixer.
    """
    
    def __init__(self, script_dir, video_filter=None):
        self.script_dir = script_dir
        self.video_filter = video_filter
        self.logger = get_logger("video_processor")
        self.temp_snippet_dir = os.path.join(script_dir, TEMP_DIR_NAME)
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self.ffmpeg_found = False
        self.ffprobe_found = False
        self.current_process = None
        self.abort_requested = False
        self.check_ffmpeg_tools()
    
    def check_ffmpeg_tools(self):
        """Checks for ffmpeg and ffprobe in PATH and returns their paths if found."""
        self.ffmpeg_path, self.ffmpeg_found = None, False
        self.ffprobe_path, self.ffprobe_found = None, False
        cmd_f = "where" if os.name == 'nt' else "which"

        try:
            proc_ffmpeg = subprocess.run(
                [cmd_f, "ffmpeg"], 
                capture_output=True, 
                text=True, 
                check=True, 
                shell=(os.name=='nt'), 
                encoding='utf-8', 
                errors='ignore'
            )
            ffmpeg_path_out = proc_ffmpeg.stdout.strip().split('\n')[0]
            if ffmpeg_path_out and os.path.isfile(ffmpeg_path_out) and os.access(ffmpeg_path_out, os.X_OK):
                self.ffmpeg_path = ffmpeg_path_out
                self.ffmpeg_found = True
                safe_print(f"INFO: Found FFmpeg at: {self.ffmpeg_path}")
            else:
                safe_print(f"WARNING: 'which/where ffmpeg' found '{ffmpeg_path_out}', but it's not a valid executable file.")
        except Exception:
            safe_print("WARNING: FFmpeg not found in system PATH or error checking.")

        try:
            proc_ffprobe = subprocess.run(
                [cmd_f, "ffprobe"], 
                capture_output=True, 
                text=True, 
                check=True, 
                shell=(os.name=='nt'), 
                encoding='utf-8', 
                errors='ignore'
            )
            ffprobe_path_out = proc_ffprobe.stdout.strip().split('\n')[0]
            if ffprobe_path_out and os.path.isfile(ffprobe_path_out) and os.access(ffprobe_path_out, os.X_OK):
                self.ffprobe_path = ffprobe_path_out
                self.ffprobe_found = True
                safe_print(f"INFO: Found FFprobe at: {self.ffprobe_path}")
            else:
                safe_print(f"WARNING: 'which/where ffprobe' found '{ffprobe_path_out}', but it's not a valid executable file.")
        except Exception:
            safe_print("WARNING: FFprobe not found in system PATH or error checking.")

        return self.ffmpeg_found, self.ffprobe_found
    
    def get_video_info(self, filepath):
        """
        Uses ffprobe to get width, height, and duration.
        For static images, returns a placeholder duration (actual duration from snippet settings).

        Args:
            filepath (str): Path to video or image file

        Returns:
            tuple: (width, height, duration) or (None, None, None) if failed
        """
        if not self.ffprobe_found or not os.path.exists(filepath):
            safe_print(f"Debug: ffprobe not found or path invalid for info check: {filepath}")
            return None, None, None

        # Check if this is an image file
        ext = os.path.splitext(filepath.lower())[1]
        is_image = ext in IMAGE_EXTENSIONS

        command = [
            self.ffprobe_path if self.ffprobe_path else "ffprobe",
            "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", filepath
        ]

        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=creationflags
            )
            output_lines = proc.stdout.strip().split('\n')

            # Parse width and height (always present for video/images)
            width = None
            height = None
            duration = None

            if len(output_lines) >= 2:
                try:
                    width = int(output_lines[0])
                except ValueError:
                    width = None
                try:
                    height = int(output_lines[1])
                except ValueError:
                    height = None

            # For images, return large placeholder duration (actual duration comes from snippet settings)
            if is_image:
                if width is not None and height is not None:
                    safe_print(f"Image detected: '{os.path.basename(filepath)}' ({width}x{height})")
                    return width, height, 9999.0  # Placeholder - actual duration from snippet settings
                else:
                    safe_print(f"Warning: Could not parse dimensions for image '{os.path.basename(filepath)}'")
                    return None, None, None

            # For videos, parse duration from third line
            if len(output_lines) >= 3:
                duration_str = output_lines[2]
                if duration_str.lower() == 'n/a':
                    duration = None
                else:
                    try:
                        duration = float(duration_str)
                    except ValueError:
                        duration = None

                if width is not None and height is not None and duration is not None:
                    return width, height, duration
                else:
                    safe_print(f"Warning: Could not parse all info for '{os.path.basename(filepath)}': W={width}, H={height}, D={duration}")
                    return None, None, None
            else:
                safe_print(f"Warning: Unexpected ffprobe output for '{os.path.basename(filepath)}': {output_lines}")
                return None, None, None

        except subprocess.CalledProcessError as e:
            safe_print(f"Error getting info for '{os.path.basename(filepath)}' (CalledProcessError): {e}")
            return None, None, None
        except (ValueError, TypeError) as e:
            safe_print(f"Error parsing info for '{os.path.basename(filepath)}': {e}")
            return None, None, None
        except FileNotFoundError:
            safe_print(f"Error: ffprobe command not found while trying to get info.")
            return None, None, None
        except Exception as e:
            safe_print(f"Unexpected error getting info for '{os.path.basename(filepath)}': {e}")
            return None, None, None
    
    def analyze_video_durations(self, input_files, snippet_duration_sec, progress_callback=None):
        """
        Analyze video files and return valid inputs with their durations.
        
        Args:
            input_files (list): List of video file paths
            snippet_duration_sec (float): Minimum duration required
            progress_callback (callable): Optional progress callback
            
        Returns:
            tuple: (valid_inputs_dict, files_too_short_list)
        """
        valid_inputs = {}
        files_too_short = []
        
        for i, filepath in enumerate(input_files):
            if progress_callback and ((i + 1) % 5 == 0 or i == 0 or i == len(input_files) - 1):
                progress_callback(f"Analyzing ({i+1}/{len(input_files)}): {os.path.basename(filepath)}")
                
            _, _, duration = self.get_video_info(filepath)
            if duration is not None and duration > 0:
                if duration >= snippet_duration_sec:
                    valid_inputs[filepath] = duration
                else:
                    files_too_short.append(os.path.basename(filepath))
                    safe_print(f"Skipping '{os.path.basename(filepath)}': Duration ({duration:.2f}s) < snippet length ({snippet_duration_sec:.2f}s).")
            else:
                safe_print(f"Warning: Could not get duration for '{os.path.basename(filepath)}'. Skipping.")
        
        return valid_inputs, files_too_short
    
    def generate_snippet_definitions(self, valid_inputs, target_total_duration_sec, snippet_duration_spec, jitter_settings=None):
        """
        Generate random snippet definitions from valid input videos.
        
        Args:
            valid_inputs (dict): Dictionary of filepath -> duration
            target_total_duration_sec (float): Target total duration
            snippet_duration_spec (float or list): Duration per snippet (fixed) or list for modulated schedule
            jitter_settings (dict): Optional jitter settings with 'enabled' and 'intensity' keys
            
        Returns:
            list: List of (filepath, start_time, duration) tuples
        """
        if isinstance(snippet_duration_spec, (list, tuple)):
            num_snippets_needed = len(snippet_duration_spec)
            snippet_durations = list(snippet_duration_spec)
        else:
            num_snippets_needed = math.ceil(target_total_duration_sec / snippet_duration_spec)
            snippet_durations = [snippet_duration_spec] * num_snippets_needed

        if num_snippets_needed <= 0 or len(snippet_durations) == 0:
            raise ValueError("Calculated snippets needed is zero or negative.")
            
        snippet_definitions = []
        available_files = list(valid_inputs.keys())
        
        # Extract jitter settings
        jitter_enabled = False
        jitter_intensity = 50
        if jitter_settings:
            jitter_enabled = jitter_settings.get("jitter_enabled", False)
            jitter_intensity = jitter_settings.get("jitter_intensity", 50)
        
        # Calculate jitter range (0-100% maps to 0-50% variation)
        jitter_factor = (jitter_intensity / 100.0) * 0.5  # Max 50% variation
        
        if isinstance(snippet_duration_spec, (list, tuple)):
            safe_print(f"Need {num_snippets_needed} snippets (variable durations).")
        else:
            safe_print(f"Need {num_snippets_needed} snippets of {snippet_duration_spec:.3f}s each.")
        if jitter_enabled:
            safe_print(f"Jitter enabled with intensity {jitter_intensity}% (~{jitter_factor*100:.1f}% variation)")
        
        for i in range(num_snippets_needed):
            if not available_files:
                raise ValueError("Ran out of source material unexpectedly.")
            
            chosen_file = random.choice(available_files)
            
            # Apply jitter to duration if enabled
            actual_duration = snippet_durations[i]
            if jitter_enabled and jitter_factor > 0:
                # Random variation between -jitter_factor and +jitter_factor
                duration_variation = random.uniform(-jitter_factor, jitter_factor)
                actual_duration = snippet_durations[i] * (1 + duration_variation)
                # Ensure minimum duration of 0.1 seconds
                actual_duration = max(0.1, actual_duration)
            
            # Calculate max start time based on actual duration
            max_start_time = max(0, valid_inputs[chosen_file] - actual_duration)
            
            # Apply jitter to start time if enabled
            if jitter_enabled and jitter_factor > 0 and max_start_time > 0:
                # Add some randomness to the start time selection
                # Instead of pure uniform distribution, add some jitter
                base_start = random.uniform(0, max_start_time)
                start_jitter = random.uniform(-jitter_factor, jitter_factor) * min(5.0, max_start_time * 0.2)
                random_start = max(0, min(max_start_time, base_start + start_jitter))
            else:
                random_start = random.uniform(0, max_start_time) if max_start_time > 0 else 0
            
            snippet_definitions.append((chosen_file, random_start, actual_duration))
        
        return snippet_definitions
    
    def calculate_intermediate_resolution(self, aspect_ratio_str, export_settings=None):
        """
        Calculate appropriate intermediate resolution based on aspect ratio and export settings.
        
        Args:
            aspect_ratio_str (str): Target aspect ratio (e.g., "16:9", "9:16", "Original")
            export_settings (dict): Optional export settings with custom width/height
            
        Returns:
            tuple: (width, height) for intermediate processing
        """
        # Check for custom resolution in export settings
        if export_settings:
            custom_width = export_settings.get("custom_width")
            custom_height = export_settings.get("custom_height")
            if custom_width and custom_height:
                # Ensure even dimensions for codec compatibility
                width = int(custom_width) if int(custom_width) % 2 == 0 else int(custom_width) + 1
                height = int(custom_height) if int(custom_height) % 2 == 0 else int(custom_height) + 1
                return width, height
        
        # Use predefined resolutions for common aspect ratios
        if aspect_ratio_str in ASPECT_RATIO_RESOLUTIONS:
            return ASPECT_RATIO_RESOLUTIONS[aspect_ratio_str]
        
        # Calculate for custom aspect ratios
        if aspect_ratio_str != "Original":
            ar_value = parse_aspect_ratio(aspect_ratio_str)
            if ar_value:
                # Base height of 720p, calculate width
                base_height = 720
                calculated_width = int(base_height * ar_value)
                # Ensure even dimensions
                if calculated_width % 2 != 0:
                    calculated_width += 1
                return calculated_width, base_height
        
        # Default fallback
        return 1280, 720
    
    def prepare_temp_directory(self):
        """
        Prepare temporary directory for snippet processing.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if os.path.exists(self.temp_snippet_dir):
            try:
                shutil.rmtree(self.temp_snippet_dir)
            except OSError as e:
                safe_print(f"Warning: Could not remove existing temp dir '{self.temp_snippet_dir}': {e}")
        
        try:
            os.makedirs(self.temp_snippet_dir, exist_ok=True)
            return True
        except OSError as e:
            safe_print(f"Error: Could not create temp dir: {e}")
            return False
    
    def cut_video_snippets(self, snippet_definitions, aspect_ratio="16:9", export_settings=None, progress_callback=None, aspect_ratio_mode="crop"):
        """
        Cut video snippets from source files.
        
        Args:
            snippet_definitions (list): List of (filepath, start_time, duration) tuples
            aspect_ratio (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Optional progress callback
            aspect_ratio_mode (str): How to handle aspect ratio - "crop" or "pad"
            
        Returns:
            list: List of successfully created snippet file paths
        """
        snippet_files = []
        
        # Calculate intermediate resolution
        width, height = self.calculate_intermediate_resolution(aspect_ratio, export_settings)
        resolution_str = f"{width}:{height}"
        
        # Get frame rate from export settings
        fps = DEFAULT_INTERMEDIATE_FPS
        if export_settings and not export_settings.get("match_input_fps"):
            fps = export_settings.get("frame_rate", DEFAULT_INTERMEDIATE_FPS)
        
        # Get quality settings
        quality_params = ["-preset", "fast", "-crf", "23"]
        if export_settings:
            if export_settings.get("bitrate_mode") == "crf":
                crf = export_settings.get("quality_crf", 23)
                quality_params = ["-preset", "fast", "-crf", str(crf)]
            else:
                bitrate = export_settings.get("bitrate", "5M")
                quality_params = ["-b:v", bitrate]
        
        remove_audio = export_settings.get("remove_audio", False) if export_settings else False
        if remove_audio:
            self.logger.info("Audio muting enabled for snippet generation.")
            safe_print("Audio muting enabled for snippet generation.")

        for i, (filepath, start, duration) in enumerate(snippet_definitions):
            if progress_callback:
                progress_callback(f"Cutting snippet {i+1}/{len(snippet_definitions)}...")
                
            temp_snippet_path = os.path.join(self.temp_snippet_dir, f"snippet_{i:04d}{INTERMEDIATE_EXTENSION}")
            
            # Build video filter
            vf_parts = []
            if export_settings and export_settings.get("match_input_fps"):
                # Don't change FPS if matching input
                pass
            else:
                vf_parts.append(f"fps={fps}")
            
            # Apply aspect ratio mode
            if aspect_ratio_mode == "pad":
                # Scale to fit within frame (may have black bars) then pad to exact size
                vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=decrease")
                vf_parts.append(f"pad={resolution_str}:(ow-iw)/2:(oh-ih)/2:black")
            else:
                # Default to crop mode
                # Scale to fill frame (may overflow) then crop to exact size
                vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=increase")
                vf_parts.append(f"crop={resolution_str}")
            vf_filter = ",".join(vf_parts)
            
            # Handle trim if specified in export settings
            input_params = []
            if export_settings and export_settings.get("trim_start"):
                from .utils import parse_time_to_seconds
                trim_start = parse_time_to_seconds(export_settings["trim_start"])
                if trim_start is not None:
                    start += trim_start  # Adjust start time by trim
            
            # Check if this is an image file
            ext = os.path.splitext(filepath.lower())[1]
            is_image = ext in IMAGE_EXTENSIONS

            if is_image:
                # For images: use -loop 1 to create video from static image
                # Images have no audio, so always use -an
                cut_command = [
                    self.ffmpeg_path or "ffmpeg",
                    "-hide_banner", "-loglevel", "error",
                    "-loop", "1",
                    "-i", filepath,
                    "-t", str(duration),
                    "-vf", vf_filter,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",  # Required for broad compatibility
                ] + quality_params + [
                    "-an",  # No audio for images
                    "-y", temp_snippet_path
                ]
            else:
                # For videos: use standard -ss and -t for seeking
                audio_params = ["-an"] if remove_audio else ["-c:a", "aac", "-b:a", "128k"]

                cut_command = [
                    self.ffmpeg_path or "ffmpeg",
                    "-hide_banner", "-loglevel", "error",
                    "-i", filepath,
                    "-ss", str(start),
                    "-t", str(duration),
                    "-vf", vf_filter,
                    "-c:v", "libx264"] + quality_params + audio_params + [
                    "-avoid_negative_ts", "make_zero",
                    "-y", temp_snippet_path
                ]

            # Log the full command
            with LoggingContext(self.video_filter, video_file=filepath):
                log_ffmpeg_command(self.logger, cut_command)
                
            try:
                # Check abort before starting
                if self.abort_requested:
                    raise Exception("Processing aborted by user")
                    
                start_time = time.time()
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                self.current_process = subprocess.Popen(
                    cut_command, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True, 
                    encoding='utf-8', 
                    errors='ignore', 
                    creationflags=creationflags
                )
                stdout, stderr = self.current_process.communicate()
                return_code = self.current_process.returncode
                
                # Clean up subprocess pipes to prevent resource leak
                if hasattr(self.current_process.stdout, 'close'):
                    try:
                        self.current_process.stdout.close()
                    except Exception:
                        pass
                if hasattr(self.current_process.stderr, 'close'):
                    try:
                        self.current_process.stderr.close()
                    except Exception:
                        pass
                
                self.current_process = None
                
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, cut_command, stdout, stderr)
                elapsed = time.time() - start_time
                
                # Verify output and log results
                if os.path.exists(temp_snippet_path):
                    output_width, output_height, output_duration = self.get_video_info(temp_snippet_path)
                    if output_width and output_height:
                        with LoggingContext(self.video_filter, 
                                          video_file=filepath,
                                          dimensions=f"{output_width}x{output_height}",
                                          aspect_ratio=f"{output_width/output_height:.3f}"):
                            self.logger.info(f"Snippet {i+1} created successfully in {elapsed:.2f}s")
                            self.logger.debug(f"Output: {output_width}x{output_height}, duration: {output_duration:.2f}s")
                    snippet_files.append(temp_snippet_path)
                    
                    # Optionally verify snippet dimensions
                    if export_settings and export_settings.get("verify_snippets", False):
                        actual_w, actual_h, _ = self.verify_output_dimensions(
                            temp_snippet_path, width, height, False
                        )
                        if actual_w != width or actual_h != height:
                            self.logger.warning(f"Snippet {i+1} dimension mismatch! Expected: {width}x{height}, Actual: {actual_w}x{actual_h}")
                            safe_print(f"Warning: Snippet {i+1} dimension mismatch! Expected: {width}x{height}, Actual: {actual_w}x{actual_h}")
                else:
                    raise Exception(f"Output file not created: {temp_snippet_path}")
                    
            except subprocess.CalledProcessError as e:
                self.logger.error(f"FFmpeg error cutting snippet {i+1}: {e}")
                if e.stderr:
                    self.logger.error(f"FFmpeg stderr: {e.stderr}")
                safe_print(f"Error cutting snippet {i+1}:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}")
                raise Exception(f"Error cutting snippet {i+1}")
            except Exception as e:
                self.logger.error(f"Unexpected error cutting snippet {i+1}: {e}", exc_info=True)
                safe_print(f"Unexpected error cutting snippet {i+1}: {e}")
                raise Exception(f"Unexpected error cutting snippet {i+1}")
        
        self.logger.info(f"Successfully created {len(snippet_files)} snippets")
        return snippet_files
    
    def concatenate_snippets(self, snippet_files, progress_callback=None):
        """
        Concatenate video snippets into a single file.
        
        Args:
            snippet_files (list): List of snippet file paths
            progress_callback (callable): Optional progress callback
            
        Returns:
            str: Path to concatenated video file
        """
        if progress_callback:
            progress_callback("Preparing concatenation list...")
            
        concat_list_path = os.path.join(self.temp_snippet_dir, "mylist.txt")
        temp_concat_path = os.path.join(self.temp_snippet_dir, TEMP_CONCAT_FILENAME)
        
        try:
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for snip_path in snippet_files:
                    safe_path = snip_path.replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
        except IOError as e:
            safe_print(f"Error writing concat list file: {e}")
            raise Exception("Failed to write concat list file.")

        if progress_callback:
            progress_callback("Concatenating snippets...")
            
        concat_command = [
            self.ffmpeg_path or "ffmpeg", 
            "-hide_banner", "-loglevel", "error", 
            "-f", "concat", "-safe", "0", 
            "-i", concat_list_path, 
            "-c", "copy", 
            "-y", temp_concat_path
        ]
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(
                concat_command, 
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True, 
                check=True, 
                encoding='utf-8', 
                errors='ignore', 
                creationflags=creationflags
            )
        except subprocess.CalledProcessError as e:
            safe_print(f"Error concatenating snippets:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}")
            raise Exception("Concatenation failed")
        except Exception as e:
            safe_print(f"Unexpected error during concatenation: {e}")
            raise Exception("Unexpected concatenation error")
            
        if not os.path.exists(temp_concat_path):
            raise Exception("Concatenated temp file not found.")
            
        return temp_concat_path
    
    def adjust_aspect_ratio(self, temp_concat_path, final_output_path, aspect_ratio_selection, export_settings=None, progress_callback=None, aspect_ratio_mode="crop"):
        """
        Adjust aspect ratio and create final output file.
        
        Args:
            temp_concat_path (str): Path to temporary concatenated file
            final_output_path (str): Path for final output file
            aspect_ratio_selection (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Optional progress callback
            aspect_ratio_mode (str): How to handle aspect ratio - "crop" or "pad"
            
        Returns:
            bool: True if successful, False otherwise
        """
        remove_audio = export_settings.get("remove_audio", False) if export_settings else False
        if remove_audio:
            self.logger.info("Audio muting enabled for final output.")
            safe_print("Audio muting enabled for final export.")

        if aspect_ratio_selection == "Original":
            if progress_callback:
                suffix = " (audio muted)" if remove_audio else ""
                progress_callback(f"Finalizing (Original Aspect Ratio){suffix}...")
            if remove_audio:
                command = [
                    self.ffmpeg_path or "ffmpeg",
                    "-hide_banner", "-loglevel", "error",
                    "-i", temp_concat_path,
                    "-c:v", "copy",
                    "-an",
                    "-y", final_output_path
                ]
                try:
                    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    subprocess.run(
                        command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        encoding='utf-8',
                        errors='ignore',
                        creationflags=creationflags
                    )
                    try:
                        os.remove(temp_concat_path)
                    except OSError as e:
                        safe_print(f"Warning: Could not remove temp concat file after muting audio: {e}")
                    return True
                except subprocess.CalledProcessError as e:
                    safe_print(f"Error muting audio:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}")
                    return False
                except Exception as e:
                    safe_print(f"Unexpected error while muting audio: {e}")
                    return False
            else:
                try:
                    shutil.move(temp_concat_path, final_output_path)
                    return True
                except (IOError, OSError) as e:
                    safe_print(f"Error moving temp concat file: {e}")
                    return False
        else:
            if progress_callback:
                progress_callback(f"Adjusting Aspect Ratio to {aspect_ratio_selection}...")
                
            width, height, _ = self.get_video_info(temp_concat_path)
            target_ar_val = parse_aspect_ratio(aspect_ratio_selection)
            
            if width and height and target_ar_val:
                source_ar_val = width / height
                
                # Calculate target dimensions
                if aspect_ratio_selection in ASPECT_RATIO_RESOLUTIONS:
                    target_width, target_height = ASPECT_RATIO_RESOLUTIONS[aspect_ratio_selection]
                else:
                    # Use current height and calculate width for custom aspect ratios
                    target_height = height
                    target_width = int(target_height * target_ar_val)
                    # Ensure even dimensions
                    if target_width % 2 != 0:
                        target_width += 1
                
                # Build filter based on aspect ratio mode
                if aspect_ratio_mode == "pad":
                    # Scale to fit and pad with black bars
                    ar_filter_vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black"
                else:
                    # Default to crop mode - scale to fill and crop excess
                    ar_filter_vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height}"
                
                safe_print(f"AR Filter ({aspect_ratio_mode} mode): {ar_filter_vf}")
                
                # Get quality settings from export_settings
                quality_params = ["-preset", "fast", "-crf", "23"]
                if export_settings:
                    if export_settings.get("bitrate_mode") == "crf":
                        crf = export_settings.get("quality_crf", 23)
                        quality_params = ["-preset", "fast", "-crf", str(crf)]
                    else:
                        bitrate = export_settings.get("bitrate", "5M")
                        quality_params = ["-b:v", bitrate]
                
                audio_params = ["-an"] if remove_audio else ["-c:a", "copy"]

                ar_command = [
                    self.ffmpeg_path or "ffmpeg", 
                    "-hide_banner", "-loglevel", "error", 
                    "-i", temp_concat_path,
                    "-vf", ar_filter_vf, 
                    "-c:v", "libx264"] + quality_params + audio_params + [
                    "-y", final_output_path
                ]
                
                try:
                    safe_print(f"Running FFmpeg AR Adjust: {' '.join(ar_command)}")
                    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    subprocess.run(
                        ar_command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        encoding='utf-8',
                        errors='ignore',
                        creationflags=creationflags
                    )
                    
                    # Clean up intermediate after success
                    try:
                        os.remove(temp_concat_path)
                    except OSError as e:
                        safe_print(f"Warning: Could not remove temp concat file after AR adjust: {e}")
                    
                    return True
                except subprocess.CalledProcessError as e:
                    safe_print(f"Error adjusting AR:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}")
                    return False
                except Exception as e:
                    safe_print(f"Unexpected error adjusting AR: {e}")
                    return False
            else:
                safe_print("Error: Cannot adjust AR (invalid info/target). Saving intermediate.")
                try:
                    shutil.move(temp_concat_path, final_output_path)
                    return True
                except (IOError, OSError) as e:
                    safe_print(f"Error moving temp concat file: {e}")
                    return False
    
    def cleanup_temp_directory(self):
        """
        Clean up temporary directory and files.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if os.path.exists(self.temp_snippet_dir):
            try:
                shutil.rmtree(self.temp_snippet_dir)
                safe_print(f"Successfully removed temporary directory: {self.temp_snippet_dir}")
                return True
            except OSError as e:
                safe_print(f"Error removing temporary directory '{self.temp_snippet_dir}': {e}")
                return False
        return True
    
    def are_tools_available(self):
        """
        Check if both FFmpeg and FFprobe are available.
        
        Returns:
            tuple: (ffmpeg_found, ffprobe_found)
        """
        return self.ffmpeg_found, self.ffprobe_found
    
    def abort_processing(self):
        """
        Request abort of current processing and terminate any running subprocess.
        """
        self.abort_requested = True
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
                self.current_process.wait()
            except Exception as e:
                self.logger.error(f"Error terminating subprocess: {e}")
            finally:
                # Clean up subprocess pipes after termination
                if hasattr(self.current_process, 'stdout') and self.current_process.stdout:
                    try:
                        self.current_process.stdout.close()
                    except Exception:
                        pass
                if hasattr(self.current_process, 'stderr') and self.current_process.stderr:
                    try:
                        self.current_process.stderr.close()
                    except Exception:
                        pass
    
    def verify_output_dimensions(self, video_path, expected_width=None, expected_height=None, check_black_bars=False):
        """
        Verify the actual output dimensions of a video file and optionally check for black bars.
        
        Args:
            video_path (str): Path to the video file to verify
            expected_width (int): Expected width (optional)
            expected_height (int): Expected height (optional)
            check_black_bars (bool): Whether to check for black bars using blackdetect filter
            
        Returns:
            tuple: (actual_width, actual_height, has_black_bars)
                   Returns (None, None, None) if verification fails
        """
        if not self.ffprobe_found or not os.path.exists(video_path):
            self.logger.debug(f"ffprobe not found or path invalid for verification: {video_path}")
            safe_print(f"Debug: ffprobe not found or path invalid for verification: {video_path}")
            return None, None, None
        
        # Get video dimensions using ffprobe with JSON output
        with LoggingContext(self.video_filter, video_file=video_path):
            self.logger.debug("Verifying output dimensions")
            
        try:
            # Use ffprobe to get stream information in JSON format
            command = [
                self.ffprobe_path if self.ffprobe_path else "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", "v:0",
                video_path
            ]
            
            log_ffmpeg_command(self.logger, command, level=logging.DEBUG)
            
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=creationflags
            )
            
            import json
            data = json.loads(proc.stdout)
            
            # Extract dimensions from the first video stream
            if data.get("streams") and len(data["streams"]) > 0:
                stream = data["streams"][0]
                actual_width = stream.get("width")
                actual_height = stream.get("height")
                
                if actual_width is None or actual_height is None:
                    safe_print(f"Warning: Could not extract dimensions from video stream")
                    return None, None, None
                
                # Log dimension verification
                if expected_width and expected_height:
                    if actual_width != expected_width or actual_height != expected_height:
                        safe_print(f"Warning: Output dimensions mismatch! Expected: {expected_width}x{expected_height}, Actual: {actual_width}x{actual_height}")
                    else:
                        safe_print(f"Info: Output dimensions verified: {actual_width}x{actual_height}")
                else:
                    safe_print(f"Info: Video dimensions: {actual_width}x{actual_height}")
                
            else:
                safe_print(f"Error: No video streams found in {video_path}")
                return None, None, None
                
        except subprocess.CalledProcessError as e:
            safe_print(f"Error getting dimensions for '{os.path.basename(video_path)}': {e}")
            return None, None, None
        except json.JSONDecodeError as e:
            safe_print(f"Error parsing ffprobe JSON output: {e}")
            return None, None, None
        except Exception as e:
            safe_print(f"Unexpected error verifying dimensions: {e}")
            return None, None, None
        
        # Check for black bars if requested
        has_black_bars = False
        if check_black_bars and self.ffmpeg_found:
            try:
                # Use ffmpeg with blackdetect filter
                # d=0.1: black duration threshold (0.1 seconds)
                # pix_th=0.10: pixel threshold (10% deviation from pure black)
                command = [
                    self.ffmpeg_path if self.ffmpeg_path else "ffmpeg",
                    "-i", video_path,
                    "-vf", "blackdetect=d=0.1:pix_th=0.10",
                    "-an",  # Disable audio processing
                    "-f", "null",
                    "-"  # Null output
                ]
                
                proc = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=creationflags
                )
                
                # blackdetect outputs to stderr
                stderr_output = proc.stderr.lower()
                
                # Check if blackdetect found any black areas
                if "black_start" in stderr_output or "blackdetect" in stderr_output:
                    # Parse blackdetect output to check if bars span the entire video
                    lines = proc.stderr.split('\n')
                    black_detections = []
                    
                    for line in lines:
                        if "black_start" in line:
                            # Extract black detection info
                            black_detections.append(line)
                    
                    # If we have consistent black areas throughout the video, likely black bars
                    if len(black_detections) > 0:
                        # Get video duration for comparison
                        _, _, duration = self.get_video_info(video_path)
                        if duration and len(black_detections) > int(duration * 0.8):  # Black detected in 80%+ of video
                            has_black_bars = True
                            safe_print(f"Warning: Black bars detected in output video!")
                        else:
                            safe_print(f"Info: Some black frames detected but not consistent black bars ({len(black_detections)} detections)")
                else:
                    safe_print(f"Info: No black bars detected in output video")
                    
            except subprocess.CalledProcessError as e:
                safe_print(f"Warning: Could not check for black bars (non-critical): {e}")
            except Exception as e:
                safe_print(f"Warning: Error during black bar detection (non-critical): {e}")
        
        return actual_width, actual_height, has_black_bars
