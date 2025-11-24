# Video Splitter Module

The Video Splitter slices long-form videos into evenly timed clips with optional jitter randomization. It is a Tkinter tool intended for rapid content repurposing workflows inside Bedrot Productions.

## Features

- Add multiple videos via file picker, folder ingestion, or drag-and-drop (TkDND).
- Auto-saves clip length, jitter, and output preferences to `config/video_splitter_settings.json`.
- Optional jitter slider (0–50%) randomizes clip durations ±N% while clamping at a minimum length.
- Queue multiple videos; each file generates numbered clips such as `_clip_000.mp4`.
- Uses FFmpeg stream-copy to avoid re-encoding when possible; fails fast if FFmpeg/FFprobe missing.
- Respect `[INFO]/[ERROR]` ASCII logging format and writes to `logs/video_splitter/video_splitter.log`.

## Workflow

1. Launch via `python src/video_splitter_modular.py` or through the main launcher tab.
2. Drag files/folders into the source list (folders are scanned for supported extensions).
3. Choose an output folder and configure clip length/jitter.
4. Click **Start Splitting**; progress updates per segment and per video.
5. Clips land inside the selected output directory with reset timestamps for standalone playback.

## Configuration Keys

| Key | Description |
| --- | --- |
| `clip_length_seconds` | Base clip duration in seconds. |
| `jitter_percent` | Percentage swing applied to the base duration. |
| `min_clip_length` | Safety floor so jitter never produces tiny clips. |
| `per_clip_jitter` | If `true`, jitter recalculates for every segment; otherwise once per file. |
| `reset_timestamps` | Includes `-reset_timestamps 1` for clean playback. |
| `overwrite_existing` | If `false`, existing clip files are skipped. |

## Testing

Tests live in `tests/test_video_splitter_*.py`:

- `test_video_splitter_config.py` validates autosave behavior.
- `test_video_splitter_scheduler.py` covers jitter schedule generation.
- `test_video_splitter_cli.py` exercises the FFmpeg pipeline against synthetic fixtures.
