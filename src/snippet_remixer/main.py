#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Video Snippet Remixer application.
Classic tkinter interface only.
"""

import sys


def main():
    """Main entry point - classic interface."""
    print("[INFO] Starting Video Snippet Remixer...")
    from .main_app import main as classic_main
    return classic_main()


if __name__ == "__main__":
    sys.exit(main())