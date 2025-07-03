# CLAUDE.md - Snippet Remixer Module

This file provides guidance to Claude Code when working with the snippet remixer module.

## Module Overview

The Snippet Remixer is a Tkinter-based application that creates video remixes by extracting and concatenating random snippets from multiple input videos. It uses direct FFmpeg commands for all video processing, providing professional-grade control over output quality and format.

## Architecture

### Entry Points
- **Via Launcher**: `src/snippet_remixer.py` or `src/snippet_remixer_modular.py`
- **Direct Module**: `python -m src.snippet_remixer.main`
- **Process Type**: Independent subprocess with stdout/stderr logging

### Module Structure

```
snippet_remixer/
├── __init__.py                # Package exports with lazy imports
├── main.py                   # Simple entry point
├── main_app.py              # Main Tkinter application
├── config_manager.py        # Configuration management
├── video_processor.py       # FFmpeg-based video processing
├── processing_worker.py     # Threading for background tasks
├── export_settings_dialog.py # Advanced export settings UI
└── utils.py                 # Utility functions
```

## Important Corrections

**Note**: The root CLAUDE.md contains some inaccuracies about this module:
- Uses **Tkinter**, not PyQt5
- Uses **direct FFmpeg commands**, not MoviePy
- Uses Python's **threading.Thread**, not QThread

## Configuration

**File**: `config/video_remixer_settings.json`

### Integration with Core
```python
# Attempts to use centralized config system
try:
    from core import get_config_manager
    self.core_config = get_config_manager()
except ImportError:
    self.core_config = None
```

### Settings Structure
```json
{
  "input_folder": "",
  "output_folder": "",
  "length_mode": "seconds",  // or "bpm"
  "snippet_length": 1.0,
  "bpm": 120,
  "beats": 4,
  "bars": 4,
  "aspect_ratio": "16:9",
  "export_settings": {
    "resolution": "1920x1080",
    "frame_rate": 30,
    "quality_mode": "crf",
    "crf_value": 23,
    "bitrate": "5M",
    "trim_start": "00:00:00",
    "trim_end": ""
  }
}
```

## Core Features

### 1. Length Control Modes

**Seconds Mode**:
- Direct duration specification
- Snippet length in seconds (0.1 - 10.0)

**BPM Mode**:
- Musical timing calculation
- Formula: `duration = (60 / bpm) * beats * bars`
- Allows rhythm-synced editing

### 2. Aspect Ratio Management

Supported ratios with intelligent resizing:
- **16:9** (1920x1080) - Standard widescreen
- **9:16** (1080x1920) - Vertical video
- **1:1** (1080x1080) - Square format
- **4:3** (1440x1080) - Classic TV
- **21:9** (2560x1080) - Ultrawide
- **Original** - Maintains source aspect ratio

### 3. Video Processing Pipeline

```python
def process_video(input_videos, output_path, settings):
    # 1. Analyze input videos for duration
    # 2. Generate random snippet definitions
    # 3. Cut snippets with aspect ratio adjustment
    # 4. Convert to intermediate .ts format
    # 5. Concatenate using concat demuxer
    # 6. Final encode with settings
```

## FFmpeg Integration

### Direct Command Execution
```python
# No MoviePy - direct FFmpeg subprocess calls
subprocess.run([
    'ffmpeg', '-i', input_file,
    '-ss', start_time,
    '-t', duration,
    # ... more parameters
], capture_output=True, text=True)
```

### Key FFmpeg Operations

1. **Duration Analysis**: `ffprobe -show_entries format=duration`
2. **Snippet Extraction**: `ffmpeg -ss {start} -i {input} -t {duration}`
3. **Aspect Ratio**: `-vf "scale=...,pad=...,setsar=1"`
4. **Concatenation**: Using concat demuxer with .ts intermediate files
5. **Quality Control**: CRF mode or bitrate mode encoding

## Threading Model

### Worker Thread Pattern
```python
class VideoProcessingThread(threading.Thread):
    def __init__(self, callback_dict):
        self.progress_callback = callback_dict.get('progress')
        self.error_callback = callback_dict.get('error')
        self.completion_callback = callback_dict.get('completion')
```

### Thread-Safe GUI Updates
```python
# Schedule GUI updates on main thread
self.root.after(0, lambda: self.status_label.config(text=message))
```

## Export Settings Dialog

Advanced options for professional control:

### Resolution Presets
- 4K (3840x2160)
- 1080p (1920x1080)
- 720p (1280x720)
- Custom dimensions

### Frame Rate Options
- 12, 24, 25, 30, 48, 50, 60 fps
- "Match Input" option

### Quality Modes
- **CRF Mode**: Constant Rate Factor (0-51)
- **Bitrate Mode**: Target bitrate (e.g., "5M")

### Input Trimming
- Start/end timestamps
- Format: HH:MM:SS or seconds

## Error Handling

Multi-layer error handling approach:

1. **FFmpeg Validation**: Check for FFmpeg/FFprobe in PATH
2. **Input Validation**: Verify video files and durations
3. **Process Errors**: Capture and parse FFmpeg stderr
4. **User Feedback**: Convert technical errors to friendly messages
5. **Cleanup**: Remove temporary files on failure

## Development Guidelines

### Best Practices

1. **FFmpeg Commands**: Always use lists, not string concatenation
2. **Path Handling**: Use proper quoting for spaces in paths
3. **Temp Files**: Create in system temp directory, clean up after
4. **Unicode Safety**: Use `safe_print()` for console output
5. **Progress Updates**: Provide meaningful status messages

### Common Patterns

```python
# Safe command construction
cmd = ['ffmpeg', '-y']  # -y for overwrite
cmd.extend(['-i', input_path])
cmd.extend(['-c:v', 'libx264'])
# ... more parameters

# Error checking
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    raise Exception(f"FFmpeg error: {result.stderr}")
```

## Testing

To test the module:

1. **Standalone**: `python src/snippet_remixer_modular.py`
2. **FFmpeg Check**: Verify FFmpeg/FFprobe are accessible
3. **Process Videos**: Test with various formats and aspect ratios
4. **Export Settings**: Verify all quality modes work
5. **Error Cases**: Test with invalid inputs, missing files

## Performance Considerations

1. **Intermediate Files**: Uses .ts format for fast concatenation
2. **Memory Usage**: Processes videos sequentially, not in memory
3. **Disk I/O**: Creates temp files in system temp directory
4. **CPU Usage**: FFmpeg uses all available cores by default

## Common Issues

### FFmpeg Not Found
```python
# Module checks PATH and provides helpful error
"FFmpeg not found. Please install FFmpeg and ensure it's in your PATH"
```

### Aspect Ratio Mismatches
- Module handles gracefully with padding/cropping
- Black bars added to maintain aspect ratio

### Audio Sync
- Preserves audio with `-c:a aac` encoding
- Handles videos without audio tracks

## Future Enhancements

Potential improvements:
1. Transition effects between snippets
2. Audio crossfading
3. GPU acceleration support
4. Batch processing multiple outputs
5. Preview before final render

# Enhanced Continuous Mode with Dynamic Settings

## Overview
The Continuous Mode in Snippet Remixer now supports real-time dynamic updates of all remix settings including BPM, duration, aspect ratio, and jitter settings. When you change any setting while continuous mode is running, the next generated clip will immediately use the new values without requiring a restart.

## Features

### Real-Time Setting Updates
- **BPM Changes**: Modify BPM from 225 to 230 and the next remix uses the new BPM instantly
- **Unit Changes**: Switch between beats, bars, measures without interruption
- **Duration Changes**: Adjust total duration in seconds mode
- **Aspect Ratio**: Change aspect ratios on-the-fly
- **Jitter Settings**: Enable/disable jitter or adjust intensity in real-time
- **Immediate Input Response**: Type new values and press Enter or click elsewhere - changes apply instantly

### Visual Feedback
- **Status Updates**: Clear messages when settings change between remixes
- **Current Settings Display**: Live counter shows active BPM/duration settings
- **Change Detection**: Explicit notifications when settings are updated
- **Logging**: Detailed logs of all setting changes for debugging

### Enhanced User Experience
- **No Restart Required**: Change settings without stopping continuous mode
- **Immediate Application**: Next remix uses new settings automatically
- **Visual Confirmation**: See exactly what settings are being used
- **Seamless Workflow**: Experiment with different settings while generating

## Usage Example

1. Start continuous mode with BPM 120, 4 bars
2. While running, change BPM to 140
3. Status shows: "Settings updated for remix #3: BPM 120.0 → 140.0"
4. Next remix automatically uses BPM 140
5. Counter displays: "Remixes created: 3 | Current: 140.0 BPM, 4 bars"

## Input Field Responsiveness

### Problem Solved
Previously, typed changes in input fields (BPM: 230, Units: 28) wouldn't register until you clicked another control. This caused confusion as the next remix would use outdated settings.

### Solution Implemented
- **Enter Key Binding**: Press Enter after typing to immediately apply changes
- **Focus Loss Detection**: Click elsewhere or tab away to trigger updates  
- **Instant Feedback**: Status shows "BPM updated to 230 - will apply to next remix"
- **Smart Focus Flow**: Enter moves BPM → Units → clears focus for smooth workflow

### Technical Details
- Added `<Return>` and `<FocusOut>` event bindings to all critical Entry widgets
- Real-time validation and feedback without requiring secondary interactions
- Immediate continuous counter updates reflecting new settings
- Blue status counter now reads live GUI values instead of cached settings

### Real-Time Blue Status Counter
**Issue Fixed**: The blue status text "Remixes created: 0 | Current: 225.0 BPM, 57 Beats" would not update in real-time when typing new values in BPM or Units fields.

**Solution**: Modified `update_continuous_counter()` to always read current live values from GUI widgets instead of cached settings. Now:
- Type "150" in BPM field → Press Enter → Status immediately shows "Current: 150 BPM"  
- Type "28" in Units field → Click elsewhere → Status immediately shows "28 Beats"
- Change dropdown from "Beat" to "Bar" → Status immediately shows "Bars"
- No more stale cached values - always shows what will be used for next remix

## Implementation Details

### Core Components
- `start_next_continuous_remix()`: Enhanced to detect and log setting changes
- `_get_current_settings()`: Captures live GUI values
- `_detect_setting_changes()`: Compares old vs new settings
- `update_continuous_counter()`: Shows real-time setting information
- Real-time trace callbacks update display as settings change

### Logging
All setting changes are logged with timestamps and details:
```
[CONTINUOUS] Settings updated for remix #2: BPM 225.0 → 230.0, Units 8 → 6
[CONTINUOUS] Starting remix #2 (BPM: 230.0, 6 bars)...
```

This enhancement makes continuous mode much more interactive and efficient for users who want to experiment with different settings while generating multiple remixes.