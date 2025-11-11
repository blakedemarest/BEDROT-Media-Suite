# -*- coding: utf-8 -*-
"""
Modular launcher wrapper for the Lyric Video Uploader GUI.

Aligns with the Bedrot launcher expectation by exposing a thin entry point that
hands control to the package-level GUI bootstrap.
"""

from __future__ import annotations

from lyric_video_uploader import get_gui_entry


def main() -> None:
    """Launch the lyric video uploader GUI."""
    gui_main = get_gui_entry()
    gui_main()


if __name__ == "__main__":
    main()

