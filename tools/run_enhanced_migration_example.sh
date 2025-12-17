#!/bin/bash
# Enhanced Video Aspect Ratio Migration - Usage Examples
# =====================================================

echo "Enhanced Video Aspect Ratio Migration - Usage Examples"
echo "======================================================"

# Set the tools directory
TOOLS_DIR="/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-media-suite/tools"
cd "$TOOLS_DIR"

echo ""
echo "1. Testing system requirements..."
echo "--------------------------------"

# Check if FFprobe is available
if command -v ffprobe &> /dev/null; then
    echo "[SUCCESS] FFprobe is available"
    ffprobe -version | head -1
else
    echo "[ERROR] FFprobe not found. Install FFmpeg first:"
    echo "  sudo apt install ffmpeg"
    exit 1
fi

# Test core functionality
echo ""
echo "2. Testing core functionality..."
echo "-------------------------------"
python simple_video_test.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Core functionality test failed"
    exit 1
fi

echo ""
echo "3. Running dry-run on production CSV..."
echo "---------------------------------------"
echo "This will scan actual video files but make no changes."
echo ""

# Dry run with verbose output
python apply_video_aspect_ratio_migration.py --dry-run --verbose

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Dry run completed successfully!"
    echo ""
    echo "If you're satisfied with the results, run the migration for real:"
    echo "  python apply_video_aspect_ratio_migration.py"
    echo ""
    echo "Or with overwrite to replace existing values:"
    echo "  python apply_video_aspect_ratio_migration.py --overwrite"
else
    echo "[ERROR] Dry run failed. Check the error messages above."
    exit 1
fi

echo ""
echo "Usage Summary:"
echo "=============="
echo "Dry run (safe):       python apply_video_aspect_ratio_migration.py --dry-run"
echo "Production run:       python apply_video_aspect_ratio_migration.py"  
echo "With overwrite:       python apply_video_aspect_ratio_migration.py --overwrite"
echo "Verbose output:       python apply_video_aspect_ratio_migration.py --verbose"
echo "Custom CSV:           python video_aspect_ratio_migrator.py /path/to/file.csv"
echo ""
echo "For help:             python apply_video_aspect_ratio_migration.py --help"