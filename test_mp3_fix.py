#!/usr/bin/env python3
"""
Test the MP3 download fix
"""

import os
import sys
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("TESTING MP3 DOWNLOAD FIX")
print("=" * 60)

# Test URL - a short video
test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
output_dir = "E:/VIDEOS/A04_MEDIADOWNLOADEROUTPUTS"

# Use venv Python
venv_python = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    print(f"ERROR: venv Python not found at {venv_python}")
    sys.exit(1)

# Clean up any existing test files
import glob
for pattern in ["DIRECT_FIX_TEST_*.mp3", "DIRECT_FIX_TEST_*.m4a"]:
    for f in glob.glob(os.path.join(output_dir, pattern)):
        try:
            os.remove(f)
            print(f"Cleaned up: {os.path.basename(f)}")
        except:
            pass

print(f"\nDownloading: {test_url}")
print(f"Output directory: {output_dir}")
print(f"Format: MP3")

# Test direct yt-dlp command
output_template = os.path.join(output_dir, "DIRECT_FIX_TEST_%(title)s.%(ext)s")
cmd = [
    venv_python, "-m", "yt_dlp",
    test_url,
    "-x", "--audio-format", "mp3",
    "-o", output_template,
    "--no-playlist",
    "--progress"
]

print(f"\nRunning command...")
start_time = time.time()

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = process.communicate()

elapsed = time.time() - start_time
print(f"\nCommand completed in {elapsed:.1f} seconds")
print(f"Return code: {process.returncode}")

if process.returncode == 0:
    print("\n[SUCCESS] yt-dlp command succeeded!")
    
    # Check for MP3 file
    mp3_files = glob.glob(os.path.join(output_dir, "DIRECT_FIX_TEST_*.mp3"))
    if mp3_files:
        for f in mp3_files:
            size_mb = os.path.getsize(f) / (1024 * 1024)
            print(f"[OK] Found MP3: {os.path.basename(f)} ({size_mb:.1f} MB)")
    else:
        print("[FAIL] No MP3 files found!")
        
    # Check for leftover m4a files
    m4a_files = glob.glob(os.path.join(output_dir, "DIRECT_FIX_TEST_*.m4a"))
    if m4a_files:
        print("[FAIL] Warning: Found leftover m4a files:")
        for f in m4a_files:
            print(f"  - {os.path.basename(f)}")
    else:
        print("[OK] No leftover m4a files (good!)")
else:
    print(f"\n[FAIL] yt-dlp command failed!")
    print(f"Error output:\n{stderr}")

print("\n" + "=" * 60)
print("Now test the GUI to verify it works correctly.")
print("The fix should:")
print("1. Download the video as m4a")
print("2. Convert to MP3") 
print("3. Delete the m4a")
print("4. Correctly detect the MP3 as successful")
print("5. NOT show 'yt-dlp Error Log' for successful downloads")
print("=" * 60)