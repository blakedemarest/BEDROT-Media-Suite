# Requirements Specification - Fix Cropping Issue with Aspect Ratio Handling

## Problem Statement

The Snippet Remixer module is introducing black bars (letterboxing/pillarboxing) when converting videos between different aspect ratios, particularly when converting 9:16 portrait videos to 1:1 square format. Despite a recent fix attempt that changed from padding to cropping, users are still experiencing black bars in their output videos.

## Solution Overview

Implement a robust aspect ratio management system that:
1. Always crops to fill the target frame (with user option to pad instead)
2. Verifies output dimensions to ensure no black bars
3. Provides clear logging for debugging
4. Fixes the confusing Height x Width notation
5. Removes tolerance checks that may skip necessary adjustments

## Functional Requirements

### FR1: Aspect Ratio Fill Modes
- Add a new user-selectable option: "Aspect Ratio Mode"
  - "Crop to Fill" (default) - Crops video to fill entire frame
  - "Pad to Fit" - Adds black bars to maintain original aspect ratio
- Store this preference in the configuration file
- Display option in the main UI, near the aspect ratio dropdown

### FR2: Proper Aspect Ratio Notation
- Change all aspect ratio displays from "Height x Width" to "Width x Height"
- Update ASPECT_RATIOS list in config_manager.py:
  - "1920x1080 (16:9 Landscape)" instead of "1080x1920 (9:16 Portrait)"
  - "1080x1920 (9:16 Portrait)" instead of "1920x1080 (16:9 Landscape)"
  - "1080x1080 (1:1 Square)" remains the same
- Ensure backward compatibility when loading old configs

### FR3: Output Verification
- After FFmpeg processing, verify the actual output dimensions
- Use ffprobe to check for black detect filter results
- Log warnings if output doesn't match expected dimensions
- Optionally re-process if black bars are detected

### FR4: Enhanced Logging
- Log source video dimensions and aspect ratio
- Log target dimensions and aspect ratio
- Log the FFmpeg filter chain being used
- Log the actual output dimensions achieved
- Include timestamp and video filename in logs

### FR5: Exact Aspect Ratio Matching
- Remove the 0.01 tolerance check in adjust_aspect_ratio
- Ensure exact aspect ratio calculations
- Use precise decimal calculations to avoid rounding errors

## Technical Requirements

### TR1: Update video_processor.py

1. **Modify cut_video_snippets method**:
   ```python
   # Add aspect_ratio_mode parameter
   def cut_video_snippets(self, ..., aspect_ratio_mode="crop"):
       # Apply appropriate filter based on mode
       if aspect_ratio_mode == "crop":
           vf_parts.append(f"scale={width}:{height}:force_original_aspect_ratio=increase")
           vf_parts.append(f"crop={width}:{height}")
       else:  # pad mode
           vf_parts.append(f"scale={width}:{height}:force_original_aspect_ratio=decrease")
           vf_parts.append(f"pad={width}:{height}:-1:-1:color=black")
   ```

2. **Update adjust_aspect_ratio method**:
   - Remove tolerance check
   - Add aspect_ratio_mode parameter
   - Implement proper crop/pad logic

3. **Add verify_output_dimensions method**:
   ```python
   def verify_output_dimensions(self, output_path, expected_width, expected_height):
       # Use ffprobe to get actual dimensions
       # Return (actual_width, actual_height, has_black_bars)
   ```

### TR2: Update config_manager.py

1. **Fix ASPECT_RATIOS list**:
   ```python
   ASPECT_RATIOS = [
       "Original",
       "1920x1080 (16:9 Landscape)",
       "1080x1920 (9:16 Portrait)",
       "1080x1080 (1:1 Square)",
       "1440x1080 (4:3 Classic)",
       "2560x1080 (21:9 Ultrawide)",
       "1920x817 (2.35:1 Cinema)",
       "1920x1038 (1.85:1 Film)"
   ]
   ```

2. **Add aspect_ratio_mode to config**:
   ```python
   "aspect_ratio_mode": "crop",  # or "pad"
   ```

### TR3: Update main_app.py UI

1. Add radio buttons or dropdown for aspect ratio mode
2. Position near the existing aspect ratio dropdown
3. Save/load the preference from config

### TR4: Logging Enhancements

1. Create a dedicated logging section in video_processor.py
2. Use consistent format: `[timestamp] [video_file] [dimension_info]`
3. Write logs to both console and optional log file

## Implementation Hints

### Parse Resolution Correctly
When parsing aspect ratios, ensure Width x Height order:
```python
if 'x' in aspect_ratio:
    parts = aspect_ratio.split('x')
    width = int(parts[0])
    height = int(parts[1].split()[0])  # Remove trailing text
```

### FFmpeg Filter Chains
For crop to fill:
```bash
-vf "scale=w=1080:h=1080:force_original_aspect_ratio=increase,crop=1080:1080"
```

For pad to fit:
```bash
-vf "scale=w=1080:h=1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black"
```

### Black Bar Detection
Use FFmpeg's blackdetect filter:
```bash
ffmpeg -i output.mp4 -vf "blackdetect=d=0.1:pix_th=0.10" -f null -
```

## Acceptance Criteria

1. ✓ When "Crop to Fill" is selected, no black bars appear in any aspect ratio conversion
2. ✓ When "Pad to Fit" is selected, black bars appear only as needed to preserve aspect ratio
3. ✓ Aspect ratios display in standard Width x Height format
4. ✓ Detailed logs show source, target, and actual dimensions
5. ✓ Output verification confirms no unexpected black bars
6. ✓ The fix works for all aspect ratio conversions, not just 9:16 to 1:1
7. ✓ Existing presets and configs continue to work (with auto-migration if needed)
8. ✓ User can easily switch between crop and pad modes

## Assumptions

1. FFmpeg and ffprobe are available in the system PATH
2. Users want crop to fill as the default behavior
3. The existing recent fix attempt needs refinement rather than complete replacement
4. Performance impact of output verification is acceptable
5. Users want detailed logging for troubleshooting

## Out of Scope

1. Adding more aspect ratio presets
2. Implementing smart crop detection (face/object detection)
3. Adding transition effects between snippets
4. GPU acceleration for processing
5. Batch processing improvements

## Risk Mitigation

1. **Backward Compatibility**: Detect old Height x Width format and auto-convert
2. **Performance**: Make output verification optional via config
3. **FFmpeg Versions**: Test with multiple FFmpeg versions
4. **Error Handling**: Gracefully handle verification failures