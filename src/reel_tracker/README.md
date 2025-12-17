# Reel Tracker - Modular Application

This folder contains the modular version of the Reel Tracker application, broken down into focused, reusable components.

## Module Structure

```
reel_tracker/
├── __init__.py              # Package initialization and exports
├── README.md               # This documentation file
├── config_manager.py       # Configuration management
├── main_app.py            # Main application window and core functionality
├── media_randomizer.py    # Media file randomization and selection
├── reel_dialog.py         # Reel entry and editing dialogs
└── utils.py               # Utility functions
```

## Modules Overview

### `config_manager.py`
- **Purpose**: Handles all configuration management
- **Features**: 
  - JSON-based configuration storage
  - Dropdown values persistence
  - Last CSV file path management
  - Application settings management
- **Main Class**: `ConfigManager`

### `media_randomizer.py`
- **Purpose**: Media file scanning and randomization
- **Features**:
  - Background file scanning with threading
  - Video and image file detection
  - User interface for folder selection
  - File type filtering and randomization
- **Main Classes**: `MediaRandomizerWorker`, `MediaRandomizerDialog`

### `reel_dialog.py`
- **Purpose**: Data entry and editing interface
- **Features**:
  - Comprehensive reel data entry forms
  - File browsing and media selection
  - Auto-generation of captions and templates
  - Integration with media randomizer
- **Main Class**: `ReelEntryDialog`

### `main_app.py`
- **Purpose**: Main application window and core functionality
- **Features**:
  - CSV import/export functionality
  - Table management with dropdown delegates
  - Drag-and-drop file handling
  - Menu system and user interface
- **Main Classes**: `ReelTrackerApp`, `DropdownDelegate`

### `utils.py`
- **Purpose**: Common utility functions
- **Features**:
  - Safe console output for Unicode handling
  - Shared helper functions
- **Main Functions**: `safe_print()`

## Usage

### Running the Application
```python
# From the parent directory
python src/reel_tracker_modular.py

# Or import directly
from reel_tracker import ReelTrackerApp
app = ReelTrackerApp()
app.show()
```

### Using Individual Components
```python
# Configuration management
from reel_tracker import ConfigManager
config = ConfigManager()

# Media randomization
from reel_tracker import MediaRandomizerDialog
randomizer = MediaRandomizerDialog()

# Reel entry dialog
from reel_tracker import ReelEntryDialog
dialog = ReelEntryDialog()
```

## Benefits of Modular Design

1. **Separation of Concerns**: Each module has a clear, focused responsibility
2. **Reusability**: Components can be used independently or in other projects
3. **Maintainability**: Easier to debug, test, and modify individual components
4. **Scalability**: New features can be added as separate modules
5. **Code Organization**: Logical grouping of related functionality

## Configuration

The application uses `config/reel_tracker_config.json` for persistent settings:

- **Dropdown Values**: Persona, Release, and Reel Type options
- **Last CSV Path**: Auto-loading of recent files
- **Application Settings**: User preferences and behavior

## Dependencies

- PyQt5: GUI framework
- pandas: CSV data manipulation
- pathlib: File path operations
- Standard library modules: os, json, datetime, random, math

## Error Handling

All modules include comprehensive error handling:
- Graceful degradation when components fail
- Safe Unicode output for Windows compatibility
- Fallback behaviors for missing dependencies
- User-friendly error messages

## Future Enhancements

The modular structure makes it easy to add:
- Plugin system for custom functionality
- Additional data export formats
- Enhanced media processing capabilities
- Integration with external APIs
- Advanced filtering and search features