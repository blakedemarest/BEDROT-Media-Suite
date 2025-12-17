# Snippet Remixer Crop Fix Documentation

## Problem Description

The video snippet remixer was introducing black bars (letterboxing/pillarboxing) when processing videos with different aspect ratios. This occurred because the FFmpeg filters were configured to:

1. Scale videos DOWN to fit within the target dimensions (`force_original_aspect_ratio=decrease`)
2. Add black padding to fill the remaining space

## Root Cause

In `video_processor.py`, the `cut_video_snippets` method was using:
```python
vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=decrease")
vf_parts.append(f"pad={resolution_str}:-1:-1:color=black")
```

This combination:
- Scales the video to fit INSIDE the target dimensions
- Preserves aspect ratio by making the video smaller
- Fills empty space with black bars

## Solution

Changed the approach to crop instead of pad:

### 1. In `cut_video_snippets` (lines 380-392):
```python
# Scale to fill frame (may overflow) then crop to exact size
# This ensures no black bars - the video fills the entire frame
vf_parts.append(f"scale={resolution_str}:force_original_aspect_ratio=increase")
vf_parts.append(f"crop={resolution_str}")
```

This:
- Scales the video to fill the ENTIRE target dimensions
- May cause overflow in one dimension to maintain aspect ratio
- Crops the overflow to get exact dimensions
- Results in a full-frame video with no black bars

### 2. In `adjust_aspect_ratio` (lines 541-547):
```python
# Always crop to target aspect ratio, never pad
if source_ar_val > target_ar_val:
    # Video is too wide, crop width
    ar_filter_vf = f"crop=w=ih*{target_ar_val:.4f}:h=ih"
else:
    # Video is too tall, crop height
    ar_filter_vf = f"crop=w=iw:h=iw/{target_ar_val:.4f}"
```

Previously, when video was too tall, it would add padding. Now it always crops.

## Visual Example

### Before (with black bars):
```
Original 16:9 video → Target 1:1
┌─────────────────┐
│  black bars     │
├─────────────────┤
│                 │
│   video content │
│                 │
├─────────────────┤
│  black bars     │
└─────────────────┘
```

### After (cropped):
```
Original 16:9 video → Target 1:1
┌─────────────────┐
│                 │
│   video fills   │
│  entire frame   │
│  (sides cropped)│
│                 │
└─────────────────┘
```

## Benefits

1. **No Black Bars**: Videos always fill the entire frame
2. **Professional Look**: Content appears full-screen without letterboxing
3. **Better for Social Media**: Platforms like Instagram/TikTok prefer full-frame content
4. **Consistent Output**: All snippets have the same visual style

## Considerations

- Some content from the edges may be cropped
- Important visual elements should be centered in source videos
- The crop is center-aligned by default
- Original videos are never modified - only the output is affected

## Testing

Run the test script to verify the fix:
```bash
python test_crop_fix.py
```

This creates test videos with different aspect ratios and verifies they're properly cropped without black bars.