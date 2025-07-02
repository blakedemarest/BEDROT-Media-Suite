# CLAUDE.md - Source Directory Architecture

This file provides guidance to Claude Code when working with the modular architecture of the Bedrot Productions Media Tool Suite.

## System Architecture Overview

### Launch Flow
```
start_launcher.bat (Windows Entry Point)
    ├── Creates/activates virtual environment
    ├── Installs dependencies
    └── Launches launcher.py
        └── launcher.py (Process Orchestrator)
            ├── media_download_app.py (Tkinter)
            ├── reel_tracker_modular.py → reel_tracker package (PyQt5)
            ├── snippet_remixer_modular.py → snippet_remixer package (Tkinter)
            └── random_slideshow/main.py (PyQt5)
```

### Process Management Architecture

The launcher implements a sophisticated process management system:

1. **Process Isolation**: Each module runs as an independent subprocess
   - Windows: Uses `CREATE_NEW_PROCESS_GROUP` for process tree management
   - Unix/Linux: Uses `start_new_session=True` for process isolation

2. **Real-time Logging**:
   - Captures stdout/stderr from all subprocesses
   - Aggregates output with timestamps `[YYYY-MM-DD HH:MM:SS]`
   - Thread-safe GUI updates using `root.after()`

3. **Graceful Termination**:
   - Clean shutdown with `terminate()` followed by `kill()` if needed
   - User confirmation before terminating running processes

### Core Infrastructure (`core/`)

Centralized utilities available to all modules:

```python
from core import get_config_manager, resolve_path, resolve_config_path
from core.env_loader import get_env_var, load_environment
from core.path_utils import validate_path, check_path_security
```

Key components:
- **config_manager.py**: Centralized JSON configuration with validation
- **env_loader.py**: Environment variable handling with .env support
- **path_utils.py**: Secure path resolution and validation

### Module Integration Patterns

#### 1. Direct Applications
```python
# media_download_app.py pattern
if __name__ == "__main__":
    root = tk.Tk()
    app = MediaDownloadApp(root)
    root.mainloop()
```

#### 2. Modular Package Pattern
```python
# snippet_remixer_modular.py pattern
from snippet_remixer.main_app import main
if __name__ == "__main__":
    main()
```

#### 3. PyQt5 Applications
```python
# random_slideshow/main.py pattern
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
```

### Configuration Hierarchy

```
Environment Variables (.env)
    ↓
Core Configuration (core/config_manager.py)
    ↓
Module Configuration (config/*.json)
    ↓
Runtime Settings (in-memory)
```

### Logging Standards

All modules should follow these logging patterns:
```python
# Module identification in logs
print(f"[{module_name}] Starting operation...")

# Error reporting
print(f"[{module_name}] ERROR: {error_message}")

# Progress updates
print(f"[{module_name}] Processing {current}/{total}...")
```

### Module Communication

Modules communicate with the launcher through:
- **stdout/stderr**: Primary communication channel
- **Exit codes**: Success (0) or failure (non-zero)
- **Shared configuration**: Via centralized config files
- **No direct IPC**: Modules are independent processes

### Security Considerations

- **Path Validation**: All file operations use validated paths
- **Process Isolation**: Crashes in one module don't affect others
- **Configuration Security**: Local-only config files, no network transmission
- **Resource Cleanup**: Proper cleanup in finally blocks

### Development Guidelines

1. **Consistent Entry Points**: All modules should have clear entry points
2. **Error Handling**: Comprehensive try-except blocks with user-friendly messages
3. **Unicode Safety**: Use `safe_print()` for cross-platform compatibility
4. **Thread Safety**: GUI updates must be scheduled on the main thread
5. **Resource Management**: Clean up resources (files, processes) on exit

### Testing Module Integration

To test a module's launcher integration:
1. Run `python launcher.py` or double-click `start_launcher.bat`
2. Click the tab for your module
3. Click "Run" to start the module
4. Verify logging appears in the central log area
5. Test "Stop" button for graceful shutdown
6. Check "Stop All & Exit" for clean termination

### Module Dependencies Matrix

| Module | GUI Framework | External Tools | Key Python Deps |
|--------|--------------|----------------|-----------------|
| media_download_app | Tkinter | yt-dlp, FFmpeg | Standard library |
| reel_tracker | PyQt5 | None | pandas |
| snippet_remixer | Tkinter | FFmpeg, FFprobe | Standard library |
| random_slideshow | PyQt5 | FFmpeg | MoviePy, Pillow |

### Adding New Modules

To add a new module to the launcher:
1. Create module following the modular package pattern
2. Add entry in `launcher.py` with appropriate script path
3. Create new tab in the launcher GUI
4. Ensure proper logging with module identification
5. Test process lifecycle (start, run, stop)
6. Update this documentation