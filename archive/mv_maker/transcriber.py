"""Speech-to-text transcription module using ElevenLabs."""

import os
import sys
import warnings
import requests
import time
import json
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from absolute path to handle direct script execution
try:
    from .utils import safe_print, get_optimal_device, check_cuda_available
    from .config_manager import get_mv_maker_config
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import safe_print, get_optimal_device, check_cuda_available
    from mv_maker.config_manager import get_mv_maker_config

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

class Transcriber:
    """Handles speech-to-text transcription using ElevenLabs API or fallback service."""
    
    def __init__(self, api_key=None, use_fallback=False):
        """
        Initialize transcriber with ElevenLabs API or fallback service.
        
        Args:
            api_key: ElevenLabs API key (if not provided, reads from env/config)
            use_fallback: Force use of fallback transcriber
        """
        self.config = get_mv_maker_config()
        
        # Get API key from various sources
        self.api_key = (
            api_key or 
            os.environ.get('ELEVENLABS_API_KEY') or
            self.config.get('elevenlabs_api_key', '')
        )
        
        # Check if we should use fallback
        self.use_fallback = use_fallback or not self.api_key
        
        if self.use_fallback:
            safe_print("No ElevenLabs API key found. Using fallback transcription service.")
            # Import fallback transcriber
            try:
                from .whisper_transcriber import WhisperTranscriber
            except ImportError:
                from mv_maker.whisper_transcriber import WhisperTranscriber
            self.fallback_transcriber = WhisperTranscriber()
        elif not self.api_key:
            raise ValueError(
                "ElevenLabs API key not found. Please set ELEVENLABS_API_KEY "
                "environment variable or add 'elevenlabs_api_key' to config."
            )
        
        # Only set up ElevenLabs stuff if not using fallback
        if not self.use_fallback:
            # API endpoints
            self.base_url = "https://api.elevenlabs.io/v1"
            self.transcribe_url = f"{self.base_url}/speech-to-text/convert"
            
            # Model configuration
            self.model_id = self.config.get('elevenlabs_model', 'scribe_v1')
            
            # Headers for API requests
            self.headers = {
                "xi-api-key": self.api_key
            }
    
    def load_model(self, progress_callback=None):
        """Compatibility method - ElevenLabs uses cloud API, no local model loading needed."""
        if self.use_fallback:
            if progress_callback:
                progress_callback(100, 100, "Fallback transcriber ready")
            safe_print("Using fallback transcription service")
        else:
            if progress_callback:
                progress_callback(100, 100, "ElevenLabs API ready")
            safe_print("Using ElevenLabs cloud API for transcription")
    
    def transcribe(self, audio_path, language=None, initial_prompt=None,
                  progress_callback=None, task='transcribe'):
        """
        Transcribe audio file to text with timestamps using ElevenLabs API or fallback.
        
        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
            initial_prompt: Not used by ElevenLabs API
            progress_callback: Callback for progress updates
            task: 'transcribe' only (ElevenLabs doesn't support translation)
            
        Returns:
            Dictionary with transcription results including segments
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Use fallback if configured
        if self.use_fallback:
            return self.fallback_transcriber.transcribe_audio(
                audio_path, language, progress_callback
            )
        
        if task != 'transcribe':
            safe_print("Warning: ElevenLabs only supports transcription, not translation")
        
        try:
            if progress_callback:
                progress_callback(0, 100, "Uploading audio to ElevenLabs...")
            
            safe_print(f"Transcribing audio with ElevenLabs: {Path(audio_path).name}")
            
            # Prepare the request
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'file': (Path(audio_path).name, audio_file, 'audio/wav')
                }
                
                # Build parameters
                data = {
                    'model_id': self.model_id,
                    'audio_events': str(self.config.get('audio_events', False)).lower(),
                    'diarize': str(self.config.get('diarize_speakers', True)).lower(),
                    'timestamps_granularity': 'word'  # Always use word-level for captions
                }
                
                # Add language if specified
                if language and language != 'auto':
                    data['language_code'] = language
                
                # Add speaker detection if enabled
                if self.config.get('detect_speakers', True):
                    data['num_speakers'] = self.config.get('max_speakers', 32)
                
                if progress_callback:
                    progress_callback(20, 100, "Processing audio with ElevenLabs...")
                
                # Make the API request
                response = requests.post(
                    self.transcribe_url,
                    headers=self.headers,
                    files=files,
                    data=data
                )
                
                # Check for errors
                if response.status_code != 200:
                    error_msg = f"ElevenLabs API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'detail' in error_data:
                            error_msg += f" - {error_data['detail']}"
                    except:
                        error_msg += f" - {response.text}"
                    raise RuntimeError(error_msg)
                
                if progress_callback:
                    progress_callback(80, 100, "Processing transcription results...")
                
                # Parse response
                result = response.json()
                
                # Convert ElevenLabs format to our standard format
                segments = self._convert_elevenlabs_segments(result)
                
                if progress_callback:
                    progress_callback(100, 100, "Transcription complete")
                
                # Build return structure
                full_text = ' '.join(seg['text'] for seg in segments)
                detected_language = result.get('language_code', language or 'en')
                
                return {
                    'text': full_text,
                    'segments': segments,
                    'language': detected_language,
                    'duration': segments[-1]['end'] if segments else 0,
                    'speakers': result.get('speakers', [])
                }
                
        except Exception as e:
            safe_print(f"Error during ElevenLabs transcription: {e}")
            raise
    
    def _convert_elevenlabs_segments(self, api_result):
        """Convert ElevenLabs API response to our segment format."""
        segments = []
        
        # ElevenLabs returns different formats based on parameters
        if 'words' in api_result:
            # Word-level timestamps
            current_segment = None
            segment_id = 0
            
            for word_data in api_result['words']:
                word = word_data.get('word', '')
                start = word_data.get('start_time', 0) / 1000.0  # Convert ms to seconds
                end = word_data.get('end_time', 0) / 1000.0
                speaker = word_data.get('speaker')
                
                # Group words into segments (by sentence or time gaps)
                if self._should_start_new_segment(current_segment, word, start):
                    if current_segment:
                        segments.append(current_segment)
                    
                    current_segment = {
                        'id': segment_id,
                        'start': start,
                        'end': end,
                        'text': word,
                        'words': [{
                            'word': word,
                            'start': start,
                            'end': end,
                            'speaker': speaker
                        }],
                        'speaker': speaker
                    }
                    segment_id += 1
                else:
                    # Add to current segment
                    current_segment['text'] += ' ' + word
                    current_segment['end'] = end
                    current_segment['words'].append({
                        'word': word,
                        'start': start,
                        'end': end,
                        'speaker': speaker
                    })
            
            # Add final segment
            if current_segment:
                segments.append(current_segment)
                
        elif 'segments' in api_result:
            # Segment-level response
            for idx, seg in enumerate(api_result['segments']):
                segments.append({
                    'id': idx,
                    'start': seg.get('start_time', 0) / 1000.0,
                    'end': seg.get('end_time', 0) / 1000.0,
                    'text': seg.get('text', '').strip(),
                    'words': [],  # No word-level data in this format
                    'speaker': seg.get('speaker')
                })
        else:
            # Fallback for simple text response
            text = api_result.get('text', '')
            if text:
                segments.append({
                    'id': 0,
                    'start': 0.0,
                    'end': api_result.get('duration', 10.0) / 1000.0,
                    'text': text,
                    'words': []
                })
        
        return segments
    
    def _should_start_new_segment(self, current_segment, word, start_time):
        """Determine if a new segment should be started."""
        if not current_segment:
            return True
        
        # Start new segment after sentence-ending punctuation
        if current_segment['text'].rstrip().endswith(('.', '!', '?')):
            return True
        
        # Start new segment if there's a long pause (> 1 second)
        if start_time - current_segment['end'] > 1.0:
            return True
        
        # Start new segment if current is getting too long
        if len(current_segment['text']) > 100:
            return True
        
        return False
    
    def transcribe_with_fallback(self, audio_path, language=None, 
                               progress_callback=None):
        """
        Transcribe using ElevenLabs with fallback to local transcriber if API fails.
        """
        try:
            # Try ElevenLabs first
            return self.transcribe(audio_path, language, progress_callback=progress_callback)
            
        except Exception as elevenlabs_error:
            safe_print(f"ElevenLabs failed, trying fallback transcription service: {elevenlabs_error}")
            
            # Try fallback transcriber
            try:
                if progress_callback:
                    progress_callback(0, 100, "Using fallback transcription service...")
                
                # Import fallback transcriber
                try:
                    from .whisper_transcriber import WhisperTranscriber
                except ImportError:
                    from mv_maker.whisper_transcriber import WhisperTranscriber
                
                fallback_transcriber = WhisperTranscriber()
                
                # Transcribe using fallback
                result = fallback_transcriber.transcribe_audio(
                    audio_path,
                    language=language if language != 'auto' else None,
                    progress_callback=progress_callback
                )
                
                if progress_callback:
                    progress_callback(100, 100, "Fallback transcription complete")
                
                safe_print("Successfully completed transcription using fallback service")
                return result
                
            except Exception as fallback_error:
                safe_print(f"Fallback transcription also failed: {fallback_error}")
                raise elevenlabs_error  # Re-raise original error
    
    def detect_language(self, audio_path):
        """
        Detect the language of the audio using ElevenLabs.
        
        Note: ElevenLabs auto-detects language when not specified.
        This method performs a partial transcription to detect language.
        """
        try:
            # Do a quick transcription without specifying language
            result = self.transcribe(audio_path, language=None)
            detected_language = result.get('language', 'en')
            
            safe_print(f"Detected language: {detected_language}")
            return detected_language
            
        except Exception as e:
            safe_print(f"Error detecting language: {e}")
            return 'en'  # Default to English
    
    def get_model_info(self):
        """Get information about the ElevenLabs configuration."""
        return {
            'service': 'ElevenLabs',
            'model': self.model_id,
            'api_configured': bool(self.api_key),
            'features': {
                'multi_speaker': True,
                'audio_events': self.config.get('audio_events', False),
                'diarization': self.config.get('diarize_speakers', True),
                'word_timestamps': True,
                'max_file_size': '1GB',
                'max_duration': '4.5 hours'
            }
        }
    
    def check_api_status(self):
        """Check if ElevenLabs API is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False