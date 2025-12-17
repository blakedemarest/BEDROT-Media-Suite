# Output Dimension Verification Implementation

## Overview
This implementation adds output dimension verification to the Video Snippet Remixer to ensure videos are processed correctly without black bars or unexpected dimension changes.

## Components Modified

### 1. VideoProcessor (`src/snippet_remixer/video_processor.py`)
Added the `verify_output_dimensions` method that:
- Uses ffprobe with JSON output to get accurate video dimensions
- Optionally uses FFmpeg's blackdetect filter to detect black bars
- Returns a tuple of (actual_width, actual_height, has_black_bars)
- Logs warnings when dimensions don't match expectations

Key features:
- **JSON parsing**: Uses ffprobe's JSON output format for reliable parsing
- **Black bar detection**: Uses `blackdetect=d=0.1:pix_th=0.10` filter
- **Error handling**: Gracefully handles missing tools, invalid files, and parsing errors

### 2. ProcessingWorker (`src/snippet_remixer/processing_worker.py`)
Enhanced to:
- Call `verify_output_dimensions` after successful video processing
- Calculate expected dimensions based on aspect ratio settings
- Show warnings to users if black bars are detected
- Optionally verify individual snippet dimensions during processing

### 3. ExportSettingsDialog (`src/snippet_remixer/export_settings_dialog.py`)
Added new UI section "Output Verification" with options:
- **Check for black bars**: Enables black bar detection in final output
- **Verify snippet dimensions**: Enables verification of individual snippets (slower)

## Usage

### From UI
1. Open Export Settings dialog
2. Enable "Check for black bars in output" option
3. Process video normally
4. If black bars are detected, a warning will be shown

### From Code
```python
processor = VideoProcessor(script_dir)

# Basic dimension check
width, height, has_bars = processor.verify_output_dimensions(
    "output.mp4", 
    expected_width=1920, 
    expected_height=1080,
    check_black_bars=True
)

if has_bars:
    print("Warning: Black bars detected!")
```

## Testing
Run the test script to verify functionality:
```bash
python test_output_verification.py
```

The test script creates sample videos and verifies:
1. Normal video without black bars
2. Video with artificial black bars
3. Dimension mismatch detection
4. Basic dimension retrieval

## FFmpeg/ffprobe Requirements
- ffprobe: For dimension detection (JSON output)
- ffmpeg: For blackdetect filter (optional)

## Performance Considerations
- Basic dimension check: Very fast (< 100ms)
- Black bar detection: Slower (processes entire video)
- Snippet verification: Adds overhead to each snippet

## Future Enhancements
- Detect letterboxing vs pillarboxing specifically
- Configurable black detection thresholds
- Export dimension verification report
- Auto-correction of detected issues