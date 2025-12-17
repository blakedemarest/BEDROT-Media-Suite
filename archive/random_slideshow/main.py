#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Random Slideshow Generator application.
This script can be run directly to launch the PyQt5 GUI application.
"""

import sys
import os

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add current directory for local imports
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Python version: {sys.version}")
print(f"Current directory: {current_dir}")
print(f"Project root: {project_root}")

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    print("PyQt5 imported successfully")
except ImportError as e:
    print(f"ERROR: Could not import PyQt5: {e}")
    print("Please install PyQt5: pip install PyQt5")
    sys.exit(1)

try:
    # Use the simple version without batch processing
    from main_app_simple import RandomSlideshowEditor
    print("RandomSlideshowEditor imported successfully")
except ImportError as e:
    print(f"ERROR: Could not import RandomSlideshowEditor: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to show error dialog
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Import Error", 
                        f"Failed to import Random Slideshow modules:\n\n{e}\n\n"
                        "Please check that all dependencies are installed.")
    sys.exit(1)


def main():
    """Main entry point for the application."""
    print("Starting Random Slideshow Generator...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Random Slideshow Generator")
    app.setOrganizationName("Bedrot Productions")
    
    try:
        window = RandomSlideshowEditor()
        window.show()
        print("Window created and shown")
        return app.exec_()
    except Exception as e:
        print(f"ERROR: Failed to create window: {e}")
        import traceback
        traceback.print_exc()
        
        QMessageBox.critical(None, "Startup Error",
                           f"Failed to start Random Slideshow Generator:\n\n{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())