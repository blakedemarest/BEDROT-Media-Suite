"""
Smoke test scaffold for Lyric Video Uploader placeholders.

The suite prints PASS/FAIL summaries to align with existing Bedrot test scripts.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.lyric_video_uploader import ProjectContext
from src.lyric_video_uploader.tempo.manual_input import build_settings, parse_bpm, parse_offset
from src.lyric_video_uploader.tempo.tempo_map_loader import load_tempo_map
from src.lyric_video_uploader.tempo.service import persist_beat_grid, load_persisted_beat_grid
from src.lyric_video_uploader.schemas import WordToken, LineSegment, TempoEvent, BeatGrid
from src.lyric_video_uploader.timing.alignment import build_document, write_outputs

try:  # pragma: no cover - optional dependency
    import pysubs2  # noqa: F401
    PYSUBS_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    PYSUBS_AVAILABLE = False
from src.lyric_video_uploader.export.packager import package_exports


def run() -> bool:
    """Execute placeholder assertions."""
    results: list[tuple[str, bool]] = []

    # BPM parsing
    try:
        assert parse_bpm("128") == 128.0
        results.append(("parse_bpm accepts numeric strings", True))
    except Exception as exc:  # pragma: no cover - CLI style test
        results.append((f"parse_bpm raised unexpected error: {exc}", False))

    try:
        parse_bpm("-10")
        results.append(("parse_bpm rejects negative BPM (expected failure)", False))
    except ValueError:
        results.append(("parse_bpm rejects negative BPM", True))

    # Offset parsing
    try:
        assert parse_offset("1.5") == 1.5
        results.append(("parse_offset handles decimals", True))
    except Exception as exc:
        results.append((f"parse_offset error: {exc}", False))

    # Manual settings builder
    try:
        settings = build_settings("90", "0.25", subdivision=8)
        assert settings.bpm == 90.0 and settings.offset_seconds == 0.25 and settings.subdivision == 8
        results.append(("build_settings returns expected dataclass", True))
    except Exception as exc:
        results.append((f"build_settings error: {exc}", False))

    # Project context directory provisioning
    temp_dir = Path(tempfile.mkdtemp(prefix="lyric_video_test_"))
    try:
        context = ProjectContext(root=temp_dir)
        context.ensure_structure()
        expected = [
            context.stems_dir,
            context.timing_dir,
            context.renders_dir,
            context.exports_dir / "snippet_bridge",
            context.exports_dir / "ready_for_upload",
        ]
        if all(path.exists() for path in expected):
            results.append(("ProjectContext.ensure_structure creates directories", True))
        else:
            results.append(("ProjectContext.ensure_structure missing directories", False))
        # Tempo map loader (CSV)
        tempo_csv = temp_dir / "tempo.csv"
        tempo_csv.write_text("start,bpm\n0,120\n10,128\n", encoding="utf-8")
        events = load_tempo_map(tempo_csv)
        results.append(("tempo_map_loader parses CSV", len(events) == 2 and events[1].bpm == 128))

        # Beat grid persistence
        grid = BeatGrid(source="test", events=[TempoEvent(start=0.0, bpm=120)])
        persist_result = persist_beat_grid(grid, context)
        loaded_grid = load_persisted_beat_grid(persist_result.destination)
        results.append(("persist_beat_grid writes file", persist_result.destination.exists()))
        results.append(("load_persisted_beat_grid returns events", bool(loaded_grid.events)))

        # Timing outputs
        words = [
            WordToken(text="Hello", start=0.0, end=0.5),
            WordToken(text="world", start=0.5, end=1.0),
        ]
        line = LineSegment(words=words, text="Hello world", start=0.0, end=1.0)
        doc = build_document(audio_path=temp_dir / "dummy.wav", words=words, lines=[line], beat_grid=grid)
        if PYSUBS_AVAILABLE:
            outputs = write_outputs(doc, context)
            timing_files_exist = all(Path(path).exists() for path in outputs.values() if path is not None)
            results.append(("write_outputs generates timing files", timing_files_exist))
        else:
            outputs = {"words_srt": None, "lines_srt": None, "lyrics_ass": None, "lyrics_json": None}
            results.append(("write_outputs skipped (pysubs2 missing)", True))

        # Package exports
        render_path = temp_dir / "final.mp4"
        render_path.write_bytes(b"fakevideo")
        metadata = {"title": "Test", "description": "Demo"}
        caption_inputs = {
            key: Path(path) for key, path in outputs.items() if path is not None
        } if PYSUBS_AVAILABLE else {}
        ready_dir = package_exports(
            context,
            metadata,
            render_path=render_path,
            caption_paths=caption_inputs,
            extra_files=[persist_result.destination],
        )
        results.append(("package_exports bundles files", ready_dir.exists() and any(ready_dir.iterdir())))

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Report results
    total = len(results)
    passed = sum(1 for _, ok in results if ok)

    print("Lyric Video Uploader Placeholder Tests")
    for message, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f" - {status}: {message}")

    outcome = passed == total
    overall = "PASS" if outcome else "FAIL"
    print(f"RESULT: {overall} ({passed}/{total} checks passed)")
    return outcome


if __name__ == "__main__":
    success = run()
    raise SystemExit(0 if success else 1)
