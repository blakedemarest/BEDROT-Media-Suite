# -*- coding: utf-8 -*-
"""
Transcription Service for Caption Generator.

QThread-based service for ElevenLabs Speech-to-Text transcription.
Extracted from batch_worker.py for reuse in both batch and single-file modes.
"""

import os
import sys
from io import BytesIO
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.env_loader import load_environment, get_env_var
from transcriber_tool.subtitle_generator import words_to_segments, generate_srt


class TranscriptionService(QThread):
    """
    QThread service for transcribing audio files to SRT subtitles.

    Uses ElevenLabs Speech-to-Text API for transcription.
    Can be used standalone or integrated with batch processing.

    Signals:
        log_signal(str): Log messages for display
        transcription_started(str): Emitted when transcription begins (filename)
        transcription_completed(str, str): Success - (audio_path, srt_path)
        transcription_failed(str, str): Failure - (audio_path, error_message)
    """

    log_signal = pyqtSignal(str)
    transcription_started = pyqtSignal(str)  # audio filename
    transcription_completed = pyqtSignal(str, str)  # audio_path, srt_path
    transcription_failed = pyqtSignal(str, str)  # audio_path, error_msg

    def __init__(self, audio_path: str, output_folder: str,
                 max_words_per_segment: int = 1, parent=None):
        """
        Initialize the transcription service.

        Args:
            audio_path: Path to the audio file to transcribe
            output_folder: Folder where SRT files will be saved
            max_words_per_segment: Maximum words per subtitle segment (1-20)
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.audio_path = audio_path
        self.output_folder = output_folder
        self.max_words_per_segment = max_words_per_segment

        # Cancel flag
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the transcription."""
        self._cancelled = True

    def run(self):
        """Main transcription thread."""
        filename = os.path.basename(self.audio_path)
        self.transcription_started.emit(filename)
        self.log_signal.emit(f"[TRANSCRIBE] Starting transcription: {filename}")

        try:
            srt_path = self._transcribe_and_generate_subtitles()

            if srt_path:
                self.transcription_completed.emit(self.audio_path, srt_path)
                self.log_signal.emit(f"[OK] Transcription complete: {os.path.basename(srt_path)}")
            else:
                self.transcription_failed.emit(self.audio_path, "Transcription returned no result")

        except Exception as e:
            error_msg = str(e)
            self.transcription_failed.emit(self.audio_path, error_msg)
            self.log_signal.emit(f"[ERROR] Transcription failed: {error_msg}")

    def _transcribe_and_generate_subtitles(self) -> Optional[str]:
        """
        Transcribe audio and generate SRT file.

        Returns:
            Path to SRT file or None if failed
        """
        # Load environment and get API key
        load_environment()
        api_key = get_env_var("ELEVENLABS_API_KEY")

        if not api_key:
            self.log_signal.emit("[ERROR] ELEVENLABS_API_KEY not set in environment variables")
            self.log_signal.emit("[ERROR] Please add ELEVENLABS_API_KEY=your_key to .env file")
            self.transcription_failed.emit(self.audio_path, "API key not configured")
            return None

        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=api_key)
        except ImportError:
            self.log_signal.emit("[ERROR] elevenlabs package not installed")
            self.log_signal.emit("[ERROR] Run: pip install elevenlabs")
            self.transcription_failed.emit(self.audio_path, "elevenlabs package not installed")
            return None

        # Convert to MP3 if needed
        mp3_path = self._ensure_mp3()
        if not mp3_path:
            return None

        if self._cancelled:
            self.log_signal.emit("[TRANSCRIBE] Cancelled by user")
            return None

        try:
            # Read audio file
            with open(mp3_path, "rb") as f:
                audio_data = BytesIO(f.read())

            self.log_signal.emit("[TRANSCRIBE] Sending to ElevenLabs API...")

            # Call ElevenLabs API
            transcription = client.speech_to_text.convert(
                file=audio_data,
                model_id="scribe_v1",
                tag_audio_events=True,
                language_code="eng",
                diarize=True,
                timestamps_granularity="word"
            )

            if self._cancelled:
                self.log_signal.emit("[TRANSCRIBE] Cancelled by user")
                return None

            # Extract words from response
            words = getattr(transcription, 'words', []) or []

            if not words:
                self.log_signal.emit("[ERROR] No words returned from transcription")
                self.transcription_failed.emit(self.audio_path, "No words in transcription result")
                return None

            self.log_signal.emit(f"[TRANSCRIBE] Received {len(words)} words from API")

            # Generate SRT
            base_name = os.path.splitext(os.path.basename(self.audio_path))[0]

            # Ensure output folder exists
            os.makedirs(self.output_folder, exist_ok=True)

            srt_path = os.path.join(self.output_folder, f"{base_name}.srt")

            # Generate segments with configurable words per segment
            self.log_signal.emit(
                f"[TRANSCRIBE] Grouping into segments (max {self.max_words_per_segment} words each)"
            )
            segments = words_to_segments(words, max_words=self.max_words_per_segment)

            # Generate SRT
            if generate_srt(segments, srt_path):
                self.log_signal.emit(f"[OK] Saved SRT: {os.path.basename(srt_path)}")
            else:
                self.log_signal.emit("[ERROR] Failed to generate SRT file")
                self.transcription_failed.emit(self.audio_path, "Failed to write SRT file")
                return None

            return srt_path

        except Exception as e:
            self.log_signal.emit(f"[ERROR] Transcription error: {e}")
            self.transcription_failed.emit(self.audio_path, str(e))
            return None

    def _ensure_mp3(self) -> Optional[str]:
        """
        Convert audio to MP3 if needed for ElevenLabs API.

        Returns:
            Path to MP3 file or None if conversion failed
        """
        ext = os.path.splitext(self.audio_path)[1].lower()

        # Already MP3
        if ext == '.mp3':
            return self.audio_path

        base = os.path.splitext(self.audio_path)[0]
        mp3_path = base + ".mp3"

        self.log_signal.emit(f"[CONVERT] Converting {ext.upper()} to MP3...")

        try:
            if ext in ['.wav', '.m4a', '.flac', '.aac']:
                from pydub import AudioSegment

                if ext == '.wav':
                    audio = AudioSegment.from_wav(self.audio_path)
                elif ext == '.m4a':
                    audio = AudioSegment.from_file(self.audio_path, format="m4a")
                elif ext == '.flac':
                    audio = AudioSegment.from_file(self.audio_path, format="flac")
                elif ext == '.aac':
                    audio = AudioSegment.from_file(self.audio_path, format="aac")
                else:
                    audio = AudioSegment.from_file(self.audio_path)

                audio.export(mp3_path, format="mp3")
                self.log_signal.emit(f"[OK] Conversion complete: {os.path.basename(mp3_path)}")
                return mp3_path

            else:
                self.log_signal.emit(f"[ERROR] Unsupported audio format: {ext}")
                self.transcription_failed.emit(
                    self.audio_path, f"Unsupported audio format: {ext}"
                )
                return None

        except ImportError:
            self.log_signal.emit("[ERROR] pydub not installed for audio conversion")
            self.transcription_failed.emit(
                self.audio_path, "pydub not installed for audio conversion"
            )
            return None
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Conversion error: {e}")
            self.transcription_failed.emit(self.audio_path, f"Audio conversion error: {e}")
            return None
