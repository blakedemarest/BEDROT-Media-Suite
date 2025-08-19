#!/usr/bin/env python3
"""
Test MoviePy speed for aspect ratio detection.
MoviePy only reads metadata (very fast) vs FFprobe which spawns external process.
"""

import time
import os
import sys

def test_moviepy():
    """Test if MoviePy is available and working."""
    try:
        from moviepy.editor import VideoFileClip
        print("[SUCCESS] MoviePy is installed and imported successfully")
        return True
    except ImportError as e:
        print(f"[ERROR] MoviePy not installed: {e}")
        print("\nTo install MoviePy, run:")
        print("pip install moviepy")
        return False

def get_aspect_ratio_moviepy(filepath):
    """Get aspect ratio using MoviePy (fast - metadata only)."""
    try:
        from moviepy.editor import VideoFileClip
        
        start = time.time()
        clip = VideoFileClip(filepath)
        width = clip.w
        height = clip.h
        duration = clip.duration
        fps = clip.fps
        clip.close()  # Important!
        elapsed = time.time() - start
        
        # Calculate aspect ratio
        ratio = width / height
        
        # Map to canonical
        canonical = "unknown"
        ratios = [
            (9/16, "9:16"),
            (16/9, "16:9"),
            (1.0, "1:1"),
            (4/5, "4:5"),
        ]
        
        for target, label in ratios:
            if abs(ratio - target) / target < 0.05:
                canonical = label
                break
        
        print(f"\n[MoviePy Results]")
        print(f"  File: {os.path.basename(filepath)}")
        print(f"  Dimensions: {width}x{height}")
        print(f"  Aspect Ratio: {canonical}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  FPS: {fps}")
        print(f"  Time taken: {elapsed:.3f} seconds")
        
        return canonical, elapsed
        
    except Exception as e:
        print(f"[ERROR] MoviePy failed: {e}")
        return None, 0

def test_sample_video():
    """Test with a sample video file."""
    # Try to find a sample video
    test_paths = [
        r"E:\VIDEOS\RELEASE CONTENT\PIG1987_RENEGADE_PIPELINE\PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_135.mp4",
        r"E:\VIDEOS\RELEASE CONTENT\PIG1987_RENEGADE_PIPELINE\PIG1987_RENEGADE_PIPELINE_REEL_20250623_063634_136.mp4",
    ]
    
    for path in test_paths:
        if os.path.exists(path):
            print(f"\nTesting with: {path}")
            result, time_taken = get_aspect_ratio_moviepy(path)
            if result:
                print(f"\n[SPEED TEST] MoviePy detected aspect ratio in {time_taken:.3f} seconds")
                print("[INFO] This is much faster than FFprobe which takes 1-2 seconds per file")
            return
    
    print("[WARNING] No test video files found")
    print("Please provide a video file path as argument:")
    print(f"  python {sys.argv[0]} <video_file_path>")

def main():
    """Main test function."""
    print("="*60)
    print("MoviePy Speed Test for Aspect Ratio Detection")
    print("="*60)
    
    if not test_moviepy():
        return
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        if os.path.exists(video_path):
            print(f"\nTesting with provided file: {video_path}")
            get_aspect_ratio_moviepy(video_path)
        else:
            print(f"[ERROR] File not found: {video_path}")
    else:
        test_sample_video()
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    main()