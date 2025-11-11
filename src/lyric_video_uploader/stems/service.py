# -*- coding: utf-8 -*-
"""
High-level stem separation service orchestrating Demucs and caching logic.

Currently provides dependency validation and structured error messaging, with
implementation stubs for future iterations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from .. import ProjectContext, get_config_manager, get_package_logger
from ..ingest.validators import validate_audio_file
from .demucs_engine import DemucsEngine

LOGGER = get_package_logger("lyric_video.stems.service")


def separate(audio_path: Path, context: ProjectContext, *, force: bool = False) -> Dict[str, Path]:
    """
    Separate the provided audio file into stems using Demucs.

    Args:
        audio_path: Input audio path selected by the operator.
        context: Project context for locating cache/output directories.
        force: When True, bypasses future cache reuse logic.

    Returns:
        Mapping of stem name -> file path.
    """
    context.ensure_structure()
    audio_path = validate_audio_file(audio_path)

    config = get_config_manager().load_config("lyric_video_config.json", "lyric_video")
    stems_cfg = config.get("stems", {})
    LOGGER.info("Preparing Demucs separation for %s", audio_path.name)

    engine = DemucsEngine(
        model_name=stems_cfg.get("model", "htdemucs_ft"),
        require_gpu=stems_cfg.get("gpu_required", True),
        cache_enabled=stems_cfg.get("cache_enabled", True),
        overwrite_existing=stems_cfg.get("overwrite_existing", False),
        segment_seconds=int(stems_cfg.get("chunk_size_seconds", 60) or 0),
    )
    return engine.separate(audio_path, context.stems_dir, force=force)


__all__ = ["separate"]
