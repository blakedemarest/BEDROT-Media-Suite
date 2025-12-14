# Caption Generator Preview Functionality - Implementation Specification

## 1. Overview

### 1.1 Feature Summary
Add the ability for users to preview how captions will appear on the video **before** generating the full video. This feature will:

- Display a real-time preview of the audio with caption overlay
- Synchronize captions to audio playback based on SRT timing
- Show accurate visual representation of font, color, size, position, and alignment settings
- Allow users to scrub through the audio timeline
- Support both single-file preview and queue item preview

### 1.2 User Value
- **Time savings**: Users can verify caption appearance without waiting for full video generation
- **Iterative refinement**: Easily adjust styles and timing before committing to render
- **Error prevention**: Catch timing mismatches or style issues before wasting processing time

---

## 2. Technical Approach

### 2.1 Options Considered

| Approach | Pros | Cons | Complexity |
|----------|------|------|------------|
| **A. Port LivePreviewWidget** | Existing tested code, full video support, caption overlay ready | Need to adapt to caption_generator settings model | Medium |
| **B. New QMediaPlayer + QPainter overlay** | Clean implementation, tailored to caption_generator | More development work | Medium-High |
| **C. FFmpeg frame extraction + QLabel** | Works for still frames, no multimedia deps | No audio playback, choppy scrubbing | Low-Medium |

### 2.2 Recommended Approach: Hybrid A + B

**Port and adapt the `LivePreviewWidget` from `archive/mv_maker/live_preview_widget.py`** with modifications:

1. **Reuse `CaptionOverlay` class** - The existing overlay rendering code handles fonts, colors, shadows, and positioning well
2. **Adapt `LivePreviewWidget`** - Modify to work with SRT timing data and caption generator settings
3. **Add SRT synchronization** - Create a new `CaptionSyncController` to update captions based on audio position
4. **Integrate into main_app.py** - Add as either a dialog or collapsible panel

---

## 3. Files to Modify and Create

### 3.1 New Files to Create

| File | Purpose |
|------|---------|
| `src/caption_generator/preview_widget.py` | Main preview widget with audio player and caption overlay |
| `src/caption_generator/caption_sync.py` | Controller class for synchronizing SRT timing with audio position |
| `src/caption_generator/preview_dialog.py` | Modal dialog wrapper for preview functionality |

### 3.2 Files to Modify

| File | Changes |
|------|---------|
| `src/caption_generator/main_app.py` | Add "Preview" button, integrate preview dialog launch |
| `src/caption_generator/config_manager.py` | Add preview-related settings (last preview position, etc.) |
| `src/caption_generator/srt_data_model.py` | Add helper method for finding caption at timestamp |

---

## 4. Detailed Implementation Steps

### Phase 1: Core Preview Infrastructure

#### Step 1.1: Create `caption_sync.py`

**Key Classes:**
- `CaptionSyncController` - Manages caption state based on audio position
  - `__init__(self, model: SRTDataModel)` - Initialize with SRT data
  - `get_caption_at_time(self, position_ms: int) -> Optional[WordBlock]` - Get active caption
  - `get_next_caption_time(self, position_ms: int) -> Optional[int]` - For efficient updates
  - `preload_timing_index()` - Build binary search index for large SRT files

**Algorithm for `get_caption_at_time`:**
```python
def get_caption_at_time(self, position_ms: int) -> Optional[WordBlock]:
    for block in self.model.blocks:
        if block.start_ms <= position_ms <= block.end_ms:
            return block
    return None
```

For large files, use binary search on a pre-sorted index.

#### Step 1.2: Create `preview_widget.py`

**Key Classes:**

1. **`CaptionPreviewOverlay(QWidget)`** - Adapted from archive/mv_maker
   - Renders caption text with configurable styling
   - Properties: font_name, font_size, font_color, bg_color, alignment, position
   - `paintEvent()` - Draws caption with background box, shadow, outline

2. **`PreviewWidget(QWidget)`** - Main preview container
   - Contains QMediaPlayer for audio playback
   - Renders solid/transparent background (matching video settings)
   - Hosts CaptionPreviewOverlay

   **Methods:**
   - `load_audio(self, audio_path: str)`
   - `load_srt(self, srt_path: str)`
   - `apply_style_settings(self, settings: Dict)`
   - `play()`, `pause()`, `seek(position_ms: int)`
   - `_on_position_changed(self, position)` - Updates caption overlay

#### Step 1.3: Create `preview_dialog.py`

**UI Layout:**
```
+--------------------------------------------------+
|  CAPTION PREVIEW                            [X]  |
+--------------------------------------------------+
|  +-----------------------------------------+     |
|  |                                         |     |
|  |        [Preview Area with              |     |
|  |         Caption Overlay]               |     |
|  |                                         |     |
|  +-----------------------------------------+     |
|                                                  |
|  [|<]  [<<]  [>PLAY]  [>>]  [>|]     00:15/03:24|
|  [===================================|----]      |
|                                                  |
|  +---------------+  +-------------------------+  |
|  | Style Preview |  |  Current Caption:       |  |
|  | Font: Arial   |  |  "Hello world"          |  |
|  | Size: 56px    |  |  00:14.500 -> 00:15.200 |  |
|  +---------------+  +-------------------------+  |
|                                                  |
|       [EDIT SETTINGS]    [CLOSE]                 |
+--------------------------------------------------+
```

### Phase 2: Integration with Main Application

#### Step 2.1: Modify `main_app.py`

**Add UI Elements:**

1. Add "PREVIEW" button next to "GENERATE VIDEO" button (around line 383):
```python
self.preview_btn = QPushButton("PREVIEW")
self.preview_btn.setStyleSheet("""
    QPushButton {
        background-color: #00ccff;
        color: #000000;
        font-size: 14px;
        font-weight: bold;
        padding: 12px;
        border: none;
        border-radius: 4px;
    }
    QPushButton:hover { background-color: #00aadd; }
    QPushButton:disabled { background-color: #404040; color: #808080; }
""")
self.preview_btn.clicked.connect(self._preview_captions)
btn_layout.addWidget(self.preview_btn)
```

2. Add preview method:
```python
def _preview_captions(self):
    """Open caption preview dialog for currently selected files."""
    srt_path = self.srt_input.text().strip()
    audio_path = self.audio_input.text().strip()

    if not srt_path or not os.path.exists(srt_path):
        QMessageBox.warning(self, "Missing SRT", "Please select an SRT file first.")
        return
    if not audio_path or not os.path.exists(audio_path):
        QMessageBox.warning(self, "Missing Audio", "Please select an audio file first.")
        return

    settings = self._get_settings()
    from .preview_dialog import PreviewDialog
    dialog = PreviewDialog(audio_path, srt_path, settings, self)
    dialog.exec_()
```

3. Add preview button to queue table actions
4. Add queue item preview method

#### Step 2.2: Modify `srt_data_model.py`

Add helper methods for caption lookup:
```python
def get_block_at_time(self, position_ms: int) -> Optional[WordBlock]:
    """Find the word block active at a given timestamp."""
    for block in self.blocks:
        if block.start_ms <= position_ms <= block.end_ms:
            return block
    return None
```

### Phase 3: Enhanced Features

- Text Transform Preview (ALL CAPS, punctuation removal)
- Resolution-Aware Preview (scale to match aspect ratio)
- Timeline Caption Markers (visual markers on slider)

---

## 5. UI/UX Design Considerations

### 5.1 Preview Area
- **Background**: Match the selected background color or show transparency grid for WebM mode
- **Aspect Ratio**: Maintain configured aspect ratio (16:9, 9:16, 4:3, 1:1)
- **Caption Rendering**: Match FFmpeg subtitles filter appearance as closely as possible

### 5.2 Controls
- **Transport**: Standard media player controls (Play/Pause/Seek)
- **Keyboard shortcuts**: Space=Play/Pause, Left/Right=Seek, Home/End=Jump
- **Timestamp display**: Show current position and total duration

### 5.3 Theme Consistency
Match BEDROT dark theme:
```python
BG_PRIMARY = "#121212"
BG_SECONDARY = "#1a1a1a"
ACCENT_CYAN = "#00ffff"
ACCENT_GREEN = "#00ff88"
TEXT_PRIMARY = "#e0e0e0"
BORDER = "#404040"
```

---

## 6. Dependencies

### Required (Already in requirements.txt)
- `PyQt5` - Core UI framework
- `PyQt5-sip` - PyQt5 bindings
- `pysrt` - SRT file parsing

### May Need Verification
```bash
pip install PyQt5-multimedia
```

---

## 7. Potential Challenges and Mitigations

| Challenge | Mitigation |
|-----------|------------|
| Font rendering differs from FFmpeg | Document differences; use similar fonts; add disclaimer |
| Audio format support varies by platform | Convert unsupported formats to MP3 using pydub |
| Large SRT files slow lookup | Use binary search index for O(log n) lookup |
| Position/size accuracy | Use same alignment logic as video_generator.py |
| Transparent background preview | Show checkerboard pattern for transparency |

---

## 8. Testing Considerations

### Unit Tests
- `test_caption_sync_basic` - Verify caption lookup at exact timestamps
- `test_caption_sync_boundaries` - Test edge cases (before first, after last)
- `test_text_transform_all_caps` - Verify ALL CAPS transformation
- `test_style_mapping` - Verify settings dict maps correctly to overlay

### Manual Testing Checklist
- [ ] Preview opens from manual file selection
- [ ] Preview opens from queue item
- [ ] Play/Pause works correctly
- [ ] Captions appear at correct times
- [ ] Text transforms apply correctly
- [ ] Font/size/color match settings
- [ ] Alignment displays correctly
- [ ] Works with various audio formats
- [ ] Handles missing/corrupt files gracefully

---

## 9. Critical Files

1. `src/caption_generator/main_app.py` - Main UI integration (lines 336-385 for button layout)
2. `src/caption_generator/srt_data_model.py` - Add `get_block_at_time()` helper
3. `archive/mv_maker/live_preview_widget.py` - Reference implementation to port
4. `src/caption_generator/video_generator.py` - Reference for alignment and style mapping
