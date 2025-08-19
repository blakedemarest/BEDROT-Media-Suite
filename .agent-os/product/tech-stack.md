# Tech Stack

## Current Implementation

### GUI Frameworks
- **Launcher**: Tkinter 8.6+ with tkinterdnd2
- **Main Tools**: PyQt5 5.15+
- **Release Calendar**: PyQt6 6.5+
- **Styling**: BEDROT cyberpunk theme (custom CSS/QSS)

### Video Processing
- **Core Engine**: MoviePy 1.0.3+
- **Transcoding**: FFmpeg 6.0+
- **Download**: yt-dlp (latest)
- **Formats**: MP4, MOV, AVI, MKV, WebM
- **Codecs**: H.264, H.265, VP9, AV1

### Image Processing
- **Library**: Pillow 10.0+
- **Scaling**: Custom bicubic algorithms
- **Effects**: PhotoMosh integration
- **Formats**: PNG, JPG, WebP, GIF, TIFF
- **Optimization**: pngquant, mozjpeg

### Audio Processing
- **Core**: pydub 0.25+
- **Speech Recognition**: SpeechRecognition 3.10+
- **Formats**: MP3, WAV, FLAC, OGG, M4A
- **Captions**: WebVTT, SRT, ASS
- **Effects**: Sox integration

### AI Integration
- **TTS/SFX**: ElevenLabs API (in progress)
- **Transcription**: OpenAI Whisper (planned)
- **Enhancement**: Real-ESRGAN (planned)

### Data Management
- **Configuration**: JSON with schema validation
- **Database**: CSV files (current), SQLite (planned)
- **Caching**: File-based with TTL
- **Backup**: Automated with versioning

### Development Tools
- **Python**: 3.11+ with type hints
- **Virtual Environment**: .venv standard
- **Package Management**: pip with requirements.txt
- **Testing**: pytest 7.4+
- **Linting**: flake8, black, mypy

### Platform Support
- **Primary**: Windows 11
- **Secondary**: Windows 10, WSL2
- **Future**: macOS, Linux

### Process Management
- **Launcher**: multiprocessing module
- **IPC**: Queue and Pipe objects
- **Logging**: Python logging with rotation
- **Monitoring**: psutil for resource tracking

## Architecture Patterns

### Modular Design
```
bedrot-media-suite/
├── launcher.py          # Central control
├── src/
│   ├── core/           # Shared utilities
│   └── [tool_name]/    # Isolated tools
└── config/             # Centralized config
```

### Process Isolation
- Each tool runs in separate process
- No shared memory between tools
- Clean shutdown handling
- Resource cleanup on exit

### Configuration Management
```python
{
  "tool_name": {
    "version": "1.0.0",
    "settings": {},
    "presets": [],
    "paths": {}
  }
}
```

## Planned Upgrades

### Q1 2025
- PyQt6 standardization
- SQLite for metadata
- Redis for caching
- Celery for task queue

### Q2 2025
- FastAPI backend
- WebSocket real-time updates
- Docker containerization
- CI/CD pipeline

### Q3 2025
- Kubernetes orchestration
- S3-compatible storage
- CDN for media delivery
- GraphQL API

### Q4 2025
- React Native mobile app
- Electron desktop wrapper
- WebAssembly modules
- Edge computing

## Technology Decisions

### Why Mixed PyQt5/PyQt6?
- **Historical**: Tools developed at different times
- **Compatibility**: Some libraries only support PyQt5
- **Migration**: Planned consolidation to PyQt6
- **Isolation**: Process separation prevents conflicts

### Why Tkinter for Launcher?
- **Simplicity**: Minimal dependencies
- **Stability**: Mature and reliable
- **Performance**: Lightweight for control UI
- **Built-in**: No additional installation

### Why MoviePy + FFmpeg?
- **MoviePy**: Pythonic interface for editing
- **FFmpeg**: Industry standard for transcoding
- **Flexibility**: Handles any format
- **Performance**: Hardware acceleration support

### Why CSV/JSON Storage?
- **Simplicity**: Human-readable formats
- **Portability**: No database server needed
- **Version Control**: Git-friendly
- **Migration Path**: Easy to convert to DB

## Development Standards

### Code Organization
- One tool per directory
- Shared code in core/
- Configuration separate from code
- Clear entry points

### Error Handling
- Graceful degradation
- User-friendly messages
- Automatic retry logic
- Comprehensive logging

### Performance Guidelines
- Lazy loading for large files
- Streaming for video processing
- Batch operations where possible
- Memory-mapped files for large datasets

### Testing Strategy
- Unit tests for core logic
- Integration tests for workflows
- Performance benchmarks
- User acceptance testing

## Security Considerations

### API Keys
- Stored in .env files
- Never committed to git
- Encrypted in memory
- Rotation schedule

### File Access
- Sandboxed operations
- Path validation
- Size limits enforced
- Malware scanning

### Network Security
- HTTPS only for APIs
- Certificate validation
- Rate limiting
- Request signing