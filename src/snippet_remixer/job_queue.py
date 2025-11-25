# -*- coding: utf-8 -*-
"""
Job Queue Manager for Video Snippet Remixer.

This module provides a queue-based processing system for handling multiple
video generation tasks with different settings when continuous mode is disabled.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import threading


class JobStatus(Enum):
    """Status states for processing jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Represents a single video processing job with its settings."""
    
    # Job identification
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)
    
    # Job settings (captured at queue time)
    input_files: List[str] = field(default_factory=list)
    output_path: str = ""
    target_duration: float = 0.0
    snippet_duration: Any = 0.0
    aspect_ratio: str = "16:9"
    export_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata
    length_mode: str = "seconds"
    bpm: float = 120.0
    num_units: int = 4
    bpm_unit: str = "bars"
    tempo_mod_enabled: bool = False
    tempo_mod_start_bpm: float = 120.0
    tempo_mod_end_bpm: float = 120.0
    tempo_mod_duration_seconds: float = 15.0
    tempo_mod_points: List[Dict[str, float]] = field(default_factory=list)
    jitter_enabled: bool = False
    jitter_intensity: int = 50
    
    # Job status
    status: JobStatus = JobStatus.PENDING
    progress_message: str = ""
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def get_display_name(self) -> str:
        """Get a friendly display name for the job."""
        if self.length_mode == "BPM":
            if self.tempo_mod_enabled:
                return (f"Job #{self.job_id}: {self.tempo_mod_start_bpm:.0f}->"
                        f"{self.tempo_mod_end_bpm:.0f} BPM, {self.tempo_mod_duration_seconds:.1f}s")
            return f"Job #{self.job_id}: {self.bpm:.0f} BPM, {self.num_units} {self.bpm_unit}"
        else:
            return f"Job #{self.job_id}: {self.target_duration:.1f}s @ {self.aspect_ratio}"
    
    def get_duration_text(self) -> str:
        """Get formatted duration text."""
        if self.length_mode == "BPM":
            if self.tempo_mod_enabled:
                return (f"{self.tempo_mod_start_bpm:.0f}->{self.tempo_mod_end_bpm:.0f} BPM, "
                        f"{self.tempo_mod_duration_seconds:.1f}s")
            return f"{self.bpm:.0f} BPM, {self.num_units} {self.bpm_unit}"
        else:
            return f"{self.target_duration:.1f} seconds"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            'job_id': self.job_id,
            'created_at': self.created_at.isoformat(),
            'input_files': self.input_files,
            'output_path': self.output_path,
            'target_duration': self.target_duration,
            'snippet_duration': self.snippet_duration,
            'aspect_ratio': self.aspect_ratio,
            'export_settings': self.export_settings,
            'length_mode': self.length_mode,
            'bpm': self.bpm,
            'num_units': self.num_units,
            'bpm_unit': self.bpm_unit,
            'tempo_mod_enabled': self.tempo_mod_enabled,
            'tempo_mod_start_bpm': self.tempo_mod_start_bpm,
            'tempo_mod_end_bpm': self.tempo_mod_end_bpm,
            'tempo_mod_duration_seconds': self.tempo_mod_duration_seconds,
            'tempo_mod_points': self.tempo_mod_points,
            'jitter_enabled': self.jitter_enabled,
            'jitter_intensity': self.jitter_intensity,
            'status': self.status.value,
            'progress_message': self.progress_message,
            'error_message': self.error_message
        }


class JobQueue:
    """
    Manages a queue of video processing jobs.
    
    Features:
    - Add jobs with current settings snapshot
    - Process jobs sequentially
    - Track job status and progress
    - Allow cancellation of pending jobs
    - Provide queue statistics
    """
    
    def __init__(self, max_history: int = 50):
        """
        Initialize the job queue.
        
        Args:
            max_history: Maximum number of completed jobs to keep in history
        """
        self._lock = threading.RLock()
        self._pending_jobs: List[ProcessingJob] = []
        self._current_job: Optional[ProcessingJob] = None
        self._completed_jobs: List[ProcessingJob] = []
        self._max_history = max_history
        
        # Callbacks
        self._on_queue_update: Optional[Callable] = None
        self._on_job_start: Optional[Callable] = None
        self._on_job_complete: Optional[Callable] = None
        self._on_job_progress: Optional[Callable] = None
        
        # Statistics
        self._total_jobs_added = 0
        self._total_jobs_completed = 0
        self._total_jobs_failed = 0
        
    def set_callbacks(self, 
                      on_queue_update: Optional[Callable] = None,
                      on_job_start: Optional[Callable] = None,
                      on_job_complete: Optional[Callable] = None,
                      on_job_progress: Optional[Callable] = None):
        """Set callback functions for queue events."""
        self._on_queue_update = on_queue_update
        self._on_job_start = on_job_start
        self._on_job_complete = on_job_complete
        self._on_job_progress = on_job_progress
    
    def add_job(self, job: ProcessingJob) -> str:
        """
        Add a new job to the queue.
        
        Args:
            job: ProcessingJob instance with settings
            
        Returns:
            Job ID of the added job
        """
        with self._lock:
            self._pending_jobs.append(job)
            self._total_jobs_added += 1
            
            if self._on_queue_update:
                self._on_queue_update()
            
            return job.job_id
    
    def get_next_job(self) -> Optional[ProcessingJob]:
        """
        Get the next pending job from the queue.
        
        Returns:
            Next ProcessingJob or None if queue is empty
        """
        with self._lock:
            if not self._pending_jobs:
                return None
            
            job = self._pending_jobs.pop(0)
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
            self._current_job = job
            
            if self._on_job_start:
                self._on_job_start(job)
            if self._on_queue_update:
                self._on_queue_update()
            
            return job
    
    def complete_current_job(self, success: bool = True, error_message: str = ""):
        """
        Mark the current job as completed.
        
        Args:
            success: Whether the job completed successfully
            error_message: Error message if job failed
        """
        with self._lock:
            if not self._current_job:
                return
            
            self._current_job.completed_at = datetime.now()
            
            if success:
                self._current_job.status = JobStatus.COMPLETED
                self._total_jobs_completed += 1
            else:
                self._current_job.status = JobStatus.FAILED
                self._current_job.error_message = error_message
                self._total_jobs_failed += 1
            
            # Move to completed list
            self._completed_jobs.append(self._current_job)
            
            # Trim history if needed
            if len(self._completed_jobs) > self._max_history:
                self._completed_jobs = self._completed_jobs[-self._max_history:]
            
            if self._on_job_complete:
                self._on_job_complete(self._current_job)
            
            self._current_job = None
            
            if self._on_queue_update:
                self._on_queue_update()
    
    def update_job_progress(self, message: str):
        """Update progress message for current job."""
        with self._lock:
            if self._current_job:
                self._current_job.progress_message = message
                if self._on_job_progress:
                    self._on_job_progress(self._current_job, message)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            True if job was cancelled, False if not found or already processing
        """
        with self._lock:
            for i, job in enumerate(self._pending_jobs):
                if job.job_id == job_id:
                    job.status = JobStatus.CANCELLED
                    self._pending_jobs.pop(i)
                    self._completed_jobs.append(job)
                    
                    if self._on_queue_update:
                        self._on_queue_update()
                    
                    return True
            return False
    
    def clear_pending_jobs(self):
        """Cancel all pending jobs."""
        with self._lock:
            for job in self._pending_jobs:
                job.status = JobStatus.CANCELLED
                self._completed_jobs.append(job)
            
            self._pending_jobs.clear()
            
            if self._on_queue_update:
                self._on_queue_update()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.
        
        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            return {
                'pending_count': len(self._pending_jobs),
                'current_job': self._current_job.get_display_name() if self._current_job else None,
                'completed_count': len(self._completed_jobs),
                'total_added': self._total_jobs_added,
                'total_completed': self._total_jobs_completed,
                'total_failed': self._total_jobs_failed,
                'queue_empty': len(self._pending_jobs) == 0 and self._current_job is None
            }
    
    def get_pending_jobs(self) -> List[ProcessingJob]:
        """Get list of pending jobs."""
        with self._lock:
            return self._pending_jobs.copy()
    
    def get_current_job(self) -> Optional[ProcessingJob]:
        """Get the currently processing job."""
        with self._lock:
            return self._current_job
    
    def get_completed_jobs(self, limit: int = 10) -> List[ProcessingJob]:
        """
        Get recent completed jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of completed jobs (most recent first)
        """
        with self._lock:
            return list(reversed(self._completed_jobs[-limit:]))
    
    def is_processing(self) -> bool:
        """Check if a job is currently being processed."""
        with self._lock:
            return self._current_job is not None
    
    def has_pending_jobs(self) -> bool:
        """Check if there are pending jobs in the queue."""
        with self._lock:
            return len(self._pending_jobs) > 0
