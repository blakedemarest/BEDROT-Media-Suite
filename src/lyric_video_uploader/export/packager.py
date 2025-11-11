# -*- coding: utf-8 -*-
"""
Export packaging placeholder.

Bundles rendered assets, subtitles, and metadata into a ready-for-upload folder.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Mapping
import json
import shutil

from .. import ProjectContext, get_config_manager, get_package_logger

LOGGER = get_package_logger("lyric_video.export")


def package_exports(
    context: ProjectContext,
    metadata: Dict[str, str],
    *,
    render_path: Path,
    caption_paths: Mapping[str, Path],
    extra_files: Iterable[Path] | None = None,
) -> Path:
    """
    Assemble export bundle.

    Args:
        context: Project context for locating output directories.
        metadata: Dictionary containing upload metadata fields.
        render_path: Final rendered video to ship.
        caption_paths: Mapping of caption identifier -> file path.
        extra_files: Additional files to copy (optional).
    """
    context.ensure_structure()

    config = get_config_manager().load_config("lyric_video_config.json", "lyric_video")
    exports_cfg = config.get("exports", {})
    ready_dirname = exports_cfg.get("ready_for_upload_dirname", "ready_for_upload")
    ready_dir = context.exports_dir / ready_dirname
    ready_dir.mkdir(parents=True, exist_ok=True)

    if not render_path.exists():
        raise FileNotFoundError(f"Render file not found: {render_path}")

    # Copy render
    render_destination = ready_dir / render_path.name
    shutil.copy2(render_path, render_destination)
    LOGGER.info("Copied render to %s", render_destination)

    # Copy captions
    for key, path in caption_paths.items():
        if not path or not Path(path).exists():
            raise FileNotFoundError(f"Caption file for '{key}' not found: {path}")
        dest = ready_dir / path.name
        shutil.copy2(path, dest)
        LOGGER.info("Copied caption (%s) to %s", key, dest)

    # Copy extras
    for extra in extra_files or []:
        extra = Path(extra)
        if not extra.exists():
            raise FileNotFoundError(f"Supplemental file not found: {extra}")
        dest = ready_dir / extra.name
        shutil.copy2(extra, dest)

    metadata_path = ready_dir / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    LOGGER.info("Metadata written to %s", metadata_path)
    return ready_dir


__all__ = ["package_exports"]
