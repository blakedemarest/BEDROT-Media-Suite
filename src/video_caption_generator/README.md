# Video & Audio Caption Generator

An advanced AI-powered tool for generating time-synchronized captions for videos and audio files with real-time preview, professional styling options, and MP4 output with burned-in captions. Features ElevenLabs' state-of-the-art speech recognition API with fallback support for OpenAI's Whisper model.

## Features

### Core Transcription Features
- **ElevenLabs Integration**: Primary transcription using ElevenLabs' Scribe v1 model
- **Multi-Speaker Support**: Accurately transcribes up to 32 speakers with diarization
- **Audio Event Detection**: Tags non-speech sounds like (laughter), (applause), etc.
- **High Accuracy**: Best-in-class transcription accuracy across 99 languages
- **Multiple Language Support**: Auto-detects language or allows manual selection
- **Time-Synchronized Captions**: Generates properly timed captions with word-level precision
- **Whisper Fallback**: Local transcription option when API is unavailable

### Enhanced UI and Real-Time Features
- **Real-Time Caption Preview**: Live preview with instant updates as you change settings
- **Split-Panel Interface**: Video preview on left, controls on right
- **Professional Fonts**: Arial, Helvetica, Verdana, Roboto, Open Sans, and Impact
- **Color Wheel Interface**: Advanced HSV color selection with opacity control
- **Click-to-Position**: Click anywhere on the preview to position captions
- **Advanced Positioning**: X/Y sliders, text alignment (left/center/right)
- **Drag & Drop Support**: Drag media files directly onto the application

### Audio and Video Support
- **Video Formats**: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V
- **Audio Formats**: MP3, WAV, FLAC, M4A, AAC, OGG, WMA
- **Audio-to-Video Generation**: Automatically creates video from audio files
- **Multiple Aspect Ratios**: 16:9, 9:16 (vertical), 1:1 (square), 4:3
- **Resolution Options**: 720p, 1080p, 4K
- **Background Options**: Solid color, gradient, image, or waveform

### Output Formats
- **SRT (SubRip)**: Universal subtitle format
- **WebVTT**: Web-friendly format with styling support
- **Simple Format**: [MM:SS] timestamp format for easy reading
- **MP4 with Captions**: Video file with permanently burned-in captions
- **JSON**: Detailed transcription data for custom processing
- **HTML Preview**: Interactive preview with video player

### Additional Features
- **Batch Processing**: Process multiple videos and audio files at once
- **Customizable Styling**: Real-time preview of all style changes
- **Cross-Platform Font Support**: Intelligent font fallback system
- **Configuration Templates**: Save and load caption style presets

## Requirements

### System Requirements
- Python 3.8+
- FFmpeg (must be installed and in PATH)
- 4GB RAM minimum (8GB+ recommended for larger models)
- GPU with CUDA support (optional, for acceleration)

### Python Dependencies
```bash
# Core dependencies
pip install requests ffmpeg-python moviepy pydub
pip install pysrt webvtt-py PyQt5 pandas numpy python-dotenv

# Optional: For Whisper fallback support
# pip install openai-whisper torch torchaudio
```

### API Requirements
- **ElevenLabs API Key**: Required for transcription
  - Sign up at https://elevenlabs.io
  - Get your API key from the profile settings
  - Set as environment variable: `ELEVENLABS_API_KEY`

## Installation

1. Ensure FFmpeg is installed:
   ```bash
   # Windows: Download from https://ffmpeg.org/download.html
   # Linux: sudo apt install ffmpeg
   # Mac: brew install ffmpeg
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your ElevenLabs API key:
   ```bash
   # Windows
   set ELEVENLABS_API_KEY=your_api_key_here
   
   # Linux/Mac
   export ELEVENLABS_API_KEY=your_api_key_here
   
   # Or add to .env file
   echo "ELEVENLABS_API_KEY=your_api_key_here" >> .env
   ```

4. The tool is integrated with the Bedrot Media Suite launcher

## Usage

### Via Launcher
1. Run `launcher.py` or `start_launcher.bat`
2. Navigate to the "Caption Generator" tab
3. Click "Run Caption Generator"

### Standalone
```bash
python src/video_caption_generator/main_app.py
```

### Basic Workflow
1. Ensure your ElevenLabs API key is configured
2. Add a media file by either:
   - **Drag & Drop**: Drag a video or audio file directly onto the application window
   - **Browse**: Click the Browse button to select a file
3. Select language or use auto-detect
4. Click "Generate Captions"
5. Find generated files in the same directory as the media file

### Batch Processing
1. Click "Batch Process"
2. Select a directory containing video files
3. Choose which videos to process
4. Captions will be generated for all selected videos

## Transcription Services

### ElevenLabs (Primary)
- **Scribe v1**: Production model with high accuracy
- **Scribe v1 Experimental**: Latest features, may be unstable
- Supports files up to 1GB and 4.5 hours duration
- Cloud-based processing (no local resources needed)

### Whisper (Fallback)
If ElevenLabs is unavailable, the tool can fall back to local Whisper:
- **tiny**: ~39MB, fastest, lowest accuracy
- **base**: ~74MB, good balance
- **small**: ~244MB, better accuracy
- **medium**: ~769MB, high accuracy
- **large**: ~1550MB, best accuracy, slowest

## Configuration

Settings are stored in `config/video_caption_generator_config.json`

### Key Settings:
- `transcription_service`: Choose between 'elevenlabs' or 'whisper'
- `elevenlabs_api_key`: Your ElevenLabs API key
- `elevenlabs_model`: 'scribe_v1' or 'scribe_v1_experimental'
- `diarize_speakers`: Enable speaker identification (default: true)
- `audio_events`: Tag non-speech sounds (default: false)
- `language`: Default language (auto for detection)
- `caption_max_length`: Maximum characters per line (default: 42)
- `caption_max_duration`: Maximum caption display time (default: 7.0 seconds)
- `output_formats`: List of formats to generate (includes 'mp4' for video output)

### New Styling Settings:
- `font_family`: Choose from 'arial', 'helvetica', 'verdana', 'roboto', 'open_sans', 'impact'
- `font_size`: Caption font size in pixels (12-72)
- `font_color`: Hex color code for caption text
- `background_color`: Hex color code for caption background
- `background_opacity`: Background transparency (0.0-1.0)
- `position_x`: Horizontal position (0-100%)
- `position_y`: Vertical position (0-100%)
- `text_align`: Text alignment ('left', 'center', 'right')
- `aspect_ratio`: Video aspect ratio for audio files ('16:9', '9:16', '1:1', '4:3')
- `video_resolution`: Output resolution ('720p', '1080p', '4k')
- `background_type`: Background for audio files ('solid', 'gradient', 'image')

### Environment Variables:
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (required)
- `ELEVENLABS_MODEL`: Override ElevenLabs model selection
- `CAPTION_TRANSCRIPTION_SERVICE`: Choose service ('elevenlabs' or 'whisper')
- `CAPTION_OUTPUT_DIR`: Default output directory
- `CAPTION_LANGUAGE`: Default language
- `CAPTION_WHISPER_MODEL`: Whisper model for fallback
- `CAPTION_DEVICE`: Device for Whisper fallback (cpu/cuda)
- `CAPTION_FONT_FAMILY`: Default font family
- `CAPTION_FONT_SIZE`: Default font size
- `CAPTION_POSITION_X`: Default X position (0-100)
- `CAPTION_POSITION_Y`: Default Y position (0-100)
- `CAPTION_ASPECT_RATIO`: Default aspect ratio for audio-to-video
- `CAPTION_VIDEO_RESOLUTION`: Default video resolution

## Output Files

For a media file named `example.mp4` or `example.wav`, the tool generates:

- `example.srt` - Standard subtitle file
- `example.vtt` - WebVTT with styling
- `example.txt` - Simple format with [MM:SS] timestamps
- `example_captioned.mp4` - Video with burned-in captions (NEW)
- `example.json` - Detailed transcription data (optional)
- `example_preview.html` - Interactive preview (optional)

For audio files (MP3, WAV), the tool automatically:
1. Generates a video with your chosen background
2. Burns the captions into the video
3. Outputs an MP4 file ready for upload

## Performance Tips

1. **ElevenLabs Processing**: Cloud-based, no local GPU needed
2. **Concurrent Processing**: ElevenLabs supports high concurrency
3. **Long Files**: Files over 8 minutes are processed in parallel
4. **Batch Processing**: Efficient for multiple files
5. **Network Speed**: Ensure stable internet for API calls

## Troubleshooting

### "FFmpeg not found"
- Ensure FFmpeg is installed and in system PATH
- Restart the application after installing FFmpeg

### "ElevenLabs API error"
- Check your API key is valid
- Verify you have API credits remaining
- Check internet connection
- File size must be under 1GB

### "No audio detected"
- Verify the video has an audio track
- Check the video file isn't corrupted

### Slow processing
- Check internet connection speed
- Large files take longer to upload
- Consider splitting very long videos

## Advanced Features

### Real-Time Caption Preview
- **Live Updates**: See caption changes instantly as you adjust settings
- **Click Positioning**: Click on the preview to position captions
- **Preview Controls**: Play, pause, and seek through the video
- **Audio Visualization**: Waveform display for audio-only files

### Professional Caption Styling
- **Font Selection**: Six professional fonts with cross-platform support
- **Color Wheel**: Advanced HSV-based color selection
- **Opacity Control**: Adjust background transparency
- **Position Control**: Precise X/Y positioning with percentage or pixel values
- **Alignment Options**: Left, center, or right text alignment

### Audio-to-Video Conversion
For audio files (MP3, WAV, etc.), the tool automatically:
1. Generates a video canvas with your chosen aspect ratio
2. Applies your selected background (solid, gradient, or image)
3. Burns captions directly into the video
4. Outputs an MP4 ready for social media or video platforms

### Custom Styling (WebVTT)
The WebVTT output includes CSS styling for:
- Font size and family
- Text and background colors
- Background transparency
- Caption positioning
- Border and shadow effects

### Word-Level Timestamps
When available, the tool preserves word-level timing for precise synchronization.

### Speaker Diarization
ElevenLabs can identify and label different speakers in the audio, making it ideal for interviews, podcasts, and multi-person content.

### Audio Event Detection
Optionally tags non-speech sounds like:
- (laughter)
- (applause)
- (music)
- (footsteps)
- And other ambient sounds

### Language Detection
Automatic language detection supports 99 languages with high accuracy.

## API Usage

For integration with other tools:

```python
import os
from video_caption_generator import get_transcriber, get_audio_extractor
from video_caption_generator.caption_generator import CaptionGenerator
from video_caption_generator.caption_exporter import CaptionExporter

# Set API key
os.environ['ELEVENLABS_API_KEY'] = 'your_key_here'

# Extract audio
extractor = get_audio_extractor()
audio_path = extractor.extract_audio("video.mp4")

# Transcribe with ElevenLabs
transcriber = get_transcriber()
result = transcriber.transcribe(audio_path)

# Generate captions
generator = CaptionGenerator()
captions = generator.generate_captions(result)

# Export
exporter = CaptionExporter()
exporter.export_srt(captions, "output.srt")
```

## Credits

- Primary transcription by [ElevenLabs](https://elevenlabs.io) Scribe v1
- Fallback support for [OpenAI Whisper](https://github.com/openai/whisper)
- Integrated with Bedrot Productions Media Tool Suite
- Built with PyQt5 for the user interface
- Real-time preview system with custom caption overlay
- Cross-platform font management system
- Advanced color wheel widget for intuitive color selection