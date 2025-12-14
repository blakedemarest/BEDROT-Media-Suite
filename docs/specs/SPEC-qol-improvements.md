# SRT Editor Quality of Life Improvements - Implementation Specification

## Executive Summary

Three quality of life improvements to the Caption Generator's SRT Editor:
1. **Undo/Redo Functionality** - Command pattern using PyQt5's QUndoStack
2. **Audio Playback During Editing** - PyQt5 multimedia with optional waveform
3. **Export to Multiple Formats** - ASS, JSON, and plain text export

---

## 1. Undo/Redo Functionality

### 1.1 Overview

Add comprehensive undo/redo support to track all editing operations in both the Word Editor and Raw SRT views. Users can undo/redo using keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z) and toolbar buttons.

### 1.2 Technical Approach: Command Pattern

**Recommendation: PyQt5's QUndoStack**

- PyQt5 provides built-in `QUndoStack` and `QUndoCommand` classes
- More memory efficient than full state snapshots
- Supports command merging for sequential edits
- Native integration with Qt's action system

### 1.3 New File: `src/caption_generator/undo_commands.py`

```python
class EditBlockCommand(QUndoCommand):
    """Undo/redo for single block text/timing edits"""
    def __init__(self, model, block_index, old_state, new_state): ...
    def undo(self): ...
    def redo(self): ...

class ApplyOffsetCommand(QUndoCommand):
    """Undo/redo for timing offset operations"""
    def __init__(self, model, offset_ms, affected_blocks): ...
    def undo(self): ...
    def redo(self): ...

class RawTextChangeCommand(QUndoCommand):
    """Undo/redo for raw text editor changes (with merging)"""
    def __init__(self, model, old_text, new_text): ...
    def mergeWith(self, other): ...  # Combine sequential character edits
    def id(self): return 1  # Enable merging
```

### 1.4 Files to Modify

| File | Changes |
|------|---------|
| `srt_editor_dialog.py` | Add QUndoStack, undo/redo buttons, keyboard shortcuts |
| `srt_data_model.py` | Add `get_state()` and `set_state()` methods |
| `word_editor_view.py` | Emit command signals instead of direct model updates |

### 1.5 Implementation Steps

1. **Create undo_commands.py module:**
   - Define command classes inheriting from `QUndoCommand`
   - Implement EditBlockCommand, ApplyOffsetCommand, RawTextChangeCommand

2. **Modify SRTDataModel:**
   - Add `get_block_state(index)` -> returns dict of block properties
   - Add `set_block_state(index, state_dict)` -> restores block from dict

3. **Modify SRTEditorDialog:**
   - Add `self.undo_stack = QUndoStack(self)` in `__init__`
   - Add undo/redo buttons to header area
   - Create `QAction` for Ctrl+Z and Ctrl+Shift+Z
   - Connect stack signals to button enable states

4. **Modify WordEditorView:**
   - Change `_on_edit_block()` to emit signal with old/new values
   - Add signal: `edit_command_requested = pyqtSignal(int, dict, dict)`

### 1.6 UI Design

```
┌─────────────────────────────────────────────────────────┐
│ [↶ Undo] [↷ Redo]    Timing Offset: [0 ↕] ms [Apply]   │
└─────────────────────────────────────────────────────────┘
```

- Buttons disabled when stack is empty
- Window title asterisk (*) based on undo stack clean state
- Brief status message on undo/redo

### 1.7 Challenges and Mitigations

| Challenge | Mitigation |
|-----------|------------|
| View synchronization after undo | Always refresh both views after undo/redo |
| Raw text command merging | Use Qt's `mergeWith()` with timer-based finalization |
| Large files causing memory issues | Limit undo stack to 100 commands |

---

## 2. Audio Playback During Editing

### 2.1 Overview

Play associated audio file while editing subtitles to verify timing accuracy. Playback position syncs with selected subtitle blocks, with optional waveform visualization.

### 2.2 Technical Approach: QMediaPlayer

**Recommendation: QMediaPlayer with QAudioOutput**

| Option | Pros | Cons |
|--------|------|------|
| QMediaPlayer | Native Qt, seeking support | Requires QAudioOutput setup |
| QSound | Simple | No seeking, no position tracking |
| pydub + pyaudio | Already available | Threading complexity |

### 2.3 New File: `src/caption_generator/audio_player_widget.py`

```python
class AudioPlayerWidget(QWidget):
    """Main player control widget"""
    def __init__(self, parent=None): ...
    def set_audio_file(self, path: str): ...
    def play(self): ...
    def pause(self): ...
    def seek_to_ms(self, position_ms: int): ...
    def set_loop_range(self, start_ms: int, end_ms: int): ...

    # Signals
    position_changed = pyqtSignal(int)  # ms
    playback_state_changed = pyqtSignal(bool)  # playing

class WaveformWidget(QWidget):
    """Optional waveform visualization"""
    def __init__(self, parent=None): ...
    def load_audio(self, path: str): ...  # Background thread
    def set_position(self, position_ms: int): ...
    def highlight_region(self, start_ms: int, end_ms: int): ...

    # Signals
    seek_requested = pyqtSignal(int)  # Click to seek
```

### 2.4 Files to Modify

| File | Changes |
|------|---------|
| `srt_editor_dialog.py` | Add audio player widget, connect block selection to seek |
| `word_editor_view.py` | Add signal for block selection |
| `main_app.py` | Pass audio_path to SRTEditorDialog |

### 2.5 Implementation Steps

1. **Create audio_player_widget.py:**
   - Implement `AudioPlayerWidget` with QMediaPlayer
   - Add playback controls (play, pause, seek slider)
   - Add `seek_to_ms()` method for external control

2. **Create WaveformWidget (optional phase 2):**
   - Background thread generates waveform data using pydub/numpy
   - Custom `paintEvent()` draws waveform
   - Click handler for seek-to-position

3. **Modify SRTEditorDialog:**
   - Accept optional `audio_path` parameter
   - Add collapsible audio player section
   - Connect block selection to audio seek

4. **Modify WordEditorView:**
   - Add `block_selected = pyqtSignal(int, int, int)` (index, start_ms, end_ms)
   - Emit on block click

### 2.6 UI Design

```
┌─────────────────────────────────────────────────────────┐
│ [▶/⏸]  [◄◄] [►►]  │▬▬▬▬▬▬▬●▬▬▬▬▬▬▬│  01:23 / 03:45  │
│ [🔊───●──]  [🔁 Loop Block]                             │
├─────────────────────────────────────────────────────────┤
│ ▁▂▃▄█▇▅▃▂▁▂▄▆█▇▅▄▃▂▁  (waveform - optional)           │
└─────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click subtitle block -> audio seeks to block start
- Double-click -> opens edit dialog (existing)
- "Loop Block" checkbox loops selected block's time range
- Waveform click seeks to position

### 2.7 Dependencies

```
PyQt5.QtMultimedia  # Part of PyQt5
numpy               # Already in requirements.txt
```

### 2.8 Challenges and Mitigations

| Challenge | Mitigation |
|-----------|------------|
| Audio codec compatibility | Use QMediaPlayer's format detection; show warning if unsupported |
| Large files slow to load | Load asynchronously, show loading indicator |
| Waveform generation slow | Generate in background QThread, show placeholder |
| No associated audio file | Show "No Audio" state, disable controls |

---

## 3. Export to Other Formats

### 3.1 Overview

Export SRT content in additional formats:
- **ASS (Advanced SubStation Alpha)** - For advanced styling
- **JSON** - For programmatic access
- **Plain Text** - For transcripts without timing

### 3.2 Technical Approach: pysubs2

**Use pysubs2 library (already in requirements.txt)**
- Native SRT, ASS, SSA, JSON support
- Already used in lyric_video_uploader module

### 3.3 Format Specifications

#### ASS Format
```ass
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ...
Style: Default,Arial,48,&H00FFFFFF,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,First subtitle line
```

#### JSON Schema
```json
{
  "version": "1.0",
  "source_file": "example.srt",
  "export_date": "2025-01-15T12:30:00Z",
  "total_entries": 42,
  "entries": [
    {
      "index": 1,
      "start_ms": 1000,
      "end_ms": 4000,
      "text": "First subtitle line",
      "word_count": 3
    }
  ],
  "metadata": {
    "total_word_count": 176
  }
}
```

#### Plain Text
```
First subtitle line
Second subtitle line
Third subtitle line

---
Transcript exported from BEDROT Caption Generator
```

### 3.4 New File: `src/caption_generator/export_formats.py`

```python
class ASSExporter:
    """Export to ASS format with style options"""
    def __init__(self, style_options: dict = None): ...
    def export(self, model: SRTDataModel, output_path: str): ...

class JSONExporter:
    """Export to structured JSON"""
    def __init__(self, include_metadata: bool = True, pretty: bool = True): ...
    def export(self, model: SRTDataModel, output_path: str): ...

class PlainTextExporter:
    """Export transcript without timing"""
    def __init__(self, include_timestamps: bool = False,
                 include_line_numbers: bool = False): ...
    def export(self, model: SRTDataModel, output_path: str): ...

class ExportOptionsDialog(QDialog):
    """Dialog for format-specific settings"""
    def __init__(self, parent=None): ...
```

### 3.5 Files to Modify

| File | Changes |
|------|---------|
| `srt_editor_dialog.py` | Add "Export As..." button, connect to dialog |
| `srt_data_model.py` | Add `to_ass()`, `to_json()`, `to_plain_text()` methods |

### 3.6 Implementation Steps

1. **Create export_formats.py module:**
   - Implement ASSExporter using pysubs2
   - Implement JSONExporter with schema
   - Implement PlainTextExporter
   - Create ExportOptionsDialog with tabbed interface

2. **Modify SRTDataModel:**
   - Add `to_ass(options: dict) -> str`
   - Add `to_json(options: dict) -> str`
   - Add `to_plain_text(options: dict) -> str`

3. **Modify SRTEditorDialog:**
   - Add "Export As..." button before Save
   - Open ExportOptionsDialog on click

### 3.7 UI Design

**Export Button Placement:**
```
┌─────────────────────────────────────────────────────────┐
│                  [EXPORT AS...]  [SAVE]  [CANCEL]       │
└─────────────────────────────────────────────────────────┘
```

**Export Options Dialog:**
```
┌─ Export Options ─────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [ASS] [JSON] [Plain Text]                            │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ ASS Settings:                                        │ │
│ │   Font: [Arial        ▼]  Size: [48    ]            │ │
│ │   Text Color: [#ffffff] [Pick]                       │ │
│ │   Alignment: (●) Center  ( ) Top  ( ) Bottom        │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Output File: [________________________] [Browse...]     │
│                                                          │
│              [Preview]          [Export]  [Cancel]       │
└──────────────────────────────────────────────────────────┘
```

### 3.8 Dependencies

**Existing (no new installs):**
- `pysubs2` - Already in requirements.txt
- `json`, `datetime` - Python standard library

### 3.9 Challenges and Mitigations

| Challenge | Mitigation |
|-----------|------------|
| ASS style compatibility | Use standard V4+ format; test with VLC, mpv |
| Special characters in text | pysubs2 handles escaping |
| File overwrite | Show confirmation if file exists |

---

## 4. Integration and Sequencing

### 4.1 Recommended Order

1. **Phase 1: Undo/Redo** (Foundation)
   - Required for safe editing workflows
   - Enables confident experimentation

2. **Phase 2: Export Formats** (Low Risk)
   - Self-contained feature
   - Uses proven pysubs2 library

3. **Phase 3: Audio Playback** (Most Complex)
   - Requires multimedia integration
   - Waveform is optional enhancement

### 4.2 New Files Summary

| File | Purpose |
|------|---------|
| `undo_commands.py` | QUndoCommand implementations |
| `audio_player_widget.py` | Audio playback controls and waveform |
| `export_formats.py` | ASS/JSON/PlainText exporters |

### 4.3 Shared Modifications

| File | Features |
|------|----------|
| `srt_editor_dialog.py` | All three features |
| `srt_data_model.py` | Undo/Redo, Export |
| `word_editor_view.py` | Undo/Redo, Audio Playback |
| `main_app.py` | Audio Playback |

---

## 5. Testing Summary

### Unit Tests
- Undo/redo command cycles
- Export format validation
- Audio player state management

### Integration Tests
- Edit in Word view, switch to Raw, undo, verify state
- Export ASS, verify plays in VLC
- Audio sync with subtitle selection

### Manual Testing
- [ ] Ctrl+Z/Ctrl+Shift+Z shortcuts work
- [ ] Undo 50+ operations successfully
- [ ] Export to all three formats
- [ ] Audio plays with various formats
- [ ] Block selection seeks audio correctly

---

## 6. Critical Files

1. **`src/caption_generator/srt_editor_dialog.py`** - Central hub for all three features
2. **`src/caption_generator/srt_data_model.py`** - Needs state serialization and export methods
3. **`src/caption_generator/word_editor_view.py`** - Needs signal changes for undo and audio sync
4. **`src/lyric_video_uploader/timing/alignment.py`** - Reference for pysubs2 usage
5. **`src/caption_generator/video_generator.py`** - Reference for ASS alignment values
