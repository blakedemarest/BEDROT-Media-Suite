# -*- coding: utf-8 -*-
"""
Lyric Video Uploader - Modular pipeline for lyric-synced video exports.

The package orchestrates:
- Project directory provisioning and path resolution
- Audio stem separation and caching
- Speech-to-text transcription with external providers
- Manual tempo/beat grid authoring and validation
- Timing alignment and subtitle generation
- Rendering pipelines (ASS → FFmpeg NVENC, optional MoviePy)
- Export packaging and Snippet Remixer bridge artifacts
- Tkinter GUI/CLI entry points with Windows-first ergonomics
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import sys
from pathlib import Path
from typing import Optional

SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import get_config_manager  # type: ignore[import]
from core.logger import get_logger  # type: ignore[import]
from core.path_utils import get_path_resolver  # type: ignore[import]


@dataclass(frozen=True)
class ProjectContext:
    """
    Lightweight descriptor for a lyric video project workspace.

    Attributes:
        root: Base directory selected by the operator.
        config_name: Optional override for config profile selection.
    """

    root: Path
    config_name: Optional[str] = None

    def ensure_structure(self) -> None:
        """Create expected child directories if they are absent."""
        for child in (
            "stems",
            "timing",
            "renders",
            "exports/snippet_bridge",
            "exports/ready_for_upload",
        ):
            target = self.root / child
            target.mkdir(parents=True, exist_ok=True)

    @property
    def stems_dir(self) -> Path:
        return self.root / "stems"

    @property
    def timing_dir(self) -> Path:
        return self.root / "timing"

    @property
    def renders_dir(self) -> Path:
        return self.root / "renders"

    @property
    def exports_dir(self) -> Path:
        return self.root / "exports"


def get_package_logger(name: str = "lyric_video") -> "logging.Logger":
    """Return a namespace-scoped logger for lyric video tooling."""
    return get_logger(name)


def get_gui_entry():
    """Lazy import for GUI entry point to avoid tkinter overhead at import time."""
    from .ui.app import main as gui_main  # noqa: WPS433 (delayed import)

    return gui_main


def get_cli_entry():
    """Lazy import of CLI entry point to defer Typer/Click imports."""
    from .cli.main import app as cli_app  # noqa: WPS433 (delayed import)

    return cli_app


__all__ = [
    "ProjectContext",
    "get_package_logger",
    "get_gui_entry",
    "get_cli_entry",
    "get_config_manager",
    "get_path_resolver",
]
