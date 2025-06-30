# -*- coding: utf-8 -*-
"""
Smart Preset Templates for Video Snippet Remixer.

Provides intelligent preset configurations for different creative use cases,
complete with optimized settings, descriptions, and visual branding.

Features:
- Creative use case templates
- Optimized settings per template
- Visual descriptions and icons
- Quick start configurations
- Randomization options
"""

import random
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class PresetTemplate:
    """Data class for preset template configuration."""
    name: str
    description: str
    use_case: str
    icon: str  # Unicode emoji for visual representation
    
    # Length settings
    length_mode: str  # "Seconds" or "BPM"
    duration_seconds: float
    bpm: float
    bpm_unit: str
    num_units: int
    
    # Output settings
    aspect_ratio: str
    quality_description: str
    
    # Export settings
    export_settings: Dict[str, Any]
    
    # Creative attributes
    energy_level: str  # "low", "medium", "high", "extreme"
    target_audience: str
    recommended_content: List[str]


class PresetManager:
    """
    Manages preset templates and provides intelligent recommendations.
    """
    
    def __init__(self):
        self.presets = self._initialize_presets()
        self.recent_presets = []
        self.favorites = []
    
    def _initialize_presets(self) -> Dict[str, PresetTemplate]:
        """Initialize all preset templates."""
        presets = {}
        
        # Social Media Presets
        presets["instagram_story"] = PresetTemplate(
            name="Instagram Story",
            description="Vertical video optimized for Instagram Stories with punchy, short segments",
            use_case="Social media content creation",
            icon="📱",
            length_mode="Seconds",
            duration_seconds=15.0,
            bpm=128.0,
            bpm_unit="Beat",
            num_units=16,
            aspect_ratio="1080x1920 (9:16 Portrait)",
            quality_description="High quality for mobile viewing",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 20,  # High quality for social
                "bitrate": "8M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="high",
            target_audience="Social media users, content creators",
            recommended_content=["Music videos", "Dance clips", "Lifestyle content", "Fashion videos"]
        )
        
        presets["tiktok_viral"] = PresetTemplate(
            name="TikTok Viral",
            description="Fast-paced, high-energy remix perfect for viral TikTok content",
            use_case="Viral social content",
            icon="🎵",
            length_mode="BPM",
            duration_seconds=30.0,
            bpm=140.0,
            bpm_unit="1/2 Beat",
            num_units=64,
            aspect_ratio="1080x1920 (9:16 Portrait)",
            quality_description="Optimized for mobile and quick upload",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 22,
                "bitrate": "6M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="extreme",
            target_audience="Gen Z, viral content creators",
            recommended_content=["Action clips", "Comedy sketches", "Music performances", "Sports highlights"]
        )
        
        presets["youtube_short"] = PresetTemplate(
            name="YouTube Short",
            description="Engaging short-form content optimized for YouTube Shorts algorithm",
            use_case="YouTube content creation",
            icon="📺",
            length_mode="Seconds",
            duration_seconds=45.0,
            bpm=120.0,
            bpm_unit="Beat",
            num_units=32,
            aspect_ratio="1080x1920 (9:16 Portrait)",
            quality_description="High quality for YouTube platform",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 18,  # Very high quality for YouTube
                "bitrate": "10M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="high",
            target_audience="YouTubers, educators, entertainers",
            recommended_content=["Educational content", "Entertainment clips", "Gaming highlights", "Tutorials"]
        )
        
        # Creative/Artistic Presets
        presets["music_video"] = PresetTemplate(
            name="Music Video Remix",
            description="Cinematic remix synced to musical beats with professional quality",
            use_case="Music and artistic content",
            icon="🎬",
            length_mode="BPM",
            duration_seconds=60.0,
            bpm=120.0,
            bpm_unit="Bar",
            num_units=8,
            aspect_ratio="1920x1080 (16:9 Landscape)",
            quality_description="Cinema-grade quality for artistic work",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "24",  # Cinematic frame rate
                "bitrate_mode": "crf",
                "quality_crf": 16,  # Very high quality
                "bitrate": "15M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="medium",
            target_audience="Musicians, artists, filmmakers",
            recommended_content=["Concert footage", "Artistic visuals", "Performance videos", "Nature scenes"]
        )
        
        presets["film_trailer"] = PresetTemplate(
            name="Film Trailer",
            description="Dramatic, tension-building remix with cinematic pacing",
            use_case="Promotional and dramatic content",
            icon="🎭",
            length_mode="Seconds",
            duration_seconds=90.0,
            bpm=80.0,
            bpm_unit="Beat",
            num_units=24,
            aspect_ratio="2560x1080 (21:9 Ultrawide)",
            quality_description="Ultra-high quality for theatrical presentation",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "24",
                "bitrate_mode": "crf",
                "quality_crf": 14,  # Extremely high quality
                "bitrate": "20M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="medium",
            target_audience="Filmmakers, content marketers",
            recommended_content=["Movie clips", "Dramatic scenes", "Action sequences", "Emotional moments"]
        )
        
        presets["art_showcase"] = PresetTemplate(
            name="Art Showcase",
            description="Smooth, contemplative remix perfect for showcasing visual art",
            use_case="Art and portfolio presentation",
            icon="🎨",
            length_mode="Seconds",
            duration_seconds=120.0,
            bpm=60.0,
            bpm_unit="Bar",
            num_units=8,
            aspect_ratio="1080x1080 (1:1 Square)",
            quality_description="Gallery-quality for art presentation",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 15,
                "bitrate": "12M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="low",
            target_audience="Artists, galleries, portfolios",
            recommended_content=["Art processes", "Gallery tours", "Creative workflows", "Studio sessions"]
        )
        
        # Gaming and Entertainment
        presets["gaming_montage"] = PresetTemplate(
            name="Gaming Montage",
            description="High-energy gaming highlights with rapid cuts and intense pacing",
            use_case="Gaming content creation",
            icon="🎮",
            length_mode="BPM",
            duration_seconds=45.0,
            bpm=150.0,
            bpm_unit="1/4 Beat",
            num_units=120,
            aspect_ratio="1920x1080 (16:9 Landscape)",
            quality_description="High quality for streaming platforms",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "60",  # High frame rate for gaming
                "bitrate_mode": "crf",
                "quality_crf": 19,
                "bitrate": "12M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="extreme",
            target_audience="Gamers, streamers, esports",
            recommended_content=["Gameplay highlights", "Epic moments", "Skill demonstrations", "Competitive plays"]
        )
        
        presets["sports_highlight"] = PresetTemplate(
            name="Sports Highlight",
            description="Dynamic sports compilation with energetic cuts",
            use_case="Sports content creation",
            icon="⚽",
            length_mode="BPM",
            duration_seconds=30.0,
            bpm=130.0,
            bpm_unit="1/2 Beat",
            num_units=48,
            aspect_ratio="1920x1080 (16:9 Landscape)",
            quality_description="Broadcast quality for sports content",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 18,
                "bitrate": "10M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="high",
            target_audience="Sports fans, athletes, coaches",
            recommended_content=["Game highlights", "Training sessions", "Athletic performances", "Team moments"]
        )
        
        # Professional and Business
        presets["corporate_promo"] = PresetTemplate(
            name="Corporate Promo",
            description="Professional, polished remix for business presentations",
            use_case="Corporate and business content",
            icon="💼",
            length_mode="Seconds",
            duration_seconds=30.0,
            bpm=100.0,
            bpm_unit="Beat",
            num_units=20,
            aspect_ratio="1920x1080 (16:9 Landscape)",
            quality_description="Professional broadcast quality",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 17,
                "bitrate": "8M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="medium",
            target_audience="Businesses, marketers, professionals",
            recommended_content=["Product demos", "Company culture", "Testimonials", "Brand content"]
        )
        
        presets["educational_content"] = PresetTemplate(
            name="Educational Content",
            description="Clear, focused remix perfect for instructional material",
            use_case="Educational and instructional content",
            icon="📚",
            length_mode="Seconds",
            duration_seconds=60.0,
            bpm=90.0,
            bpm_unit="Beat",
            num_units=24,
            aspect_ratio="1920x1080 (16:9 Landscape)",
            quality_description="Clear quality for educational viewing",
            export_settings={
                "custom_width": None,
                "custom_height": None,
                "maintain_aspect_ratio": True,
                "match_input_fps": False,
                "frame_rate": "30",
                "bitrate_mode": "crf",
                "quality_crf": 20,
                "bitrate": "6M",
                "trim_start": "",
                "trim_end": ""
            },
            energy_level="low",
            target_audience="Educators, students, trainers",
            recommended_content=["Lectures", "Demonstrations", "Tutorials", "Educational videos"]
        )
        
        return presets
    
    def get_all_presets(self) -> Dict[str, PresetTemplate]:
        """Get all available presets."""
        return self.presets
    
    def get_preset(self, name: str) -> PresetTemplate:
        """Get a specific preset by name."""
        return self.presets.get(name)
    
    def get_presets_by_category(self) -> Dict[str, List[str]]:
        """Get presets organized by category."""
        categories = {
            "Social Media": ["instagram_story", "tiktok_viral", "youtube_short"],
            "Creative & Artistic": ["music_video", "film_trailer", "art_showcase"],
            "Gaming & Entertainment": ["gaming_montage", "sports_highlight"],
            "Professional & Business": ["corporate_promo", "educational_content"]
        }
        return categories
    
    def get_preset_recommendations(self, input_video_count: int = 0, 
                                 estimated_duration: float = 0) -> List[str]:
        """Get smart preset recommendations based on input characteristics."""
        recommendations = []
        
        # Base recommendations
        if input_video_count <= 3:
            recommendations.extend(["art_showcase", "educational_content"])
        elif input_video_count <= 10:
            recommendations.extend(["music_video", "corporate_promo"])
        else:
            recommendations.extend(["gaming_montage", "sports_highlight"])
        
        # Duration-based recommendations
        if estimated_duration > 300:  # 5+ minutes
            recommendations.extend(["film_trailer", "music_video"])
        elif estimated_duration > 60:  # 1+ minutes
            recommendations.extend(["youtube_short", "corporate_promo"])
        else:
            recommendations.extend(["tiktok_viral", "instagram_story"])
        
        # Remove duplicates and return top 4
        return list(dict.fromkeys(recommendations))[:4]
    
    def get_random_preset(self, energy_filter: str = None) -> str:
        """Get a random preset, optionally filtered by energy level."""
        available_presets = list(self.presets.keys())
        
        if energy_filter:
            available_presets = [
                name for name, preset in self.presets.items()
                if preset.energy_level == energy_filter
            ]
        
        return random.choice(available_presets) if available_presets else "music_video"
    
    def add_to_recent(self, preset_name: str):
        """Add a preset to recent usage list."""
        if preset_name in self.recent_presets:
            self.recent_presets.remove(preset_name)
        self.recent_presets.insert(0, preset_name)
        # Keep only last 5
        self.recent_presets = self.recent_presets[:5]
    
    def add_to_favorites(self, preset_name: str):
        """Add a preset to favorites."""
        if preset_name not in self.favorites:
            self.favorites.append(preset_name)
    
    def remove_from_favorites(self, preset_name: str):
        """Remove a preset from favorites."""
        if preset_name in self.favorites:
            self.favorites.remove(preset_name)
    
    def get_surprise_settings(self) -> Dict[str, Any]:
        """Generate random creative settings for 'Surprise Me' feature."""
        surprise_configs = [
            {
                "name": "Glitch Aesthetic",
                "length_mode": "BPM",
                "bpm": random.randint(160, 180),
                "bpm_unit": "1/6 Beat",
                "num_units": random.randint(80, 120),
                "aspect_ratio": "1080x1080 (1:1 Square)",
                "description": "Ultra-fast cuts with digital glitch aesthetic"
            },
            {
                "name": "Cinematic Flow",
                "length_mode": "Seconds",
                "duration_seconds": random.uniform(90, 150),
                "bpm": random.randint(60, 80),
                "bpm_unit": "Bar",
                "num_units": random.randint(6, 12),
                "aspect_ratio": "1920x817 (2.35:1 Cinema)",
                "description": "Smooth, flowing cuts with cinematic timing"
            },
            {
                "name": "Rhythmic Pulse",
                "length_mode": "BPM",
                "bpm": random.randint(120, 140),
                "bpm_unit": random.choice(["1/2 Beat", "Beat"]),
                "num_units": random.randint(32, 64),
                "aspect_ratio": random.choice([
                    "1920x1080 (16:9 Landscape)",
                    "1080x1920 (9:16 Portrait)"
                ]),
                "description": "Perfect sync with musical rhythm"
            },
            {
                "name": "Minimal Focus",
                "length_mode": "Seconds",
                "duration_seconds": random.uniform(20, 40),
                "bpm": random.randint(40, 60),
                "bpm_unit": "Bar",
                "num_units": random.randint(4, 8),
                "aspect_ratio": "1080x1080 (1:1 Square)",
                "description": "Few, long cuts for contemplative viewing"
            }
        ]
        
        return random.choice(surprise_configs)


# Global preset manager instance
preset_manager = PresetManager()