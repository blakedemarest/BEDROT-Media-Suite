# -*- coding: utf-8 -*-
"""
Video Snippet Remixer - Modular Entry Point

This is the main entry point for the modular Video Snippet Remixer application.
It imports and runs the application from the launcher package.

This modular version provides the same functionality as the original snippet_remixer.py
but with clean separation of concerns:
- Configuration management
- Video processing core
- UI components
- Background worker threads
- Utility functions
"""

if __name__ == "__main__":
    from snippet_remixer.main import main
    main()