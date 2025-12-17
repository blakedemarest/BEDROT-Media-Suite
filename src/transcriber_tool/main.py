#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main entry point for the Transcriber Tool module."""

import sys


def main():
    """Launch the Transcriber Tool GUI."""
    from .main_app import main as launch_app
    return launch_app()


if __name__ == "__main__":
    sys.exit(main())
