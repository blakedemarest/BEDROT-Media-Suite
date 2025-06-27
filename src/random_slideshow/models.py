# -*- coding: utf-8 -*-
"""
Data Models for Random Slideshow Batch Processing.

This module contains data structures for managing batch slideshow generation jobs.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import uuid
from datetime import datetime


class JobStatus(Enum):
    """Enumeration of possible job statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SlideshowJob:
    """Represents a single slideshow generation job with all its configuration."""
    
    # Job identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    status: JobStatus = JobStatus.PENDING
    priority: int = 0  # Higher values = higher priority
    
    # Job configuration
    image_folder: str = ""
    output_folder: str = ""
    aspect_ratio: str = "16:9"  # "16:9" or "9:16"
    num_videos: int = 1
    duration_range: Tuple[float, float] = (12.0, 17.8)
    image_duration_range: Tuple[float, float] = (0.05, 0.45)
    
    # Output settings
    fps: int = 30
    video_quality: str = "high"  # "low", "medium", "high"
    
    # Progress tracking
    videos_completed: int = 0
    current_video_progress: float = 0.0
    current_video_name: str = ""
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    generated_files: List[str] = field(default_factory=list)
    
    @property
    def overall_progress(self) -> float:
        """Calculate overall job progress as percentage (0-100)."""
        if self.num_videos == 0:
            return 100.0
        
        # Calculate progress based on completed videos plus current video progress
        base_progress = (self.videos_completed / self.num_videos) * 100
        current_progress = (self.current_video_progress / 100.0) * (100.0 / self.num_videos)
        
        return min(base_progress + current_progress, 100.0)
    
    @property
    def is_active(self) -> bool:
        """Check if job is currently being processed."""
        return self.status == JobStatus.PROCESSING
    
    @property
    def is_complete(self) -> bool:
        """Check if job has finished (completed or failed)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
    
    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority,
            'image_folder': self.image_folder,
            'output_folder': self.output_folder,
            'aspect_ratio': self.aspect_ratio,
            'num_videos': self.num_videos,
            'duration_range': list(self.duration_range),
            'image_duration_range': list(self.image_duration_range),
            'fps': self.fps,
            'video_quality': self.video_quality,
            'videos_completed': self.videos_completed,
            'current_video_progress': self.current_video_progress,
            'current_video_name': self.current_video_name,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'generated_files': self.generated_files
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SlideshowJob':
        """Create job instance from dictionary."""
        job = cls()
        
        # Basic fields
        job.id = data.get('id', str(uuid.uuid4()))
        job.name = data.get('name', '')
        job.status = JobStatus(data.get('status', 'pending'))
        job.priority = data.get('priority', 0)
        
        # Configuration
        job.image_folder = data.get('image_folder', '')
        job.output_folder = data.get('output_folder', '')
        job.aspect_ratio = data.get('aspect_ratio', '16:9')
        job.num_videos = data.get('num_videos', 1)
        job.duration_range = tuple(data.get('duration_range', [12.0, 17.8]))
        job.image_duration_range = tuple(data.get('image_duration_range', [0.05, 0.45]))
        job.fps = data.get('fps', 30)
        job.video_quality = data.get('video_quality', 'high')
        
        # Progress
        job.videos_completed = data.get('videos_completed', 0)
        job.current_video_progress = data.get('current_video_progress', 0.0)
        job.current_video_name = data.get('current_video_name', '')
        job.error_message = data.get('error_message')
        
        # Timestamps
        if data.get('created_at'):
            job.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            job.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            job.completed_at = datetime.fromisoformat(data['completed_at'])
        
        # Results
        job.generated_files = data.get('generated_files', [])
        
        return job


@dataclass
class BatchSettings:
    """Global settings for batch processing."""
    max_workers: int = 4
    max_memory_mb: int = 2048  # Maximum memory usage in MB
    cache_size: int = 100  # Number of images to cache
    auto_start: bool = False  # Auto-start processing when jobs are added
    preserve_completed_jobs: bool = True  # Keep completed jobs in list
    completed_jobs_limit: int = 50  # Maximum completed jobs to keep