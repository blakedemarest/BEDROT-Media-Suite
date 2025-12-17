# -*- coding: utf-8 -*-
"""
Batch Manager Widget for Random Slideshow Generator.

This module provides the main UI widget for managing batch slideshow generation.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

import os
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QProgressBar,
    QLabel, QSpinBox, QHeaderView, QMenu,
    QMessageBox, QAbstractItemView, QFileDialog, QDialog
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QColor

from models import SlideshowJob, JobStatus, BatchSettings
from batch_processor import BatchProcessor
from batch_config_dialog import BatchJobDialog


class BatchManagerWidget(QWidget):
    """Widget for managing batch slideshow generation."""
    
    # Column indices for the job table
    COL_NAME = 0
    COL_STATUS = 1
    COL_PROGRESS = 2
    COL_VIDEOS = 3
    COL_PRIORITY = 4
    COL_FOLDER = 5
    COL_ACTIONS = 6
    
    # Status colors
    STATUS_COLORS = {
        JobStatus.PENDING: QColor(200, 200, 200),
        JobStatus.PROCESSING: QColor(100, 200, 255),
        JobStatus.COMPLETED: QColor(100, 255, 100),
        JobStatus.FAILED: QColor(255, 100, 100),
        JobStatus.CANCELLED: QColor(255, 200, 100)
    }
    
    def __init__(self, config_manager=None, parent=None):
        """
        Initialize the batch manager widget.
        
        Args:
            config_manager: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        
        # Create batch processor with error handling
        try:
            settings = self._load_batch_settings()
            self.processor = BatchProcessor(settings, config_manager)
        except Exception as e:
            print(f"Error creating batch processor: {e}")
            # Create a minimal processor with default settings
            self.processor = BatchProcessor(BatchSettings(), config_manager)
        
        # Job tracking
        self.job_rows: Dict[str, int] = {}  # job_id -> row index
        
        # Setup UI with error handling
        try:
            self.setup_ui()
            self.connect_signals()
        except Exception as e:
            print(f"Error setting up batch manager UI: {e}")
            # Create minimal UI to prevent crash
            layout = QVBoxLayout()
            error_label = QLabel(f"Error initializing batch processing: {e}")
            layout.addWidget(error_label)
            self.setLayout(layout)
            return
        
        # Update timer for UI refresh (deferred start)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        # Timer will be started in showEvent
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("<h2>Batch Processing</h2>")
        layout.addWidget(title_label)
        
        # Control buttons
        self._create_control_buttons(layout)
        
        # Job table
        self._create_job_table(layout)
        
        # Statistics section
        self._create_statistics_section(layout)
        
        self.setLayout(layout)
    
    def _create_control_buttons(self, parent_layout):
        """Create control buttons section."""
        btn_layout = QHBoxLayout()
        
        # Job management buttons
        self.add_job_btn = QPushButton("Add Job")
        self.add_job_btn.setToolTip("Add a new batch job")
        
        self.load_preset_btn = QPushButton("Load Preset")
        self.load_preset_btn.setToolTip("Load a saved job preset")
        
        self.save_preset_btn = QPushButton("Save Preset")
        self.save_preset_btn.setToolTip("Save selected job as preset")
        
        btn_layout.addWidget(self.add_job_btn)
        btn_layout.addWidget(self.load_preset_btn)
        btn_layout.addWidget(self.save_preset_btn)
        
        btn_layout.addWidget(QLabel("  |  "))  # Separator
        
        # Processing control buttons
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addWidget(QLabel("  |  "))  # Separator
        
        # Queue management
        self.clear_completed_btn = QPushButton("Clear Completed")
        self.clear_completed_btn.setToolTip("Remove all completed jobs from the list")
        
        self.cancel_all_btn = QPushButton("Cancel All")
        self.cancel_all_btn.setToolTip("Cancel all pending and active jobs")
        
        btn_layout.addWidget(self.clear_completed_btn)
        btn_layout.addWidget(self.cancel_all_btn)
        
        btn_layout.addStretch()
        
        # Worker count control
        btn_layout.addWidget(QLabel("Max Workers:"))
        self.worker_spin = QSpinBox()
        self.worker_spin.setRange(1, 16)
        self.worker_spin.setValue(self.processor.settings.max_workers)
        self.worker_spin.setToolTip("Maximum number of concurrent workers")
        btn_layout.addWidget(self.worker_spin)
        
        parent_layout.addLayout(btn_layout)
    
    def _create_job_table(self, parent_layout):
        """Create the job table."""
        self.job_table = QTableWidget()
        self.job_table.setColumnCount(7)
        self.job_table.setHorizontalHeaderLabels([
            "Name", "Status", "Progress", "Videos", "Priority", "Folder", "Actions"
        ])
        
        # Table properties
        self.job_table.setAlternatingRowColors(True)
        self.job_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.job_table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Column sizing
        header = self.job_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_PROGRESS, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_VIDEOS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_PRIORITY, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_FOLDER, QHeaderView.Interactive)
        header.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeToContents)
        
        self.job_table.setColumnWidth(self.COL_PROGRESS, 200)
        self.job_table.setColumnWidth(self.COL_FOLDER, 150)
        
        parent_layout.addWidget(self.job_table)
    
    def _create_statistics_section(self, parent_layout):
        """Create statistics section."""
        stats_layout = QHBoxLayout()
        
        # Overall progress
        stats_layout.addWidget(QLabel("Overall Progress:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setTextVisible(True)
        stats_layout.addWidget(self.overall_progress)
        
        # Statistics labels
        self.stats_label = QLabel("Pending: 0 | Processing: 0 | Completed: 0 | Failed: 0")
        stats_layout.addWidget(self.stats_label)
        
        # Active workers indicator
        self.workers_label = QLabel("Workers: 0/4")
        stats_layout.addWidget(self.workers_label)
        
        parent_layout.addLayout(stats_layout)
    
    def connect_signals(self):
        """Connect UI signals."""
        # Button signals
        self.add_job_btn.clicked.connect(self.add_job)
        self.load_preset_btn.clicked.connect(self.load_preset)
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.start_btn.clicked.connect(self.start_processing)
        self.pause_btn.clicked.connect(self.pause_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
        self.clear_completed_btn.clicked.connect(self.clear_completed)
        self.cancel_all_btn.clicked.connect(self.cancel_all)
        self.worker_spin.valueChanged.connect(self.update_worker_count)
        
        # Table signals
        self.job_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Processor signals
        self.processor.job_started.connect(self.on_job_started)
        self.processor.job_progress.connect(self.on_job_progress)
        self.processor.job_video_completed.connect(self.on_job_video_completed)
        self.processor.job_completed.connect(self.on_job_completed)
        self.processor.job_failed.connect(self.on_job_failed)
        self.processor.job_cancelled.connect(self.on_job_cancelled)
        self.processor.queue_updated.connect(self.refresh_table)
        self.processor.worker_status_changed.connect(self.on_worker_status_changed)
    
    @pyqtSlot()
    def add_job(self):
        """Add a new job."""
        dialog = BatchJobDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            job = dialog.get_job()
            self.processor.add_job(job)
            self.refresh_table()
    
    @pyqtSlot()
    def load_preset(self):
        """Load a job preset."""
        if not self.config_manager:
            return
        
        presets = self.config_manager.get_job_presets()
        if not presets:
            QMessageBox.information(self, "No Presets", "No job presets have been saved yet.")
            return
        
        # Create preset selection dialog
        from PyQt5.QtWidgets import QInputDialog
        preset_names = [p.get("name", "Unnamed") for p in presets]
        
        preset_name, ok = QInputDialog.getItem(
            self, "Load Preset", "Select a preset to load:",
            preset_names, 0, False
        )
        
        if ok and preset_name:
            preset = self.config_manager.get_job_preset(preset_name)
            if preset:
                # Create job from preset
                job = SlideshowJob()
                
                # Copy preset settings to job
                for key in ["name", "image_folder", "output_folder", "aspect_ratio",
                           "num_videos", "duration_range", "image_duration_range",
                           "fps", "video_quality", "priority"]:
                    if key in preset:
                        setattr(job, key, preset[key])
                
                # Open dialog to confirm/edit
                dialog = BatchJobDialog(job, parent=self)
                if dialog.exec_() == QDialog.Accepted:
                    job = dialog.get_job()
                    self.processor.add_job(job)
                    self.refresh_table()
    
    @pyqtSlot()
    def save_preset(self):
        """Save selected job as preset."""
        if not self.config_manager:
            return
        
        # Get selected job
        selected_items = self.job_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a job to save as preset.")
            return
        
        row = selected_items[0].row()
        job_id = self.job_table.item(row, 0).data(Qt.UserRole)
        job = self.processor.job_queue.get_job(job_id)
        
        if not job:
            return
        
        # Get preset name
        from PyQt5.QtWidgets import QInputDialog
        preset_name, ok = QInputDialog.getText(
            self, "Save Preset", "Enter a name for this preset:",
            text=job.name
        )
        
        if ok and preset_name:
            # Create preset from job
            preset = {
                "name": preset_name,
                "image_folder": job.image_folder,
                "output_folder": job.output_folder,
                "aspect_ratio": job.aspect_ratio,
                "num_videos": job.num_videos,
                "duration_range": list(job.duration_range),
                "image_duration_range": list(job.image_duration_range),
                "fps": job.fps,
                "video_quality": job.video_quality,
                "priority": job.priority
            }
            
            self.config_manager.add_job_preset(preset)
            QMessageBox.information(
                self, "Preset Saved", 
                f"Job preset '{preset_name}' has been saved."
            )
    
    @pyqtSlot()
    def start_processing(self):
        """Start batch processing."""
        self.processor.start()
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
    
    @pyqtSlot()
    def pause_processing(self):
        """Pause batch processing."""
        self.processor.pause()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
    
    @pyqtSlot()
    def stop_processing(self):
        """Stop batch processing."""
        reply = QMessageBox.question(
            self,
            "Stop Processing",
            "Are you sure you want to stop all processing?\nActive jobs will be cancelled.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.processor.stop(wait=False)
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
    
    @pyqtSlot()
    def clear_completed(self):
        """Clear completed jobs."""
        count = self.processor.clear_completed_jobs()
        self.refresh_table()
        if count > 0:
            QMessageBox.information(
                self,
                "Jobs Cleared",
                f"Removed {count} completed job(s) from the list."
            )
    
    @pyqtSlot()
    def cancel_all(self):
        """Cancel all jobs."""
        reply = QMessageBox.question(
            self,
            "Cancel All Jobs",
            "Are you sure you want to cancel all pending and active jobs?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = self.processor.cancel_all_jobs()
            self.refresh_table()
            QMessageBox.information(
                self,
                "Jobs Cancelled",
                f"Cancelled {count} job(s)."
            )
    
    @pyqtSlot(int)
    def update_worker_count(self, value):
        """Update maximum worker count."""
        self.processor.set_max_workers(value)
        self._save_batch_settings()
    
    @pyqtSlot(str)
    def on_job_started(self, job_id):
        """Handle job started event."""
        self.refresh_job_row(job_id)
    
    @pyqtSlot(str, float)
    def on_job_progress(self, job_id, progress):
        """Handle job progress update."""
        if job_id in self.job_rows:
            row = self.job_rows[job_id]
            progress_item = self.job_table.item(row, self.COL_PROGRESS)
            if progress_item:
                progress_item.setText(f"{progress:.1f}%")
    
    @pyqtSlot(str, str)
    def on_job_video_completed(self, job_id, video_path):
        """Handle video completion."""
        self.refresh_job_row(job_id)
    
    @pyqtSlot(str)
    def on_job_completed(self, job_id):
        """Handle job completion."""
        self.refresh_job_row(job_id)
        
        # Show notification
        job = self.processor.job_queue.get_job(job_id)
        if job:
            QMessageBox.information(
                self,
                "Job Completed",
                f"Job '{job.name}' completed successfully!\n"
                f"Generated {job.videos_completed} video(s)."
            )
    
    @pyqtSlot(str, str)
    def on_job_failed(self, job_id, error):
        """Handle job failure."""
        self.refresh_job_row(job_id)
        
        # Show error
        job = self.processor.job_queue.get_job(job_id)
        if job:
            QMessageBox.critical(
                self,
                "Job Failed",
                f"Job '{job.name}' failed:\n{error}"
            )
    
    @pyqtSlot(str)
    def on_job_cancelled(self, job_id):
        """Handle job cancellation."""
        self.refresh_job_row(job_id)
    
    @pyqtSlot(int, int)
    def on_worker_status_changed(self, active, maximum):
        """Handle worker status change."""
        self.workers_label.setText(f"Workers: {active}/{maximum}")
    
    def refresh_table(self):
        """Refresh the entire job table."""
        # Save current selection
        selected_job_ids = set()
        for row in range(self.job_table.rowCount()):
            if self.job_table.item(row, 0).isSelected():
                selected_job_ids.add(self.job_table.item(row, 0).data(Qt.UserRole))
        
        # Clear table
        self.job_table.setRowCount(0)
        self.job_rows.clear()
        
        # Get all jobs
        jobs = self.processor.job_queue.get_all_jobs()
        
        # Sort jobs by status and priority
        jobs.sort(key=lambda j: (
            j.status != JobStatus.PROCESSING,  # Processing first
            j.status != JobStatus.PENDING,      # Then pending
            -j.priority,                        # Then by priority
            j.created_at                        # Then by creation time
        ))
        
        # Add jobs to table
        for job in jobs:
            self._add_job_to_table(job)
            
            # Restore selection
            if job.id in selected_job_ids:
                row = self.job_rows[job.id]
                for col in range(self.job_table.columnCount()):
                    item = self.job_table.item(row, col)
                    if item:
                        item.setSelected(True)
    
    def refresh_job_row(self, job_id: str):
        """Refresh a specific job row."""
        job = self.processor.job_queue.get_job(job_id)
        if not job:
            return
        
        if job_id not in self.job_rows:
            self._add_job_to_table(job)
        else:
            self._update_job_row(job)
    
    def _add_job_to_table(self, job: SlideshowJob):
        """Add a job to the table."""
        row = self.job_table.rowCount()
        self.job_table.insertRow(row)
        self.job_rows[job.id] = row
        
        # Create table items
        name_item = QTableWidgetItem(job.name)
        name_item.setData(Qt.UserRole, job.id)  # Store job ID
        status_item = QTableWidgetItem(job.status.value.title())
        progress_item = QTableWidgetItem(f"{job.overall_progress:.1f}%")
        videos_item = QTableWidgetItem(f"{job.videos_completed}/{job.num_videos}")
        priority_item = QTableWidgetItem(str(job.priority))
        folder_item = QTableWidgetItem(os.path.basename(job.image_folder))
        folder_item.setToolTip(job.image_folder)
        
        # Set items
        self.job_table.setItem(row, self.COL_NAME, name_item)
        self.job_table.setItem(row, self.COL_STATUS, status_item)
        self.job_table.setItem(row, self.COL_PROGRESS, progress_item)
        self.job_table.setItem(row, self.COL_VIDEOS, videos_item)
        self.job_table.setItem(row, self.COL_PRIORITY, priority_item)
        self.job_table.setItem(row, self.COL_FOLDER, folder_item)
        
        # Create action buttons
        action_widget = self._create_action_buttons(job)
        self.job_table.setCellWidget(row, self.COL_ACTIONS, action_widget)
        
        # Set row color based on status
        self._update_job_row_color(row, job.status)
    
    def _update_job_row(self, job: SlideshowJob):
        """Update an existing job row."""
        if job.id not in self.job_rows:
            return
        
        row = self.job_rows[job.id]
        
        # Update items
        self.job_table.item(row, self.COL_STATUS).setText(job.status.value.title())
        self.job_table.item(row, self.COL_PROGRESS).setText(f"{job.overall_progress:.1f}%")
        self.job_table.item(row, self.COL_VIDEOS).setText(f"{job.videos_completed}/{job.num_videos}")
        
        # Update action buttons
        action_widget = self._create_action_buttons(job)
        self.job_table.setCellWidget(row, self.COL_ACTIONS, action_widget)
        
        # Update row color
        self._update_job_row_color(row, job.status)
    
    def _update_job_row_color(self, row: int, status: JobStatus):
        """Update row background color based on status."""
        color = self.STATUS_COLORS.get(status, QColor(255, 255, 255))
        for col in range(self.job_table.columnCount() - 1):  # Exclude actions column
            item = self.job_table.item(row, col)
            if item:
                item.setBackground(color)
    
    def _create_action_buttons(self, job: SlideshowJob) -> QWidget:
        """Create action buttons for a job."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Edit button
        if job.status == JobStatus.PENDING:
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda: self.edit_job(job.id))
            layout.addWidget(edit_btn)
        
        # Cancel button
        if job.status in (JobStatus.PENDING, JobStatus.PROCESSING):
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(lambda: self.cancel_job(job.id))
            layout.addWidget(cancel_btn)
        
        # Open folder button
        if job.status == JobStatus.COMPLETED and job.generated_files:
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda: self.open_output_folder(job))
            layout.addWidget(open_btn)
        
        # Remove button
        if job.is_complete:
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda: self.remove_job(job.id))
            layout.addWidget(remove_btn)
        
        widget.setLayout(layout)
        return widget
    
    def edit_job(self, job_id: str):
        """Edit a pending job."""
        job = self.processor.job_queue.get_job(job_id)
        if not job or job.status != JobStatus.PENDING:
            return
        
        dialog = BatchJobDialog(job, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_job_row(job_id)
    
    def cancel_job(self, job_id: str):
        """Cancel a specific job."""
        job = self.processor.job_queue.get_job(job_id)
        if not job:
            return
        
        reply = QMessageBox.question(
            self,
            "Cancel Job",
            f"Are you sure you want to cancel job '{job.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.processor.cancel_job(job_id)
    
    def remove_job(self, job_id: str):
        """Remove a job from the queue."""
        job = self.processor.job_queue.get_job(job_id)
        if not job:
            return
        
        self.processor.job_queue.remove_job(job_id)
        self.refresh_table()
    
    def open_output_folder(self, job: SlideshowJob):
        """Open the output folder for a completed job."""
        if job.generated_files:
            folder = os.path.dirname(job.generated_files[0])
            if os.path.exists(folder):
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(folder)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', folder])
                else:  # Linux
                    subprocess.Popen(['xdg-open', folder])
    
    def show_context_menu(self, position):
        """Show context menu for job table."""
        item = self.job_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        job_id = self.job_table.item(row, 0).data(Qt.UserRole)
        job = self.processor.job_queue.get_job(job_id)
        if not job:
            return
        
        menu = QMenu(self)
        
        # Add actions based on job status
        if job.status == JobStatus.PENDING:
            edit_action = menu.addAction("Edit Job")
            edit_action.triggered.connect(lambda: self.edit_job(job_id))
        
        if job.status in (JobStatus.PENDING, JobStatus.PROCESSING):
            cancel_action = menu.addAction("Cancel Job")
            cancel_action.triggered.connect(lambda: self.cancel_job(job_id))
        
        if job.is_complete:
            remove_action = menu.addAction("Remove Job")
            remove_action.triggered.connect(lambda: self.remove_job(job_id))
        
        if job.status == JobStatus.COMPLETED and job.generated_files:
            menu.addSeparator()
            open_action = menu.addAction("Open Output Folder")
            open_action.triggered.connect(lambda: self.open_output_folder(job))
        
        menu.exec_(self.job_table.mapToGlobal(position))
    
    def update_statistics(self):
        """Update statistics display."""
        try:
            # Check if processor exists and is valid
            if not hasattr(self, 'processor') or not self.processor:
                return
                
            stats = self.processor.get_statistics()
            
            # Update statistics label
            self.stats_label.setText(
                f"Pending: {stats['jobs_by_status'].get('pending', 0)} | "
                f"Processing: {stats['jobs_by_status'].get('processing', 0)} | "
                f"Completed: {stats['jobs_by_status'].get('completed', 0)} | "
                f"Failed: {stats['jobs_by_status'].get('failed', 0)}"
            )
            
            # Update overall progress
            total_jobs = stats['total_jobs']
            if total_jobs > 0:
                completed = stats['jobs_by_status'].get('completed', 0)
                failed = stats['jobs_by_status'].get('failed', 0)
                cancelled = stats['jobs_by_status'].get('cancelled', 0)
                finished = completed + failed + cancelled
                
                # Calculate overall progress including partial progress of active jobs
                overall_progress = 0
                try:
                    jobs = self.processor.job_queue.get_all_jobs()
                    for job in jobs:
                        overall_progress += job.overall_progress
                    
                    if jobs:
                        overall_progress = overall_progress / len(jobs)
                except:
                    # Fallback to simple calculation
                    overall_progress = (finished / total_jobs) * 100 if total_jobs > 0 else 0
                
                self.overall_progress.setValue(int(overall_progress))
                self.overall_progress.setFormat(f"{overall_progress:.1f}% ({finished}/{total_jobs} jobs)")
            else:
                self.overall_progress.setValue(0)
                self.overall_progress.setFormat("No jobs")
                
            # Reset error count on successful update
            if hasattr(self, '_update_error_count'):
                self._update_error_count = 0
                
        except Exception as e:
            print(f"Error updating statistics: {e}")
            # Stop the timer if repeated errors occur
            if hasattr(self, '_update_error_count'):
                self._update_error_count += 1
                if self._update_error_count > 5:
                    if hasattr(self, 'update_timer') and self.update_timer:
                        self.update_timer.stop()
                    print("Stopping statistics updates due to repeated errors")
            else:
                self._update_error_count = 1
    
    def _load_batch_settings(self) -> BatchSettings:
        """Load batch settings from configuration."""
        try:
            if self.config_manager:
                settings_dict = self.config_manager.get_batch_settings()
                settings = BatchSettings()
                
                # Update settings from config
                for key, value in settings_dict.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                
                return settings
        except Exception as e:
            print(f"Error loading batch settings: {e}")
        
        return BatchSettings()
    
    def _save_batch_settings(self):
        """Save batch settings to configuration."""
        if self.config_manager:
            settings_dict = {
                "max_workers": self.processor.settings.max_workers,
                "max_memory_mb": self.processor.settings.max_memory_mb,
                "cache_size": self.processor.settings.cache_size,
                "auto_start": self.processor.settings.auto_start,
                "preserve_completed_jobs": self.processor.settings.preserve_completed_jobs,
                "completed_jobs_limit": self.processor.settings.completed_jobs_limit
            }
            self.config_manager.set_batch_settings(settings_dict)
    
    def showEvent(self, event):
        """Handle widget show event."""
        super().showEvent(event)
        # Start the update timer when widget is shown (if it exists)
        if hasattr(self, 'update_timer') and self.update_timer and not self.update_timer.isActive():
            self.update_timer.start(2000)  # Update every 2 seconds
    
    def closeEvent(self, event):
        """Handle widget close event."""
        # Stop processor if it exists
        if hasattr(self, 'processor') and self.processor:
            self.processor.stop(wait=True)
        
        # Stop update timer if it exists
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
        
        event.accept()