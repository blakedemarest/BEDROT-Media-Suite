# -*- coding: utf-8 -*-
"""
Caption Generator - Modular Entry Point

This is the launcher entry point for the Caption Generator application.
It imports and runs the application from the modular package.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main entry point for the caption generator."""
    try:
        print("[Caption Generator] Starting application...")
        from caption_generator.main_app import main as app_main
        app_main()

    except ImportError as e:
        print(f"[Caption Generator] ERROR: Missing dependencies: {e}")
        print("[Caption Generator] Please ensure PyQt5 is installed: pip install PyQt5")
        sys.exit(1)
    except Exception as e:
        print(f"[Caption Generator] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
