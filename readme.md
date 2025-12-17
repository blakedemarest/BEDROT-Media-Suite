# Bedrot Productions - Media Tool Suite

> **Important:** This repository is maintained for internal workflows at Bedrot Productions and is provided publicly for educational and referential purposes only. The suite targets Windows environments exclusively and is not supported on macOS or Linux.

A comprehensive Python-based multimedia processing suite for content creation, video downloading, editing, and automated slideshow generation. All tools are managed through a central GUI launcher with real-time process monitoring, and every workflow assumes a Windows host.

## Quick Start (Windows Only)

```batch
# Recommended method for Windows users
start_launcher.bat
```

> **Note:** Non-Windows operating systems are unsupported. The commands and tooling documented below assume Windows PowerShell or Command Prompt.

## Directory Structure

```
bedrot-media-suite/
|-- launcher.py                    # Main GUI launcher (Tkinter-based)
|-- start_launcher.bat             # Windows batch launcher (recommended for Windows)
|-- requirements.txt               # Python dependencies
|-- .env                           # Environment configuration (create from .env.example)
|-- .env.example                   # Template for environment variables
|-- config/                        # Primary configuration directory
|   |-- yt_downloader_gui_settings.json     # Media Downloader settings
|   |-- video_remixer_settings.json         # Snippet Remixer settings
|   |-- video_splitter_settings.json        # Video Splitter settings
|   |-- config.json                        # Slideshow Editor settings
|   |-- reel_tracker_config.json           # Reel Tracker settings
|   |-- release_calendar_config.json       # Release Calendar settings
|   |-- calendar_data.json                 # Release Calendar data
|   |-- transcriber_tool_settings.json     # Transcriber Tool settings
|   `-- caption_generator_settings.json    # Caption Generator settings
|-- src/                           # Source code directory
|   |-- core/                      # Centralized utilities (shared)
|   |-- media_download_app.py      # Standalone media downloader
|   |-- snippet_remixer_modular.py # Snippet Remixer entry point
|   |-- video_splitter_modular.py  # Video Splitter entry point
|   |-- reel_tracker_modular.py    # Reel Tracker entry point
|   |-- release_calendar_modular.py# Release Calendar entry point
|   |-- transcriber_tool_modular.py# Transcriber Tool entry point
|   |-- caption_generator_modular.py# Caption Generator entry point
|   |-- snippet_remixer/           # Snippet Remixer package
|   |-- video_splitter/            # Video Splitter package
|   |-- reel_tracker/              # Reel Tracker package
|   |-- release_calendar/          # Release Calendar package
|   |-- transcriber_tool/          # Transcriber Tool package
|   `-- caption_generator/         # Caption Generator package
|-- archive/                       # Archived modules retained for reference
|   |-- mv_maker/                  # Legacy MV Maker package and configs
|   `-- random_slideshow/          # Legacy Random Slideshow package and configs
`-- tools/                         # Standalone utilities
    |-- slideshow_editor.py        # PyQt5 slideshow editor
    |-- xyimagescaler.py           # Image scaling utility
    `-- generate_function_registry.py # Code analysis tool
```

## Core Components

1. **Launcher (`launcher.py`)** - Central control hub with tabbed interface for all tools
2. **Media Downloader** - YouTube/media downloader with format conversion
3. **Snippet Remixer** - Creates remixed videos from random snippets
4. **Video Splitter** - Batch slices long-form videos into configurable clip lengths with jitter
5. **Reel Tracker** - Advanced content tracking with CSV backend
6. **Release Calendar** - Music release scheduling (requires PyQt6)
7. **Lyric Video Uploader** - Manual tempo lyric video pipeline (Tkinter GUI + Typer CLI, see `docs/lyric_video_uploader/`)
8. **Transcriber Tool** - ElevenLabs-powered speech-to-text with SRT/VTT export
9. **Caption Generator** - Creates lyric videos from SRT/VTT + audio files

> Archived modules: MV Maker and Random Slideshow now live under `archive/` for historical access only.

## Installation & Setup

### Prerequisites (Windows)

1. **Windows 10 or later** with permission to install software
2. **Python 3.8+** - Download from [python.org](https://www.python.org/)
3. **FFmpeg/FFprobe** - Install and add to PATH (e.g., via [FFmpeg for Windows builds](https://www.gyan.dev/ffmpeg/builds/))

### Windows Installation (Recommended)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/yourusername/bedrot-media-suite.git
   cd bedrot-media-suite
   ```

2. **Run the Windows launcher:**
   ```batch
   start_launcher.bat
   ```
   This will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Launch the application

### Manual Installation (Windows)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/yourusername/bedrot-media-suite.git
   cd bedrot-media-suite
   ```

2. **Create virtual environment:**
   ```powershell
   python -m venv venv
   ```

3. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure environment (optional):**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your preferred settings
   ```

6. **Run the launcher:**
   ```powershell
   python launcher.py
   ```

## Usage Policy

- Intended for internal use by Bedrot Productions staff.
- Provided publicly for educational and referential review only.
- External users should not expect official support, warranties, or non-Windows compatibility.

## Usage Guide

### Running the Launcher

**Windows (Recommended):**
```batch
start_launcher.bat
```

**Windows (Manual command):**
```powershell
python launcher.py
```

### Using the Suite

1. **Launch** - Run the launcher from project root
2. **Select Tool** - Click the tab for your desired tool
3. **Run Tool** - Click the "Run..." button to launch
4. **Monitor** - Watch real-time logs in the output area
5. **Multiple Tools** - Run several tools simultaneously
6. **Shutdown** - Close launcher to terminate all tools

### Running Tools Individually

You can also run tools directly without the launcher:

```powershell
# Media Downloader
python src/media_download_app.py

# Snippet Remixer (use modular version)
python src/snippet_remixer_modular.py

# Video Splitter
python src/video_splitter_modular.py

# Reel Tracker
python src/reel_tracker_modular.py

# Release Calendar (requires PyQt6)
python src/release_calendar_modular.py

# Lyric Video Uploader (placeholder GUI)
python src/lyric_video_uploader_modular.py

# Transcriber Tool
python src/transcriber_tool_modular.py

# Caption Generator
python src/caption_generator_modular.py

# Tools
python tools/slideshow_editor.py
python tools/xyimagescaler.py

# Lyric Video Uploader CLI
python -m src.lyric_video_uploader.cli --help

# Archived modules (reference only)
# See archive/mv_maker/ and archive/random_slideshow/ for legacy entry points.
```

## Tool Descriptions

### 1. Media Downloader (`src/media_download_app.py`)

**GUI Framework:** Tkinter  
**Config:** `config/yt_downloader_gui_settings.json`

**Features:**
- Multi-platform video/audio downloading via yt-dlp
- MP4/MP3 format conversion
- Time trimming and aspect ratio adjustment
- Queue-based batch processing
- Real-time progress updates

### 2. Snippet Remixer (`src/snippet_remixer_modular.py`)

**GUI Framework:** Tkinter  
**Config:** `config/video_remixer_settings.json`

**Features:**
- Random video snippet combination
- BPM-based or seconds-based timing
- Background processing with progress tracking
- Automatic temp file cleanup
- Output naming with unique suffixes

### 3. Video Splitter (`src/video_splitter_modular.py`)

**GUI Framework:** Tkinter  
**Config:** `config/video_splitter_settings.json`

**Features:**
- Queue-based source list with file/folder drag-and-drop
- Configurable clip length plus minimum guardrail
- Jitter slider randomizes segment durations for organic edits
- Autosaves preferences (output directory, jitter, timestamps)
- Stream-copy splitting with optional `-reset_timestamps 1`

### 4. Reel Tracker (`src/reel_tracker_modular.py`)

**GUI Framework:** PyQt5  
**Config:** `config/reel_tracker_config.json`

**Features:**
- CSV-based content management
- Advanced configuration with version history
- Automatic backup system
- Bulk editing capabilities
- Media randomization tools
- Custom metadata fields

### 5. Release Calendar (`src/release_calendar_modular.py`)

**GUI Framework:** PyQt6 (Note: Different from other tools!)  
**Config:** `config/release_calendar_config.json`, `config/calendar_data.json`

**Features:**
- Visual drag-and-drop calendar interface
- Multi-artist release scheduling
- 9+ deliverable checklist per release
- Waterfall strategy (8 singles, 1 EP, 1 album/year)
- Excel and iCal export
- Automatic conflict detection
- Friday release day highlighting

### 6. Transcriber Tool (`src/transcriber_tool_modular.py`)

**GUI Framework:** PyQt5
**Config:** `config/transcriber_tool_settings.json`

**Features:**
- Drag-and-drop audio/video transcription using ElevenLabs Speech-to-Text API (Scribe v1)
- Multi-format export: TXT (plain text), SRT, VTT with word-level timestamps
- Audio format conversion (MP4, WAV, M4A, FLAC to MP3)
- Speaker diarization and audio event tagging
- Batch processing with real-time progress
- Precise word-by-word timing for lyric video synchronization

**Requirements:**
- `ELEVENLABS_API_KEY` environment variable set in `.env`

### 7. Caption Generator (`src/caption_generator_modular.py`)

**GUI Framework:** PyQt5
**Config:** `config/caption_generator_settings.json`

**Features:**
- Creates lyric/caption videos from SRT/VTT + audio files
- Customizable font (Arial Narrow, Impact, etc.), size, and color
- Background color selection
- Multiple resolution presets (1080p, 720p, 4K, vertical 1080x1920)
- Text alignment options (top, center, bottom)
- Uses ffmpeg with libass subtitle filter
- Works seamlessly with Transcriber Tool output

### Archived Modules (reference only)

- Random Slideshow (`archive/random_slideshow/`) Ã¢â‚¬â€ legacy PyQt5 generator and original configs now stored under `config_root/`.
- MV Maker (`archive/mv_maker/`) Ã¢â‚¬â€ legacy captioning suite with archived configs under `config_root/`.

## Additional Tools

### Slideshow Editor (`tools/slideshow_editor.py`)
- PyQt5-based single slideshow creator
- Drag-and-drop image interface
- Duration and aspect ratio controls
- Config: `config/config.json`

### XY Image Scaler (`tools/xyimagescaler.py`)
- Simple image scaling/cropping utility
- Default output: 1632x2912
- Tkinter-based interface

### Function Registry Generator (`tools/generate_function_registry.py`)
- Code analysis tool
- Generates function registry for codebase
- Useful for documentation and refactoring

## Troubleshooting

### Common Issues

1. **"No module named tkinter"**
   - Linux/WSL: `sudo apt-get install python3-tk`
   - Windows: Reinstall Python with tkinter included

2. **FFmpeg not found**
   - Ensure FFmpeg is in system PATH
   - Windows: Add FFmpeg/bin to environment variables
   - Linux: `sudo apt install ffmpeg`

3. **PyQt5/PyQt6 conflicts**
   - Run tools through launcher (isolates processes)
   - Both versions can coexist when launched separately

4. **Module import errors**
   - Always run from project root directory
   - Use modular entry points (e.g., `snippet_remixer_modular.py`)
   - Ensure virtual environment is activated

5. **Configuration file not found**
   - Check `/config/` directory first
   - Some modules have configs in subdirectories
   - Create from defaults if missing

6. **Launcher won't start tools**
   - Check log output for specific errors
   - Verify Python path in virtual environment
   - Some launcher fallback paths are incorrect (known issue)

### Getting Help

- Check the launcher's log output for detailed error messages
- Review CLAUDE.md for technical implementation details
- Ensure all prerequisites are installed
- Verify FFmpeg is accessible from command line: `ffmpeg -version`

## Known Issues

1. **Launcher fallback paths** - Some hardcoded paths in launcher.py are incorrect
2. **Configuration duplication** - Some modules have config files in multiple locations
3. **Inconsistent entry points** - Mix of modular and direct entry points
4. **Missing tkinter in requirements** - Must be installed separately on Linux/WSL

## Contributing

This project is actively maintained. When contributing:
- Follow existing code patterns
- Update both README.md and CLAUDE.md
- Test on both Windows and Linux/WSL
- Maintain backwards compatibility

## License

[Add your license information here]




