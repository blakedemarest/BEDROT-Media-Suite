# Reel Tracker - Aspect Ratio Scanning Guide

## Overview

The Reel Tracker now includes automatic aspect ratio detection that scans actual video files to determine their true dimensions, rather than making assumptions based on filenames.

## How to Scan Existing Rows

### Method 1: Scan All Rows (via Button)

1. **Open Reel Tracker** with your CSV loaded
2. Click the **[SCAN] Aspect Ratios** button in the toolbar
3. Confirm when prompted (scanning 686 files may take a few minutes)
4. Watch the progress bar in the status bar
5. Review the results summary showing:
   - Files scanned
   - Success/failure counts
   - Rows updated
   - Success rate percentage

### Method 2: Scan All Rows (via Menu)

1. Go to **Tools** menu
2. Select **Scan Video Aspect Ratios**
3. Follow the same process as above

### Method 3: Scan Selected Rows Only

1. Select specific rows in the table (click and drag or Ctrl+click)
2. Go to **Tools** menu
3. Select **Refresh Selected Aspect Ratios**
4. Only the selected rows will be scanned

## Automatic Detection for New Files

When you drag and drop new video files into Reel Tracker:
- The aspect ratio is **automatically detected** using FFprobe
- No manual intervention needed
- If detection fails, defaults to "9:16" (standard reel format)

## Aspect Ratio Values

The scanner detects and categorizes videos into canonical aspect ratios:

| Aspect Ratio | Description | Common Use |
|-------------|-------------|------------|
| **9:16** | Portrait/Vertical | Reels, Shorts, TikTok, Stories |
| **16:9** | Landscape/Horizontal | YouTube, traditional video |
| **1:1** | Square | Instagram posts, some social media |
| **4:5** | Portrait | Instagram feed posts |
| **5:4** | Alternative landscape | Less common |
| **4:3** | Traditional TV | Older content |
| **3:4** | Alternative portrait | Less common |
| **21:9** | Ultrawide | Cinematic content |
| **2:3** | Portrait | Photography aspect |
| **unknown** | Cannot determine | File inaccessible or not a video |

## How It Works

1. **FFprobe Integration**: Uses FFprobe to read actual video dimensions
2. **Tolerance Matching**: Matches to nearest canonical ratio (5% tolerance)
3. **Fallback Logic**: If exact match not found, shows simplified ratio (e.g., "17:10")
4. **Error Handling**: Gracefully handles missing/inaccessible files

## Performance

- **Speed**: ~1-2 seconds per video file
- **686 files**: Approximately 10-15 minutes for full scan
- **Progress**: Real-time progress bar shows scanning status
- **Auto-save**: Changes are automatically saved after scanning

## Troubleshooting

### "Scanner Not Found" Warning
The advanced scanner module isn't loaded, but basic FFprobe scanning still works.

### Files Show "unknown"
- File doesn't exist at the specified path
- File is corrupted or not a valid video
- FFprobe is not installed or not in PATH

### All Files Show "9:16"
- This is the default fallback if scanning fails
- Check that FFprobe is installed: `ffprobe -version`
- Verify file paths are correct and accessible

### Scan Takes Too Long
- Scan selected rows instead of all rows
- Files on network drives scan slower than local files
- Close other applications to free up resources

## Manual Override

You can still manually edit aspect ratios:
1. Click on any cell in the "Aspect Ratio" column
2. Select from dropdown or type custom value
3. Changes are saved automatically

## Benefits

- **Accurate Categorization**: Know exactly which videos are square, landscape, or portrait
- **Content Planning**: Better organize content by actual format
- **Platform Optimization**: Match content to platform requirements
- **Inventory Management**: True picture of your content library's format distribution

## Technical Details

- **No File Modification**: Scanning only reads video metadata, never modifies files
- **Cached Results**: Once scanned, values are stored in CSV
- **Idempotent**: Running scan multiple times is safe
- **Backup System**: Original CSV is backed up before any changes

## Integration with File Organization

When using the "Organize Files" feature:
- Aspect ratio information is preserved
- Can be used in future updates for aspect-ratio-based organization
- Helps identify content suitable for different platforms

## Future Enhancements

Planned improvements:
- Batch export by aspect ratio
- Filter/sort by aspect ratio
- Platform-specific export (e.g., export all 9:16 for TikTok)
- Aspect ratio statistics and reporting
- Thumbnail previews showing aspect ratio visually