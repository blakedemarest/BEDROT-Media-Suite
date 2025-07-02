#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Video Snippet Remixer application.

Automatically chooses between modern and classic interface based on availability.
"""

import sys


def main():
    """Main entry point with automatic interface selection."""
    try:
        # Try to use the modern interface
        import customtkinter
        from .modern_main_app import ModernVideoRemixerApp
        print("[INFO] Starting Video Snippet Remixer with Modern UI...")
        app = ModernVideoRemixerApp()
        app.root.mainloop()
        return 0
    except ImportError:
        # Fall back to classic interface
        print("[WARNING] CustomTkinter not available, using classic interface...")
        print("[TIP] Install CustomTkinter for the modern UI: pip install customtkinter")
        from .main_app import main as classic_main
        return classic_main()
    except Exception as e:
        print(f"[ERROR] Error starting modern interface: {e}")
        print("[INFO] Falling back to classic interface...")
        from .main_app import main as classic_main
        return classic_main()


if __name__ == "__main__":
    sys.exit(main())