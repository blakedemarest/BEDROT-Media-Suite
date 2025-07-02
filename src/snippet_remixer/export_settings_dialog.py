# -*- coding: utf-8 -*-
"""
Export Settings Dialog for Video Snippet Remixer.

Provides comprehensive export settings including:
- Custom resolution with aspect ratio maintenance
- Frame rate selection
- Quality settings
- Input trimming options
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .utils import safe_print


class ExportSettingsDialog:
    """
    Dialog for configuring video export settings.
    """
    
    def __init__(self, parent, config_manager, current_aspect_ratio="16:9"):
        self.parent = parent
        self.config_manager = config_manager
        self.current_aspect_ratio = current_aspect_ratio
        self.result = None
        
        # Load existing settings or defaults
        self.export_settings = self.config_manager.get_export_settings()
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Settings")
        self.dialog.geometry("500x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Variables
        self.setup_variables()
        
        # Create UI
        self.create_ui()
        
        # Load current settings
        self.load_settings()
        
        # Bind events
        self.bind_events()
        
        # Focus
        self.dialog.focus_set()
    
    def setup_variables(self):
        """Initialize tkinter variables."""
        # Resolution variables
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.maintain_aspect_var = tk.BooleanVar(value=True)
        self.use_preset_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar()
        
        # Frame rate variables
        self.frame_rate_var = tk.StringVar(value="30")
        self.match_input_fps_var = tk.BooleanVar(value=False)
        
        # Quality variables
        self.quality_var = tk.IntVar(value=23)
        self.bitrate_mode_var = tk.StringVar(value="crf")
        self.bitrate_var = tk.StringVar(value="5M")
        
        # Trim variables
        self.enable_trim_var = tk.BooleanVar(value=False)
        self.trim_start_var = tk.StringVar()
        self.trim_end_var = tk.StringVar()
        
        # Verification variables
        self.check_black_bars_var = tk.BooleanVar(value=False)
        self.verify_snippets_var = tk.BooleanVar(value=False)
    
    def create_ui(self):
        """Create the dialog UI."""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Resolution Section
        self.create_resolution_section(main_frame)
        
        # Frame Rate Section
        self.create_framerate_section(main_frame)
        
        # Quality Section
        self.create_quality_section(main_frame)
        
        # Trim Section
        self.create_trim_section(main_frame)
        
        # Verification Section
        self.create_verification_section(main_frame)
        
        # Buttons
        self.create_buttons(main_frame)
    
    def create_resolution_section(self, parent):
        """Create resolution settings section."""
        # Resolution Frame
        res_frame = ttk.LabelFrame(parent, text="Resolution", padding="10")
        res_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Preset selection
        preset_check = ttk.Checkbutton(
            res_frame,
            text="Use Preset:",
            variable=self.use_preset_var,
            command=self.toggle_resolution_mode
        )
        preset_check.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Common presets
        presets = [
            "1920×1080 (16:9)",
            "1280×720 (16:9)",
            "1080×1920 (9:16)",
            "720×1280 (9:16)",
            "1080×1080 (1:1)",
            "720×720 (1:1)",
            "3840×2160 (16:9)",
            "2160×3840 (9:16)"
        ]
        
        self.preset_combo = ttk.Combobox(
            res_frame,
            textvariable=self.preset_var,
            values=presets,
            state="readonly",
            width=20
        )
        self.preset_combo.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_selected)
        
        # Custom resolution
        ttk.Label(res_frame, text="Custom:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Width
        ttk.Label(res_frame, text="Width:").grid(row=1, column=1, padx=(20, 5), sticky=tk.E)
        self.width_entry = ttk.Entry(res_frame, textvariable=self.width_var, width=8)
        self.width_entry.grid(row=1, column=2, padx=5, sticky=tk.W)
        
        # Height
        ttk.Label(res_frame, text="Height:").grid(row=1, column=3, padx=(20, 5), sticky=tk.E)
        self.height_entry = ttk.Entry(res_frame, textvariable=self.height_var, width=8)
        self.height_entry.grid(row=1, column=4, padx=5, sticky=tk.W)
        
        # Maintain aspect ratio
        self.maintain_check = ttk.Checkbutton(
            res_frame,
            text="Maintain aspect ratio",
            variable=self.maintain_aspect_var
        )
        self.maintain_check.grid(row=2, column=1, columnspan=3, pady=5, sticky=tk.W)
        
        # Info label
        info_label = ttk.Label(
            res_frame,
            text="Note: Leave empty to use aspect ratio from main window",
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        info_label.grid(row=3, column=0, columnspan=5, pady=(5, 0))
    
    def create_framerate_section(self, parent):
        """Create frame rate settings section."""
        fps_frame = ttk.LabelFrame(parent, text="Frame Rate", padding="10")
        fps_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Match input checkbox
        match_check = ttk.Checkbutton(
            fps_frame,
            text="Match input video",
            variable=self.match_input_fps_var,
            command=self.toggle_fps_mode
        )
        match_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # FPS selection
        ttk.Label(fps_frame, text="Target FPS:").grid(row=1, column=0, sticky=tk.W, padx=(20, 5))
        
        fps_values = ["12", "24", "25", "30", "48", "50", "60"]
        self.fps_combo = ttk.Combobox(
            fps_frame,
            textvariable=self.frame_rate_var,
            values=fps_values,
            state="readonly",
            width=10
        )
        self.fps_combo.grid(row=1, column=1, padx=5, sticky=tk.W)
    
    def create_quality_section(self, parent):
        """Create quality settings section."""
        quality_frame = ttk.LabelFrame(parent, text="Quality", padding="10")
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Quality mode
        ttk.Label(quality_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        
        crf_radio = ttk.Radiobutton(
            quality_frame,
            text="Constant Quality (CRF)",
            variable=self.bitrate_mode_var,
            value="crf",
            command=self.toggle_quality_mode
        )
        crf_radio.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=5)
        
        bitrate_radio = ttk.Radiobutton(
            quality_frame,
            text="Target Bitrate",
            variable=self.bitrate_mode_var,
            value="bitrate",
            command=self.toggle_quality_mode
        )
        bitrate_radio.grid(row=0, column=3, columnspan=2, sticky=tk.W, padx=5)
        
        # CRF slider
        ttk.Label(quality_frame, text="CRF:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        self.crf_scale = ttk.Scale(
            quality_frame,
            from_=0,
            to=51,
            orient=tk.HORIZONTAL,
            variable=self.quality_var,
            command=self.update_quality_label
        )
        self.crf_scale.grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=(10, 5))
        
        self.crf_label = ttk.Label(quality_frame, text="23 (Good)")
        self.crf_label.grid(row=1, column=4, padx=5, pady=(10, 5))
        
        # Bitrate entry
        ttk.Label(quality_frame, text="Bitrate:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.bitrate_entry = ttk.Entry(
            quality_frame,
            textvariable=self.bitrate_var,
            width=10,
            state=tk.DISABLED
        )
        self.bitrate_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(quality_frame, text="(e.g., 5M, 8000k)").grid(row=2, column=2, columnspan=2, sticky=tk.W)
        
        # Quality guide
        guide_text = "CRF: 0=lossless, 18=high, 23=good, 28=acceptable, 51=worst"
        guide_label = ttk.Label(quality_frame, text=guide_text, font=("TkDefaultFont", 8), foreground="gray")
        guide_label.grid(row=3, column=0, columnspan=5, pady=(5, 0))
    
    def create_trim_section(self, parent):
        """Create trim settings section."""
        trim_frame = ttk.LabelFrame(parent, text="Trim Input", padding="10")
        trim_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Enable trim
        enable_check = ttk.Checkbutton(
            trim_frame,
            text="Enable trimming",
            variable=self.enable_trim_var,
            command=self.toggle_trim_mode
        )
        enable_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Start time
        ttk.Label(trim_frame, text="Start time:").grid(row=1, column=0, sticky=tk.W, padx=(20, 5))
        self.trim_start_entry = ttk.Entry(
            trim_frame,
            textvariable=self.trim_start_var,
            width=15,
            state=tk.DISABLED
        )
        self.trim_start_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        
        # End time
        ttk.Label(trim_frame, text="End time:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        self.trim_end_entry = ttk.Entry(
            trim_frame,
            textvariable=self.trim_end_var,
            width=15,
            state=tk.DISABLED
        )
        self.trim_end_entry.grid(row=1, column=3, padx=5, sticky=tk.W)
        
        # Format hint
        hint_label = ttk.Label(
            trim_frame,
            text="Format: HH:MM:SS or MM:SS or seconds",
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        hint_label.grid(row=2, column=0, columnspan=4, pady=(5, 0))
    
    def create_verification_section(self, parent):
        """Create verification settings section."""
        verify_frame = ttk.LabelFrame(parent, text="Output Verification", padding="10")
        verify_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Check black bars
        black_bars_check = ttk.Checkbutton(
            verify_frame,
            text="Check for black bars in output (uses blackdetect filter)",
            variable=self.check_black_bars_var
        )
        black_bars_check.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Verify snippets
        snippets_check = ttk.Checkbutton(
            verify_frame,
            text="Verify dimensions of individual snippets (slower)",
            variable=self.verify_snippets_var
        )
        snippets_check.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Info label
        info_label = ttk.Label(
            verify_frame,
            text="Note: Verification helps ensure output quality but may increase processing time",
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        info_label.grid(row=2, column=0, pady=(5, 0))
    
    def create_buttons(self, parent):
        """Create dialog buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Apply button
        apply_btn = ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_settings
        )
        apply_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        # Reset button
        reset_btn = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults
        )
        reset_btn.pack(side=tk.LEFT)
    
    def bind_events(self):
        """Bind event handlers."""
        # Width/height change events
        self.width_var.trace('w', self.on_dimension_changed)
        self.height_var.trace('w', self.on_dimension_changed)
        
        # Dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def toggle_resolution_mode(self):
        """Toggle between preset and custom resolution."""
        if self.use_preset_var.get():
            self.preset_combo.configure(state="readonly")
            self.width_entry.configure(state=tk.DISABLED)
            self.height_entry.configure(state=tk.DISABLED)
            self.maintain_check.configure(state=tk.DISABLED)
        else:
            self.preset_combo.configure(state=tk.DISABLED)
            self.width_entry.configure(state=tk.NORMAL)
            self.height_entry.configure(state=tk.NORMAL)
            self.maintain_check.configure(state=tk.NORMAL)
    
    def toggle_fps_mode(self):
        """Toggle between match input and custom FPS."""
        if self.match_input_fps_var.get():
            self.fps_combo.configure(state=tk.DISABLED)
        else:
            self.fps_combo.configure(state="readonly")
    
    def toggle_quality_mode(self):
        """Toggle between CRF and bitrate modes."""
        if self.bitrate_mode_var.get() == "crf":
            self.crf_scale.configure(state=tk.NORMAL)
            self.bitrate_entry.configure(state=tk.DISABLED)
        else:
            self.crf_scale.configure(state=tk.DISABLED)
            self.bitrate_entry.configure(state=tk.NORMAL)
    
    def toggle_trim_mode(self):
        """Toggle trim input fields."""
        if self.enable_trim_var.get():
            self.trim_start_entry.configure(state=tk.NORMAL)
            self.trim_end_entry.configure(state=tk.NORMAL)
        else:
            self.trim_start_entry.configure(state=tk.DISABLED)
            self.trim_end_entry.configure(state=tk.DISABLED)
    
    def on_preset_selected(self, event=None):
        """Handle preset selection."""
        preset = self.preset_var.get()
        if "×" in preset:
            # Extract dimensions from preset
            dims = preset.split(" ")[0]
            width, height = dims.split("×")
            self.width_var.set(width)
            self.height_var.set(height)
    
    def on_dimension_changed(self, *args):
        """Handle dimension change for aspect ratio maintenance."""
        if not self.maintain_aspect_var.get() or self.use_preset_var.get():
            return
        
        # This would need the original aspect ratio to maintain it properly
        # For now, we'll just validate the input
        pass
    
    def update_quality_label(self, value):
        """Update quality label based on CRF value."""
        crf = int(float(value))
        if crf == 0:
            quality = "Lossless"
        elif crf <= 18:
            quality = "High"
        elif crf <= 23:
            quality = "Good"
        elif crf <= 28:
            quality = "Acceptable"
        elif crf <= 35:
            quality = "Low"
        else:
            quality = "Very Low"
        
        self.crf_label.config(text=f"{crf} ({quality})")
    
    def load_settings(self):
        """Load current settings into UI."""
        settings = self.export_settings
        
        # Resolution
        if settings.get("custom_width") and settings.get("custom_height"):
            self.use_preset_var.set(False)
            self.width_var.set(str(settings["custom_width"]))
            self.height_var.set(str(settings["custom_height"]))
        else:
            self.use_preset_var.set(True)
            # Set default preset based on current aspect ratio
            if self.current_aspect_ratio == "16:9":
                self.preset_var.set("1280×720 (16:9)")
            elif self.current_aspect_ratio == "9:16":
                self.preset_var.set("720×1280 (9:16)")
            elif self.current_aspect_ratio == "1:1":
                self.preset_var.set("720×720 (1:1)")
        
        self.maintain_aspect_var.set(settings.get("maintain_aspect_ratio", True))
        
        # Frame rate
        if settings.get("match_input_fps", False):
            self.match_input_fps_var.set(True)
        else:
            self.frame_rate_var.set(str(settings.get("frame_rate", "30")))
        
        # Quality
        if settings.get("bitrate_mode") == "bitrate":
            self.bitrate_mode_var.set("bitrate")
            self.bitrate_var.set(settings.get("bitrate", "5M"))
        else:
            self.bitrate_mode_var.set("crf")
            self.quality_var.set(settings.get("quality_crf", 23))
        
        # Trim
        if settings.get("trim_start") or settings.get("trim_end"):
            self.enable_trim_var.set(True)
            self.trim_start_var.set(settings.get("trim_start", ""))
            self.trim_end_var.set(settings.get("trim_end", ""))
        
        # Verification
        self.check_black_bars_var.set(settings.get("check_black_bars", False))
        self.verify_snippets_var.set(settings.get("verify_snippets", False))
        
        # Update UI states
        self.toggle_resolution_mode()
        self.toggle_fps_mode()
        self.toggle_quality_mode()
        self.toggle_trim_mode()
    
    def validate_settings(self):
        """Validate current settings."""
        # Validate resolution if custom
        if not self.use_preset_var.get():
            try:
                width = int(self.width_var.get())
                height = int(self.height_var.get())
                if width <= 0 or height <= 0:
                    raise ValueError("Dimensions must be positive")
                if width > 7680 or height > 4320:  # 8K limit
                    raise ValueError("Dimensions exceed maximum (7680×4320)")
                # Ensure dimensions are even (required for many codecs)
                if width % 2 != 0 or height % 2 != 0:
                    raise ValueError("Width and height must be even numbers")
            except ValueError as e:
                messagebox.showerror("Invalid Resolution", str(e), parent=self.dialog)
                return False
        
        # Validate trim times if enabled
        if self.enable_trim_var.get():
            from .utils import parse_time_to_seconds
            start_str = self.trim_start_var.get().strip()
            end_str = self.trim_end_var.get().strip()
            
            if start_str:
                start_time = parse_time_to_seconds(start_str)
                if start_time is None:
                    messagebox.showerror("Invalid Start Time", 
                                       "Please enter time in format HH:MM:SS, MM:SS, or seconds",
                                       parent=self.dialog)
                    return False
            
            if end_str:
                end_time = parse_time_to_seconds(end_str)
                if end_time is None:
                    messagebox.showerror("Invalid End Time", 
                                       "Please enter time in format HH:MM:SS, MM:SS, or seconds",
                                       parent=self.dialog)
                    return False
                
                if start_str and end_time <= parse_time_to_seconds(start_str):
                    messagebox.showerror("Invalid Time Range", 
                                       "End time must be after start time",
                                       parent=self.dialog)
                    return False
        
        return True
    
    def apply_settings(self):
        """Apply and save settings."""
        if not self.validate_settings():
            return
        
        # Build settings dictionary
        settings = {}
        
        # Resolution
        if self.use_preset_var.get() and self.preset_var.get():
            # Extract from preset
            preset = self.preset_var.get()
            if "×" in preset:
                dims = preset.split(" ")[0]
                width, height = dims.split("×")
                settings["custom_width"] = int(width)
                settings["custom_height"] = int(height)
            else:
                settings["custom_width"] = None
                settings["custom_height"] = None
        elif not self.use_preset_var.get():
            # Custom dimensions
            try:
                settings["custom_width"] = int(self.width_var.get())
                settings["custom_height"] = int(self.height_var.get())
            except ValueError:
                settings["custom_width"] = None
                settings["custom_height"] = None
        else:
            settings["custom_width"] = None
            settings["custom_height"] = None
        
        settings["maintain_aspect_ratio"] = self.maintain_aspect_var.get()
        
        # Frame rate
        settings["match_input_fps"] = self.match_input_fps_var.get()
        settings["frame_rate"] = self.frame_rate_var.get()
        
        # Quality
        settings["bitrate_mode"] = self.bitrate_mode_var.get()
        settings["quality_crf"] = self.quality_var.get()
        settings["bitrate"] = self.bitrate_var.get()
        
        # Trim
        if self.enable_trim_var.get():
            settings["trim_start"] = self.trim_start_var.get()
            settings["trim_end"] = self.trim_end_var.get()
        else:
            settings["trim_start"] = ""
            settings["trim_end"] = ""
        
        # Verification
        settings["check_black_bars"] = self.check_black_bars_var.get()
        settings["verify_snippets"] = self.verify_snippets_var.get()
        
        # Save to config
        self.config_manager.set_export_settings(settings)
        
        # Set result and close
        self.result = settings
        self.dialog.destroy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        # Resolution
        self.use_preset_var.set(True)
        self.preset_var.set("1280×720 (16:9)")
        self.width_var.set("")
        self.height_var.set("")
        self.maintain_aspect_var.set(True)
        
        # Frame rate
        self.match_input_fps_var.set(False)
        self.frame_rate_var.set("30")
        
        # Quality
        self.bitrate_mode_var.set("crf")
        self.quality_var.set(23)
        self.bitrate_var.set("5M")
        
        # Trim
        self.enable_trim_var.set(False)
        self.trim_start_var.set("")
        self.trim_end_var.set("")
        
        # Verification
        self.check_black_bars_var.set(False)
        self.verify_snippets_var.set(False)
        
        # Update UI states
        self.toggle_resolution_mode()
        self.toggle_fps_mode()
        self.toggle_quality_mode()
        self.toggle_trim_mode()
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.dialog.destroy()
    
    def get_result(self):
        """Get the dialog result."""
        return self.result