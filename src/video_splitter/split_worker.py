# -*- coding: utf-8 -*-
"""
Background worker for running FFmpeg split jobs.
"""

from __future__ import annotations

import queue
import subprocess
import threading
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

from .ffmpeg_splitter import build_segment_command, generate_segments, probe_video
from .models import SplitJob, SplitSegment
from .utils import ensure_directory, safe_print

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[dict], None]


class SplitWorker:
    """Execute split jobs sequentially on a background thread."""

    def __init__(self, log_callback: Optional[LogCallback] = None, progress_callback: Optional[ProgressCallback] = None):
        self.log = log_callback or safe_print
        self.progress_callback = progress_callback
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_process: Optional[subprocess.Popen[str]] = None
        self._queue: queue.Queue[SplitJob] = queue.Queue()
        self._job_lock = threading.Lock()
        self._on_complete: Optional[Callable[[bool], None]] = None

    def start(self, jobs: Iterable[SplitJob], on_complete: Optional[Callable[[bool], None]] = None) -> bool:
        """Start processing jobs. Returns False if already running."""
        with self._job_lock:
            if self.is_running:
                self.log("[video_splitter] Worker already running")
                return False

            self._on_complete = on_complete
            self._stop_event.clear()

            while not self._queue.empty():
                self._queue.get_nowait()

            for job in jobs:
                resolved_dir = ensure_directory(job.output_dir)
                job.output_dir = Path(resolved_dir)
                self._queue.put(job)

            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return True

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self) -> None:
        """Request stop and terminate active FFmpeg process."""
        self._stop_event.set()
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
            except Exception:
                pass

    def _emit_progress(self, payload: dict) -> None:
        if self.progress_callback:
            try:
                self.progress_callback(payload)
            except Exception:
                pass

    def _run(self) -> None:
        success = True
        try:
            total_jobs = self._queue.qsize()
            job_index = 0
            while not self._stop_event.is_set() and not self._queue.empty():
                job = self._queue.get_nowait()
                job_index += 1
                if not self._process_job(job, job_index, total_jobs):
                    success = False
                    break
        finally:
            if self._on_complete:
                self._on_complete(success and not self._stop_event.is_set())
            self._thread = None
            self._current_process = None
            self._stop_event.clear()

    def _process_job(self, job: SplitJob, job_index: int, total_jobs: int) -> bool:
        self.log(f"[video_splitter] Processing {job.source_path.name} ({job_index}/{total_jobs})")
        try:
            metadata = probe_video(job.source_path)
        except Exception as exc:
            self.log(f"[video_splitter] ERROR: Failed to probe {job.source_path}: {exc}")
            self._emit_progress({"type": "job_error", "job_index": job_index, "message": str(exc)})
            return False

        segments = generate_segments(job, metadata.duration)
        if not segments:
            self.log(f"[video_splitter] WARNING: No segments generated for {job.source_path}")
            return True

        for segment in segments:
            if self._stop_event.is_set():
                self.log("[video_splitter] Stop requested, aborting job")
                return False

            if segment.output_path.exists() and not job.overwrite_existing:
                self.log(f"[video_splitter] Skipping existing clip: {segment.output_path}")
                self._emit_progress(
                    {
                        "type": "segment_skipped",
                        "job_index": job_index,
                        "segment_index": segment.index,
                        "total_segments": len(segments),
                        "file": str(segment.output_path),
                    }
                )
                continue

            if not self._run_segment(job, segment):
                return False

            self._emit_progress(
                {
                    "type": "segment_complete",
                    "job_index": job_index,
                    "segment_index": segment.index,
                    "total_segments": len(segments),
                    "file": str(segment.output_path),
                }
            )

        self._emit_progress({"type": "job_complete", "job_index": job_index, "total_jobs": total_jobs})
        return True

    def _run_segment(self, job: SplitJob, segment: SplitSegment) -> bool:
        command = build_segment_command(job, segment)
        self.log(f"[video_splitter] Running {' '.join(command)}")

        try:
            self._current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except FileNotFoundError:
            self.log("[video_splitter] ERROR: FFmpeg not found in PATH.")
            return False

        assert self._current_process.stdout is not None
        for line in self._current_process.stdout:
            normalized = line.strip()
            if normalized:
                self.log(f"[video_splitter] {normalized}")
            if self._stop_event.is_set():
                self.log("[video_splitter] Terminating FFmpeg due to stop request")
                self._current_process.terminate()
                self._current_process.wait()
                return False

        return_code = self._current_process.wait()
        if return_code != 0:
            self.log(f"[video_splitter] ERROR: FFmpeg exited with code {return_code}")
            return False
        return True
