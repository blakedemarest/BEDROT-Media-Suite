"""Audio to video generator for creating MP4 from audio files."""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from .utils import safe_print, get_ffmpeg_path, run_ffmpeg_command
except ImportError:
    from mv_maker.utils import safe_print, get_ffmpeg_path, run_ffmpeg_command


class AudioToVideoGenerator:
    """Generates video files from audio input with configurable backgrounds."""
    
    # Common aspect ratios with dimensions
    ASPECT_RATIOS = {
        '16:9': {
            'name': 'Widescreen (YouTube, TV)',
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '4k': (3840, 2160)
        },
        '9:16': {
            'name': 'Vertical (TikTok, Reels)',
            '720p': (720, 1280),
            '1080p': (1080, 1920),
            '4k': (2160, 3840)
        },
        '1:1': {
            'name': 'Square (Instagram)',
            '720p': (720, 720),
            '1080p': (1080, 1080),
            '4k': (2160, 2160)
        },
        '4:3': {
            'name': 'Classic TV',
            '720p': (960, 720),
            '1080p': (1440, 1080),
            '4k': (2880, 2160)
        }
    }
    
    def __init__(self):
        """Initialize audio to video generator."""
        self.ffmpeg_path = get_ffmpeg_path()
        self.temp_dir = None
    
    def generate_video_from_audio(
        self,
        audio_path: str,
        output_path: str,
        aspect_ratio: str = '16:9',
        resolution: str = '1080p',
        background_type: str = 'solid',
        background_value: str = '#000000',
        duration: Optional[float] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Generate a video file from an audio file with specified background.
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for output video file
            aspect_ratio: Aspect ratio ('16:9', '9:16', '1:1', '4:3')
            resolution: Resolution ('720p', '1080p', '4k')
            background_type: Type of background ('solid', 'gradient', 'image', 'waveform')
            background_value: Background value (color, gradient colors, or image path)
            duration: Optional duration override
            progress_callback: Progress callback function(current, total, message)
            
        Returns:
            Path to generated video file
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get video dimensions
        dimensions = self._get_dimensions(aspect_ratio, resolution)
        if not dimensions:
            raise ValueError(f"Invalid aspect ratio or resolution: {aspect_ratio}, {resolution}")
        
        width, height = dimensions
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="audio_to_video_")
        
        try:
            # Get audio duration if not provided
            if duration is None:
                duration = self._get_audio_duration(audio_path)
            
            if progress_callback:
                progress_callback(0, 100, "Preparing video generation...")
            
            # Generate background based on type
            if background_type == 'solid':
                video_path = self._generate_solid_background_video(
                    width, height, duration, background_value, output_path,
                    audio_path, progress_callback
                )
            elif background_type == 'gradient':
                video_path = self._generate_gradient_background_video(
                    width, height, duration, background_value, output_path,
                    audio_path, progress_callback
                )
            elif background_type == 'image':
                video_path = self._generate_image_background_video(
                    width, height, duration, background_value, output_path,
                    audio_path, progress_callback
                )
            elif background_type == 'waveform':
                video_path = self._generate_waveform_video(
                    width, height, duration, audio_path, output_path,
                    background_value, progress_callback
                )
            else:
                # Default to solid black
                video_path = self._generate_solid_background_video(
                    width, height, duration, '#000000', output_path,
                    audio_path, progress_callback
                )
            
            if progress_callback:
                progress_callback(100, 100, "Video generation complete!")
            
            return video_path
            
        finally:
            # Clean up temporary directory
            self._cleanup_temp_dir()
    
    def _get_dimensions(self, aspect_ratio: str, resolution: str) -> Optional[Tuple[int, int]]:
        """Get video dimensions for aspect ratio and resolution."""
        if aspect_ratio in self.ASPECT_RATIOS:
            return self.ASPECT_RATIOS[aspect_ratio].get(resolution)
        return None
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except:
            # Default to 60 seconds if can't determine
            return 60.0
    
    def _generate_solid_background_video(
        self, width: int, height: int, duration: float,
        color: str, output_path: str, audio_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Generate video with solid color background."""
        # Convert hex color to FFmpeg format
        if color.startswith('#'):
            color = color[1:]
        
        if progress_callback:
            progress_callback(20, 100, "Creating solid background video...")
        
        # FFmpeg command to create video with solid color and audio
        cmd = [
            self.ffmpeg_path,
            '-f', 'lavfi',
            '-i', f'color=c=0x{color}:s={width}x{height}:d={duration}',
            '-i', audio_path,
            '-shortest',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        # Run FFmpeg with progress monitoring
        self._run_ffmpeg_with_progress(cmd, duration, progress_callback, 20, 80)
        
        return output_path
    
    def _generate_gradient_background_video(
        self, width: int, height: int, duration: float,
        gradient_value: str, output_path: str, audio_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Generate video with gradient background."""
        # Parse gradient colors (format: "#color1,#color2")
        colors = gradient_value.split(',')
        if len(colors) < 2:
            colors = ['#000000', '#333333']
        
        color1 = colors[0].strip().replace('#', '')
        color2 = colors[1].strip().replace('#', '')
        
        if progress_callback:
            progress_callback(20, 100, "Creating gradient background video...")
        
        # Create gradient filter
        gradient_filter = (
            f"gradients=s={width}x{height}:c0=0x{color1}:c1=0x{color2}:"
            f"x0=0:y0=0:x1=0:y1={height}:d={duration}"
        )
        
        cmd = [
            self.ffmpeg_path,
            '-f', 'lavfi',
            '-i', gradient_filter,
            '-i', audio_path,
            '-shortest',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        self._run_ffmpeg_with_progress(cmd, duration, progress_callback, 20, 80)
        
        return output_path
    
    def _generate_image_background_video(
        self, width: int, height: int, duration: float,
        image_path: str, output_path: str, audio_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Generate video with image background."""
        if not os.path.exists(image_path):
            # Fallback to solid color if image not found
            return self._generate_solid_background_video(
                width, height, duration, '#000000', output_path,
                audio_path, progress_callback
            )
        
        if progress_callback:
            progress_callback(20, 100, "Creating image background video...")
        
        # FFmpeg command to create video from image
        cmd = [
            self.ffmpeg_path,
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
                   f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
            '-shortest',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        self._run_ffmpeg_with_progress(cmd, duration, progress_callback, 20, 80)
        
        return output_path
    
    def _generate_waveform_video(
        self, width: int, height: int, duration: float,
        audio_path: str, output_path: str, bg_color: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Generate video with audio waveform visualization."""
        if bg_color.startswith('#'):
            bg_color = bg_color[1:]
        
        if progress_callback:
            progress_callback(20, 100, "Creating waveform visualization...")
        
        # Create waveform visualization
        waveform_filter = (
            f"showwaves=s={width}x{height}:mode=cline:rate=25:"
            f"colors=white@0.8,format=yuv420p"
        )
        
        cmd = [
            self.ffmpeg_path,
            '-i', audio_path,
            '-filter_complex',
            f'[0:a]{waveform_filter},drawbox=0:0:{width}:{height}:0x{bg_color}:fill[v]',
            '-map', '[v]',
            '-map', '0:a',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-y',
            output_path
        ]
        
        self._run_ffmpeg_with_progress(cmd, duration, progress_callback, 20, 80)
        
        return output_path
    
    def _run_ffmpeg_with_progress(
        self, cmd: list, duration: float,
        progress_callback: Optional[callable],
        start_percent: int, end_percent: int
    ):
        """Run FFmpeg command with progress monitoring."""
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            if line and progress_callback:
                # Parse FFmpeg progress
                if 'time=' in line:
                    try:
                        time_str = line.split('time=')[1].split()[0]
                        current_time = self._parse_time_string(time_str)
                        progress = min(current_time / duration, 1.0)
                        
                        current_percent = start_percent + int(progress * (end_percent - start_percent))
                        progress_callback(current_percent, 100, "Generating video...")
                    except:
                        pass
        
        return_code = process.wait()
        if return_code != 0:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"FFmpeg failed with return code {return_code}: {stderr}")
    
    def _parse_time_string(self, time_str: str) -> float:
        """Parse FFmpeg time string to seconds."""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return 0.0
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def get_aspect_ratio_info(self) -> Dict[str, Dict]:
        """Get information about available aspect ratios."""
        return {
            ratio: {
                'name': info['name'],
                'resolutions': [res for res in info.keys() if res != 'name']
            }
            for ratio, info in self.ASPECT_RATIOS.items()
        }