# Video-Based Aspect Ratio Migration

This document describes the enhanced aspect ratio migration system that scans actual video files to determine their true dimensions, rather than relying on filename or keyword heuristics.

## Overview

The original aspect ratio migration assumed all files with "REEL" in the name were 9:16, but actual video files could be:
- **Square (1:1)** - 1080x1080, 1024x1024
- **Portrait (9:16, 4:5)** - 1080x1920, 1080x1350
- **Landscape (16:9, 21:9)** - 1920x1080, 2560x1080

The enhanced system addresses this by scanning the actual video files using FFprobe.

## Features

### Video File Scanning
- **FFprobe Integration**: Uses FFprobe to get actual video dimensions
- **Path Conversion**: Automatically converts Windows paths (`E:\`) to WSL mounts (`/mnt/e/`)
- **Robust Error Handling**: Graceful handling of missing or inaccessible files
- **Caching**: Scan results are cached to avoid redundant operations

### Enhanced Aspect Ratio Detection
- **Priority-Based Detection**:
  1. **Scan actual video files** (NEW - highest priority)
  2. Explicit width/height columns
  3. Resolution string parsing
  4. Platform/format hints
  5. Default to 'unknown'

### Comprehensive Categorization
Supports all common aspect ratios:
- `9:16` - Vertical (Reels, Shorts, TikTok)
- `16:9` - Horizontal (YouTube, landscape)
- `1:1` - Square (Instagram posts)
- `4:5` - Portrait (Instagram posts)
- `21:9` - Ultrawide
- `4:3` - Traditional TV
- And more...

### Advanced Features
- **Idempotent Operations**: Safe to run multiple times
- **Automatic Backups**: Creates timestamped backups
- **Detailed Reporting**: Comprehensive statistics and error reporting
- **Tolerance Matching**: 5% tolerance for close aspect ratio matches

## Usage

### Quick Start

```bash
# Navigate to tools directory
cd "/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-media-suite/tools"

# Dry run to preview changes
python apply_video_aspect_ratio_migration.py --dry-run

# Apply the migration (creates backup automatically)
python apply_video_aspect_ratio_migration.py

# Verbose output for debugging
python apply_video_aspect_ratio_migration.py --verbose
```

### Command Line Options

```bash
python apply_video_aspect_ratio_migration.py [OPTIONS]

Options:
  --dry-run              Preview changes without saving
  --verbose              Enable detailed logging
  --overwrite            Overwrite existing Aspect Ratio column
  -h, --help             Show help message
```

### Custom CSV File

```bash
# Use with custom CSV file
python video_aspect_ratio_migrator.py /path/to/custom.csv --dry-run

# Save to different output file
python video_aspect_ratio_migrator.py input.csv --output output.csv
```

## Requirements

### System Dependencies
- **FFmpeg/FFprobe**: Required for video scanning
  - Linux/WSL: `sudo apt install ffmpeg`
  - Windows: Download from https://ffmpeg.org/
- **Python 3.6+**: Required for execution

### Python Dependencies
- `pandas` - CSV file manipulation
- `subprocess` - FFprobe execution
- `pathlib` - Path handling
- Standard library modules

### File Structure Requirements
The CSV must have a column containing video file paths. The system looks for:
- `FilePath`
- `File Path` 
- `Clip Filename`
- `filename`
- `path`

## Expected CSV Format

```csv
Clip Filename,Reel Type,Platform,Description
E:/VIDEOS/RELEASE CONTENT/PIG1987_RENEGADE_PIPELINE/PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_135.mp4,REEL,Instagram,Vertical video
E:/VIDEOS/RELEASE CONTENT/ZONE_A0/ZONE_A0_SQUARE_POST_20250615_120000_001.mp4,SQUARE,Instagram,Square post
E:/VIDEOS/RELEASE CONTENT/PIG1987/PIG1987_LANDSCAPE_20250610_090000_042.mp4,LANDSCAPE,YouTube,Horizontal video
```

After migration:
```csv
Clip Filename,Reel Type,Platform,Description,Aspect Ratio
E:/VIDEOS/RELEASE CONTENT/PIG1987_RENEGADE_PIPELINE/PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_135.mp4,REEL,Instagram,Vertical video,9:16
E:/VIDEOS/RELEASE CONTENT/ZONE_A0/ZONE_A0_SQUARE_POST_20250615_120000_001.mp4,SQUARE,Instagram,Square post,1:1
E:/VIDEOS/RELEASE CONTENT/PIG1987/PIG1987_LANDSCAPE_20250610_090000_042.mp4,LANDSCAPE,YouTube,Horizontal video,16:9
```

## Output Reports

### Migration Report
```
============================================================
[MIGRATION REPORT]
============================================================

Column: Aspect Ratio
Total Rows: 686
Rows Added: 0
Rows Updated: 450
Rows Unchanged: 236
Rows Unknown: 0
Backfill Success Rate: 100.0%

Output Path: /path/to/bedrot-reel-tracker.csv
Backup Path: /path/to/backups/bedrot-reel-tracker_backup_20250819_143022.csv

[VALUE DISTRIBUTION]
  9:16: 402 (58.6%)
  16:9: 183 (26.7%)
  1:1: 67 (9.8%)
  4:5: 34 (5.0%)
```

### Video Scanning Report
```
============================================================
[VIDEO SCANNING REPORT]
============================================================

Total Files Processed: 686
Successfully Scanned: 642
Scan Failures: 44
Missing Files: 23
Heuristic Fallbacks: 21
Processing Time: 45.67 seconds
Video Scan Success Rate: 93.6%

[ERROR BREAKDOWN]
  File not found: 23 files
  FFprobe timeout: 12 files
  Invalid format: 9 files

[SUCCESSFUL SCANS - Sample]
  PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_135.mp4: 1080x1920
  ZONE_A0_SQUARE_POST_20250615_120000_001.mp4: 1080x1080
  PIG1987_LANDSCAPE_20250610_090000_042.mp4: 1920x1080
```

## Error Handling

The system gracefully handles various error conditions:

### Missing Files
- **Detection**: File path exists in CSV but file not found on disk
- **Behavior**: Falls back to heuristic detection
- **Reporting**: Counted in "Missing Files" statistic

### Inaccessible Files
- **Detection**: File exists but cannot be read (permissions, corruption)
- **Behavior**: Falls back to heuristic detection  
- **Reporting**: Logged as scan failure

### FFprobe Unavailable
- **Detection**: FFprobe not found in PATH
- **Behavior**: Uses heuristic-only mode
- **Reporting**: Warning displayed, all files use fallback

### Invalid File Formats
- **Detection**: File exists but FFprobe cannot process it
- **Behavior**: Falls back to heuristic detection
- **Reporting**: Logged as format error

## Validation

### Pre-Migration Validation
```bash
# Test core functionality
python simple_video_test.py

# Comprehensive validation (requires pandas)
python validate_video_migrator.py
```

### Post-Migration Validation
The system includes automatic idempotency testing:
- Runs migration a second time after completion
- Verifies no additional changes are made
- Reports if unexpected modifications occur

## Performance

### Benchmarks
- **Average scan time**: ~0.067 seconds per file
- **Success rate**: 93.6% (based on 686 file test)
- **Memory usage**: Minimal (results cached efficiently)

### Optimization Features
- **Result caching**: Prevents redundant scans
- **Batch processing**: Processes files efficiently
- **Timeout handling**: 30-second timeout per file
- **Windows console hiding**: No popup windows during scanning

## Troubleshooting

### Common Issues

1. **"FFprobe not found"**
   - Install FFmpeg: `sudo apt install ffmpeg`
   - Verify installation: `ffprobe -version`

2. **"No module named pandas"**
   - Install pandas: `pip install pandas`
   - Or use virtual environment: `source venv/bin/activate`

3. **"Permission denied" errors**
   - Check file permissions on video files
   - Ensure read access to video directory

4. **Windows path issues**
   - System automatically converts `E:\` to `/mnt/e/`
   - Ensure WSL can access Windows drives

### Debug Mode
```bash
# Enable verbose logging for troubleshooting
python apply_video_aspect_ratio_migration.py --verbose --dry-run
```

This shows detailed information about:
- File scanning attempts
- Path conversions
- FFprobe command execution
- Error details

## Safety Features

### Backup Protection
- **Automatic backups**: Created before any modifications
- **Timestamped names**: `filename_backup_20250819_143022.csv`
- **Separate directory**: Stored in `backups/` subdirectory

### Idempotent Operations
- **Safe re-runs**: Can be run multiple times safely
- **Change detection**: Only modifies empty or missing values
- **Validation**: Automatic verification of results

### Error Recovery
- **Transactional**: All changes succeed or none applied
- **Fallback modes**: Graceful degradation when video scanning fails
- **Detailed logging**: Complete error reporting for troubleshooting

## Integration

This enhanced migration system is fully compatible with the existing CSV column migration framework and can be used alongside other migration tools in the BEDROT Media Suite.

The `VideoAspectRatioMigrator` extends the base `AspectRatioMigrator` class, maintaining all existing functionality while adding video scanning capabilities.