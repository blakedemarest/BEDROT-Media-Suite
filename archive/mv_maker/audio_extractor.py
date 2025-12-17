"""Audio extraction module for MV Maker."""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from absolute path to handle direct script execution
try:
    from .utils import (
        safe_print, get_ffmpeg_path, run_ffmpeg_command,
        get_video_info, get_audio_duration
    )
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import (
        safe_print, get_ffmpeg_path, run_ffmpeg_command,
        get_video_info, get_audio_duration
    )

class AudioExtractor:
    """Handles audio extraction from video files and direct audio processing."""
    
    def __init__(self):
        """Initialize audio extractor."""
        self.ffmpeg_path = get_ffmpeg_path()
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        self.supported_audio_formats = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma']
        self.supported_formats = self.supported_video_formats + self.supported_audio_formats
    
    def is_supported_format(self, file_path):
        """Check if the file format is supported."""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_formats
    
    def is_audio_file(self, file_path):
        """Check if the file is an audio file."""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_audio_formats
    
    def is_video_file(self, file_path):
        """Check if the file is a video file."""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_video_formats
    
    def extract_audio(self, video_path, output_path=None, audio_format='wav', 
                     progress_callback=None):
        """
        Extract audio from video file or process audio file directly.
        
        Args:
            video_path: Path to input video or audio file
            output_path: Path for output audio file (optional)
            audio_format: Output audio format (wav, mp3, etc.)
            progress_callback: Callback function for progress updates
            
        Returns:
            Path to extracted/processed audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Media file not found: {video_path}")
        
        if not self.is_supported_format(video_path):
            raise ValueError(f"Unsupported media format: {video_path}")
        
        # Check if input is an audio file
        is_audio_input = self.is_audio_file(video_path)
        
        # Generate output path if not provided
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            base_name = Path(video_path).stem
            output_path = os.path.join(temp_dir, f"{base_name}_audio.{audio_format}")
        
        # If input is already an audio file and in the desired format, we might not need to convert
        if is_audio_input:
            input_ext = Path(video_path).suffix.lower()
            desired_ext = f".{audio_format.lower()}"
            
            # If the input is already in the desired format and meets our requirements (16kHz mono)
            # we still need to convert to ensure proper format for transcription
            if progress_callback:
                progress_callback(0, 100, "Processing audio file...")
        else:
            # Get video info for progress tracking
            video_info = get_video_info(video_path)
            duration = video_info.get('duration', 0)
            
            if progress_callback:
                progress_callback(0, 100, "Starting audio extraction...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Build FFmpeg command
        if is_audio_input:
            # For audio files, convert to optimal format for transcription
            command = [
                self.ffmpeg_path,
                '-i', video_path,  # Input audio file
                '-acodec', 'pcm_s16le' if audio_format == 'wav' else 'libmp3lame',  # Audio codec
                '-ar', '16000',  # Sample rate (16kHz is good for speech)
                '-ac', '1',  # Mono audio
                '-y',  # Overwrite output
                output_path
            ]
        else:
            # For video files, extract audio
            command = [
                self.ffmpeg_path,
                '-i', video_path,  # Input file
                '-vn',  # No video
                '-acodec', 'pcm_s16le' if audio_format == 'wav' else 'libmp3lame',  # Audio codec
                '-ar', '16000',  # Sample rate (16kHz is good for speech)
                '-ac', '1',  # Mono audio
                '-y',  # Overwrite output
                output_path
            ]
        
        try:
            # Run extraction/conversion
            if is_audio_input:
                safe_print(f"Processing audio file: {Path(video_path).name}")
            else:
                safe_print(f"Extracting audio from: {Path(video_path).name}")
            
            run_ffmpeg_command(command)
            
            # Verify output file exists
            if not os.path.exists(output_path):
                operation = "Audio processing" if is_audio_input else "Audio extraction"
                raise RuntimeError(f"{operation} failed - output file not created")
            
            # Verify audio duration
            audio_duration = get_audio_duration(output_path)
            if audio_duration == 0:
                operation = "Audio processing" if is_audio_input else "Audio extraction"
                raise RuntimeError(f"{operation} failed - output file has no duration")
            
            if progress_callback:
                operation = "Audio processing" if is_audio_input else "Audio extraction"
                progress_callback(100, 100, f"{operation} complete")
            
            operation = "processed" if is_audio_input else "extracted"
            safe_print(f"Audio {operation} successfully: {output_path}")
            safe_print(f"Duration: {audio_duration:.1f} seconds")
            
            return output_path
            
        except Exception as e:
            operation = "processing" if is_audio_input else "extracting"
            safe_print(f"Error {operation} audio: {e}")
            # Clean up partial output
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise
    
    def extract_audio_segment(self, video_path, start_time, end_time, 
                            output_path=None, audio_format='wav'):
        """
        Extract a specific segment of audio from video.
        
        Args:
            video_path: Path to input video file
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output audio file (optional)
            audio_format: Output audio format
            
        Returns:
            Path to extracted audio segment
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        duration = end_time - start_time
        if duration <= 0:
            raise ValueError("Invalid time range")
        
        # Generate output path if not provided
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            base_name = Path(video_path).stem
            output_path = os.path.join(
                temp_dir, 
                f"{base_name}_segment_{start_time}-{end_time}.{audio_format}"
            )
        
        # Build FFmpeg command
        command = [
            self.ffmpeg_path,
            '-i', video_path,
            '-ss', str(start_time),  # Start time
            '-t', str(duration),  # Duration
            '-vn',  # No video
            '-acodec', 'pcm_s16le' if audio_format == 'wav' else 'libmp3lame',
            '-ar', '16000',  # Sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            output_path
        ]
        
        try:
            run_ffmpeg_command(command)
            return output_path
        except Exception as e:
            safe_print(f"Error extracting audio segment: {e}")
            raise
    
    def get_audio_properties(self, video_path):
        """
        Get audio properties from video file.
        
        Returns:
            Dictionary with audio properties (codec, bitrate, channels, etc.)
        """
        ffprobe_path = get_ffmpeg_path().replace('ffmpeg', 'ffprobe')
        
        command = [
            ffprobe_path,
            '-v', 'error',
            '-select_streams', 'a:0',  # First audio stream
            '-show_entries', 'stream=codec_name,sample_rate,channels,bit_rate',
            '-of', 'json',
            video_path
        ]
        
        try:
            import json
            output = run_ffmpeg_command(command)
            data = json.loads(output)
            
            if 'streams' in data and data['streams']:
                stream = data['streams'][0]
                return {
                    'codec': stream.get('codec_name', 'unknown'),
                    'sample_rate': int(stream.get('sample_rate', 0)),
                    'channels': int(stream.get('channels', 0)),
                    'bit_rate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0
                }
        except Exception as e:
            safe_print(f"Error getting audio properties: {e}")
        
        return {
            'codec': 'unknown',
            'sample_rate': 0,
            'channels': 0,
            'bit_rate': 0
        }
    
    def has_audio_stream(self, video_path):
        """Check if video file has an audio stream."""
        properties = self.get_audio_properties(video_path)
        return properties['channels'] > 0