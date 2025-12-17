# Video Processing Logging System

## Overview

The Video Snippet Remixer now includes a comprehensive logging system designed to help diagnose aspect ratio issues and track the entire video processing pipeline. The logging system provides detailed information about:

- Source video dimensions and aspect ratios
- Target dimensions and aspect ratios
- FFmpeg filter chains being used
- Actual output dimensions achieved
- Processing times and performance metrics
- Errors and warnings with full context

## Key Features

### 1. Structured Logging Format

All log entries follow a consistent format with timestamp, level, module name, and optional video context:

```
2024-01-15 14:23:45,123 [INFO    ] snippet_remixer.video_processor  video_processor.py:145 [test_video.mp4] [1920x1080] [AR: 1.778] - Successfully extracted video information
```

### 2. Video Context Tracking

The logging system automatically tracks which video file is being processed and includes relevant dimensional information in each log entry. This makes it easy to trace issues with specific files.

### 3. Multi-Level Logging

- **Console Output**: Shows INFO level and above for user-friendly progress tracking
- **File Logging**: Captures DEBUG level and above for detailed troubleshooting
- **Error Log**: Separate file for ERROR level messages for quick issue identification

### 4. Log Rotation

Log files are automatically rotated when they reach 10MB, with up to 5 backup files kept. This prevents disk space issues while maintaining history.

## Log File Locations

By default, log files are created in the `logs/` subdirectory:

- `video_processor_YYYYMMDD.log` - Main processing log
- `video_processor_errors_YYYYMMDD.log` - Error-only log

## Understanding the Logs

### Aspect Ratio Processing

The logs provide detailed information about aspect ratio handling:

```
[INFO] Target aspect ratio: 16:9, mode: crop
[INFO] Intermediate resolution: 1920x1080 (aspect ratio: 1.778)
[DEBUG] FFmpeg filter chain: fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080
[INFO] Source dimensions: 1920x1080 (AR: 1.778)
[INFO] Target aspect ratio: 1.778 (16:9)
[INFO] Final output: 1920x1080 (AR: 1.778)
```

### FFmpeg Commands

All FFmpeg commands are logged in full for debugging:

```
[DEBUG] FFmpeg Command: ffmpeg -hide_banner -loglevel error -i "input.mp4" -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" -c:v libx264 -preset fast -crf 23 -y "output.mp4"
```

### Performance Metrics

Processing times are tracked and logged:

```
[INFO] Snippet 1 created successfully in 2.34s
[INFO] Concatenation completed in 1.56s
[INFO] ========================================
[INFO] PROCESSING SUMMARY
[INFO] Input Videos: 10
[INFO] Output File: remix_output.mp4
[INFO] Output Duration: 60.00s
[INFO] Processing Time: 45.23s
[INFO] Processing Speed: 1.33x realtime
[INFO] ========================================
```

## Using the Logging System

### For Developers

To add logging to new components:

```python
from .logging_config import get_logger, LoggingContext, log_ffmpeg_command

# Get a logger
logger = get_logger("my_module")

# Basic logging
logger.info("Processing started")

# With video context
with LoggingContext(video_filter, video_file="input.mp4", dimensions="1920x1080"):
    logger.info("Processing video")
    
# Log FFmpeg commands
log_ffmpeg_command(logger, ["ffmpeg", "-i", "input.mp4", ...])
```

### For Users

1. **Enable Debug Logging**: Set console level to DEBUG for maximum verbosity
2. **Check Log Files**: Look in the `logs/` directory for detailed information
3. **Share Logs**: When reporting issues, include relevant portions of the log files

## Diagnosing Aspect Ratio Issues

The enhanced logging makes it easy to diagnose aspect ratio problems:

1. **Check Source Dimensions**: Look for "Video Info:" entries to see source dimensions
2. **Verify Filter Chain**: Check "FFmpeg filter chain:" entries for the scaling/cropping operations
3. **Compare Output**: Look for "Final output:" entries to see if dimensions match expectations
4. **Watch for Warnings**: "Black bars detected" or "dimension mismatch" warnings indicate issues

## Example Log Analysis

Here's how to read the logs when diagnosing an aspect ratio issue:

```
[INFO] Video Info: source.mp4 | Dimensions: 1920x1080 | Aspect Ratio: 1.778 (1920:1080) | Duration: 60.00s
[INFO] Target aspect ratio: 9:16, mode: crop
[INFO] Intermediate resolution: 1080x1920 (aspect ratio: 0.563)
[DEBUG] FFmpeg filter chain: fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
[WARNING] Final aspect ratio 0.563 differs from target 0.562
```

This shows that:
- Source video is 16:9 landscape (1920x1080)
- Target is 9:16 portrait (1080x1920)
- The filter properly scales and crops
- There's a tiny rounding difference in the final aspect ratio

## Testing the Logging System

Run the test script to see the logging system in action:

```bash
python test_video_logging.py
```

This will create sample log entries demonstrating all logging features.