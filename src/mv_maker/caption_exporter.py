"""Caption export module for SRT and WebVTT formats."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from absolute path to handle direct script execution
try:
    from .utils import format_timestamp, safe_print
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import format_timestamp, safe_print

class CaptionExporter:
    """Exports captions to various subtitle formats."""
    
    def __init__(self):
        """Initialize caption exporter."""
        pass
    
    def export_srt(self, captions, output_path):
        """
        Export captions to SRT format.
        
        Args:
            captions: List of caption dictionaries
            output_path: Path for output SRT file
            
        Returns:
            Path to created SRT file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, caption in enumerate(captions, 1):
                    # Caption number
                    f.write(f"{i}\n")
                    
                    # Timestamps
                    start_time = format_timestamp(caption['start'], 'srt')
                    end_time = format_timestamp(caption['end'], 'srt')
                    f.write(f"{start_time} --> {end_time}\n")
                    
                    # Text
                    f.write(f"{caption['text']}\n")
                    
                    # Empty line between captions
                    f.write("\n")
            
            safe_print(f"SRT file exported: {output_path}")
            return output_path
            
        except Exception as e:
            safe_print(f"Error exporting SRT: {e}")
            raise
    
    def export_webvtt(self, captions, output_path, include_styling=True):
        """
        Export captions to WebVTT format with optional styling.
        
        Args:
            captions: List of caption dictionaries
            output_path: Path for output WebVTT file
            include_styling: Whether to include CSS styling
            
        Returns:
            Path to created WebVTT file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # WebVTT header
                f.write("WEBVTT\n")
                f.write("Kind: captions\n")
                f.write("Language: en\n\n")
                
                # Optional CSS styling
                if include_styling and captions and 'style' in captions[0]:
                    f.write("STYLE\n")
                    f.write(self._generate_webvtt_style(captions[0]['style']))
                    f.write("\n\n")
                
                # Write captions
                for i, caption in enumerate(captions, 1):
                    # Optional cue identifier
                    f.write(f"{i}\n")
                    
                    # Timestamps
                    start_time = format_timestamp(caption['start'], 'vtt')
                    end_time = format_timestamp(caption['end'], 'vtt')
                    
                    # Position and alignment
                    position = caption.get('style', {}).get('position', 'bottom')
                    if position == 'bottom':
                        f.write(f"{start_time} --> {end_time} align:center line:90%\n")
                    elif position == 'top':
                        f.write(f"{start_time} --> {end_time} align:center line:10%\n")
                    else:  # middle
                        f.write(f"{start_time} --> {end_time} align:center line:50%\n")
                    
                    # Text with optional styling
                    if include_styling:
                        f.write(f"<c.caption>{caption['text']}</c>\n")
                    else:
                        f.write(f"{caption['text']}\n")
                    
                    # Empty line between captions
                    f.write("\n")
            
            safe_print(f"WebVTT file exported: {output_path}")
            return output_path
            
        except Exception as e:
            safe_print(f"Error exporting WebVTT: {e}")
            raise
    
    def _generate_webvtt_style(self, style_dict):
        """Generate WebVTT CSS style block."""
        font_size = style_dict.get('font_size', 24)
        font_color = style_dict.get('font_color', '#FFFFFF')
        bg_color = style_dict.get('background_color', '#000000')
        bg_opacity = style_dict.get('background_opacity', 0.7)
        
        # Convert hex color to rgba for background
        if bg_color.startswith('#'):
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            bg_rgba = f"rgba({r}, {g}, {b}, {bg_opacity})"
        else:
            bg_rgba = bg_color
        
        style = f"""::cue(.caption) {{
  font-family: Arial, sans-serif;
  font-size: {font_size}px;
  color: {font_color};
  background-color: {bg_rgba};
  padding: 4px 8px;
  border-radius: 4px;
}}

::cue {{
  font-family: Arial, sans-serif;
  font-size: {font_size}px;
  color: {font_color};
  background-color: {bg_rgba};
  padding: 4px 8px;
  border-radius: 4px;
}}"""
        
        return style
    
    def export_both_formats(self, captions, base_output_path, include_styling=True):
        """
        Export captions to both SRT and WebVTT formats.
        
        Args:
            captions: List of caption dictionaries
            base_output_path: Base path without extension
            include_styling: Whether to include WebVTT styling
            
        Returns:
            Dictionary with paths to both files
        """
        # Remove any existing extension
        base_path = str(Path(base_output_path).with_suffix(''))
        
        # Export both formats
        srt_path = f"{base_path}.srt"
        vtt_path = f"{base_path}.vtt"
        
        self.export_srt(captions, srt_path)
        self.export_webvtt(captions, vtt_path, include_styling)
        
        return {
            'srt': srt_path,
            'vtt': vtt_path
        }
    
    def export_all_formats(self, captions, base_output_path, include_styling=True, include_simple=True, include_mp4=False, video_path=None, config=None, progress_callback=None):
        """
        Export captions to all available formats (SRT, WebVTT, Simple, and MP4 overlay).
        
        Args:
            captions: List of caption dictionaries
            base_output_path: Base path without extension
            include_styling: Whether to include WebVTT styling
            include_simple: Whether to include simple [MM:SS] format
            include_mp4: Whether to include MP4 with burned-in captions
            video_path: Path to source video (required for MP4 overlay)
            config: Configuration dictionary for MP4 overlay
            progress_callback: Progress callback function for MP4 processing
            
        Returns:
            Dictionary with paths to all exported files
        """
        # Remove any existing extension
        base_path = str(Path(base_output_path).with_suffix(''))
        
        # Export all formats
        result = {}
        
        srt_path = f"{base_path}.srt"
        vtt_path = f"{base_path}.vtt"
        simple_path = f"{base_path}.txt"
        
        result['srt'] = self.export_srt(captions, srt_path)
        result['vtt'] = self.export_webvtt(captions, vtt_path, include_styling)
        
        if include_simple:
            result['simple'] = self.export_simple_format(captions, simple_path)
        
        # Export MP4 overlay if requested
        if include_mp4 and video_path:
            try:
                from .video_processor import VideoProcessor
                mp4_path = f"{base_path}_captioned.mp4"
                processor = VideoProcessor()
                result['mp4'] = processor.generate_mp4_overlay(
                    video_path, captions, mp4_path, 
                    config or {}, progress_callback
                )
            except Exception as e:
                safe_print(f"Error creating MP4 overlay: {e}")
                # Continue without MP4 if it fails
        
        return result
    
    def export_to_json(self, captions, output_path):
        """
        Export captions to JSON format for further processing.
        
        Args:
            captions: List of caption dictionaries
            output_path: Path for output JSON file
            
        Returns:
            Path to created JSON file
        """
        import json
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Prepare data for JSON serialization
            json_data = {
                'format': 'mv-maker',
                'version': '1.0',
                'captions': []
            }
            
            for caption in captions:
                json_caption = {
                    'start': caption['start'],
                    'end': caption['end'],
                    'text': caption['text'],
                    'duration': caption['end'] - caption['start']
                }
                
                # Include word-level data if available
                if 'words' in caption and caption['words']:
                    json_caption['words'] = [
                        {
                            'word': w['word'],
                            'start': w['start'],
                            'end': w['end']
                        }
                        for w in caption['words']
                    ]
                
                # Include style if available
                if 'style' in caption:
                    json_caption['style'] = caption['style']
                
                json_data['captions'].append(json_caption)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            safe_print(f"JSON file exported: {output_path}")
            return output_path
            
        except Exception as e:
            safe_print(f"Error exporting JSON: {e}")
            raise
    
    def export_simple_format(self, captions, output_path):
        """
        Export captions to simple timestamp format [MM:SS] Caption text.
        
        Args:
            captions: List of caption dictionaries
            output_path: Path for output text file
            
        Returns:
            Path to created text file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for caption in captions:
                    # Format timestamp in [MM:SS] style
                    timestamp = format_timestamp(caption['start'], 'simple')
                    text = caption['text'].strip()
                    
                    # Write in format: [MM:SS] Caption text
                    f.write(f"{timestamp} {text}\n")
            
            safe_print(f"Simple format file exported: {output_path}")
            return output_path
            
        except Exception as e:
            safe_print(f"Error exporting simple format: {e}")
            raise
    
    def generate_preview_html(self, video_path, caption_paths, output_path):
        """
        Generate an HTML preview page with video and captions.
        
        Args:
            video_path: Path to video file
            caption_paths: Dictionary with caption file paths
            output_path: Path for output HTML file
        """
        video_name = Path(video_path).name
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Caption Preview - {video_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f0f0;
        }}
        .video-container {{
            background-color: #000;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        video {{
            width: 100%;
            max-width: 100%;
            height: auto;
        }}
        .controls {{
            margin-top: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 4px;
        }}
        .caption-info {{
            margin-top: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 4px;
        }}
        button {{
            padding: 8px 16px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            background-color: #007bff;
            color: white;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #0056b3;
        }}
    </style>
</head>
<body>
    <h1>Caption Preview</h1>
    <div class="video-container">
        <video id="video" controls>
            <source src="{Path(video_path).name}" type="video/mp4">
"""
        
        # Add caption tracks
        if 'vtt' in caption_paths:
            html_content += f'            <track label="English" kind="subtitles" srclang="en" src="{Path(caption_paths["vtt"]).name}" default>\n'
        
        html_content += """            Your browser does not support the video tag.
        </video>
    </div>
    
    <div class="controls">
        <h3>Playback Controls</h3>
        <button onclick="toggleCaptions()">Toggle Captions</button>
        <button onclick="playbackSpeed(0.5)">0.5x Speed</button>
        <button onclick="playbackSpeed(1.0)">1x Speed</button>
        <button onclick="playbackSpeed(1.5)">1.5x Speed</button>
        <button onclick="playbackSpeed(2.0)">2x Speed</button>
    </div>
    
    <div class="caption-info">
        <h3>Caption Files</h3>
        <ul>
"""
        
        # List caption files
        for fmt, path in caption_paths.items():
            html_content += f'            <li>{fmt.upper()}: <a href="{Path(path).name}" download>{Path(path).name}</a></li>\n'
        
        html_content += """        </ul>
    </div>
    
    <script>
        const video = document.getElementById('video');
        
        function toggleCaptions() {
            const track = video.textTracks[0];
            if (track) {
                track.mode = track.mode === 'showing' ? 'hidden' : 'showing';
            }
        }
        
        function playbackSpeed(speed) {
            video.playbackRate = speed;
        }
        
        // Show captions by default
        if (video.textTracks[0]) {
            video.textTracks[0].mode = 'showing';
        }
    </script>
</body>
</html>"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            safe_print(f"Preview HTML generated: {output_path}")
            return output_path
            
        except Exception as e:
            safe_print(f"Error generating preview HTML: {e}")
            raise