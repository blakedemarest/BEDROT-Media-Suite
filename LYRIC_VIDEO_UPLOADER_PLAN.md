# Lyric Video Uploader Implementation Plan

This document captures the repository-aware plan for delivering the new `lyric_video_uploader` module requested in the Bedrot Lyric Video Uploader Agent system prompt. It reconciles the specification with the current Bedrot Media Suite (BMS) codebase so a follow-up agent can execute work without guessing about structure, dependencies, or Windows-specific launch requirements.

## 1. Research Highlights
- **Launcher integration:** `launcher.py` already wires six tool tabs via centralized script resolution; a new tab must follow the same pattern (status label, run/stop buttons, logging) and update the `SCRIPT_*_PATH` constants plus Tkinter UI blocks around lines 430–520.【F:launcher.py†L39-L89】【F:launcher.py†L372-L474】
- **Process management & logging:** The launcher routes tool output into a shared `ScrolledText` widget with timestamped logs handled by `update_log`; new modules should reuse this logging approach and rely on `core.logger` for internal loggers to stay consistent.【F:launcher.py†L91-L220】【F:src/core/logger.py†L1-L120】
- **Configuration system:** `core.config_manager.ConfigManager` provides defaults and script path resolution for existing apps; adding a lyric-video config requires extending `_get_default_config_for_app`, `get_script_path`, and `.env.example` mappings so Windows launcher overrides continue to work. The config should expose manual tempo/tempo-map settings instead of auto-detection.【F:src/core/config_manager.py†L21-L125】【F:.env.example†L29-L94】
- **Windows-only workflows:** `start_launcher.bat` provisions a venv and launches `launcher.py`; the new module must be callable from this flow and should not rely on POSIX tooling. GPU-specific dependencies (Demucs/Torch) need Windows-friendly installation instructions in docs and batch scripts.【F:start_launcher.bat†L1-L53】
- **Snippet Remixer architecture:** The remixer package lives in `src/snippet_remixer/` with a job queue (`job_queue.py`), config manager, and modular entry point. Integration hooks should align with this package (file contracts in `exports/` plus optional Python import) without editing its internals unless necessary.【F:src/snippet_remixer/__init__.py†L1-L40】【F:src/snippet_remixer/job_queue.py†L1-L140】
- **Testing conventions:** Existing regression tests are executable scripts under `tests/` that print PASS/FAIL summaries rather than using pytest. New coverage for lyric video functionality should follow this pattern (e.g., `tests/test_lyric_video_uploader.py`).【F:tests/test_config_system.py†L1-L120】
- **Requirements baseline:** `requirements.txt` already includes moviepy, ffmpeg-python, SpeechRecognition, etc., but lacks Demucs, Torch, pysubs2, and ElevenLabs SDK; plan for pinned Windows-compatible versions and GPU extras while avoiding duplicate entries.【F:requirements.txt†L1-L40】
- **No fallback policy:** Project owners requested strict dependency enforcement; the plan must remove every "fallback" path and instead perform preflight checks that fail fast when prerequisites (GPU, NVENC, ElevenLabs API access) are not satisfied.

## 2. Implementation Roadmap

### Phase 1 — Package Scaffold & Configuration
:::task-stub{title="Create lyric_video_uploader package skeleton"}
1. Add `src/lyric_video_uploader/` with subpackages mirroring the spec (`ingest`, `stems`, `stt`, `timing`, `tempo`, `render`, `export`, `bridge_snippets`, `ui`, `cli`, `schemas`, `tests` if colocated) and populate `__init__.py` with lazy imports following `snippet_remixer` conventions.【F:src/snippet_remixer/__init__.py†L1-L40】
2. Leverage `core.path_utils.get_path_resolver()` for project-relative directories (stems, timing, renders, exports) and `core.logger` for module-wide loggers.
3. Update `core.config_manager.ConfigManager` to register `'lyric_video'` defaults, including stems/STT/render options and ElevenLabs key placeholders, mirroring the archived `'mv_maker'` defaults (see `archive/mv_maker/config_root/`).【F:src/core/config_manager.py†L69-L125】
4. Extend `.env.example` and `core.config_manager.get_script_path` mapping so Windows overrides can set `SLIDESHOW_LYRIC_VIDEO_SCRIPT` and `SLIDESHOW_LYRIC_VIDEO_CONFIG` analogues.【F:.env.example†L45-L94】
:::

### Phase 2 — Configuration Schemas & Assets
:::task-stub{title="Define configuration & schema contracts"}
1. Create `config/lyric_video_config.json` seeded with defaults that match the spec (render backend, encoder, stems/STT settings) plus manual tempo controls (`default_bpm`, `allow_tempo_map`, file patterns) and ensure the `ConfigManager` loads it when `app_name='lyric_video'`.
2. Implement Pydantic models in `schemas/` for `WordToken`, `Line`, `LyricDoc`, `BeatGrid`, and `ProjectConfig`, exporting JSON Schemas alongside (write to `schemas/*.schema.json`). Clarify that `BeatGrid` values originate from user-supplied tempo data, not automated analysis.
3. Add a repository-level data directory (`assets/templates/lyric_video`, `assets/bg_loops`, `assets/fonts`) or reuse existing assets if present; document expected structure in package README.
4. Update `bedrot_media_suite_function_registry.json` regeneration instructions in this plan’s final checklist once new modules exist.【F:AGENTS.md†L13-L21】
:::

### Phase 3 — Stem Separation Service
:::task-stub{title="Implement stems engine with caching"}
1. Wrap Demucs (preferred) in `stems/demucs_engine.py` with GPU verification (`torch.cuda.is_available()`) and chunked inference; if GPU or model prerequisites are missing, raise a clear setup error rather than downgrading. Cache results under `<project>/stems/` keyed by SHA256 of input audio.
2. Integrate with `core.path_utils.PathResolver` for safe directory creation and reuse `core.thread_safety` utilities if background threads are required.
3. Expose `stems/service.py` with `separate(audio_path, *, force=False, progress_cb=None)` returning paths to vocals/instrumental and raising structured errors when GPUs missing.
4. Document Windows installation quirks for Demucs/Torch (CUDA 12, pip extra index) in the README section of the new module.
:::

### Phase 4 — STT Pipeline & Timing Outputs
:::task-stub{title="Build transcription and timing pipeline"}
1. Implement ElevenLabs STT client under `stt/elevenlabs_client.py` using `requests` with timeout/retry logic and environment-driven API key retrieval via `core.env_loader.get_env_var`. Provide CLI/UI error messaging when the key is absent.
2. Enforce ElevenLabs STT as the supported path in `stt/elevenlabs_client.py`; add upfront environment validation (API key present, service reachable) and fail fast with actionable errors instead of bundling alternate transcription engines.
3. Create `timing/alignment.py` that transforms word tokens into per-word SRT, line-level SRT, ASS (via `pysubs2`), and canonical JSON, honoring the gating rule by writing assets only after transcripts succeed.
4. Persist outputs under `<project>/timing/` and ensure file naming matches the spec: `words.srt`, `lines.srt`, `lyrics.ass`, `lyrics.json`.
:::

### Phase 5 — Manual Tempo Authoring & Beat Maps
:::task-stub{title="Collect user tempo data and build beat grids"}
1. Implement `tempo/manual_input.py` to accept BPM and offset from CLI/UI forms, validating numerical ranges and documenting when quarter-note grids or subdivisions are applied.
2. Support tempo changes by allowing users to load a tempo map file (e.g., CSV or JSON with `{timecode, bpm}` entries) via `tempo/tempo_map_loader.py`; include UI helpers to preview segments and warn about gaps/overlaps.
3. Build `tempo/service.py` that turns the manual tempo or tempo-map data into `BeatGrid` models stored at `<project>/timing/beatgrid.json`, marking provenance as `"manual"` and capturing tempo-change breakpoints for downstream consumers.
4. Provide utilities to snap word timings to beats without mutating raw timestamps, storing snapped indices and tempo-section metadata in `lyrics.json` for Snippet Remixer consumption.
:::

### Phase 6 — Snippet Remixer Bridge
:::task-stub{title="Publish lyric timeline for snippet_remixer"}
1. Define a file-based contract under `<project>/exports/snippet_bridge/` for `lyric_timeline.json`, `sections.json`, and `beatgrid.json`, ensuring serialization matches Snippet Remixer expectations and that tempo data reflects the manual tempo-map inputs (tempo sections, offsets, provenance).【F:src/snippet_remixer/job_queue.py†L1-L140】
2. Expose `bridge_snippets/publisher.py` that writes these files and asserts the `snippet_remixer` module is importable; if the import fails, surface a hard error directing the user to repair their installation before proceeding.
3. Emit log markers (`LyricTimingReady`, `BeatGridReady`) through `core.logger` so existing log monitoring tools can react.
4. Update Snippet Remixer documentation (if required) to mention the new bridge and confirm no launcher workflow breaks.
:::

### Phase 7 — Rendering Pipeline
:::task-stub{title="Implement ASS-based rendering with NVENC"}
1. Author `render/preset_manager.py` to load template metadata (backgrounds, fonts, layout) from `config/lyric_video_config.json` and assets directories.
2. Build `render/ffmpeg_renderer.py` that consumes ASS files and audio to produce MP4 outputs using FFmpeg with `h264_nvenc`, validating NVENC availability during initialization and halting with guidance if the encoder is not present; rely on `ffmpeg-python` already in requirements.
3. Provide optional MoviePy compositor in `render/moviepy_renderer.py`, behind a feature flag, ensuring resources are released with `clip.close()` per existing project conventions.【F:AGENTS.md†L31-L37】
4. Save renders under `<project>/renders/{preset}/final.mp4` and include adjacent copies of `lyrics.ass` and `words.srt`.
:::

### Phase 8 — Export Packaging & Manual Upload Guidance
:::task-stub{title="Prepare outputs for user-managed uploading"}
1. Replace the uploader plugin scope with an export packager that assembles rendered video, SRT/ASS captions, and metadata JSON under `<project>/exports/ready_for_upload/` for users to submit manually.
2. Document required metadata fields (title, description, tags) in a structured template file so users can paste values into YouTube or other platforms without an automated API call.
3. Update CLI/UI flows to stop after export packaging, displaying explicit instructions that uploading is manual and pointing to the generated metadata bundle.
:::

### Phase 9 — CLI & GUI Entry Points
:::task-stub{title="Expose CLI tool and launcher tab"}
1. Implement Typer/Click-based CLI in `cli/main.py` with commands `new`, `render`, and `package` (for export bundling), writing a thin wrapper script (`tools/bms_lv.py` or entry stub) for Windows shortcuts.
2. Build a Tkinter panel in `ui/panel.py` following launcher styling: file pickers (audio/vocals), toggles, API key field, progress bars, and disabled buttons that unlock post-transcription. Reuse `core.safe_print` for console output.
3. Update `launcher.py` to add a new `SCRIPT_7_PATH` (or rename existing constants) and corresponding tab with RUN/STOP buttons pointing to the module’s GUI entry script. Maintain Windows color/style conventions shown in existing tabs.【F:launcher.py†L39-L189】【F:launcher.py†L372-L474】
4. Modify `start_launcher.bat` to mention the new dependency bootstrap if it needs pre-download steps (e.g., `python -m lyric_video_uploader.cli` setup), but keep current venv workflow intact.【F:start_launcher.bat†L1-L53】
:::

### Phase 10 — Testing, Samples, and Tooling
:::task-stub{title="Add automated coverage and demo assets"}
1. Create `tests/test_lyric_video_uploader.py` mirroring existing script-style tests to exercise config loading, stem caching mocks, STT client mock, manual tempo map ingestion, and renderer command construction.【F:tests/test_config_system.py†L1-L120】
2. Provide a small demo project folder under `tests/data/lyric_video_demo/` (short audio clip, expected outputs) to drive integration tests without large binaries; ensure Git LFS or zipped assets aren’t required.
3. Update `tools/generate_function_registry.py` output after new modules land and include instructions in this plan’s final checklist to rerun it.【F:AGENTS.md†L13-L21】
4. Document manual QA steps for Windows (Demucs GPU verification, ElevenLabs integration) and include them in the README or docs addendum.
:::

### Phase 11 — Documentation & Release Notes
:::task-stub{title="Document module and update suite references"}
1. Add `docs/lyric_video_uploader/` with architecture diagrams (if feasible), config reference, and troubleshooting specific to CUDA/FFmpeg/ElevenLabs.
2. Update `readme.md` to introduce the Lyric Video Uploader, mention Windows + RTX 4090 expectations, and clarify archived MV Maker/Slideshow status if still referenced.
3. Insert launcher screenshot(s) showing the new tab once implemented (Windows capture) and describe CLI usage.
4. Append release notes or changelog entry summarizing dependencies and manual setup requirements.
:::

## 3. Dependency & Environment Checklist
- Pin Windows-friendly versions for `torch`, `torchaudio`, `demucs`, `pysubs2`, `typer` (or `click`), and `tqdm` in `requirements.txt`. Provide CUDA 12 guidance in docs.
- Validate ElevenLabs SDK, Demucs, Torch, pysubs2, typer, and tqdm installations as required dependencies during setup scripts so missing packages are surfaced immediately on Windows.
- Verify FFmpeg availability via existing environment vars; document how to configure custom paths if NVENC detection fails.

## 4. Validation Plan
1. Run unit-style scripts for stems, manual tempo parsing, and export packaging (mocking heavy dependencies) plus existing regression suite (`python tests/test_config_system.py`, etc.).
2. Execute two end-to-end scenarios on Windows: (A) mixed track only (Demucs + ElevenLabs); (B) vocals supplied (skip stems). Confirm outputs in `timing/`, `renders/`, and `exports/snippet_bridge/` with beat maps derived from manual tempo input or tempo map file.
3. Launch the GUI via `start_launcher.bat` to ensure the new tab works, buttons gate correctly, and log output mirrors other tools.
4. Validate CLI commands (`bms-lv new`, `bms-lv render`, `bms-lv package`) inside the repo venv and confirm help text is accurate.

## 5. Final Deliverables Checklist
- [ ] New `src/lyric_video_uploader/` package with submodules, schemas, and documentation.
- [ ] Updated configuration files (`config/lyric_video_config.json`, `.env.example`, `core.config_manager` defaults, launcher script map).
- [ ] Launcher and batch script updates exposing the GUI tile and ensuring Windows compatibility.
- [ ] Added requirements, assets directories, and demo data.
- [ ] Automated tests and refreshed `bedrot_media_suite_function_registry.json`.
- [ ] Updated README/docs highlighting the new workflow, manual tempo entry expectations, and dependency notes.
- [ ] PR summary capturing tests run and any manual verification steps for GPU/STT integration and tempo-map validation.
