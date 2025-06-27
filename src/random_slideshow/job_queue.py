# -*- coding: utf-8 -*-
"""
Job Queue Management for Random Slideshow Batch Processing.

This module provides thread-safe job queue management with priority support.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

import queue
import threading
from typing import List, Optional, Dict, Callable
from datetime import datetime
from models import SlideshowJob, JobStatus


class JobQueue:
    """Thread-safe job queue with priority support and job management."""
    
    def __init__(self):
        """Initialize the job queue."""
        # Priority queue for pending jobs (negative priority for higher priority first)
        self._pending_queue = queue.PriorityQueue()
        
        # Dictionary to store all jobs by ID
        self._jobs_dict: Dict[str, SlideshowJob] = {}
        
        # Lock for thread-safe operations
        self._lock = threading.RLock()
        
        # Callbacks for queue events
        self._listeners: List[Callable] = []
        
        # Job counters
        self._total_jobs_added = 0
        self._total_jobs_completed = 0
        self._total_jobs_failed = 0
    
    def add_job(self, job: SlideshowJob) -> None:
        """
        Add a job to the queue.
        
        Args:
            job: The slideshow job to add
        """
        with self._lock:
            # Add to jobs dictionary
            self._jobs_dict[job.id] = job
            
            # Add to pending queue with priority
            # Use negative priority so higher values come first
            # Add timestamp to ensure FIFO for same priority
            priority_tuple = (-job.priority, job.created_at, job.id)
            self._pending_queue.put((priority_tuple, job))
            
            self._total_jobs_added += 1
            self._notify_listeners('job_added', job)
    
    def get_next_job(self) -> Optional[SlideshowJob]:
        """
        Get the next job from the queue.
        
        Returns:
            The next job to process, or None if queue is empty
        """
        try:
            # Get job from priority queue (non-blocking)
            priority_tuple, job = self._pending_queue.get_nowait()
            
            # Update job status
            with self._lock:
                if job.id in self._jobs_dict:
                    self._jobs_dict[job.id].status = JobStatus.PROCESSING
                    self._jobs_dict[job.id].started_at = datetime.now()
                    self._notify_listeners('job_started', job)
            
            return job
            
        except queue.Empty:
            return None
    
    def get_job(self, job_id: str) -> Optional[SlideshowJob]:
        """
        Get a specific job by ID.
        
        Args:
            job_id: The job ID to retrieve
            
        Returns:
            The job if found, None otherwise
        """
        with self._lock:
            return self._jobs_dict.get(job_id)
    
    def get_all_jobs(self) -> List[SlideshowJob]:
        """
        Get all jobs (pending, processing, completed).
        
        Returns:
            List of all jobs
        """
        with self._lock:
            return list(self._jobs_dict.values())
    
    def get_jobs_by_status(self, status: JobStatus) -> List[SlideshowJob]:
        """
        Get jobs filtered by status.
        
        Args:
            status: The job status to filter by
            
        Returns:
            List of jobs with the specified status
        """
        with self._lock:
            return [job for job in self._jobs_dict.values() if job.status == status]
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         error_message: Optional[str] = None) -> bool:
        """
        Update job status.
        
        Args:
            job_id: The job ID to update
            status: The new status
            error_message: Optional error message for failed jobs
            
        Returns:
            True if job was updated, False if job not found
        """
        with self._lock:
            if job_id not in self._jobs_dict:
                return False
            
            job = self._jobs_dict[job_id]
            job.status = status
            
            if error_message:
                job.error_message = error_message
            
            # Update timestamps
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.now()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                job.completed_at = datetime.now()
                
                # Update counters
                if status == JobStatus.COMPLETED:
                    self._total_jobs_completed += 1
                elif status == JobStatus.FAILED:
                    self._total_jobs_failed += 1
            
            self._notify_listeners('job_updated', job)
            return True
    
    def update_job_progress(self, job_id: str, progress: float, 
                           current_video_name: str = "") -> bool:
        """
        Update job progress.
        
        Args:
            job_id: The job ID to update
            progress: Current video progress (0-100)
            current_video_name: Name of the video being processed
            
        Returns:
            True if job was updated, False if job not found
        """
        with self._lock:
            if job_id not in self._jobs_dict:
                return False
            
            job = self._jobs_dict[job_id]
            job.current_video_progress = progress
            
            if current_video_name:
                job.current_video_name = current_video_name
            
            self._notify_listeners('job_progress', job)
            return True
    
    def increment_videos_completed(self, job_id: str, video_path: str) -> bool:
        """
        Increment the videos completed counter for a job.
        
        Args:
            job_id: The job ID to update
            video_path: Path to the generated video
            
        Returns:
            True if job was updated, False if job not found
        """
        with self._lock:
            if job_id not in self._jobs_dict:
                return False
            
            job = self._jobs_dict[job_id]
            job.videos_completed += 1
            job.generated_files.append(video_path)
            job.current_video_progress = 0.0  # Reset progress for next video
            
            self._notify_listeners('video_completed', job)
            return True
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or processing job.
        
        Args:
            job_id: The job ID to cancel
            
        Returns:
            True if job was cancelled, False if not found or already complete
        """
        with self._lock:
            if job_id not in self._jobs_dict:
                return False
            
            job = self._jobs_dict[job_id]
            
            # Can only cancel pending or processing jobs
            if job.status in (JobStatus.PENDING, JobStatus.PROCESSING):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                self._notify_listeners('job_cancelled', job)
                return True
            
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the queue entirely.
        
        Args:
            job_id: The job ID to remove
            
        Returns:
            True if job was removed, False if not found
        """
        with self._lock:
            if job_id in self._jobs_dict:
                job = self._jobs_dict[job_id]
                del self._jobs_dict[job_id]
                self._notify_listeners('job_removed', job)
                return True
            return False
    
    def clear_completed_jobs(self) -> int:
        """
        Remove all completed, failed, and cancelled jobs.
        
        Returns:
            Number of jobs removed
        """
        with self._lock:
            completed_jobs = [
                job_id for job_id, job in self._jobs_dict.items()
                if job.is_complete
            ]
            
            for job_id in completed_jobs:
                del self._jobs_dict[job_id]
            
            if completed_jobs:
                self._notify_listeners('completed_jobs_cleared', len(completed_jobs))
            
            return len(completed_jobs)
    
    def get_statistics(self) -> Dict:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            jobs_by_status = {}
            for status in JobStatus:
                jobs_by_status[status.value] = len(self.get_jobs_by_status(status))
            
            return {
                'total_jobs': len(self._jobs_dict),
                'jobs_by_status': jobs_by_status,
                'total_added': self._total_jobs_added,
                'total_completed': self._total_jobs_completed,
                'total_failed': self._total_jobs_failed,
                'pending_count': self._pending_queue.qsize()
            }
    
    def add_listener(self, callback: Callable) -> None:
        """
        Add a listener for queue events.
        
        Args:
            callback: Function to call on queue events
        """
        with self._lock:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable) -> None:
        """
        Remove a listener.
        
        Args:
            callback: The callback to remove
        """
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
    
    def _notify_listeners(self, event: str, data: any) -> None:
        """
        Notify all listeners of an event.
        
        Args:
            event: The event type
            data: Event data
        """
        for listener in self._listeners:
            try:
                listener(event, data)
            except Exception as e:
                print(f"Error notifying listener: {e}")
    
    def save_to_dict(self) -> Dict:
        """
        Save queue state to dictionary.
        
        Returns:
            Dictionary representation of queue state
        """
        with self._lock:
            return {
                'jobs': [job.to_dict() for job in self._jobs_dict.values()],
                'statistics': self.get_statistics()
            }
    
    def load_from_dict(self, data: Dict) -> None:
        """
        Load queue state from dictionary.
        
        Args:
            data: Dictionary with queue state
        """
        with self._lock:
            # Clear existing jobs
            self._jobs_dict.clear()
            self._pending_queue = queue.PriorityQueue()
            
            # Load jobs
            for job_data in data.get('jobs', []):
                job = SlideshowJob.from_dict(job_data)
                self._jobs_dict[job.id] = job
                
                # Re-add pending jobs to queue
                if job.status == JobStatus.PENDING:
                    priority_tuple = (-job.priority, job.created_at, job.id)
                    self._pending_queue.put((priority_tuple, job))