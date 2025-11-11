# -*- coding: utf-8 -*-
"""
ElevenLabs transcription client.

Provides a fail-fast wrapper around the ElevenLabs speech-to-text REST API,
returning structured word and line timing data for downstream processing.
"""

from __future__ import annotations

import json
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import requests

from .. import ProjectContext, get_config_manager, get_package_logger
from ..schemas import LineSegment, WordToken, coerce_word_tokens

LOGGER = get_package_logger("lyric_video.stt")
DEFAULT_ENDPOINT = "https://api.elevenlabs.io"


@dataclass(slots=True)
class ElevenLabsConfig:
    """Configuration for interacting with the ElevenLabs STT API."""

    api_key_env: str = "ELEVENLABS_API_KEY"
    language: str = "en"
    model_id: str = "eleven_multilingual_v2"
    base_url: str = DEFAULT_ENDPOINT
    request_timeout: int = 60
    max_retries: int = 2


@dataclass(slots=True)
class TranscriptionResult:
    """Structured transcription output."""

    words: List[WordToken]
    lines: List[LineSegment]
    raw: Dict


class ElevenLabsClient:
    """HTTP client for ElevenLabs speech-to-text."""

    def __init__(self, config: ElevenLabsConfig | None = None, session: requests.Session | None = None):
        self.config = config or ElevenLabsConfig()
        self.session = session or requests.Session()

        self.base_url = self.config.base_url.rstrip("/")
        self.api_key = os.getenv(self.config.api_key_env)
        if not self.api_key:
            raise RuntimeError(
                f"ElevenLabs API key missing. Set {self.config.api_key_env} in your environment."
            )
        LOGGER.info("ElevenLabs client ready (language=%s, model=%s)", self.config.language, self.config.model_id)

    def preflight(self) -> None:
        """Validate that the API is reachable."""
        url = f"{self.base_url}/v1"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code >= 500:
                raise RuntimeError("ElevenLabs API reports service outage; retry later.")
        except requests.RequestException as exc:
            raise RuntimeError("Unable to reach ElevenLabs API. Check network connectivity.") from exc

    def transcribe(self, audio_path: Path, context: ProjectContext) -> TranscriptionResult:
        """
        Submit audio for transcription and return structured timings.

        Args:
            audio_path: Input audio file.
            context: Project context (unused for now but kept for parity with other services).
        """
        audio_path = audio_path.expanduser().resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.base_url}/v1/speech-to-text/convert"
        headers = {"xi-api-key": self.api_key}
        audio_bytes = audio_path.read_bytes()
        mime_type, _ = mimetypes.guess_type(audio_path.name)
        mime_type = mime_type or "audio/wav"

        payload = {
            "model_id": self.config.model_id,
            "language_code": self.config.language,
        }

        for attempt in range(self.config.max_retries + 1):
            files = {"file": (audio_path.name, audio_bytes, mime_type)}
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    data=payload,
                    files=files,
                    timeout=self.config.request_timeout,
                )
            except requests.RequestException as exc:
                if attempt == self.config.max_retries:
                    raise RuntimeError("ElevenLabs transcription request failed due to network error.") from exc
                sleep_for = 2 ** attempt
                LOGGER.warning("Network error contacting ElevenLabs (attempt %s). Retrying in %ss.", attempt + 1, sleep_for)
                time.sleep(sleep_for)
                continue

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError as exc:
                    raise RuntimeError("ElevenLabs returned malformed JSON.") from exc
                return self._parse_response(data)

            if response.status_code in {429, 503} and attempt < self.config.max_retries:
                retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                LOGGER.warning(
                    "ElevenLabs throttled the request (status %s). Retrying in %ss.",
                    response.status_code,
                    retry_after,
                )
                time.sleep(retry_after)
                continue

            raise RuntimeError(
                f"ElevenLabs transcription failed (status {response.status_code}): {response.text}"
            )

        raise RuntimeError("ElevenLabs transcription failed after all retries.")

    @staticmethod
    def _parse_response(payload: Dict) -> TranscriptionResult:
        """Convert ElevenLabs JSON into structured word and line segments."""
        words_raw = (
            payload.get("words")
            or payload.get("word_segments")
            or payload.get("word_timestamps")
            or []
        )
        words = coerce_word_tokens(words_raw)
        lines = ElevenLabsClient._build_line_segments(payload, words)
        return TranscriptionResult(words=words, lines=lines, raw=payload)

    @staticmethod
    def _build_line_segments(payload: Dict, words: Sequence[WordToken]) -> List[LineSegment]:
        """Create line segments either from payload data or heuristics."""
        lines: List[LineSegment] = []

        explicit_lines = payload.get("lines") or payload.get("segments") or payload.get("utterances")
        if explicit_lines:
            for item in explicit_lines:
                try:
                    text = str(item.get("text") or item.get("content") or "")
                    start = float(item.get("start", item.get("start_time")))
                    end = float(item.get("end", item.get("end_time")))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid line segment payload: {item}") from exc
                segment_words = [w for w in words if w.start >= start and w.end <= end]
                lines.append(LineSegment(words=segment_words, text=text.strip(), start=start, end=end))
            return lines

        # Fallback heuristic: group words by punctuation or time gaps.
        if not words:
            return lines

        current_words: List[WordToken] = []
        sentence_start = words[0].start
        for token in words:
            current_words.append(token)
            end_punctuation = token.text.strip().endswith((".", "!", "?", ";"))
            next_gap = None
            if token is not words[-1]:
                next_token = words[words.index(token) + 1]
                next_gap = next_token.start - token.end

            if end_punctuation or (next_gap is not None and next_gap > 1.5):
                text = " ".join(w.text for w in current_words).strip()
                lines.append(
                    LineSegment(
                        words=list(current_words),
                        text=text,
                        start=sentence_start,
                        end=current_words[-1].end,
                    )
                )
                current_words = []
                sentence_start = next_token.start if next_gap is not None else sentence_start

        if current_words:
            text = " ".join(w.text for w in current_words).strip()
            lines.append(
                LineSegment(
                    words=list(current_words),
                    text=text,
                    start=current_words[0].start,
                    end=current_words[-1].end,
                )
            )

        return lines


def prepare_words(payload: Iterable[Dict]) -> List[WordToken]:
    """Helper maintained for backwards compatibility with older stubs."""
    return coerce_word_tokens(payload)


def build_client_from_config() -> ElevenLabsClient:
    """Factory that loads configuration from the central config manager."""
    config = get_config_manager().load_config("lyric_video_config.json", "lyric_video")
    stt_cfg = config.get("stt", {})
    return ElevenLabsClient(
        ElevenLabsConfig(
            api_key_env=stt_cfg.get("api_key_env", "ELEVENLABS_API_KEY"),
            language=stt_cfg.get("language", "en"),
            model_id=stt_cfg.get("model_id", "eleven_multilingual_v2"),
            base_url=stt_cfg.get("base_url", DEFAULT_ENDPOINT),
            request_timeout=int(stt_cfg.get("request_timeout", 60) or 60),
            max_retries=int(stt_cfg.get("max_retries", 2) or 2),
        )
    )


__all__ = ["ElevenLabsClient", "ElevenLabsConfig", "TranscriptionResult", "prepare_words", "build_client_from_config"]
