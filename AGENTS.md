# Repository Guidelines

**Windows-Only / Internal Use Notice**

This codebase targets Windows environments exclusively and is maintained for internal workflows at Bedrot Productions. The repository is publicly visible strictly for educational and referential purposes; external users should not expect cross-platform support or production readiness.

## Mandatory Briefing
Before writing any code, open `CLAUDE.md` and follow its directives. That file contains the authoritative checklist for entry points, config locations, duplicate functions, and tooling expectations; treating it as the first stop prevents regressions and aligns new work with current audits.

## Project Structure & Entry Points
`launcher.py` is the orchestrator; run it from the repo root to keep relative paths intact. Core apps live under `src/` with wrappers such as `src/snippet_remixer_modular.py`, but note the launcher still targets the legacy `src/snippet_remixer.py`. Configuration defaults sit in `config/` (plus a few module-level duplicates) and per-tool docs live in `docs/`. Utility scripts are in `tools/`; reproducible diagnostics live in `tests/`.

**Video Splitter Module**
- Entry script: `src/video_splitter_modular.py`
- Package: `src/video_splitter/`
- Config: `config/video_splitter_settings.json`
- Reference doc: `docs/video_splitter.md`
- Launcher tab: "Video Splitter" (between Snippet Remixer and Lyric Video Uploader)

**Transcriber Tool Module**
- Entry script: `src/transcriber_tool_modular.py`
- Package: `src/transcriber_tool/`
- Config: `config/transcriber_tool_settings.json`
- Launcher tab: "Transcriber Tool"
- Features: ElevenLabs Speech-to-Text API integration, drag-and-drop audio/video transcription
- Exports: TXT (plain text), SRT (SubRip), VTT (WebVTT) with word-level timestamps
- Dependencies: `elevenlabs`, `pysrt`, `webvtt-py`

**Caption Generator Module**
- Entry script: `src/caption_generator_modular.py`
- Package: `src/caption_generator/`
- Config: `config/caption_generator_settings.json`
- Launcher tab: "Caption Generator"
- Features: Creates lyric/caption videos from SRT/VTT + audio files using ffmpeg
- Style options: Font, size, color, background color, alignment (top/center/bottom)
- Video options: Resolution (1080p, 720p, 4K, vertical), FPS
- Dependencies: PyQt5, ffmpeg (system)

## Function Registry & Modularity
Before adding code, inspect `bedrot_media_suite_function_registry.json` to reuse existing utilities and avoid duplicates like `parse_aspect_ratio`, `generate_unique_suffix`, or redundant config accessors. After structural changes, regenerate the registry with `python tools/generate_function_registry.py` so future agents get accurate locations.

## Build & Run Workflow
On Windows prefer `start_launcher.bat`; it provisions the venv, installs `requirements.txt`, and opens the GUI. Manual flow: `python -m venv venv`, activate (`.\\venv\\Scripts\\activate` or `source venv/bin/activate`), then `pip install -r requirements.txt`. Launch individual tools with `python launcher.py`, `python src/reel_tracker_modular.py`, or `python tools/slideshow_editor.py` while iterating.

## Coding Standards & Output Rules
Follow PEP 8 with 4-space indent, `snake_case` modules/functions, and `PascalCase` Qt/Tk widgets. Centralize path handling through `src/core/path_utils.py` when practical instead of hardcoding separators. All console/UI text must be ASCIIreplace emojis with tags like `[INFO]`, `[ERROR]`, etc.to stay Windows-safe.

## No Fallback Policy
All new work must assume required dependencies are present and correctly configured. Do not ship automatic downgrades, alternate execution paths, or silent fallbacks for missing GPU support, third-party APIs, or optional packages. Instead, implement explicit preflight checks that fail fast with actionable setup instructions so Windows installations stay deterministic.

## Testing & Diagnostics
Tests are executable scripts in `tests/` that print explicit PASS/FAIL summaries; run individually (`python tests/test_config_system.py`, `python tests/test_video_logging.py`) or batch via `for %f in (tests\test_*.py) do python %f`. New features should ship with a sibling `test_<feature>.py` covering config paths, FFmpeg interactions, and thread safety; document OS-specific assumptions at the top.

## Commit & PR Expectations
History favors concise, present-tense subjects ("aspect ratio detection support"); keep them under 60 characters and expand in the body when needed. PRs should outline affected tools, list the exact test scripts run, attach before/after screenshots for UI work, flag config or `.env` changes, and request review from the module owner with at least one QA sign-off.

## Environment & Configuration Notes
Keep secrets out of `.env.example`; store credentials only in local `.env`. Verify FFmpeg (`ffmpeg -version`) and install `python3-tk` on Linux/WSL before launching Tkinter tools. Track duplicate configs (legacy Random Slideshow presets now sit under `archive/random_slideshow/config_root/`) and update all copies during changes. PyQt5 and PyQt6 coexistactivate the intended venv before running `src/release_calendar_modular.py`.
