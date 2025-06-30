# -*- coding: utf-8 -*-
"""
Modern Video Snippet Remixer - Redesigned Main Application.

A complete UX/UI redesign featuring:
- Step-by-step wizard workflow
- Modern dark theme with creative accents
- Visual feedback and progress indicators
- Smart preset templates
- Intuitive user guidance
- Professional creative tool aesthetic
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from typing import List, Dict, Any, Optional
from enum import Enum

# Import our modern components
from .ui_theme import theme, widgets, layout, animations, status
from .preset_templates import preset_manager, PresetTemplate
from .config_manager import ConfigManager
from .processing_worker import ProcessingWorker
from .utils import safe_print, validate_directory_path


class WizardStep(Enum):
    """Enumeration for wizard steps."""
    WELCOME = "welcome"
    PRESET_SELECTION = "preset_selection"
    INPUT_FILES = "input_files"
    CREATIVE_SETTINGS = "creative_settings"
    OUTPUT_SETTINGS = "output_settings"
    PROCESSING = "processing"
    COMPLETE = "complete"


class ModernVideoRemixerApp:
    """
    Modern redesigned Video Snippet Remixer with wizard workflow.
    """
    
    def __init__(self):
        self.root = widgets.create_window("Video Snippet Remixer - Create Amazing Remixes", 1000, 750)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.processing_worker = ProcessingWorker(self.config_manager.get_script_dir())
        self.settings = self.config_manager.config
        
        # Wizard state
        self.current_step = WizardStep.WELCOME
        self.wizard_data = {
            'selected_preset': None,
            'input_files': [],
            'custom_settings': {},
            'output_folder': self.settings.get("output_folder", ""),
            'processing_complete': False,
            'continuous_mode': self.settings.get("continuous_mode", False)
        }
        
        # Continuous mode state
        self.continuous_processing = False
        self.continuous_count = 0
        
        # UI components
        self.step_cards = {}
        self.navigation_frame = None
        self.content_frame = None
        self.progress_bar = None
        self.step_indicator = None
        
        # Check dependencies
        self.ffmpeg_available, self.ffprobe_available = self.processing_worker.get_video_processor().are_tools_available()
        
        # Build UI
        self.create_main_layout()
        self.show_step(WizardStep.WELCOME)
        
        # Window setup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Show dependency warning if needed
        if not self.ffmpeg_available or not self.ffprobe_available:
            self.show_dependency_warning()
    
    def create_main_layout(self):
        """Create the main application layout."""
        # Main container
        main_container = ctk.CTkFrame(
            self.root,
            fg_color=theme.COLORS['bg_primary'],
            corner_radius=0
        )
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header section with title and progress
        self.create_header_section(main_container)
        
        # Content area
        self.content_frame = ctk.CTkFrame(
            main_container,
            fg_color="transparent"
        )
        self.content_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Navigation footer
        self.create_navigation_section(main_container)
    
    def create_header_section(self, parent):
        """Create the header with title, subtitle, and progress indicator."""
        header_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=120
        )
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Title
        title_label = widgets.create_label(
            header_frame,
            "🎬 Video Snippet Remixer",
            "heading_large"
        )
        title_label.pack(pady=(10, 5))
        
        # Subtitle
        subtitle_label = widgets.create_label(
            header_frame,
            "Create amazing video remixes with professional templates",
            "body"
        )
        subtitle_label.pack()
        
        # Progress indicator
        self.create_progress_indicator(header_frame)
    
    def create_progress_indicator(self, parent):
        """Create visual progress indicator for wizard steps."""
        progress_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        progress_frame.pack(pady=(20, 0))
        
        # Step labels and indicators
        steps = [
            ("Welcome", "👋"),
            ("Preset", "🎨"),
            ("Files", "📁"),
            ("Settings", "⚙️"),
            ("Output", "📤"),
            ("Process", "🚀"),
            ("Done", "✨")
        ]
        
        self.step_indicators = []
        
        for i, (label, icon) in enumerate(steps):
            # Step container
            step_container = ctk.CTkFrame(
                progress_frame,
                fg_color="transparent"
            )
            step_container.pack(side="left", padx=10)
            
            # Step circle
            step_circle = ctk.CTkFrame(
                step_container,
                width=40,
                height=40,
                corner_radius=20,
                fg_color=theme.COLORS['bg_tertiary']
            )
            step_circle.pack()
            step_circle.pack_propagate(False)
            
            # Step icon
            step_icon = widgets.create_label(
                step_circle,
                icon,
                "body_large"
            )
            step_icon.place(relx=0.5, rely=0.5, anchor="center")
            
            # Step label
            step_label = widgets.create_label(
                step_container,
                label,
                "caption"
            )
            step_label.pack(pady=(5, 0))
            
            # Store references
            self.step_indicators.append({
                'circle': step_circle,
                'icon': step_icon,
                'label': step_label
            })
            
            # Add connector line (except for last step)
            if i < len(steps) - 1:
                connector = ctk.CTkFrame(
                    progress_frame,
                    width=30,
                    height=2,
                    fg_color=theme.COLORS['bg_tertiary']
                )
                connector.pack(side="left", pady=(15, 0))
    
    def create_navigation_section(self, parent):
        """Create navigation buttons at the bottom."""
        self.navigation_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=80
        )
        self.navigation_frame.pack(side="bottom", fill="x")
        self.navigation_frame.pack_propagate(False)
        
        # Button frame
        button_frame = ctk.CTkFrame(
            self.navigation_frame,
            fg_color="transparent"
        )
        button_frame.pack(expand=True)
        
        # Back button
        self.back_button = widgets.create_button(
            button_frame,
            "← Back",
            self.go_back,
            "secondary",
            120
        )
        self.back_button.pack(side="left", padx=(0, 20))
        
        # Next button
        self.next_button = widgets.create_button(
            button_frame,
            "Next →",
            self.go_next,
            "primary",
            120
        )
        self.next_button.pack(side="right", padx=(20, 0))
        
        # Center action button (changes based on step)
        self.action_button = widgets.create_button(
            button_frame,
            "Get Started",
            self.perform_action,
            "accent",
            180
        )
        self.action_button.pack()
    
    def show_step(self, step: WizardStep):
        """Show a specific wizard step."""
        self.current_step = step
        self.update_progress_indicator()
        self.update_navigation_buttons()
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show appropriate step content
        if step == WizardStep.WELCOME:
            self.show_welcome_step()
        elif step == WizardStep.PRESET_SELECTION:
            self.show_preset_selection_step()
        elif step == WizardStep.INPUT_FILES:
            self.show_input_files_step()
        elif step == WizardStep.CREATIVE_SETTINGS:
            self.show_creative_settings_step()
        elif step == WizardStep.OUTPUT_SETTINGS:
            self.show_output_settings_step()
        elif step == WizardStep.PROCESSING:
            self.show_processing_step()
        elif step == WizardStep.COMPLETE:
            self.show_complete_step()
    
    def show_welcome_step(self):
        """Show the welcome/introduction step."""
        welcome_card = widgets.create_card(self.content_frame)
        welcome_card.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Content container
        content = ctk.CTkFrame(welcome_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Main welcome message
        welcome_title = widgets.create_label(
            content,
            "Welcome to the Future of Video Remixing",
            "heading_large"
        )
        welcome_title.pack(pady=(0, 20))
        
        # Feature highlights
        features_frame = ctk.CTkFrame(content, fg_color="transparent")
        features_frame.pack(fill="x", pady=20)
        
        features = [
            ("🎨", "Smart Presets", "Professional templates for every creative need"),
            ("⚡", "Lightning Fast", "Professional results in seconds, not hours"),
            ("🎬", "Cinema Quality", "HD output with customizable settings"),
            ("🎵", "Beat Perfect", "Sync to music with BPM-based cutting")
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            feature_row = ctk.CTkFrame(features_frame, fg_color="transparent")
            feature_row.pack(fill="x", pady=10)
            
            icon_label = widgets.create_label(feature_row, icon, "heading_medium")
            icon_label.pack(side="left", padx=(0, 15))
            
            text_frame = ctk.CTkFrame(feature_row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            
            title_label = widgets.create_label(text_frame, title, "heading_small")
            title_label.pack(anchor="w")
            
            desc_label = widgets.create_label(text_frame, desc, "body")
            desc_label.pack(anchor="w")
        
        # Dependency status
        self.create_dependency_status(content)
        
        # Quick stats or tips
        tips_frame = ctk.CTkFrame(content, fg_color=theme.COLORS['bg_tertiary'], corner_radius=8)
        tips_frame.pack(fill="x", pady=(30, 0))
        
        tips_title = widgets.create_label(tips_frame, "💡 Pro Tip", "heading_small")
        tips_title.pack(pady=(15, 5), padx=20, anchor="w")
        
        tips_text = widgets.create_label(
            tips_frame,
            "Start with a preset template for best results, then customize to your heart's content!",
            "body"
        )
        tips_text.pack(pady=(0, 15), padx=20, anchor="w")
    
    def show_preset_selection_step(self):
        """Show the preset selection step."""
        preset_card = widgets.create_card(self.content_frame, "Choose Your Creative Style")
        preset_card.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(
            preset_card,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Quick actions at top
        quick_actions = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        quick_actions.pack(fill="x", pady=(0, 20))
        
        surprise_btn = widgets.create_button(
            quick_actions,
            "🎲 Surprise Me!",
            self.surprise_me,
            "accent",
            160
        )
        surprise_btn.pack(side="left")
        
        recent_label = widgets.create_label(quick_actions, "Recent:", "body")
        recent_label.pack(side="right", padx=(20, 10))
        
        # Show preset categories
        categories = preset_manager.get_presets_by_category()
        
        for category_name, preset_names in categories.items():
            # Category header
            category_header = layout.create_section_header(
                scroll_frame,
                category_name,
                f"{len(preset_names)} templates available"
            )
            category_header.pack(fill="x", pady=(20, 10))
            
            # Preset grid
            presets_grid = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            presets_grid.pack(fill="x", pady=(0, 10))
            
            # Configure grid
            cols = 2
            for i in range(cols):
                presets_grid.columnconfigure(i, weight=1)
            
            # Add preset cards
            for i, preset_name in enumerate(preset_names):
                preset = preset_manager.get_preset(preset_name)
                if preset:
                    row = i // cols
                    col = i % cols
                    
                    preset_card_widget = self.create_preset_card(presets_grid, preset)
                    preset_card_widget.grid(
                        row=row, column=col,
                        padx=10, pady=5,
                        sticky="ew"
                    )
    
    def create_preset_card(self, parent, preset: PresetTemplate) -> ctk.CTkFrame:
        """Create a preset selection card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.COLORS['bg_tertiary'],
            corner_radius=8,
            border_width=2,
            border_color=theme.COLORS['border_primary']
        )
        
        # Make card clickable
        def select_preset():
            self.wizard_data['selected_preset'] = preset.name
            # Update visual selection
            self.update_preset_selection_visual(card)
            # Enable next button
            self.next_button.configure(state="normal")
        
        card.bind("<Button-1>", lambda e: select_preset())
        
        # Card content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header with icon and title
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")
        
        icon_label = widgets.create_label(header, preset.icon, "heading_medium")
        icon_label.pack(side="left")
        
        title_label = widgets.create_label(header, preset.name, "heading_small")
        title_label.pack(side="left", padx=(10, 0))
        
        # Energy level badge
        energy_badge = status.create_status_badge(header, preset.energy_level.title(), "accent")
        energy_badge.pack(side="right")
        
        # Description
        desc_label = widgets.create_label(content, preset.description, "body")
        desc_label.pack(fill="x", pady=(10, 5))
        
        # Use case
        use_case_label = widgets.create_label(content, f"Best for: {preset.use_case}", "caption")
        use_case_label.pack(fill="x")
        
        # Technical specs
        specs_frame = ctk.CTkFrame(content, fg_color="transparent")
        specs_frame.pack(fill="x", pady=(10, 0))
        
        # Duration info
        if preset.length_mode == "Seconds":
            duration_text = f"{preset.duration_seconds}s"
        else:
            duration_text = f"{preset.bpm} BPM"
        
        duration_label = widgets.create_label(specs_frame, f"⏱️ {duration_text}", "caption")
        duration_label.pack(side="left")
        
        # Quality info
        quality_label = widgets.create_label(specs_frame, f"🎯 {preset.aspect_ratio.split()[0]}", "caption")
        quality_label.pack(side="right")
        
        return card
    
    def show_input_files_step(self):
        """Show the input files selection step."""
        files_card = widgets.create_card(self.content_frame, "Add Your Video Files")
        files_card.pack(fill="both", expand=True, padx=30, pady=20)
        
        content = ctk.CTkFrame(files_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # File drop zone
        drop_zone = self.create_file_drop_zone(content)
        drop_zone.pack(fill="both", expand=True, pady=(0, 20))
        
        # File list
        files_list_frame = ctk.CTkFrame(content, fg_color=theme.COLORS['bg_tertiary'], corner_radius=8)
        files_list_frame.pack(fill="x", pady=(0, 20))
        
        list_header = widgets.create_label(files_list_frame, "📁 Selected Files", "heading_small")
        list_header.pack(pady=(15, 10), padx=20, anchor="w")
        
        # Scrollable file list
        self.file_list_scroll = ctk.CTkScrollableFrame(
            files_list_frame,
            height=150,
            fg_color="transparent"
        )
        self.file_list_scroll.pack(fill="both", padx=20, pady=(0, 15))
        
        # File info summary
        self.create_file_info_summary(content)
        
        # Update file list display
        self.update_file_list_display()
    
    def create_file_drop_zone(self, parent) -> ctk.CTkFrame:
        """Create a visual file drop zone."""
        drop_zone = ctk.CTkFrame(
            parent,
            fg_color=theme.COLORS['bg_secondary'],
            border_width=2,
            border_color=theme.COLORS['border_primary'],
            corner_radius=12
        )
        
        # Drop zone content
        drop_content = ctk.CTkFrame(drop_zone, fg_color="transparent")
        drop_content.pack(expand=True)
        
        # Icon
        drop_icon = widgets.create_label(drop_content, "📁", "heading_large")
        drop_icon.pack(pady=(20, 10))
        
        # Instructions
        drop_title = widgets.create_label(drop_content, "Drag & Drop Video Files", "heading_medium")
        drop_title.pack()
        
        drop_subtitle = widgets.create_label(
            drop_content,
            "Or click browse to select files",
            "body"
        )
        drop_subtitle.pack(pady=(5, 15))
        
        # Browse button
        browse_btn = widgets.create_button(
            drop_content,
            "📂 Browse Files",
            self.browse_input_files,
            "primary",
            160
        )
        browse_btn.pack(pady=(0, 20))
        
        # Supported formats
        formats_label = widgets.create_label(
            drop_content,
            "Supports: MP4, AVI, MOV, MKV, WEBM, FLV, WMV",
            "caption"
        )
        formats_label.pack(pady=(0, 20))
        
        return drop_zone
    
    def show_creative_settings_step(self):
        """Show creative settings customization step."""
        settings_card = widgets.create_card(self.content_frame, "Fine-tune Your Creation")
        settings_card.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Get selected preset for defaults
        preset_name = self.wizard_data.get('selected_preset')
        preset = preset_manager.get_preset(preset_name) if preset_name else None
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(
            settings_card,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Current preset info
        if preset:
            self.show_current_preset_info(scroll_frame, preset)
        
        # Length settings
        self.create_length_settings_section(scroll_frame, preset)
        
        # Aspect ratio settings
        self.create_aspect_ratio_section(scroll_frame, preset)
        
        # Advanced settings toggle
        self.create_advanced_settings_section(scroll_frame)
    
    def show_output_settings_step(self):
        """Show output settings step."""
        output_card = widgets.create_card(self.content_frame, "Output Configuration")
        output_card.pack(fill="both", expand=True, padx=30, pady=20)
        
        content = ctk.CTkFrame(output_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Output folder selection
        self.create_output_folder_section(content)
        
        # Continuous mode toggle
        self.create_continuous_mode_section(content)
        
        # Quality settings
        self.create_quality_settings_section(content)
        
        # Final preview
        self.create_final_preview_section(content)
    
    def show_processing_step(self):
        """Show the processing step with live progress."""
        process_card = widgets.create_card(self.content_frame, "🚀 Creating Your Remix")
        process_card.pack(fill="both", expand=True, padx=30, pady=20)
        
        content = ctk.CTkFrame(process_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Progress visualization
        self.create_processing_visualization(content)
        
        # Start processing
        self.start_processing()
    
    def show_complete_step(self):
        """Show completion step with results."""
        complete_card = widgets.create_card(self.content_frame, "✨ Remix Complete!")
        complete_card.pack(fill="both", expand=True, padx=30, pady=20)
        
        content = ctk.CTkFrame(complete_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Success animation/visual
        success_frame = ctk.CTkFrame(content, fg_color="transparent")
        success_frame.pack(fill="x", pady=(0, 30))
        
        success_icon = widgets.create_label(success_frame, "🎉", "heading_large")
        success_icon.pack()
        
        success_title = widgets.create_label(
            success_frame,
            "Your Amazing Remix is Ready!",
            "heading_medium"
        )
        success_title.pack(pady=(10, 5))
        
        # File info and actions
        self.create_completion_actions(content)
    
    # Navigation methods
    def go_back(self):
        """Go to the previous step."""
        steps = list(WizardStep)
        current_index = steps.index(self.current_step)
        if current_index > 0:
            self.show_step(steps[current_index - 1])
    
    def go_next(self):
        """Go to the next step."""
        steps = list(WizardStep)
        current_index = steps.index(self.current_step)
        if current_index < len(steps) - 1:
            # Validate current step before proceeding
            if self.validate_current_step():
                self.show_step(steps[current_index + 1])
    
    def perform_action(self):
        """Perform the main action for the current step."""
        if self.current_step == WizardStep.WELCOME:
            self.show_step(WizardStep.PRESET_SELECTION)
        elif self.current_step == WizardStep.COMPLETE:
            self.start_new_project()
    
    def validate_current_step(self) -> bool:
        """Validate the current step before proceeding."""
        if self.current_step == WizardStep.PRESET_SELECTION:
            if not self.wizard_data.get('selected_preset'):
                messagebox.showwarning("Selection Required", "Please select a preset template to continue.")
                return False
        elif self.current_step == WizardStep.INPUT_FILES:
            if not self.wizard_data.get('input_files'):
                messagebox.showwarning("Files Required", "Please add at least one video file to continue.")
                return False
        elif self.current_step == WizardStep.OUTPUT_SETTINGS:
            if not self.wizard_data.get('output_folder'):
                messagebox.showwarning("Output Folder Required", "Please select an output folder.")
                return False
        
        return True
    
    def update_progress_indicator(self):
        """Update the visual progress indicator."""
        steps = list(WizardStep)
        current_index = steps.index(self.current_step)
        
        for i, indicator in enumerate(self.step_indicators):
            if i <= current_index:
                # Completed or current step
                indicator['circle'].configure(fg_color=theme.COLORS['accent_primary'])
                indicator['label'].configure(text_color=theme.COLORS['text_primary'])
            else:
                # Future step
                indicator['circle'].configure(fg_color=theme.COLORS['bg_tertiary'])
                indicator['label'].configure(text_color=theme.COLORS['text_muted'])
    
    def update_navigation_buttons(self):
        """Update navigation button states and text."""
        steps = list(WizardStep)
        current_index = steps.index(self.current_step)
        
        # Back button
        if current_index == 0:
            self.back_button.configure(state="disabled")
        else:
            self.back_button.configure(state="normal")
        
        # Next button
        if current_index == len(steps) - 1:
            self.next_button.configure(state="disabled")
        else:
            self.next_button.configure(state="normal")
        
        # Action button
        if self.current_step == WizardStep.WELCOME:
            self.action_button.configure(text="Get Started")
            self.action_button.pack()
        elif self.current_step == WizardStep.COMPLETE:
            self.action_button.configure(text="🔄 New Project")
            self.action_button.pack()
        else:
            self.action_button.pack_forget()
    
    # Helper methods (stubs for now - will be implemented based on original functionality)
    def surprise_me(self):
        """Apply random creative settings."""
        surprise_settings = preset_manager.get_surprise_settings()
        # Apply surprise settings
        messagebox.showinfo("Surprise!", f"Applied: {surprise_settings['name']}")
    
    def browse_input_files(self):
        """Browse for input video files."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv"),
            ("All files", "*.*")
        ]
        
        filepaths = filedialog.askopenfilenames(
            title="Select Input Video Files",
            filetypes=filetypes
        )
        
        if filepaths:
            self.wizard_data['input_files'].extend(filepaths)
            self.update_file_list_display()
    
    def update_file_list_display(self):
        """Update the file list display."""
        # Clear existing
        for widget in self.file_list_scroll.winfo_children():
            widget.destroy()
        
        # Add files
        for filepath in self.wizard_data['input_files']:
            file_item = self.create_file_list_item(self.file_list_scroll, filepath)
            file_item.pack(fill="x", pady=2)
    
    def create_file_list_item(self, parent, filepath: str) -> ctk.CTkFrame:
        """Create a file list item widget."""
        item = ctk.CTkFrame(parent, fg_color=theme.COLORS['bg_secondary'], corner_radius=6)
        
        # File info
        filename = os.path.basename(filepath)
        file_label = widgets.create_label(item, f"📹 {filename}", "body")
        file_label.pack(side="left", padx=10, pady=8)
        
        # Remove button
        remove_btn = widgets.create_button(
            item,
            "✕",
            lambda: self.remove_file(filepath),
            "secondary",
            30
        )
        remove_btn.pack(side="right", padx=10, pady=5)
        
        return item
    
    def remove_file(self, filepath: str):
        """Remove a file from the input list."""
        if filepath in self.wizard_data['input_files']:
            self.wizard_data['input_files'].remove(filepath)
            self.update_file_list_display()
    
    def create_dependency_status(self, parent):
        """Create dependency status display."""
        status_frame = ctk.CTkFrame(parent, fg_color=theme.COLORS['bg_tertiary'], corner_radius=8)
        status_frame.pack(fill="x", pady=(30, 0))
        
        status_title = widgets.create_label(status_frame, "🔧 System Status", "heading_small")
        status_title.pack(pady=(15, 10), padx=20, anchor="w")
        
        # FFmpeg status
        ffmpeg_status = "✅ Ready" if self.ffmpeg_available else "❌ Missing"
        ffmpeg_label = widgets.create_label(
            status_frame,
            f"FFmpeg: {ffmpeg_status}",
            "success" if self.ffmpeg_available else "error"
        )
        ffmpeg_label.pack(padx=20, anchor="w")
        
        # FFprobe status
        ffprobe_status = "✅ Ready" if self.ffprobe_available else "❌ Missing"
        ffprobe_label = widgets.create_label(
            status_frame,
            f"FFprobe: {ffprobe_status}",
            "success" if self.ffprobe_available else "error"
        )
        ffprobe_label.pack(padx=20, pady=(0, 15), anchor="w")
    
    # Additional helper methods would be implemented here...
    def show_dependency_warning(self):
        """Show dependency warning if FFmpeg is missing."""
        if not self.ffmpeg_available or not self.ffprobe_available:
            missing = []
            if not self.ffmpeg_available:
                missing.append("FFmpeg")
            if not self.ffprobe_available:
                missing.append("FFprobe")
            
            messagebox.showwarning(
                "Dependencies Missing",
                f"{' and '.join(missing)} not found in PATH.\n\n"
                "Please install FFmpeg and add it to your system's PATH.\n"
                "Video processing will not work without these tools."
            )
    
    def create_continuous_mode_section(self, parent):
        """Create continuous mode toggle section."""
        continuous_card = widgets.create_card(parent, "🔄 Continuous Mode")
        continuous_card.pack(fill="x", pady=(0, 20))
        
        content = ctk.CTkFrame(continuous_card, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=(0, 15))
        
        # Continuous mode switch
        self.continuous_switch = widgets.create_switch(
            content,
            "Keep making videos automatically"
        )
        self.continuous_switch.pack(pady=10)
        
        # Set initial state
        if self.wizard_data.get('continuous_mode', False):
            self.continuous_switch.select()
        
        # Description
        desc_label = widgets.create_label(
            content,
            "When enabled, the remixer will continuously create new videos with random variations.",
            "caption"
        )
        desc_label.pack(pady=(0, 10))
        
        # Counter display
        self.continuous_counter_label = widgets.create_label(
            content,
            "",
            "body_accent"
        )
        self.continuous_counter_label.pack()
    
    def on_closing(self):
        """Handle application closing."""
        # Save continuous mode setting
        if hasattr(self, 'continuous_switch'):
            self.wizard_data['continuous_mode'] = self.continuous_switch.get()
            self.settings['continuous_mode'] = self.continuous_switch.get()
        
        # Save settings
        self.config_manager.save_config(self.settings)
        self.root.destroy()


def main():
    """Main entry point for the modern application."""
    try:
        # Check if CustomTkinter is available
        import customtkinter
        app = ModernVideoRemixerApp()
        app.root.mainloop()
    except ImportError:
        # Fallback to original if CustomTkinter not available
        messagebox.showerror(
            "Missing Dependency",
            "CustomTkinter is required for the modern UI.\n"
            "Please install it with: pip install customtkinter\n\n"
            "Falling back to classic interface..."
        )
        # Import and run original app
        from .main_app import main as original_main
        original_main()


if __name__ == "__main__":
    main()