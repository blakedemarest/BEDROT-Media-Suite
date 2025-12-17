# -*- coding: utf-8 -*-
"""
Batch Worker Module for Caption Generator.

QThread-based worker for batch transcription and caption video generation.
Handles ElevenLabs API integration, SRT generation, and ffmpeg video creation.
"""

import os
import sys
import time
from io import BytesIO
from typing import Dict, List, Optional, Any

from PyQt5.QtCore import QThread, pyqtSignal

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.env_loader import load_environment, get_env_var
from transcriber_tool.subtitle_generator import words_to_segments, generate_srt
from .video_generator import generate_caption_video
from .pairing_history import PairingHistory


class BatchCaptionWorker(QThread):
    """
    Background worker for batch caption video generation.

    Handles:
    - Audio transcription via ElevenLabs API (when needed)
    - SRT subtitle generation
    - Caption video generation via ffmpeg
    - Progress tracking and error handling
    """

    # Signal definitions
    log_signal = pyqtSignal(str)
    batch_started = pyqtSignal(int)  # Total file count
    progress_signal = pyqtSignal(int, int, str)  # current, total, filename
    transcription_started = pyqtSignal(str)  # filename
    transcription_completed = pyqtSignal(str, str)  # filename, srt_path
    generation_started = pyqtSignal(str)  # filename
    generation_completed = pyqtSignal(str, bool, str)  # filename, success, message
    file_error = pyqtSignal(str, str)  # filename, error_message
    batch_summary = pyqtSignal(dict)  # Final statistics
    finished = pyqtSignal()

    def __init__(self, queue_items: List[Dict], settings: Dict,
                 output_folder: str, transcript_folder: str,
                 pairing_history: PairingHistory,
                 continue_on_error: bool = True,
                 max_words_per_segment: int = 1):
        """
        Initialize the batch worker.

        Args:
            queue_items: List of dicts with keys:
                - audio_path: str - Full path to audio file
                - srt_path: Optional[str] - Path to existing SRT, or None
                - needs_transcription: bool - Whether to transcribe
            settings: Video generation settings (font, color, resolution, etc.)
            output_folder: Where to save generated videos
            transcript_folder: Where to save generated SRT files
            pairing_history: PairingHistory instance for recording pairings
            continue_on_error: Whether to continue processing on individual file errors
            max_words_per_segment: Maximum words per subtitle segment (1-20)
        """
        super().__init__()
        self.queue_items = queue_items
        self.settings = settings
        self.output_folder = output_folder
        self.transcript_folder = transcript_folder
        self.pairing_history = pairing_history
        self.continue_on_error = continue_on_error
        self.max_words_per_segment = max_words_per_segment

        # Statistics tracking
        self.stats = {
            'total_files': len(queue_items),
            'successful_transcriptions': 0,
            'successful_generations': 0,
            'transcription_failures': 0,
            'generation_failures': 0,
            'skipped_files': 0,
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0
        }

        # Cancel flag
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the batch processing."""
        self._cancelled = True

    def run(self):
        """Main processing loop."""
        self.stats['start_time'] = time.time()

        # Emit batch start
        self.batch_started.emit(self.stats['total_files'])
        self.log_signal.emit(f"[BATCH] Starting batch processing: {self.stats['total_files']} files")
        self.log_signal.emit("=" * 60)

        # Process each item
        for index, item in enumerate(self.queue_items, 1):
            if self._cancelled:
                self.log_signal.emit("[BATCH] Processing cancelled by user")
                break

            audio_path = item['audio_path']
            filename = os.path.basename(audio_path)

            self.progress_signal.emit(index, self.stats['total_files'], filename)
            self.log_signal.emit(f"[{index}/{self.stats['total_files']}] Processing: {filename}")

            try:
                # Step 1: Get or generate SRT
                srt_path = item.get('srt_path')

                if item.get('needs_transcription', False) or not srt_path:
                    # Need to transcribe
                    self.transcription_started.emit(filename)
                    self.log_signal.emit(f"[TRANSCRIBE] Transcribing: {filename}")

                    srt_path = self._transcribe_and_generate_subtitles(audio_path)

                    if srt_path is None:
                        self.stats['transcription_failures'] += 1
                        self.file_error.emit(filename, "Transcription failed")
                        if not self.continue_on_error:
                            break
                        continue

                    self.stats['successful_transcriptions'] += 1
                    self.transcription_completed.emit(filename, srt_path)
                    self.log_signal.emit(f"[OK] Transcription complete: {os.path.basename(srt_path)}")

                    # Save pairing to history
                    self.pairing_history.add_pairing(
                        audio_path, srt_path, source='auto_transcribed'
                    )

                # Step 2: Generate video
                if not srt_path or not os.path.exists(srt_path):
                    self.stats['generation_failures'] += 1
                    self.file_error.emit(filename, "SRT file not found")
                    if not self.continue_on_error:
                        break
                    continue

                self.generation_started.emit(filename)
                self.log_signal.emit(f"[GENERATE] Creating video for: {filename}")

                # Determine output path
                base_name = os.path.splitext(filename)[0]
                is_transparent = self.settings.get('transparent_background', False)
                extension = ".webm" if is_transparent else ".mp4"
                output_path = os.path.join(self.output_folder, f"{base_name}_captions{extension}")

                success, message = generate_caption_video(
                    srt_path,
                    audio_path,
                    output_path,
                    self.settings,
                    progress_callback=lambda msg: self.log_signal.emit(msg),
                    transparent=is_transparent
                )

                if success:
                    self.stats['successful_generations'] += 1
                    self.generation_completed.emit(filename, True, output_path)
                    self.log_signal.emit(f"[OK] Video created: {os.path.basename(output_path)}")
                else:
                    self.stats['generation_failures'] += 1
                    self.generation_completed.emit(filename, False, message)
                    self.file_error.emit(filename, message)
                    self.log_signal.emit(f"[ERROR] Video generation failed: {message}")
                    if not self.continue_on_error:
                        break

            except Exception as e:
                self.stats['generation_failures'] += 1
                error_msg = str(e)
                self.file_error.emit(filename, error_msg)
                self.log_signal.emit(f"[ERROR] Unexpected error processing {filename}: {error_msg}")
                if not self.continue_on_error:
                    break

        # Calculate final statistics
        self.stats['end_time'] = time.time()
        self.stats['duration_seconds'] = self.stats['end_time'] - self.stats['start_time']

        # Emit summary
        self.log_signal.emit("=" * 60)
        self.log_signal.emit("[BATCH] PROCESSING COMPLETE")
        self._log_summary()

        self.batch_summary.emit(self.stats)
        self.finished.emit()

    def _log_summary(self):
        """Log the batch processing summary."""
        duration_str = f"{self.stats['duration_seconds']:.1f}s"

        self.log_signal.emit(f"[SUMMARY] Total Files: {self.stats['total_files']}")
        self.log_signal.emit(f"[SUMMARY] Successful Transcriptions: {self.stats['successful_transcriptions']}")
        self.log_signal.emit(f"[SUMMARY] Successful Videos: {self.stats['successful_generations']}")
        self.log_signal.emit(f"[SUMMARY] Transcription Failures: {self.stats['transcription_failures']}")
        self.log_signal.emit(f"[SUMMARY] Generation Failures: {self.stats['generation_failures']}")
        self.log_signal.emit(f"[SUMMARY] Processing Time: {duration_str}")

    def _transcribe_and_generate_subtitles(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio and generate SRT file.

        Args:
            audio_path: Path to the audio file

        Returns:
            Path to SRT file or None if failed
        """
        # Load environment and get API key
        load_environment()
        api_key = get_env_var("ELEVENLABS_API_KEY")

        if not api_key:
            self.log_signal.emit("[ERROR] ELEVENLABS_API_KEY not set in environment variables")
            self.log_signal.emit("[ERROR] Please add ELEVENLABS_API_KEY=your_key to .env file")
            return None

        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=api_key)
        except ImportError:
            self.log_signal.emit("[ERROR] elevenlabs package not installed")
            self.log_signal.emit("[ERROR] Run: pip install elevenlabs")
            return None

        # Convert to MP3 if needed
        mp3_path = self._ensure_mp3(audio_path)
        if not mp3_path:
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

            # Extract words from response
            words = getattr(transcription, 'words', []) or []

            if not words:
                self.log_signal.emit("[ERROR] No words returned from transcription")
                return None

            self.log_signal.emit(f"[TRANSCRIBE] Received {len(words)} words from API")

            # Generate SRT
            base_name = os.path.splitext(os.path.basename(audio_path))[0]

            # Ensure transcript folder exists
            os.makedirs(self.transcript_folder, exist_ok=True)

            srt_path = os.path.join(self.transcript_folder, f"{base_name}.srt")

            # Generate segments with configurable words per segment
            self.log_signal.emit(f"[TRANSCRIBE] Grouping into segments (max {self.max_words_per_segment} words each)")
            segments = words_to_segments(words, max_words=self.max_words_per_segment)

            # Generate SRT
            if generate_srt(segments, srt_path):
                self.log_signal.emit(f"[OK] Saved SRT: {os.path.basename(srt_path)}")
            else:
                self.log_signal.emit("[ERROR] Failed to generate SRT file")
                return None

            return srt_path

        except Exception as e:
            self.log_signal.emit(f"[ERROR] Transcription error: {e}")
            return None

    def _ensure_mp3(self, audio_path: str) -> Optional[str]:
        """
        Convert audio to MP3 if needed for ElevenLabs API.

        Args:
            audio_path: Path to audio file

        Returns:
            Path to MP3 file or None if conversion failed
        """
        ext = os.path.splitext(audio_path)[1].lower()

        # Already MP3
        if ext == '.mp3':
            return audio_path

        base = os.path.splitext(audio_path)[0]
        mp3_path = base + ".mp3"

        self.log_signal.emit(f"[CONVERT] Converting {ext.upper()} to MP3...")

        try:
            if ext in ['.wav', '.m4a', '.flac', '.aac']:
                from pydub import AudioSegment

                if ext == '.wav':
                    audio = AudioSegment.from_wav(audio_path)
                elif ext == '.m4a':
                    audio = AudioSegment.from_file(audio_path, format="m4a")
                elif ext == '.flac':
                    audio = AudioSegment.from_file(audio_path, format="flac")
                elif ext == '.aac':
                    audio = AudioSegment.from_file(audio_path, format="aac")
                else:
                    audio = AudioSegment.from_file(audio_path)

                audio.export(mp3_path, format="mp3")
                self.log_signal.emit(f"[OK] Conversion complete: {os.path.basename(mp3_path)}")
                return mp3_path

            else:
                self.log_signal.emit(f"[ERROR] Unsupported audio format: {ext}")
                return None

        except ImportError:
            self.log_signal.emit("[ERROR] pydub not installed for audio conversion")
            return None
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Conversion error: {e}")
            return None
