"""Video processing module for generating MP4 overlays with captions."""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from absolute path to handle direct script execution
try:
    from .utils import safe_print, sanitize_filename
    from .font_manager import get_font_manager
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import safe_print, sanitize_filename
    from mv_maker.font_manager import get_font_manager

class VideoProcessor:
    """Handles video processing operations including caption overlays."""
    
    def __init__(self):
        """Initialize video processor."""
        self.temp_dir = None
        self.font_manager = get_font_manager()
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_font_name(self, font_family):
        """Get the appropriate font name for FFmpeg based on font family."""
        # Use font manager to get proper font path/name
        return self.font_manager.get_font_for_ffmpeg(font_family)
    
    def generate_ass_subtitles(self, captions, output_path, config):
        """
        Generate ASS subtitle file for advanced styling.
        
        Args:
            captions: List of caption dictionaries
            output_path: Path for output ASS file
            config: Configuration dictionary
            
        Returns:
            Path to created ASS file
        """
        font_family = config.get('font_family', 'sans')
        font_size = config.get('font_size', 24)
        font_color = config.get('font_color', '#FFFFFF')
        background_opacity = int(config.get('background_opacity', 0.7) * 255)
        border = config.get('subtitle_border', 2)
        shadow = config.get('subtitle_shadow', True)
        position = config.get('position', 'bottom')
        
        # Convert hex color to BGR for ASS format
        if font_color.startswith('#'):
            hex_color = font_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)  
            b = int(hex_color[4:6], 16)
            ass_color = f"&H00{b:02X}{g:02X}{r:02X}"
        else:
            ass_color = "&H00FFFFFF"
        
        # Get font name
        font_name = self.get_font_name(font_family)
        
        # Validate font availability
        font_family = self.font_manager.validate_font_selection(font_family)
        
        # Set alignment based on position
        if position == 'top':
            alignment = 8  # Top center
            margin_v = 30
        elif position == 'middle':
            alignment = 5  # Middle center
            margin_v = 0
        else:  # bottom
            alignment = 2  # Bottom center
            margin_v = 30
        
        # Create ASS content
        ass_content = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{ass_color},&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,{border},{2 if shadow else 0},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Add captions
        for caption in captions:
            start_time = self.format_ass_time(caption['start'])
            end_time = self.format_ass_time(caption['end'])
            text = caption['text'].replace('\n', '\\N')
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
        
        # Write ASS file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        return output_path
    
    def format_ass_time(self, seconds):
        """Format time for ASS subtitle format (H:MM:SS.CS)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def generate_mp4_overlay(self, video_path, captions, output_path, config, progress_callback=None):
        """
        Generate MP4 video with caption overlay.
        
        Args:
            video_path: Path to input video file
            captions: List of caption dictionaries
            output_path: Path for output MP4 file
            config: Configuration dictionary
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to created MP4 file
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg is required for MP4 overlay generation. Please install FFmpeg.")
        
        if progress_callback:
            progress_callback(0, 100, "Preparing subtitle overlay...")
        
        # Create temporary directory for subtitle file
        self.temp_dir = tempfile.mkdtemp(prefix="video_overlay_")
        
        try:
            # Generate ASS subtitle file
            ass_path = os.path.join(self.temp_dir, "subtitles.ass")
            self.generate_ass_subtitles(captions, ass_path, config)
            
            if progress_callback:
                progress_callback(20, 100, "Generating MP4 overlay...")
            
            # Prepare FFmpeg command
            quality = config.get('mp4_overlay_quality', 'high')
            bitrate = config.get('mp4_overlay_bitrate', '2M')
            
            # Quality settings
            if quality == 'low':
                preset = 'ultrafast'
                crf = '28'
            elif quality == 'medium':
                preset = 'medium'
                crf = '23'
            else:  # high
                preset = 'slow'
                crf = '18'
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'ass={ass_path}',
                '-c:v', 'libx264',
                '-preset', preset,
                '-crf', crf,
                '-b:v', bitrate,
                '-c:a', 'copy',  # Copy audio stream without re-encoding
                '-y',  # Overwrite output file
                output_path
            ]
            
            safe_print(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Monitor progress
            stderr_output = []
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                    
                if line:
                    stderr_output.append(line.strip())
                    
                    # Extract progress information
                    if 'time=' in line and progress_callback:
                        try:
                            time_str = line.split('time=')[1].split()[0]
                            current_seconds = self.parse_ffmpeg_time(time_str)
                            
                            # Get video duration if we haven't already
                            if hasattr(self, '_video_duration'):
                                progress = min(int((current_seconds / self._video_duration) * 80) + 20, 100)
                                progress_callback(progress, 100, f"Processing video... {time_str}")
                        except:
                            pass
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code != 0:
                error_msg = '\n'.join(stderr_output[-10:])  # Last 10 lines
                raise RuntimeError(f"FFmpeg failed with return code {return_code}:\n{error_msg}")
            
            if progress_callback:
                progress_callback(100, 100, "MP4 overlay completed!")
            
            safe_print(f"MP4 overlay created: {output_path}")
            return output_path
            
        finally:
            # Clean up temporary files
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
    
    def parse_ffmpeg_time(self, time_str):
        """Parse FFmpeg time format (HH:MM:SS.MS) to seconds."""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return 0
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds using FFprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                self._video_duration = duration
                return duration
        except:
            pass
        
        # Fallback: assume 60 seconds for progress calculation
        self._video_duration = 60
        return 60 