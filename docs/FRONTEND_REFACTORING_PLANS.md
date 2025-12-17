# Frontend Refactoring Implementation Plans

## Overview

This document contains detailed implementation plans for refactoring the BEDROT Media Suite frontend modules into reusable, decoupled component classes. The goal is to separate frontend logic from backend logic while preserving the existing visual appearance and UI behavior exactly.

### Guiding Principles

1. **No Visual Changes** - All UI styling, colors, fonts, and layouts must remain identical
2. **Backend Isolation** - Business logic must be framework-agnostic (no Tkinter/PyQt imports)
3. **Reusable Components** - UI elements become composable, testable classes
4. **Callback Abstraction** - Replace framework-specific signals with plain Python callbacks
5. **Configuration Decoupling** - Settings should use dataclasses, not UI variables

### Architecture Pattern

Each module will follow this layered architecture:

```
[UI Layer]          - Framework-specific widgets and layouts
     |
[Component Layer]   - Reusable UI component classes
     |
[Controller Layer]  - Orchestrates UI and services (no framework imports)
     |
[Service Layer]     - Pure business logic (already exists in most modules)
     |
[Data Layer]        - Models, config, persistence
```

---

## Plan 1: Video Splitter Module

**Current State**: Tkinter application with moderate coupling
**Lines of Code**: ~608 in `main_app.py`
**Framework**: Tkinter + tkinterdnd2
**Coupling Level**: Moderate - has separate `SplitWorker` with callback pattern

### Current Architecture Analysis

**Good Patterns (Keep)**:
- `SplitWorker` uses plain Python threads with callback functions
- `ffmpeg_splitter.py` has no UI dependencies
- `models.py` contains pure dataclasses (`SplitJob`, `SplitSegment`)
- Config/settings are loaded at startup, not bound to UI variables

**Coupling Issues**:
- `VideoSplitterApp.__init__` mixes UI setup with business logic initialization
- Tkinter variables (`tk.StringVar`, `tk.DoubleVar`) directly bound to settings
- Theme/styling embedded in application class (400+ lines)
- File management methods mixed with UI callbacks

### Refactoring Strategy

#### Phase 1: Extract Theme System

Create `src/video_splitter/theme.py`:
```python
# Theme configuration as pure data
BEDROT_COLORS = {
    "bg": "#121212",
    "bg_secondary": "#1a1a1a",
    "fg": "#e0e0e0",
    "accent_green": "#00ff88",
    "accent_cyan": "#00ffff",
    # ... all colors
}

def apply_bedrot_theme(root: tk.Tk, style: ttk.Style) -> dict:
    """Apply BEDROT theme to Tkinter widgets. Returns color dict."""
    # Move entire apply_bedrot_theme() method here
```

#### Phase 2: Create UI Components

Create `src/video_splitter/components/` directory:

**`file_list_component.py`**:
```python
class FileListComponent:
    """Reusable file list with drag-drop support."""

    def __init__(self, parent, on_files_added: Callable, on_files_removed: Callable):
        self.frame = ttk.LabelFrame(parent, text="SOURCE VIDEOS")
        self._on_files_added = on_files_added
        self._on_files_removed = on_files_removed
        self._files: List[str] = []
        self._build_ui()

    def _build_ui(self):
        # Listbox, scrollbar, buttons - extracted from main_app
        pass

    def add_files(self, paths: Iterable[str]) -> int:
        """Add files, return count added."""
        pass

    def get_files(self) -> List[str]:
        return self._files.copy()

    def clear(self):
        self._files.clear()
        self._refresh_display()
```

**`settings_panel_component.py`**:
```python
@dataclass
class SplitterSettings:
    """Settings data transfer object."""
    output_dir: str
    clip_length_seconds: float
    jitter_percent: int
    min_clip_length: float
    per_clip_jitter: bool
    reset_timestamps: bool
    overwrite_existing: bool

class SettingsPanelComponent:
    """Clip settings configuration panel."""

    def __init__(self, parent, initial_settings: SplitterSettings,
                 on_settings_changed: Callable[[SplitterSettings], None]):
        self.frame = ttk.LabelFrame(parent, text="OUTPUT & CLIP SETTINGS")
        self._settings = initial_settings
        self._on_changed = on_settings_changed
        self._build_ui()

    def get_settings(self) -> SplitterSettings:
        return SplitterSettings(
            output_dir=self._output_var.get(),
            clip_length_seconds=float(self._clip_var.get()),
            # ... extract all values
        )
```

**`progress_component.py`**:
```python
class ProgressComponent:
    """Progress bar with status display."""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self._build_ui()

    def set_progress(self, percent: float, status: str):
        self._progress_var.set(percent)
        self._status_var.set(status)

    def reset(self):
        self._progress_var.set(0)
        self._status_var.set("[INFO] Ready")
```

**`log_panel_component.py`**:
```python
class LogPanelComponent:
    """Scrollable log output panel."""

    def __init__(self, parent, colors: dict):
        self.frame = ttk.LabelFrame(parent, text="LOG OUTPUT")
        self._build_ui(colors)

    def log(self, message: str):
        """Thread-safe log append."""
        self._widget.config(state=tk.NORMAL)
        self._widget.insert(tk.END, message + "\n")
        self._widget.see(tk.END)
        self._widget.config(state=tk.DISABLED)
```

#### Phase 3: Create Controller

Create `src/video_splitter/controller.py`:
```python
class VideoSplitterController:
    """
    Orchestrates video splitting operations.
    No Tkinter imports - uses callbacks for UI updates.
    """

    def __init__(self,
                 config_manager: ConfigManager,
                 on_log: Callable[[str], None],
                 on_progress: Callable[[float, str], None],
                 on_complete: Callable[[bool], None]):
        self.config = config_manager
        self._on_log = on_log
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._worker = SplitWorker(
            log_callback=on_log,
            progress_callback=self._handle_progress
        )

    def start_splitting(self, files: List[str], settings: SplitterSettings) -> bool:
        """Start split operation. Returns False if already running."""
        if not files:
            return False

        jobs = [self._create_job(f, settings) for f in files]
        return self._worker.start(jobs, on_complete=self._on_complete)

    def stop(self):
        self._worker.stop()

    @property
    def is_running(self) -> bool:
        return self._worker.is_running
```

#### Phase 4: Refactor Main Application

Refactored `src/video_splitter/main_app.py`:
```python
class VideoSplitterApp:
    """Main application window - UI assembly only."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BEDROT VIDEO SPLITTER // CLIP ENGINE")

        # Apply theme
        self.colors = apply_bedrot_theme(root, ttk.Style())

        # Load config
        self.config_manager = ConfigManager()
        initial_settings = self._load_settings()

        # Create controller
        self.controller = VideoSplitterController(
            config_manager=self.config_manager,
            on_log=self._thread_safe_log,
            on_progress=self._thread_safe_progress,
            on_complete=self._on_complete
        )

        # Build UI components
        self._build_ui(initial_settings)

    def _build_ui(self, settings: SplitterSettings):
        self.root.columnconfigure(0, weight=1)

        # File list component
        self.file_list = FileListComponent(
            self.root,
            on_files_added=self._on_files_added,
            on_files_removed=lambda: None
        )
        self.file_list.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Settings panel
        self.settings_panel = SettingsPanelComponent(
            self.root,
            initial_settings=settings,
            on_settings_changed=self._persist_settings
        )
        self.settings_panel.frame.grid(row=1, column=0, sticky="nsew", padx=10)

        # Progress
        self.progress = ProgressComponent(self.root)
        self.progress.frame.grid(row=2, column=0, sticky="ew", padx=10)

        # Action buttons
        self._build_action_buttons()

        # Log panel
        self.log_panel = LogPanelComponent(self.root, self.colors)
        self.log_panel.frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)

    def start_processing(self):
        files = self.file_list.get_files()
        settings = self.settings_panel.get_settings()

        if self.controller.start_splitting(files, settings):
            self._set_running_state(True)
```

### File Structure After Refactoring

```
src/video_splitter/
├── __init__.py
├── main.py                    # Entry point
├── main_app.py                # Slim UI assembly (~150 lines)
├── controller.py              # Business logic orchestration
├── theme.py                   # Theme configuration
├── components/
│   ├── __init__.py
│   ├── file_list_component.py
│   ├── settings_panel_component.py
│   ├── progress_component.py
│   └── log_panel_component.py
├── config_manager.py          # (unchanged)
├── models.py                  # (unchanged)
├── split_worker.py            # (unchanged - already decoupled)
├── ffmpeg_splitter.py         # (unchanged - already decoupled)
└── utils.py                   # (unchanged)
```

### Verification Checklist

- [ ] All UI colors and fonts identical to original
- [ ] Drag-drop functionality works exactly as before
- [ ] Settings persist between sessions
- [ ] Progress updates display correctly
- [ ] Log output format unchanged
- [ ] Start/Stop buttons enable/disable correctly
- [ ] Window resize behavior preserved

---

## Plan 2: Caption Generator Module

**Current State**: PyQt5 application with severe coupling
**Lines of Code**: ~1,229 in `main_app.py`, ~348 in `batch_worker.py`
**Framework**: PyQt5
**Coupling Level**: Severe - `BatchCaptionWorker` inherits from `QThread`

### Current Architecture Analysis

**Good Patterns (Keep)**:
- `video_generator.py` is pure business logic (no Qt imports)
- `pairing_history.py` uses SQLite directly
- Settings are stored in config, loaded on startup

**Critical Coupling Issues**:
- `GeneratorWorker(QThread)` - inherits from Qt class
- `BatchCaptionWorker(QThread)` - inherits from Qt class with `pyqtSignal`
- Worker classes cannot be tested without PyQt5 running
- Theme/styling inline in `_apply_theme()` method (~150 lines)

### Refactoring Strategy

#### Phase 1: Create Framework-Agnostic Workers

Create `src/caption_generator/workers/` directory:

**`base_worker.py`**:
```python
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
from enum import Enum
import threading

class WorkerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkerCallbacks:
    """Callback interface for worker communication."""
    on_log: Callable[[str], None]
    on_progress: Callable[[int], None] = lambda x: None
    on_finished: Callable[[bool, str], None] = lambda s, m: None

class BaseWorker:
    """Base class for background workers - no Qt dependency."""

    def __init__(self, callbacks: WorkerCallbacks):
        self.callbacks = callbacks
        self._thread: Optional[threading.Thread] = None
        self._state = WorkerState.IDLE
        self._cancel_requested = False

    def start(self):
        if self._state == WorkerState.RUNNING:
            return False
        self._cancel_requested = False
        self._thread = threading.Thread(target=self._run_wrapper, daemon=True)
        self._thread.start()
        return True

    def cancel(self):
        self._cancel_requested = True

    def _run_wrapper(self):
        self._state = WorkerState.RUNNING
        try:
            self._run()
            self._state = WorkerState.COMPLETED
        except Exception as e:
            self._state = WorkerState.FAILED
            self.callbacks.on_finished(False, str(e))

    def _run(self):
        """Override in subclass."""
        raise NotImplementedError
```

**`generation_worker.py`**:
```python
@dataclass
class GenerationJob:
    srt_path: str
    audio_path: str
    output_path: str
    settings: Dict[str, Any]
    transparent: bool = False

class GenerationWorker(BaseWorker):
    """Single video generation worker."""

    def __init__(self, job: GenerationJob, callbacks: WorkerCallbacks):
        super().__init__(callbacks)
        self.job = job

    def _run(self):
        from .video_generator import generate_caption_video

        format_type = "WebM (transparent)" if self.job.transparent else "MP4"
        self.callbacks.on_log(f"[Caption Generator] Starting {format_type} video generation...")

        success, message = generate_caption_video(
            self.job.srt_path,
            self.job.audio_path,
            self.job.output_path,
            self.job.settings,
            progress_callback=self.callbacks.on_log,
            transparent=self.job.transparent
        )

        self.callbacks.on_finished(success, message)
```

**`batch_worker.py`** (refactored):
```python
@dataclass
class BatchCallbacks:
    """Extended callbacks for batch processing."""
    on_log: Callable[[str], None]
    on_batch_started: Callable[[int], None]
    on_progress: Callable[[int, int, str], None]  # current, total, filename
    on_transcription_completed: Callable[[str, str], None]  # filename, srt_path
    on_generation_completed: Callable[[str, bool, str], None]  # filename, success, message
    on_batch_summary: Callable[[Dict], None]
    on_finished: Callable[[], None]

class BatchCaptionWorker(BaseWorker):
    """Batch processing worker - no Qt dependency."""

    def __init__(self,
                 queue_items: List[Dict],
                 settings: Dict,
                 output_folder: str,
                 transcript_folder: str,
                 pairing_history,
                 callbacks: BatchCallbacks,
                 max_words_per_segment: int = 1):
        # Convert BatchCallbacks to WorkerCallbacks for base class
        base_callbacks = WorkerCallbacks(on_log=callbacks.on_log)
        super().__init__(base_callbacks)

        self.queue_items = queue_items
        self.settings = settings
        self.output_folder = output_folder
        self.transcript_folder = transcript_folder
        self.pairing_history = pairing_history
        self.batch_callbacks = callbacks
        self.max_words_per_segment = max_words_per_segment
        self.stats = {...}

    def _run(self):
        # Same logic as before, but using self.batch_callbacks instead of pyqtSignal
        self.batch_callbacks.on_batch_started(len(self.queue_items))
        # ... rest of processing
```

#### Phase 2: Create Qt Adapter Layer

Create `src/caption_generator/qt_adapters.py`:
```python
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from .workers import GenerationWorker, BatchCaptionWorker, WorkerCallbacks, BatchCallbacks

class QtGenerationWorker(QObject):
    """Qt wrapper for GenerationWorker - bridges signals."""

    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, job):
        super().__init__()
        callbacks = WorkerCallbacks(
            on_log=lambda msg: self.log_signal.emit(msg),
            on_progress=lambda p: self.progress_signal.emit(p),
            on_finished=lambda s, m: self.finished_signal.emit(s, m)
        )
        self._worker = GenerationWorker(job, callbacks)

    def start(self):
        self._worker.start()

    def cancel(self):
        self._worker.cancel()

class QtBatchWorker(QObject):
    """Qt wrapper for BatchCaptionWorker."""

    log_signal = pyqtSignal(str)
    batch_started = pyqtSignal(int)
    progress_signal = pyqtSignal(int, int, str)
    transcription_completed = pyqtSignal(str, str)
    generation_completed = pyqtSignal(str, bool, str)
    batch_summary = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, queue_items, settings, output_folder,
                 transcript_folder, pairing_history, max_words_per_segment):
        super().__init__()

        callbacks = BatchCallbacks(
            on_log=lambda m: self.log_signal.emit(m),
            on_batch_started=lambda t: self.batch_started.emit(t),
            on_progress=lambda c, t, f: self.progress_signal.emit(c, t, f),
            on_transcription_completed=lambda f, s: self.transcription_completed.emit(f, s),
            on_generation_completed=lambda f, s, m: self.generation_completed.emit(f, s, m),
            on_batch_summary=lambda s: self.batch_summary.emit(s),
            on_finished=lambda: self.finished.emit()
        )

        self._worker = BatchCaptionWorker(
            queue_items, settings, output_folder, transcript_folder,
            pairing_history, callbacks, max_words_per_segment
        )

    def start(self):
        self._worker.start()
```

#### Phase 3: Extract UI Components

Create `src/caption_generator/components/` directory:

**`drop_zone_component.py`** (already exists as `drop_zone.py` - refactor):
```python
class DropZoneComponent(QWidget):
    """Drag-drop zone for audio/SRT files."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.setAcceptDrops(True)
```

**`style_settings_component.py`**:
```python
@dataclass
class StyleSettings:
    font_name: str
    font_size: int
    text_color: str
    background_color: str
    transparent: bool
    all_caps: bool
    ignore_grammar: bool
    alignment: str  # "top", "center", "bottom"
    words_per_segment: int

class StyleSettingsComponent(QGroupBox):
    """Style configuration panel."""

    settings_changed = pyqtSignal(StyleSettings)

    def __init__(self, initial: StyleSettings, parent=None):
        super().__init__("Style Settings", parent)
        self._settings = initial
        self._setup_ui()

    def get_settings(self) -> StyleSettings:
        return StyleSettings(
            font_name=self.font_combo.currentText(),
            font_size=self.size_spin.value(),
            # ... extract all values
        )
```

**`video_settings_component.py`**:
```python
@dataclass
class VideoSettings:
    resolution: str  # "1920x1080", "1280x720", etc.
    fps: int

class VideoSettingsComponent(QGroupBox):
    """Video output settings panel."""

    def __init__(self, initial: VideoSettings, parent=None):
        super().__init__("Video Settings", parent)
        self._setup_ui(initial)

    def get_settings(self) -> VideoSettings:
        return VideoSettings(
            resolution=self.res_combo.currentText(),
            fps=self.fps_spin.value()
        )
```

**`queue_table_component.py`**:
```python
class QueueTableComponent(QWidget):
    """Processing queue table with actions."""

    srt_browse_requested = pyqtSignal(int)  # row
    srt_edit_requested = pyqtSignal(int)
    regenerate_requested = pyqtSignal(int)
    remove_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()

    def add_item(self, audio_path: str, srt_path: Optional[str],
                 needs_transcription: bool):
        """Add item to queue table."""
        pass

    def update_item_status(self, row: int, status: str, color: str):
        """Update status display for a row."""
        pass

    def clear(self):
        self.table.setRowCount(0)
```

#### Phase 4: Create Controller

Create `src/caption_generator/controller.py`:
```python
class CaptionGeneratorController:
    """
    Orchestrates caption generation operations.
    No PyQt5 imports - uses callbacks.
    """

    def __init__(self,
                 config,
                 pairing_history: PairingHistory,
                 callbacks: dict):
        self.config = config
        self.pairing_history = pairing_history
        self._callbacks = callbacks
        self._current_worker = None
        self._batch_worker = None
        self.queue: List[Dict] = []

    def add_to_queue(self, audio_path: str, srt_path: Optional[str] = None) -> Dict:
        """Add file to processing queue. Returns queue item dict."""
        needs_transcription = False

        if srt_path and os.path.exists(srt_path):
            # Manual SRT
            self.pairing_history.add_pairing(audio_path, srt_path, 'user_provided')
        else:
            # Check history
            pairing = self.pairing_history.find_pairing(audio_path)
            if pairing and pairing.get('srt_path') and os.path.exists(pairing['srt_path']):
                srt_path = pairing['srt_path']
            else:
                needs_transcription = True

        item = {
            'audio_path': audio_path,
            'srt_path': srt_path,
            'needs_transcription': needs_transcription
        }
        self.queue.append(item)
        return item

    def generate_single(self, srt_path: str, audio_path: str,
                       style_settings: StyleSettings,
                       video_settings: VideoSettings,
                       output_folder: str):
        """Start single video generation."""
        pass

    def generate_all(self, style_settings: StyleSettings,
                    video_settings: VideoSettings,
                    output_folder: str,
                    transcript_folder: str):
        """Start batch processing."""
        pass
```

### File Structure After Refactoring

```
src/caption_generator/
├── __init__.py
├── main.py
├── main_app.py                    # Slim UI assembly (~300 lines)
├── controller.py                  # Business logic orchestration
├── theme.py                       # Extracted theme/styling
├── workers/
│   ├── __init__.py
│   ├── base_worker.py             # Framework-agnostic base
│   ├── generation_worker.py       # Single video worker
│   └── batch_worker.py            # Batch processing worker
├── qt_adapters.py                 # Qt signal wrappers
├── components/
│   ├── __init__.py
│   ├── drop_zone_component.py
│   ├── style_settings_component.py
│   ├── video_settings_component.py
│   ├── queue_table_component.py
│   ├── output_component.py
│   └── log_component.py
├── config_manager.py              # (unchanged)
├── video_generator.py             # (unchanged - already decoupled)
├── pairing_history.py             # (unchanged)
├── srt_editor_dialog.py           # (minor refactor)
└── srt_data_model.py              # (unchanged)
```

---

## Plan 3: Snippet Remixer Module

**Current State**: Tkinter application with severe coupling
**Lines of Code**: ~2,345 in `main_app.py`
**Framework**: Tkinter + tkinterdnd2
**Coupling Level**: Severe - largest monolithic file

### Current Architecture Analysis

**Good Patterns (Keep)**:
- `VideoProcessor` class is mostly decoupled
- `ProcessingWorker` uses callback pattern (not Qt signals)
- `JobQueue` is pure Python with no UI dependencies

**Critical Coupling Issues**:
- 2,345 lines in single file mixing UI, state, and logic
- 80+ Tkinter variables (`StringVar`, `BooleanVar`, etc.)
- Complex tempo modulation UI tightly coupled to processing
- Theme styling inline (~200 lines)

### Refactoring Strategy

#### Phase 1: Extract Data Models

Create `src/snippet_remixer/models.py`:
```python
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

class LengthMode(Enum):
    SECONDS = "seconds"
    BPM = "bpm"

class BPMUnit(Enum):
    BEATS = "beats"
    BARS = "bars"

@dataclass
class RemixSettings:
    """All remix configuration in one place."""
    output_folder: str
    length_mode: LengthMode
    duration_seconds: float
    bpm: float
    bpm_unit: BPMUnit
    num_units: int
    aspect_ratio: str
    aspect_ratio_mode: str
    continuous_mode: bool
    mute_audio: bool

@dataclass
class TempoModSettings:
    """Tempo modulation configuration."""
    enabled: bool
    start_bpm: float
    end_bpm: float
    duration_seconds: float
    control_points: List[Tuple[float, float]] = field(default_factory=list)

@dataclass
class RemixerState:
    """Complete application state."""
    settings: RemixSettings
    tempo_mod: TempoModSettings
    input_files: List[str] = field(default_factory=list)
    is_processing: bool = False
    continuous_count: int = 0
```

#### Phase 2: Extract UI Components

Create `src/snippet_remixer/components/` directory:

**`input_section_component.py`**:
```python
class InputSectionComponent:
    """Input videos section with listbox and buttons."""

    def __init__(self, parent, on_files_changed: Callable[[List[str]], None]):
        self._on_files_changed = on_files_changed
        self._files: List[str] = []
        self._build_ui(parent)

    def _build_ui(self, parent):
        # Container with BEDROT styling
        container = tk.Frame(parent, bg='#121212')
        container.pack(fill=tk.X, pady=5)

        # Label
        label = tk.Label(container, text=" INPUT VIDEOS ",
                        bg='#121212', fg='#00ffff',
                        font=('Segoe UI', 10, 'bold'))
        label.pack(anchor='w', padx=15)

        # ... rest of UI construction

    def set_files(self, files: List[str]):
        self._files = list(files)
        self._refresh_display()

    def get_files(self) -> List[str]:
        return self._files.copy()
```

**`output_section_component.py`**:
```python
class OutputSectionComponent:
    """Output folder and aspect ratio settings."""

    def __init__(self, parent, initial_settings: RemixSettings,
                 on_settings_changed: Callable[[str, str, str], None]):
        # on_settings_changed(output_folder, aspect_ratio, aspect_mode)
        self._build_ui(parent, initial_settings)
```

**`length_control_component.py`**:
```python
class LengthControlComponent:
    """Length/BPM control section with mode switching."""

    def __init__(self, parent, initial_settings: RemixSettings,
                 on_mode_changed: Callable[[LengthMode], None],
                 on_settings_changed: Callable):
        self._build_ui(parent, initial_settings)

    def get_duration(self) -> float:
        """Calculate final duration based on mode."""
        if self._mode == LengthMode.SECONDS:
            return self._duration_seconds
        else:
            return self._calculate_bpm_duration()
```

**`tempo_mod_component.py`**:
```python
class TempoModComponent:
    """Tempo modulation control with graph canvas."""

    def __init__(self, parent, initial: TempoModSettings,
                 on_changed: Callable[[TempoModSettings], None]):
        self._settings = initial
        self._on_changed = on_changed
        self._build_ui(parent)

    def _build_canvas(self):
        """Build the tempo modulation graph canvas."""
        self.canvas = tk.Canvas(
            self._inner_frame,
            width=280, height=100,
            bg='#1a1a1a',
            highlightbackground='#404040',
            highlightthickness=1
        )
        # ... bindings and drawing

    def get_settings(self) -> TempoModSettings:
        return TempoModSettings(
            enabled=self._enabled_var.get(),
            start_bpm=float(self._start_var.get()),
            end_bpm=float(self._end_var.get()),
            duration_seconds=float(self._duration_var.get()),
            control_points=self._get_control_points()
        )
```

**`process_control_component.py`**:
```python
class ProcessControlComponent:
    """Process buttons and continuous mode toggle."""

    def __init__(self, parent,
                 on_generate: Callable,
                 on_stop: Callable,
                 on_continuous_toggle: Callable[[bool], None]):
        self._build_ui(parent)

    def set_processing_state(self, is_processing: bool, is_continuous: bool):
        """Update button states."""
        if is_processing:
            self._generate_btn.config(state=tk.DISABLED)
            self._stop_btn.config(state=tk.NORMAL)
        else:
            self._generate_btn.config(state=tk.NORMAL)
            self._stop_btn.config(state=tk.DISABLED)
```

**`status_section_component.py`**:
```python
class StatusSectionComponent:
    """Status bar, queue display, and log output."""

    def __init__(self, parent, colors: dict):
        self._build_ui(parent, colors)

    def set_status(self, message: str):
        self._status_var.set(message)

    def update_queue_display(self, queue_status: str):
        self._queue_label.config(text=queue_status)

    def log(self, message: str):
        self._log_text.insert(tk.END, message + "\n")
        self._log_text.see(tk.END)
```

#### Phase 3: Create Controller

Create `src/snippet_remixer/controller.py`:
```python
class SnippetRemixerController:
    """
    Orchestrates remix operations.
    No Tkinter imports.
    """

    def __init__(self,
                 config_manager: ConfigManager,
                 callbacks: dict):
        self.config = config_manager
        self._callbacks = callbacks
        self._worker = ProcessingWorker(
            config_manager.get_script_dir(),
            callbacks.get('video_filter')
        )
        self._state = RemixerState(...)
        self._job_queue = JobQueue(max_history=50)

    def set_input_files(self, files: List[str]):
        self._state.input_files = files

    def start_processing(self, settings: RemixSettings,
                         tempo_mod: TempoModSettings) -> bool:
        """Start remix generation."""
        if not self._state.input_files:
            return False

        # Build jobs
        jobs = self._build_jobs(settings, tempo_mod)

        if settings.continuous_mode:
            return self._start_continuous(jobs)
        else:
            return self._start_queue(jobs)

    def stop_processing(self):
        self._worker.abort_current_job()
        if self._state.settings.continuous_mode:
            self._stop_continuous()
```

#### Phase 4: Refactor Main Application

New `main_app.py` (~400 lines instead of 2,345):
```python
class VideoRemixerApp:
    """Main application - UI assembly only."""

    def __init__(self, root):
        self.root = root
        self.root.title("BEDROT SNIPPET REMIXER // CYBERCORE VIDEO MANIPULATION")

        # Apply theme
        self.colors = apply_bedrot_theme(root)

        # Load config and create controller
        self.config = ConfigManager()
        self.controller = SnippetRemixerController(
            config_manager=self.config,
            callbacks={
                'on_log': self._thread_safe_log,
                'on_status': self._thread_safe_status,
                'on_progress': self._thread_safe_progress,
                'on_complete': self._on_job_complete,
                'video_filter': self._setup_logging()
            }
        )

        # Build UI
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        initial = self._load_initial_state()

        # Input section
        self.input_section = InputSectionComponent(
            main_frame,
            on_files_changed=self.controller.set_input_files
        )

        # Output section
        self.output_section = OutputSectionComponent(
            main_frame,
            initial_settings=initial.settings,
            on_settings_changed=self._on_output_changed
        )

        # Length control
        self.length_control = LengthControlComponent(
            main_frame,
            initial_settings=initial.settings,
            on_mode_changed=self._on_length_mode_changed,
            on_settings_changed=self._on_length_changed
        )

        # Tempo modulation
        self.tempo_mod = TempoModComponent(
            main_frame,
            initial=initial.tempo_mod,
            on_changed=self._on_tempo_mod_changed
        )

        # Process control
        self.process_control = ProcessControlComponent(
            main_frame,
            on_generate=self._start_processing,
            on_stop=self._stop_processing,
            on_continuous_toggle=self._on_continuous_toggle
        )

        # Status section
        self.status_section = StatusSectionComponent(main_frame, self.colors)
```

### File Structure After Refactoring

```
src/snippet_remixer/
├── __init__.py
├── main.py
├── main_app.py                    # Slim UI assembly (~400 lines)
├── controller.py                  # Business logic orchestration
├── models.py                      # Data models and state
├── theme.py                       # Extracted theme
├── components/
│   ├── __init__.py
│   ├── input_section_component.py
│   ├── output_section_component.py
│   ├── length_control_component.py
│   ├── tempo_mod_component.py
│   ├── process_control_component.py
│   └── status_section_component.py
├── config_manager.py              # (unchanged)
├── processing_worker.py           # (unchanged - already decoupled)
├── video_processor.py             # (unchanged - already decoupled)
├── job_queue.py                   # (unchanged - already decoupled)
└── utils.py                       # (unchanged)
```

---

## Plan 4: Reel Tracker Module

**Current State**: PyQt5 application with high coupling
**Lines of Code**: ~2,655 in `main_app.py`
**Framework**: PyQt5
**Coupling Level**: High - large monolithic file with embedded dialogs

### Current Architecture Analysis

**Good Patterns (Keep)**:
- `file_organizer.py` has no UI dependencies
- `backup_manager.py` is pure Python
- Dialog classes are already separate files
- `CSVProtectionManager` is decoupled

**Coupling Issues**:
- 2,655 lines in main_app.py
- `DropdownDelegate` creates Qt widgets in business logic
- Theme inline (~400 lines)
- Table management mixed with data operations

### Refactoring Strategy

#### Phase 1: Extract Data Models

Create `src/reel_tracker/models.py`:
```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

@dataclass
class ReelEntry:
    """Single reel record."""
    reel_id: str
    persona: str
    release: str
    reel_type: str
    clip_filename: str
    caption: str
    aspect_ratio: str
    file_path: str

@dataclass
class TrackerState:
    """Application state."""
    csv_path: Optional[str] = None
    entries: List[ReelEntry] = field(default_factory=list)
    has_unsaved_changes: bool = False

    @property
    def columns(self) -> List[str]:
        return [
            "Reel ID", "Persona", "Release", "Reel Type",
            "Clip Filename", "Caption", "Aspect Ratio", "FilePath"
        ]
```

#### Phase 2: Create Service Layer

Create `src/reel_tracker/services/` directory:

**`csv_service.py`**:
```python
class CSVService:
    """CSV file operations - no Qt dependency."""

    def __init__(self, protection_manager: CSVProtectionManager,
                 backup_manager: Optional[BackupManager] = None):
        self._protection = protection_manager
        self._backup = backup_manager

    def load_csv(self, path: str) -> Tuple[List[ReelEntry], str]:
        """Load CSV and return entries with status message."""
        try:
            df = pd.read_csv(path, encoding='utf-8-sig')
            entries = [self._row_to_entry(row) for _, row in df.iterrows()]
            return entries, f"Loaded {len(entries)} entries"
        except Exception as e:
            return [], f"Error loading: {e}"

    def save_csv(self, entries: List[ReelEntry], path: str) -> Tuple[bool, str]:
        """Save entries to CSV with protection."""
        data = [self._entry_to_row(e) for e in entries]
        columns = ReelEntry.__dataclass_fields__.keys()
        return self._protection.safe_csv_write(data, columns, path, self._backup)
```

**`dropdown_service.py`**:
```python
class DropdownService:
    """Manages dropdown values - no Qt dependency."""

    def __init__(self, config_manager: ConfigManager):
        self._config = config_manager

    def get_values(self, dropdown_type: str) -> List[str]:
        return self._config.get_dropdown_values(dropdown_type)

    def add_value(self, dropdown_type: str, value: str) -> bool:
        if value and value.strip():
            return self._config.add_dropdown_value(dropdown_type, value.strip())
        return False
```

#### Phase 3: Extract UI Components

Create `src/reel_tracker/components/` directory:

**`reel_table_component.py`**:
```python
class ReelTableComponent(QWidget):
    """Main data table with dropdown delegates."""

    # Signals
    data_changed = pyqtSignal()
    row_selected = pyqtSignal(int)

    def __init__(self, columns: List[str],
                 dropdown_service: DropdownService,
                 parent=None):
        super().__init__(parent)
        self._columns = columns
        self._dropdown_service = dropdown_service
        self._setup_table()
        self._setup_delegates()

    def _setup_delegates(self):
        """Configure dropdown delegates for specific columns."""
        dropdown_columns = {
            "Persona": 1,
            "Release": 2,
            "Reel Type": 3,
            "Aspect Ratio": 6
        }
        for name, col in dropdown_columns.items():
            delegate = DropdownDelegate(self, name, self._dropdown_service)
            self.table.setItemDelegateForColumn(col, delegate)

    def load_entries(self, entries: List[ReelEntry]):
        """Populate table from entries."""
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._populate_row(row, entry)

    def get_entries(self) -> List[ReelEntry]:
        """Extract entries from table."""
        entries = []
        for row in range(self.table.rowCount()):
            entries.append(self._extract_row(row))
        return entries
```

**`toolbar_component.py`**:
```python
class ToolbarComponent(QWidget):
    """Action toolbar with buttons."""

    # Signals for actions
    load_requested = pyqtSignal()
    save_requested = pyqtSignal()
    add_reel_requested = pyqtSignal()
    bulk_edit_requested = pyqtSignal()
    randomizer_requested = pyqtSignal()
    organize_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Create buttons and connect to signals
        self.load_btn = self._create_button("Load CSV", self.load_requested)
        self.save_btn = self._create_button("Save", self.save_requested)
        # ... etc
```

**`status_bar_component.py`**:
```python
class StatusBarComponent(QStatusBar):
    """Enhanced status bar with auto-save indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def set_status(self, message: str, is_error: bool = False):
        color = "#ff0066" if is_error else "#00ff88"
        self._status_label.setStyleSheet(f"color: {color};")
        self._status_label.setText(message)

    def set_save_indicator(self, has_changes: bool):
        self._save_indicator.setVisible(has_changes)
```

#### Phase 4: Create Controller

Create `src/reel_tracker/controller.py`:
```python
class ReelTrackerController:
    """
    Orchestrates reel tracking operations.
    No PyQt5 imports.
    """

    def __init__(self,
                 config_manager: ConfigManager,
                 csv_service: CSVService,
                 dropdown_service: DropdownService,
                 callbacks: dict):
        self.config = config_manager
        self.csv_service = csv_service
        self.dropdown_service = dropdown_service
        self._callbacks = callbacks
        self._state = TrackerState()

    def load_csv(self, path: str) -> bool:
        """Load CSV file."""
        entries, message = self.csv_service.load_csv(path)
        if entries:
            self._state.csv_path = path
            self._state.entries = entries
            self._state.has_unsaved_changes = False
            self.config.set("last_csv_path", path)
            self._callbacks['on_entries_loaded'](entries)
            self._callbacks['on_status'](message)
            return True
        else:
            self._callbacks['on_error'](message)
            return False

    def save_csv(self, entries: List[ReelEntry]) -> bool:
        """Save current entries."""
        if not self._state.csv_path:
            return False

        success, message = self.csv_service.save_csv(
            entries, self._state.csv_path
        )
        if success:
            self._state.has_unsaved_changes = False
        self._callbacks['on_status'](message, not success)
        return success

    def add_reel(self, entry: ReelEntry):
        """Add new reel entry."""
        self._state.entries.append(entry)
        self._state.has_unsaved_changes = True
        self._callbacks['on_entry_added'](entry)

    def get_autofill_values(self) -> Dict[str, str]:
        """Get last-used values for autofill."""
        return self.config.get("last_autofill", {
            "Persona": "",
            "Release": "RENEGADE PIPELINE",
            "Reel Type": "",
            "Aspect Ratio": "9:16"
        })
```

#### Phase 5: Refactor Main Application

New `main_app.py` (~500 lines instead of 2,655):
```python
class ReelTrackerApp(QMainWindow):
    """Main application - UI assembly only."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BEDROT REEL TRACKER // CYBERCORE CONTENT MANAGEMENT")
        self.setGeometry(100, 100, 1600, 800)

        # Initialize services
        self.config = ConfigManager()
        self.csv_service = CSVService(
            CSVProtectionManager(),
            BackupManager(self.config)
        )
        self.dropdown_service = DropdownService(self.config)

        # Create controller
        self.controller = ReelTrackerController(
            config_manager=self.config,
            csv_service=self.csv_service,
            dropdown_service=self.dropdown_service,
            callbacks={
                'on_entries_loaded': self._on_entries_loaded,
                'on_entry_added': self._on_entry_added,
                'on_status': self._update_status,
                'on_error': self._show_error
            }
        )

        # Apply theme and build UI
        self._apply_theme()
        self._build_ui()

        # Auto-load last CSV
        self._auto_load_last_csv()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Toolbar
        self.toolbar = ToolbarComponent()
        self.toolbar.load_requested.connect(self._on_load_requested)
        self.toolbar.save_requested.connect(self._on_save_requested)
        # ... connect other signals
        layout.addWidget(self.toolbar)

        # Main table
        self.table = ReelTableComponent(
            columns=TrackerState().columns,
            dropdown_service=self.dropdown_service
        )
        self.table.data_changed.connect(self._on_data_changed)
        layout.addWidget(self.table)

        # Status bar
        self.status_bar = StatusBarComponent()
        self.setStatusBar(self.status_bar)
```

### File Structure After Refactoring

```
src/reel_tracker/
├── __init__.py
├── main.py
├── main_app.py                    # Slim UI assembly (~500 lines)
├── controller.py                  # Business logic orchestration
├── models.py                      # Data models
├── theme.py                       # Extracted theme
├── services/
│   ├── __init__.py
│   ├── csv_service.py
│   └── dropdown_service.py
├── components/
│   ├── __init__.py
│   ├── reel_table_component.py
│   ├── toolbar_component.py
│   └── status_bar_component.py
├── dialogs/                       # (existing, minor refactors)
│   ├── reel_dialog.py
│   ├── bulk_edit_dialog.py
│   ├── default_metadata_dialog.py
│   └── file_organization_dialog.py
├── config_manager.py              # (unchanged)
├── backup_manager.py              # (unchanged)
├── file_organizer.py              # (unchanged)
├── media_randomizer.py            # (unchanged)
└── utils.py                       # (unchanged)
```

---

## Plan 5: Transcriber Tool Module

**Current State**: PyQt5 application with severe coupling
**Lines of Code**: ~574 in `main_app.py`
**Framework**: PyQt5
**Coupling Level**: Severe - `Worker` inherits from `QThread`

### Current Architecture Analysis

**Good Patterns (Keep)**:
- `subtitle_generator.py` is pure Python
- Simple drag-drop interface
- Config manager pattern

**Coupling Issues**:
- `Worker(QThread)` - inherits from Qt class
- All signals defined on worker class
- Theme inline in main() function

### Refactoring Strategy

#### Phase 1: Create Framework-Agnostic Worker

Create `src/transcriber_tool/workers/transcription_worker.py`:
```python
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
import threading
import time

@dataclass
class TranscriptionCallbacks:
    on_log: Callable[[str], None]
    on_batch_started: Callable[[int], None]
    on_progress: Callable[[int, int, str], None]
    on_file_completed: Callable[[str, str], None]
    on_batch_summary: Callable[[Dict], None]
    on_finished: Callable[[], None]

@dataclass
class TranscriptionJob:
    file_path: str
    output_folder: str
    export_txt: bool = True
    export_srt: bool = False

class TranscriptionWorker:
    """
    Batch transcription worker - no Qt dependency.
    """

    def __init__(self, jobs: List[TranscriptionJob],
                 callbacks: TranscriptionCallbacks,
                 config: dict):
        self.jobs = jobs
        self.callbacks = callbacks
        self.config = config
        self._thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        self.stats = {
            'total_files': len(jobs),
            'successful_conversions': 0,
            'successful_transcriptions': 0,
            'conversion_failures': 0,
            'transcription_failures': 0,
            'skipped_files': 0,
            'start_time': None,
            'duration_seconds': 0
        }

    def start(self):
        self._cancel_requested = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel_requested = True

    def _run(self):
        self.stats['start_time'] = time.time()
        self.callbacks.on_batch_started(self.stats['total_files'])
        self.callbacks.on_log(f"[BATCH] Starting batch processing: {self.stats['total_files']} files")

        for index, job in enumerate(self.jobs, 1):
            if self._cancel_requested:
                break

            filename = os.path.basename(job.file_path)
            self.callbacks.on_progress(index, self.stats['total_files'], filename)
            self._process_file(job, index)

        # Calculate duration and emit summary
        self.stats['duration_seconds'] = time.time() - self.stats['start_time']
        self.callbacks.on_batch_summary(self.stats)
        self.callbacks.on_finished()

    def _process_file(self, job: TranscriptionJob, index: int):
        """Process single file - conversion + transcription."""
        filename = os.path.basename(job.file_path)

        # Convert to MP3
        mp3_path = self._convert_to_mp3(job.file_path)
        if not mp3_path:
            self.stats['conversion_failures'] += 1
            self.callbacks.on_file_completed(filename, "[FAILED] Conversion Failed")
            return

        self.stats['successful_conversions'] += 1

        # Transcribe
        transcription = self._transcribe_audio(mp3_path)
        if transcription is None:
            self.stats['transcription_failures'] += 1
            self.callbacks.on_file_completed(filename, "[FAILED] Transcription Failed")
            return

        self.stats['successful_transcriptions'] += 1

        # Save outputs
        self._save_outputs(job, transcription, filename)

    def _convert_to_mp3(self, input_path: str) -> Optional[str]:
        """Convert audio/video to MP3."""
        # Same logic as current Worker.convert_to_mp3
        pass

    def _transcribe_audio(self, mp3_path: str):
        """Transcribe using ElevenLabs API."""
        # Same logic as current Worker.transcribe_audio
        pass

    def _save_outputs(self, job: TranscriptionJob, transcription, filename: str):
        """Save TXT and/or SRT outputs."""
        pass
```

#### Phase 2: Create Qt Adapter

Create `src/transcriber_tool/qt_adapter.py`:
```python
from PyQt5.QtCore import QObject, pyqtSignal
from .workers.transcription_worker import TranscriptionWorker, TranscriptionCallbacks, TranscriptionJob

class QtTranscriptionWorker(QObject):
    """Qt signal wrapper for TranscriptionWorker."""

    log_signal = pyqtSignal(str)
    batch_started_signal = pyqtSignal(int)
    progress_signal = pyqtSignal(int, int, str)
    file_completed_signal = pyqtSignal(str, str)
    batch_summary_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, jobs: list, config: dict):
        super().__init__()

        callbacks = TranscriptionCallbacks(
            on_log=lambda m: self.log_signal.emit(m),
            on_batch_started=lambda t: self.batch_started_signal.emit(t),
            on_progress=lambda c, t, f: self.progress_signal.emit(c, t, f),
            on_file_completed=lambda f, s: self.file_completed_signal.emit(f, s),
            on_batch_summary=lambda s: self.batch_summary_signal.emit(s),
            on_finished=lambda: self.finished_signal.emit()
        )

        self._worker = TranscriptionWorker(jobs, callbacks, config)

    def start(self):
        self._worker.start()

    def cancel(self):
        self._worker.cancel()
```

#### Phase 3: Extract UI Components

Create `src/transcriber_tool/components/` directory:

**`drop_zone_component.py`**:
```python
class TranscriberDropZone(QWidget):
    """Drag-drop zone for audio/video files."""

    files_dropped = pyqtSignal(list)

    def __init__(self, supported_formats: List[str], parent=None):
        super().__init__(parent)
        self._formats = supported_formats
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel(
            "Drag and drop MP4/MP3/WAV/M4A/FLAC files here to transcribe."
        )
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()
                 if os.path.isfile(url.toLocalFile())]
        if files:
            self.files_dropped.emit(files)
```

**`output_settings_component.py`**:
```python
@dataclass
class OutputSettings:
    folder: str
    export_txt: bool
    export_srt: bool

class OutputSettingsComponent(QWidget):
    """Output folder and format selection."""

    settings_changed = pyqtSignal(OutputSettings)

    def __init__(self, initial: OutputSettings, parent=None):
        super().__init__(parent)
        self._setup_ui(initial)

    def get_settings(self) -> OutputSettings:
        return OutputSettings(
            folder=self.folder_line.text(),
            export_txt=self.txt_checkbox.isChecked(),
            export_srt=self.srt_checkbox.isChecked()
        )
```

**`log_component.py`**:
```python
class LogComponent(QTextEdit):
    """Read-only log output display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("font-family: Consolas; font-size: 10px;")

    def log(self, message: str):
        self.append(message)
```

#### Phase 4: Create Controller

Create `src/transcriber_tool/controller.py`:
```python
class TranscriberController:
    """
    Orchestrates transcription operations.
    No PyQt5 imports.
    """

    def __init__(self, config, callbacks: dict):
        self.config = config
        self._callbacks = callbacks
        self._worker = None

    def start_transcription(self, files: List[str],
                           output_settings: OutputSettings):
        """Start batch transcription."""
        jobs = [
            TranscriptionJob(
                file_path=f,
                output_folder=output_settings.folder,
                export_txt=output_settings.export_txt,
                export_srt=output_settings.export_srt
            )
            for f in files
        ]

        self._worker = TranscriptionWorker(
            jobs=jobs,
            callbacks=TranscriptionCallbacks(
                on_log=self._callbacks['on_log'],
                on_batch_started=self._callbacks['on_batch_started'],
                on_progress=self._callbacks['on_progress'],
                on_file_completed=self._callbacks['on_file_completed'],
                on_batch_summary=self._callbacks['on_batch_summary'],
                on_finished=self._callbacks['on_finished']
            ),
            config=self.config.config
        )
        self._worker.start()
```

#### Phase 5: Refactor Main Application

New `main_app.py` (~200 lines instead of 574):
```python
class TranscriberApp(QWidget):
    """Main transcriber application - UI assembly only."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriber Tool - Drag and Drop")
        self.resize(700, 500)

        # Initialize
        self.config = get_config()

        # Create controller
        self.controller = TranscriberController(
            config=self.config,
            callbacks={
                'on_log': self._on_log,
                'on_batch_started': self._on_batch_started,
                'on_progress': self._on_progress,
                'on_file_completed': self._on_file_completed,
                'on_batch_summary': self._on_batch_summary,
                'on_finished': self._on_finished
            }
        )

        # Build UI
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Drop zone
        self.drop_zone = TranscriberDropZone(
            supported_formats=[".mp3", ".mp4", ".wav", ".m4a", ".flac"]
        )
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_zone)

        # Output settings
        self.output_settings = OutputSettingsComponent(
            initial=OutputSettings(
                folder=self.config.get_output_folder(),
                export_txt=True,
                export_srt=True
            )
        )
        layout.addWidget(self.output_settings)

        # Log
        self.log = LogComponent()
        layout.addWidget(self.log)

        self.log.log("[TranscriberTool] Ready. Drag and drop files to begin.")

    def _on_files_dropped(self, files: List[str]):
        settings = self.output_settings.get_settings()
        self.controller.start_transcription(files, settings)
```

### File Structure After Refactoring

```
src/transcriber_tool/
├── __init__.py
├── main.py
├── main_app.py                    # Slim UI assembly (~200 lines)
├── controller.py                  # Business logic orchestration
├── theme.py                       # Extracted theme
├── workers/
│   ├── __init__.py
│   └── transcription_worker.py    # Framework-agnostic worker
├── qt_adapter.py                  # Qt signal wrapper
├── components/
│   ├── __init__.py
│   ├── drop_zone_component.py
│   ├── output_settings_component.py
│   └── log_component.py
├── config_manager.py              # (unchanged)
└── subtitle_generator.py          # (unchanged - already decoupled)
```

---

## Summary: Estimated Reduction in Coupling

| Module | Before (lines) | After (main_app) | Components | Reduction |
|--------|---------------|------------------|------------|-----------|
| Video Splitter | 608 | ~150 | 4 | 75% |
| Caption Generator | 1,229 | ~300 | 6 | 76% |
| Snippet Remixer | 2,345 | ~400 | 6 | 83% |
| Reel Tracker | 2,655 | ~500 | 3 | 81% |
| Transcriber Tool | 574 | ~200 | 3 | 65% |

### Key Benefits After Refactoring

1. **Testability**: Workers and controllers can be unit tested without UI frameworks
2. **Portability**: Backend logic can be reused with any frontend (web, CLI, etc.)
3. **Maintainability**: Smaller, focused files are easier to understand and modify
4. **Consistency**: All modules follow the same architectural pattern
5. **Reusability**: UI components can be shared across modules

### Implementation Priority

1. **Video Splitter** - Simplest, good template for others
2. **Transcriber Tool** - Small, demonstrates Qt adapter pattern
3. **Caption Generator** - Complex workers, validates batch pattern
4. **Reel Tracker** - Validates service layer pattern
5. **Snippet Remixer** - Most complex, benefits from patterns established in others
