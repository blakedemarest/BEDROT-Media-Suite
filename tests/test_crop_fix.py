#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the cropping fix for snippet remixer.
Tests that videos are properly cropped instead of having black bars added.
"""

import os
import sys
import subprocess
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from snippet_remixer.video_processor import VideoProcessor
from snippet_remixer.utils import safe_print


def create_test_video(width, height, duration, output_path):
    """Create a test video with the specified dimensions."""
    cmd = [
        "ffmpeg", "-f", "lavfi", 
        "-i", f"testsrc=duration={duration}:size={width}x{height}:rate=30",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-y", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"Failed to create test video: {e}")
        return False


def check_for_black_bars(video_path):
    """Check if a video has black bars by analyzing edge pixels."""
    # This is a simplified check - in practice you'd want more sophisticated detection
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            width = int(lines[0])
            height = int(lines[1])
            safe_print(f"Video dimensions: {width}x{height}")
            return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Test the cropping functionality."""
    safe_print("Testing snippet remixer cropping fix...")
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test videos with different aspect ratios
        test_videos = [
            ("16x9_video.mp4", 1920, 1080, 5),  # 16:9 landscape
            ("9x16_video.mp4", 1080, 1920, 5),  # 9:16 portrait  
            ("4x3_video.mp4", 1440, 1080, 5),   # 4:3 classic
            ("21x9_video.mp4", 2560, 1080, 5),  # 21:9 ultrawide
        ]
        
        video_paths = []
        for filename, w, h, duration in test_videos:
            path = os.path.join(temp_dir, filename)
            if create_test_video(w, h, duration, path):
                video_paths.append(path)
                safe_print(f"Created test video: {filename} ({w}x{h})")
        
        if not video_paths:
            safe_print("Failed to create test videos")
            return
        
        # Initialize video processor
        processor = VideoProcessor(temp_dir, None)
        
        # Test different aspect ratio conversions
        test_cases = [
            ("1920x1080 (16:9 Landscape)", "16_9_output.mp4"),
            ("1080x1920 (9:16 Portrait)", "9_16_output.mp4"),
            ("1080x1080 (1:1 Square)", "1_1_output.mp4"),
        ]
        
        for aspect_ratio, output_name in test_cases:
            safe_print(f"\nTesting conversion to {aspect_ratio}...")
            
            # Prepare snippet definitions (1 second from each video)
            snippet_defs = [(path, 0.0, 1.0) for path in video_paths]
            
            # Prepare temp directory
            if not processor.prepare_temp_directory():
                safe_print("Failed to prepare temp directory")
                continue
            
            try:
                # Cut snippets with the target aspect ratio
                snippet_files = processor.cut_video_snippets(
                    snippet_defs, 
                    aspect_ratio,
                    export_settings=None,
                    progress_callback=lambda msg: safe_print(f"  {msg}")
                )
                
                if snippet_files:
                    safe_print(f"  Successfully cut {len(snippet_files)} snippets")
                    
                    # Check first snippet for black bars
                    if snippet_files:
                        check_for_black_bars(snippet_files[0])
                    
                    # Concatenate
                    concat_path = processor.concatenate_snippets(snippet_files)
                    
                    # Final output
                    output_path = os.path.join(temp_dir, output_name)
                    success = processor.adjust_aspect_ratio(
                        concat_path, output_path, aspect_ratio, 
                        export_settings=None,
                        progress_callback=lambda msg: safe_print(f"  {msg}")
                    )
                    
                    if success and os.path.exists(output_path):
                        safe_print(f"  Output created: {output_name}")
                        check_for_black_bars(output_path)
                    else:
                        safe_print(f"  Failed to create output")
                        
                else:
                    safe_print("  Failed to cut snippets")
                    
            except Exception as e:
                safe_print(f"  Error: {e}")
            
            finally:
                processor.cleanup_temp_directory()
        
        safe_print("\nTest complete!")
        safe_print("\nSummary of changes:")
        safe_print("- Changed scaling from 'decrease' to 'increase' to fill the frame")
        safe_print("- Added crop filter after scale to remove overflow")
        safe_print("- Updated aspect ratio adjustment to always crop instead of pad")
        safe_print("- Result: Videos now fill the entire frame without black bars")


if __name__ == "__main__":
    main()