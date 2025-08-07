#!/usr/bin/env python3
"""
Simple test to see what's happening with the GUI
"""

import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))

# Redirect print to file to avoid unicode issues
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
    
    def write(self, message):
        self.log.write(message)
        self.log.flush()
        try:
            self.terminal.write(message)
        except:
            # Ignore unicode errors
            pass
    
    def flush(self):
        pass

sys.stdout = Logger('gui_test_log.txt')

print("Starting GUI test...")

import tkinter as tk
from media_download_app import MediaDownloaderApp

def test_sequence():
    """Run a test download sequence"""
    print("\n=== TEST SEQUENCE STARTED ===")
    
    # Check initial state
    print(f"Download path: {app.download_path.get()}")
    print(f"Queue items: {list(app.queue_listbox.get(0, tk.END))}")
    
    # Add test URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    app.url_entry.delete(0, tk.END)
    app.url_entry.insert(0, test_url)
    print(f"Set URL: {test_url}")
    
    # Set format to MP3
    app.download_format.set("mp3")
    print("Set format: MP3")
    
    # Add to queue
    print("Adding to queue...")
    app.add_to_queue_threaded()
    
    # Schedule download start
    root.after(3000, start_download)

def start_download():
    """Start download after queue is populated"""
    queue_items = list(app.queue_listbox.get(0, tk.END))
    print(f"\nQueue now has {len(queue_items)} items: {queue_items}")
    
    if queue_items:
        print("Starting download...")
        # Check if method exists
        if hasattr(app, 'start_download_thread'):
            app.start_download_thread()
            print("Download started!")
            
            # Monitor status
            root.after(1000, monitor_status)
        else:
            print("ERROR: start_download_thread method not found!")
    else:
        print("ERROR: Queue is still empty!")
        # Try again
        root.after(2000, start_download)

def monitor_status():
    """Monitor download status"""
    status = app.status_var.get()
    print(f"Status: {status}")
    
    # Check if download is complete or failed
    if "Complete" in status or "failed" in status.lower() or "error" in status.lower():
        print(f"\nFinal status: {status}")
        
        # Check for downloaded files
        import glob
        files = glob.glob("E:/VIDEOS/A04_MEDIADOWNLOADEROUTPUTS/*.mp3")
        print(f"MP3 files found: {len(files)}")
        for f in files[-5:]:  # Show last 5 files
            print(f"  - {os.path.basename(f)}")
        
        # Close after a delay
        root.after(2000, root.quit)
    else:
        # Continue monitoring
        root.after(1000, monitor_status)

# Create GUI
root = tk.Tk()
app = MediaDownloaderApp(root)

# Start test after GUI is ready
root.after(1000, test_sequence)

# Add quit button
quit_btn = tk.Button(root, text="QUIT TEST", command=root.quit, bg="red", fg="white")
quit_btn.pack(side=tk.BOTTOM, pady=10)

print("GUI created, starting mainloop...")
root.mainloop()

print("\nTest completed!")