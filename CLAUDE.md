# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Bedrot Productions Media Tool Suite** is a sophisticated Python-based collection of multimedia processing tools designed for content creation, video downloading, editing, and automated slideshow generation. The suite has evolved from monolithic scripts to a modern modular architecture with centralized process orchestration.

## Quick Start Commands

### Running the Application
```bash
# Main entry point - run from project root
python launcher.py

# Alternative Windows entry point <-- this is primarily how this program is opened
start_launcher.bat
```

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Individual Tools (Direct Launch)
```bash
# Media downloader
python src/media_download_app.py

# Reel tracker (modular)
python src/reel_tracker_modular.py

# Snippet remixer (modular)
python src/snippet_remixer_modular.py

# Random slideshow (modular)
python src/random_slideshow/main.py

# Standalone tools
python tools/slideshow_editor.py
python tools/xyimagescaler.py
```

## Architecture Overview

### Central Process Orchestration
- **`launcher.py`**: Central hub managing all applications with unified logging
- **Process Management**: Independent processes for each tool with graceful termination
- **Real-time Logging**: Aggregated stdout/stderr with timestamps from all running tools

### Modular Package Structure
```
src/
├── reel_tracker/          # Advanced CSV-based content tracking
├── snippet_remixer/       # Video remixing with worker threads  
├── random_slideshow/      # Automated slideshow generation
├── media_download_app.py  # yt-dlp based media downloader
└── MODULARIZATION_GUIDELINES.md  # Development standards
```

### Configuration Architecture
- **Centralized Configuration System**: New `src/core/` module with environment variable support
- **Multi-tier Configuration**: From basic JSON to version-tracked audit systems
- **Per-application Settings**: Stored in `config/` directory (configurable via `SLIDESHOW_CONFIG_DIR`)
- **Environment Variables**: Comprehensive .env file support for all paths and settings
- **Advanced Features**: Version history, audit trails, dynamic dropdowns (reel_tracker)
- **Security**: Path validation, extension checking, and directory traversal prevention

## Key Dependencies

### Essential External Tools
- **FFmpeg/FFprobe**: Video processing backbone (must be in PATH)
- **yt-dlp**: Media download engine
- **Python 3.x**: Runtime environment

### Python Frameworks
- **Tkinter**: Basic GUI framework (launcher, media downloader, snippet remixer)
- **PyQt5**: Advanced GUI components (reel tracker, random slideshow, slideshow editor)
- **pandas**: CSV data management (reel tracker)
- **MoviePy**: High-level video operations
- **Pillow**: Image processing

## Development Guidelines

### Modular Package Pattern
Follow the established pattern from `src/MODULARIZATION_GUIDELINES.md`:
```
package_name/
├── __init__.py           # Package exports and lazy imports
├── main_app.py          # Main application/GUI class
├── config_manager.py    # Configuration handling
├── core_logic.py        # Core business logic
├── worker_threads.py    # Background processing
├── dialogs.py           # UI dialogs and forms
├── utils.py             # Utility functions
└── README.md            # Module documentation
```

### Configuration Management Pattern
```python
class ConfigManager:
    def __init__(self, config_file="config/app_config.json"):
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        self.config = self.load_config()
```

### Worker Thread Architecture
Use `QThread` for CPU-intensive operations with progress reporting:
```python
class ProcessingWorker(QThread):
    progress_updated = pyqtSignal(int, int, str)
    operation_completed = pyqtSignal(dict)
```

### Error Handling Standards
- Use `safe_print()` utility for Unicode-safe output
- Implement multi-layer error handling with graceful degradation
- Provide fallback configurations and sensible defaults

## File Organization

### Configuration Files (`config/`)
- `config.json`: Slideshow Editor settings
- `yt_downloader_gui_settings.json`: Media Downloader settings
- `video_remixer_settings.json`: Snippet Remixer settings
- `combined_random_config.json`: Random Slideshow settings
- `reel_tracker_config.json`: Advanced configuration with version history

### Important Development Files
- `ARCHITECTURE_DOCUMENTATION.md`: Comprehensive architecture analysis
- `src/MODULARIZATION_GUIDELINES.md`: Modularization standards and patterns
- `requirements.txt`: Python dependencies (note: some entries have spacing issues)

## Environment Variables

### Key Configuration Variables
```bash
# Project structure (auto-detected if not set)
SLIDESHOW_PROJECT_ROOT=/path/to/slideshow_editor
SLIDESHOW_CONFIG_DIR=config
SLIDESHOW_SRC_DIR=src
SLIDESHOW_TOOLS_DIR=tools

# Default output directories
SLIDESHOW_DEFAULT_OUTPUT_DIR=~/Videos/RandomSlideshows
SLIDESHOW_DEFAULT_DOWNLOADS_DIR=~/Videos/Downloads
SLIDESHOW_DEFAULT_EXPORTS_DIR=~/Videos/Exports

# Application settings
SLIDESHOW_DEFAULT_QUALITY=720p
SLIDESHOW_DEFAULT_ASPECT_RATIO=16:9

# Security settings
SLIDESHOW_ENABLE_PATH_VALIDATION=true
SLIDESHOW_RESTRICT_TO_PROJECT=true
```

### Using Environment Variables
Create a `.env` file in the project root (copy from `.env.example`) to customize paths and settings for your environment.

## Common Patterns

### Centralized Configuration Access
```python
from core import get_config_manager, resolve_path, resolve_config_path
from core.env_loader import get_env_var

# Get configuration manager
config_manager = get_config_manager()

# Resolve paths securely
config_path = resolve_config_path('app_config.json')
output_path = resolve_output_path()

# Get environment variables with fallbacks
quality = get_env_var('SLIDESHOW_DEFAULT_QUALITY', '720p')
```

### Lazy Imports (for Optional Dependencies)
```python
# In __init__.py
def get_main_app():
    """Lazy import to avoid PyQt5 dependency issues."""
    from .main_app import MainApplication
    return MainApplication
```

### Thread-Safe GUI Updates
```python
# Use QThread signals for GUI updates from background threads
self.progress_updated.emit(current, total, message)
```

### Cross-Platform Compatibility
- Centralized path resolution using `pathlib.Path`
- Environment variable support for custom paths
- Security validation for all file operations
- Process management handles both Windows and Unix systems

## Testing Approach

This project does not have a formal test framework configured. When adding tests:
- Test modular packages independently
- Mock external dependencies (FFmpeg, yt-dlp)
- Test configuration loading/saving with temporary files
- Verify UI components with pytest-qt for PyQt5 applications

## Performance Considerations

- **I/O Bound**: Media downloads, file operations
- **CPU Bound**: Video processing, image manipulation
- **Memory Management**: Explicit cleanup of large MoviePy clips
- **Threading**: Background processing for responsive UIs

## Security Notes

- Local file processing only - no network transmission of user data
- Path validation prevents directory traversal
- Process isolation prevents cascading failures
- Configuration files stored locally with secure defaults