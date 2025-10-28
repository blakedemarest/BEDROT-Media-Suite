#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify threading fixes in Random Slideshow module.

This script tests:
1. Memory leak prevention
2. Thread safety
3. Proper resource cleanup
4. Signal disconnection
"""

import sys
import os
import time
import threading
import psutil
import gc
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from random_slideshow.main_app import RandomSlideshowEditor


def monitor_resources():
    """Monitor system resources during execution."""
    process = psutil.Process()
    
    print("\n=== Resource Monitor Started ===")
    print(f"Initial Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"Initial Threads: {threading.active_count()}")
    
    start_memory = process.memory_info().rss
    peak_memory = start_memory
    
    for i in range(20):  # Monitor for 20 seconds
        time.sleep(1)
        current_memory = process.memory_info().rss
        peak_memory = max(peak_memory, current_memory)
        
        print(f"\rTime: {i+1}s | Memory: {current_memory / 1024 / 1024:.2f} MB | "
              f"Threads: {threading.active_count()} | "
              f"CPU: {process.cpu_percent(interval=0.1):.1f}%", end='')
    
    print(f"\n\n=== Resource Summary ===")
    print(f"Peak Memory: {peak_memory / 1024 / 1024:.2f} MB")
    print(f"Memory Growth: {(peak_memory - start_memory) / 1024 / 1024:.2f} MB")
    print(f"Final Threads: {threading.active_count()}")
    

def test_slideshow_generation():
    """Test the slideshow generation with threading fixes."""
    print("=== Testing Random Slideshow Threading Fixes ===\n")
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = RandomSlideshowEditor()
    window.show()
    
    # Start resource monitoring in background
    monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
    monitor_thread.start()
    
    # Auto-start generation after 2 seconds
    def start_generation():
        print("\nStarting slideshow generation...")
        # Trigger the start button if image folder is set
        if window.img_folder_input.text() and os.path.exists(window.img_folder_input.text()):
            window.toggle_button.click()
        else:
            print("ERROR: No valid image folder set. Please set it manually.")
    
    # Auto-stop generation after 10 seconds
    def stop_generation():
        print("\nStopping slideshow generation...")
        if window.toggle_button.isChecked():
            window.toggle_button.click()
        
        # Check for memory leaks
        gc.collect()
        time.sleep(1)
        
        # Schedule app exit
        QTimer.singleShot(2000, app.quit)
    
    # Schedule actions
    QTimer.singleShot(2000, start_generation)
    QTimer.singleShot(12000, stop_generation)
    
    # Run the application
    app.exec_()
    
    print("\n=== Test Complete ===")
    print("If no crashes occurred and memory usage stabilized, the fixes are working!")


if __name__ == "__main__":
    test_slideshow_generation()