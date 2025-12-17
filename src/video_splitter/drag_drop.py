# -*- coding: utf-8 -*-
"""
Drag and drop helpers for the Video Splitter module.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    TkinterDnD = None  # type: ignore
    DND_FILES = None  # type: ignore
    DND_AVAILABLE = False


def create_root() -> tk.Tk:
    """
    Create a Tk root window with drag and drop support if available.
    """
    if DND_AVAILABLE and TkinterDnD:
        return TkinterDnD.Tk()  # type: ignore
    return tk.Tk()


def setup_drop_target(widget: tk.Widget, on_drop: Callable[[str], None]) -> bool:
    """
    Configure widget as a drag and drop target if supported.

    Returns:
        True if drag and drop was enabled, False otherwise.
    """
    if not (DND_AVAILABLE and hasattr(widget, "drop_target_register")):
        return False

    try:
        widget.drop_target_register(DND_FILES)  # type: ignore

        def _handle_drop(event):
            if event.data:
                on_drop(event.data)

        widget.dnd_bind("<<Drop>>", _handle_drop)
        return True
    except Exception:
        return False
