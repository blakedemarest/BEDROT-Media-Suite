# -*- coding: utf-8 -*-
"""Speech-to-text adapters for lyric alignment workflows."""

from .elevenlabs_client import (
    ElevenLabsClient,
    ElevenLabsConfig,
    TranscriptionResult,
    build_client_from_config,
)

__all__ = [
    "ElevenLabsClient",
    "ElevenLabsConfig",
    "TranscriptionResult",
    "build_client_from_config",
]
