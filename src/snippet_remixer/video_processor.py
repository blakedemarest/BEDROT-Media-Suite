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
from .utils import safe_print, parse_aspect_ratio

# Constants
DEFAULT_INTERMEDIATE_FPS = "30"
INTERMEDIATE_EXTENSION = ".ts"
TEMP_CONCAT_FILENAME = "_temp_concat.mp4"
TEMP_DIR_NAME = "remixer_temp_snippets"

# Common resolutions for different aspect ratios (1080p quality)
ASPECT_RATIO_RESOLUTIONS = {
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
    
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.temp_snippet_dir = os.path.join(script_dir, TEMP_DIR_NAME)
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self.ffmpeg_found = False
        self.ffprobe_found = False
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
        
        Args:
            filepath (str): Path to video file
            
        Returns:
            tuple: (width, height, duration) or (None, None, None) if failed
        """
        if not self.ffprobe_found or not os.path.exists(filepath):
            safe_print(f"Debug: ffprobe not found or path invalid for info check: {filepath}")
            return None, None, None
            
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
            
            if len(output_lines) >= 3:
                try:
                    width = int(output_lines[0])
                except ValueError:
                    width = None
                try:
                    height = int(output_lines[1])
                except ValueError:
                    height = None
                    
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
    
    def generate_snippet_definitions(self, valid_inputs, target_total_duration_sec, snippet_duration_sec):
        """
        Generate random snippet definitions from valid input videos.
        
        Args:
            valid_inputs (dict): Dictionary of filepath -> duration
            target_total_duration_sec (float): Target total duration
            snippet_duration_sec (float): Duration per snippet
            
        Returns:
            list: List of (filepath, start_time, duration) tuples
        """
        num_snippets_needed = math.ceil(target_total_duration_sec / snippet_duration_sec)
        if num_snippets_needed <= 0:
            raise ValueError("Calculated snippets needed is zero or negative.")
            
        snippet_definitions = []
        available_files = list(valid_inputs.keys())
        safe_print(f"Need {num_snippets_needed} snippets of {snippet_duration_sec:.3f}s each.")
        
        for _ in range(num_snippets_needed):
            if not available_files:
                raise ValueError("Ran out of source material unexpectedly.")
                
            chosen_file = random.choice(available_files)
            max_start_time = max(0, valid_inputs[chosen_file] - snippet_duration_sec)
            random_start = random.uniform(0, max_start_time)
            snippet_definitions.append((chosen_file, random_start, snippet_duration_sec))
        
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
    
    def cut_video_snippets(self, snippet_definitions, aspect_ratio="16:9", export_settings=None, progress_callback=None):
        """
        Cut video snippets from source files.
        
        Args:
            snippet_definitions (list): List of (filepath, start_time, duration) tuples
            aspect_ratio (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Optional progress callback
            
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
        
        for i, (filepath, start, duration) in enumerate(snippet_definitions):
            if progress_callback:
                progress_callback(f"Cutting snippet {i+1}/{len(snippet_definitions)}...")
                
            temp_snippet_path = os.path.join(self.temp_snippet_dir, f"snippet_{i:04d}{INTERMEDIATE_EXTENSION}")
            
            # Build video filter
            vf_parts = []
            if export_settings and export_settings.get("match_input_fps"):
                # Don't change FPS if matching input
                vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=decrease")
            else:
                vf_parts.append(f"fps={fps}")
                vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=decrease")
            
            vf_parts.append(f"pad={resolution_str}:-1:-1:color=black")
            vf_filter = ",".join(vf_parts)
            
            # Handle trim if specified in export settings
            input_params = []
            if export_settings and export_settings.get("trim_start"):
                from .utils import parse_time_to_seconds
                trim_start = parse_time_to_seconds(export_settings["trim_start"])
                if trim_start is not None:
                    start += trim_start  # Adjust start time by trim
            
            cut_command = [
                self.ffmpeg_path or "ffmpeg", 
                "-hide_banner", "-loglevel", "error", 
                "-i", filepath,
                "-ss", str(start), 
                "-t", str(duration), 
                "-vf", vf_filter,
                "-c:v", "libx264"] + quality_params + [
                "-c:a", "aac", "-b:a", "128k", 
                "-avoid_negative_ts", "make_zero",
                "-y", temp_snippet_path
            ]
            
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.run(
                    cut_command, 
                    capture_output=True, 
                    text=True, 
                    check=True, 
                    encoding='utf-8', 
                    errors='ignore', 
                    creationflags=creationflags
                )
                snippet_files.append(temp_snippet_path)
            except subprocess.CalledProcessError as e:
                safe_print(f"Error cutting snippet {i+1}:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}")
                raise Exception(f"Error cutting snippet {i+1}")
            except Exception as e:
                safe_print(f"Unexpected error cutting snippet {i+1}: {e}")
                raise Exception(f"Unexpected error cutting snippet {i+1}")
        
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
                capture_output=True, 
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
    
    def adjust_aspect_ratio(self, temp_concat_path, final_output_path, aspect_ratio_selection, export_settings=None, progress_callback=None):
        """
        Adjust aspect ratio and create final output file.
        
        Args:
            temp_concat_path (str): Path to temporary concatenated file
            final_output_path (str): Path for final output file
            aspect_ratio_selection (str): Target aspect ratio
            export_settings (dict): Optional export settings
            progress_callback (callable): Optional progress callback
            
        Returns:
            bool: True if successful, False otherwise
        """
        if aspect_ratio_selection == "Original":
            if progress_callback:
                progress_callback("Finalizing (Original Aspect Ratio)...")
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
                tolerance = 0.01
                
                if abs(source_ar_val - target_ar_val) < tolerance:
                    if progress_callback:
                        progress_callback("Intermediate matches target AR. Finalizing...")
                    try:
                        shutil.move(temp_concat_path, final_output_path)
                        return True
                    except (IOError, OSError) as e:
                        safe_print(f"Error moving temp concat file: {e}")
                        return False
                else:
                    if source_ar_val > target_ar_val:
                        ar_filter_vf = f"crop=w=ih*{target_ar_val:.4f}:h=ih"
                    else:
                        ar_filter_vf = f"pad=w=ih*{target_ar_val:.4f}:h=ih:x=(ow-iw)/2:y=0:color=black"
                    
                    safe_print(f"AR Filter: {ar_filter_vf}")
                    
                    # Get quality settings from export_settings
                    quality_params = ["-preset", "fast", "-crf", "23"]
                    if export_settings:
                        if export_settings.get("bitrate_mode") == "crf":
                            crf = export_settings.get("quality_crf", 23)
                            quality_params = ["-preset", "fast", "-crf", str(crf)]
                        else:
                            bitrate = export_settings.get("bitrate", "5M")
                            quality_params = ["-b:v", bitrate]
                    
                    ar_command = [
                        self.ffmpeg_path or "ffmpeg", 
                        "-hide_banner", "-loglevel", "error", 
                        "-i", temp_concat_path,
                        "-vf", ar_filter_vf, 
                        "-c:v", "libx264"] + quality_params + [
                        "-c:a", "copy",
                        "-y", final_output_path
                    ]
                    
                    try:
                        safe_print(f"Running FFmpeg AR Adjust: {' '.join(ar_command)}")
                        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        subprocess.run(
                            ar_command, 
                            capture_output=True, 
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