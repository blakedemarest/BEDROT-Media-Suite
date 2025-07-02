# CLAUDE.md - Reel Tracker Module

This file provides guidance to Claude Code when working with the reel tracker module.

## Module Overview

The Reel Tracker is a PyQt5-based application for managing content production with CSV-based data storage. It features advanced configuration management with version history, dynamic dropdown values, and sophisticated file organization capabilities.

**Current Version**: 3.1.0

## Architecture

### Entry Points
- **Via Launcher**: `src/reel_tracker_modular.py`
- **Direct Import**: `from reel_tracker.main_app import main`
- **Process Type**: Independent subprocess with real-time logging

### Module Structure

```
reel_tracker/
├── __init__.py                  # Package exports, version info
├── main_app.py                 # Main PyQt5 application (ReelTrackerApp)
├── config_manager.py           # Advanced config with version history
├── reel_dialog.py              # Add/edit reel dialog
├── file_organizer.py           # File organization engine
├── media_randomizer.py         # Media scanning and randomization
├── bulk_edit_dialog.py         # Bulk editing interface
├── default_metadata_dialog.py  # Default metadata settings
├── file_organization_dialog.py # File organization settings
├── custom_item_manager.py      # Dropdown value management
└── utils.py                   # Utilities (safe_print)
```

## Configuration System

### Advanced Features
- **Version History**: Complete audit trail of all config changes
- **Dynamic Dropdowns**: User-added values automatically saved
- **Multi-tier Structure**: Supports complex nested configurations
- **Auto-save**: Changes persist immediately

### Configuration Schema
```json
{
  "dropdown_values": {
    "Persona": ["Persona1", "Persona2", ...],
    "Release": ["Release1", "Release2", ...],
    "Reel Type": ["Type1", "Type2", ...]
  },
  "last_csv_path": "path/to/last.csv",
  "window_settings": {
    "geometry": "...",
    "splitter_state": "..."
  },
  "app_settings": {
    "auto_load_csv": true,
    "confirm_delete": true
  },
  "default_metadata": {
    "persona": "",
    "release": "",
    "reel_type": ""
  },
  "file_organization": {
    "master_export_folder": "",
    "create_persona_release_folders": true,
    "safe_mode": true
  },
  "version_history": [...]
}
```

## Core Features

### 1. CSV Data Management
- **Columns**: Reel ID, Persona, Release, Reel Type, Clip Filename, Caption, FilePath
- **pandas Integration**: Robust CSV handling with automatic column management
- **Auto-save**: Every change immediately persisted to CSV
- **Drag & Drop**: Drop media files directly into table

### 2. File Organization System

**FileOrganizer** class provides:
```python
# Naming convention: PERSONA_RELEASE_REELID.extension
# Folder structure: master_folder/PERSONA_RELEASE/
```

Features:
- **Duplicate Detection**: Smart pattern matching to avoid overwrites
- **Safe Mode**: Copy vs move operations
- **Batch Processing**: Progress callbacks with CSV updates
- **Path Sanitization**: Removes invalid characters
- **Preview Mode**: See changes before execution

### 3. Dynamic Dropdown Management

Dropdowns are editable ComboBoxes that:
- Save new values automatically to config
- Maintain sorted lists
- Share values across all rows
- Persist between sessions

### 4. Release Goal Tracking

Visual progress toward 124 reel goal:
- Progress bar with percentage
- Color coding (red → yellow → green)
- Celebration animation on achievement
- Per-release tracking

## Dependencies

### Python Libraries
- **PyQt5**: Primary GUI framework
- **pandas**: CSV data manipulation
- **Standard Library**: pathlib, json, datetime, threading, etc.

### No External Tools Required
Unlike other modules, doesn't require FFmpeg or other external tools.

## Key Classes and Patterns

### ReelTrackerApp (Main Window)
```python
class ReelTrackerApp(QMainWindow):
    def __init__(self):
        # Initialize UI
        # Load configuration
        # Setup table with custom delegates
        # Connect signals
```

### Thread-Safe Media Scanning
```python
class MediaRandomizerThread(QThread):
    progress_update = pyqtSignal(int, int)
    scan_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
```

### Custom Delegates for Dropdowns
```python
class ComboBoxDelegate(QStyledItemDelegate):
    # Provides editable dropdowns in table cells
    # Auto-saves new values to config
```

## Error Handling

Comprehensive error handling throughout:
1. **File Operations**: Try-except blocks with user notifications
2. **CSV Operations**: Graceful handling of malformed data
3. **Configuration**: Fallback to defaults on corruption
4. **Unicode Safety**: All console output uses `safe_print()`

## Integration with Core System

When core module is available:
```python
try:
    from core import resolve_config_path
    config_path = resolve_config_path('reel_tracker_config.json')
except ImportError:
    # Fallback to local config handling
```

## File Organization Workflow

1. **Setup**: Configure master export folder
2. **Select Rows**: Choose reels to organize
3. **Preview**: See proposed changes
4. **Execute**: Copy/move files with progress tracking
5. **Update**: CSV automatically updated with new paths

## Common Operations

### Adding New Reel
1. Click "Add New Reel"
2. Select media file (auto-fills metadata)
3. Edit fields as needed
4. Confirm to add to table

### Bulk Editing
1. Select multiple rows
2. Click "Edit Selected"
3. Choose "Bulk Edit"
4. Set values to apply to all

### Random Reel Discovery
1. Click "Random Reel"
2. Select folder to scan
3. Choose from discovered media files
4. Auto-generates reel with metadata

## Development Guidelines

1. **Unicode Safety**: Always use `safe_print()` for console output
2. **Thread Safety**: Use Qt signals for cross-thread communication
3. **Configuration Changes**: All changes tracked in version history
4. **CSV Integrity**: Never modify CSV structure without migration
5. **Path Handling**: Use pathlib for cross-platform compatibility

## Testing

To test the module:
1. Run standalone: `python src/reel_tracker_modular.py`
2. Create test CSV with sample data
3. Test all CRUD operations
4. Verify file organization with test files
5. Check configuration persistence

## Future Enhancements

Potential improvements identified:
1. Export to multiple formats (JSON, Excel)
2. Advanced filtering and search
3. Thumbnail previews in table
4. Batch caption editing
5. Integration with video processing modules