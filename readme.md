# Bedrot Productions - Media Tool Suite

A comprehensive Python-based multimedia processing suite for content creation, video downloading, editing, and automated slideshow generation. All tools are managed through a central GUI launcher with real-time process monitoring.

## Quick Start (Windows)

```batch
# Recommended method for Windows users
start_launcher.bat
```

## Quick Start (Linux/macOS)

```bash
# Install system dependencies (Linux/WSL)
sudo apt-get install python3-tk ffmpeg

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run the launcher
python launcher.py
```

## Directory Structure

```
bedrot-media-suite/
├── launcher.py                   # Main GUI launcher (Tkinter-based)
├── start_launcher.bat           # Windows batch launcher (recommended for Windows)
├── requirements.txt             # Python dependencies
├── .env                        # Environment configuration (create from .env.example)
├── .env.example               # Template for environment variables
│
├── config/                    # Primary configuration directory
│   ├── yt_downloader_gui_settings.json     # Media Downloader settings
│   ├── video_remixer_settings.json         # Snippet Remixer settings
│   ├── combined_random_config.json         # Random Slideshow settings
│   ├── config.json                         # Slideshow Editor settings
│   ├── reel_tracker_config.json            # Reel Tracker settings
│   ├── video_caption_generator_config.json # Caption Generator settings
│   ├── release_calendar_config.json        # Release Calendar settings
│   ├── calendar_data.json                  # Release Calendar data
│   └── slideshow_presets.json             # Slideshow presets
│
├── src/                       # Source code directory
│   ├── core/                 # Centralized utilities (partially implemented)
│   ├── media_download_app.py               # Standalone media downloader
│   ├── snippet_remixer_modular.py          # Snippet remixer entry point
│   ├── reel_tracker_modular.py             # Reel tracker entry point
│   ├── release_calendar_modular.py         # Release calendar entry point
│   ├── snippet_remixer/                    # Snippet remixer package
│   ├── random_slideshow/                   # Random slideshow package
│   ├── reel_tracker/                       # Reel tracker package
│   ├── release_calendar/                   # Release calendar package
│   └── video_caption_generator/            # Caption generator package
│
└── tools/                     # Standalone utilities
    ├── slideshow_editor.py   # PyQt5 slideshow editor
    ├── xyimagescaler.py     # Image scaling utility
    └── generate_function_registry.py # Code analysis tool

```

## Core Components

1. **Launcher (`launcher.py`)** - Central control hub with tabbed interface for all tools
2. **Media Downloader** - YouTube/media downloader with format conversion
3. **Snippet Remixer** - Creates remixed videos from random snippets
4. **Random Slideshow Generator** - Automated slideshow creation from images
5. **Reel Tracker** - Advanced content tracking with CSV backend
6. **Video Caption Generator** - AI-powered caption generation
7. **Release Calendar** - Music release scheduling (requires PyQt6)

## Installation & Setup

### Prerequisites

1. **Python 3.8+** - Download from [python.org](https://www.python.org/)
2. **FFmpeg/FFprobe** - Required for video processing
3. **System Dependencies:**
   - **Linux/WSL:** `sudo apt-get install python3-tk ffmpeg`
   - **Windows:** FFmpeg must be in PATH
   - **macOS:** `brew install ffmpeg`

### Windows Installation (Recommended)

1. **Clone the repository:**
   ```bash
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

### Manual Installation (All Platforms)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bedrot-media-suite.git
   cd bedrot-media-suite
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `.\venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Linux/WSL only - Install tkinter:**
   ```bash
   sudo apt-get install python3-tk
   ```

6. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

7. **Run the launcher:**
   ```bash
   python launcher.py
   ```

## Usage Guide

### Running the Launcher

**Windows (Recommended):**
```batch
start_launcher.bat
```

**All Platforms:**
```bash
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

```bash
# Media Downloader
python src/media_download_app.py

# Snippet Remixer (use modular version)
python src/snippet_remixer_modular.py

# Random Slideshow
python src/random_slideshow/main.py

# Reel Tracker
python src/reel_tracker_modular.py

# Release Calendar (requires PyQt6)
python src/release_calendar_modular.py

# Video Caption Generator
python -m src.video_caption_generator.main_app

# Tools
python tools/slideshow_editor.py
python tools/xyimagescaler.py
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

### 3. Random Slideshow Generator (`src/random_slideshow/main.py`)

**GUI Framework:** PyQt5  
**Config:** `config/combined_random_config.json`

**Features:**
- Continuous automated slideshow generation
- 16:9 and 9:16 aspect ratio support
- Batch processing capabilities
- Preset management system
- Resource-efficient processing

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

### 6. Video Caption Generator

**Entry:** `python -m src.video_caption_generator.main_app`  
**Config:** `config/video_caption_generator_config.json`

**Features:**
- AI-powered caption generation
- Live preview widget
- Font management system
- Multiple export formats
- Audio transcription support

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

