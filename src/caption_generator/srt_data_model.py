# -*- coding: utf-8 -*-
"""
SRT Data Model for Caption Generator SRT Editor.

Provides a unified data model for representing SRT/VTT content as word blocks
with synchronized text conversion between views.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# Word block cycling colors (7 colors)
BLOCK_COLORS = [
    '#ff6666',  # red
    '#ffaa66',  # orange
    '#ffff66',  # yellow
    '#66ff88',  # green
    '#66ffff',  # cyan
    '#6688ff',  # blue
    '#ff66ff',  # purple
]


@dataclass
class WordBlock:
    """Single subtitle entry block with timing and display color."""

    text: str
    start_ms: int  # Start time in milliseconds
    end_ms: int    # End time in milliseconds
    index: int     # Sequence number (1-based)

    @property
    def color(self) -> str:
        """Get the display color for this block (cycles through 7 colors)."""
        return BLOCK_COLORS[self.index % len(BLOCK_COLORS)]

    @property
    def start_time_str(self) -> str:
        """Format start time as SRT timestamp (HH:MM:SS,mmm)."""
        return ms_to_srt_timestamp(self.start_ms)

    @property
    def end_time_str(self) -> str:
        """Format end time as SRT timestamp (HH:MM:SS,mmm)."""
        return ms_to_srt_timestamp(self.end_ms)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'text': self.text,
            'start_ms': self.start_ms,
            'end_ms': self.end_ms,
            'index': self.index
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WordBlock':
        """Deserialize from dictionary."""
        return cls(
            text=data['text'],
            start_ms=data['start_ms'],
            end_ms=data['end_ms'],
            index=data['index']
        )


def ms_to_srt_timestamp(ms: int) -> str:
    """
    Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm).

    Args:
        ms: Time in milliseconds

    Returns:
        Formatted timestamp string
    """
    if ms < 0:
        ms = 0

    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def srt_timestamp_to_ms(timestamp: str) -> int:
    """
    Parse SRT timestamp format (HH:MM:SS,mmm) to milliseconds.

    Args:
        timestamp: SRT formatted timestamp

    Returns:
        Time in milliseconds

    Raises:
        ValueError: If timestamp format is invalid
    """
    timestamp = timestamp.strip()

    # Handle VTT format (uses . instead of ,)
    timestamp = timestamp.replace('.', ',')

    try:
        time_part, ms_part = timestamp.split(',')
        parts = time_part.split(':')

        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours = '0'
            minutes, seconds = parts
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

        total_ms = (
            int(hours) * 3600000 +
            int(minutes) * 60000 +
            int(seconds) * 1000 +
            int(ms_part)
        )
        return total_ms

    except Exception as e:
        raise ValueError(f"Invalid timestamp format '{timestamp}': {e}")


class SRTDataModel:
    """
    Central data model for SRT/VTT content.

    Manages word blocks and provides conversion between block representation
    and raw SRT text format.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the data model.

        Args:
            file_path: Optional path to SRT/VTT file to load
        """
        self.file_path: Optional[str] = file_path
        self.blocks: List[WordBlock] = []
        self.is_vtt: bool = False

        if file_path and os.path.exists(file_path):
            self.load_from_file(file_path)

    def load_from_file(self, file_path: str) -> bool:
        """
        Load SRT or VTT file into word blocks.

        Args:
            file_path: Path to subtitle file

        Returns:
            True if successful, False otherwise
        """
        self.file_path = file_path
        self.blocks = []

        ext = os.path.splitext(file_path)[1].lower()
        self.is_vtt = (ext == '.vtt')

        try:
            if self.is_vtt:
                return self._load_vtt(file_path)
            else:
                return self._load_srt(file_path)
        except Exception as e:
            print(f"[SRT Editor] Error loading file: {e}")
            return False

    def _load_srt(self, file_path: str) -> bool:
        """Load SRT file using pysrt library."""
        try:
            import pysrt

            subs = pysrt.open(file_path, encoding='utf-8')

            for sub in subs:
                # Convert SubRipTime to milliseconds
                start_ms = (
                    sub.start.hours * 3600000 +
                    sub.start.minutes * 60000 +
                    sub.start.seconds * 1000 +
                    sub.start.milliseconds
                )
                end_ms = (
                    sub.end.hours * 3600000 +
                    sub.end.minutes * 60000 +
                    sub.end.seconds * 1000 +
                    sub.end.milliseconds
                )

                block = WordBlock(
                    text=sub.text,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    index=sub.index
                )
                self.blocks.append(block)

            return True

        except Exception as e:
            print(f"[SRT Editor] Error parsing SRT: {e}")
            return False

    def _load_vtt(self, file_path: str) -> bool:
        """Load VTT file using webvtt-py library."""
        try:
            import webvtt

            vtt = webvtt.read(file_path)

            for idx, caption in enumerate(vtt.captions, start=1):
                # Parse VTT timestamps (HH:MM:SS.mmm format)
                start_ms = self._vtt_timestamp_to_ms(caption.start)
                end_ms = self._vtt_timestamp_to_ms(caption.end)

                block = WordBlock(
                    text=caption.text,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    index=idx
                )
                self.blocks.append(block)

            return True

        except Exception as e:
            print(f"[SRT Editor] Error parsing VTT: {e}")
            return False

    def _vtt_timestamp_to_ms(self, timestamp: str) -> int:
        """Parse VTT timestamp (HH:MM:SS.mmm) to milliseconds."""
        parts = timestamp.split(':')

        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            sec_parts = parts[2].split('.')
            seconds = int(sec_parts[0])
            milliseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        elif len(parts) == 2:
            hours = 0
            minutes = int(parts[0])
            sec_parts = parts[1].split('.')
            seconds = int(sec_parts[0])
            milliseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        else:
            return 0

        return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds

    def save_to_file(self, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Save word blocks to SRT or VTT file.

        Args:
            file_path: Path to save to (uses original path if None)

        Returns:
            Tuple of (success, message)
        """
        save_path = file_path or self.file_path

        if not save_path:
            return False, "No file path specified"

        ext = os.path.splitext(save_path)[1].lower()

        try:
            if ext == '.vtt':
                return self._save_vtt(save_path)
            else:
                return self._save_srt(save_path)
        except Exception as e:
            return False, f"Error saving file: {e}"

    def _save_srt(self, file_path: str) -> Tuple[bool, str]:
        """Save as SRT file using pysrt library."""
        try:
            import pysrt

            srt_file = pysrt.SubRipFile()

            for block in self.blocks:
                # Convert milliseconds to SubRipTime
                start_time = pysrt.SubRipTime(milliseconds=block.start_ms)
                end_time = pysrt.SubRipTime(milliseconds=block.end_ms)

                item = pysrt.SubRipItem(
                    index=block.index,
                    start=start_time,
                    end=end_time,
                    text=block.text
                )
                srt_file.append(item)

            srt_file.save(file_path, encoding='utf-8')
            return True, f"Saved to {os.path.basename(file_path)}"

        except Exception as e:
            return False, f"Error saving SRT: {e}"

    def _save_vtt(self, file_path: str) -> Tuple[bool, str]:
        """Save as VTT file using webvtt-py library."""
        try:
            import webvtt

            vtt = webvtt.WebVTT()

            for block in self.blocks:
                start_str = self._ms_to_vtt_timestamp(block.start_ms)
                end_str = self._ms_to_vtt_timestamp(block.end_ms)

                caption = webvtt.Caption(
                    start=start_str,
                    end=end_str,
                    text=block.text
                )
                vtt.captions.append(caption)

            vtt.save(file_path)
            return True, f"Saved to {os.path.basename(file_path)}"

        except Exception as e:
            return False, f"Error saving VTT: {e}"

    def _ms_to_vtt_timestamp(self, ms: int) -> str:
        """Convert milliseconds to VTT timestamp (HH:MM:SS.mmm)."""
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        milliseconds = ms % 1000

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

    def to_raw_text(self) -> str:
        """
        Generate raw SRT/VTT text from word blocks.

        Returns:
            Raw subtitle file content as string
        """
        if self.is_vtt:
            return self._to_raw_vtt()
        else:
            return self._to_raw_srt()

    def _to_raw_srt(self) -> str:
        """Generate raw SRT text."""
        lines = []

        for block in self.blocks:
            lines.append(str(block.index))
            lines.append(f"{block.start_time_str} --> {block.end_time_str}")
            lines.append(block.text)
            lines.append('')  # Blank line between entries

        return '\n'.join(lines)

    def _to_raw_vtt(self) -> str:
        """Generate raw VTT text."""
        lines = ['WEBVTT', '']

        for block in self.blocks:
            start_str = self._ms_to_vtt_timestamp(block.start_ms)
            end_str = self._ms_to_vtt_timestamp(block.end_ms)

            lines.append(f"{start_str} --> {end_str}")
            lines.append(block.text)
            lines.append('')  # Blank line between entries

        return '\n'.join(lines)

    def update_from_raw_text(self, raw_text: str) -> Tuple[bool, str]:
        """
        Parse raw SRT/VTT text and update word blocks.

        Args:
            raw_text: Raw subtitle file content

        Returns:
            Tuple of (success, error_message)
        """
        if self.is_vtt or raw_text.strip().startswith('WEBVTT'):
            return self._parse_raw_vtt(raw_text)
        else:
            return self._parse_raw_srt(raw_text)

    def _parse_raw_srt(self, raw_text: str) -> Tuple[bool, str]:
        """Parse raw SRT text into word blocks."""
        new_blocks = []
        lines = raw_text.strip().split('\n')

        i = 0
        entry_index = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Try to parse sequence number
            if line.isdigit():
                entry_index = int(line)
                i += 1

                if i >= len(lines):
                    break

                # Parse timestamp line
                timestamp_line = lines[i].strip()
                if '-->' not in timestamp_line:
                    return False, f"Expected timestamp at line {i + 1}, got: {timestamp_line}"

                try:
                    parts = timestamp_line.split('-->')
                    start_ms = srt_timestamp_to_ms(parts[0].strip())
                    end_ms = srt_timestamp_to_ms(parts[1].strip())
                except ValueError as e:
                    return False, f"Invalid timestamp at line {i + 1}: {e}"

                i += 1

                # Collect text lines until empty line or next number
                text_lines = []
                while i < len(lines):
                    text_line = lines[i]

                    # Check if we've hit the next entry
                    if text_line.strip() == '' or (text_line.strip().isdigit() and i + 1 < len(lines) and '-->' in lines[i + 1]):
                        if text_line.strip().isdigit():
                            # Don't consume the next index
                            break
                        i += 1
                        break

                    text_lines.append(text_line)
                    i += 1

                block = WordBlock(
                    text='\n'.join(text_lines),
                    start_ms=start_ms,
                    end_ms=end_ms,
                    index=entry_index
                )
                new_blocks.append(block)
            else:
                # Try to parse as timestamp line (some SRT files don't have sequence numbers)
                if '-->' in line:
                    entry_index += 1

                    try:
                        parts = line.split('-->')
                        start_ms = srt_timestamp_to_ms(parts[0].strip())
                        end_ms = srt_timestamp_to_ms(parts[1].strip())
                    except ValueError as e:
                        return False, f"Invalid timestamp at line {i + 1}: {e}"

                    i += 1

                    # Collect text lines
                    text_lines = []
                    while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                        text_lines.append(lines[i])
                        i += 1

                    block = WordBlock(
                        text='\n'.join(text_lines),
                        start_ms=start_ms,
                        end_ms=end_ms,
                        index=entry_index
                    )
                    new_blocks.append(block)
                else:
                    i += 1

        self.blocks = new_blocks
        return True, ""

    def _parse_raw_vtt(self, raw_text: str) -> Tuple[bool, str]:
        """Parse raw VTT text into word blocks."""
        new_blocks = []
        lines = raw_text.strip().split('\n')

        i = 0
        entry_index = 0

        # Skip WEBVTT header
        if lines and lines[0].strip().startswith('WEBVTT'):
            i = 1

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('NOTE'):
                i += 1
                continue

            # Look for timestamp line
            if '-->' in line:
                entry_index += 1

                try:
                    parts = line.split('-->')
                    start_ms = self._vtt_timestamp_to_ms(parts[0].strip())
                    end_ms = self._vtt_timestamp_to_ms(parts[1].strip().split()[0])  # Handle cue settings
                except Exception as e:
                    return False, f"Invalid timestamp at line {i + 1}: {e}"

                i += 1

                # Collect text lines
                text_lines = []
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text_lines.append(lines[i])
                    i += 1

                block = WordBlock(
                    text='\n'.join(text_lines),
                    start_ms=start_ms,
                    end_ms=end_ms,
                    index=entry_index
                )
                new_blocks.append(block)
            else:
                # Skip cue identifiers or other non-timestamp lines
                i += 1

        self.blocks = new_blocks
        return True, ""

    def update_block(self, index: int, text: str, start_ms: int, end_ms: int) -> bool:
        """
        Update a specific word block.

        Args:
            index: Block index in self.blocks list
            text: New text content
            start_ms: New start time in milliseconds
            end_ms: New end time in milliseconds

        Returns:
            True if successful
        """
        if 0 <= index < len(self.blocks):
            self.blocks[index].text = text
            self.blocks[index].start_ms = start_ms
            self.blocks[index].end_ms = end_ms
            return True
        return False

    def apply_offset(self, offset_ms: int) -> int:
        """
        Apply a time offset to all subtitle blocks.

        Args:
            offset_ms: Offset in milliseconds (positive = later, negative = earlier)

        Returns:
            Number of blocks that were modified
        """
        modified_count = 0

        for block in self.blocks:
            new_start = block.start_ms + offset_ms
            new_end = block.end_ms + offset_ms

            # Ensure times don't go negative
            if new_start < 0:
                new_start = 0
            if new_end < 0:
                new_end = 0

            if new_start != block.start_ms or new_end != block.end_ms:
                block.start_ms = new_start
                block.end_ms = new_end
                modified_count += 1

        return modified_count

    def scale_timing(self, factor: float) -> int:
        """
        Scale all subtitle timing by a factor.

        Args:
            factor: Scaling factor (e.g., 1.1 = 10% slower, 0.9 = 10% faster)

        Returns:
            Number of blocks that were modified
        """
        if factor <= 0:
            return 0

        modified_count = 0

        for block in self.blocks:
            new_start = int(block.start_ms * factor)
            new_end = int(block.end_ms * factor)

            if new_start != block.start_ms or new_end != block.end_ms:
                block.start_ms = new_start
                block.end_ms = new_end
                modified_count += 1

        return modified_count

    def __len__(self) -> int:
        """Return number of word blocks."""
        return len(self.blocks)

    def __iter__(self):
        """Iterate over word blocks."""
        return iter(self.blocks)
