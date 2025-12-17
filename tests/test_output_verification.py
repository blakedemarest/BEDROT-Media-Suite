#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for output dimension verification functionality.
Tests the verify_output_dimensions method with sample videos.
"""

import os
import sys
import tempfile
import subprocess

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from snippet_remixer.video_processor import VideoProcessor


def create_test_video(width, height, duration=1, filename="test_video.mp4", add_black_bars=False):
    """Create a test video with specified dimensions."""
    if add_black_bars:
        # Create video with black bars by padding
        filter_complex = f"color=c=red:s={width-100}x{height-100}:d={duration}[v0];[v0]pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    else:
        # Create solid color video
        filter_complex = f"color=c=blue:s={width}x{height}:d={duration}"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"nullsrc=s={width}x{height}:d={duration}",
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        filename
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating test video: {e}")
        return False


def main():
    """Run verification tests."""
    print("Testing Output Dimension Verification")
    print("=" * 50)
    
    # Initialize video processor
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processor = VideoProcessor(script_dir, None)
    
    if not processor.ffmpeg_found or not processor.ffprobe_found:
        print("Error: FFmpeg/FFprobe not found in PATH")
        return
    
    # Create temporary directory for test videos
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Normal video without black bars
        print("\nTest 1: Normal video (1920x1080)")
        test_file1 = os.path.join(temp_dir, "test1.mp4")
        if create_test_video(1920, 1080, filename=test_file1):
            width, height, has_black_bars = processor.verify_output_dimensions(
                test_file1, 1920, 1080, check_black_bars=True
            )
            print(f"  Dimensions: {width}x{height}")
            print(f"  Has black bars: {has_black_bars}")
            print(f"  Result: {'PASS' if width == 1920 and height == 1080 and not has_black_bars else 'FAIL'}")
        
        # Test 2: Video with black bars
        print("\nTest 2: Video with black bars (1920x1080 with padding)")
        test_file2 = os.path.join(temp_dir, "test2.mp4")
        if create_test_video(1920, 1080, filename=test_file2, add_black_bars=True):
            width, height, has_black_bars = processor.verify_output_dimensions(
                test_file2, 1920, 1080, check_black_bars=True
            )
            print(f"  Dimensions: {width}x{height}")
            print(f"  Has black bars: {has_black_bars}")
            print(f"  Result: {'PASS' if width == 1920 and height == 1080 and has_black_bars else 'FAIL'}")
        
        # Test 3: Dimension mismatch
        print("\nTest 3: Dimension mismatch (expected 1280x720, actual 1920x1080)")
        test_file3 = os.path.join(temp_dir, "test3.mp4")
        if create_test_video(1920, 1080, filename=test_file3):
            width, height, has_black_bars = processor.verify_output_dimensions(
                test_file3, 1280, 720, check_black_bars=False
            )
            print(f"  Dimensions: {width}x{height}")
            print(f"  Has black bars: {has_black_bars}")
            print(f"  Result: {'PASS' if width == 1920 and height == 1080 else 'FAIL'}")
        
        # Test 4: No expected dimensions provided
        print("\nTest 4: No expected dimensions (just get actual)")
        test_file4 = os.path.join(temp_dir, "test4.mp4")
        if create_test_video(854, 480, filename=test_file4):
            width, height, has_black_bars = processor.verify_output_dimensions(
                test_file4, check_black_bars=False
            )
            print(f"  Dimensions: {width}x{height}")
            print(f"  Has black bars: {has_black_bars}")
            print(f"  Result: {'PASS' if width == 854 and height == 480 else 'FAIL'}")
    
    print("\n" + "=" * 50)
    print("Tests completed!")


if __name__ == "__main__":
    main()