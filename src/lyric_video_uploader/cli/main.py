# -*- coding: utf-8 -*-
"""
Lyric Video Uploader command-line interface powered by Typer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import typer

from .. import ProjectContext, get_package_logger
from ..bridge_snippets.publisher import publish as publish_bridge
from ..export.packager import package_exports
from ..schemas import LineSegment, coerce_word_tokens
from ..stems.service import separate as separate_stems
from ..stt import build_client_from_config
from ..tempo.manual_input import build_settings
from ..tempo.service import (
    build_from_tempo_map,
    build_manual_grid,
    load_persisted_beat_grid,
    persist_beat_grid,
)
from ..timing.alignment import build_document, snap_words_to_beats, write_outputs
from ..render.ffmpeg_renderer import FFmpegRenderer
from ..render.preset_manager import PresetManager

APP = typer.Typer(add_completion=False, help="Lyric Video Uploader CLI")
LOGGER = get_package_logger("lyric_video.cli")
TRANSCRIPT_FILENAME = "transcript.json"


def _project_context(project_dir: Path) -> ProjectContext:
    context = ProjectContext(root=project_dir.resolve())
    context.ensure_structure()
    return context


def _transcript_path(context: ProjectContext) -> Path:
    return context.timing_dir / TRANSCRIPT_FILENAME


def _load_transcript(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found at {path}. Run the transcribe command first.")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@APP.command()
def new(project_dir: Path) -> None:
    """Create a new project directory with expected structure."""
    context = _project_context(project_dir)
    typer.echo(f"[INFO] Project scaffold ready at: {context.root}")


@APP.command()
def stems(project_dir: Path, audio: Path, force: bool = typer.Option(False, help="Bypass cached stems")) -> None:
    """Separate stems from an input audio file using Demucs."""
    context = _project_context(project_dir)
    result = separate_stems(audio_path=audio, context=context, force=force)
    for stem, path in result.items():
        typer.echo(f"[INFO] {stem} -> {path}")


@APP.command()
def transcribe(project_dir: Path, audio: Path) -> None:
    """Transcribe audio using ElevenLabs and save transcript JSON."""
    context = _project_context(project_dir)
    client = build_client_from_config()
    result = client.transcribe(audio_path=audio, context=context)

    transcript_path = _transcript_path(context)
    payload = {
        "audio_path": str(audio.resolve()),
        "words": [word.to_dict() for word in result.words],
        "lines": [line.to_dict() for line in result.lines],
        "raw": result.raw,
    }
    with transcript_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    typer.echo(f"[INFO] Transcript saved to {transcript_path}")


@APP.command()
def beatgrid(
    project_dir: Path,
    bpm: Optional[float] = typer.Option(None, help="Manual BPM for uniform tempo"),
    offset: float = typer.Option(0.0, help="Offset in seconds for manual BPM"),
    tempo_map: Optional[Path] = typer.Option(None, help="Path to a tempo map CSV or JSON file"),
    subdivision: int = typer.Option(4, help="Sub-beats per beat when authoring manual grids"),
) -> None:
    """Create or load a beat grid for the project."""
    if bpm is None and tempo_map is None:
        raise typer.BadParameter("Provide either --bpm for manual tempo or --tempo-map for file-based tempo changes.")

    context = _project_context(project_dir)

    if tempo_map is not None:
        grid = build_from_tempo_map(tempo_map, subdivision=subdivision)
    else:
        settings = build_settings(str(bpm), str(offset), subdivision=subdivision)
        grid = build_manual_grid(settings)

    result = persist_beat_grid(grid, context)
    typer.echo(f"[INFO] Beat grid stored at {result.destination}")


@APP.command()
def timing(
    project_dir: Path,
    audio: Optional[Path] = typer.Option(None, help="Audio path for context; defaults to transcript metadata."),
    snap_to_beats: bool = typer.Option(False, help="Snap word timings to nearest beats in the beat grid."),
) -> None:
    """Generate SRT/ASS/JSON timing outputs."""
    context = _project_context(project_dir)
    transcript = _load_transcript(_transcript_path(context))

    audio_path = Path(transcript.get("audio_path", audio or context.root / "audio.wav"))
    if audio is not None:
        audio_path = audio.resolve()

    words = coerce_word_tokens(transcript.get("words", []))
    line_payload = transcript.get("lines") or []
    lines = [
        LineSegment(
            words=coerce_word_tokens(item.get("words", [])),
            text=item.get("text", ""),
            start=float(item.get("start", 0.0)),
            end=float(item.get("end", 0.0)),
        )
        for item in line_payload
    ]

    beat_grid_path = context.timing_dir / "beatgrid.json"
    beat_grid = load_persisted_beat_grid(beat_grid_path) if beat_grid_path.exists() else None

    if snap_to_beats and beat_grid is not None:
        words_snapped = snap_words_to_beats(words, beat_grid)
    else:
        words_snapped = words

    doc = build_document(
        audio_path=audio_path,
        words=words_snapped,
        lines=lines,
        beat_grid=beat_grid,
    )
    paths = write_outputs(doc, context)
    typer.echo(f"[INFO] Timing outputs generated: {paths}")

    # Publish bridge artifacts when beat grid is available.
    publish_bridge(doc, context)


@APP.command()
def render(
    project_dir: Path,
    audio: Path = typer.Option(..., help="Audio track to combine with subtitles."),
    preset: str = typer.Option("default", help="Render preset name"),
    output: Optional[Path] = typer.Option(None, help="Optional output path override"),
    background: Optional[Path] = typer.Option(None, help="Override preset background asset"),
) -> None:
    """Render the lyric video using FFmpeg NVENC."""
    context = _project_context(project_dir)
    preset_manager = PresetManager()
    preset_obj = preset_manager.get_preset(preset)

    ass_path = context.timing_dir / "lyrics.ass"
    if not ass_path.exists():
        raise FileNotFoundError(f"ASS subtitle file not found: {ass_path}. Run the timing command first.")

    audio_path = audio.resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file for rendering not found: {audio_path}")

    background_path = background.resolve() if background else preset_obj.background
    renderer = FFmpegRenderer()

    if output is None:
        render_dir = context.renders_dir / preset_obj.name
        render_dir.mkdir(parents=True, exist_ok=True)
        output_path = render_dir / "final.mp4"
    else:
        output_path = output.resolve()

    renderer.render(
        ass_path=ass_path,
        audio_path=audio_path,
        background_path=background_path,
        output_path=output_path,
        preset=preset_obj,
    )
    typer.echo(f"[INFO] Render complete: {output_path}")


@APP.command()
def package(
    project_dir: Path,
    render_path: Path,
    metadata_file: Path = typer.Option(..., help="Path to JSON metadata describing the upload."),
) -> None:
    """Bundle rendered assets, captions, and metadata for manual upload."""
    context = _project_context(project_dir)

    with metadata_file.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    caption_paths = {
        "words": context.timing_dir / "words.srt",
        "lines": context.timing_dir / "lines.srt",
        "ass": context.timing_dir / "lyrics.ass",
        "json": context.timing_dir / "lyrics.json",
    }

    extra_files = []
    beat_grid_path = context.timing_dir / "beatgrid.json"
    if beat_grid_path.exists():
        extra_files.append(beat_grid_path)
    snippet_bridge_dir = context.exports_dir / "snippet_bridge"
    if snippet_bridge_dir.exists():
        extra_files.extend(path for path in snippet_bridge_dir.iterdir() if path.is_file())

    ready_dir = package_exports(
        context,
        metadata,
        render_path=render_path,
        caption_paths=caption_paths,
        extra_files=extra_files,
    )
    typer.echo(f"[INFO] Export bundle ready at {ready_dir}")


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point used by launcher."""
    APP(prog_name="lyric-video-uploader", standalone_mode=False)


app = APP

__all__ = ["APP", "app", "main"]
