# BEDROT Media Suite - Pain Points & Skill Solutions Analysis

> **Date:** 2026-01-08
> **Analysis Scope:** Deep dive into repository structure, architecture documentation, source code patterns, and developer friction points
> **Objective:** Identify 15+ critical pain points that custom Claude Code skills could alleviate

---

## Executive Summary

This analysis identifies **17 extremely serious pain points** discovered through comprehensive code review of the BEDROT Media Suite. Each pain point is documented with:
- Evidence from the codebase
- Impact on developer productivity and reliability
- A concrete skill-based solution using the Claude Code skill builder

These are not generic suggestions—they address **real friction patterns** observed in the 155+ Python files, 9 configuration systems, and multi-framework architecture of this repository.

---

## Pain Point #1: FFmpeg Command Construction Hell

### Evidence
- `src/media_download_app.py:1020-1037` - 17+ lines of conditional FFmpeg format flags
- `src/snippet_remixer/video_processor.py` - Complex filter chain construction
- `src/caption_generator/main_app.py` - libass subtitle filter complexity
- Multiple DEBUG statements throughout for FFmpeg command debugging

### Impact
- **High** - FFmpeg commands are error-prone, platform-specific, and hard to debug
- Developers must memorize arcane FFmpeg syntax for each use case
- Filter chain errors only manifest at runtime, often with cryptic messages
- Cross-platform differences (Windows vs Linux) cause silent failures

### Skill Solution: `ffmpeg-command-builder`

```yaml
---
name: ffmpeg-command-builder
description: Build and validate FFmpeg commands for video processing, aspect ratio adjustment, audio removal, subtitle burning, and video concatenation in the BEDROT Media Suite
---

# FFmpeg Command Builder Skill

## When to Use
Activate when the user needs to:
- Construct FFmpeg filter chains for video processing
- Debug failing FFmpeg commands
- Convert between aspect ratios (9:16, 16:9, 1:1, 4:5)
- Remove/extract audio tracks
- Burn subtitles with libass
- Concatenate video segments

## BEDROT-Specific Patterns

### Aspect Ratio Adjustment (from video_processor.py)
```bash
# Crop to fill pattern
-vf "scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"

# Letterbox/pillarbox pattern
-vf "scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
```

### Audio Removal (from media_download_app.py)
```bash
ffmpeg -i input.mp4 -c:v copy -an output.mp4
```

### Subtitle Burning (from caption_generator)
```bash
ffmpeg -i input.mp4 -vf "subtitles=captions.srt:force_style='FontName=Arial,FontSize=24'" output.mp4
```

## Validation Rules
1. Always use `-y` for overwrite confirmation in batch operations
2. Use `-hide_banner -loglevel error` for cleaner output
3. Prefer stream copy (`-c:v copy`) when no transcoding needed
4. Always specify output container format explicitly

## Common Errors in This Codebase
- Missing `-reset_timestamps 1` in segment operations
- Incorrect filter graph syntax for complex chains
- Platform-specific path escaping issues
```

---

## Pain Point #2: PyQt5/PyQt6 Framework Conflict

### Evidence
- `readme.md:332-334` - Documents the conflict requiring process isolation
- `requirements.txt:41-44` - Both PyQt5 and PyQt6 pinned simultaneously
- Release Calendar uses PyQt6; all other tools use PyQt5
- `launcher.py` spawns separate processes as workaround

### Impact
- **Critical** - Framework conflicts cause import crashes
- Cannot run multiple PyQt apps in same process
- Forces complex process isolation architecture
- New developers frequently hit this on first setup

### Skill Solution: `pyqt-migration-assistant`

```yaml
---
name: pyqt-migration-assistant
description: Assist with PyQt5 to PyQt6 migration or vice versa, handle framework conflicts, and ensure proper import patterns for BEDROT GUI tools
---

# PyQt Migration Assistant

## Framework Status in BEDROT
| Module | Framework | Migration Priority |
|--------|-----------|-------------------|
| Reel Tracker | PyQt5 | Low |
| Snippet Remixer | PyQt5 | Low |
| Caption Generator | PyQt5 | Low |
| Transcriber Tool | PyQt5 | Low |
| Release Calendar | PyQt6 | N/A (already migrated) |

## Critical Import Patterns

### NEVER do this (causes conflicts):
```python
from PyQt5.QtWidgets import QWidget
from PyQt6.QtWidgets import QDialog  # CRASH!
```

### ALWAYS use this pattern:
```python
# At module top, choose one framework
try:
    from PyQt6.QtWidgets import QWidget, QDialog
    from PyQt6.QtCore import Qt, pyqtSignal
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QWidget, QDialog
    from PyQt5.QtCore import Qt, pyqtSignal
    PYQT_VERSION = 5
```

## Migration Checklist
1. [ ] Replace `exec_()` with `exec()` (PyQt6)
2. [ ] Update signal/slot syntax
3. [ ] Replace deprecated enum access patterns
4. [ ] Update QAction parent requirements
5. [ ] Test in isolated process first
```

---

## Pain Point #3: sys.path Manipulation Anti-Pattern

### Evidence
- 11+ occurrences of `sys.path.insert(0, ...)` across packages
- `launcher.py:14` - Adds src to path
- Every modular entry point (`*_modular.py`) manipulates sys.path
- Causes import ordering issues and IDE confusion

### Impact
- **High** - Unpredictable import behavior
- IDE autocompletion breaks frequently
- Circular import risks
- Different behavior when run from different directories

### Skill Solution: `import-fixer`

```yaml
---
name: import-fixer
description: Fix Python import issues, eliminate sys.path hacks, and establish proper package structure for BEDROT modular applications
---

# Import Pattern Fixer

## Current Anti-Pattern (found 11 times):
```python
# BAD - found in launcher.py, all *_modular.py files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))
```

## Correct Pattern:
```python
# In each package's __init__.py, use relative imports
from .config_manager import ConfigManager
from .main_app import MainApplication

# In entry points, use package imports after ensuring PYTHONPATH
# Or use: python -m src.package_name.main
```

## BEDROT-Specific Fix Strategy

### Step 1: Verify pyproject.toml/setup.py exists
The project needs proper package installation.

### Step 2: Replace sys.path hacks with:
```python
# In entry point scripts
if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add project root to path ONCE at entry point only
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.package_name import main
    main()
```

### Step 3: Update launch commands
```bash
# Instead of: python src/snippet_remixer_modular.py
# Use: python -m src.snippet_remixer
```
```

---

## Pain Point #4: Configuration File Sprawl

### Evidence
- 9 separate JSON config files in `/config/`
- 3 additional config locations in archived modules
- `reel_tracker_config.json` - Advanced with version history
- Others - Simple JSON without versioning
- No unified schema validation

### Impact
- **High** - Configuration drift between tools
- No validation = silent failures with bad config
- Version history only in one tool (reel_tracker)
- Migration between config versions is manual

### Skill Solution: `config-validator`

```yaml
---
name: config-validator
description: Validate, migrate, and manage JSON configuration files for BEDROT Media Suite tools with schema enforcement and version tracking
---

# Configuration Validator

## Configuration Files in BEDROT

| File | Tool | Schema Status |
|------|------|---------------|
| yt_downloader_gui_settings.json | Media Downloader | No schema |
| video_remixer_settings.json | Snippet Remixer | No schema |
| video_splitter_settings.json | Video Splitter | No schema |
| reel_tracker_config.json | Reel Tracker | Has version history |
| release_calendar_config.json | Release Calendar | No schema |
| calendar_data.json | Release Calendar | No schema |
| transcriber_tool_settings.json | Transcriber | No schema |
| caption_generator_settings.json | Caption Generator | No schema |

## Validation Actions

### 1. Check for Required Fields
```python
REQUIRED_FIELDS = {
    "video_remixer_settings.json": ["output_folder", "bpm", "aspect_ratio"],
    "yt_downloader_gui_settings.json": ["download_path", "format"],
    # ... etc
}
```

### 2. Type Validation
```python
FIELD_TYPES = {
    "bpm": (int, float),
    "output_folder": str,
    "aspect_ratio": str,  # Must match pattern like "16:9" or "1920x1080 (HD)"
}
```

### 3. Path Existence Checks
All `*_folder` and `*_path` fields should point to existing directories.

## Migration Support
When adding new required fields, provide defaults:
```python
def migrate_config(config, from_version, to_version):
    if from_version < 2 and to_version >= 2:
        config.setdefault("new_field", "default_value")
    return config
```
```

---

## Pain Point #5: Temporary File Cleanup Fragility

### Evidence
- `src/media_download_app.py:940-948` - 4 different temp file naming patterns
- `TEMP_DOWNLOAD_`, `_TEMP_NOAUDIO`, `_TEMP_AR`, `_TEMP_CUT` prefixes
- Multiple cleanup blocks scattered through download pipeline
- `src/snippet_remixer/video_processor.py` - `.ts` intermediate files

### Impact
- **Critical** - Disk space exhaustion on failed runs
- Orphaned temp files accumulate over time
- No centralized cleanup mechanism
- Different naming conventions make cleanup scripts unreliable

### Skill Solution: `temp-file-manager`

```yaml
---
name: temp-file-manager
description: Manage temporary file creation, tracking, and cleanup for BEDROT video processing pipelines to prevent disk space exhaustion
---

# Temporary File Manager

## Known Temp File Patterns in BEDROT

### Media Downloader (media_download_app.py)
```
TEMP_DOWNLOAD_{uuid}.*           # Initial download
{title}_TEMP_NOAUDIO.mp4         # After audio removal
{title}_TEMP_AR.mp4              # After aspect ratio adjust
{title}_TEMP_CUT.mp4             # After time cutting
```

### Snippet Remixer (video_processor.py)
```
snippet_{index}_{timestamp}.ts   # Intermediate segments
concat_list_{timestamp}.txt      # FFmpeg concat demuxer input
```

### Caption Generator
```
temp_audio_{uuid}.wav            # Extracted audio for transcription
```

## Cleanup Strategy

### 1. Context Manager Pattern (Recommended)
```python
from contextlib import contextmanager
import tempfile
import os

@contextmanager
def temp_video_file(suffix=".mp4", prefix="BEDROT_TEMP_"):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    try:
        os.close(fd)
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)
```

### 2. Cleanup on Startup
```python
def cleanup_orphaned_temps(directory, max_age_hours=24):
    """Remove temp files older than max_age_hours."""
    patterns = ["TEMP_DOWNLOAD_*", "*_TEMP_NOAUDIO*", "*_TEMP_AR*", "*_TEMP_CUT*", "snippet_*.ts"]
    # Implementation...
```

### 3. Graceful Failure Cleanup
Always wrap processing in try/finally that cleans temp files.
```

---

## Pain Point #6: No Automated Testing Infrastructure

### Evidence
- `tests/` contains only 8 test files
- No `pytest.ini`, `tox.ini`, or CI/CD configuration
- No GUI testing framework configured
- Manual testing documented as primary approach
- `tests/test_pyqt5.py` - Just checks if PyQt5 imports

### Impact
- **Critical** - Regressions go undetected
- Refactoring is high-risk
- No confidence in cross-platform compatibility
- New contributors can't validate changes

### Skill Solution: `test-generator`

```yaml
---
name: test-generator
description: Generate pytest test cases for BEDROT Media Suite modules including unit tests, integration tests, and mock-based GUI tests
---

# Test Generator for BEDROT

## Current Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Video Splitter | 4 tests | ~15% |
| Config System | 1 test | ~5% |
| Video Logging | 1 test | ~10% |
| Crop Fix | 1 test | ~5% |
| PyQt5 Import | 1 test | N/A |

## Test Templates

### ConfigManager Test Template
```python
import pytest
from src.{package}.config_manager import ConfigManager

class TestConfigManager:
    @pytest.fixture
    def config_manager(self, tmp_path):
        config_file = tmp_path / "test_config.json"
        return ConfigManager(str(config_file))

    def test_default_config_created(self, config_manager):
        assert config_manager.config is not None

    def test_save_and_load_roundtrip(self, config_manager):
        config_manager.config["test_key"] = "test_value"
        config_manager.save_config()
        # Reload and verify
        new_manager = ConfigManager(config_manager.config_file)
        assert new_manager.config["test_key"] == "test_value"
```

### FFmpeg Integration Test Template
```python
import pytest
import subprocess

@pytest.fixture
def sample_video(tmp_path):
    # Generate test video with FFmpeg
    output = tmp_path / "test.mp4"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=1:size=1920x1080",
        "-c:v", "libx264", "-y", str(output)
    ], check=True)
    return output

def test_aspect_ratio_conversion(sample_video, tmp_path):
    # Test conversion logic here
    pass
```

### PyQt Mock Test Template
```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_qapplication():
    with patch('PyQt5.QtWidgets.QApplication') as mock:
        yield mock

def test_main_window_initialization(mock_qapplication):
    from src.{package}.main_app import MainApplication
    # Test initialization without actual GUI
    pass
```

## pytest.ini Configuration
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    gui: marks tests requiring GUI
    integration: marks integration tests
```
```

---

## Pain Point #7: Monolithic Main App Files

### Evidence
- `src/snippet_remixer/main_app.py` - 2,352 lines
- `src/reel_tracker/main_app.py` - 2,199 lines
- `src/release_calendar/main_app.py` - 1,440 lines
- `src/media_download_app.py` - 1,645 lines

### Impact
- **High** - Hard to navigate, test, and maintain
- Single file changes risk breaking unrelated functionality
- Code reviews are overwhelming
- IDE performance degradation

### Skill Solution: `module-splitter`

```yaml
---
name: module-splitter
description: Refactor monolithic BEDROT main_app.py files into focused modules following the established modularization guidelines
---

# Module Splitter

## Target Files for Refactoring

| File | Lines | Priority |
|------|-------|----------|
| snippet_remixer/main_app.py | 2,352 | High |
| reel_tracker/main_app.py | 2,199 | Medium |
| media_download_app.py | 1,645 | High |
| release_calendar/main_app.py | 1,440 | Medium |

## Extraction Strategy (per MODULARIZATION_GUIDELINES.md)

### Step 1: Identify Extractable Components
Look for these patterns in main_app.py:
- Inner classes → Move to separate modules
- Callback methods > 50 lines → Extract to handlers.py
- UI setup methods → Move to ui_components.py
- Business logic mixed with UI → Extract to services.py

### Step 2: Standard Module Structure
```
package_name/
├── __init__.py
├── main_app.py          # < 500 lines, UI shell only
├── config_manager.py    # Already extracted
├── ui_components.py     # NEW: Widget factories
├── handlers.py          # NEW: Event handlers
├── services.py          # NEW: Business logic
├── dialogs.py           # Dialog classes
└── utils.py             # Utilities
```

### Step 3: Extraction Checklist
- [ ] Move inner classes to separate files
- [ ] Extract methods > 100 lines
- [ ] Remove inline lambda callbacks > 3 lines
- [ ] Consolidate duplicate UI patterns
- [ ] Add type hints during extraction
```

---

## Pain Point #8: Inconsistent Logging Approaches

### Evidence
- `src/core/logger.py` - Centralized logging
- `src/core/safe_print.py` - 485 lines for Windows Unicode handling
- `src/snippet_remixer/logging_config.py` - Package-specific logging
- Print statements with `DEBUG:` prefix throughout
- `src/media_download_app.py:965+` - Multiple `print(f"DEBUG: ...")` statements

### Impact
- **Medium-High** - Inconsistent debug output
- No log aggregation possible
- Windows Unicode issues require special handling
- Different verbosity controls per module

### Skill Solution: `logging-standardizer`

```yaml
---
name: logging-standardizer
description: Standardize logging across BEDROT modules using the centralized logger with proper levels, Unicode handling, and file rotation
---

# Logging Standardizer

## Current Logging Approaches (Inconsistent)

### 1. Core Logger (src/core/logger.py)
```python
from core.logger import get_logger
logger = get_logger(__name__)
logger.info("Message")
```

### 2. Safe Print (src/core/safe_print.py)
```python
from core.safe_print import safe_print
safe_print("Unicode-safe message: \u2713")
```

### 3. Raw Print with DEBUG Prefix
```python
print(f"DEBUG: Some message")  # Found 20+ times in media_download_app.py
```

### 4. Package-Specific Logger (snippet_remixer)
```python
from .logging_config import setup_logging, get_logger
```

## Standardization Rules

### Rule 1: Use Core Logger Everywhere
```python
# At module top
from src.core.logger import get_logger
logger = get_logger(__name__)

# Replace all print(f"DEBUG: ...") with:
logger.debug("Message with %s", variable)
```

### Rule 2: Use safe_print Only for User-Facing Output
```python
# For status messages shown to users (not logs)
from src.core.safe_print import safe_print
safe_print("Processing complete!")
```

### Rule 3: Configure Log Levels via Environment
```bash
# In .env
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=INFO   # For production
```

### Rule 4: Structured Logging for Video Operations
```python
logger.info("Processing video", extra={
    "video_file": filename,
    "operation": "aspect_ratio_adjust",
    "target_ratio": "16:9"
})
```

## Migration Script
```python
# Find and replace DEBUG prints
import re
pattern = r'print\(f"DEBUG: (.*)"\)'
replacement = r'logger.debug("\1")'
```
```

---

## Pain Point #9: Environment Variable Overload

### Evidence
- `.env.example` - 50+ environment variables
- Different prefix conventions: `SLIDESHOW_*`, `BEDROT_*`, no prefix
- Some tools ignore environment variables entirely
- No validation of required vs optional variables

### Impact
- **Medium** - Configuration confusion
- New developers overwhelmed by options
- Missing variables cause silent failures
- No documentation of which variables each tool needs

### Skill Solution: `env-validator`

```yaml
---
name: env-validator
description: Validate, document, and manage environment variables for BEDROT Media Suite with per-tool requirements and sensible defaults
---

# Environment Variable Validator

## Variable Categories

### Required for All Tools
```bash
# None currently - all have defaults
```

### Required for Specific Tools

#### Transcriber Tool
```bash
ELEVENLABS_API_KEY=your_key_here  # REQUIRED - No default
```

#### Media Downloader
```bash
# All optional, has defaults
BEDROT_DOWNLOAD_PATH=./downloads
```

### Optional Performance Tuning
```bash
SLIDESHOW_MAX_PROCESSES=4
BEDROT_LOG_LEVEL=INFO
```

## Validation Script
```python
def validate_environment(tool_name: str) -> list[str]:
    """Return list of missing required variables for tool."""
    required = {
        "transcriber_tool": ["ELEVENLABS_API_KEY"],
        "media_downloader": [],
        "snippet_remixer": [],
        # ... etc
    }

    missing = []
    for var in required.get(tool_name, []):
        if not os.getenv(var):
            missing.append(var)
    return missing
```

## Startup Check Pattern
```python
# Add to each tool's startup
missing = validate_environment("transcriber_tool")
if missing:
    print(f"ERROR: Missing required environment variables: {missing}")
    print("See .env.example for configuration")
    sys.exit(1)
```
```

---

## Pain Point #10: No Health Check Integration in Launcher

### Evidence
- `src/core/health_check.py` - 975 lines, comprehensive but unused
- `launcher.py` - Spawns tools without checking dependencies
- Tools fail at runtime if FFmpeg/yt-dlp missing
- No pre-flight validation

### Impact
- **High** - Poor user experience on first run
- Silent failures when dependencies missing
- Health check system exists but isn't integrated
- Users must troubleshoot manually

### Skill Solution: `startup-validator`

```yaml
---
name: startup-validator
description: Integrate health checks into BEDROT launcher startup, validate dependencies before spawning tools, and provide actionable fix instructions
---

# Startup Validator

## Available Health Checks (from src/core/health_check.py)

The HealthChecker class provides these checks:
- `check_python_version()` - Python 3.7+ required
- `check_ffmpeg()` - FFmpeg and FFprobe availability
- `check_ytdlp()` - yt-dlp installation
- `check_python_package()` - Required packages
- `check_output_directory_permissions()` - Write access
- `check_disk_space()` - Minimum free space
- `check_pyqt5_installation()` - GUI framework
- `check_system_resources()` - CPU/memory
- `check_network_connectivity()` - For download tools

## Integration Points

### 1. Launcher Startup
```python
# In launcher.py, before creating GUI
from src.core.health_check import HealthChecker

checker = HealthChecker()
results = checker.run_all_checks()
errors = [r for r in results if r.status == 'error']

if errors:
    # Show error dialog before proceeding
    show_health_check_errors(errors)
```

### 2. Per-Tool Validation
```python
TOOL_REQUIREMENTS = {
    "media_download": ["ffmpeg", "yt-dlp"],
    "snippet_remixer": ["ffmpeg", "ffprobe"],
    "caption_generator": ["ffmpeg"],
    "transcriber_tool": ["elevenlabs_api_key"],
}

def validate_tool_requirements(tool_name):
    checker = HealthChecker()
    required = TOOL_REQUIREMENTS.get(tool_name, [])
    # Run only relevant checks
```

### 3. Fix Instructions
```python
FIX_INSTRUCTIONS = {
    "ffmpeg": "Install FFmpeg: https://ffmpeg.org/download.html\nAdd to PATH",
    "yt-dlp": "pip install yt-dlp",
    "elevenlabs_api_key": "Set ELEVENLABS_API_KEY in .env file",
}
```
```

---

## Pain Point #11: Manual Aspect Ratio Data Migration

### Evidence
- `tools/video_aspect_ratio_migrator.py` - 471+ lines
- `tools/apply_video_aspect_ratio_migration.py` - Companion script
- `tools/csv_column_migrator.py` - CSV schema migrations
- Manual process with backup/restore complexity

### Impact
- **Medium-High** - Data migrations are risky and manual
- No rollback automation
- Confidence scoring requires interpretation
- Multiple scripts must be run in sequence

### Skill Solution: `data-migrator`

```yaml
---
name: data-migrator
description: Automate CSV and configuration data migrations for BEDROT Reel Tracker with backup, validation, and rollback support
---

# Data Migrator

## Migration Types

### 1. Aspect Ratio Migration (video_aspect_ratio_migrator.py)
Updates aspect_ratio column based on actual video dimensions via FFprobe.

### 2. CSV Column Migration (csv_column_migrator.py)
Renames, reorganizes, or adds columns to CSV data files.

### 3. Config Version Migration
Updates configuration files to new schema versions.

## Safe Migration Workflow

```python
def safe_migrate(migration_func, source_file, *args):
    """
    Wrapper for safe migrations with automatic backup and rollback.
    """
    # 1. Create timestamped backup
    backup_path = create_backup(source_file)

    try:
        # 2. Run migration on copy
        temp_output = migration_func(source_file, *args)

        # 3. Validate output
        if not validate_migration_output(temp_output):
            raise MigrationError("Validation failed")

        # 4. Replace original
        shutil.move(temp_output, source_file)

        return {"success": True, "backup": backup_path}

    except Exception as e:
        # 5. Rollback on failure
        shutil.copy(backup_path, source_file)
        return {"success": False, "error": str(e), "backup": backup_path}
```

## Pre-Migration Checklist
- [ ] Backup exists and is verified
- [ ] Source file is not open in other applications
- [ ] Sufficient disk space for backup + temp files
- [ ] Migration has been tested on sample data
- [ ] Rollback procedure documented

## Common Migrations

### Add New Column
```python
df['new_column'] = df.get('new_column', 'default_value')
```

### Rename Column
```python
df.rename(columns={'old_name': 'new_name'}, inplace=True)
```

### Update Aspect Ratio Format
```python
# From: "16:9"
# To: "1920x1080 (HD 16:9)"
```
```

---

## Pain Point #12: No Batch Processing Coordination

### Evidence
- Each tool has independent batch processing
- `src/snippet_remixer/job_queue.py` - Queue for remixer only
- No cross-tool job coordination
- Release Calendar targets 678 assets/month but no batch workflow

### Impact
- **High** - Manual orchestration required for large batches
- Can't queue: "download 50 videos, then remix, then track"
- No progress tracking across pipeline stages
- Resource contention when running multiple tools

### Skill Solution: `batch-orchestrator`

```yaml
---
name: batch-orchestrator
description: Coordinate multi-tool batch workflows for BEDROT content production pipelines with progress tracking and resource management
---

# Batch Orchestrator

## Pipeline Definition

A BEDROT production pipeline typically flows:
```
Download → Process → Track → Schedule
```

### Example: Reel Production Pipeline
```yaml
pipeline: reel_production
steps:
  - tool: media_downloader
    action: download_batch
    input: urls.txt
    output: ./downloads/raw/

  - tool: snippet_remixer
    action: remix_batch
    input: ./downloads/raw/
    output: ./downloads/remixed/
    settings:
      bpm: 140
      duration: 30

  - tool: reel_tracker
    action: import_batch
    input: ./downloads/remixed/
    metadata:
      persona: "ZONE_A0"
      release: "AUTO_GENERATED"
```

## Resource Management

```python
# Prevent resource contention
MAX_CONCURRENT_FFMPEG = 2
MAX_CONCURRENT_DOWNLOADS = 3

class ResourcePool:
    def __init__(self):
        self.ffmpeg_semaphore = Semaphore(MAX_CONCURRENT_FFMPEG)
        self.download_semaphore = Semaphore(MAX_CONCURRENT_DOWNLOADS)
```

## Progress Tracking

```python
class PipelineProgress:
    def __init__(self, pipeline_name, total_steps):
        self.pipeline_name = pipeline_name
        self.total_steps = total_steps
        self.current_step = 0
        self.step_progress = {}

    def report(self):
        return {
            "pipeline": self.pipeline_name,
            "overall": f"{self.current_step}/{self.total_steps}",
            "current_step": self.step_progress
        }
```

## Error Handling

```python
# On step failure:
# 1. Log error with full context
# 2. Save pipeline state for resume
# 3. Option to skip failed item or abort
# 4. Notify user with actionable message
```
```

---

## Pain Point #13: Unicode/Windows Compatibility Fragility

### Evidence
- `src/core/safe_print.py` - 485 lines dedicated to Windows Unicode
- Multiple encoding fallbacks in file operations
- `csv_column_migrator.py:` - `latin-1` encoding fallback
- Media files with international characters fail silently

### Impact
- **Medium-High** - Windows users hit encoding issues frequently
- Non-ASCII filenames cause crashes
- Console output garbled without safe_print
- CSV operations fail on special characters

### Skill Solution: `unicode-hardener`

```yaml
---
name: unicode-hardener
description: Ensure Unicode compatibility across BEDROT operations including file paths, CSV data, console output, and FFmpeg commands on Windows
---

# Unicode Hardener

## Problem Areas

### 1. Console Output (Windows CMD/PowerShell)
```python
# BROKEN: Direct print of Unicode
print("Processing: \u2713 Done")  # Crashes on some Windows consoles

# FIXED: Use safe_print
from src.core.safe_print import safe_print
safe_print("Processing: \u2713 Done")
```

### 2. File Paths with Special Characters
```python
# BROKEN: Raw path handling
subprocess.run(["ffmpeg", "-i", path_with_emoji])

# FIXED: Proper encoding
import os
if os.name == 'nt':
    # Windows: Use short path names for problem files
    path = get_short_path_name(path_with_emoji)
```

### 3. CSV Operations
```python
# BROKEN: Default encoding
df = pd.read_csv(file)

# FIXED: Explicit encoding with fallback
try:
    df = pd.read_csv(file, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(file, encoding='latin-1')
```

### 4. FFmpeg Subprocess Calls
```python
# BROKEN: Unicode in FFmpeg command
subprocess.run([...], text=True)

# FIXED: Explicit encoding
subprocess.run([...], text=True, encoding='utf-8', errors='replace')
```

## Validation Checklist
- [ ] All file operations use explicit encoding
- [ ] All subprocess calls handle encoding
- [ ] Console output uses safe_print
- [ ] File paths are validated before use
- [ ] CSV read/write has fallback encodings

## Testing Non-ASCII
```python
TEST_STRINGS = [
    "normal_file.mp4",
    "archivo_español.mp4",
    "日本語ファイル.mp4",
    "emoji_🎵_file.mp4",
]
```
```

---

## Pain Point #14: No Release Calendar ↔ Reel Tracker Integration

### Evidence
- Release Calendar manages 678 assets/month target
- Reel Tracker manages individual content metadata
- No automated connection between them
- Manual process to ensure scheduled releases have content

### Impact
- **High** - Risk of scheduling releases without content
- No visibility into content readiness per release
- Manual cross-referencing between tools
- Can't answer "Is this release ready?" automatically

### Skill Solution: `release-content-linker`

```yaml
---
name: release-content-linker
description: Link BEDROT Release Calendar releases to Reel Tracker content, validate release readiness, and identify content gaps
---

# Release-Content Linker

## Data Mapping

### Release Calendar Schema (calendar_data.json)
```json
{
  "releases": [
    {
      "id": "release_123",
      "title": "ZONE_A0 - New Single",
      "date": "2026-01-15",
      "persona": "ZONE_A0",
      "deliverables": ["TikTok", "IG Reel", "YouTube Short"]
    }
  ]
}
```

### Reel Tracker Schema (CSV)
```
reel_id,persona,release,reel_type,file_path,status
REEL_001,ZONE_A0,NEW_SINGLE,TikTok,/path/to/file.mp4,ready
```

## Linking Logic

```python
def get_release_content(release_id: str) -> dict:
    """
    Find all Reel Tracker entries linked to a Release Calendar release.
    """
    release = get_release_from_calendar(release_id)
    reels = read_reel_tracker_csv()

    linked = reels[
        (reels['persona'] == release['persona']) &
        (reels['release'] == release['title'])
    ]

    return {
        "release": release,
        "content_count": len(linked),
        "by_type": linked.groupby('reel_type').size().to_dict(),
        "ready_count": len(linked[linked['status'] == 'ready'])
    }

def check_release_readiness(release_id: str) -> dict:
    """
    Validate release has required deliverables.
    """
    release = get_release_from_calendar(release_id)
    content = get_release_content(release_id)

    missing = []
    for deliverable in release['deliverables']:
        if deliverable not in content['by_type']:
            missing.append(deliverable)

    return {
        "ready": len(missing) == 0,
        "missing_deliverables": missing,
        "content_summary": content
    }
```

## Readiness Report

```
Release: ZONE_A0 - New Single (2026-01-15)
Status: NOT READY

Required Deliverables:
  [x] TikTok (3 ready)
  [x] IG Reel (2 ready)
  [ ] YouTube Short (0 ready) <- MISSING

Action Required: Create YouTube Short content for this release.
```
```

---

## Pain Point #15: Hardcoded Paths and Magic Numbers

### Evidence
- `launcher.py:51-57` - Hardcoded script paths
- `src/media_download_app.py` - Hardcoded aspect ratio values
- `src/caption_generator/` - Hardcoded resolution presets
- No centralized constants file

### Impact
- **Medium** - Path changes require multi-file updates
- Magic numbers scattered throughout code
- Inconsistent values across tools (e.g., aspect ratio strings)
- Refactoring is error-prone

### Skill Solution: `constants-extractor`

```yaml
---
name: constants-extractor
description: Extract hardcoded paths, magic numbers, and repeated literals into centralized constants for BEDROT Media Suite
---

# Constants Extractor

## Identified Magic Values

### Aspect Ratios (inconsistent formats!)
```python
# In media_download_app.py
"16:9", "9:16", "1:1", "4:5"

# In snippet_remixer
"1920x1080 (HD 16:9)", "1080x1920 (Vertical 9:16)"

# In caption_generator
"1080p", "720p", "4K", "vertical_1080x1920"
```

### Resolution Values
```python
# Scattered throughout:
1920, 1080, 1280, 720, 3840, 2160
```

### Script Paths (launcher.py)
```python
SCRIPT_1_PATH = 'src/media_download_app.py'
SCRIPT_2_PATH = 'src/snippet_remixer_modular.py'
# ... etc
```

## Proposed Constants Module

### src/core/constants.py
```python
"""
Centralized constants for BEDROT Media Suite.
"""

# Aspect Ratios - Canonical Format
class AspectRatio:
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    SQUARE_1_1 = "1:1"
    PORTRAIT_4_5 = "4:5"

    # Dimension mappings
    DIMENSIONS = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
    }

# Resolutions
class Resolution:
    HD_1080P = (1920, 1080)
    HD_720P = (1280, 720)
    UHD_4K = (3840, 2160)
    VERTICAL_HD = (1080, 1920)

# Tool Paths (relative to project root)
class ToolPaths:
    MEDIA_DOWNLOADER = "src/media_download_app.py"
    SNIPPET_REMIXER = "src/snippet_remixer_modular.py"
    VIDEO_SPLITTER = "src/video_splitter_modular.py"
    REEL_TRACKER = "src/reel_tracker_modular.py"
    RELEASE_CALENDAR = "src/release_calendar_modular.py"
    TRANSCRIBER = "src/transcriber_tool_modular.py"
    CAPTION_GENERATOR = "src/caption_generator_modular.py"

# Temp File Prefixes
class TempPrefixes:
    DOWNLOAD = "TEMP_DOWNLOAD_"
    NO_AUDIO = "_TEMP_NOAUDIO"
    ASPECT_RATIO = "_TEMP_AR"
    TIME_CUT = "_TEMP_CUT"
    SNIPPET = "snippet_"
```

## Migration Pattern
```python
# Before
if aspect_ratio == "16:9":
    width, height = 1920, 1080

# After
from src.core.constants import AspectRatio
if aspect_ratio == AspectRatio.LANDSCAPE_16_9:
    width, height = AspectRatio.DIMENSIONS[aspect_ratio]
```
```

---

## Pain Point #16: No Preset/Template Management

### Evidence
- Each tool stores settings independently
- No way to save/load processing presets
- Users must manually reconfigure for different content types
- Release Calendar has some preset patterns, others don't

### Impact
- **Medium-High** - Repetitive configuration work
- No consistency across batch runs
- Can't share settings between team members
- Different personas require different settings (6 personas documented)

### Skill Solution: `preset-manager`

```yaml
---
name: preset-manager
description: Create, save, load, and share processing presets for BEDROT tools including per-persona defaults and batch configurations
---

# Preset Manager

## Preset Types

### 1. Snippet Remixer Presets
```json
{
  "preset_name": "ZONE_A0_TikTok",
  "tool": "snippet_remixer",
  "settings": {
    "bpm": 140,
    "duration_seconds": 30,
    "aspect_ratio": "9:16",
    "mute_audio": false
  }
}
```

### 2. Media Downloader Presets
```json
{
  "preset_name": "High Quality Source",
  "tool": "media_downloader",
  "settings": {
    "format": "mp4",
    "video_only": false,
    "aspect_ratio": "Original"
  }
}
```

### 3. Caption Generator Presets
```json
{
  "preset_name": "BEDROT_Standard_Captions",
  "tool": "caption_generator",
  "settings": {
    "font": "Impact",
    "font_size": 48,
    "color": "#FFFFFF",
    "background": "#000000",
    "resolution": "1080x1920"
  }
}
```

## Per-Persona Defaults (6 BEDROT Personas)

```json
{
  "ZONE_A0": {
    "remixer": {"bpm": 140, "aspect_ratio": "9:16"},
    "captions": {"font": "Impact", "color": "#00FF00"}
  },
  "PIG1987": {
    "remixer": {"bpm": 120, "aspect_ratio": "9:16"},
    "captions": {"font": "Arial Narrow", "color": "#FF0000"}
  },
  // ... etc for all 6 personas
}
```

## Preset Storage Structure
```
config/
├── presets/
│   ├── snippet_remixer/
│   │   ├── zone_a0_tiktok.json
│   │   ├── pig1987_instagram.json
│   │   └── default.json
│   ├── caption_generator/
│   │   └── bedrot_standard.json
│   └── media_downloader/
│       └── high_quality.json
```

## Quick Apply in UI
```python
def load_preset(tool_name: str, preset_name: str) -> dict:
    preset_path = f"config/presets/{tool_name}/{preset_name}.json"
    with open(preset_path) as f:
        return json.load(f)

def apply_preset(tool_instance, preset: dict):
    for key, value in preset['settings'].items():
        tool_instance.set_setting(key, value)
```
```

---

## Pain Point #17: No Progress/Status Dashboard

### Evidence
- `launcher.py` has basic log aggregation only
- No unified view of running operations
- Each tool shows progress independently
- Can't see overall system health at a glance

### Impact
- **Medium** - No situational awareness
- Must check each tool individually
- Resource usage invisible
- No historical operation tracking

### Skill Solution: `operations-dashboard`

```yaml
---
name: operations-dashboard
description: Provide unified progress, status, and resource monitoring across all running BEDROT tools with historical metrics
---

# Operations Dashboard

## Data Sources

### 1. Process Status (from launcher.py)
```python
active_processes = []  # Already tracked
process_map = {}       # Script path -> process
```

### 2. Tool-Specific Progress
Each tool should emit progress events:
```python
{
    "tool": "snippet_remixer",
    "operation": "remix",
    "progress": 0.45,
    "current_file": "video_023.mp4",
    "eta_seconds": 120
}
```

### 3. System Resources (from health_check.py)
```python
{
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_free_gb": 128.5
}
```

## Dashboard Views

### 1. Active Operations
```
┌─────────────────────────────────────────────────────┐
│ BEDROT OPERATIONS DASHBOARD                         │
├─────────────────────────────────────────────────────┤
│ RUNNING:                                            │
│   [▓▓▓▓▓▓░░░░] Snippet Remixer - 60% (ETA: 2m)    │
│   [▓▓▓░░░░░░░] Media Downloader - 30% (3/10)       │
│                                                     │
│ IDLE:                                               │
│   Reel Tracker, Caption Generator                   │
│                                                     │
│ SYSTEM: CPU 45% | RAM 62% | Disk 128GB free        │
└─────────────────────────────────────────────────────┘
```

### 2. Operation History
```
Recent Operations:
  [SUCCESS] 14:23 - Downloaded 10 videos (Media Downloader)
  [SUCCESS] 14:45 - Generated 5 remixes (Snippet Remixer)
  [FAILED]  15:02 - Transcription failed: API limit (Transcriber)
```

## Implementation Approach

### Event Bus Pattern
```python
class OperationEventBus:
    def __init__(self):
        self.subscribers = []

    def emit(self, event: dict):
        for subscriber in self.subscribers:
            subscriber(event)

    def subscribe(self, callback):
        self.subscribers.append(callback)

# In each tool:
event_bus.emit({
    "type": "progress",
    "tool": "snippet_remixer",
    "data": {"progress": 0.45, ...}
})
```

## Metrics Storage
```python
# Simple SQLite for operation history
CREATE TABLE operations (
    id INTEGER PRIMARY KEY,
    tool TEXT,
    operation TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    details JSON
);
```
```

---

## Summary: Skill Implementation Priority

| Priority | Skill | Impact | Effort |
|----------|-------|--------|--------|
| **P0** | ffmpeg-command-builder | Critical | Medium |
| **P0** | startup-validator | Critical | Low |
| **P0** | test-generator | Critical | High |
| **P1** | config-validator | High | Medium |
| **P1** | temp-file-manager | High | Low |
| **P1** | logging-standardizer | High | Medium |
| **P1** | module-splitter | High | High |
| **P2** | pyqt-migration-assistant | Medium-High | Medium |
| **P2** | import-fixer | Medium-High | Medium |
| **P2** | batch-orchestrator | High | High |
| **P2** | release-content-linker | High | Medium |
| **P3** | env-validator | Medium | Low |
| **P3** | unicode-hardener | Medium | Medium |
| **P3** | constants-extractor | Medium | Low |
| **P3** | data-migrator | Medium | Medium |
| **P3** | preset-manager | Medium | Medium |
| **P3** | operations-dashboard | Medium | High |

---

## Next Steps

1. **Create `.claude/skills/` directory** in repository
2. **Implement P0 skills first** - highest impact, unblocks other work
3. **Add skill descriptions to CLAUDE.md** for automatic discovery
4. **Test skills** with real BEDROT workflows
5. **Iterate based on usage** - refine descriptions and instructions

---

*Analysis completed 2026-01-08*
*Repository: bedrot-media-suite*
*Branch: claude/repo-pain-points-analysis-UNgsV*
