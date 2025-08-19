# CSV Column Migration Guide

## Overview

The CSV Column Migration system provides a safe, repeatable method to add new columns to the Reel Tracker CSV and backfill data for existing rows. The system is designed to be idempotent (can run multiple times safely) and non-destructive (creates backups before modifications).

## Migration Completed: Aspect Ratio Column

### What Was Added
- **Column Name**: `Aspect Ratio`
- **Position**: Between `Caption` and `FilePath` columns
- **Values**: Canonical aspect ratios like `9:16`, `16:9`, `1:1`, `4:5`, etc.
- **Default**: `unknown` for rows that cannot be determined

### Migration Results
- **Total Rows**: 686
- **Successfully Backfilled**: 686 (100%)
- **Aspect Ratio Distribution**: All rows identified as `9:16` (vertical format for reels)
- **Backup Created**: `E:\VIDEOS\RELEASE CONTENT\backups\bedrot-reel-tracker_backup_20250819_045618.csv`

## How to Use the Migration System

### 1. For Aspect Ratio Migration (Already Applied)

The aspect ratio migration has already been applied to production. To verify or re-run:

```bash
# Check current state (dry run)
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-media-suite"
.\venv\Scripts\python.exe tools\apply_aspect_ratio_migration.py --dry-run

# Apply migration (already done)
.\venv\Scripts\python.exe tools\apply_aspect_ratio_migration.py
```

### 2. For Adding New Columns in the Future

The migration framework is generic and reusable. To add a new column:

#### Step 1: Create a Backfill Function (Optional)

If you want to populate existing rows with intelligent values:

```python
def backfill_new_column(row: pd.Series) -> str:
    """
    Custom backfill logic for your new column.
    
    Args:
        row: A pandas Series representing one row of data
        
    Returns:
        The value to populate for this row
    """
    # Priority 1: Check if data exists in other columns
    if 'SomeColumn' in row and row['SomeColumn']:
        return derive_value_from(row['SomeColumn'])
    
    # Priority 2: Use platform/type hints
    if 'Reel Type' in row and 'Tutorial' in row['Reel Type']:
        return 'educational'
    
    # Default fallback
    return 'unknown'
```

#### Step 2: Run the Migration

```python
from csv_column_migrator import ColumnMigrator

# Initialize migrator
migrator = ColumnMigrator("path/to/your.csv")

# Add column with backfill
result = migrator.add_column(
    column_name="Your Column Name",
    default_value="default_value",
    backfill_func=backfill_new_column,  # Optional
    create_backup=True
)

# Check results
print(f"Rows updated: {result.rows_updated}")
print(f"Success rate: {(result.rows_updated / result.total_rows) * 100:.1f}%")
```

### 3. Command-Line Usage

The migration tool can also be used from command line:

```bash
# Add aspect_ratio column (default behavior)
python tools/csv_column_migrator.py "E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv"

# Add custom column
python tools/csv_column_migrator.py "path/to/file.csv" --column "New Column"

# Dry run (preview without saving)
python tools/csv_column_migrator.py "path/to/file.csv" --dry-run

# Overwrite existing column values
python tools/csv_column_migrator.py "path/to/file.csv" --overwrite

# Skip backup creation
python tools/csv_column_migrator.py "path/to/file.csv" --no-backup
```

## Backfill Logic for Aspect Ratio

The aspect ratio backfill uses a priority-based approach:

### Priority Order

1. **Explicit Width/Height Columns**
   - Looks for columns named: `width`, `height`, `video_width`, `video_height`, etc.
   - Calculates and simplifies ratio (e.g., 1080x1920 → 9:16)

2. **Resolution String Parsing**
   - Searches columns: `resolution`, `dimensions`, `size`, `metadata`
   - Parses patterns like: `1920x1080`, `1920X1080`, `1920×1080`
   - Also checks filenames for resolution hints

3. **Platform/Format Hints**
   - Keywords in `Reel Type`, `Platform`, `Caption`, `Clip Filename`
   - Mappings:
     - `reel`, `shorts`, `tiktok`, `story` → `9:16` (vertical)
     - `youtube`, `landscape` → `16:9` (horizontal)
     - `square`, `post` → `1:1` (square)
     - `feed` → `4:5` (portrait)

4. **Default Fallback**
   - Returns `unknown` if no hints found

### Canonical Aspect Ratios

The system recognizes and standardizes to these canonical ratios:

- `9:16` - Vertical (Reels, Shorts, TikTok)
- `16:9` - Horizontal (YouTube, landscape)
- `1:1` - Square (Instagram posts)
- `4:5` - Portrait (Instagram feed)
- `5:4` - Landscape alternative
- `3:4` - Portrait alternative
- `4:3` - Traditional TV
- `21:9` - Ultrawide
- `2:3` - Portrait

## UI Integration

The Reel Tracker UI has been updated to support the aspect_ratio column:

### Changes Made

1. **Column Definition** (`src/reel_tracker/main_app.py`)
   - Added `Aspect Ratio` to columns list
   - Positioned between `Caption` and `FilePath`

2. **Dropdown Support**
   - Added aspect_ratio dropdown delegate
   - Predefined values: `9:16`, `16:9`, `1:1`, `4:5`, etc.
   - Users can add custom ratios

3. **Configuration** (`src/reel_tracker/config_manager.py`)
   - Added default aspect_ratio dropdown values
   - Set column width to 90 pixels

### Using in Reel Tracker

1. Launch Reel Tracker application
2. The Aspect Ratio column will appear automatically
3. Click on any cell in the column to see dropdown options
4. Select from predefined ratios or type custom value
5. New values are automatically saved to configuration

## Safety Features

### Idempotency
- Running the migration multiple times doesn't duplicate or corrupt data
- Existing values are preserved unless `overwrite_existing=True`
- Empty values can be backfilled without affecting populated ones

### Non-Destructive
- Always creates timestamped backups before modification
- Original file preserved in backups folder
- Can restore from backup if needed

### Validation
- Validates data before writing
- Prevents empty CSV writes
- Reports detailed statistics and errors

### Atomic Operations
- Uses temporary files during write
- Only replaces original after successful write
- Prevents partial writes on failure

## Restoring from Backup

If you need to restore the original CSV:

```bash
# Windows Command Prompt
copy "E:\VIDEOS\RELEASE CONTENT\backups\bedrot-reel-tracker_backup_20250819_045618.csv" "E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv"

# Or from Python
import shutil
shutil.copy2(
    r"E:\VIDEOS\RELEASE CONTENT\backups\bedrot-reel-tracker_backup_20250819_045618.csv",
    r"E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv"
)
```

## Troubleshooting

### Column Already Exists
- Migration will skip adding the column
- Will only backfill empty values
- Use `--overwrite` flag to replace all values

### Encoding Issues
- Tool automatically handles UTF-8 with BOM
- Falls back to latin-1 if needed
- Output always saved as UTF-8 with BOM

### Path Issues
- Use raw strings for Windows paths: `r"E:\path\to\file.csv"`
- Tool automatically detects platform (Windows/Linux)

### Missing Dependencies
- Requires: pandas, numpy, pathlib
- Install: `pip install pandas numpy`

## Future Enhancements

Potential columns to add using this framework:

1. **Duration** - Video length in seconds
2. **File Size** - Size in MB
3. **Resolution** - Explicit width x height
4. **Frame Rate** - FPS value
5. **Codec** - Video encoding format
6. **Creation Date** - When file was created
7. **Tags** - Comma-separated keywords
8. **Platform** - Target platform for reel
9. **Status** - Draft, Published, Archived
10. **Performance** - Views, likes, engagement

Each can be added using the same migration framework with appropriate backfill logic.

## Code Architecture

### Core Components

1. **ColumnMigrator** (`tools/csv_column_migrator.py`)
   - Generic CSV column addition framework
   - Handles backups, validation, atomic writes
   - Platform-agnostic path handling

2. **AspectRatioMigrator** (`tools/csv_column_migrator.py`)
   - Specialized backfill logic for aspect ratios
   - Resolution parsing and simplification
   - Platform hint detection

3. **Migration Scripts**
   - `run_aspect_ratio_migration.py` - Interactive version
   - `apply_aspect_ratio_migration.py` - Non-interactive version

4. **UI Integration** (`src/reel_tracker/`)
   - `main_app.py` - Column display and editing
   - `config_manager.py` - Dropdown value management

## Summary

The CSV Column Migration system successfully added the aspect_ratio column to 686 rows with 100% backfill success rate. The framework is now available for adding future columns with the same safety and reliability guarantees. All changes are tracked, reversible, and maintain data integrity throughout the process.