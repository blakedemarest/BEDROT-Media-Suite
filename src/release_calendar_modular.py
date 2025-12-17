"""
Release Calendar - Modular Entry Point

This is the main entry point for the Release Calendar module when launched
from the Media Suite launcher. It imports and runs the application from
the modular package.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the release calendar."""
    try:
        # Import PyQt6 first to check availability
        from PyQt6.QtWidgets import QApplication
        
        # Import the main app
        from release_calendar.main_app import CalendarApp
        
        # Create application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("BEDROT Release Calendar")
        app.setOrganizationName("BEDROT Productions")
        
        # Set style
        app.setStyle('Fusion')
        
        # Create and show main window
        print("[Release Calendar] Starting application...")
        window = CalendarApp()
        window.show()
        
        # Run event loop
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"[Release Calendar] ERROR: Missing required dependencies: {e}")
        print("[Release Calendar] Please ensure PyQt6 is installed:")
        print("[Release Calendar]   pip install PyQt6==6.6.1")
        sys.exit(1)
        
    except Exception as e:
        print(f"[Release Calendar] ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()