# -*- coding: utf-8 -*-
"""
Controller for Snippet Remixer.

Orchestrates remix operations, managing processing state, continuous mode,
and job queue coordination. Has NO Tkinter imports - pure business logic.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Callable, Dict, List, Optional, Any

from .job_queue import JobQueue, ProcessingJob, JobStatus, RemixerSettings
from .utils import safe_print, validate_directory_path


class SnippetRemixerController:
    """
    Orchestrates remix operations - no Tkinter imports.

    Manages:
    - Processing orchestration (single + continuous modes)
    - Settings validation and calculation
    - Job queue coordination
    - State management
    """

    def __init__(
        self,
        config_manager,
        processing_worker,
        job_queue: JobQueue,
        callbacks: Dict[str, Callable],
    ):
        """
        Initialize the controller.

        Args:
            config_manager: Configuration manager instance.
            processing_worker: ProcessingWorker instance.
            job_queue: JobQueue instance.
            callbacks: Dictionary of UI callback functions:
                - on_status: Callable[[str], None] - Update status message
                - on_status_success: Callable[[str], None] - Success status
                - on_status_warning: Callable[[str], None] - Warning status
                - on_status_error: Callable[[str], None] - Error status
                - on_enable_generate: Callable[[bool], None] - Enable/disable generate
                - on_continuous_update: Callable[[int, str], None] - Update continuous counter
                - on_queue_update: Callable[[], None] - Update queue display
                - on_show_warning: Callable[[str, str], None] - Show warning dialog
                - on_show_error: Callable[[str, str], None] - Show error dialog
                - schedule_callback: Callable[[int, Callable], None] - Schedule delayed callback
        """
        self.config_manager = config_manager
        self.worker = processing_worker
        self.job_queue = job_queue
        self.callbacks = callbacks
        self.logger = None  # Set externally if needed

        # Processing state
        self._is_continuous = False
        self._continuous_count = 0
        self._last_settings: Dict[str, Any] = {}
        self._queue_processor_active = False

        # Setup job queue callbacks
        self.job_queue.set_callbacks(
            on_queue_update=self._on_queue_update,
            on_job_start=self._on_job_started,
            on_job_complete=self._on_job_completed,
            on_job_progress=self._on_job_progress,
        )

    def set_logger(self, logger) -> None:
        """Set the logger instance."""
        self.logger = logger

    # -------------------------------------------------------------------------
    # Callback helpers
    # -------------------------------------------------------------------------
    def _call(self, name: str, *args) -> None:
        """Safely call a callback if it exists."""
        callback = self.callbacks.get(name)
        if callback:
            callback(*args)

    def _log(self, message: str, level: str = "info") -> None:
        """Log a message if logger is available."""
        if self.logger:
            getattr(self.logger, level, self.logger.info)(message)

    # -------------------------------------------------------------------------
    # State properties
    # -------------------------------------------------------------------------
    @property
    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return self.worker.is_processing()

    @property
    def is_continuous_mode(self) -> bool:
        """Check if continuous mode is active."""
        return self._is_continuous

    @property
    def continuous_count(self) -> int:
        """Get the number of remixes created in continuous mode."""
        return self._continuous_count

    @property
    def queue_processor_active(self) -> bool:
        """Check if queue processor is running."""
        return self._queue_processor_active

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    def validate_settings(
        self,
        input_files: List[str],
        output_folder: str,
        aspect_ratio: str,
    ) -> tuple[bool, str]:
        """
        Validate settings before processing.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check FFmpeg tools
        ffmpeg_found, ffprobe_found = self.worker.get_video_processor().are_tools_available()
        if not ffmpeg_found or not ffprobe_found:
            missing = []
            if not ffmpeg_found:
                missing.append("FFmpeg")
            if not ffprobe_found:
                missing.append("FFprobe")
            return False, f"Cannot process. {'/'.join(missing)} not found."

        # Check input files
        if not input_files:
            return False, "Please add video files to the queue."

        # Check output folder
        if not output_folder or not validate_directory_path(output_folder):
            return False, f"Output folder is invalid or not set:\n{output_folder}"

        # Check aspect ratio
        if aspect_ratio not in self.config_manager.get_aspect_ratios():
            return False, "Invalid Aspect Ratio selected."

        return True, ""

    def calculate_durations(
        self,
        length_mode: str,
        settings: Dict[str, Any],
    ) -> tuple[float, Any]:
        """
        Calculate target duration and snippet spec from settings.

        Args:
            length_mode: "Seconds" or "BPM"
            settings: Dictionary with duration/BPM settings

        Returns:
            Tuple of (target_total_duration, snippet_duration_spec)
        """
        return self.worker.calculate_durations(length_mode, settings)

    # -------------------------------------------------------------------------
    # Single Remix Processing
    # -------------------------------------------------------------------------
    def start_single_remix(
        self,
        input_files: List[str],
        settings: RemixerSettings,
        settings_dict: Dict[str, Any],
    ) -> bool:
        """
        Start a single remix operation.

        Args:
            input_files: List of input video file paths.
            settings: RemixerSettings dataclass with all settings.
            settings_dict: Raw settings dictionary for duration calculation.

        Returns:
            True if processing started, False otherwise.
        """
        if self.is_processing:
            self._call("on_show_warning", "Busy", "Processing is already in progress.")
            return False

        # Validate
        is_valid, error_msg = self.validate_settings(
            input_files, settings.output_folder, settings.aspect_ratio
        )
        if not is_valid:
            self._call("on_show_error", "Validation Error", error_msg)
            return False

        try:
            # Calculate durations
            target_duration, snippet_spec = self.calculate_durations(
                settings.length_mode, settings_dict
            )
        except ValueError as e:
            self._call("on_show_error", "Invalid Input", f"Please check length/BPM settings:\n{e}")
            return False
        except Exception as e:
            self._call("on_show_error", "Error", f"An unexpected error occurred during setup:\n{e}")
            return False

        # Generate unique filename
        final_output_path = self.worker.generate_output_filename(
            settings.aspect_ratio, settings.output_folder
        )

        # Update UI
        self._call("on_enable_generate", False)
        output_msg = f"Output: {os.path.basename(final_output_path)}"
        self._call("on_status", output_msg)
        safe_print(f"[VIDEO] {output_msg}")
        self._log(f"Starting video processing - {output_msg}")

        # Schedule delayed start
        def start_delayed():
            self._execute_processing(
                input_files, final_output_path, target_duration,
                snippet_spec, settings, settings_dict
            )

        schedule = self.callbacks.get("schedule_callback")
        if schedule:
            schedule(500, start_delayed)
        else:
            start_delayed()

        return True

    def _execute_processing(
        self,
        input_files: List[str],
        output_path: str,
        target_duration: float,
        snippet_spec: Any,
        settings: RemixerSettings,
        settings_dict: Dict[str, Any],
    ) -> None:
        """Execute the actual processing with callbacks."""
        self._call("on_status", "Starting processing...")
        safe_print("[START] Starting processing...")
        self._log(f"Processing started: {len(input_files)} input files, target duration: {target_duration:.1f}s")

        # Define callbacks
        def progress_callback(message: str) -> None:
            self._call("on_status", message)
            safe_print(f"Progress: {message}")
            self._log(f"Progress: {message}")

        def error_callback(error_type: str, title: str, message: str) -> None:
            if error_type == "warning":
                safe_print(f"[WARNING] {title}: {message}")
                self._log(f"{title}: {message}", "warning")
                self._call("on_status_warning", f"{title}: {message}")
                self._call("on_show_warning", title, message)
            else:
                safe_print(f"[ERROR] {title}: {message}")
                self._log(f"{title}: {message}", "error")
                self._call("on_status_error", f"{title}: {message}")
                self._call("on_show_error", title, message)

        def completion_callback(success: bool, output_path: str) -> None:
            self._on_processing_complete(success, output_path, settings)

        # Build export settings
        export_settings = self.config_manager.get_export_settings().copy()
        export_settings["jitter_enabled"] = settings.jitter_enabled
        export_settings["jitter_intensity"] = settings.jitter_intensity
        export_settings["aspect_ratio_mode"] = settings.aspect_ratio_mode
        export_settings["remove_audio"] = settings.mute_audio

        # Start processing
        self.worker.start_processing_thread(
            input_files, output_path, target_duration,
            snippet_spec, settings.aspect_ratio,
            export_settings,
            progress_callback, error_callback, completion_callback
        )

    def _on_processing_complete(
        self,
        success: bool,
        output_path: str,
        settings: RemixerSettings,
    ) -> None:
        """Handle processing completion."""
        if success:
            self._continuous_count += 1
            success_msg = f"Remix #{self._continuous_count} saved: {os.path.basename(output_path)}"
            self._call("on_status_success", success_msg)
            safe_print(f"[SUCCESS] {success_msg}")
            self._log(success_msg)

            # Update counter display
            self._call("on_continuous_update", self._continuous_count, "")

            # If continuous mode, start next
            if self._is_continuous:
                schedule = self.callbacks.get("schedule_callback")
                if schedule:
                    schedule(2000, lambda: self._call("on_start_next_continuous"))
            else:
                self._call("on_enable_generate", True)
                self._is_continuous = False
        else:
            failure_msg = "Processing failed. Check console for details."
            self._call("on_status_error", failure_msg)
            safe_print(f"[FAILED] {failure_msg}")
            self._log(failure_msg, "error")
            self._call("on_enable_generate", True)
            self._is_continuous = False

    # -------------------------------------------------------------------------
    # Continuous Mode
    # -------------------------------------------------------------------------
    def start_continuous_mode(
        self,
        input_files: List[str],
        settings: RemixerSettings,
        settings_dict: Dict[str, Any],
    ) -> bool:
        """
        Start continuous mode processing.

        Args:
            input_files: List of input video file paths.
            settings: RemixerSettings dataclass.
            settings_dict: Raw settings dictionary.

        Returns:
            True if continuous mode started.
        """
        if not self._is_continuous:
            self._is_continuous = True
            self._continuous_count = 0
            self._last_settings = settings_dict.copy()
            self._call("on_continuous_update", 0, "")
            self._log("Continuous mode started")

        return self.start_single_remix(input_files, settings, settings_dict)

    def continue_continuous_mode(
        self,
        input_files: List[str],
        settings: RemixerSettings,
        settings_dict: Dict[str, Any],
    ) -> bool:
        """
        Continue continuous mode with next remix.

        Args:
            input_files: List of input video file paths.
            settings: RemixerSettings dataclass.
            settings_dict: Raw settings dictionary.

        Returns:
            True if next remix started.
        """
        if not self._is_continuous:
            return False

        # Detect setting changes
        changes = self.detect_setting_changes(self._last_settings, settings_dict)
        if changes:
            change_msg = f"Settings updated for remix #{self._continuous_count + 1}: {', '.join(changes)}"
            self._call("on_status", change_msg)
            safe_print(f"[CONTINUOUS] {change_msg}")
            self._log(f"Continuous mode - {change_msg}")

        # Store current settings for next comparison
        self._last_settings = settings_dict.copy()

        # Create status message
        status_msg = self._build_continuous_status_message(settings, settings_dict)
        self._call("on_status", status_msg)
        safe_print(f"[CONTINUOUS] {status_msg}")

        return self.start_single_remix(input_files, settings, settings_dict)

    def _build_continuous_status_message(
        self,
        settings: RemixerSettings,
        settings_dict: Dict[str, Any],
    ) -> str:
        """Build status message for continuous mode."""
        if settings.tempo_mod_enabled:
            return (f"Starting remix #{self._continuous_count + 1} "
                    f"(BPM ramp: {settings.tempo_mod_start_bpm}->{settings.tempo_mod_end_bpm} "
                    f"over {settings.tempo_mod_duration}s)...")
        elif settings.length_mode == "BPM":
            return (f"Starting remix #{self._continuous_count + 1} "
                    f"(BPM: {settings.bpm}, {settings.num_units} {settings.bpm_unit}s)...")
        else:
            return (f"Starting remix #{self._continuous_count + 1} "
                    f"(Duration: {settings.duration_seconds}s)...")

    def stop_continuous_mode(self) -> None:
        """Stop continuous mode processing."""
        self._is_continuous = False
        self._call("on_enable_generate", True)
        self._call("on_status", f"Continuous mode stopped. Created {self._continuous_count} remixes.")
        self._log(f"Continuous mode stopped after {self._continuous_count} remixes")

    def detect_setting_changes(
        self,
        old_settings: Dict[str, Any],
        new_settings: Dict[str, Any],
    ) -> List[str]:
        """
        Detect and describe changes between settings.

        Returns:
            List of change descriptions.
        """
        changes = []

        comparisons = [
            ("bpm", "BPM"),
            ("num_units", "Units"),
            ("bpm_unit", "Unit type"),
            ("duration_seconds", "Duration", "s"),
            ("tempo_mod_start_bpm", "Start BPM"),
            ("tempo_mod_end_bpm", "End BPM"),
            ("tempo_mod_duration_seconds", "Mod clip", "s"),
            ("aspect_ratio", "Aspect ratio"),
            ("length_mode", "Mode"),
        ]

        for item in comparisons:
            key = item[0]
            label = item[1]
            suffix = item[2] if len(item) > 2 else ""

            old_val = old_settings.get(key)
            new_val = new_settings.get(key)

            if old_val != new_val:
                changes.append(f"{label} {old_val}{suffix} -> {new_val}{suffix}")

        # Boolean toggles
        if old_settings.get("tempo_mod_enabled") != new_settings.get("tempo_mod_enabled"):
            mod_state = "enabled" if new_settings.get("tempo_mod_enabled") else "disabled"
            changes.append(f"Tempo modulation {mod_state}")

        if old_settings.get("jitter_enabled") != new_settings.get("jitter_enabled"):
            jitter_state = "enabled" if new_settings.get("jitter_enabled") else "disabled"
            changes.append(f"Jitter {jitter_state}")

        if old_settings.get("mute_audio") != new_settings.get("mute_audio"):
            audio_state = "muted" if new_settings.get("mute_audio") else "enabled"
            changes.append(f"Audio {audio_state}")

        # Jitter intensity (only if both have jitter enabled)
        if (old_settings.get("jitter_enabled") and new_settings.get("jitter_enabled") and
            old_settings.get("jitter_intensity") != new_settings.get("jitter_intensity")):
            changes.append(f"Jitter intensity {old_settings.get('jitter_intensity')}% -> {new_settings.get('jitter_intensity')}%")

        # Tempo mod points
        if old_settings.get("tempo_mod_points") != new_settings.get("tempo_mod_points"):
            changes.append("Tempo graph updated")

        return changes

    # -------------------------------------------------------------------------
    # Abort
    # -------------------------------------------------------------------------
    def abort_processing(self) -> None:
        """Abort the current processing operation."""
        if self._is_continuous:
            self.stop_continuous_mode()
        elif self.is_processing:
            self._call("on_status", "Aborting processing...")
            self.worker.abort_processing()
            self._call("on_enable_generate", True)

    # -------------------------------------------------------------------------
    # Queue Mode
    # -------------------------------------------------------------------------
    def add_job_to_queue(
        self,
        input_files: List[str],
        settings: RemixerSettings,
        settings_dict: Dict[str, Any],
        tempo_mod_points: List[tuple],
    ) -> Optional[str]:
        """
        Add a new job to the processing queue.

        Returns:
            Job ID if successful, None otherwise.
        """
        # Validate
        is_valid, error_msg = self.validate_settings(
            input_files, settings.output_folder, settings.aspect_ratio
        )
        if not is_valid:
            self._call("on_show_error", "Validation Error", error_msg)
            return None

        try:
            # Calculate durations
            target_duration, snippet_spec = self.calculate_durations(
                settings.length_mode, settings_dict
            )

            # Generate unique filename
            output_path = self.worker.generate_output_filename(
                settings.aspect_ratio, settings.output_folder
            )

            # Build export settings
            export_settings = self.config_manager.get_export_settings().copy()
            export_settings["jitter_enabled"] = settings.jitter_enabled
            export_settings["jitter_intensity"] = settings.jitter_intensity
            export_settings["aspect_ratio_mode"] = settings.aspect_ratio_mode
            export_settings["remove_audio"] = settings.mute_audio

            # Create job
            job = ProcessingJob(
                input_files=input_files.copy(),
                output_path=output_path,
                target_duration=target_duration,
                snippet_duration=snippet_spec,
                aspect_ratio=settings.aspect_ratio,
                export_settings=export_settings.copy(),
                length_mode=settings.length_mode,
                bpm=settings.bpm,
                num_units=settings.num_units,
                bpm_unit=settings.bpm_unit,
                tempo_mod_enabled=settings.tempo_mod_enabled,
                tempo_mod_start_bpm=settings.tempo_mod_start_bpm,
                tempo_mod_end_bpm=settings.tempo_mod_end_bpm,
                tempo_mod_duration_seconds=settings.tempo_mod_duration,
                tempo_mod_points=tempo_mod_points.copy(),
                jitter_enabled=settings.jitter_enabled,
                jitter_intensity=settings.jitter_intensity,
            )

            # Add to queue
            job_id = self.job_queue.add_job(job)

            # Feedback
            self._call("on_status", f"Added to queue: {job.get_display_name()}")
            safe_print(f"[QUEUE] Job added: {job.get_display_name()}")
            self._log(f"Job {job_id} added to queue: {job.get_duration_text()}")

            return job_id

        except ValueError as e:
            self._call("on_show_error", "Invalid Input", f"Please check settings:\n{e}")
            return None
        except Exception as e:
            self._call("on_show_error", "Error", f"Failed to add job to queue:\n{e}")
            return None

    def process_next_queued_job(self) -> bool:
        """
        Process the next job in the queue.

        Returns:
            True if a job was started, False otherwise.
        """
        if self.is_processing:
            return False

        job = self.job_queue.get_next_job()
        if not job:
            self._queue_processor_active = False
            self._call("on_status", "Queue processing complete")
            return False

        self._queue_processor_active = True
        self._call("on_enable_generate", False)

        output_msg = f"Processing: {os.path.basename(job.output_path)}"
        self._call("on_status", output_msg)
        safe_print(f"[QUEUE] Processing job {job.job_id}: {job.get_display_name()}")
        self._log(f"Starting job {job.job_id} from queue")

        # Define callbacks
        def progress_callback(message: str) -> None:
            self.job_queue.update_job_progress(message)
            self._call("on_status", f"[Job {job.job_id}] {message}")
            safe_print(f"[Job {job.job_id}] {message}")
            self._log(f"Job {job.job_id} progress: {message}")

        def error_callback(error_type: str, title: str, message: str) -> None:
            if error_type == "warning":
                safe_print(f"[WARNING] Job {job.job_id}: {title}: {message}")
                self._log(f"Job {job.job_id}: {title}: {message}", "warning")
                self._call("on_status_warning", f"Job {job.job_id}: {title}: {message}")
            else:
                safe_print(f"[ERROR] Job {job.job_id}: {title}: {message}")
                self._log(f"Job {job.job_id}: {title}: {message}", "error")
                self._call("on_status_error", f"Job {job.job_id}: {title}: {message}")
                self.job_queue.complete_current_job(success=False, error_message=message)

        def completion_callback(success: bool, output_path: str) -> None:
            self.job_queue.complete_current_job(success=success)

            if success:
                success_msg = f"Job {job.job_id} completed: {os.path.basename(output_path)}"
                self._call("on_status_success", success_msg)
                safe_print(f"[SUCCESS] {success_msg}")
                self._log(success_msg)
            else:
                failure_msg = f"Job {job.job_id} failed"
                self._call("on_status_error", failure_msg)
                safe_print(f"[FAILED] {failure_msg}")
                self._log(failure_msg, "error")

            self._call("on_enable_generate", True)

            # Process next job after delay
            schedule = self.callbacks.get("schedule_callback")
            if schedule:
                schedule(1000, lambda: self.process_next_queued_job())

        # Start processing
        self.worker.start_processing_thread(
            job.input_files, job.output_path, job.target_duration,
            job.snippet_duration, job.aspect_ratio,
            job.export_settings,
            progress_callback, error_callback, completion_callback
        )

        return True

    # -------------------------------------------------------------------------
    # Job Queue Callbacks
    # -------------------------------------------------------------------------
    def _on_queue_update(self) -> None:
        """Handle queue update event."""
        self._call("on_queue_update")

    def _on_job_started(self, job: ProcessingJob) -> None:
        """Handle job started event."""
        self._log(f"Job {job.job_id} started")

    def _on_job_completed(self, job: ProcessingJob, success: bool) -> None:
        """Handle job completed event."""
        status = "completed" if success else "failed"
        self._log(f"Job {job.job_id} {status}")

    def _on_job_progress(self, job: ProcessingJob, message: str) -> None:
        """Handle job progress event."""
        pass  # Progress handled via direct callbacks
