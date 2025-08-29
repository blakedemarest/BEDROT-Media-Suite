"""Font management module for cross-platform font handling."""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from .utils import safe_print
except ImportError:
    from mv_maker.utils import safe_print

class FontManager:
    """Manages font availability and mapping across different platforms."""
    
    # Primary font mappings for our supported fonts
    FONT_MAPPINGS = {
        'arial': {
            'display_name': 'Arial',
            'windows': ['arial.ttf', 'Arial'],
            'linux': ['Liberation Sans', 'Arial', 'DejaVu Sans'],
            'darwin': ['Arial', 'Helvetica']
        },
        'helvetica': {
            'display_name': 'Helvetica',
            'windows': ['helvetica.ttf', 'Helvetica', 'Arial'],
            'linux': ['Helvetica', 'Liberation Sans', 'Nimbus Sans'],
            'darwin': ['Helvetica', 'Helvetica Neue']
        },
        'verdana': {
            'display_name': 'Verdana',
            'windows': ['verdana.ttf', 'Verdana'],
            'linux': ['Verdana', 'DejaVu Sans', 'Bitstream Vera Sans'],
            'darwin': ['Verdana', 'Geneva']
        },
        'roboto': {
            'display_name': 'Roboto',
            'windows': ['Roboto-Regular.ttf', 'Roboto'],
            'linux': ['Roboto', 'Roboto Regular', 'Noto Sans'],
            'darwin': ['Roboto', 'Roboto-Regular']
        },
        'open_sans': {
            'display_name': 'Open Sans',
            'windows': ['OpenSans-Regular.ttf', 'Open Sans'],
            'linux': ['Open Sans', 'OpenSans', 'Noto Sans'],
            'darwin': ['Open Sans', 'OpenSans-Regular']
        },
        'impact': {
            'display_name': 'Impact',
            'windows': ['impact.ttf', 'Impact'],
            'linux': ['Impact', 'Anton', 'BebasNeue'],
            'darwin': ['Impact', 'Helvetica-Bold']
        }
    }
    
    # Common font directories by platform
    FONT_DIRS = {
        'windows': [
            'C:/Windows/Fonts',
            os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft/Windows/Fonts')
        ],
        'linux': [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            '/usr/share/fonts/truetype',
            os.path.expanduser('~/.fonts'),
            os.path.expanduser('~/.local/share/fonts')
        ],
        'darwin': [
            '/System/Library/Fonts',
            '/Library/Fonts',
            os.path.expanduser('~/Library/Fonts'),
            '/System/Library/Fonts/Supplemental'
        ]
    }
    
    def __init__(self):
        """Initialize font manager."""
        self.platform = platform.system().lower()
        if self.platform not in ['windows', 'linux', 'darwin']:
            self.platform = 'linux'  # Default fallback
        
        self._font_cache = {}
        self._available_fonts = None
        
    def get_font_list(self) -> List[Tuple[str, str]]:
        """
        Get list of available fonts from our supported set.
        
        Returns:
            List of tuples (font_key, display_name)
        """
        available = []
        for font_key, font_info in self.FONT_MAPPINGS.items():
            if self._is_font_available(font_key):
                available.append((font_key, font_info['display_name']))
        
        # Always ensure at least Arial is available as fallback
        if not available:
            available.append(('arial', 'Arial'))
        
        return available
    
    def get_font_path(self, font_key: str) -> Optional[str]:
        """
        Get the font file path or font name for FFmpeg.
        
        Args:
            font_key: Font identifier (e.g., 'arial', 'roboto')
            
        Returns:
            Font file path or font name suitable for FFmpeg
        """
        if font_key not in self.FONT_MAPPINGS:
            font_key = 'arial'  # Fallback to Arial
        
        # Check cache first
        if font_key in self._font_cache:
            return self._font_cache[font_key]
        
        font_info = self.FONT_MAPPINGS[font_key]
        font_variants = font_info.get(self.platform, font_info.get('linux', []))
        
        # Try to find the font
        for variant in font_variants:
            if self.platform == 'windows':
                # On Windows, try to find the actual font file
                font_path = self._find_font_file_windows(variant)
                if font_path:
                    self._font_cache[font_key] = font_path
                    return font_path
            else:
                # On Linux/macOS, return the font name for fontconfig
                if self._check_font_exists(variant):
                    self._font_cache[font_key] = variant
                    return variant
        
        # Fallback to first variant
        fallback = font_variants[0] if font_variants else 'Arial'
        self._font_cache[font_key] = fallback
        return fallback
    
    def _is_font_available(self, font_key: str) -> bool:
        """Check if a font is available on the system."""
        if font_key not in self.FONT_MAPPINGS:
            return False
        
        font_info = self.FONT_MAPPINGS[font_key]
        font_variants = font_info.get(self.platform, font_info.get('linux', []))
        
        for variant in font_variants:
            if self.platform == 'windows':
                if self._find_font_file_windows(variant):
                    return True
            else:
                if self._check_font_exists(variant):
                    return True
        
        return False
    
    def _find_font_file_windows(self, font_name: str) -> Optional[str]:
        """Find font file on Windows."""
        # If it's already a path-like string with .ttf
        if font_name.endswith('.ttf'):
            # Check in font directories
            for font_dir in self.FONT_DIRS['windows']:
                if os.path.exists(font_dir):
                    font_path = os.path.join(font_dir, font_name)
                    if os.path.exists(font_path):
                        return font_path
        
        # Try common variations
        variations = [
            font_name,
            f"{font_name}.ttf",
            f"{font_name}-Regular.ttf",
            f"{font_name}Regular.ttf"
        ]
        
        for font_dir in self.FONT_DIRS['windows']:
            if os.path.exists(font_dir):
                for variant in variations:
                    font_path = os.path.join(font_dir, variant)
                    if os.path.exists(font_path):
                        return font_path
        
        return None
    
    def _check_font_exists(self, font_name: str) -> bool:
        """Check if font exists on Linux/macOS using fontconfig."""
        if self.platform == 'darwin':
            # On macOS, we trust that system fonts are available
            return True
        
        # On Linux, try to use fc-list if available
        try:
            import subprocess
            result = subprocess.run(
                ['fc-list', ':family'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                font_families = result.stdout.lower()
                return font_name.lower() in font_families
        except:
            pass
        
        # Fallback: assume it exists
        return True
    
    def get_font_for_ffmpeg(self, font_key: str) -> str:
        """
        Get font specification for FFmpeg based on platform.
        
        Args:
            font_key: Font identifier
            
        Returns:
            Font specification string for FFmpeg
        """
        font_path_or_name = self.get_font_path(font_key)
        
        if self.platform == 'windows' and os.path.exists(font_path_or_name):
            # Return full path for Windows
            return font_path_or_name.replace('\\', '/')
        else:
            # Return font name for fontconfig
            return font_path_or_name
    
    def get_available_fonts_info(self) -> Dict[str, Dict]:
        """Get detailed information about available fonts."""
        info = {}
        for font_key, font_data in self.FONT_MAPPINGS.items():
            if self._is_font_available(font_key):
                info[font_key] = {
                    'display_name': font_data['display_name'],
                    'available': True,
                    'font_path': self.get_font_path(font_key)
                }
        return info
    
    def get_fallback_font(self) -> str:
        """Get a guaranteed fallback font."""
        # Try our preferred fonts in order
        fallback_order = ['arial', 'helvetica', 'verdana', 'open_sans', 'roboto', 'impact']
        
        for font_key in fallback_order:
            if self._is_font_available(font_key):
                return font_key
        
        # Ultimate fallback
        return 'arial'
    
    def validate_font_selection(self, font_key: str) -> str:
        """
        Validate and potentially correct a font selection.
        
        Args:
            font_key: Requested font
            
        Returns:
            Valid font key (original or fallback)
        """
        if font_key in self.FONT_MAPPINGS and self._is_font_available(font_key):
            return font_key
        
        safe_print(f"Font '{font_key}' not available, using fallback")
        return self.get_fallback_font()


# Singleton instance
_font_manager = None

def get_font_manager() -> FontManager:
    """Get or create the singleton FontManager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager