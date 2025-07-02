# Expert Detail Questions - Cropping Implementation

## Q6: Should we verify the actual output dimensions after FFmpeg processing to ensure no black bars were introduced?
**Default if unknown:** Yes (verification ensures the fix works correctly across all FFmpeg versions)

## Q7: Do you want to preserve the current "Height x Width" format in config_manager.py ASPECT_RATIOS list?
**Default if unknown:** No (industry standard is "Width x Height", changing would prevent confusion)

## Q8: Should the tolerance check (currently 0.01) in adjust_aspect_ratio be removed to ensure exact aspect ratio matching?
**Default if unknown:** Yes (exact matching prevents edge cases where slight mismatches introduce bars)

## Q9: Do you need the system to log detailed information about source and target dimensions for debugging?
**Default if unknown:** Yes (helps diagnose issues when they occur with specific video inputs)

## Q10: Should we add a user-visible option to choose between "crop to fill" and "pad with bars" behaviors?
**Default if unknown:** No (the requirement specifically asks to prevent black bars, so crop should be the only option)