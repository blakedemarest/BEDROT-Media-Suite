# CLAUDE.md - Random Slideshow Module

This file provides guidance to Claude Code when working with the random slideshow module.

## Module Overview

The Random Slideshow module is a PyQt5-based application that generates continuous random slideshows from image folders. It supports both single generation mode (currently active) and advanced batch processing capabilities.

## Architecture

### Entry Points
- **Via Launcher**: `src/random_slideshow/main.py`
- **Standalone**: `python -m src.random_slideshow.main`
- **Process Type**: Independent subprocess with stdout/stderr logging

### Key Components

```
random_slideshow/
├── main.py                    # Entry point
├── main_app_simple.py         # Simple continuous generation (CURRENTLY USED)
├── main_app.py               # Full version with batch processing
├── config_manager.py         # Configuration management
├── image_processor.py        # Image processing and aspect ratios
├── slideshow_worker.py       # Single generation worker thread
├── batch_processor.py        # Concurrent batch orchestrator
├── batch_slideshow_worker.py # Batch-adapted worker
├── preset_manager.py         # Preset CRUD operations
├── models.py                # Data models for jobs
├── job_queue.py             # Job queue management
└── resource_manager.py       # Memory and cache management
```

### Configuration

**File**: `config/combined_random_config.json`

Key settings:
- Image and output folder paths
- Aspect ratio preferences
- Batch processing settings (when enabled)
- Job presets and history
- Resource limits

## Features

### Currently Active (Simple Mode)

1. **Continuous Generation**:
   - Generates videos indefinitely until stopped
   - Random duration: 12.0 - 17.8 seconds
   - Random image duration: 0.05 - 0.45 seconds per image
   - 30 FPS output

2. **Aspect Ratios**:
   - **16:9 (Landscape)**: Letterbox/pillarbox with black bars
   - **9:16 (Portrait)**: Scale and center-crop method

3. **Filename Pattern**: `random_slideshow_{timestamp}_{width}x{height}.mp4`

### Available but Inactive (Batch Mode)

- Queue-based job management
- Concurrent processing with worker threads
- Job priorities and progress tracking
- Resource monitoring and throttling
- Import/export presets

## Dependencies

### External Tools
- **FFmpeg**: Required by MoviePy for video encoding
- **Python 3.x**: Runtime environment

### Python Libraries
- **PyQt5**: GUI framework
- **MoviePy**: Video processing (`imageio[ffmpeg]`)
- **Pillow**: Image manipulation
- **NumPy**: Array operations
- **psutil** (optional): Resource monitoring

## Threading Model

### Main Thread
- PyQt5 GUI and event loop
- All UI updates via signals

### Worker Thread (RandomSlideshowWorker)
```python
class RandomSlideshowWorker(QThread):
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    generation_count_updated = pyqtSignal(int)
```

Key behaviors:
- Continuous generation loop in `run()`
- Graceful shutdown via `stop_generation` flag
- Thread-safe communication via Qt signals

## Image Processing Strategies

### 9:16 Portrait Mode
```python
# Scale to fill height, then center crop width
scale_factor = target_height / img.height
new_width = int(img.width * scale_factor)
# Crop center portion to target_width
```

### 16:9 Landscape Mode
```python
# Calculate scaling to fit within bounds
width_scale = target_width / img.width
height_scale = target_height / img.height
scale_factor = min(width_scale, height_scale)
# Add black bars as needed
```

## Memory Management

Critical for preventing memory leaks:
```python
# After each video generation
clip.close()
for img_clip in clips:
    img_clip.close()
del clip, clips
import gc
gc.collect()
```

## Error Handling

1. **Image Errors**: Skip corrupt/invalid images, use black placeholder
2. **Memory Errors**: Automatic garbage collection and clip cleanup
3. **File System Errors**: Validate paths before processing
4. **Thread Errors**: Report via signals to main thread

## Integration with Launcher

The module integrates seamlessly:
1. Launched as subprocess from `launcher.py`
2. All print statements appear in launcher log
3. Process termination handled gracefully
4. No direct IPC - communication via stdout

## Common Issues and Solutions

### PIL Version Compatibility
```python
# Handle both old and new PIL versions
if hasattr(img, 'Resampling'):
    resample = img.Resampling.LANCZOS
else:
    resample = img.ANTIALIAS
```

### Unicode Output
```python
# Use safe_print for cross-platform compatibility
from ..reel_tracker.utils import safe_print
safe_print(f"Status: {message}")
```

### Resource Exhaustion
- Implement clip cleanup after each generation
- Monitor memory usage in batch mode
- Use LRU cache for frequently accessed images

## Development Tips

1. **Testing**: Run standalone with `python src/random_slideshow/main.py`
2. **Debugging**: Enable verbose MoviePy logging
3. **Performance**: Use resource manager for batch operations
4. **UI Updates**: Always use Qt signals from worker threads

## Future Enhancements

The full batch processing system is implemented but not currently active. To enable:
1. Import `MainWindow` from `main_app.py` instead of `main_app_simple.py`
2. Uncomment batch processing UI elements
3. Test resource management with concurrent jobs