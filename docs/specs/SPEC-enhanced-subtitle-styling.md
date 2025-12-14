# Enhanced Subtitle Styling Options - Implementation Specification

## 1. Feature Overview

### 1.1 Summary
Extend the Caption Generator's styling capabilities to include drop shadows, text effects, animation options, and a preset management system leveraging ASS (Advanced SubStation Alpha) subtitle format capabilities.

### 1.2 Goals
- Add configurable drop shadow styling (color, depth, opacity)
- Implement animation effects (fade-in, pop-in, karaoke highlighting)
- Create a style preset system for saving/loading custom configurations
- Maintain backward compatibility with existing workflow

### 1.3 Scope
- **In Scope**: Drop shadows, fade animations, karaoke effects, presets
- **Limited Support**: Text gradients (ASS has limited native support)
- **Out of Scope**: Complex vector animations, per-character transformations

---

## 2. Technical Approach - ASS/FFmpeg Capabilities

### 2.1 ASS Subtitle Format Capabilities

**Style Definition Fields:**
```
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour,
        BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment...
```

**Drop Shadow Support:**
- `Shadow` parameter: Float value (0-4 typical)
- `BackColour` / Shadow color: `&HAABBGGRR` format

**Animation Override Tags:**
- `\fad(fade_in_ms, fade_out_ms)` - Simple fade in/out
- `\fade(a1,a2,a3,t1,t2,t3,t4)` - Complex alpha animation
- `\t(t1,t2,\style)` - Transform effect over time
- `\k<duration>` - Karaoke (syllable highlight)
- `\kf<duration>` - Karaoke fill (smooth highlight)

### 2.2 Current Implementation

**video_generator.py (lines 189-198)** - Current force_style:
```python
force_style = (
    f"FontName={font_name},"
    f"FontSize={font_size},"
    f"PrimaryColour=&H{font_color_bgr},"
    f"Alignment={align_value},"
    f"BorderStyle=1,"
    f"Outline={outline_size},"
    f"Shadow=0"  # Currently hardcoded to 0
)
```

### 2.3 Proposed Architecture

**Recommended: Generate ASS files directly instead of SRT with force_style**
- More control over per-event animations
- Can use override tags in dialogue lines
- Leverages `pysubs2` library already in project

---

## 3. Files to Modify and Create

### 3.1 New Files to Create

| File | Purpose |
|------|---------|
| `src/caption_generator/style_models.py` | Dataclasses for SubtitleStyle, ShadowSettings, AnimationSettings |
| `src/caption_generator/ass_generator.py` | ASS file generation with advanced styling |
| `src/caption_generator/preset_manager.py` | Load/save/manage style presets |
| `src/caption_generator/style_widgets.py` | Reusable PyQt5 widgets for style configuration |
| `config/caption_style_presets.json` | Default and user presets storage |

### 3.2 Files to Modify

| File | Changes |
|------|---------|
| `src/caption_generator/main_app.py` | Add enhanced styling UI section, preset selector |
| `src/caption_generator/video_generator.py` | Replace SRT+force_style with ASS generation |
| `src/caption_generator/config_manager.py` | Add new config keys for shadows, animations |

---

## 4. Detailed Implementation Steps

### Phase 1: Core Style Models and ASS Generator

#### Step 1.1: Create style_models.py

```python
@dataclass
class ShadowSettings:
    enabled: bool = False
    depth: float = 2.0  # 0.0-4.0
    color: str = "#000000"
    alpha: int = 128  # 0-255

@dataclass
class AnimationSettings:
    effect_type: str = "none"  # "none", "fade", "pop", "karaoke", "karaoke_fill"
    fade_in_ms: int = 0
    fade_out_ms: int = 0
    karaoke_primary_color: str = "#ffffff"
    karaoke_secondary_color: str = "#00ffff"

@dataclass
class SubtitleStyle:
    name: str
    font_name: str = "Arial Narrow"
    font_size: int = 56
    font_color: str = "#ffffff"
    outline_color: str = "#000000"
    outline_size: float = 2
    alignment: str = "center"
    bold: bool = False
    italic: bool = False
    shadow: ShadowSettings = field(default_factory=ShadowSettings)
    animation: AnimationSettings = field(default_factory=AnimationSettings)

    def to_dict(self) -> dict: ...
    def from_dict(data: dict) -> 'SubtitleStyle': ...
    def to_ass_style_line(self) -> str: ...
```

#### Step 1.2: Create ass_generator.py

```python
def hex_to_ass_color(hex_color: str, alpha: int = 0) -> str:
    """Convert "#RRGGBB" to "&HAABBGGRR" format"""

def generate_ass_header(style: SubtitleStyle, resolution: str) -> str:
    """Create [Script Info] and [V4+ Styles] sections"""

def generate_ass_dialogue(index: int, start_ms: int, end_ms: int,
                          text: str, style: SubtitleStyle) -> str:
    """Create Dialogue line with override tags for animations"""

def apply_animation_tags(text: str, animation: AnimationSettings,
                         duration_ms: int) -> str:
    """Insert \fad, \k, \t tags based on animation settings"""

def srt_to_ass(srt_path: str, output_path: str, style: SubtitleStyle,
               text_transforms: dict) -> str:
    """Convert SRT file to ASS with full styling"""
```

#### Step 1.3: Modify video_generator.py

Replace subtitles filter with ASS filter:
```python
def build_ffmpeg_command(
    srt_path: str,
    audio_path: str,
    output_path: str,
    style: SubtitleStyle,  # New parameter type
    resolution: str,
    fps: int,
    transparent: bool = False
) -> list:
    # Generate ASS file from SRT
    ass_path = srt_to_ass(srt_path, temp_ass_path, style, transforms)
    # Use ass= filter instead of subtitles=
    "-vf", f"ass='{escaped_ass_path}'"
```

### Phase 2: Preset Management System

#### Step 2.1: Create preset_manager.py

```python
class PresetManager:
    def __init__(self, presets_file: str): ...
    def load_presets(self) -> Dict[str, SubtitleStyle]: ...
    def save_presets(self, presets: Dict[str, SubtitleStyle]): ...
    def get_preset(self, name: str) -> Optional[SubtitleStyle]: ...
    def save_preset(self, name: str, style: SubtitleStyle, overwrite: bool = False): ...
    def delete_preset(self, name: str): ...
    def get_preset_names(self) -> List[str]: ...
    def export_preset(self, name: str, file_path: str): ...
    def import_preset(self, file_path: str) -> str: ...
```

**Default Presets:**
- "Default" - White text, black outline, no effects
- "Social Media Bold" - Impact font, yellow, heavy shadow, pop effect
- "Karaoke" - Word-by-word highlighting with secondary color
- "Cinematic" - Fade in/out, subtle shadow
- "Minimal" - No outline, no shadow, clean look
- "High Contrast" - Large, bold, maximum readability

#### Step 2.2: Create config/caption_style_presets.json

```json
{
  "version": "1.0",
  "default_preset": "Default",
  "presets": {
    "Default": {
      "is_builtin": true,
      "style": {
        "font_name": "Arial Narrow",
        "font_size": 56,
        "font_color": "#ffffff",
        "shadow": { "enabled": false, "depth": 0 },
        "animation": { "effect_type": "none" }
      }
    },
    "Social Media Bold": {
      "is_builtin": true,
      "style": {
        "font_name": "Impact",
        "font_size": 64,
        "font_color": "#ffff00",
        "shadow": { "enabled": true, "depth": 3, "alpha": 180 },
        "animation": { "effect_type": "pop", "fade_in_ms": 100 }
      }
    }
  }
}
```

### Phase 3: UI Implementation

#### Step 3.1: Create style_widgets.py

```python
class ColorPickerButton(QPushButton):
    """Button that shows current color and opens color picker on click."""
    color_changed = pyqtSignal(str)

class ShadowSettingsWidget(QGroupBox):
    """Grouped controls for shadow configuration."""
    # QCheckBox: Enable shadow
    # QDoubleSpinBox: Shadow depth (0.0-4.0)
    # ColorPickerButton: Shadow color
    # QSlider: Shadow alpha (0-255)
    settings_changed = pyqtSignal(ShadowSettings)

class AnimationSettingsWidget(QGroupBox):
    """Controls for animation effects."""
    # QComboBox: Effect type
    # QSpinBox: Fade in/out duration
    # ColorPickerButton: Karaoke secondary color
    settings_changed = pyqtSignal(AnimationSettings)

class PresetSelectorWidget(QWidget):
    """Preset dropdown with save/load/delete buttons."""
    preset_selected = pyqtSignal(str)
    preset_saved = pyqtSignal(str, SubtitleStyle)
```

#### Step 3.2: Modify main_app.py - UI Changes

Add "Advanced Styling" group box after existing Style Settings:

```
"Advanced Styling" QGroupBox
├── Preset Row
│   ├── QLabel "Preset:"
│   ├── PresetSelectorWidget
│   └── [stretch]
│
├── Shadow Settings Row
│   ├── QCheckBox "Drop Shadow"
│   ├── QLabel "Depth:" + QDoubleSpinBox (0.0-4.0)
│   ├── QLabel "Color:" + ColorPickerButton
│   ├── QLabel "Opacity:" + QSlider (0-100%)
│
├── Animation Settings Row
│   ├── QLabel "Effect:" + QComboBox
│   ├── QLabel "Fade In:" + QSpinBox (ms)
│   ├── QLabel "Fade Out:" + QSpinBox (ms)
│
├── Karaoke Settings Row (shown only when karaoke selected)
│   ├── QLabel "Highlight Color:" + ColorPickerButton
│
└── Text Effects Row
    ├── QCheckBox "Bold"
    ├── QCheckBox "Italic"
```

---

## 5. UI/UX Design

### 5.1 Layout Mockup

```
┌─ Advanced Styling ──────────────────────────────────────────┐
│  Preset: [Social Media Bold ▼] [Save] [Delete] [Import]     │
│  ─────────────────────────────────────────────────────────  │
│  ☑ Drop Shadow                                              │
│    Depth: [2.0 ↕]  Color: [██] [Pick]  Opacity: [──●──] 80% │
│  ─────────────────────────────────────────────────────────  │
│  Animation Effect: [Fade In/Out ▼]                          │
│    Fade In: [200 ↕] ms    Fade Out: [100 ↕] ms             │
│  ─────────────────────────────────────────────────────────  │
│  Text Style: ☐ Bold  ☐ Italic                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Animation Effect Descriptions

| Effect | Description | ASS Implementation |
|--------|-------------|-------------------|
| None | Standard display | No override tags |
| Fade In/Out | Smooth opacity fade | `\fad(in_ms,out_ms)` |
| Pop In | Quick scale-up entrance | `\t(0,100,\fscx110\fscy110)\t(100,200,\fscx100\fscy100)` |
| Karaoke | Word highlight progression | `\k<duration>` per word |
| Karaoke Fill | Smooth fill highlight | `\kf<duration>` per word |

---

## 6. Style Preset System Design

### 6.1 Preset Storage Structure

```json
{
  "version": "1.0",
  "default_preset": "Default",
  "presets": {
    "Preset Name": {
      "is_builtin": false,
      "description": "User description",
      "created_at": "2025-12-14T10:30:00",
      "style": { ... }
    }
  }
}
```

### 6.2 Preset Import/Export
- **Export**: Single preset to standalone JSON file
- **Import**: Load preset from external JSON file, prompt on name conflict

---

## 7. Potential Challenges and Mitigations

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| No native gradient support | Can't do true gradients | Use karaoke mode with secondary color |
| Limited animation complexity | Can't do complex transforms | Stick to fade, scale, karaoke |
| Font availability | Fonts must exist on system | Add font validation, fallback to Arial |
| Per-word timing for karaoke | Requires word-level timestamps | Only enable karaoke when using transcription |
| Shadow blur | ASS shadow is hard-edged | Accept limitation, document in UI |

---

## 8. Testing Considerations

### Unit Tests
```python
class TestStyleModels:
    def test_shadow_settings_to_dict()
    def test_subtitle_style_to_ass_style_line()
    def test_subtitle_style_round_trip()

class TestASSGenerator:
    def test_hex_to_ass_color()
    def test_generate_ass_header()
    def test_generate_dialogue_with_fade()
    def test_srt_to_ass_with_shadow()

class TestPresetManager:
    def test_load_default_presets()
    def test_save_custom_preset()
    def test_cannot_delete_builtin_preset()
```

### Manual Testing Checklist
- [ ] Default preset generates video identical to current behavior
- [ ] Shadow renders correctly at various depths
- [ ] Fade in/out timing is accurate
- [ ] Karaoke highlighting works with word-level SRT
- [ ] Bold and italic render correctly
- [ ] Preset save/load preserves all settings
- [ ] Transparent WebM mode works with all effects

---

## 9. Critical Files

1. **`src/caption_generator/video_generator.py`** - Core FFmpeg command generation (lines 152-241)
2. **`src/caption_generator/main_app.py`** - Main UI; needs Advanced Styling section (after line 289)
3. **`src/caption_generator/config_manager.py`** - Configuration persistence (lines 27-55)
4. **`archive/mv_maker/video_processor.py`** - Reference ASS generation code (lines 46-127)
