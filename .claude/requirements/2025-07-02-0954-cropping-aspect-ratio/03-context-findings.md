# Context Findings - Video Processing and Aspect Ratio Implementation

## Current Implementation Analysis

### Files Analyzed
1. `src/snippet_remixer/video_processor.py` - Core video processing logic
2. `src/snippet_remixer/config_manager.py` - Configuration and aspect ratio definitions
3. `src/snippet_remixer/CLAUDE.md` - Module documentation

### Key Findings

#### 1. Recent Fix Already Applied
The codebase shows evidence that a fix was recently implemented:
- **Lines 388-392** in `video_processor.py`: Changed from padding to cropping approach
- Uses `force_original_aspect_ratio=increase` followed by crop filter
- This should theoretically prevent black bars

#### 2. Two-Stage Aspect Ratio Processing
The system applies aspect ratio adjustments at two points:

**Stage 1: During snippet cutting** (lines 388-392)
```python
vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=increase")
vf_parts.append(f"crop={resolution_str}")
```

**Stage 2: Final adjustment** (lines 541-547)
```python
if source_ar_val > target_ar_val:
    # Video is too wide, crop width
    ar_filter_vf = f"crop=w=ih*{target_ar_val:.4f}:h=ih"
else:
    # Video is too tall, crop height
    ar_filter_vf = f"crop=w=iw:h=iw/{target_ar_val:.4f}"
```

#### 3. Aspect Ratio Format
- Uses "Height x Width" format (e.g., "1080x1080")
- This is reversed from typical "Width x Height" convention
- May cause confusion in aspect ratio calculations

#### 4. Resolution String Parsing
The system parses aspect ratio strings to extract dimensions:
```python
# From config_manager.py
if 'x' in aspect_ratio:
    parts = aspect_ratio.split('x')
    height = int(parts[0])
    width = int(parts[1].split()[0])  # Remove any trailing text
```

### Potential Issues Identified

1. **Height x Width Format Confusion**
   - The unconventional format may lead to calculation errors
   - Example: "1080x1920" is labeled as 9:16 Portrait but reads as height x width

2. **Double Processing**
   - Aspect ratio adjustments happen twice in the pipeline
   - This could potentially reintroduce issues if not properly coordinated

3. **Tolerance Check**
   - Uses a tolerance of 0.01 for aspect ratio comparison
   - May skip necessary adjustments for near-matches

4. **Intermediate File Format**
   - Uses .ts format for concatenation
   - These files might not preserve aspect ratio metadata correctly

### Technical Constraints

1. **FFmpeg Version Dependency**
   - Different FFmpeg versions may handle filters differently
   - No version checking in the code

2. **No Validation of Filter Results**
   - The code assumes FFmpeg filters work correctly
   - No verification that output matches expected dimensions

### Similar Features in Codebase

1. **Random Slideshow Module**
   - Also handles aspect ratios but uses MoviePy
   - Has its own aspect ratio management system

2. **Slideshow Editor (tools/)**
   - Separate implementation with different approach
   - May have solved similar issues differently

### Integration Points

1. **Config System**
   - Centralized configuration in `config/video_remixer_settings.json`
   - Aspect ratio is saved/loaded with other settings

2. **Export Settings Dialog**
   - Allows custom resolution input
   - May override aspect ratio presets

3. **Progress Callbacks**
   - Updates UI during processing
   - Could be used to report actual dimensions achieved