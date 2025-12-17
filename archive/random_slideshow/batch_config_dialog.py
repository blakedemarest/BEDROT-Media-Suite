# -*- coding: utf-8 -*-
"""
Batch Job Configuration Dialog for Random Slideshow Generator.

This module provides a dialog for configuring batch slideshow generation jobs.
"""

# Import helper ensures paths are set correctly
try:
    from _import_helper import setup_imports
    setup_imports()
except ImportError:
    pass

import os
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QComboBox,
    QPushButton, QDialogButtonBox, QFileDialog,
    QDoubleSpinBox, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt

from models import SlideshowJob


class BatchJobDialog(QDialog):
    """Dialog for configuring batch slideshow jobs."""
    
    def __init__(self, job: Optional[SlideshowJob] = None, parent=None):
        """
        Initialize the batch job configuration dialog.
        
        Args:
            job: Existing job to edit, or None for new job
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create new job or use existing
        self.job = job if job else SlideshowJob()
        self.is_new_job = job is None
        
        # Set window properties
        self.setWindowTitle("New Batch Job" if self.is_new_job else "Edit Batch Job")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Setup UI
        self.setup_ui()
        
        # Load existing job data if editing
        if not self.is_new_job:
            self.load_job_data()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Job identification section
        self._create_identification_section(layout)
        
        # Folders section
        self._create_folders_section(layout)
        
        # Generation settings section
        self._create_generation_section(layout)
        
        # Advanced settings section
        self._create_advanced_section(layout)
        
        # Dialog buttons
        self._create_buttons(layout)
        
        self.setLayout(layout)
    
    def _create_identification_section(self, parent_layout):
        """Create job identification section."""
        # Job name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Job Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a descriptive name for this job")
        name_layout.addWidget(self.name_input)
        parent_layout.addLayout(name_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority:"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 10)
        self.priority_spin.setValue(5)
        self.priority_spin.setToolTip("Higher values = higher priority (0-10)")
        priority_layout.addWidget(self.priority_spin)
        priority_layout.addStretch()
        parent_layout.addLayout(priority_layout)
    
    def _create_folders_section(self, parent_layout):
        """Create folders configuration section."""
        folders_group = QGroupBox("Folders")
        folders_layout = QVBoxLayout()
        
        # Image folder
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("Image Folder:"))
        self.img_folder_input = QLineEdit()
        self.img_folder_input.setPlaceholderText("Select folder containing images")
        self.img_browse_btn = QPushButton("Browse")
        self.img_browse_btn.clicked.connect(self.browse_image_folder)
        img_layout.addWidget(self.img_folder_input)
        img_layout.addWidget(self.img_browse_btn)
        folders_layout.addLayout(img_layout)
        
        # Output folder
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output Folder:"))
        self.out_folder_input = QLineEdit()
        self.out_folder_input.setPlaceholderText("Select folder for generated videos")
        self.out_browse_btn = QPushButton("Browse")
        self.out_browse_btn.clicked.connect(self.browse_output_folder)
        out_layout.addWidget(self.out_folder_input)
        out_layout.addWidget(self.out_browse_btn)
        folders_layout.addLayout(out_layout)
        
        folders_group.setLayout(folders_layout)
        parent_layout.addWidget(folders_group)
    
    def _create_generation_section(self, parent_layout):
        """Create generation settings section."""
        settings_group = QGroupBox("Generation Settings")
        settings_layout = QGridLayout()
        
        # Number of videos
        settings_layout.addWidget(QLabel("Number of Videos:"), 0, 0)
        self.num_videos_spin = QSpinBox()
        self.num_videos_spin.setRange(1, 1000)
        self.num_videos_spin.setValue(1)
        self.num_videos_spin.setToolTip("Number of videos to generate")
        settings_layout.addWidget(self.num_videos_spin, 0, 1)
        
        # Aspect ratio
        settings_layout.addWidget(QLabel("Aspect Ratio:"), 1, 0)
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9", "9:16"])
        self.aspect_combo.setToolTip("Video aspect ratio")
        settings_layout.addWidget(self.aspect_combo, 1, 1)
        
        # Video duration range
        settings_layout.addWidget(QLabel("Video Duration (sec):"), 2, 0)
        duration_layout = QHBoxLayout()
        
        self.duration_min_spin = QDoubleSpinBox()
        self.duration_min_spin.setRange(1.0, 300.0)
        self.duration_min_spin.setValue(12.0)
        self.duration_min_spin.setSingleStep(0.5)
        self.duration_min_spin.setDecimals(1)
        
        duration_layout.addWidget(self.duration_min_spin)
        duration_layout.addWidget(QLabel("to"))
        
        self.duration_max_spin = QDoubleSpinBox()
        self.duration_max_spin.setRange(1.0, 300.0)
        self.duration_max_spin.setValue(17.8)
        self.duration_max_spin.setSingleStep(0.5)
        self.duration_max_spin.setDecimals(1)
        
        duration_layout.addWidget(self.duration_max_spin)
        duration_layout.addStretch()
        settings_layout.addLayout(duration_layout, 2, 1)
        
        # Image duration range
        settings_layout.addWidget(QLabel("Image Duration (sec):"), 3, 0)
        img_duration_layout = QHBoxLayout()
        
        self.img_duration_min_spin = QDoubleSpinBox()
        self.img_duration_min_spin.setRange(0.05, 10.0)
        self.img_duration_min_spin.setValue(0.05)
        self.img_duration_min_spin.setSingleStep(0.05)
        self.img_duration_min_spin.setDecimals(2)
        
        img_duration_layout.addWidget(self.img_duration_min_spin)
        img_duration_layout.addWidget(QLabel("to"))
        
        self.img_duration_max_spin = QDoubleSpinBox()
        self.img_duration_max_spin.setRange(0.05, 10.0)
        self.img_duration_max_spin.setValue(0.45)
        self.img_duration_max_spin.setSingleStep(0.05)
        self.img_duration_max_spin.setDecimals(2)
        
        img_duration_layout.addWidget(self.img_duration_max_spin)
        img_duration_layout.addStretch()
        settings_layout.addLayout(img_duration_layout, 3, 1)
        
        settings_group.setLayout(settings_layout)
        parent_layout.addWidget(settings_group)
    
    def _create_advanced_section(self, parent_layout):
        """Create advanced settings section."""
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QGridLayout()
        
        # Frame rate
        advanced_layout.addWidget(QLabel("Frame Rate:"), 0, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        self.fps_spin.setSuffix(" fps")
        advanced_layout.addWidget(self.fps_spin, 0, 1)
        
        # Video quality
        advanced_layout.addWidget(QLabel("Video Quality:"), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low (1 Mbps)", "Medium (5 Mbps)", "High (10 Mbps)"])
        self.quality_combo.setCurrentIndex(2)  # Default to high
        advanced_layout.addWidget(self.quality_combo, 1, 1)
        
        advanced_group.setLayout(advanced_layout)
        parent_layout.addWidget(advanced_group)
    
    def _create_buttons(self, parent_layout):
        """Create dialog buttons."""
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept_job)
        buttons.rejected.connect(self.reject)
        parent_layout.addWidget(buttons)
    
    def browse_image_folder(self):
        """Browse for image folder."""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Image Folder", 
            self.img_folder_input.text() or os.path.expanduser("~")
        )
        if folder:
            self.img_folder_input.setText(folder)
    
    def browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Folder", 
            self.out_folder_input.text() or os.path.expanduser("~")
        )
        if folder:
            self.out_folder_input.setText(folder)
    
    def load_job_data(self):
        """Load existing job data into the form."""
        self.name_input.setText(self.job.name)
        self.priority_spin.setValue(self.job.priority)
        self.img_folder_input.setText(self.job.image_folder)
        self.out_folder_input.setText(self.job.output_folder)
        self.num_videos_spin.setValue(self.job.num_videos)
        self.aspect_combo.setCurrentText(self.job.aspect_ratio)
        
        # Duration ranges
        self.duration_min_spin.setValue(self.job.duration_range[0])
        self.duration_max_spin.setValue(self.job.duration_range[1])
        self.img_duration_min_spin.setValue(self.job.image_duration_range[0])
        self.img_duration_max_spin.setValue(self.job.image_duration_range[1])
        
        # Advanced settings
        self.fps_spin.setValue(self.job.fps)
        
        # Map quality to combo index
        quality_map = {"low": 0, "medium": 1, "high": 2}
        self.quality_combo.setCurrentIndex(quality_map.get(self.job.video_quality, 2))
    
    def validate_input(self) -> bool:
        """
        Validate user input.
        
        Returns:
            True if input is valid, False otherwise
        """
        # Check job name
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a job name.")
            return False
        
        # Check folders
        if not self.img_folder_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please select an image folder.")
            return False
        
        if not self.out_folder_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please select an output folder.")
            return False
        
        # Check if image folder exists
        if not os.path.exists(self.img_folder_input.text()):
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "The selected image folder does not exist."
            )
            return False
        
        # Check duration ranges
        if self.duration_min_spin.value() > self.duration_max_spin.value():
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "Minimum video duration cannot be greater than maximum."
            )
            return False
        
        if self.img_duration_min_spin.value() > self.img_duration_max_spin.value():
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "Minimum image duration cannot be greater than maximum."
            )
            return False
        
        return True
    
    def accept_job(self):
        """Accept the job configuration."""
        if not self.validate_input():
            return
        
        # Update job with form data
        self.job.name = self.name_input.text().strip()
        self.job.priority = self.priority_spin.value()
        self.job.image_folder = self.img_folder_input.text().strip()
        self.job.output_folder = self.out_folder_input.text().strip()
        self.job.num_videos = self.num_videos_spin.value()
        self.job.aspect_ratio = self.aspect_combo.currentText()
        
        # Duration ranges
        self.job.duration_range = (
            self.duration_min_spin.value(),
            self.duration_max_spin.value()
        )
        self.job.image_duration_range = (
            self.img_duration_min_spin.value(),
            self.img_duration_max_spin.value()
        )
        
        # Advanced settings
        self.job.fps = self.fps_spin.value()
        
        # Map combo index to quality
        quality_map = {0: "low", 1: "medium", 2: "high"}
        self.job.video_quality = quality_map.get(self.quality_combo.currentIndex(), "high")
        
        # Create output folder if it doesn't exist
        try:
            os.makedirs(self.job.output_folder, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Folder Creation Error",
                f"Could not create output folder: {e}"
            )
            return
        
        self.accept()
    
    def get_job(self) -> SlideshowJob:
        """
        Get the configured job.
        
        Returns:
            The configured slideshow job
        """
        return self.job