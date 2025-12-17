#!/usr/bin/env python3
"""
Main entry point for the Bedrot Video Splitter module.
"""

import sys


def main():
    """Launch the Video Splitter GUI."""
    from .main_app import main as launch_app

    return launch_app()


if __name__ == "__main__":
    sys.exit(main())
