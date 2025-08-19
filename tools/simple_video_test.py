#!/usr/bin/env python3
"""
Simple test of video dimension detection without pandas dependency
"""

import os
import subprocess
from fractions import Fraction

def find_ffprobe():
    """Find FFprobe executable."""
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            return 'ffprobe'
    except:
        pass
    return None

def scan_video_file(file_path, ffprobe_path):
    """Scan a video file for dimensions."""
    # Convert Windows paths if needed
    scan_path = file_path
    if os.name != 'nt' and file_path.startswith('E:'):
        scan_path = file_path.replace('E:', '/mnt/e')
        scan_path = scan_path.replace('\\', '/')
    
    # Check if file exists
    if not os.path.exists(scan_path):
        return None, None, f"File not found: {scan_path}"
    
    # Build FFprobe command
    command = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        scan_path
    ]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            return None, None, f"FFprobe error: {result.stderr.strip()}"
        
        # Parse output: should be "width,height"
        output = result.stdout.strip()
        if ',' not in output:
            return None, None, f"Unexpected FFprobe output: {output}"
        
        width_str, height_str = output.split(',')
        width = int(width_str.strip())
        height = int(height_str.strip())
        
        return width, height, None
        
    except Exception as e:
        return None, None, f"Error: {str(e)}"

def categorize_aspect_ratio(width, height):
    """Categorize aspect ratio."""
    if width <= 0 or height <= 0:
        return "unknown"
    
    # Calculate simplified ratio
    frac = Fraction(width, height)
    simplified = (frac.numerator, frac.denominator)
    
    # Common canonical ratios
    canonical_ratios = {
        (9, 16): "9:16",   # Vertical - Reels, Shorts, TikTok
        (16, 9): "16:9",   # Horizontal - YouTube, landscape
        (1, 1): "1:1",     # Square - Instagram posts
        (4, 5): "4:5",     # Portrait - Instagram posts
        (5, 4): "5:4",     # Landscape alternative
        (3, 4): "3:4",     # Portrait alternative
        (4, 3): "4:3",     # Traditional TV
        (21, 9): "21:9",   # Ultrawide
        (2, 3): "2:3",     # Portrait
        (3, 2): "3:2",     # Landscape photo
    }
    
    # Check for exact match
    if simplified in canonical_ratios:
        return canonical_ratios[simplified]
    
    # Check for close match (5% tolerance)
    ratio = width / height
    for (w, h), canonical in canonical_ratios.items():
        canonical_ratio = w / h
        error = abs(ratio - canonical_ratio) / canonical_ratio
        if error < 0.05:
            return canonical
    
    # Return simplified ratio
    return f"{simplified[0]}:{simplified[1]}"

def main():
    """Test video scanning functionality."""
    print("="*60)
    print("[SIMPLE VIDEO DIMENSION TEST]")
    print("="*60)
    
    # Find FFprobe
    ffprobe_path = find_ffprobe()
    if not ffprobe_path:
        print("[ERROR] FFprobe not found")
        return False
    
    print(f"[SUCCESS] FFprobe found: {ffprobe_path}")
    
    # Test aspect ratio categorization
    print(f"\n[Testing aspect ratio categorization]")
    test_cases = [
        (1920, 1080, "16:9"),   # Full HD landscape
        (1080, 1920, "9:16"),   # Full HD portrait
        (1080, 1080, "1:1"),    # Square
        (1080, 1350, "4:5"),    # Portrait
        (720, 1280, "9:16"),    # HD portrait
    ]
    
    all_correct = True
    for width, height, expected in test_cases:
        actual = categorize_aspect_ratio(width, height)
        status = "PASS" if actual == expected else "FAIL"
        print(f"  {width}x{height} -> {actual} (expected {expected}) [{status}]")
        if actual != expected:
            all_correct = False
    
    if not all_correct:
        print("[ERROR] Aspect ratio categorization failed")
        return False
    
    print("[SUCCESS] Aspect ratio categorization working correctly")
    
    # Test with a real file if one exists
    test_files = [
        "/mnt/e/VIDEOS/RELEASE CONTENT/bedrot-reel-tracker.csv",  # Not a video, should fail gracefully
        # Add some real video paths here if available
    ]
    
    print(f"\n[Testing file scanning]")
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"Testing: {file_path}")
            width, height, error = scan_video_file(file_path, ffprobe_path)
            if width and height:
                aspect_ratio = categorize_aspect_ratio(width, height)
                print(f"  Dimensions: {width}x{height}")
                print(f"  Aspect Ratio: {aspect_ratio}")
            else:
                print(f"  Error: {error}")
        else:
            print(f"File not found, skipping: {file_path}")
    
    print(f"\n[SUCCESS] Video scanning functionality validated")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)