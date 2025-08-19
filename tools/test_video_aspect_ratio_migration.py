#!/usr/bin/env python3
"""
Test Video Aspect Ratio Migration
=================================

This script tests the enhanced video-based aspect ratio migration with various
test cases to ensure robust functionality.

Usage:
    python test_video_aspect_ratio_migration.py
"""

import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
import logging

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_aspect_ratio_migrator import VideoAspectRatioMigrator


def create_test_csv(temp_dir: str) -> str:
    """Create a test CSV with various file path scenarios."""
    test_data = {
        'Clip Filename': [
            'E:/VIDEOS/RELEASE CONTENT/PIG1987_RENEGADE_PIPELINE/PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_135.mp4',
            'E:/VIDEOS/RELEASE CONTENT/ZONE_A0/ZONE_A0_SQUARE_POST_20250615_120000_001.mp4',
            'E:/VIDEOS/RELEASE CONTENT/PIG1987/PIG1987_LANDSCAPE_20250610_090000_042.mp4',
            '/nonexistent/path/video.mp4',  # Non-existent file
            '',  # Empty path
            'invalid_path_no_extension',  # Invalid path
        ],
        'Reel Type': [
            'REEL',
            'SQUARE',
            'LANDSCAPE', 
            'REEL',
            'UNKNOWN',
            'POST',
        ],
        'Platform': [
            'Instagram',
            'Instagram',
            'YouTube',
            'TikTok',
            '',
            'Facebook',
        ],
        'Description': [
            'Vertical video for reels',
            'Square post for Instagram',
            'Horizontal landscape video',
            'Another reel video',
            'No description',
            'Regular post content',
        ]
    }
    
    df = pd.DataFrame(test_data)
    csv_path = os.path.join(temp_dir, 'test_reel_tracker.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path


def test_video_dimension_scanning():
    """Test video dimension scanning functionality."""
    print("="*60)
    print("[TEST: Video Dimension Scanning]")
    print("="*60)
    
    migrator = VideoAspectRatioMigrator()
    
    print(f"FFprobe available: {migrator.ffprobe_available}")
    if migrator.ffprobe_available:
        print(f"FFprobe path: {migrator.ffprobe_path}")
    else:
        print("FFprobe not found - will test heuristic fallback")
    
    # Test various file path scenarios
    test_paths = [
        'E:/VIDEOS/RELEASE CONTENT/PIG1987_RENEGADE_PIPELINE/PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_135.mp4',
        '/nonexistent/path/video.mp4',
        '',
        'invalid_path',
    ]
    
    print(f"\n[Testing file scanning...]")
    for path in test_paths:
        width, height, error = migrator.scan_video_file(path)
        print(f"Path: {path}")
        print(f"  Result: {width}x{height} (Error: {error})")
        
        if width and height:
            aspect_ratio = migrator.categorize_aspect_ratio(width, height)
            print(f"  Aspect Ratio: {aspect_ratio}")
        print()


def test_aspect_ratio_categorization():
    """Test aspect ratio categorization with various dimensions."""
    print("="*60)
    print("[TEST: Aspect Ratio Categorization]")
    print("="*60)
    
    migrator = VideoAspectRatioMigrator()
    
    # Test common video dimensions
    test_dimensions = [
        (1920, 1080),  # 16:9 Full HD
        (1080, 1920),  # 9:16 Vertical Full HD
        (1080, 1080),  # 1:1 Square
        (1080, 1350),  # 4:5 Portrait
        (1350, 1080),  # 5:4 Landscape
        (2560, 1440),  # 16:9 2K
        (3840, 2160),  # 16:9 4K
        (720, 1280),   # 9:16 HD
        (1024, 1024),  # 1:1 Square alternative
        (1440, 1080),  # 4:3 Traditional
        (1200, 900),   # 4:3 Alternative
        (2560, 1080),  # 21:9 Ultrawide
        (0, 0),        # Invalid dimensions
        (1920, 0),     # Invalid height
    ]
    
    print(f"Testing aspect ratio categorization:")
    for width, height in test_dimensions:
        aspect_ratio = migrator.categorize_aspect_ratio(width, height)
        print(f"{width}x{height} -> {aspect_ratio}")


def test_enhanced_backfill():
    """Test the enhanced backfill function."""
    print("="*60)
    print("[TEST: Enhanced Backfill Function]")
    print("="*60)
    
    migrator = VideoAspectRatioMigrator()
    
    # Create test rows
    test_rows = [
        pd.Series({
            'FilePath': 'E:/VIDEOS/test_video_1920x1080.mp4',
            'Reel Type': 'LANDSCAPE',
            'Platform': 'YouTube'
        }),
        pd.Series({
            'Clip Filename': '/nonexistent/vertical_video.mp4',
            'Reel Type': 'REEL',
            'Platform': 'Instagram'
        }),
        pd.Series({
            'width': 1080,
            'height': 1080,
            'Reel Type': 'SQUARE'
        }),
        pd.Series({
            'resolution': '1920x1080',
            'Platform': 'YouTube'
        }),
        pd.Series({
            'Reel Type': 'REEL',
            'Platform': 'TikTok'
        }),
        pd.Series({
            'Description': 'Random content with no hints'
        })
    ]
    
    print(f"Testing enhanced backfill function:")
    for i, row in enumerate(test_rows):
        aspect_ratio = migrator.enhanced_backfill_aspect_ratio(row, migrator_instance=migrator)
        print(f"Row {i+1}: {aspect_ratio}")
        print(f"  Input: {dict(row)}")
        print()


def test_full_migration():
    """Test full migration process with test CSV."""
    print("="*60)
    print("[TEST: Full Migration Process]")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test CSV
        csv_path = create_test_csv(temp_dir)
        print(f"Created test CSV: {csv_path}")
        
        # Load and display original data
        df_original = pd.read_csv(csv_path)
        print(f"\nOriginal data ({len(df_original)} rows):")
        print(df_original.to_string(index=False))
        
        # Perform migration
        migrator = VideoAspectRatioMigrator()
        migration_result, scan_result = migrator.migrate_with_video_scanning(
            csv_path,
            create_backup=False
        )
        
        # Load and display results
        df_result = pd.read_csv(csv_path)
        print(f"\nAfter migration:")
        print(df_result.to_string(index=False))
        
        # Print statistics
        print(f"\n[Migration Results]")
        print(f"Total rows: {migration_result.total_rows}")
        print(f"Rows updated: {migration_result.rows_updated}")
        print(f"Rows unchanged: {migration_result.rows_unchanged}")
        print(f"Rows unknown: {migration_result.rows_unknown}")
        
        print(f"\n[Video Scan Results]")
        print(f"Total files: {scan_result.total_files}")
        print(f"Successful scans: {scan_result.scanned_successfully}")
        print(f"Failed scans: {scan_result.scan_failures}")
        print(f"Processing time: {scan_result.processing_time:.2f}s")
        
        if scan_result.error_summary:
            print(f"\nError summary: {scan_result.error_summary}")


def main():
    """Run all tests."""
    print("="*80)
    print("[VIDEO ASPECT RATIO MIGRATION - COMPREHENSIVE TESTS]")
    print("="*80)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    
    try:
        # Run individual tests
        test_video_dimension_scanning()
        test_aspect_ratio_categorization()
        test_enhanced_backfill()
        test_full_migration()
        
        print("="*80)
        print("[ALL TESTS COMPLETED SUCCESSFULLY]")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()