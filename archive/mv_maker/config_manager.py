"""Configuration management for MV Maker."""

import os
import json
from pathlib import Path

try:
    from core import get_config_manager, resolve_config_path
    from core.env_loader import get_env_var
except ImportError:
    # Fallback if core module not available
    def get_env_var(key, default=None):
        return os.environ.get(key, default)
    
    def resolve_config_path(filename):
        return os.path.join("config", filename)

class MVMakerConfig:
    """Manages configuration for MV Maker."""
    
    DEFAULT_CONFIG = {
        # Transcription service settings
        "transcription_service": "elevenlabs",  # elevenlabs or whisper
        "elevenlabs_api_key": "",  # API key for ElevenLabs
        "elevenlabs_model": "scribe_v1",  # scribe_v1 or scribe_v1_experimental
        
        # ElevenLabs specific settings
        "audio_events": False,  # Tag audio events like (laughter), (footsteps)
        "diarize_speakers": True,  # Annotate which speaker is talking
        "detect_speakers": True,  # Auto-detect number of speakers
        "max_speakers": 32,  # Maximum speakers to detect
        
        # Legacy Whisper settings (for fallback)
        "whisper_model": "base",  # tiny, base, small, medium, large
        
        # Common settings
        "language": "auto",  # auto-detect or specific language code
        "output_formats": ["srt", "vtt"],  # srt, vtt, simple, mp4_overlay, or combinations
        "output_directory": "",  # Empty means same as input
        "caption_max_length": 42,  # Maximum characters per line
        "caption_max_duration": 7.0,  # Maximum seconds per caption
        
        # Font and styling settings
        "font_family": "sans",  # sans, serif, mono, impact
        "font_size": 24,
        "font_color": "#FFFFFF",
        "background_color": "#000000",
        "background_opacity": 0.7,
        "position": "bottom",  # top, middle, bottom
        "margin": 20,
        
        # MP4 overlay settings
        "mp4_overlay_quality": "high",  # low, medium, high
        "mp4_overlay_bitrate": "2M",  # Video bitrate for overlay output
        "subtitle_border": 2,  # Border thickness for better readability
        "subtitle_shadow": True,  # Add shadow effect
        
        # Legacy Whisper-specific settings (kept for compatibility)
        "device": "auto",  # auto, cpu, cuda
        "batch_size": 16,
        "compute_type": "float16",  # float16, int8, float32
        "beam_size": 5,
        "best_of": 5,
        "patience": 1.0,
        "length_penalty": 1.0,
        "temperature": 0.0,
        "compression_ratio_threshold": 2.4,
        "logprob_threshold": -1.0,
        "no_speech_threshold": 0.6,
        "condition_on_previous_text": True,
        "initial_prompt": None,
        "word_timestamps": True,
        "prepend_punctuation": "\"'([{-",
        "append_punctuation": "\"'.)]}",
        
        # UI state
        "last_video_path": "",
        "last_output_path": ""
    }
    
    def __init__(self, config_file="mv_maker_config.json"):
        """Initialize configuration manager."""
        self.config_file = resolve_config_path(config_file)
        self.config_dir = os.path.dirname(self.config_file)
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def load_config(self):
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config=None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to config."""
        # ElevenLabs API key
        api_key = get_env_var('ELEVENLABS_API_KEY')
        if api_key:
            self.config['elevenlabs_api_key'] = api_key
        
        # Transcription service
        service = get_env_var('CAPTION_TRANSCRIPTION_SERVICE')
        if service:
            self.config['transcription_service'] = service
        
        # Model selection
        model = get_env_var('CAPTION_WHISPER_MODEL')
        if model:
            self.config['whisper_model'] = model
        
        # ElevenLabs model
        el_model = get_env_var('ELEVENLABS_MODEL')
        if el_model:
            self.config['elevenlabs_model'] = el_model
        
        # Output directory
        output_dir = get_env_var('CAPTION_OUTPUT_DIR')
        if output_dir:
            self.config['output_directory'] = output_dir
        
        # Language
        language = get_env_var('CAPTION_LANGUAGE')
        if language:
            self.config['language'] = language
        
        # Device
        device = get_env_var('CAPTION_DEVICE')
        if device:
            self.config['device'] = device
    
    def get(self, key, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value."""
        self.config[key] = value
    
    def update(self, updates):
        """Update multiple configuration values."""
        self.config.update(updates)
        self.save_config()
    
    def get_output_directory(self, input_file=None):
        """Get output directory, defaulting to input file directory if not set."""
        output_dir = self.config.get('output_directory', '')
        
        if output_dir and os.path.exists(output_dir):
            return output_dir
        elif input_file:
            return os.path.dirname(input_file)
        else:
            # Default to Videos/Captions
            default_dir = os.path.expanduser("~/Videos/Captions")
            os.makedirs(default_dir, exist_ok=True)
            return default_dir
    
    def get_model_path(self):
        """Get the path where Whisper models are stored."""
        # Default Whisper cache directory
        cache_dir = get_env_var('WHISPER_CACHE_DIR')
        if cache_dir:
            return cache_dir
        
        # Default to user's cache directory
        return os.path.expanduser("~/.cache/whisper")
    
    def validate_config(self):
        """Validate configuration values."""
        errors = []
        
        # Validate model
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if self.config['whisper_model'] not in valid_models:
            errors.append(f"Invalid model: {self.config['whisper_model']}")
        
        # Validate output formats
        valid_formats = ['srt', 'vtt']
        for fmt in self.config['output_formats']:
            if fmt not in valid_formats:
                errors.append(f"Invalid output format: {fmt}")
        
        # Validate numeric values
        if self.config['caption_max_duration'] <= 0:
            errors.append("Caption duration must be positive")
        
        if self.config['caption_max_length'] <= 0:
            errors.append("Caption length must be positive")
        
        return errors

# Global config instance
_config_instance = None

def get_mv_maker_config():
    """Get or create the global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = MVMakerConfig()
    return _config_instance