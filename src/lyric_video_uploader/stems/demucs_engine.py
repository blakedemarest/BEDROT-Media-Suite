# -*- coding: utf-8 -*-
"""
Demucs-based stem separation placeholder.

Provides dependency validation and a structured surface for the full stem
pipeline. The actual separation routine will be implemented in a follow-up
iteration once GPU-accelerated Demucs integration is finalized.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from .. import ProjectContext, get_config_manager, get_package_logger

LOGGER = get_package_logger("lyric_video.stems")
CACHE_MANIFEST = "manifest.json"


def _import_torch(skip_gpu_check: bool) -> object:
    """Attempt to import torch and optionally verify CUDA availability."""
    try:
        torch_module = importlib.import_module("torch")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyTorch is required for Demucs stem separation but is not installed. "
            "Follow the instructions in docs/lyric_video_uploader/ to install a "
            "CUDA-enabled torch build."
        ) from exc

    allow_cpu = os.getenv("LYRIC_VIDEO_ALLOW_CPU", "").lower() in {"1", "true", "yes"}
    if not skip_gpu_check and not allow_cpu and not torch_module.cuda.is_available():
        raise RuntimeError(
            "CUDA GPU not detected. Lyric Video Uploader requires an RTX-class GPU "
            "for Demucs separation. Set LYRIC_VIDEO_ALLOW_CPU=true only for testing."
        )
    return torch_module


def _ensure_demucs_cli() -> str:
    """Ensure the demucs CLI entry point is discoverable and return its path."""
    cli_path = shutil.which("demucs")
    if cli_path is None:
        raise RuntimeError(
            "Demucs CLI is not available on PATH. Install `demucs` inside the project "
            "virtual environment to continue."
        )
    return cli_path


def _hash_audio_file(audio_path: Path) -> str:
    """Compute a SHA-256 hash of the audio file for caching purposes."""
    sha256 = hashlib.sha256()
    with audio_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _collect_stem_candidates(root: Path) -> Dict[str, Path]:
    """Return a mapping of logical stem names to generated files."""
    candidates: Dict[str, Path] = {}
    for wav_path in root.rglob("*.wav"):
        name = wav_path.stem.lower()
        normalized = name.replace("-", "_")
        if "vocals" in normalized and "no" not in normalized:
            candidates["vocals"] = wav_path
        elif any(tag in normalized for tag in ("no_vocals", "instrumental", "accompaniment", "karaoke")):
            candidates["instrumental"] = wav_path
    return candidates


@dataclass(slots=True)
class DemucsEngine:
    """
    Demucs stem separation engine with GPU enforcement and caching.

    Args:
        model_name: Demucs model identifier.
        require_gpu: Whether to enforce CUDA GPU availability.
        cache_enabled: Toggle for reusing existing stems.
        overwrite_existing: Whether to overwrite cached stems when forcing runs.
        segment_seconds: Chunk size passed to Demucs for long files.
    """

    model_name: str = "htdemucs_ft"
    require_gpu: bool = True
    cache_enabled: bool = True
    overwrite_existing: bool = False
    segment_seconds: int = 60
    demucs_cli: str = field(init=False)
    torch_module: object = field(init=False)

    def __post_init__(self) -> None:
        self.demucs_cli = _ensure_demucs_cli()
        self.torch_module = _import_torch(skip_gpu_check=not self.require_gpu)
        LOGGER.info(
            "Demucs engine initialized (model=%s, require_gpu=%s, cache_enabled=%s)",
            self.model_name,
            self.require_gpu,
            self.cache_enabled,
        )

    def separate(self, audio_path: Path, output_dir: Path, *, force: bool = False) -> dict[str, Path]:
        """
        Separate audio into stems using Demucs.

        Args:
            audio_path: Source audio file.
            output_dir: Base directory for cached stems.
            force: Force re-separation even if cache is present.

        Returns:
            Mapping of stem names to file paths.
        """
        audio_path = audio_path.expanduser().resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        cache_key = _hash_audio_file(audio_path)
        cache_dir = output_dir / cache_key
        expected = {
            "vocals": cache_dir / "vocals.wav",
            "instrumental": cache_dir / "instrumental.wav",
        }

        if self.cache_enabled and not force and self._is_cache_valid(expected):
            LOGGER.info("Using cached stems for %s", audio_path.name)
            return expected

        if cache_dir.exists() and (force or self.overwrite_existing):
            shutil.rmtree(cache_dir)

        temp_dir = output_dir / f".demucs_tmp_{cache_key}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._run_demucs(audio_path, temp_dir)
            return self._promote_outputs(temp_dir, cache_dir, expected)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _run_demucs(self, audio_path: Path, destination: Path) -> None:
        """Invoke the Demucs CLI."""
        command = [
            self.demucs_cli,
            "--out",
            str(destination),
            "--jobs",
            "1",
            "--two-stems",
            "vocals",
            "-n",
            self.model_name,
            str(audio_path),
        ]
        if self.segment_seconds:
            command.extend(["--segment", str(self.segment_seconds)])
        device = "cuda" if self.require_gpu else "cpu"
        command.extend(["--device", device])

        LOGGER.info("Running Demucs: %s", " ".join(command))
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as exc:
            LOGGER.error("Demucs failed: %s", exc.stderr)
            raise RuntimeError(f"Demucs separation failed for {audio_path.name}") from exc

    def _promote_outputs(self, temp_dir: Path, cache_dir: Path, expected: Dict[str, Path]) -> Dict[str, Path]:
        """Move Demucs outputs into the cache directory and write manifest."""
        candidates = _collect_stem_candidates(temp_dir)
        if "vocals" not in candidates or "instrumental" not in candidates:
            raise RuntimeError(
                "Demucs output did not contain expected stems. Verify Demucs installation and model selection."
            )

        cache_dir.mkdir(parents=True, exist_ok=True)
        final_paths: Dict[str, Path] = {}
        for stem, src in candidates.items():
            dest = expected[stem]
            shutil.copy2(src, dest)
            final_paths[stem] = dest

        manifest = {
            "model": self.model_name,
            "source_audio": str(cache_dir.name),
            "stems": {stem: str(path.name) for stem, path in final_paths.items()},
        }
        with (cache_dir / CACHE_MANIFEST).open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)

        LOGGER.info("Demucs stems cached at %s", cache_dir)
        return final_paths

    @staticmethod
    def _is_cache_valid(expected: Dict[str, Path]) -> bool:
        """Check whether cached stems exist."""
        return all(path.exists() for path in expected.values())


def separate_audio(context: ProjectContext, audio_path: Path, force: bool = False) -> dict[str, Path]:
    """Convenience wrapper that loads configuration and executes separation."""
    config = get_config_manager().load_config("lyric_video_config.json", "lyric_video")
    stems_cfg = config.get("stems", {})
    engine = DemucsEngine(
        model_name=stems_cfg.get("model", "htdemucs_ft"),
        require_gpu=stems_cfg.get("gpu_required", True),
        cache_enabled=stems_cfg.get("cache_enabled", True),
        overwrite_existing=stems_cfg.get("overwrite_existing", False),
        segment_seconds=int(stems_cfg.get("chunk_size_seconds", 60) or 0),
    )
    context.ensure_structure()
    return engine.separate(audio_path, context.stems_dir, force=force)


__all__ = ["DemucsEngine", "separate_audio"]
