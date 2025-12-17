#!/usr/bin/env python3
"""
Direct test and fix for the GUI media downloader
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))

from media_download_app import MediaDownloaderApp

class TestWrapper:
    def __init__(self):
        self.root = tk.Tk()
        self.app = MediaDownloaderApp(self.root)
        
        # Override the process_queue_sequential to add debugging
        self.original_process = self.app.process_queue_sequential
        self.app.process_queue_sequential = self.wrapped_process_queue
        
        # Add test button
        test_frame = ttk.Frame(self.root)
        test_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        ttk.Label(test_frame, text="TEST MODE", foreground="red", font=("Arial", 12, "bold")).pack()
        
        test_btn = ttk.Button(test_frame, text="Quick Test Download", command=self.quick_test)
        test_btn.pack(pady=5)
        
        self.log_text = tk.Text(test_frame, height=10, width=80)
        self.log_text.pack(pady=5)
        
    def log(self, msg):
        """Add message to log window"""
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def wrapped_process_queue(self, *args, **kwargs):
        """Wrapper to add logging to the download process"""
        self.log("Starting download process...")
        try:
            # Log the arguments
            self.log(f"Queue: {args[0]}")
            self.log(f"Format: {args[4] if len(args) > 4 else 'unknown'}")
            
            # Call original method
            result = self.original_process(*args, **kwargs)
            self.log("Download process completed")
            return result
        except Exception as e:
            self.log(f"ERROR in download process: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            raise
            
    def quick_test(self):
        """Quick test with a short video"""
        self.log("Starting quick test...")
        
        # Clear queue
        self.app.queue_listbox.delete(0, tk.END)
        
        # Add a short test video
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.app.url_entry.delete(0, tk.END)
        self.app.url_entry.insert(0, test_url)
        
        # Set MP3 format
        self.app.download_format.set("mp3")
        
        self.log(f"Adding URL: {test_url}")
        self.log(f"Format: MP3")
        
        # Add to queue
        self.app.add_to_queue_threaded()
        
        # Wait a bit for queue to update
        self.root.after(2000, self.start_download)
        
    def start_download(self):
        """Start the download after queue is ready"""
        queue_items = list(self.app.queue_listbox.get(0, tk.END))
        self.log(f"Queue has {len(queue_items)} items")
        
        if queue_items:
            self.log("Starting download...")
            self.app.start_download_thread()
        else:
            self.log("ERROR: Queue is empty!")
            
    def run(self):
        self.root.mainloop()

def direct_test_download():
    """Test download functionality directly without GUI"""
    print("\nDirect download test (bypassing GUI)...")
    
    import subprocess
    
    venv_python = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    output_path = "E:/VIDEOS/A04_MEDIADOWNLOADEROUTPUTS"
    
    # Test if basic download works
    output_file = os.path.join(output_path, "DIRECT_TEST_%(title)s.%(ext)s")
    
    cmd = [
        venv_python, "-m", "yt_dlp",
        test_url,
        "-x", "--audio-format", "mp3",
        "-o", output_file,
        "--no-playlist"
    ]
    
    print(f"Running: {' '.join(cmd[:5])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Direct download works!")
        # Clean up
        import glob
        for f in glob.glob(os.path.join(output_path, "DIRECT_TEST_*.mp3")):
            os.remove(f)
            print(f"Cleaned up: {os.path.basename(f)}")
    else:
        print("✗ Direct download failed!")
        print(f"Error: {result.stderr}")
        
    return result.returncode == 0

if __name__ == "__main__":
    print("=" * 60)
    print("MEDIA DOWNLOADER GUI TEST & FIX")
    print("=" * 60)
    
    # First test direct download
    if direct_test_download():
        print("\nDirect download works. Testing GUI...")
        
        # Run GUI test
        wrapper = TestWrapper()
        wrapper.run()
    else:
        print("\nDirect download failed. Check your environment!")