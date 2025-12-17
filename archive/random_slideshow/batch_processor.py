# -*- coding: utf-8 -*-
"""
Batch Processor for Random Slideshow Generation.

This module manages concurrent slideshow generation with a thread pool.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal

from models import SlideshowJob, JobStatus, BatchSettings
from job_queue import JobQueue


class BatchProcessor(QObject):
    """Manages concurrent slideshow generation with configurable worker threads."""
    
    # Signals for UI updates
    job_started = pyqtSignal(str)  # job_id
    job_progress = pyqtSignal(str, float)  # job_id, progress
    job_video_completed = pyqtSignal(str, str)  # job_id, video_path
    job_completed = pyqtSignal(str)  # job_id
    job_failed = pyqtSignal(str, str)  # job_id, error
    job_cancelled = pyqtSignal(str)  # job_id
    queue_updated = pyqtSignal()
    worker_status_changed = pyqtSignal(int, int)  # active_workers, max_workers
    
    def __init__(self, settings: Optional[BatchSettings] = None, config_manager=None):
        """
        Initialize the batch processor.
        
        Args:
            settings: Batch processing settings
            config_manager: Configuration manager for persistence
        """
        super().__init__()
        
        # Settings
        self.settings = settings or BatchSettings()
        self.config_manager = config_manager
        
        # Job queue
        self.job_queue = JobQueue()
        self.job_queue.add_listener(self._on_queue_event)
        
        # Thread pool (with error handling)
        try:
            self.executor = ThreadPoolExecutor(max_workers=self.settings.max_workers)
        except Exception as e:
            print(f"Warning: Failed to create thread pool with {self.settings.max_workers} workers: {e}")
            # Fallback to single worker
            self.settings.max_workers = 1
            self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Active workers tracking
        self.active_workers: Dict[str, Future] = {}  # job_id -> Future
        self.active_threads: Dict[str, threading.Thread] = {}  # job_id -> Thread
        
        # Processing state
        self._running = False
        self._lock = threading.Lock()
        
        # Statistics
        self._total_videos_generated = 0
        self._total_processing_time = 0.0
        
        # Health check
        self._job_start_times: Dict[str, float] = {}  # Track when jobs started
    
    def add_job(self, job: SlideshowJob) -> None:
        """
        Add a job to the processing queue.
        
        Args:
            job: The slideshow job to add
        """
        self.job_queue.add_job(job)
        
        # Auto-start if enabled
        if self.settings.auto_start and self._running:
            self._try_start_next_job()
    
    def start(self) -> None:
        """Start the batch processor."""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            
            # Start processing jobs up to max_workers
            for _ in range(self.settings.max_workers):
                self._try_start_next_job()
    
    def stop(self, wait: bool = True) -> None:
        """
        Stop the batch processor.
        
        Args:
            wait: Whether to wait for active jobs to complete
        """
        with self._lock:
            self._running = False
            
            # Cancel all active workers
            for job_id in list(self.active_workers.keys()):
                self.cancel_job(job_id)
        
        if wait:
            self.executor.shutdown(wait=True)
        else:
            self.executor.shutdown(wait=False)
    
    def pause(self) -> None:
        """Pause processing (don't start new jobs but let active ones finish)."""
        with self._lock:
            self._running = False
    
    def resume(self) -> None:
        """Resume processing."""
        self.start()
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a specific job.
        
        Args:
            job_id: The job ID to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        with self._lock:
            # Cancel in queue
            if self.job_queue.cancel_job(job_id):
                # If job is active, stop the worker
                if job_id in self.active_workers:
                    future = self.active_workers[job_id]
                    future.cancel()
                    
                    # Try to interrupt the thread if possible
                    if job_id in self.active_threads:
                        # Note: Thread interruption is complex in Python
                        # Worker should check for cancellation periodically
                        pass
                
                self.job_cancelled.emit(job_id)
                return True
            
            return False
    
    def cancel_all_jobs(self) -> int:
        """
        Cancel all pending and active jobs.
        
        Returns:
            Number of jobs cancelled
        """
        cancelled = 0
        
        # Get all pending and processing jobs
        jobs = self.job_queue.get_all_jobs()
        for job in jobs:
            if job.status in (JobStatus.PENDING, JobStatus.PROCESSING):
                if self.cancel_job(job.id):
                    cancelled += 1
        
        return cancelled
    
    def clear_completed_jobs(self) -> int:
        """
        Clear all completed jobs from the queue.
        
        Returns:
            Number of jobs cleared
        """
        return self.job_queue.clear_completed_jobs()
    
    def get_active_worker_count(self) -> int:
        """Get the number of currently active workers."""
        with self._lock:
            return len(self.active_workers)
    
    def set_max_workers(self, max_workers: int) -> None:
        """
        Update the maximum number of concurrent workers.
        
        Args:
            max_workers: New maximum worker count
        """
        old_executor = None
        should_start_more = False
        additional_workers = 0
        active_count = 0
        
        with self._lock:
            old_max = self.settings.max_workers
            self.settings.max_workers = max_workers
            
            # Create new executor with updated worker count
            old_executor = self.executor
            try:
                self.executor = ThreadPoolExecutor(max_workers=max_workers)
            except Exception as e:
                print(f"Warning: Failed to create thread pool with {max_workers} workers: {e}")
                # Restore old settings
                self.settings.max_workers = old_max
                self.executor = old_executor
                return
            
            # Get current state before releasing lock (don't call methods that acquire lock)
            active_count = len(self.active_workers)
            should_start_more = max_workers > old_max and self._running
            additional_workers = max_workers - active_count if should_start_more else 0
        
        # Shutdown old executor outside of lock
        if old_executor:
            old_executor.shutdown(wait=False)
        
        # Start additional workers outside of lock
        if additional_workers > 0:
            for _ in range(additional_workers):
                self._try_start_next_job()
        
        self.worker_status_changed.emit(active_count, max_workers)
    
    def _try_start_next_job(self) -> bool:
        """
        Try to start the next job from the queue.
        
        Returns:
            True if a job was started, False otherwise
        """
        with self._lock:
            if not self._running:
                return False
            
            # Check if we can start more workers
            if self.get_active_worker_count() >= self.settings.max_workers:
                return False
            
            # Get next job from queue
            job = self.job_queue.get_next_job()
            if not job:
                return False
            
            # Submit job to thread pool
            future = self.executor.submit(self._run_job, job)
            self.active_workers[job.id] = future
            
            # Add callback for cleanup
            future.add_done_callback(lambda f: self._on_job_done(job.id, f))
            
            return True
    
    def _run_job(self, job: SlideshowJob) -> None:
        """
        Run a single job in a worker thread.
        
        Args:
            job: The job to run
        """
        # Store current thread for potential interruption
        with self._lock:
            self.active_threads[job.id] = threading.current_thread()
            self._job_start_times[job.id] = time.time()
        
        worker = None
        try:
            # Emit start signal
            self.job_started.emit(job.id)
            
            # Import here to avoid circular imports
            from batch_slideshow_worker import BatchSlideshowWorker
            
            # Create worker for this job
            worker = BatchSlideshowWorker(job, self.job_queue)
            
            # Store signal connections for cleanup
            progress_connection = worker.progress_updated.connect(
                lambda p: self._on_job_progress(job.id, p)
            )
            video_connection = worker.video_completed.connect(
                lambda path: self._on_video_completed(job.id, path)
            )
            error_connection = worker.error_occurred.connect(
                lambda msg: self._on_job_error(job.id, msg)
            )
            
            # Run the job
            success = worker.run()
            
            if success:
                # Job completed successfully
                self.job_queue.update_job_status(job.id, JobStatus.COMPLETED)
                self.job_completed.emit(job.id)
                
                # Save to job history if config manager available
                self._save_job_to_history(job)
            else:
                # Job was cancelled or stopped
                if job.status != JobStatus.CANCELLED:
                    self.job_queue.update_job_status(job.id, JobStatus.FAILED)
                    self.job_failed.emit(job.id, "Job stopped or failed")
            
        except Exception as e:
            # Job failed with exception
            error_msg = f"Job failed with error: {str(e)}"
            self.job_queue.update_job_status(job.id, JobStatus.FAILED, error_msg)
            self.job_failed.emit(job.id, error_msg)
            print(f"Error running job {job.id}: {e}")
            
        finally:
            # Disconnect signals to prevent memory leaks
            if worker:
                try:
                    worker.progress_updated.disconnect()
                    worker.video_completed.disconnect()
                    worker.error_occurred.disconnect()
                except:
                    pass  # Ignore errors during cleanup
                    
                # Delete the worker to free resources
                del worker
                
            # Clean up thread reference and timing info
            with self._lock:
                if job.id in self.active_threads:
                    del self.active_threads[job.id]
                if job.id in self._job_start_times:
                    del self._job_start_times[job.id]
    
    def _on_job_done(self, job_id: str, future: Future) -> None:
        """
        Callback when a job future completes.
        
        Args:
            job_id: The job ID
            future: The completed future
        """
        # Determine if we should start next job before acquiring lock
        should_start_next = False
        active_count = 0
        max_workers = 0
        
        with self._lock:
            # Remove from active workers
            if job_id in self.active_workers:
                del self.active_workers[job_id]
            
            # Get current counts while holding lock
            active_count = len(self.active_workers)
            max_workers = self.settings.max_workers
            
            # Check if we should start next job
            should_start_next = self._running and active_count < max_workers
        
        # Emit signal outside of lock to avoid potential deadlock
        self.worker_status_changed.emit(active_count, max_workers)
        
        # Try to start next job outside of lock to avoid nested locking
        if should_start_next:
            self._try_start_next_job()
    
    def _on_job_progress(self, job_id: str, progress: float) -> None:
        """
        Handle job progress update.
        
        Args:
            job_id: The job ID
            progress: Progress percentage (0-100)
        """
        self.job_progress.emit(job_id, progress)
    
    def _on_video_completed(self, job_id: str, video_path: str) -> None:
        """
        Handle video completion.
        
        Args:
            job_id: The job ID
            video_path: Path to the generated video
        """
        self._total_videos_generated += 1
        self.job_video_completed.emit(job_id, video_path)
    
    def _on_job_error(self, job_id: str, error_msg: str) -> None:
        """
        Handle job error.
        
        Args:
            job_id: The job ID
            error_msg: Error message
        """
        self.job_queue.update_job_status(job_id, JobStatus.FAILED, error_msg)
        self.job_failed.emit(job_id, error_msg)
    
    def _on_queue_event(self, event: str, data: any) -> None:
        """
        Handle queue events.
        
        Args:
            event: Event type
            data: Event data
        """
        # Emit queue updated signal for any queue changes
        self.queue_updated.emit()
    
    def get_statistics(self) -> Dict:
        """
        Get processor statistics.
        
        Returns:
            Dictionary with processor statistics
        """
        queue_stats = self.job_queue.get_statistics()
        
        with self._lock:
            processor_stats = {
                'active_workers': self.get_active_worker_count(),
                'max_workers': self.settings.max_workers,
                'total_videos_generated': self._total_videos_generated,
                'processor_running': self._running
            }
        
        # Add health check info
        health_info = self._check_health()
        
        return {**queue_stats, **processor_stats, 'health': health_info}
    
    def _save_job_to_history(self, job: SlideshowJob) -> None:
        """
        Save completed job to history.
        
        Args:
            job: The completed job
        """
        if self.config_manager and job.is_complete:
            try:
                # Convert job to dictionary for storage
                job_data = job.to_dict()
                self.config_manager.add_to_job_history(job_data)
            except Exception as e:
                print(f"Error saving job to history: {e}")
    
    def _check_health(self) -> Dict:
        """
        Check health of active jobs and detect stuck threads.
        
        Returns:
            Dictionary with health information
        """
        import time
        current_time = time.time()
        stuck_jobs = []
        
        with self._lock:
            for job_id, start_time in self._job_start_times.items():
                # Consider a job stuck if it's been running for more than 10 minutes
                if current_time - start_time > 600:
                    stuck_jobs.append({
                        'job_id': job_id,
                        'duration': current_time - start_time
                    })
        
        return {
            'stuck_jobs': stuck_jobs,
            'active_threads': len(self.active_threads),
            'healthy': len(stuck_jobs) == 0
        }