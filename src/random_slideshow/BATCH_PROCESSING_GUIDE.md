# Random Slideshow Batch Processing Guide

## Overview

The Random Slideshow Generator now includes powerful batch processing capabilities, allowing users to generate multiple slideshow videos concurrently with different configurations. This guide explains the new features and how to use them effectively.

## Key Features

### 1. **Dual Mode Operation**
- **Single Generation Mode**: The original continuous generation mode for quick, simple slideshow creation
- **Batch Processing Mode**: New mode for managing multiple slideshow generation jobs with different parameters

### 2. **Job Queue System**
- Priority-based job scheduling (higher priority jobs run first)
- Concurrent job execution with configurable worker threads
- Real-time progress tracking for individual jobs
- Job status tracking: Pending → Processing → Completed/Failed/Cancelled

### 3. **Job Configuration**
Each batch job can be configured with:
- **Job Name**: Descriptive name for easy identification
- **Priority**: 0-10 (higher values = higher priority)
- **Folders**: Separate input/output folders per job
- **Aspect Ratio**: 16:9 or 9:16 per job
- **Number of Videos**: How many videos to generate
- **Duration Settings**: Video and image duration ranges
- **Quality Settings**: Frame rate and video quality

### 4. **Performance Optimizations**
- **Image Caching**: Frequently used images are cached in memory for faster processing
- **Resource Monitoring**: System resources (CPU/Memory) are monitored to prevent overload
- **Concurrent Processing**: Multiple videos can be generated simultaneously
- **Smart Worker Management**: Automatic adjustment based on system capabilities

### 5. **Persistence Features**
- **Job Presets**: Save frequently used configurations as presets
- **Job History**: Track completed jobs with statistics
- **Settings Persistence**: All batch settings are saved between sessions
- **Queue Recovery**: Job queue state can be recovered after restart

## Using Batch Processing

### Getting Started
1. Launch the Random Slideshow Generator
2. Click on the "Batch Processing" tab
3. Click "Add Job" to create your first batch job

### Creating a Job
1. Enter a descriptive job name
2. Set the priority (0-10, higher = more urgent)
3. Select input folder containing images
4. Select output folder for generated videos
5. Configure generation settings:
   - Number of videos to generate
   - Aspect ratio (16:9 or 9:16)
   - Video duration range
   - Image duration range
6. Configure advanced settings:
   - Frame rate (FPS)
   - Video quality
7. Click "OK" to add the job to the queue

### Managing Jobs
- **Start Processing**: Begin processing all pending jobs
- **Pause**: Pause processing (active jobs will complete)
- **Stop**: Stop all processing immediately
- **Cancel Job**: Cancel a specific pending or active job
- **Clear Completed**: Remove completed jobs from the list

### Using Presets
1. Configure a job with your desired settings
2. Select the job in the list
3. Click "Save Preset" and enter a name
4. To use a preset: Click "Load Preset" and select from saved presets

### Monitoring Progress
- **Job Table**: Shows all jobs with status, progress, and actions
- **Progress Bars**: Individual progress for each job
- **Overall Progress**: Combined progress for all jobs
- **Worker Status**: Shows active/maximum worker threads
- **Statistics**: Real-time statistics on job completion

## Best Practices

### Performance Tips
1. **Worker Count**: Set max workers based on CPU cores (typically 1-4)
2. **Memory Usage**: Monitor memory when processing high-resolution images
3. **Batch Size**: Process similar jobs together for better cache utilization
4. **Priority**: Use priority to ensure urgent jobs complete first

### Organization Tips
1. **Naming**: Use descriptive job names with dates/categories
2. **Folders**: Organize output by project or date
3. **Presets**: Create presets for common configurations
4. **History**: Review job history to track productivity

### Error Handling
- Jobs that fail are marked with error messages
- Failed jobs can be edited and resubmitted
- Check output folder permissions before processing
- Ensure sufficient disk space for video generation

## Technical Details

### Architecture Components
- `models.py`: Data structures for jobs and settings
- `job_queue.py`: Thread-safe priority queue implementation
- `batch_processor.py`: Concurrent job execution engine
- `batch_slideshow_worker.py`: Individual job processing logic
- `batch_config_dialog.py`: Job configuration UI
- `batch_manager_widget.py`: Main batch processing interface
- `resource_manager.py`: Image caching and resource monitoring
- `config_manager.py`: Extended with batch settings persistence

### Configuration Storage
Batch processing settings are stored in the main configuration file:
- Job presets
- Batch settings (worker count, limits)
- Job history (last 50 completed jobs)
- Queue state (for recovery)

### Resource Management
- **Image Cache**: LRU cache with configurable size and TTL
- **Memory Monitoring**: Prevents excessive memory usage
- **CPU Monitoring**: Adjusts processing based on system load
- **Automatic Cleanup**: Resources are freed after job completion

## Troubleshooting

### Common Issues

1. **Jobs not starting**
   - Check if processing is started (click "Start")
   - Verify image folder contains valid images
   - Check output folder write permissions

2. **Slow performance**
   - Reduce worker count if system is overloaded
   - Check available memory
   - Close other applications

3. **Failed jobs**
   - Check error message in job status
   - Verify folder paths are correct
   - Ensure sufficient disk space

### Debug Information
- Check console output for detailed error messages
- Resource statistics show system usage
- Job history tracks completion times and success rates

## Future Enhancements

Potential improvements for future versions:
- Job templates with multiple output formats
- Scheduling jobs for specific times
- Network folder support
- GPU acceleration for video encoding
- Advanced filtering and sorting options
- Export job reports and statistics