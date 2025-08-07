#!/usr/bin/env python3
"""
Test the fixed GUI media downloader
"""

import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))

print("Testing fixed GUI media downloader...")

# Clean up any test files first
import glob
for f in glob.glob("E:/VIDEOS/A04_MEDIADOWNLOADEROUTPUTS/TEMP_DOWNLOAD_*.mp3"):
    try:
        os.remove(f)
        print(f"Cleaned up: {os.path.basename(f)}")
    except:
        pass

import tkinter as tk
from media_download_app import MediaDownloaderApp

# Create a simple test
root = tk.Tk()
app = MediaDownloaderApp(root)

def run_test():
    print("\n=== RUNNING DOWNLOAD TEST ===")
    
    # URL to test (the 2-hour video you wanted)
    test_url = "https://www.youtube.com/watch?v=yAuwQyLfueE"
    
    # Clear queue
    app.queue_listbox.delete(0, tk.END)
    
    # Add URL
    app.url_entry.delete(0, tk.END)
    app.url_entry.insert(0, test_url)
    
    # Set to MP3
    app.download_format.set("mp3")
    
    print(f"URL: {test_url}")
    print("Format: MP3")
    print("Adding to queue...")
    
    # Add to queue
    app.add_to_queue_threaded()
    
    # Wait and start download
    root.after(3000, start_download)

def start_download():
    queue = list(app.queue_listbox.get(0, tk.END))
    print(f"Queue has {len(queue)} items")
    
    if queue:
        print("Starting download (this will take time for a 2-hour video)...")
        app.start_download_thread()
        
        # Monitor status
        monitor_start_time = time.time()
        root.after(2000, lambda: monitor_download(monitor_start_time))
    else:
        print("ERROR: Queue is empty!")
        root.after(2000, start_download)  # Try again

def monitor_download(start_time):
    status = app.status_var.get()
    elapsed = time.time() - start_time
    
    # Print status every 10 seconds
    if int(elapsed) % 10 == 0:
        print(f"[{elapsed:.0f}s] Status: {status}")
    
    # Check completion
    if "Complete" in status or ("Queue finished" in status and "processed" in status):
        print(f"\n=== DOWNLOAD COMPLETED ===")
        print(f"Final status: {status}")
        print(f"Total time: {elapsed:.1f} seconds")
        
        # Check for files
        files = glob.glob("E:/VIDEOS/A04_MEDIADOWNLOADEROUTPUTS/*.mp3")
        print(f"\nMP3 files in output directory: {len(files)}")
        for f in files[-5:]:
            size_mb = os.path.getsize(f) / (1024 * 1024)
            name = os.path.basename(f)
            display_name = name if len(name) <= 60 else name[:57] + "..."
            print(f"  - {display_name} ({size_mb:.1f} MB)")
        
        # Success!
        if any("Werner Herzog" in f for f in files):
            print("\n*** SUCCESS! The 2-hour video was downloaded as MP3! ***")
        
        root.after(3000, root.quit)
    elif "failed" in status.lower() or "error" in status.lower():
        print(f"\n=== DOWNLOAD FAILED ===")
        print(f"Error: {status}")
        root.after(3000, root.quit)
    else:
        # Continue monitoring
        root.after(1000, lambda: monitor_download(start_time))

# Add control buttons
control_frame = tk.Frame(root)
control_frame.pack(side=tk.BOTTOM, pady=10)

tk.Button(control_frame, text="RUN TEST", command=run_test, bg="green", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
tk.Button(control_frame, text="QUIT", command=root.quit, bg="red", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

print("\nGUI is ready. Click 'RUN TEST' to download the 2-hour video as MP3.")
print("Or use the GUI normally to add URLs and download.")

root.mainloop()