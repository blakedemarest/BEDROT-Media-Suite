# Lyric Video Uploader – Developer Notes

This module delivers the full lyric video pipeline: Demucs stem separation, ElevenLabs transcription, manual tempo authoring, beat-aligned timing exports, NVENC/MoviePy rendering, Snippet Remixer bridge artifacts, and export packaging. Both a Typer CLI and a Tkinter GUI are provided; the launcher tab now launches the new GUI.

## Current Capabilities (2025-10-28)
- ✅ GPU-validated Demucs separation with SHA256 caching and manifest metadata.
- ✅ ElevenLabs STT client with retry/backoff and actionable failure messages.
- ✅ Timing pipeline generating `words.srt`, `lines.srt`, `lyrics.ass`, `lyrics.json`, and beat metadata.
- ✅ Snippet Remixer bridge exports (`lyric_timeline.json`, `sections.json`, `beatgrid.json`) with log markers (`LyricTimingReady`, `BeatGridReady`).
- ✅ Rendering via FFmpeg NVENC plus optional MoviePy fallback.
- ✅ Export packaging that bundles renders, captions, and metadata for manual uploads.
- ✅ Tests covering tempo parsing, beat grid persistence, timing exports, and packaging workflow.

## Dependency Provisioning (Windows Only)
The suite assumes an RTX-class GPU with CUDA 12 drivers. Install dependencies inside the project venv created by `start_launcher.bat`.

```powershell
%VENV_PYTHON% -m pip install --upgrade pip
%VENV_PYTHON% -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
%VENV_PYTHON% -m pip install demucs pysubs2 typer tqdm moviepy
```

> **No fallback policy:** Missing CUDA, Demucs, or NVENC triggers hard failures. Do not ship CPU fallbacks.

## CLI Workflow (Typer)
```powershell
python -m src.lyric_video_uploader.cli new C:\Projects\Lyrics
python -m src.lyric_video_uploader.cli stems C:\Projects\Lyrics --audio path\to\mix.wav
python -m src.lyric_video_uploader.cli transcribe C:\Projects\Lyrics --audio path\to\mix.wav
python -m src.lyric_video_uploader.cli beatgrid C:\Projects\Lyrics --bpm 120 --offset 0.0
python -m src.lyric_video_uploader.cli timing C:\Projects\Lyrics --audio path\to\mix.wav --snap-to-beats
python -m src.lyric_video_uploader.cli render C:\Projects\Lyrics --audio path\to\mix.wav --preset default
python -m src.lyric_video_uploader.cli package C:\Projects\Lyrics --render-path renders\default\final.mp4 --metadata-file docs\example_metadata.json
```

## GUI Workflow
Run `python src/lyric_video_uploader_modular.py` or select the Lyric Video Uploader tab inside `launcher.py`. The GUI exposes buttons for each pipeline stage, tracks progress in the log panel, and enforces the same dependency checks as the CLI.

## Required Assets
- Add looped backgrounds under `assets/lyric_video/backgrounds/` (e.g., `default_loop.mp4`).
- Place render presets in `config/lyric_video_config.json` referencing background and font assets.
- Install fonts referenced by presets in `assets/lyric_video/fonts/`.

## Testing
Run the module smoke tests:
```powershell
python tests/test_lyric_video_uploader.py
```
The script exercises tempo parsing, beat grid persistence, timing export generation, and export packaging.

## Next Enhancements
- Add demo assets under `tests/data/lyric_video_demo/` for reproducible integration runs.
- Expand CLI and GUI to support tempo map browsing and section previews.
- Incorporate project metadata management (title/description templates) within the UI.
