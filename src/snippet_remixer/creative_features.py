# -*- coding: utf-8 -*-
"""
Creative Features and Randomization System for Video Snippet Remixer.

Provides creative inspiration tools including:
- Intelligent randomization
- Creative prompts and suggestions
- BPM visualization and music sync
- Style generators
- Creative challenges
- Inspiration galleries
"""

import random
import math
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import customtkinter as ctk

from .ui_theme import theme, widgets, layout
from .preset_templates import preset_manager, PresetTemplate


class CreativeStyle(Enum):
    """Different creative styles for randomization."""
    GLITCH = "glitch"
    CINEMATIC = "cinematic"
    RHYTHMIC = "rhythmic"
    MINIMAL = "minimal"
    EXPERIMENTAL = "experimental"
    NOSTALGIC = "nostalgic"
    FUTURISTIC = "futuristic"
    ORGANIC = "organic"


class MoodCategory(Enum):
    """Mood categories for creative inspiration."""
    ENERGETIC = "energetic"
    CALM = "calm"
    DRAMATIC = "dramatic"
    PLAYFUL = "playful"
    MYSTERIOUS = "mysterious"
    ROMANTIC = "romantic"
    EPIC = "epic"
    NOSTALGIC = "nostalgic"


class CreativeRandomizer:
    """
    Advanced randomization system for creative video remixing.
    """
    
    def __init__(self):
        self.style_patterns = self._initialize_style_patterns()
        self.mood_configurations = self._initialize_mood_configurations()
        self.creative_prompts = self._initialize_creative_prompts()
    
    def _initialize_style_patterns(self) -> Dict[CreativeStyle, Dict[str, Any]]:
        """Initialize style-specific patterns and configurations."""
        return {
            CreativeStyle.GLITCH: {
                "bpm_range": (140, 180),
                "bpm_units": ["1/6 Beat", "1/4 Beat"],
                "snippet_count_multiplier": 1.5,
                "aspect_ratios": ["1080x1080 (1:1 Square)", "1080x1920 (9:16 Portrait)"],
                "description": "Ultra-fast cuts with digital aesthetic",
                "keywords": ["fragmented", "digital", "chaotic", "intense"]
            },
            CreativeStyle.CINEMATIC: {
                "bpm_range": (60, 90),
                "bpm_units": ["Bar", "Beat"],
                "snippet_count_multiplier": 0.3,
                "aspect_ratios": ["1920x817 (2.35:1 Cinema)", "2560x1080 (21:9 Ultrawide)"],
                "description": "Smooth, flowing cuts with cinematic timing",
                "keywords": ["flowing", "cinematic", "dramatic", "smooth"]
            },
            CreativeStyle.RHYTHMIC: {
                "bpm_range": (110, 140),
                "bpm_units": ["1/2 Beat", "Beat"],
                "snippet_count_multiplier": 1.0,
                "aspect_ratios": ["1920x1080 (16:9 Landscape)", "1080x1920 (9:16 Portrait)"],
                "description": "Perfect sync with musical rhythm",
                "keywords": ["rhythmic", "musical", "synchronized", "pulsing"]
            },
            CreativeStyle.MINIMAL: {
                "bpm_range": (40, 70),
                "bpm_units": ["Bar"],
                "snippet_count_multiplier": 0.2,
                "aspect_ratios": ["1080x1080 (1:1 Square)", "1920x1080 (16:9 Landscape)"],
                "description": "Few, long cuts for contemplative viewing",
                "keywords": ["minimal", "contemplative", "spacious", "zen"]
            },
            CreativeStyle.EXPERIMENTAL: {
                "bpm_range": (80, 160),
                "bpm_units": ["1/6 Beat", "1/3 Beat", "1/2 Beat", "Beat"],
                "snippet_count_multiplier": random.uniform(0.5, 2.0),
                "aspect_ratios": ["1080x1080 (1:1 Square)", "1920x817 (2.35:1 Cinema)"],
                "description": "Unpredictable and creative combinations",
                "keywords": ["experimental", "unpredictable", "artistic", "avant-garde"]
            },
            CreativeStyle.NOSTALGIC: {
                "bpm_range": (70, 100),
                "bpm_units": ["Beat", "Bar"],
                "snippet_count_multiplier": 0.7,
                "aspect_ratios": ["1440x1080 (4:3 Classic)", "1920x1080 (16:9 Landscape)"],
                "description": "Classic pacing with retro feel",
                "keywords": ["nostalgic", "retro", "classic", "timeless"]
            },
            CreativeStyle.FUTURISTIC: {
                "bpm_range": (120, 160),
                "bpm_units": ["1/4 Beat", "1/2 Beat"],
                "snippet_count_multiplier": 1.3,
                "aspect_ratios": ["1080x1920 (9:16 Portrait)", "2560x1080 (21:9 Ultrawide)"],
                "description": "Fast-paced with modern aesthetic",
                "keywords": ["futuristic", "modern", "sleek", "technological"]
            },
            CreativeStyle.ORGANIC: {
                "bpm_range": (60, 110),
                "bpm_units": ["Beat", "Bar"],
                "snippet_count_multiplier": 0.8,
                "aspect_ratios": ["1920x1080 (16:9 Landscape)", "1920x817 (2.35:1 Cinema)"],
                "description": "Natural, flowing rhythm",
                "keywords": ["organic", "natural", "flowing", "harmonious"]
            }
        }
    
    def _initialize_mood_configurations(self) -> Dict[MoodCategory, Dict[str, Any]]:
        """Initialize mood-specific configurations."""
        return {
            MoodCategory.ENERGETIC: {
                "suggested_styles": [CreativeStyle.GLITCH, CreativeStyle.RHYTHMIC, CreativeStyle.FUTURISTIC],
                "color_theme": "accent_primary",
                "intensity": "high",
                "recommended_duration": (15, 45)
            },
            MoodCategory.CALM: {
                "suggested_styles": [CreativeStyle.MINIMAL, CreativeStyle.ORGANIC, CreativeStyle.CINEMATIC],
                "color_theme": "success",
                "intensity": "low",
                "recommended_duration": (60, 180)
            },
            MoodCategory.DRAMATIC: {
                "suggested_styles": [CreativeStyle.CINEMATIC, CreativeStyle.EXPERIMENTAL],
                "color_theme": "error",
                "intensity": "medium",
                "recommended_duration": (30, 90)
            },
            MoodCategory.PLAYFUL: {
                "suggested_styles": [CreativeStyle.RHYTHMIC, CreativeStyle.EXPERIMENTAL, CreativeStyle.GLITCH],
                "color_theme": "accent_secondary",
                "intensity": "high",
                "recommended_duration": (20, 60)
            },
            MoodCategory.MYSTERIOUS: {
                "suggested_styles": [CreativeStyle.EXPERIMENTAL, CreativeStyle.MINIMAL],
                "color_theme": "text_muted",
                "intensity": "low",
                "recommended_duration": (45, 120)
            },
            MoodCategory.ROMANTIC: {
                "suggested_styles": [CreativeStyle.CINEMATIC, CreativeStyle.ORGANIC],
                "color_theme": "warning",
                "intensity": "low",
                "recommended_duration": (60, 180)
            },
            MoodCategory.EPIC: {
                "suggested_styles": [CreativeStyle.CINEMATIC, CreativeStyle.FUTURISTIC],
                "color_theme": "accent_primary",
                "intensity": "high",
                "recommended_duration": (60, 180)
            },
            MoodCategory.NOSTALGIC: {
                "suggested_styles": [CreativeStyle.NOSTALGIC, CreativeStyle.ORGANIC],
                "color_theme": "warning",
                "intensity": "medium",
                "recommended_duration": (45, 120)
            }
        }
    
    def _initialize_creative_prompts(self) -> List[Dict[str, str]]:
        """Initialize creative prompts and challenges."""
        return [
            {
                "title": "The Golden Hour",
                "description": "Create a dreamy remix that captures the magic of golden hour",
                "suggestion": "Use longer cuts with warm, flowing transitions"
            },
            {
                "title": "Urban Rhythm",
                "description": "Match the pulse of city life with rapid, energetic cuts",
                "suggestion": "Sync to a fast BPM and use vertical aspect ratio"
            },
            {
                "title": "Memory Lane",
                "description": "Tell a story through nostalgic, emotional moments",
                "suggestion": "Use classic 4:3 ratio with slower pacing"
            },
            {
                "title": "Future Vision",
                "description": "Create a futuristic aesthetic with sleek, modern cuts",
                "suggestion": "Use ultrawide format with precise timing"
            },
            {
                "title": "Nature's Symphony",
                "description": "Let nature guide your rhythm and pacing",
                "suggestion": "Use organic timing that flows like water"
            },
            {
                "title": "Digital Glitch",
                "description": "Embrace the chaos of digital fragmentation",
                "suggestion": "Use very fast cuts with square format"
            },
            {
                "title": "Cinematic Epic",
                "description": "Build drama like a movie trailer",
                "suggestion": "Start slow, build intensity, use cinema ratio"
            },
            {
                "title": "Minimalist Statement",
                "description": "Say more with less - focus on essential moments",
                "suggestion": "Use very few, carefully chosen cuts"
            }
        ]
    
    def generate_random_style(self, mood: Optional[MoodCategory] = None) -> Dict[str, Any]:
        """Generate a random creative style configuration."""
        # Choose style based on mood or randomly
        if mood and mood in self.mood_configurations:
            suggested_styles = self.mood_configurations[mood]["suggested_styles"]
            style = random.choice(suggested_styles)
        else:
            style = random.choice(list(CreativeStyle))
        
        pattern = self.style_patterns[style]
        
        # Generate specific configuration
        bpm = random.randint(*pattern["bpm_range"])
        bpm_unit = random.choice(pattern["bpm_units"])
        aspect_ratio = random.choice(pattern["aspect_ratios"])
        
        # Calculate duration based on style
        base_duration = random.uniform(30, 90)
        snippet_multiplier = pattern["snippet_count_multiplier"]
        
        # Adjust for BPM if using BPM mode
        use_bpm_mode = random.choice([True, False])
        if use_bpm_mode:
            # Calculate units needed for the duration
            bpm_unit_duration = self._get_bpm_unit_duration(bpm_unit, bpm)
            num_units = max(4, int(base_duration / bpm_unit_duration))
        else:
            num_units = 16
        
        return {
            "style": style,
            "name": f"{style.value.title()} Creation",
            "description": pattern["description"],
            "keywords": pattern["keywords"],
            "length_mode": "BPM" if use_bpm_mode else "Seconds",
            "duration_seconds": base_duration,
            "bpm": bpm,
            "bpm_unit": bpm_unit,
            "num_units": num_units,
            "aspect_ratio": aspect_ratio,
            "mood": mood.value if mood else "creative",
            "export_settings": self._generate_export_settings(style, aspect_ratio)
        }
    
    def _get_bpm_unit_duration(self, bpm_unit: str, bpm: float) -> float:
        """Calculate duration of a BPM unit in seconds."""
        beat_duration = 60.0 / bpm
        unit_multipliers = {
            "1/6 Beat": 1.0/6.0,
            "1/4 Beat": 1.0/4.0,
            "1/3 Beat": 1.0/3.0,
            "1/2 Beat": 1.0/2.0,
            "Beat": 1.0,
            "Bar": 4.0
        }
        return beat_duration * unit_multipliers.get(bpm_unit, 1.0)
    
    def _generate_export_settings(self, style: CreativeStyle, aspect_ratio: str) -> Dict[str, Any]:
        """Generate export settings optimized for the style."""
        base_settings = {
            "custom_width": None,
            "custom_height": None,
            "maintain_aspect_ratio": True,
            "match_input_fps": False,
            "frame_rate": "30",
            "bitrate_mode": "crf",
            "quality_crf": 20,
            "bitrate": "8M",
            "trim_start": "",
            "trim_end": ""
        }
        
        # Style-specific adjustments
        if style == CreativeStyle.GLITCH:
            base_settings["frame_rate"] = "60"  # High frame rate for glitch
            base_settings["quality_crf"] = 18   # High quality for digital aesthetic
        elif style == CreativeStyle.CINEMATIC:
            base_settings["frame_rate"] = "24"  # Cinematic frame rate
            base_settings["quality_crf"] = 16   # Very high quality
        elif style == CreativeStyle.MINIMAL:
            base_settings["quality_crf"] = 15   # Excellent quality for minimal
        
        return base_settings
    
    def get_creative_prompt(self) -> Dict[str, str]:
        """Get a random creative prompt."""
        return random.choice(self.creative_prompts)
    
    def generate_mood_based_config(self, mood: MoodCategory) -> Dict[str, Any]:
        """Generate configuration based on specific mood."""
        mood_config = self.mood_configurations[mood]
        
        # Generate style from mood
        style_config = self.generate_random_style(mood)
        
        # Adjust duration based on mood recommendations
        min_duration, max_duration = mood_config["recommended_duration"]
        style_config["duration_seconds"] = random.uniform(min_duration, max_duration)
        
        # Add mood-specific metadata
        style_config["mood"] = mood.value
        style_config["intensity"] = mood_config["intensity"]
        style_config["color_theme"] = mood_config["color_theme"]
        
        return style_config


class BPMVisualization:
    """
    Visual BPM representation and music sync tools.
    """
    
    @staticmethod
    def create_bpm_visualizer(parent, bpm: float, bpm_unit: str) -> ctk.CTkFrame:
        """Create a visual BPM indicator."""
        visualizer_frame = ctk.CTkFrame(
            parent,
            fg_color=theme.COLORS['bg_secondary'],
            corner_radius=8
        )
        
        # Title
        title = widgets.create_label(visualizer_frame, "🎵 BPM Visualization", "heading_small")
        title.pack(pady=(15, 10))
        
        # BPM display
        bpm_display = ctk.CTkFrame(
            visualizer_frame,
            fg_color=theme.COLORS['bg_tertiary'],
            corner_radius=6
        )
        bpm_display.pack(padx=20, pady=(0, 10))
        
        # BPM number
        bpm_label = widgets.create_label(bpm_display, f"{bpm:.0f}", "heading_large")
        bpm_label.pack(pady=(15, 5))
        
        bpm_unit_label = widgets.create_label(bpm_display, f"BPM ({bpm_unit})", "body")
        bpm_unit_label.pack(pady=(0, 15))
        
        # Visual beat indicator
        beat_frame = ctk.CTkFrame(visualizer_frame, fg_color="transparent")
        beat_frame.pack(padx=20, pady=(0, 15))
        
        # Create beat dots
        beat_dots = []
        num_beats = 8
        for i in range(num_beats):
            dot = ctk.CTkFrame(
                beat_frame,
                width=12,
                height=12,
                corner_radius=6,
                fg_color=theme.COLORS['bg_tertiary']
            )
            dot.pack(side="left", padx=2)
            beat_dots.append(dot)
        
        # Add tempo description
        tempo_desc = BPMVisualization.get_tempo_description(bpm)
        tempo_label = widgets.create_label(visualizer_frame, tempo_desc, "caption")
        tempo_label.pack(pady=(0, 15))
        
        return visualizer_frame
    
    @staticmethod
    def get_tempo_description(bpm: float) -> str:
        """Get descriptive text for BPM range."""
        if bpm < 60:
            return "🐌 Very Slow - Contemplative and spacious"
        elif bpm < 80:
            return "🚶 Slow - Relaxed and flowing"
        elif bpm < 100:
            return "🚶‍♂️ Moderate - Comfortable walking pace"
        elif bpm < 120:
            return "🏃‍♀️ Medium - Energetic and engaging"
        elif bpm < 140:
            return "🏃 Fast - High energy and exciting"
        elif bpm < 160:
            return "🚀 Very Fast - Intense and driving"
        else:
            return "⚡ Extreme - Frantic and overwhelming"
    
    @staticmethod
    def calculate_snippet_timing(bpm: float, bpm_unit: str, num_units: int) -> Tuple[float, int]:
        """Calculate snippet timing based on BPM settings."""
        # Calculate duration of one beat in seconds
        beat_duration = 60.0 / bpm
        
        # Calculate duration of the selected unit
        unit_multipliers = {
            "1/6 Beat": 1.0/6.0,
            "1/4 Beat": 1.0/4.0,
            "1/3 Beat": 1.0/3.0,
            "1/2 Beat": 1.0/2.0,
            "Beat": 1.0,
            "Bar": 4.0
        }
        
        unit_duration = beat_duration * unit_multipliers.get(bpm_unit, 1.0)
        total_duration = unit_duration * num_units
        
        # Estimate number of snippets needed
        snippet_duration = unit_duration
        num_snippets = num_units
        
        return total_duration, num_snippets


class CreativeWidget(ctk.CTkFrame):
    """
    Widget for creative inspiration and randomization.
    """
    
    def __init__(self, parent, randomizer: CreativeRandomizer):
        super().__init__(
            parent,
            fg_color=theme.COLORS['bg_secondary'],
            corner_radius=8
        )
        
        self.randomizer = randomizer
        self.current_config = None
        self.create_ui()
    
    def create_ui(self):
        """Create the creative widget UI."""
        # Header
        header = layout.create_section_header(
            self,
            "🎨 Creative Inspiration",
            "Discover creative styles and configurations"
        )
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        # Quick actions
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Surprise me button
        surprise_btn = widgets.create_button(
            actions_frame,
            "🎲 Surprise Me!",
            self.generate_surprise,
            "accent",
            140
        )
        surprise_btn.pack(side="left")
        
        # Mood selector
        mood_label = widgets.create_label(actions_frame, "Mood:", "body")
        mood_label.pack(side="left", padx=(20, 5))
        
        mood_values = [mood.value.title() for mood in MoodCategory]
        self.mood_combo = widgets.create_combobox(actions_frame, ["Random"] + mood_values, 120)
        self.mood_combo.pack(side="left", padx=(0, 10))
        self.mood_combo.set("Random")
        
        # Generate button
        generate_btn = widgets.create_button(
            actions_frame,
            "Generate",
            self.generate_mood_config,
            "primary",
            100
        )
        generate_btn.pack(side="left")
        
        # Results area
        self.results_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=200
        )
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Creative prompt
        self.show_creative_prompt()
    
    def generate_surprise(self):
        """Generate a surprise configuration."""
        config = self.randomizer.generate_random_style()
        self.display_config(config)
    
    def generate_mood_config(self):
        """Generate configuration based on selected mood."""
        mood_text = self.mood_combo.get()
        
        if mood_text == "Random":
            config = self.randomizer.generate_random_style()
        else:
            # Find matching mood
            mood = None
            for m in MoodCategory:
                if m.value.title() == mood_text:
                    mood = m
                    break
            
            if mood:
                config = self.randomizer.generate_mood_based_config(mood)
            else:
                config = self.randomizer.generate_random_style()
        
        self.display_config(config)
    
    def display_config(self, config: Dict[str, Any]):
        """Display the generated configuration."""
        self.current_config = config
        
        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Config card
        config_card = widgets.create_card(self.results_frame, config["name"])
        config_card.pack(fill="x", pady=(0, 15))
        
        # Description
        desc_label = widgets.create_label(
            config_card,
            config["description"],
            "body"
        )
        desc_label.pack(padx=20, pady=(0, 10), anchor="w")
        
        # Keywords
        keywords_text = " • ".join(config["keywords"])
        keywords_label = widgets.create_label(
            config_card,
            f"Style: {keywords_text}",
            "caption"
        )
        keywords_label.pack(padx=20, pady=(0, 10), anchor="w")
        
        # Settings preview
        settings_frame = ctk.CTkFrame(config_card, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Two column layout
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        
        # Left column
        left_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Right column
        right_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # Add settings to columns
        if config["length_mode"] == "BPM":
            timing_text = f"🎵 {config['bpm']} BPM ({config['bpm_unit']})"
        else:
            timing_text = f"⏱️ {config['duration_seconds']:.0f} seconds"
        
        timing_label = widgets.create_label(left_frame, timing_text, "body")
        timing_label.pack(anchor="w")
        
        ratio_text = f"📐 {config['aspect_ratio'].split()[0]}"
        ratio_label = widgets.create_label(right_frame, ratio_text, "body")
        ratio_label.pack(anchor="w")
        
        mood_text = f"🎭 {config['mood'].title()}"
        mood_label = widgets.create_label(left_frame, mood_text, "body")
        mood_label.pack(anchor="w", pady=(5, 0))
        
        # Apply button
        apply_btn = widgets.create_button(
            config_card,
            "✨ Apply This Style",
            lambda: self.apply_config(config),
            "accent",
            160
        )
        apply_btn.pack(pady=(0, 15))
    
    def show_creative_prompt(self):
        """Show a creative prompt for inspiration."""
        prompt = self.randomizer.get_creative_prompt()
        
        prompt_card = widgets.create_card(self.results_frame, "💡 Creative Challenge")
        prompt_card.pack(fill="x", pady=(0, 15))
        
        # Prompt title
        title_label = widgets.create_label(
            prompt_card,
            prompt["title"],
            "heading_small"
        )
        title_label.pack(padx=20, pady=(0, 5), anchor="w")
        
        # Prompt description
        desc_label = widgets.create_label(
            prompt_card,
            prompt["description"],
            "body"
        )
        desc_label.pack(padx=20, pady=(0, 5), anchor="w")
        
        # Suggestion
        suggestion_label = widgets.create_label(
            prompt_card,
            f"💡 {prompt['suggestion']}",
            "body_accent"
        )
        suggestion_label.pack(padx=20, pady=(0, 15), anchor="w")
    
    def apply_config(self, config: Dict[str, Any]):
        """Apply the configuration (to be implemented by parent)."""
        # This would be implemented by the parent application
        # to apply the configuration to the actual settings
        pass


# Global creative randomizer instance
creative_randomizer = CreativeRandomizer()