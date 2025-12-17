# Release Calendar Module

A comprehensive music release management system integrated into the Bedrot Media Suite. This module provides visual scheduling, deliverable tracking, and multi-artist coordination for music releases.

## Features

### Visual Calendar Interface
- **Interactive Calendar Grid**: Monthly view with drag-and-drop release rescheduling
- **Friday Highlighting**: Industry-standard release days are visually emphasized
- **Release Cards**: Visual cards showing artist emoji, title, and progress indicators
- **Deadline Badges**: Color-coded badges for upcoming deliverables

### Multi-Artist Support
- **Artist Profiles**: Manage multiple artists with custom emojis and genres
- **Conflict Detection**: Automatic detection of releases scheduled too close together
- **Waterfall Strategy**: 8 singles, 1 EP, 1 album per artist per year

### Comprehensive Checklist System
- **9+ Deliverables per Release**: Track everything from mastering to marketing
- **Status Tracking**: Visual indicators for complete, pending, and overdue tasks
- **Progress Monitoring**: Real-time progress bars and completion percentages
- **Custom Notes**: Add notes to individual deliverables

### Data Management
- **Automatic Backups**: Timestamped backups created on each save
- **JSON Data Storage**: Human-readable data format
- **Export Options**: Excel and iCal export capabilities

## Technical Details

### Dependencies
This module requires PyQt6, which is separate from the PyQt5 used by other modules:
```bash
pip install PyQt6==6.6.1
```

### Architecture
- **Modular Design**: Follows the media suite's modular architecture patterns
- **Configuration-Driven**: JSON-based configuration for flexibility
- **Event-Driven**: Uses Qt signals/slots for responsive UI

### File Structure
```
release_calendar/
├── __init__.py           # Package exports
├── main_app.py          # Main PyQt6 application
├── config_manager.py    # Configuration handling
├── calendar_logic.py    # Core business logic
├── data_manager.py      # Data persistence
├── visual_calendar.py   # Visual calendar widget
├── checklist_dialog.py  # Checklist management dialog
├── utils.py            # Utility functions
└── README.md           # This file
```

## Configuration

The module uses `config/release_calendar_config.json` for configuration:

```json
{
    "artists": {
        "ZONE A0": {
            "emoji": "[CD]",
            "genre": "Electronic/Experimental",
            "singles_per_year": 8,
            "ep_per_year": 1,
            "album_per_year": 1
        }
    },
    "deliverables": {
        "single": {
            "distributor_submission": -21,
            "final_master": -21,
            "album_artwork": -21,
            "spotify_canvas": -21,
            "reels_124": -14,
            "carousel_posts_25": -14,
            "music_video": -7,
            "ad_creatives_5": -3,
            "release_day_campaign": 0
        }
    }
}
```

## Usage

### From Media Suite Launcher
1. Open the Media Suite launcher
2. Click on the "Release Calendar" tab
3. Click "Run" to start the module

### Standalone Launch
```bash
python src/release_calendar_modular.py
```

### Key Workflows

#### Adding a Release
1. Click "+ Add Release" or use the "Add Release" tab
2. Select artist, enter title, choose type
3. Set release date (defaults to 3 weeks out)
4. Add optional notes
5. Click "Add Release"

#### Managing Checklists
1. Double-click any release or click "Edit Checklist"
2. Check off completed items
3. Add notes to deliverables
4. Monitor progress and due dates

#### Rescheduling Releases
1. In the visual calendar, drag a release card
2. Drop it on a new date
3. Checklist due dates automatically adjust

## Integration Notes

### PyQt Version Compatibility
This module uses PyQt6 while other media suite modules use PyQt5. Both can coexist when run as separate processes through the launcher.

### Data Persistence
- Calendar data is stored in `config/calendar_data.json`
- Automatic backups are created in `config/backups/`
- Data is saved automatically on changes

### Performance Considerations
- Efficient rendering for hundreds of releases
- Lazy loading of checklist dialogs
- Optimized date calculations

## Future Enhancements
- Integration with streaming platform APIs
- Automated social media scheduling
- Revenue tracking integration
- Mobile companion app support