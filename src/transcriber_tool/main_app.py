# -*- coding: utf-8 -*-
"""
Main Application Module for Transcriber Tool.

A drag-and-drop transcription tool using ElevenLabs Speech-to-Text API.
"""

import os
import sys
import time
from io import BytesIO
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QTextEdit, QMessageBox,
    QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from moviepy.editor import VideoFileClip

# Import local config manager
from .config_manager import get_config

# Import core utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.env_loader import load_environment, get_env_var


class Worker(QThread):
    """Background worker thread for batch transcription processing."""

    log_signal = pyqtSignal(str)
    batch_started_signal = pyqtSignal(int)  # Emits total file count
    progress_signal = pyqtSignal(int, int, str)  # current, total, filename
    file_completed_signal = pyqtSignal(str, str)  # filename, status
    batch_summary_signal = pyqtSignal(dict)  # Batch statistics
    finished_signal = pyqtSignal()

    def __init__(self, files, output_folder, export_formats=None):
        super().__init__()
        self.files = files
        self.output_folder = output_folder
        self.export_formats = export_formats or {"txt": True, "srt": False}
        self.config = get_config()
        self.batch_stats = {
            'total_files': len(files),
            'successful_conversions': 0,
            'successful_transcriptions': 0,
            'conversion_failures': 0,
            'transcription_failures': 0,
            'skipped_files': 0,
            'start_time': None,
            'end_time': None
        }

    def run(self):
        """Main processing loop."""
        self.batch_stats['start_time'] = time.time()

        # Emit batch start signal
        self.batch_started_signal.emit(self.batch_stats['total_files'])
        self.log_signal.emit(f"[BATCH] Starting batch processing: {self.batch_stats['total_files']} files")
        self.log_signal.emit("=" * 60)

        # Process each file one by one
        for index, file_path in enumerate(self.files, 1):
            filename = os.path.basename(file_path)
            self.progress_signal.emit(index, self.batch_stats['total_files'], filename)
            self.log_signal.emit(f"[{index}/{self.batch_stats['total_files']}] Processing: {filename}")

            # Step 1: Convert to MP3
            mp3_file = self.convert_to_mp3(file_path)
            if not mp3_file:
                self.batch_stats['conversion_failures'] += 1
                self.batch_stats['skipped_files'] += 1
                self.file_completed_signal.emit(filename, "[FAILED] Conversion Failed")
                self.log_signal.emit(f"[{index}/{self.batch_stats['total_files']}] Conversion failed: {filename}")
                continue
            else:
                self.batch_stats['successful_conversions'] += 1
                self.file_completed_signal.emit(filename, "[OK] Converted")

            # Step 2: Transcribe audio
            transcription = self.transcribe_audio(mp3_file)
            if transcription is None:
                self.batch_stats['transcription_failures'] += 1
                self.file_completed_signal.emit(filename, "[FAILED] Transcription Failed")
                self.log_signal.emit(f"[{index}/{self.batch_stats['total_files']}] Transcription failed: {filename}")
                continue
            else:
                self.batch_stats['successful_transcriptions'] += 1

            # Step 3: Save transcription(s) in selected formats
            base = os.path.splitext(os.path.basename(file_path))[0]

            # Extract text and words from transcription object
            text = getattr(transcription, 'text', str(transcription))
            words = getattr(transcription, 'words', []) or []

            try:
                saved_formats = []

                # Save TXT
                if self.export_formats.get("txt", True):
                    txt_file = os.path.join(self.output_folder, base + ".txt")
                    with open(txt_file, "w", encoding="utf-8") as f:
                        f.write(text)
                    saved_formats.append("TXT")
                    self.log_signal.emit(f"[OK] Saved TXT: {os.path.basename(txt_file)}")

                # Save SRT (word-by-word for precise timing)
                if self.export_formats.get("srt", False) and words:
                    from .subtitle_generator import words_to_segments, generate_srt
                    srt_file = os.path.join(self.output_folder, base + ".srt")
                    segments = words_to_segments(words, max_words=1)
                    if generate_srt(segments, srt_file):
                        saved_formats.append("SRT")
                        self.log_signal.emit(f"[OK] Saved SRT: {os.path.basename(srt_file)}")
                    else:
                        self.log_signal.emit(f"[WARN] SRT generation failed for: {filename}")

                if saved_formats:
                    self.file_completed_signal.emit(filename, f"[OK] {', '.join(saved_formats)}")
                else:
                    self.log_signal.emit(f"[WARN] No export formats selected for: {filename}")
                    self.file_completed_signal.emit(filename, "[WARN] No formats selected")

            except Exception as e:
                self.batch_stats['transcription_failures'] += 1
                self.file_completed_signal.emit(filename, "[FAILED] Save Failed")
                self.log_signal.emit(f"[{index}/{self.batch_stats['total_files']}] Error saving {filename}: {e}")

        # Calculate final statistics
        self.batch_stats['end_time'] = time.time()
        duration = self.batch_stats['end_time'] - self.batch_stats['start_time']
        self.batch_stats['duration_seconds'] = duration

        # Emit batch summary
        self.log_signal.emit("=" * 60)
        self.log_signal.emit("[BATCH] PROCESSING COMPLETE")
        self.batch_summary_signal.emit(self.batch_stats)
        self.finished_signal.emit()

    def convert_to_mp3(self, input_file):
        """
        Converts an audio/video file to MP3 if needed.
        If the file is already an MP3, returns the original path.
        Supports: MP3, MP4, WAV, M4A, FLAC
        Returns the path to the MP3 file or None if an error occurred.
        """
        base, ext = os.path.splitext(input_file)
        ext = ext.lower()

        # Get supported extensions from config
        supported_extensions = self.config.get("supported_formats",
                                               [".mp3", ".mp4", ".wav", ".m4a", ".flac"])
        # Ensure they have dots
        supported_extensions = [f".{e}" if not e.startswith(".") else e
                               for e in supported_extensions]

        if ext not in supported_extensions:
            self.log_signal.emit(f"[ERROR] Unsupported file type: {input_file}")
            self.log_signal.emit(f"        Supported formats: {', '.join(supported_extensions)}")
            return None

        if ext == ".mp3":
            self.log_signal.emit(f"[INFO] File is already MP3: {os.path.basename(input_file)}")
            return input_file

        output_file = base + ".mp3"
        self.log_signal.emit(f"[CONVERT] Converting {ext.upper()} to MP3...")

        try:
            if ext == ".mp4":
                # Use moviepy for MP4 files
                video_clip = VideoFileClip(input_file)
                audio_clip = video_clip.audio
                audio_clip.write_audiofile(output_file, logger=None)
                audio_clip.close()
                video_clip.close()
                self.log_signal.emit(f"[OK] Conversion complete: {os.path.basename(output_file)}")
                return output_file

            elif ext in [".wav", ".m4a", ".flac"]:
                # Use pydub for WAV, M4A, and FLAC files
                try:
                    from pydub import AudioSegment

                    if ext == ".wav":
                        audio = AudioSegment.from_wav(input_file)
                    elif ext == ".m4a":
                        audio = AudioSegment.from_file(input_file, format="m4a")
                    elif ext == ".flac":
                        audio = AudioSegment.from_file(input_file, format="flac")

                    audio.export(output_file, format="mp3")
                    self.log_signal.emit(f"[OK] Conversion complete: {os.path.basename(output_file)}")
                    return output_file

                except ImportError:
                    self.log_signal.emit(f"[ERROR] pydub not available for {ext.upper()} conversion")
                    return None
                except Exception as e:
                    self.log_signal.emit(f"[ERROR] Conversion error: {e}")
                    return None

        except Exception as e:
            self.log_signal.emit(f"[ERROR] Conversion error: {e}")
            return None

    def transcribe_audio(self, mp3_file):
        """
        Transcribes the given MP3 file using the ElevenLabs Speech to Text API.
        Returns the full transcription object (with words array) or None if an error occurred.
        """
        # Load environment and get API key
        load_environment()
        api_key_env = self.config.get("api_key_env", "ELEVENLABS_API_KEY")
        api_key = get_env_var(api_key_env)

        if not api_key:
            self.log_signal.emit(f"[ERROR] {api_key_env} not set in environment variables")
            self.log_signal.emit(f"        Please add {api_key_env}=your_key to .env file")
            return None

        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=api_key)
        except ImportError:
            self.log_signal.emit("[ERROR] elevenlabs package not installed")
            self.log_signal.emit("        Run: pip install elevenlabs")
            return None

        try:
            with open(mp3_file, "rb") as f:
                audio_data = BytesIO(f.read())

            self.log_signal.emit("[TRANSCRIBE] Transcribing audio...")

            # Get transcription settings from config
            language_code = self.config.get("language_code", "eng")
            enable_diarization = self.config.get("enable_diarization", True)
            tag_audio_events = self.config.get("tag_audio_events", True)

            transcription = client.speech_to_text.convert(
                file=audio_data,
                model_id="scribe_v1",
                tag_audio_events=tag_audio_events,
                language_code=language_code,
                diarize=enable_diarization,
                timestamps_granularity="word"
            )
            return transcription  # Return full object with words array
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Transcription error: {e}")
            return None


class TranscriberApp(QWidget):
    """Main drag-and-drop transcription application widget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriber Tool - Drag and Drop")
        self.resize(700, 500)
        self.setAcceptDrops(True)

        # Get global config
        self.config = get_config()

        # Get default output folder
        self.output_folder = self.config.get_output_folder()

        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()

        # Title label
        self.label = QLabel("Drag and drop MP4/MP3/WAV/M4A/FLAC files here to transcribe.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(self.label)

        # Output folder selector
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Output Folder:")
        self.folder_line = QLineEdit(self.output_folder)
        self.folder_line.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.select_folder)
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_output_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_line, 1)
        folder_layout.addWidget(browse_btn)
        folder_layout.addWidget(open_btn)
        layout.addLayout(folder_layout)

        # Export Format Selection
        format_group = QGroupBox("Export Formats")
        format_layout = QHBoxLayout()

        self.txt_checkbox = QCheckBox("TXT")
        self.srt_checkbox = QCheckBox("SRT")

        # Load saved preferences
        export_formats = self.config.get("export_formats", {"txt": True, "srt": True})
        self.txt_checkbox.setChecked(export_formats.get("txt", True))
        self.srt_checkbox.setChecked(export_formats.get("srt", True))

        # Connect to save on change
        self.txt_checkbox.stateChanged.connect(self.save_format_preferences)
        self.srt_checkbox.stateChanged.connect(self.save_format_preferences)

        format_layout.addWidget(self.txt_checkbox)
        format_layout.addWidget(self.srt_checkbox)
        format_layout.addStretch()

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Log output area
        log_label = QLabel("Log Output:")
        layout.addWidget(log_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("font-family: Consolas; font-size: 10px;")
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        # Initial log message
        self.update_log("[TranscriberTool] Ready. Drag and drop files to begin transcription.")

    def select_folder(self):
        """Handle output folder selection."""
        chosen = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_folder)
        if chosen:
            self.output_folder = chosen
            self.folder_line.setText(chosen)

            try:
                self.config.set("output_folder", chosen)
                self.update_log(f"[INFO] Output folder set to: {chosen}")
            except Exception as e:
                self.update_log(f"[ERROR] Error saving folder preference: {str(e)}")

    def open_output_folder(self):
        """Open the output folder in File Explorer."""
        if self.output_folder and os.path.exists(self.output_folder):
            try:
                os.startfile(self.output_folder)
                self.update_log(f"[INFO] Opened folder: {self.output_folder}")
            except Exception as e:
                self.update_log(f"[ERROR] Failed to open folder: {e}")
        else:
            self.update_log("[ERROR] Output folder not set or doesn't exist")

    def save_format_preferences(self):
        """Save export format preferences to config."""
        export_formats = {
            "txt": self.txt_checkbox.isChecked(),
            "srt": self.srt_checkbox.isChecked()
        }
        self.config.set("export_formats", export_formats)

    def dragEnterEvent(self, event):
        """Accept drag enter events with URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle dropped files."""
        self.update_log("[DROP] Drop event detected!")

        urls = event.mimeData().urls()
        if not urls:
            self.update_log("[ERROR] No URLs found in drop event")
            return

        self.update_log(f"[INFO] Found {len(urls)} URL(s) in drop event")

        # Gather all file paths
        file_paths = []
        for url in urls:
            local_file = url.toLocalFile()
            self.update_log(f"[CHECK] Checking file: {local_file}")

            if os.path.isfile(local_file):
                file_paths.append(local_file)
                self.update_log(f"[OK] Valid file: {local_file}")
            else:
                self.update_log(f"[SKIP] Not a valid file: {local_file}")

        if not file_paths:
            self.update_log("[ERROR] No valid files found in drop event")
            return

        self.update_log(f"\n[QUEUE] Files queued for batch processing ({len(file_paths)}):")
        for fp in file_paths:
            self.update_log(f"  - {os.path.basename(fp)}")
        self.update_log("")

        self.start_processing(file_paths)

    def start_processing(self, files):
        """Start the worker thread for batch processing."""
        # Get current export format selections
        export_formats = {
            "txt": self.txt_checkbox.isChecked(),
            "srt": self.srt_checkbox.isChecked()
        }
        self.worker = Worker(files, self.output_folder, export_formats)

        # Connect all signals
        self.worker.log_signal.connect(self.update_log)
        self.worker.batch_started_signal.connect(self.on_batch_started)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.file_completed_signal.connect(self.on_file_completed)
        self.worker.batch_summary_signal.connect(self.on_batch_summary)
        self.worker.finished_signal.connect(self.processing_finished)

        self.worker.start()

    def on_batch_started(self, total_files):
        """Handle batch start signal."""
        self.update_log(f"[START] Batch initialized: {total_files} files in queue")

    def on_progress(self, current, total, filename):
        """Handle progress signal."""
        progress_percent = int((current / total) * 100)
        self.update_log(f"[PROGRESS] {progress_percent}% ({current}/{total}) - {filename}")

    def on_file_completed(self, filename, status):
        """Handle file completion signal."""
        self.update_log(f"[DONE] {status} - {filename}")

    def on_batch_summary(self, stats):
        """Display comprehensive batch statistics."""
        duration_str = f"{stats['duration_seconds']:.1f}s"

        summary_lines = [
            "[SUMMARY] BATCH SUMMARY:",
            f"   Total Files: {stats['total_files']}",
            f"   Successful Transcriptions: {stats['successful_transcriptions']}",
            f"   Successful Conversions: {stats['successful_conversions']}",
            f"   Conversion Failures: {stats['conversion_failures']}",
            f"   Transcription Failures: {stats['transcription_failures']}",
            f"   Skipped Files: {stats['skipped_files']}",
            f"   Processing Time: {duration_str}",
        ]

        for line in summary_lines:
            self.update_log(line)

    def update_log(self, message):
        """Append message to log box."""
        self.log_box.append(message)

    def processing_finished(self):
        """Handle batch processing completion."""
        stats = self.worker.batch_stats

        successful = stats['successful_transcriptions']
        total = stats['total_files']
        failed = stats['conversion_failures'] + stats['transcription_failures']
        duration = f"{stats['duration_seconds']:.1f}s"

        if successful == total:
            title = "Batch Complete - All Successful!"
            message = f"Successfully processed all {total} files in {duration}"
        elif successful > 0:
            title = "Batch Complete - Partial Success"
            message = f"Processed {successful}/{total} files successfully ({failed} failed) in {duration}"
        else:
            title = "Batch Complete - All Failed"
            message = f"Failed to process any of the {total} files in {duration}"

        QMessageBox.information(self, title, message)
        self.update_log(f"[COMPLETE] Batch processing session complete!\n")


def main():
    """Application entry point."""
    # Load environment variables
    load_environment()

    app = QApplication(sys.argv)

    # Apply basic dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
        }
        QTextEdit {
            background-color: #121212;
            color: #00ff88;
            border: 1px solid #404040;
        }
        QLineEdit {
            background-color: #121212;
            color: #e0e0e0;
            border: 1px solid #404040;
            padding: 5px;
        }
        QPushButton {
            background-color: #2a2a2a;
            color: #00ffff;
            border: 1px solid #00ffff;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3a3a3a;
        }
        QLabel {
            color: #e0e0e0;
        }
        QGroupBox {
            border: 1px solid #404040;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
            font-size: 11px;
            color: #00ffff;
            background-color: #1a1a1a;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #00ffff;
            background-color: #1a1a1a;
        }
        QCheckBox {
            color: #e0e0e0;
            spacing: 8px;
            font-size: 12px;
            padding: 4px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #404040;
            border-radius: 3px;
            background-color: #1a1a1a;
        }
        QCheckBox::indicator:checked {
            background-color: #00ff88;
            border: 1px solid #00ff88;
        }
        QCheckBox::indicator:unchecked:hover {
            border: 1px solid #00ffff;
        }
    """)

    window = TranscriberApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
