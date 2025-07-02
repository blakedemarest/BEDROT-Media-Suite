# Expert Detail Answers - Cropping Implementation

## Q6: Should we verify the actual output dimensions after FFmpeg processing to ensure no black bars were introduced?
**Answer:** Yes

## Q7: Do you want to preserve the current "Height x Width" format in config_manager.py ASPECT_RATIOS list?
**Answer:** No

## Q8: Should the tolerance check (currently 0.01) in adjust_aspect_ratio be removed to ensure exact aspect ratio matching?
**Answer:** Yes

## Q9: Do you need the system to log detailed information about source and target dimensions for debugging?
**Answer:** Yes

## Q10: Should we add a user-visible option to choose between "crop to fill" and "pad with bars" behaviors?
**Answer:** Yes, crop to fill should be selected by default