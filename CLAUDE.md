# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Last Maintenance Scan**: December 19, 2024
- Function registry updated: 102 files, 212 functions, 118 classes, 1088 methods, 21 duplicates
- Entry points verified: All launcher paths exist and are correct
- Config files mapped: 11 config files in /config/, 1 duplicate in src/random_slideshow/config/
- Dependencies verified: PyQt5 (22 files), PyQt6 (4 files - release_calendar only), Tkinter (3 files)

## CRITICAL: Check Function Registry Before Writing Code

**IMPORTANT**: Before creating ANY new functions, methods, or scripts, you MUST check the function registry to avoid duplicates:

**Function Registry Location**: `bedrot_media_suite_function_registry.json` (at repository root)

This registry contains:
- All existing functions, classes, and methods in the codebase
- Their locations (file paths and line numbers)
- Signatures and docstrings
- Identified duplicate functions (23 duplicates as of last scan)

**Before writing code**:
1. Check if a similar function already exists in the registry
2. Reuse existing utilities instead of creating duplicates
3. If modifying existing functions, note their current locations
4. Update the registry after significant changes using:
   ```bash
   python tools/generate_function_registry.py
   ```

**Registry Stats (Last Updated: December 19, 2024)**:
- Files scanned: 102
- Functions found: 212
- Classes found: 118
- Methods found: 1088
- Duplicates found: 21

**Known Duplicates to Avoid**:
- `parse_aspect_ratio` - exists in 2 files
- `generate_unique_suffix` - exists in 2 files
- `main` - exists in 23 files (expected for entry points)
- `parse_time_to_seconds` - exists in 2 files
- `get_config_manager`, `get_path_resolver`, `get_video_processor` - each in 2 files
- `get_transcriber`, `get_caption_exporter`, `get_live_preview_widget` - each in 2 files

## Project Overview

The **Bedrot Productions Media Tool Suite** is a sophisticated Python-based collection of multimedia processing tools designed for content creation, video downloading, editing, and automated slideshow generation. The suite has evolved from monolithic scripts to a modern modular architecture with centralized process orchestration.

## Critical Implementation Notes

### Entry Point Status (Verified)
**IMPORTANT**: The codebase has mixed entry point patterns:

**Modular Wrappers** (in src/ directory):
- `reel_tracker_modular.py` - thin wrapper for reel_tracker package
- `release_calendar_modular.py` - thin wrapper for release_calendar package  
- `snippet_remixer_modular.py` - thin wrapper for snippet_remixer package

**Standalone Files** (in src/ directory):
- `media_download_app.py` - self-contained media downloader

**Package Entry Points** (verified to exist):
- `random_slideshow/main.py` - primary entry point
- `random_slideshow/main_app.py` - also exists (full GUI)
- `reel_tracker/main_app.py` - PyQt5 application
- `release_calendar/main_app.py` - PyQt6 application
- `snippet_remixer/main.py` - package entry
- `snippet_remixer/main_app.py` - GUI application
- `video_caption_generator/main_app.py` - main application

**Launcher.py Fallback Paths** (ALL VERIFIED TO EXIST - December 19, 2024):
- Line 48: `src/media_download_app.py` ✓
- Line 49: `src/snippet_remixer_modular.py` ✓ (now uses modular wrapper)
- Line 50: `src/random_slideshow/main.py` ✓
- Line 51: `src/reel_tracker_modular.py` ✓
- Line 52: `src/video_caption_generator/main_app.py` ✓
- Line 53: `src/release_calendar_modular.py` ✓

### Configuration File Locations (Actual State)
**WARNING**: Configuration files are scattered across multiple locations:

**Primary Config Directory** (`/config/`):
- `calendar_data.json` - release calendar data storage
- `combined_random_config.json` - slideshow settings
- `config.json` - slideshow editor settings
- `random_config.json` - legacy slideshow config
- `reel_tracker_config.json` - reel tracker settings
- `release_calendar_config.json` - release calendar settings
- `slideshow_presets.json` - slideshow presets
- `video_caption_generator_config.json` - caption generator settings
- `video_remixer_settings.json` - snippet remixer settings
- `yt_downloader_gui_settings.json` - media downloader settings

**Duplicate/Secondary Locations Found**:
- `src/random_slideshow/config/slideshow_presets.json` - duplicate of /config/slideshow_presets.json
- `src/video_caption_generator/config/video_caption_generator_config.json` - duplicate caption config

**Config Management Approaches**:
- **Direct JSON**: 17 files use `json.load()`/`json.dump()` directly
- **Core Config Manager**: Only 5 files import from `core.config_manager` or `core` config functions
- **Module-Specific**: Each module has its own `config_manager.py` with different implementations
- **Advanced**: Only `reel_tracker` has version history and audit trails

## Quick Start Commands

### Running the Application
```bash
# Main entry point - run from project root
python launcher.py

# Primary Windows entry point (RECOMMENDED for Windows users)
start_launcher.bat

# The batch file handles:
# - Virtual environment creation/activation
# - Dependency installation
# - Proper Python path configuration
```

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS (requires python3-tk package):
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Linux/WSL users MUST also install:
sudo apt-get install python3-tk  # For tkinter support
```

### Individual Tools (Direct Launch)
```bash
# Media downloader
python src/media_download_app.py

# Reel tracker (modular entry point)
python src/reel_tracker_modular.py

# Snippet remixer (modular entry point) 
python src/snippet_remixer_modular.py
# Note: src/snippet_remixer.py also exists but use modular version

# Random slideshow (package main)
python src/random_slideshow/main.py

# Release calendar (modular entry point) - requires PyQt6
python src/release_calendar_modular.py

# Video caption generator (no modular wrapper yet)
python -m src.video_caption_generator.main_app

# Standalone tools
python tools/slideshow_editor.py
python tools/xyimagescaler.py
```

## Architecture Overview

### Central Process Orchestration
- **`launcher.py`**: Central hub managing all applications with unified logging
  - Uses tkinter for GUI interface with tabbed layout
  - Launches each tool as independent subprocess
  - Fallback to hardcoded paths if core module import fails
  - Real-time log aggregation with timestamps
- **`start_launcher.bat`**: Windows-specific launcher wrapper
  - Automatically creates/activates virtual environment
  - Installs dependencies from requirements.txt
  - Handles Python path configuration for Windows
- **Process Management**: Independent processes with graceful termination on exit

### Actual File Structure (Current State)
```
bedrot-media-suite/
├── launcher.py                    # Main GUI launcher
├── start_launcher.bat             # Windows batch launcher
├── requirements.txt               # Python dependencies
├── bedrot_media_suite_function_registry.json  # Complete function registry (CHECK BEFORE CODING!)
├── .env                          # Environment configuration (user-specific)
├── .env.example                  # Template for environment variables
│
├── config/                       # Primary configuration directory
│   ├── backups/                  # Automatic config backups
│   ├── calendar_data.json       # Release calendar data
│   ├── combined_random_config.json
│   ├── config.json              # Slideshow editor settings
│   ├── random_config.json
│   ├── reel_tracker_config.json
│   ├── release_calendar_config.json
│   ├── slideshow_presets.json
│   ├── video_caption_generator_config.json
│   ├── video_remixer_settings.json
│   └── yt_downloader_gui_settings.json
│
├── src/                          # Source code directory
│   ├── core/                     # Centralized utilities (partially implemented)
│   │   ├── __init__.py
│   │   ├── config_manager.py    # Configuration management
│   │   ├── env_loader.py        # Environment variable loading
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── health_check.py      # System health checks
│   │   ├── logger.py            # Logging utilities
│   │   ├── moviepy_utils.py     # MoviePy helpers
│   │   ├── path_utils.py        # Path resolution utilities
│   │   ├── safe_print.py        # Unicode-safe printing
│   │   └── thread_safety.py     # Thread safety utilities
│   │
│   ├── media_download_app.py    # Standalone media downloader
│   ├── snippet_remixer.py       # Legacy remixer (use modular version)
│   ├── snippet_remixer_modular.py  # Modular entry point
│   ├── reel_tracker_modular.py     # Modular entry point
│   ├── release_calendar_modular.py # Modular entry point
│   │
│   ├── snippet_remixer/         # Remixer package
│   │   ├── main.py              # Package main
│   │   ├── main_app.py          # GUI application
│   │   ├── config_manager.py    # Module-specific config
│   │   ├── video_processor.py   # Core processing logic
│   │   ├── processing_worker.py # Background workers
│   │   └── logs/                # Processing logs
│   │
│   ├── random_slideshow/        # Slideshow generator package
│   │   ├── main.py              # Primary entry point
│   │   ├── main_app.py          # Full GUI application
│   │   ├── main_app_simple.py   # Simplified version
│   │   ├── config/              # Module config (duplicates!)
│   │   └── IWARY/               # Sample images
│   │
│   ├── reel_tracker/            # Content tracking package
│   │   ├── main_app.py          # PyQt5 application
│   │   ├── config_manager.py    # Advanced config with versioning
│   │   └── backup_manager.py    # Auto-backup functionality
│   │
│   ├── release_calendar/        # Release management package
│   │   ├── main_app.py          # PyQt6 application
│   │   ├── visual_calendar.py   # Calendar widget
│   │   └── data_manager.py      # Data persistence
│   │
│   └── video_caption_generator/ # Caption generation package
│       ├── main_app.py          # Main application
│       ├── config/              # Module-specific config
│       │   └── video_caption_generator_config.json
│       └── video_processor.py   # Video processing
│
├── tools/                       # Standalone utilities
│   ├── slideshow_editor.py     # PyQt5 slideshow editor
│   ├── xyimagescaler.py        # Image scaling utility
│   └── generate_function_registry.py  # Code analysis tool
│
└── docs/                        # Documentation
    ├── architecture/            # Architecture docs
    └── audit-reports/          # Security and quality audits
```

### Configuration Architecture (Reality Check)
- **Partially Centralized**: `src/core/` module exists but not all modules use it
- **Scattered Config Files**: 
  - Main configs in `/config/` directory
  - Some modules have internal `config/` subdirectories
  - Legacy configs in `src/` subdirectories
- **Environment Variables**: `.env` file support through `python-dotenv`
  - Not all modules consistently use env vars
  - Launcher has hardcoded fallbacks
- **No True Version Control**: Only reel_tracker has version history feature

## Key Dependencies

### Essential External Tools
- **FFmpeg/FFprobe**: Video processing backbone (MUST be in PATH or will fail)
- **yt-dlp**: Media download engine (installed via pip)
- **Python 3.x**: Runtime environment (3.8+ recommended)
- **python3-tk**: Required on Linux/WSL (not included in requirements.txt!)

### Python Frameworks (from requirements.txt)
#### GUI Frameworks (VERIFIED USAGE - December 19, 2024)
- **Tkinter**: Used by 3 files
  - `media_download_app.py` - main downloader GUI
  - `snippet_remixer/main_app.py` - modular GUI
  - `snippet_remixer/export_settings_dialog.py` - dialog
  - **WARNING**: Requires `python3-tk` package on Linux/WSL (NOT in requirements.txt!)
- **customtkinter**: In requirements.txt (enhanced tkinter)
- **PyQt5**: Used by 22 files across multiple modules
  - `random_slideshow/*` - all slideshow components
  - `reel_tracker/*` - all reel tracker components  
  - `video_caption_generator/*` - caption generator components
  - `core/health_check.py` - system health checks
- **PyQt6**: Used by 4 files (ONLY release_calendar!)
  - `release_calendar/main_app.py`
  - `release_calendar/visual_calendar.py`
  - `release_calendar/checklist_dialog.py`
  - `release_calendar_modular.py`
  - **WARNING**: Potential conflicts with PyQt5!
- **tkinterdnd2**: Drag-and-drop support

#### Media Processing
- **MoviePy**: High-level video operations
- **Pillow**: Image processing
- **ffmpeg-python**: FFmpeg Python bindings
- **pydub**: Audio manipulation
- **pysrt**: SRT subtitle handling
- **webvtt-py**: WebVTT subtitle support

#### Data Management
- **pandas**: CSV data management (reel tracker)
- **openpyxl**: Excel file support
- **xlsxwriter**: Excel file writing
- **python-dateutil**: Date parsing
- **icalendar**: iCal format support

#### Other Core Dependencies
- **yt-dlp**: YouTube and media downloading
- **python-dotenv**: Environment variable loading
- **requests**: HTTP requests
- **PyYAML**: YAML file support
- **numpy**: Numerical operations
- **SpeechRecognition**: Audio transcription fallback

## Module Overview

### 1. Media Downloader (`src/media_download_app.py`)
**Status**: Standalone, fully functional
**GUI Framework**: Tkinter
**Entry Point**: Direct file execution
**Config**: `config/yt_downloader_gui_settings.json`
**Features**:
- yt-dlp integration for multi-platform downloads
- MP4/MP3 conversion options
- Video trimming and aspect ratio adjustment
- Queue-based batch downloading
- Post-processing with FFmpeg

### 2. Snippet Remixer (`src/snippet_remixer/`)
**Status**: Modular package with legacy file
**GUI Framework**: Tkinter
**Entry Points**: 
- `src/snippet_remixer_modular.py` (RECOMMENDED)
- `src/snippet_remixer.py` (legacy, may have issues)
**Config**: `config/video_remixer_settings.json`
**Features**:
- Random video snippet combination
- BPM-based timing control
- Background processing with progress tracking
- Temporary file management in `remixer_temp_snippets/`
- Worker thread architecture for non-blocking UI

### 3. Random Slideshow Generator (`src/random_slideshow/`)
**Status**: Modular package with multiple entry points
**GUI Framework**: PyQt5
**Entry Points**:
- `src/random_slideshow/main.py` (PRIMARY)
- `src/random_slideshow/main_app.py` (full GUI)
- `src/random_slideshow/main_app_simple.py` (simplified version)
**Config**: Multiple!
- `config/combined_random_config.json` (main)
- `config/random_config.json` (legacy)
- `src/random_slideshow/config/slideshow_presets.json` (presets)
**Features**:
- Continuous automated slideshow generation
- Batch processing capabilities
- Preset management system
- Resource management for large image sets
- QThread-based background processing

### 4. Reel Tracker (`src/reel_tracker/`)
**Status**: Fully modular with advanced features
**GUI Framework**: PyQt5
**Entry Point**: `src/reel_tracker_modular.py`
**Config**: `config/reel_tracker_config.json` (with version history!)
**Features**:
- CSV-based content tracking
- Advanced configuration with audit trails
- Automatic backup system
- Bulk editing capabilities
- Media randomization
- Custom metadata fields
- File organization tools

### 5. Release Calendar (`src/release_calendar/`)
**Status**: Fully modular, ported from separate project
**GUI Framework**: PyQt6 (WARNING: Different from other modules!)
**Entry Point**: `src/release_calendar_modular.py`
**Config**: 
- `config/release_calendar_config.json` (settings)
- `config/calendar_data.json` (data storage)
**Features**:
- Visual drag-and-drop calendar interface
- Multi-artist release scheduling
- 9+ deliverable checklist per release
- Waterfall release strategy (8 singles, 1 EP, 1 album per artist/year)
- Excel and iCal export
- Automatic conflict detection
- Friday release day highlighting
- Progress tracking with color coding

### 6. Video Caption Generator (`src/video_caption_generator/`)
**Status**: Modular package, no modular wrapper yet
**GUI Framework**: Unknown (likely Tkinter or PyQt5)
**Entry Point**: `python -m src.video_caption_generator.main_app`
**Config**: 
- `config/video_caption_generator_config.json`
- `src/video_caption_generator/config/video_caption_generator_config.json` (duplicate!)
**Features**:
- AI-powered caption generation
- Live preview widget
- Font management system
- Audio extraction and transcription
- Multiple export formats
- Color wheel for styling
- Worker threads for processing

## Critical Coding Standards

### ASCII-Only Policy (MANDATORY)
- **NEVER use emoji characters** (❌, ✅, 🔄, etc.) in any code
- **ALWAYS use ASCII-only text** for all output, logs, and UI elements
- **Use bracketed prefixes instead**:
  - [SUCCESS] instead of ✅
  - [ERROR] instead of ❌  
  - [WARNING] instead of ⚠️
  - [INFO] instead of ℹ️
  - [BACKUP] instead of 🛡️
- This prevents Windows encoding errors (`charmap codec can't encode`)
- All console output MUST be Windows-compatible ASCII

## Development Guidelines

### Understanding the Modularization Pattern
The codebase is in transition between monolithic and modular architecture:

#### Current Patterns:
1. **Modular Wrapper Pattern** (`*_modular.py` files):
   - Thin wrapper that imports from package
   - Examples: `reel_tracker_modular.py`, `snippet_remixer_modular.py`
   
2. **Package Main Pattern** (package with `main.py`):
   - Package directory with internal `main.py`
   - Example: `random_slideshow/main.py`
   
3. **Standalone Pattern** (single file):
   - Self-contained single file application
   - Example: `media_download_app.py`

#### Ideal Package Structure (from MODULARIZATION_GUIDELINES.md):
```
package_name/
├── __init__.py           # Package exports and lazy imports
├── main.py              # Entry point (if __name__ == "__main__")
├── main_app.py          # Main application/GUI class
├── config_manager.py    # Configuration handling
├── core_logic.py        # Core business logic  
├── worker_threads.py    # Background processing
├── dialogs.py           # UI dialogs and forms
├── utils.py             # Utility functions
└── README.md            # Module documentation
```

### Configuration Management (Inconsistent!)
Different modules use different approaches:

#### Basic Pattern (most modules):
```python
import json
config_file = "config/module_config.json"
with open(config_file, 'r') as f:
    config = json.load(f)
```

#### Advanced Pattern (reel_tracker):
```python
class ConfigManager:
    def __init__(self):
        self.config_history = []
        self.audit_trail = []
        # Version tracking, validation, etc.
```

#### Core Pattern (when it works):
```python
from core import get_config_manager
config = get_config_manager().get_config('module_name')
```

### Thread Patterns by Framework

#### PyQt5/6 Threading:
```python
from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    
    def run(self):
        # Long-running task
        pass
```

#### Tkinter Threading:
```python
import threading

def background_task():
    # Long-running task
    root.after(0, update_gui)  # Schedule GUI update

thread = threading.Thread(target=background_task)
thread.daemon = True
thread.start()
```

### Known Issues and Workarounds

#### Issue 1: Launcher Uses Legacy Snippet Remixer
**Status**: VERIFIED - This is intentional, not a bug!
**Current Code** (Line 49):
```python
SCRIPT_2_PATH = get_script_path('snippet_remixer', 'src/snippet_remixer.py')  # Uses 695-line legacy file
```
**Note**: The launcher deliberately uses the standalone `snippet_remixer.py` (695 lines), NOT the modular wrapper (18 lines). Both files exist and work.

#### Issue 2: Config File Duplication
**Problem**: Multiple config files for same module
**Verified Duplicates**:
- `config/combined_random_config.json` (primary)
- `src/combined_random_config.json` (duplicate)
- `src/random_slideshow/combined_random_config.json` (another duplicate)
- `config/reel_tracker_config.json` vs `src/config/reel_tracker_config.json`
- `config/video_caption_generator_config.json` vs `src/video_caption_generator/config/video_caption_generator_config.json`
- `config/slideshow_presets.json` vs `src/random_slideshow/config/slideshow_presets.json`

#### Issue 3: Missing Dependencies
**Problem**: tkinter not in requirements.txt
**Solution for Linux/WSL**:
```bash
sudo apt-get install python3-tk
```

#### Issue 4: PyQt Version Conflicts
**Problem**: Both PyQt5 and PyQt6 installed
**Mitigation**: Modules explicitly import their version:
```python
# For PyQt5 modules
from PyQt5.QtWidgets import QApplication

# For PyQt6 modules (only release_calendar)
from PyQt6.QtWidgets import QApplication
```

## Environment Variables

### Configuration via .env File
The project supports environment variables through `.env` file (see `.env.example`):

```bash
# Core paths (rarely need changing)
SLIDESHOW_CONFIG_DIR=config
SLIDESHOW_SRC_DIR=src
SLIDESHOW_TOOLS_DIR=tools

# Script paths (for launcher)
SLIDESHOW_MEDIA_DOWNLOAD_SCRIPT=src/media_download_app.py
SLIDESHOW_SNIPPET_REMIXER_SCRIPT=src/snippet_remixer.py  # NOTE: Uses LEGACY file, not modular wrapper!
SLIDESHOW_RANDOM_SLIDESHOW_SCRIPT=src/random_slideshow/main.py
SLIDESHOW_REEL_TRACKER_SCRIPT=src/reel_tracker_modular.py
SLIDESHOW_VIDEO_CAPTION_GENERATOR_SCRIPT=src/video_caption_generator/main_app.py
SLIDESHOW_RELEASE_CALENDAR_SCRIPT=src/release_calendar_modular.py

# Default directories
SLIDESHOW_DEFAULT_OUTPUT_DIR=~/Videos/RandomSlideshows
SLIDESHOW_DEFAULT_DOWNLOADS_DIR=~/Videos/Downloads

# Processing settings
SLIDESHOW_MAX_PROCESSES=4
SLIDESHOW_DEFAULT_QUALITY=720p
SLIDESHOW_DEFAULT_ASPECT_RATIO=16:9

# Security
SLIDESHOW_ENABLE_PATH_VALIDATION=true
SLIDESHOW_RESTRICT_TO_PROJECT=true
```

**NOTE**: Not all modules respect these variables. Many have hardcoded paths.

## Common Patterns and Utilities

### Safe Print Utility (Unicode handling)
```python
from src.core.safe_print import safe_print
safe_print("Text with emojis 🎬")  # Won't crash on encoding issues
```

### Path Resolution (when core module works)
```python
from core.path_utils import get_path_resolver
resolver = get_path_resolver()
config_path = resolver.resolve_config_path('my_config.json')
```

### Config Access (inconsistent usage)
```python
# Method 1: Direct JSON load (most common)
import json
with open('config/app_config.json') as f:
    config = json.load(f)

# Method 2: Core module (when available)
from core import get_config_manager
config = get_config_manager().get_config('app_name')

# Method 3: Module-specific manager
from .config_manager import ConfigManager
config = ConfigManager()
```

## Testing and Debugging

### Common Issues and Solutions

1. **"No module named tkinter"**
   - Linux/WSL: `sudo apt-get install python3-tk`
   - Windows: Reinstall Python with tkinter option

2. **FFmpeg not found**
   - Ensure FFmpeg is in PATH
   - Windows: Add FFmpeg bin directory to System PATH
   - Linux: `sudo apt install ffmpeg`

3. **PyQt5/PyQt6 conflicts**
   - Run modules through launcher (isolates processes)
   - Or use separate virtual environments

4. **Config file not found**
   - Check multiple locations (config/, src/, src/module/)
   - Create missing config from example if available

5. **Module import errors**
   - Run from project root directory
   - Use modular entry points when available
   - Check virtual environment activation

### Debug Mode Tips
```python
# Enable verbose logging in modules that support it
import logging
logging.basicConfig(level=logging.DEBUG)

# Check which config file is being loaded
print(f"Loading config from: {config_file}")

# Verify FFmpeg availability
import subprocess
subprocess.run(['ffmpeg', '-version'], check=True)
```

## Performance Optimization

### Memory Management
- MoviePy clips should be explicitly closed: `clip.close()`
- Large image sets: Use batch processing in random_slideshow
- Video processing: Process in chunks, not entire files

### Threading Best Practices
- PyQt: Always use QThread, never Python threading
- Tkinter: Use threading.Thread with root.after() for GUI updates
- Always set daemon=True for background threads

### File I/O
- Use context managers for file operations
- Implement cleanup in finally blocks
- Delete temporary files after processing

## Security Considerations

### Path Validation
- All user-provided paths should be validated
- Prevent directory traversal attacks
- Restrict operations to project directory when possible

### Configuration Security
- Never store API keys in config files (use .env)
- Validate all configuration values on load
- Implement safe defaults for missing configs

### Process Isolation
- Each tool runs in separate process via launcher
- Process crashes don't affect other tools
- Graceful shutdown on launcher exit

## Future Improvements Needed

1. **Standardize entry points** - All modules should follow same pattern
2. **Centralize configurations** - Move all configs to /config/
3. **Fix launcher fallback paths** - Update hardcoded paths
4. **Complete core module adoption** - All modules should use core utilities
5. **Add proper testing** - pytest suite with mocked dependencies
6. **Document API keys** - ElevenLabs and other service integrations
7. **Resolve PyQt conflicts** - Consider standardizing on one version
8. **Clean up legacy files** - Remove duplicate and unused files
9. **Implement proper logging** - Centralized logging system
10. **Add CI/CD pipeline** - Automated testing and deployment