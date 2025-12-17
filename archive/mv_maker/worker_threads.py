"""Background worker threads for MV Maker."""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt5.QtCore import QThread, pyqtSignal

# Import from absolute path to handle direct script execution
try:
    from .audio_extractor import AudioExtractor
    from .transcriber import Transcriber
    from .caption_generator import CaptionGenerator
    from .caption_exporter import CaptionExporter
    from .video_processor import VideoProcessor
    from .audio_to_video_generator import AudioToVideoGenerator
    from .utils import safe_print, cleanup_temp_directory, estimate_processing_time
except ImportError:
    # Fallback for direct script execution
    from mv_maker.audio_extractor import AudioExtractor
    from mv_maker.transcriber import Transcriber
    from mv_maker.caption_generator import CaptionGenerator
    from mv_maker.caption_exporter import CaptionExporter
    from mv_maker.video_processor import VideoProcessor
    from mv_maker.audio_to_video_generator import AudioToVideoGenerator
    from mv_maker.utils import safe_print, cleanup_temp_directory, estimate_processing_time

class TranscriptionWorker(QThread):
    """Worker thread for video transcription and caption generation."""
    
    # Signals
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_completed = pyqtSignal(dict)  # result dictionary
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, parent=None):
        """Initialize transcription worker."""
        super().__init__(parent)
        self.video_path = None
        self.output_path = None
        self.model_size = 'base'
        self.language = 'auto'
        self.output_formats = ['srt', 'vtt']
        self.device = 'auto'
        self.temp_dir = None
        self.should_cancel = False
    
    def setup(self, video_path, output_path, model_size='base', 
              language='auto', output_formats=None, device='auto',
              font_family='sans', config=None):
        """
        Setup worker for transcription task.
        
        Args:
            video_path: Path to video file
            output_path: Base path for output files
            model_size: Whisper model size
            language: Language code or 'auto'
            output_formats: List of output formats
            device: Device to use for processing
            font_family: Font family for captions
            config: Configuration object
        """
        self.video_path = video_path
        self.output_path = output_path
        self.model_size = model_size
        self.language = language
        self.output_formats = output_formats or ['srt', 'vtt']
        self.device = device
        self.font_family = font_family
        self.config = config
        self.should_cancel = False
    
    def cancel(self):
        """Request cancellation of the operation."""
        self.should_cancel = True
    
    def run(self):
        """Run the transcription process."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="caption_gen_")
            
            # Check if input is audio-only file
            extractor = AudioExtractor()
            is_audio_only = extractor.is_audio_file(self.video_path)
            video_for_overlay = self.video_path
            
            # Step 1: Handle audio extraction or video generation
            if self.should_cancel:
                return
            
            if is_audio_only:
                # For audio files, we need to generate a video first if MP4 output is requested
                self.progress_updated.emit(0, 100, "Processing audio file...")
                audio_path = self.video_path  # Use audio directly
                
                # Check if MP4 output is requested
                if 'mp4' in self.output_formats or 'mp4_overlay' in self.output_formats:
                    self.progress_updated.emit(5, 100, "Generating video from audio...")
                    
                    # Generate video from audio
                    audio_to_video = AudioToVideoGenerator()
                    temp_video_path = os.path.join(self.temp_dir, "generated_video.mp4")
                    
                    # Get settings from config
                    aspect_ratio = self.config.get('aspect_ratio', '16:9') if self.config else '16:9'
                    resolution = self.config.get('video_resolution', '1080p') if self.config else '1080p'
                    bg_type = self.config.get('background_type', 'solid') if self.config else 'solid'
                    bg_value = self.config.get('background_value', '#000000') if self.config else '#000000'
                    
                    def video_gen_progress(current, total, message):
                        if self.should_cancel:
                            raise InterruptedError("Cancelled by user")
                        # Map to 0-15% range
                        progress = int((current / total) * 15)
                        self.progress_updated.emit(progress, 100, message)
                    
                    video_for_overlay = audio_to_video.generate_video_from_audio(
                        audio_path,
                        temp_video_path,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        background_type=bg_type,
                        background_value=bg_value,
                        progress_callback=video_gen_progress
                    )
            else:
                # For video files, extract audio as usual
                self.progress_updated.emit(0, 100, "Extracting audio from video...")
                audio_path = os.path.join(self.temp_dir, "extracted_audio.wav")
                
                def audio_progress(current, total, message):
                    if self.should_cancel:
                        raise InterruptedError("Cancelled by user")
                    self.progress_updated.emit(current, total, message)
                
                audio_path = extractor.extract_audio(
                    self.video_path, 
                    audio_path,
                    progress_callback=audio_progress
                )
            
            # Step 2: Load model and transcribe
            if self.should_cancel:
                return
            
            self.progress_updated.emit(20, 100, "Initializing transcription service...")
            
            # Initialize transcriber (ElevenLabs by default)
            transcriber = Transcriber()
            
            def model_progress(current, total, message):
                if self.should_cancel:
                    raise InterruptedError("Cancelled by user")
                # Map to 20-40% range
                progress = 20 + int((current / total) * 20)
                self.progress_updated.emit(progress, 100, message)
            
            transcriber.load_model(progress_callback=model_progress)
            
            # Detect language if auto
            if self.language == 'auto':
                self.progress_updated.emit(40, 100, "Detecting language...")
                detected_language = transcriber.detect_language(audio_path)
                safe_print(f"Detected language: {detected_language}")
            else:
                detected_language = self.language
            
            # Transcribe
            if self.should_cancel:
                return
            
            self.progress_updated.emit(45, 100, "Transcribing audio...")
            
            def transcribe_progress(current, total, message):
                if self.should_cancel:
                    raise InterruptedError("Cancelled by user")
                # Map to 45-70% range
                progress = 45 + int((current / total) * 25)
                self.progress_updated.emit(progress, 100, message)
            
            transcription_result = transcriber.transcribe_with_fallback(
                audio_path,
                language=detected_language,
                progress_callback=transcribe_progress
            )
            
            # Step 3: Generate captions
            if self.should_cancel:
                return
            
            self.progress_updated.emit(70, 100, "Generating captions...")
            
            generator = CaptionGenerator()
            
            def caption_progress(current, total, message):
                if self.should_cancel:
                    raise InterruptedError("Cancelled by user")
                # Map to 70-85% range
                progress = 70 + int((current / total) * 15)
                self.progress_updated.emit(progress, 100, message)
            
            captions = generator.generate_captions(
                transcription_result,
                progress_callback=caption_progress
            )
            
            # Add styling
            captions = generator.add_caption_styling(captions)
            
            # Step 4: Export captions
            if self.should_cancel:
                return
            
            self.progress_updated.emit(85, 100, "Exporting caption files...")
            
            exporter = CaptionExporter()
            exported_files = {}
            
            # Export requested formats
            if 'srt' in self.output_formats:
                srt_path = f"{self.output_path}.srt"
                exporter.export_srt(captions, srt_path)
                exported_files['srt'] = srt_path
            
            if 'vtt' in self.output_formats:
                vtt_path = f"{self.output_path}.vtt"
                exporter.export_webvtt(captions, vtt_path)
                exported_files['vtt'] = vtt_path
            
            if 'simple' in self.output_formats:
                simple_path = f"{self.output_path}.txt"
                exporter.export_simple_format(captions, simple_path)
                exported_files['simple'] = simple_path
            
            if 'json' in self.output_formats:
                json_path = f"{self.output_path}.json"
                exporter.export_to_json(captions, json_path)
                exported_files['json'] = json_path
            
            # Generate MP4 overlay if requested
            if 'mp4_overlay' in self.output_formats:
                if self.should_cancel:
                    return
                
                self.progress_updated.emit(90, 100, "Generating MP4 overlay...")
                
                # Create video processor and generate overlay
                video_processor = VideoProcessor()
                
                # Set font family in config
                if self.config:
                    self.config.set('font_family', self.font_family)
                    overlay_config = self.config.config
                else:
                    # Fallback config
                    overlay_config = {
                        'font_family': self.font_family,
                        'font_size': 24,
                        'font_color': '#FFFFFF',
                        'background_opacity': 0.7,
                        'position': 'bottom',
                        'subtitle_border': 2,
                        'subtitle_shadow': True,
                        'mp4_overlay_quality': 'high',
                        'mp4_overlay_bitrate': '2M'
                    }
                
                def overlay_progress(current, total, message):
                    if self.should_cancel:
                        raise InterruptedError("Cancelled by user")
                    # Map overlay progress to 90-98% range
                    progress = 90 + int((current / total) * 8)
                    self.progress_updated.emit(progress, 100, message)
                
                try:
                    # Get video duration for progress tracking
                    video_processor.get_video_duration(self.video_path)
                    
                    overlay_path = f"{self.output_path}_captioned.mp4"
                    video_processor.generate_mp4_overlay(
                        video_for_overlay,  # Use generated video for audio files
                        captions,
                        overlay_path,
                        overlay_config,
                        progress_callback=overlay_progress
                    )
                    exported_files['mp4_overlay'] = overlay_path
                    
                except Exception as overlay_error:
                    safe_print(f"MP4 overlay generation failed: {overlay_error}")
                    # Don't fail the entire process, just skip overlay
                    exported_files['mp4_overlay_error'] = str(overlay_error)
            
            # Generate preview HTML if requested
            if 'preview' in self.output_formats and exported_files:
                self.progress_updated.emit(98, 100, "Generating preview...")
                html_path = f"{self.output_path}_preview.html"
                exporter.generate_preview_html(
                    self.video_path,
                    exported_files,
                    html_path
                )
                exported_files['preview'] = html_path
            
            # Get statistics
            stats = generator.get_statistics(captions)
            
            # Clean up
            cleanup_temp_directory(self.temp_dir)
            
            # Complete
            self.progress_updated.emit(100, 100, "Transcription complete!")
            
            result = {
                'success': True,
                'video_path': self.video_path,
                'output_files': exported_files,
                'language': detected_language,
                'caption_count': len(captions),
                'statistics': stats,
                'transcription_text': transcription_result.get('text', '')
            }
            
            self.operation_completed.emit(result)
            
        except InterruptedError:
            safe_print("Operation cancelled by user")
            if self.temp_dir:
                cleanup_temp_directory(self.temp_dir)
            
        except Exception as e:
            safe_print(f"Error in transcription worker: {e}")
            if self.temp_dir:
                cleanup_temp_directory(self.temp_dir)
            self.error_occurred.emit(str(e))


class ModelDownloadWorker(QThread):
    """Worker thread for downloading Whisper models."""
    
    progress_updated = pyqtSignal(int, int, str)
    download_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, parent=None):
        """Initialize model download worker."""
        super().__init__(parent)
        self.model_size = 'base'
        self.should_cancel = False
    
    def setup(self, model_size):
        """Setup download for specified model."""
        self.model_size = model_size
        self.should_cancel = False
    
    def cancel(self):
        """Request cancellation."""
        self.should_cancel = True
    
    def run(self):
        """Download the model."""
        try:
            self.progress_updated.emit(0, 100, f"Downloading {self.model_size} model...")
            
            # Import whisper
            import whisper
            
            # This will download the model if not already cached
            model = whisper.load_model(self.model_size)
            
            if self.should_cancel:
                return
            
            self.progress_updated.emit(100, 100, "Model downloaded successfully")
            self.download_completed.emit(True, f"{self.model_size} model ready")
            
        except Exception as e:
            self.download_completed.emit(False, f"Error downloading model: {str(e)}")


class BatchProcessingWorker(QThread):
    """Worker thread for batch processing multiple videos."""
    
    progress_updated = pyqtSignal(int, int, str)
    file_completed = pyqtSignal(str, bool, str)  # file_path, success, message
    batch_completed = pyqtSignal(int, int)  # successful, failed
    
    def __init__(self, parent=None):
        """Initialize batch processing worker."""
        super().__init__(parent)
        self.video_files = []
        self.model_size = 'base'
        self.language = 'auto'
        self.output_formats = ['srt', 'vtt']
        self.device = 'auto'
        self.should_cancel = False
    
    def setup(self, video_files, model_size='base', language='auto',
              output_formats=None, device='auto'):
        """Setup batch processing."""
        self.video_files = video_files
        self.model_size = model_size
        self.language = language
        self.output_formats = output_formats or ['srt', 'vtt']
        self.device = device
        self.should_cancel = False
    
    def cancel(self):
        """Request cancellation."""
        self.should_cancel = True
    
    def run(self):
        """Process all videos in batch."""
        successful = 0
        failed = 0
        total_files = len(self.video_files)
        
        # Initialize services once for all files
        try:
            self.progress_updated.emit(0, 100, "Initializing transcription service for batch processing...")
            
            transcriber = Transcriber()
            transcriber.load_model()  # Compatibility call (no-op for ElevenLabs)
            
            extractor = AudioExtractor()
            generator = CaptionGenerator()
            exporter = CaptionExporter()
            
        except Exception as e:
            self.progress_updated.emit(0, 100, f"Failed to initialize: {str(e)}")
            self.batch_completed.emit(0, total_files)
            return
        
        # Process each file
        for i, video_path in enumerate(self.video_files):
            if self.should_cancel:
                break
            
            file_name = Path(video_path).name
            progress_base = int((i / total_files) * 100)
            
            try:
                self.progress_updated.emit(
                    progress_base, 100,
                    f"Processing {i+1}/{total_files}: {file_name}"
                )
                
                # Create temp directory for this file
                temp_dir = tempfile.mkdtemp(prefix="batch_caption_")
                
                # Extract audio
                audio_path = os.path.join(temp_dir, "audio.wav")
                audio_path = extractor.extract_audio(video_path, audio_path)
                
                # Transcribe
                if self.language == 'auto':
                    detected_language = transcriber.detect_language(audio_path)
                else:
                    detected_language = self.language
                
                transcription_result = transcriber.transcribe_with_fallback(
                    audio_path,
                    language=detected_language
                )
                
                # Generate captions
                captions = generator.generate_captions(transcription_result)
                captions = generator.add_caption_styling(captions)
                
                # Export
                base_output = str(Path(video_path).with_suffix(''))
                
                if 'srt' in self.output_formats:
                    exporter.export_srt(captions, f"{base_output}.srt")
                
                if 'vtt' in self.output_formats:
                    exporter.export_webvtt(captions, f"{base_output}.vtt")
                
                if 'simple' in self.output_formats:
                    exporter.export_simple_format(captions, f"{base_output}.txt")
                
                # Clean up
                cleanup_temp_directory(temp_dir)
                
                successful += 1
                self.file_completed.emit(video_path, True, "Completed successfully")
                
            except Exception as e:
                failed += 1
                self.file_completed.emit(video_path, False, str(e))
                safe_print(f"Error processing {file_name}: {e}")
        
        self.progress_updated.emit(100, 100, "Batch processing complete")
        self.batch_completed.emit(successful, failed)