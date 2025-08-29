# BEDROT Media Suite

## Product Overview

A comprehensive desktop application suite for automated media content creation, processing, and management tailored for BEDROT PRODUCTIONS' multi-platform content strategy across TikTok, Instagram, YouTube, and other social platforms.

## Core Value Proposition

Automates the entire media production pipeline from raw footage to platform-optimized content, reducing production time by 90% while maintaining the distinctive BEDROT cyberpunk aesthetic.

## Target Users

- **Primary**: Blake Demarest (ZONE A0, PIG1987, DEEPCURSE content creation)
- **Secondary**: BEDROT PRODUCTIONS team members handling visual content
- **Future**: Content creators seeking industrial/cyberpunk media automation

## Key Features

### Already Implemented ✅

#### Central Launcher System
- Tkinter-based tabbed interface managing all tools
- Real-time process monitoring and logging
- Resource management and cleanup
- Tool isolation with separate process execution

#### Media Processing Tools
- **Media Downloader**: YouTube/platform downloader with format conversion
- **Snippet Remixer**: BPM-synced video remixing from random snippets
- **Random Slideshow Generator**: Automated slideshow creation (16:9, 9:16)
- **MV Maker**: AI-powered captions with live preview
- **Reel Tracker**: Advanced CSV-based content management system

#### Visual Production Features
- BEDROT cyberpunk UI theme across all tools
- Batch processing with configurable presets
- Aspect ratio optimization (16:9, 9:16, 1:1)
- PhotoMosh integration for glitch effects
- Drag-and-drop interfaces with tkinterdnd2

#### Release Management
- **Release Calendar**: PyQt6 visual scheduling for music releases
- Drag-and-drop event management
- Multi-artist support (ZONE A0, PIG1987, DEEPCURSE)
- Export to multiple formats

### Planned Features
- ElevenLabs AI audio generation integration
- Automated social media posting
- Template-based content generation
- Cross-platform synchronization
- Cloud storage integration
- Mobile companion app

## Success Metrics

- Content production time: < 5 minutes per piece
- Batch processing: 100+ items without crashes
- Tool startup time: < 3 seconds
- Memory usage: < 2GB per tool
- Export quality: Lossless where possible

## Technical Architecture

- **GUI Frameworks**: Tkinter (launcher), PyQt5/6 (tools)
- **Video Processing**: MoviePy, FFmpeg, yt-dlp
- **Image Processing**: Pillow with custom scaling
- **Audio**: pydub, SpeechRecognition, WebVTT
- **Configuration**: JSON-based with .env support
- **Process Management**: Multiprocessing with isolation

## Business Context

Critical infrastructure for BEDROT PRODUCTIONS' content strategy, supporting:
- Weekly wallpaper drops (Tuesday: ZONE A0, Friday: PIG1987)
- TikTok/Instagram reel production
- YouTube video creation
- Visual assets for 100M+ streams goal by 2030