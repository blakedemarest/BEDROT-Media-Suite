"""Fallback transcriber using free speech recognition."""

import os
import sys
import warnings
import json
import speech_recognition as sr
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import make_chunks

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from absolute path to handle direct script execution
try:
    from .utils import safe_print
    from .config_manager import get_mv_maker_config
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import safe_print
    from mv_maker.config_manager import get_mv_maker_config

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

class WhisperTranscriber:
    """Fallback transcriber using Google Speech Recognition (free)."""
    
    def __init__(self):
        """Initialize the fallback transcriber."""
        self.config = get_mv_maker_config()
        self.recognizer = sr.Recognizer()
        
        # Configuration
        self.language = self.config.get('language', 'auto')
        self.chunk_length_ms = 30000  # 30 seconds chunks
        
        safe_print("Using free Google Speech Recognition service")
        safe_print("Note: For better accuracy, consider using ElevenLabs API")
    
    def transcribe_audio(self, audio_path, language=None, progress_callback=None):
        """
        Transcribe audio file to text with timestamps.
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
            progress_callback: Progress callback function(current, total, message)
            
        Returns:
            dict: Transcription result with segments and metadata
        """
        try:
            # Load audio file
            safe_print(f"Loading audio file: {audio_path}")
            audio = AudioSegment.from_wav(audio_path)
            
            # Prepare language code
            if language == 'auto' or language is None:
                lang_code = None  # Google will auto-detect
            else:
                # Convert to Google's language code format (e.g., 'en' -> 'en-US')
                lang_code = self._get_google_language_code(language)
            
            # Split audio into chunks
            chunks = make_chunks(audio, self.chunk_length_ms)
            total_chunks = len(chunks)
            
            segments = []
            current_time = 0.0
            
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(i, total_chunks, f"Processing chunk {i+1}/{total_chunks}")
                
                # Export chunk to temporary file
                chunk_path = f"{audio_path}_chunk_{i}.wav"
                chunk.export(chunk_path, format="wav")
                
                try:
                    # Transcribe chunk
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = self.recognizer.record(source)
                        
                        try:
                            # Use Google Speech Recognition
                            text = self.recognizer.recognize_google(
                                audio_data,
                                language=lang_code or 'en-US'
                            )
                            
                            # Create segment
                            chunk_duration = len(chunk) / 1000.0  # Convert to seconds
                            segment = {
                                'start': current_time,
                                'end': current_time + chunk_duration,
                                'text': text.strip(),
                                'words': []  # Google doesn't provide word-level timestamps
                            }
                            
                            if segment['text']:  # Only add non-empty segments
                                segments.append(segment)
                            
                        except sr.UnknownValueError:
                            safe_print(f"Could not understand audio in chunk {i+1}")
                        except sr.RequestError as e:
                            safe_print(f"Error with speech recognition service: {e}")
                    
                finally:
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                
                current_time += len(chunk) / 1000.0
            
            # Prepare result
            result = {
                'text': ' '.join(seg['text'] for seg in segments),
                'segments': segments,
                'language': lang_code or 'unknown',
                'transcription_service': 'google_speech_recognition'
            }
            
            if progress_callback:
                progress_callback(total_chunks, total_chunks, "Transcription complete")
            
            return result
            
        except Exception as e:
            safe_print(f"Error during transcription: {str(e)}")
            raise
    
    def _get_google_language_code(self, language):
        """Convert language code to Google's format."""
        # Common language mappings
        language_map = {
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-BR',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'zh': 'zh-CN',
            'ar': 'ar-SA',
            'hi': 'hi-IN'
        }
        
        return language_map.get(language, language)
    
    def get_supported_languages(self):
        """Get list of supported languages."""
        return {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi'
        }