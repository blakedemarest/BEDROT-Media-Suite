# Documentation Discrepancies Report
## Bedrot Media Suite - Code vs Documentation Analysis

### Executive Summary
This report documents discrepancies found between the actual codebase implementation and the documentation (README.md and CLAUDE.md files).

> Update (2025-10-28): The Random Slideshow and MV Maker modules were archived and moved under `archive/`. References below are retained for historical tracking and should be interpreted accordingly.

---

## Major Discrepancies Found

### 1. Module Entry Points Mismatch

#### README.md States:
- `src/snippet_remixer.py` for Snippet Remixer
- `src/random_slideshow.py` for Random Slideshow Generator  

#### Actual Implementation:
- `src/snippet_remixer_modular.py` is the actual entry point (not `snippet_remixer.py`)
- `src/random_slideshow/main.py` is correct
- There's also `src/snippet_remixer/main.py` which is imported by the modular file

**Impact**: Users following README.md would fail to launch tools directly.

---

### 2. Missing Core Module Documentation

#### CLAUDE.md States:
- "Centralized Configuration System: New `src/core/` module with environment variable support"

#### README.md:
- No mention of the `src/core/` module at all
- No documentation about the centralized configuration system

**Impact**: Critical architecture component undocumented in main README.

---

### 3. Configuration File Locations

#### Documentation States:
- All config files in `config/` directory

#### Actual Implementation:
- Most config files are in `config/` 
- BUT also found:
  - `src/combined_random_config.json`
  - `src/config/reel_tracker_config.json`
  - `src/random_slideshow/combined_random_config.json`
  - `src/random_slideshow/config/slideshow_presets.json`
  - `src/mv_maker/config/mv_maker_config.json`

**Impact**: Configuration files scattered across multiple locations, not centralized as documented.

---

### 4. Missing Tools in README

#### Not Documented in README.md:
- `tools/generate_function_registry.py`
- Multiple test files in root: `fix_and_test_gui.py`, `test_fixed_gui.py`, `test_gui_simple.py`, `test_mp3_fix.py`

#### Documented but Implementation Different:
- Slideshow Editor mentioned but implementation details incomplete

---

### 5. Environment Variables Discrepancy

#### CLAUDE.md Claims:
- Comprehensive .env file support for all paths and settings
- Lists many environment variables like `SLIDESHOW_PROJECT_ROOT`, `SLIDESHOW_CONFIG_DIR`, etc.

#### Actual Implementation:
- `.env.example` exists and documents variables
- Core module (`src/core/env_loader.py`) exists and loads environment
- BUT launcher.py has fallback hardcoded paths when core module fails
- Not all modules consistently use environment variables

---

### 6. Dependency Issues

#### requirements.txt Issues:
- Contains duplicate entries (e.g., `requests` listed twice)
- Missing `tkinter` which is assumed to be included but isn't in WSL/Linux environments
- PyQt5 and PyQt6 both listed (potential conflicts)

#### Documentation States:
- "Tkinter is usually included with Python" - This is not true for all Python installations

---

### 7. Module Structure Inconsistencies

#### Modular vs Non-Modular Pattern:
- Some modules have `*_modular.py` entry points: `reel_tracker_modular.py`, `snippet_remixer_modular.py`, `release_calendar_modular.py`
- Others use `main.py` within their package
- Pattern not documented or explained

---

### 8. Random Slideshow Module Confusion

#### Multiple Entry Points Found:
- `src/random_slideshow/main.py` (documented)
- `src/random_slideshow/main_app.py`
- `src/random_slideshow/main_app_simple.py`

No documentation explaining which to use when.

---

### 9. Launcher Script Paths

#### launcher.py References:
```python
SCRIPT_2_PATH = get_script_path('snippet_remixer', 'src/snippet_remixer.py')
```

But actual file is `src/snippet_remixer_modular.py` - the fallback path is wrong.

---

### 10. Missing PyQt6 Requirement Documentation

#### README.md Section 5.6:
- Mentions PyQt6 requirement for Release Calendar
- But doesn't emphasize this is a separate, additional requirement

#### Reality:
- Both PyQt5 and PyQt6 are needed for full functionality
- Potential for version conflicts not addressed

---

## Minor Discrepancies

### 1. Directory Structure
- README shows simplified structure, missing many subdirectories
- No mention of `src/*/logs/` directories with extensive log files

### 2. BATCH File Documentation
- `start_launcher.bat` exists and is mentioned in CLAUDE.md as primary entry point for Windows
- README.md doesn't mention this at all

### 3. Test Files
- Multiple test files in root directory not documented or explained
- Appear to be development artifacts

---

## Recommendations

1. **Update README.md** to reflect actual module entry points
2. **Document the core module** and centralized configuration system
3. **Consolidate configuration files** to single `config/` directory
4. **Fix launcher.py fallback paths** to match actual file names
5. **Add tkinter to requirements.txt** or document installation separately
6. **Clean up test files** or move to proper test directory
7. **Document the modular vs non-modular pattern** and when to use each
8. **Update environment variable documentation** to match implementation
9. **Clarify PyQt5 vs PyQt6** requirements and potential conflicts
10. **Add missing tools documentation** or remove unused tools

---

## Critical Issues Requiring Immediate Attention

1. **Launcher fallback paths are wrong** - Will fail if core module import fails
2. **Configuration files scattered** - Makes management difficult
3. **Entry point documentation wrong** - Users cannot launch tools as documented
4. **Missing tkinter dependency** - Will fail on many systems

---

*Report generated: 2025-01-07*
*Analysis based on current git status showing multiple modified files*
