"""Caption generation and timing module."""

import sys
from pathlib import Path

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from absolute path to handle direct script execution
try:
    from .utils import split_text_for_captions, safe_print
    from .config_manager import get_mv_maker_config
except ImportError:
    # Fallback for direct script execution
    from mv_maker.utils import split_text_for_captions, safe_print
    from mv_maker.config_manager import get_mv_maker_config

class CaptionGenerator:
    """Generates properly timed captions from transcription segments."""
    
    def __init__(self):
        """Initialize caption generator."""
        self.config = get_mv_maker_config()
        self.max_caption_length = self.config.get('caption_max_length', 42)
        self.max_caption_duration = self.config.get('caption_max_duration', 7.0)
    
    def generate_captions(self, transcription_result, progress_callback=None):
        """
        Generate captions from transcription segments.
        
        Args:
            transcription_result: Result from transcriber with segments
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of caption dictionaries with timing and text
        """
        segments = transcription_result.get('segments', [])
        if not segments:
            return []
        
        captions = []
        total_segments = len(segments)
        
        for i, segment in enumerate(segments):
            if progress_callback:
                progress = int((i / total_segments) * 100)
                progress_callback(progress, 100, f"Processing segment {i+1}/{total_segments}")
            
            # Process segment into captions
            segment_captions = self._process_segment(segment)
            captions.extend(segment_captions)
        
        # Post-process captions
        captions = self._merge_short_captions(captions)
        captions = self._adjust_caption_timing(captions)
        
        if progress_callback:
            progress_callback(100, 100, "Caption generation complete")
        
        return captions
    
    def _process_segment(self, segment):
        """Process a single segment into one or more captions."""
        text = segment['text'].strip()
        if not text:
            return []
        
        # If we have word-level timestamps, use them for better timing
        if segment.get('words'):
            return self._process_with_word_timing(segment)
        else:
            return self._process_without_word_timing(segment)
    
    def _process_with_word_timing(self, segment):
        """Process segment using word-level timestamps."""
        words = segment['words']
        if not words:
            return self._process_without_word_timing(segment)
        
        captions = []
        current_caption = {
            'start': words[0]['start'],
            'end': words[0]['end'],
            'text': '',
            'words': []
        }
        
        for word in words:
            word_text = word['word'].strip()
            
            # Check if adding this word would exceed limits
            test_text = (current_caption['text'] + ' ' + word_text).strip()
            caption_duration = word['end'] - current_caption['start']
            
            if (len(test_text) > self.max_caption_length or 
                caption_duration > self.max_caption_duration) and current_caption['text']:
                # Finalize current caption
                current_caption['text'] = current_caption['text'].strip()
                captions.append(current_caption)
                
                # Start new caption
                current_caption = {
                    'start': word['start'],
                    'end': word['end'],
                    'text': word_text,
                    'words': [word]
                }
            else:
                # Add word to current caption
                current_caption['text'] = test_text
                current_caption['end'] = word['end']
                current_caption['words'].append(word)
        
        # Add final caption
        if current_caption['text']:
            current_caption['text'] = current_caption['text'].strip()
            captions.append(current_caption)
        
        return captions
    
    def _process_without_word_timing(self, segment):
        """Process segment without word-level timestamps."""
        text = segment['text'].strip()
        start_time = segment['start']
        end_time = segment['end']
        duration = end_time - start_time
        
        # Split text into caption-friendly lines
        lines = split_text_for_captions(text, self.max_caption_length)
        
        if not lines:
            return []
        
        # Calculate time per caption
        time_per_caption = min(duration / len(lines), self.max_caption_duration)
        
        captions = []
        current_time = start_time
        
        for line in lines:
            caption = {
                'start': current_time,
                'end': min(current_time + time_per_caption, end_time),
                'text': line,
                'words': []  # No word-level timing available
            }
            captions.append(caption)
            current_time = caption['end']
        
        return captions
    
    def _merge_short_captions(self, captions):
        """Merge very short captions that are close together."""
        if len(captions) <= 1:
            return captions
        
        merged = []
        i = 0
        
        while i < len(captions):
            current = captions[i]
            
            # Check if we can merge with next caption
            if i + 1 < len(captions):
                next_caption = captions[i + 1]
                
                # Conditions for merging
                time_gap = next_caption['start'] - current['end']
                combined_duration = next_caption['end'] - current['start']
                combined_text = current['text'] + ' ' + next_caption['text']
                
                if (time_gap < 0.5 and  # Less than 0.5 second gap
                    combined_duration <= self.max_caption_duration and
                    len(combined_text) <= self.max_caption_length * 1.5):
                    
                    # Merge captions
                    merged_caption = {
                        'start': current['start'],
                        'end': next_caption['end'],
                        'text': combined_text,
                        'words': current.get('words', []) + next_caption.get('words', [])
                    }
                    merged.append(merged_caption)
                    i += 2  # Skip next caption
                    continue
            
            # No merge, add current caption
            merged.append(current)
            i += 1
        
        return merged
    
    def _adjust_caption_timing(self, captions):
        """Adjust caption timing to avoid overlaps and ensure minimum display time."""
        if not captions:
            return captions
        
        min_display_time = 1.0  # Minimum 1 second display time
        
        adjusted = []
        for i, caption in enumerate(captions):
            # Ensure minimum display time
            duration = caption['end'] - caption['start']
            if duration < min_display_time:
                # Try to extend end time
                if i + 1 < len(captions):
                    # Don't overlap with next caption
                    max_end = captions[i + 1]['start'] - 0.1
                    caption['end'] = min(caption['start'] + min_display_time, max_end)
                else:
                    # Last caption, can extend freely
                    caption['end'] = caption['start'] + min_display_time
            
            # Ensure no overlap with previous caption
            if adjusted and caption['start'] < adjusted[-1]['end']:
                caption['start'] = adjusted[-1]['end'] + 0.1
            
            adjusted.append(caption)
        
        return adjusted
    
    def add_caption_styling(self, captions):
        """Add styling information to captions for WebVTT format."""
        config = self.config
        
        for caption in captions:
            caption['style'] = {
                'font_size': config.get('font_size', 24),
                'font_color': config.get('font_color', '#FFFFFF'),
                'background_color': config.get('background_color', '#000000'),
                'background_opacity': config.get('background_opacity', 0.7),
                'position': config.get('position', 'bottom'),
                'margin': config.get('margin', 20)
            }
        
        return captions
    
    def validate_captions(self, captions):
        """Validate caption timing and content."""
        errors = []
        
        for i, caption in enumerate(captions):
            # Check required fields
            if 'start' not in caption or 'end' not in caption or 'text' not in caption:
                errors.append(f"Caption {i} missing required fields")
                continue
            
            # Check timing
            if caption['start'] >= caption['end']:
                errors.append(f"Caption {i}: start time >= end time")
            
            if caption['start'] < 0:
                errors.append(f"Caption {i}: negative start time")
            
            # Check for overlaps
            if i > 0 and caption['start'] < captions[i-1]['end']:
                errors.append(f"Caption {i}: overlaps with previous caption")
            
            # Check text
            if not caption['text'].strip():
                errors.append(f"Caption {i}: empty text")
        
        return errors
    
    def get_statistics(self, captions):
        """Get statistics about the generated captions."""
        if not captions:
            return {
                'total_captions': 0,
                'total_duration': 0,
                'average_duration': 0,
                'average_length': 0,
                'total_words': 0
            }
        
        total_duration = sum(c['end'] - c['start'] for c in captions)
        total_chars = sum(len(c['text']) for c in captions)
        total_words = sum(len(c['text'].split()) for c in captions)
        
        return {
            'total_captions': len(captions),
            'total_duration': total_duration,
            'average_duration': total_duration / len(captions),
            'average_length': total_chars / len(captions),
            'total_words': total_words,
            'captions_per_minute': (len(captions) / total_duration) * 60 if total_duration > 0 else 0
        }