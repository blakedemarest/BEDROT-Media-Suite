# -*- coding: utf-8 -*-
"""
Main Application Module for Video Snippet Remixer.

This module contains the main application window and GUI functionality for:
- Input file selection and management
- Output settings configuration
- Length/BPM controls
- Processing controls and status display
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import logging
from .config_manager import ConfigManager
from .processing_worker import ProcessingWorker
from .utils import safe_print, validate_directory_path
from .logging_config import setup_logging, get_logger
from .job_queue import JobQueue, ProcessingJob, JobStatus, RemixerSettings
from .theme import apply_bedrot_theme
from .drag_drop import DragDropHandler, DND_AVAILABLE
from .controller import SnippetRemixerController

# Import TkinterDnD for root window creation
try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None
    if not DND_AVAILABLE:
        print("[WARNING] tkinterdnd2 not available. Drag and drop functionality will be disabled.")
        print("[TIP] Install tkinterdnd2 for drag and drop: pip install tkinterdnd2")


class VideoRemixerApp:
    """
    Main application window for the Video Snippet Remixer.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("BEDROT SNIPPET REMIXER // CYBERCORE VIDEO MANIPULATION")

        # Apply BEDROT theme
        apply_bedrot_theme(self.root)
        
        # Set up logging
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self.logger, self.video_filter = setup_logging(
            log_dir=log_dir,
            log_level=logging.DEBUG,
            console_level=logging.INFO
        )
        self.logger.info("Video Snippet Remixer starting up")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.processing_worker = ProcessingWorker(self.config_manager.get_script_dir(), self.video_filter)
        self.settings = self.config_manager.config
        
        # Check FFmpeg tools
        ffmpeg_found, ffprobe_found = self.processing_worker.get_video_processor().are_tools_available()
        
        # GUI Variables
        self.input_file_paths = tk.Variable(value=[])
        self.output_folder_var = tk.StringVar(value=self.settings["output_folder"])
        self.length_mode_var = tk.StringVar(value=self.settings["length_mode"])
        self.duration_seconds_var = tk.StringVar(value=f"{self.settings['duration_seconds']:.1f}")
        self.bpm_var = tk.StringVar(value=f"{self.settings['bpm']:.1f}")
        self.bpm_unit_var = tk.StringVar(value=self.settings["bpm_unit"])
        self.num_units_var = tk.StringVar(value=str(self.settings["num_units"]))
        self.tempo_mod_enabled_var = tk.BooleanVar(value=self.settings.get("tempo_mod_enabled", False))
        self.tempo_mod_start_bpm_var = tk.StringVar(value=f"{self.settings.get('tempo_mod_start_bpm', self.settings['bpm']):.1f}")
        self.tempo_mod_end_bpm_var = tk.StringVar(value=f"{self.settings.get('tempo_mod_end_bpm', self.settings['bpm']):.1f}")
        self.tempo_mod_duration_var = tk.StringVar(value=f"{self.settings.get('tempo_mod_duration_seconds', self.settings['duration_seconds']):.1f}")
        # Canvas constraints for tempo modulation graph
        self._mod_canvas_pad = 12
        self._mod_canvas_min_bpm = 40.0
        self._mod_canvas_max_bpm = 240.0
        self.aspect_ratio_var = tk.StringVar(value=self.settings["aspect_ratio"])
        self.aspect_ratio_mode_var = tk.StringVar(value=self.settings.get("aspect_ratio_mode", "Crop to Fill"))
        self.status_var = tk.StringVar(value="Ready")
        self.continuous_mode_var = tk.BooleanVar(value=self.settings.get("continuous_mode", False))
        self.mute_audio_var = tk.BooleanVar(value=self.settings.get("mute_audio", False))
        self.tempo_mod_points = self._init_tempo_mod_points()
        self._mod_drag_index = None
        
        # Internal state
        self.last_input_folder = self.settings["last_input_folder"]
        self.continuous_processing = False
        self.continuous_count = 0
        self._last_continuous_settings = {}
        
        # Initialize job queue for non-continuous mode
        self.job_queue = JobQueue(max_history=50)
        self.queue_processor_active = False

        # Run N times mode state
        self.run_n_times_var = tk.IntVar(value=1)
        self.run_n_times_enabled_var = tk.BooleanVar(value=False)
        self.run_n_target = 0
        self.run_n_current = 0
        self.run_n_snapshot_settings = {}
        self.run_n_processing = False

        # Initialize controller with callbacks
        self.controller = SnippetRemixerController(
            config_manager=self.config_manager,
            processing_worker=self.processing_worker,
            job_queue=self.job_queue,
            callbacks={
                "on_status": self.update_status,
                "on_status_success": self.update_status_success,
                "on_status_warning": self.update_status_warning,
                "on_status_error": self.update_status_error,
                "on_enable_generate": self.enable_generate_button,
                "on_continuous_update": lambda count, info: self.update_continuous_counter(),
                "on_queue_update": self.update_queue_display,
                "on_show_warning": lambda title, msg: messagebox.showwarning(title, msg),
                "on_show_error": lambda title, msg: messagebox.showerror(title, msg),
                "schedule_callback": lambda delay, func: self.root.after(delay, func),
                "on_start_next_continuous": self.start_next_continuous_remix,
            }
        )
        self.controller.set_logger(self.logger)

        # Bindings
        self.length_mode_var.trace_add("write", self.toggle_length_mode_ui)
        
        # Add bindings for BPM duration estimate updates
        self.bpm_var.trace_add("write", self.update_duration_estimate)
        self.bpm_unit_var.trace_add("write", self.update_duration_estimate)
        self.num_units_var.trace_add("write", self.update_duration_estimate)
        self.tempo_mod_enabled_var.trace_add("write", self.update_duration_estimate)
        self.tempo_mod_start_bpm_var.trace_add("write", self.update_duration_estimate)
        self.tempo_mod_end_bpm_var.trace_add("write", self.update_duration_estimate)
        self.tempo_mod_duration_var.trace_add("write", self.update_duration_estimate)
        
        # Add bindings for continuous mode counter updates
        self.bpm_var.trace_add("write", self.update_continuous_counter_on_change)
        self.bpm_unit_var.trace_add("write", self.update_continuous_counter_on_change)
        self.num_units_var.trace_add("write", self.update_continuous_counter_on_change)
        self.duration_seconds_var.trace_add("write", self.update_continuous_counter_on_change)
        self.length_mode_var.trace_add("write", self.update_continuous_counter_on_change)
        self.tempo_mod_enabled_var.trace_add("write", self.update_continuous_counter_on_change)
        self.tempo_mod_start_bpm_var.trace_add("write", self.update_continuous_counter_on_change)
        self.tempo_mod_end_bpm_var.trace_add("write", self.update_continuous_counter_on_change)
        self.tempo_mod_duration_var.trace_add("write", self.update_continuous_counter_on_change)

        # Window Setup - compact size that fits all elements including queue status
        self.root.geometry("700x720")  # Sized to fit all controls with queue status
        self.root.minsize(650, 700)    # Minimum size to prevent UI cutoff
        
        # Track window state for status section visibility
        self.window_maximized = False
        self.root.bind("<Configure>", self.on_window_configure)
        
        self.create_widgets()
        self.toggle_length_mode_ui()
        
        # Initialize queue display based on mode
        self.root.after(50, self.update_queue_display)
            
        # Initialize duration estimate if in BPM mode
        self.root.after(100, self.update_duration_estimate)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Show dependency warnings
        if not ffmpeg_found or not ffprobe_found:
            missing = []
            if not ffmpeg_found:
                missing.append("FFmpeg")
            if not ffprobe_found:
                missing.append("FFprobe")
            messagebox.showwarning(
                "Dependency Missing",
                f"{' and '.join(missing)} not found in PATH.\\nPlease install FFmpeg and add it to your system's PATH.\\nRemix generation will fail."
            )
            self.status_var.set(f"Error: {'/'.join(missing)} not found!")

    def create_widgets(self):
        """Creates and arranges all the GUI elements."""
        # Simple main frame that expands with window
        main_frame = ttk.Frame(self.root, padding="5")  # Reduced padding
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Files Section
        self.create_input_section(main_frame)
        
        # Output Options Section
        self.create_output_section(main_frame)
        
        # Length Control Section
        self.create_length_section(main_frame)
        
        # Process Button
        self.create_process_section(main_frame)
        
        # Status Bar
        self.create_status_section(main_frame)

    def create_input_section(self, parent):
        """Create the input files section."""
        # Create custom frame with BEDROT styling
        input_container = tk.Frame(parent, bg='#121212', bd=0)
        input_container.pack(fill=tk.X, pady=5)
        
        # Label for the section
        input_label = tk.Label(input_container, text=" INPUT VIDEOS ", bg='#121212', fg='#00ffff', 
                               font=('Segoe UI', 10, 'bold'))
        input_label.pack(anchor='w', padx=15)
        
        # Frame with border
        input_frame = tk.Frame(input_container, bg='#121212', highlightbackground='#00ffff', 
                              highlightthickness=1, bd=0)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Inner padding frame
        input_inner = tk.Frame(input_frame, bg='#121212', bd=0)
        input_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        input_list_frame = tk.Frame(input_inner, bg='#121212')
        input_list_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP, pady=(0, 5))
        
        self.queue_listbox = tk.Listbox(
            input_list_frame, 
            listvariable=self.input_file_paths, 
            height=5,  # Reduced height for more compact UI
            selectmode=tk.EXTENDED,
            bg='#1a1a1a',
            fg='#e0e0e0',
            selectbackground='#00ffff',
            selectforeground='#000000',
            highlightbackground='#404040',
            highlightcolor='#00ffff',
            highlightthickness=1,
            font=('Segoe UI', 10),
            relief='solid',
            bd=1
        )
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure drag and drop for the listbox
        self.drag_drop_handler = DragDropHandler(
            listbox=self.queue_listbox,
            root=self.root,
            on_files_added=self.add_files_to_queue,
            on_browse_files=self.browse_input_files,
            on_status_success=self.update_status_success,
            on_status_warning=self.update_status_warning,
            on_status_error=self.update_status_error,
        )
        self.drag_drop_handler.setup()
        
        scrollbar = ttk.Scrollbar(input_list_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=scrollbar.set)
        
        input_button_frame = tk.Frame(input_inner, bg='#121212')
        input_button_frame.pack(fill=tk.X)
        
        browse_button = ttk.Button(
            input_button_frame, 
            text="BROWSE FILES", 
            command=self.browse_input_files,
            style='Browse.TButton'
        )
        browse_button.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_button = ttk.Button(
            input_button_frame, 
            text="CLEAR SELECTED", 
            command=self.clear_selected,
            style='TButton'
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        clear_all_button = ttk.Button(
            input_button_frame, 
            text="CLEAR ALL", 
            command=self.clear_all,
            style='TButton'
        )
        clear_all_button.pack(side=tk.LEFT, padx=5)

    def create_output_section(self, parent):
        """Create the output settings section."""
        # Create custom frame with BEDROT styling
        output_container = tk.Frame(parent, bg='#121212', bd=0)
        output_container.pack(fill=tk.X, pady=5)
        
        # Label for the section
        output_label = tk.Label(output_container, text=" OUTPUT SETTINGS ", bg='#121212', fg='#00ffff', 
                               font=('Segoe UI', 10, 'bold'))
        output_label.pack(anchor='w', padx=15)
        
        # Frame with border
        output_frame = tk.Frame(output_container, bg='#121212', highlightbackground='#00ffff', 
                                highlightthickness=1, bd=0)
        output_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Inner padding frame with grid
        output_inner = tk.Frame(output_frame, bg='#121212', bd=0)
        output_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        output_inner.columnconfigure(1, weight=1)
        
        # Output Folder
        tk.Label(output_inner, text="Output Folder:", bg='#121212', fg='#e0e0e0', 
                font=('Segoe UI', 10)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Create a frame to hold the folder path with a border
        folder_frame = tk.Frame(output_inner, bg='#1a1a1a', highlightbackground='#404040', highlightthickness=1, bd=0)
        folder_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        self.folder_label = tk.Label(
            folder_frame, 
            textvariable=self.output_folder_var, 
            bg='#1a1a1a',
            fg='#e0e0e0',
            font=('Segoe UI', 10),
            anchor=tk.W,
            padx=5,
            pady=2
        )
        self.folder_label.pack(fill=tk.BOTH, expand=True)
        browse_output_button = ttk.Button(
            output_inner, 
            text="BROWSE", 
            command=self.browse_output_folder,
            style='Browse.TButton'
        )
        browse_output_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Add folder open button
        open_folder_button = ttk.Button(
            output_inner,
            text="OPEN",
            command=self.open_output_folder,
            style='TButton',
            width=6
        )
        open_folder_button.grid(row=0, column=3, padx=2, pady=5)

        # Aspect Ratio
        tk.Label(output_inner, text="Aspect Ratio:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ar_combobox = ttk.Combobox(
            output_inner, 
            textvariable=self.aspect_ratio_var, 
            values=self.config_manager.get_aspect_ratios(), 
            state="readonly", 
            width=25
        )
        self.ar_combobox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Export Settings Button
        self.export_settings_button = ttk.Button(
            output_inner,
            text="EXPORT SETTINGS",
            command=self.open_export_settings,
            style='TButton'
        )
        self.export_settings_button.grid(row=1, column=2, padx=5, pady=5)
        
        tk.Label(output_inner, text="(All videos will be HD quality)", bg='#121212', fg='#888888',
                font=('Segoe UI', 9, 'italic')).grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Aspect Ratio Mode
        tk.Label(output_inner, text="Aspect Ratio Mode:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Radio buttons frame
        mode_frame = tk.Frame(output_inner, bg='#121212')
        mode_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        self.crop_radio = ttk.Radiobutton(
            mode_frame,
            text="Crop to Fill",
            variable=self.aspect_ratio_mode_var,
            value="Crop to Fill"
        )
        self.crop_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        self.pad_radio = ttk.Radiobutton(
            mode_frame,
            text="Pad to Fit",
            variable=self.aspect_ratio_mode_var,
            value="Pad to Fit"
        )
        self.pad_radio.pack(side=tk.LEFT)

    def create_length_section(self, parent):
        """Create the length control section."""
        # Create custom frame with BEDROT styling
        length_container = tk.Frame(parent, bg='#121212', bd=0)
        length_container.pack(fill=tk.X, pady=5)
        
        # Label for the section
        length_label = tk.Label(length_container, text=" REMIX LOGIC ", bg='#121212', fg='#00ffff', 
                               font=('Segoe UI', 10, 'bold'))
        length_label.pack(anchor='w', padx=15)
        
        # Frame with border
        length_frame_outer = tk.Frame(length_container, bg='#121212', highlightbackground='#00ffff', 
                                      highlightthickness=1, bd=0)
        length_frame_outer.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Inner padding frame
        length_frame = tk.Frame(length_frame_outer, bg='#121212', bd=0)
        length_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        mode_frame = tk.Frame(length_frame, bg='#121212')
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.seconds_radio = ttk.Radiobutton(
            mode_frame, 
            text="Length in Seconds", 
            variable=self.length_mode_var, 
            value="Seconds"
        )
        self.seconds_radio.pack(side=tk.LEFT, padx=5)
        
        self.bpm_radio = ttk.Radiobutton(
            mode_frame, 
            text="Length by BPM", 
            variable=self.length_mode_var, 
            value="BPM"
        )
        self.bpm_radio.pack(side=tk.LEFT, padx=20)
        
        # Seconds input frame
        self.seconds_input_frame = tk.Frame(length_frame, bg='#121212')
        tk.Label(self.seconds_input_frame, text="Total Duration (s):", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.seconds_entry = ttk.Entry(
            self.seconds_input_frame, 
            textvariable=self.duration_seconds_var, 
            width=10
        )
        self.seconds_entry.pack(side=tk.LEFT, padx=5)
        
        # Bind events for immediate updates on Enter or focus loss
        self.seconds_entry.bind('<Return>', self.on_entry_update)
        self.seconds_entry.bind('<FocusOut>', self.on_entry_update)
        
        # BPM input frame
        self.bpm_input_frame = tk.Frame(length_frame, bg='#121212')
        tk.Label(self.bpm_input_frame, text="BPM:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.bpm_entry = ttk.Entry(self.bpm_input_frame, textvariable=self.bpm_var, width=6)
        self.bpm_entry.pack(side=tk.LEFT, padx=5)
        
        # Bind events for immediate updates on Enter or focus loss
        self.bpm_entry.bind('<Return>', self.on_entry_update)
        self.bpm_entry.bind('<FocusOut>', self.on_entry_update)
        
        tk.Label(self.bpm_input_frame, text="Snippet Unit:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(15,5))
        self.bpm_unit_combo = ttk.Combobox(
            self.bpm_input_frame, 
            textvariable=self.bpm_unit_var, 
            values=list(self.config_manager.get_bpm_units().keys()), 
            state="readonly", 
            width=10
        )
        self.bpm_unit_combo.pack(side=tk.LEFT, padx=5)
        
        self.num_units_label = tk.Label(self.bpm_input_frame, text="Total Units:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10))
        self.num_units_label.pack(side=tk.LEFT, padx=(15, 5))
        self.num_units_entry = ttk.Entry(
            self.bpm_input_frame, 
            textvariable=self.num_units_var, 
            width=6
        )
        self.num_units_entry.pack(side=tk.LEFT, padx=5)
        
        # Bind events for immediate updates on Enter or focus loss
        self.num_units_entry.bind('<Return>', self.on_entry_update)
        self.num_units_entry.bind('<FocusOut>', self.on_entry_update)
        
        # Add duration estimate label
        self.duration_estimate_label = ttk.Label(
            self.bpm_input_frame, 
            text="",
            style='Blue.TLabel'
        )
        self.duration_estimate_label.pack(side=tk.LEFT, padx=(15, 5))

        # Linear tempo modulator controls
        mod_toggle_frame = tk.Frame(length_frame, bg='#121212')
        mod_toggle_frame.pack(fill=tk.X, pady=(8, 2))
        self.tempo_mod_check = ttk.Checkbutton(
            mod_toggle_frame,
            text="Linear tempo modulator (ramp BPM across clip)",
            variable=self.tempo_mod_enabled_var,
            command=self.toggle_tempo_mod_ui
        )
        self.tempo_mod_check.pack(side=tk.LEFT, padx=5)
        
        self.tempo_mod_frame = tk.Frame(length_frame, bg='#121212')
        self.tempo_mod_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(self.tempo_mod_frame, text="Start BPM:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.tempo_mod_start_entry = ttk.Entry(
            self.tempo_mod_frame,
            textvariable=self.tempo_mod_start_bpm_var,
            width=8
        )
        self.tempo_mod_start_entry.pack(side=tk.LEFT, padx=5)
        self.tempo_mod_start_entry.bind('<Return>', self.on_entry_update)
        self.tempo_mod_start_entry.bind('<FocusOut>', self.on_entry_update)
        
        tk.Label(self.tempo_mod_frame, text="End BPM:", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(15,5))
        self.tempo_mod_end_entry = ttk.Entry(
            self.tempo_mod_frame,
            textvariable=self.tempo_mod_end_bpm_var,
            width=8
        )
        self.tempo_mod_end_entry.pack(side=tk.LEFT, padx=5)
        self.tempo_mod_end_entry.bind('<Return>', self.on_entry_update)
        self.tempo_mod_end_entry.bind('<FocusOut>', self.on_entry_update)
        
        tk.Label(self.tempo_mod_frame, text="Clip Duration (s):", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(15,5))
        self.tempo_mod_duration_entry = ttk.Entry(
            self.tempo_mod_frame,
            textvariable=self.tempo_mod_duration_var,
            width=8
        )
        self.tempo_mod_duration_entry.pack(side=tk.LEFT, padx=5)
        self.tempo_mod_duration_entry.bind('<Return>', self.on_entry_update)
        self.tempo_mod_duration_entry.bind('<FocusOut>', self.on_entry_update)

        # Modulation graph canvas (automation-style)
        canvas_frame = tk.Frame(length_frame, bg='#121212')
        canvas_frame.pack(fill=tk.X, pady=(2, 5))
        tk.Label(canvas_frame, text="Tempo Automation (Time vs BPM)", bg='#121212', fg='#e0e0e0',
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=5)
        self.tempo_mod_canvas = tk.Canvas(
            canvas_frame,
            width=420,
            height=170,
            bg='#0f0f0f',
            highlightthickness=1,
            highlightbackground='#404040'
        )
        self.tempo_mod_canvas.pack(fill=tk.X, padx=5, pady=(4, 2))
        self.tempo_mod_canvas.bind("<Button-1>", self.on_mod_canvas_click)
        self.tempo_mod_canvas.bind("<B1-Motion>", self.on_mod_canvas_drag)
        self.tempo_mod_canvas.bind("<ButtonRelease-1>", self.on_mod_canvas_release)
        self.tempo_mod_canvas.bind("<Double-Button-1>", self.on_mod_canvas_double_click)
        self._mod_handle_map = {}
        self._mod_index_to_handle = {}
        self._mod_canvas_pad = 12
        self._mod_canvas_min_bpm = 40.0
        self._mod_canvas_max_bpm = 240.0
        self._draw_tempo_mod_canvas()
        
        # Jitter controls frame
        jitter_frame = tk.Frame(length_frame, bg='#121212')
        jitter_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Jitter checkbox
        self.jitter_enabled_var = tk.BooleanVar(value=self.settings.get("jitter_enabled", False))
        self.jitter_check = ttk.Checkbutton(
            jitter_frame,
            text="Jitter",
            variable=self.jitter_enabled_var,
            command=self.toggle_jitter_ui
        )
        self.jitter_check.pack(side=tk.LEFT, padx=5)
        
        # Jitter intensity slider
        self.jitter_intensity_var = tk.IntVar(value=self.settings.get("jitter_intensity", 50))
        self.jitter_slider_label = tk.Label(jitter_frame, text="Intensity:", bg='#121212', fg='#e0e0e0',
                                           font=('Segoe UI', 10))
        self.jitter_slider_label.pack(side=tk.LEFT, padx=(10, 5))
        
        self.jitter_slider = ttk.Scale(
            jitter_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.jitter_intensity_var,
            length=200,
            style='Horizontal.TScale'
        )
        self.jitter_slider.pack(side=tk.LEFT, padx=5)
        
        self.jitter_value_label = tk.Label(jitter_frame, text="50%", bg='#121212', fg='#00ff88',
                                          font=('Segoe UI', 10))
        self.jitter_value_label.pack(side=tk.LEFT, padx=5)
        
        # Bind slider changes to update the value label
        self.jitter_intensity_var.trace_add("write", self.update_jitter_value_label)

        # Initialize jitter UI state
        self.toggle_jitter_ui()

    def create_process_section(self, parent):
        """Create the process button section."""
        process_button_frame = ttk.Frame(parent, padding=(0, 5, 0, 0))
        process_button_frame.pack(fill=tk.X)
        
        # Continuous mode toggle
        continuous_frame = ttk.Frame(process_button_frame)
        continuous_frame.pack(pady=(0, 5))
        
        self.continuous_check = ttk.Checkbutton(
            continuous_frame,
            text="[Continuous Mode] Keep making videos",
            variable=self.continuous_mode_var
            # Don't bind command yet to prevent triggering on startup
        )
        self.continuous_check.pack()
        
        # Bind command AFTER widget creation to prevent startup trigger
        self.root.after(10, lambda: self.continuous_check.configure(command=self.toggle_continuous_mode))
        
        # Counter display for continuous mode
        self.continuous_label = ttk.Label(
            continuous_frame,
            text="",
            style='Blue.TLabel'
        )
        self.continuous_label.pack(pady=(5, 0))
        
        # Queue status display (shows when not in continuous mode)
        queue_frame = ttk.Frame(process_button_frame)
        queue_frame.pack(pady=(5, 5))
        
        self.queue_status_label = ttk.Label(
            queue_frame,
            text="Queue: Empty",
            style='Blue.TLabel'
        )
        self.queue_status_label.pack()
        
        # Queue details label
        self.queue_details_label = ttk.Label(
            queue_frame,
            text="",
            style='TLabel'
        )
        self.queue_details_label.pack(pady=(2, 0))

        # Run N times section
        self.run_n_frame = ttk.Frame(process_button_frame)
        self.run_n_frame.pack(pady=(5, 5))

        self.run_n_check = ttk.Checkbutton(
            self.run_n_frame,
            text="Run",
            variable=self.run_n_times_enabled_var,
            command=self.toggle_run_n_times
        )
        self.run_n_check.pack(side=tk.LEFT, padx=(0, 5))

        self.run_n_spinbox = ttk.Spinbox(
            self.run_n_frame,
            from_=1,
            to=100,
            width=4,
            textvariable=self.run_n_times_var,
            state=tk.DISABLED
        )
        self.run_n_spinbox.pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(
            self.run_n_frame,
            text="times with same settings",
            bg='#121212',
            fg='#888888',
            font=('Segoe UI', 9)
        ).pack(side=tk.LEFT)

        self.run_n_progress_label = ttk.Label(
            self.run_n_frame,
            text="",
            style='Blue.TLabel'
        )
        self.run_n_progress_label.pack(side=tk.LEFT, padx=(10, 0))

        # Audio options
        self.mute_audio_check = ttk.Checkbutton(
            process_button_frame,
            text="Mute audio in final export",
            variable=self.mute_audio_var
        )
        self.mute_audio_check.pack(pady=(0, 8))
        
        # Main Generate/Abort button
        self.generate_button = ttk.Button(
            process_button_frame, 
            text="GENERATE REMIX", 
            command=self.start_processing_thread,
            style='Generate.TButton'
        )
        self.generate_button.pack(pady=10)

    def create_status_section(self, parent):
        """Create the status display section (hidden by default)."""
        # Create custom frame with BEDROT styling
        self.status_container = tk.Frame(parent, bg='#121212', bd=0)
        # Don't pack initially - will be shown when window is maximized
        
        # Label for the section
        status_label = tk.Label(self.status_container, text=" STATUS ", bg='#121212', fg='#00ffff', 
                               font=('Segoe UI', 10, 'bold'))
        status_label.pack(anchor='w', padx=15)
        
        # Frame with border
        status_frame_outer = tk.Frame(self.status_container, bg='#121212', highlightbackground='#00ffff', 
                                      highlightthickness=1, bd=0)
        status_frame_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        # Inner padding frame
        status_frame = tk.Frame(status_frame_outer, bg='#121212', bd=0)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a simple text widget for status messages
        import tkinter.scrolledtext as scrolledtext
        self.status_text = scrolledtext.ScrolledText(
            status_frame, 
            height=8, 
            wrap=tk.WORD, 
            state=tk.NORMAL,  # Start as normal so we can add initial text
            font=('Consolas', 10),
            bg='#1a1a1a',
            fg='#00ff88',
            insertbackground='#00ffff',
            selectbackground='#00ffff',
            selectforeground='#000000',
            highlightbackground='#404040',
            highlightcolor='#00ffff',
            highlightthickness=1,
            relief='solid',
            bd=1
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure scrollbar colors for the ScrolledText widget
        self.status_text.vbar.configure(
            bg='#1a1a1a',
            troughcolor='#0a0a0a',
            activebackground='#00ff88',
            highlightthickness=0,
            borderwidth=0,
            width=12
        )
        
        # Add initial message directly
        self.status_text.insert(tk.END, "=== Snippet Remixer Status ===\n")
        self.status_text.insert(tk.END, "Ready to process videos\n")
        self.status_text.config(state=tk.DISABLED)
        
        # Simple status bar at bottom
        status_bar_frame = tk.Frame(status_frame, bg='#1a1a1a', highlightbackground='#404040', 
                                    highlightthickness=1, bd=0)
        status_bar_frame.pack(fill=tk.X, pady=(5,0))
        
        self.status_bar = tk.Label(
            status_bar_frame, 
            textvariable=self.status_var, 
            bg='#1a1a1a',
            fg='#00ff88',
            font=('Segoe UI', 9),
            anchor=tk.W, 
            padx=10,
            pady=5
        )
        self.status_bar.pack(fill=tk.X)
        
        # Set initial status
        self.status_var.set("Ready to process videos")

    def toggle_length_mode_ui(self, *args):
        """Toggle between seconds and BPM input modes."""
        mode = self.length_mode_var.get()
        if hasattr(self, 'seconds_input_frame') and hasattr(self, 'bpm_input_frame'):
            if mode == "Seconds":
                self.seconds_input_frame.pack(fill=tk.X, pady=5)
                self.bpm_input_frame.pack_forget()
            elif mode == "BPM":
                self.seconds_input_frame.pack_forget()
                self.bpm_input_frame.pack(fill=tk.X, pady=5)
                # Update duration estimate when switching to BPM mode
                self.update_duration_estimate()
            else:
                self.seconds_input_frame.pack_forget()
                self.bpm_input_frame.pack_forget()
        # Ensure tempo modulation controls follow the selected mode
        if hasattr(self, 'tempo_mod_check'):
            self.toggle_tempo_mod_ui()
    
    def toggle_tempo_mod_ui(self, *args):
        """Enable/disable tempo modulation controls based on mode and toggle state."""
        mode = self.length_mode_var.get()
        mod_requested = self.tempo_mod_enabled_var.get()
        mod_enabled = mod_requested and mode == "BPM"
        
        # Disable modulation when not in BPM mode
        if mode != "BPM":
            if mod_requested:
                self.tempo_mod_enabled_var.set(False)
            self.tempo_mod_check.state(['disabled'])
        else:
            self.tempo_mod_check.state(['!disabled'])
        
        # Configure input states
        entry_state = tk.NORMAL if mod_enabled else tk.DISABLED
        for entry in [getattr(self, attr, None) for attr in [
            "tempo_mod_start_entry", "tempo_mod_end_entry", "tempo_mod_duration_entry"
        ]]:
            if entry:
                entry.config(state=entry_state)
        
        # Disable manual unit entry when modulation drives tempo
        if hasattr(self, "num_units_entry"):
            self.num_units_entry.config(state=tk.DISABLED if mod_enabled else tk.NORMAL)
        if hasattr(self, "num_units_label"):
            self.num_units_label.configure(fg='#666666' if mod_enabled else '#e0e0e0')
        
        # Refresh estimates to reflect new mode
        self.update_duration_estimate()
        
        # Show or hide modulation canvas
        if hasattr(self, "tempo_mod_frame"):
            if mod_enabled:
                self.tempo_mod_frame.pack(fill=tk.X, pady=(0, 5))
            else:
                self.tempo_mod_frame.pack_forget()
        if hasattr(self, "tempo_mod_canvas"):
            if mod_enabled:
                self.tempo_mod_canvas.master.pack(fill=tk.X, pady=(2, 5))
            else:
                self.tempo_mod_canvas.master.pack_forget()
        if mod_enabled:
            self._sync_mod_duration_to_entry()
            self._draw_tempo_mod_canvas()

    def _init_tempo_mod_points(self):
        """Initialize tempo modulation points from settings."""
        points = self.settings.get("tempo_mod_points")
        return self._sanitize_mod_points(points)

    def _sanitize_mod_points(self, points, new_duration=None):
        """Ensure modulation points are valid, sorted, and span the clip."""
        try:
            duration_val = float(new_duration) if new_duration is not None else float(self.tempo_mod_duration_var.get())
        except (TypeError, ValueError):
            duration_val = self.settings.get("tempo_mod_duration_seconds", 15.0)
        if duration_val <= 0:
            duration_val = 15.0

        if not isinstance(points, list):
            points = []
        sanitized = []
        for p in points:
            if not isinstance(p, dict):
                continue
            try:
                t = float(p.get("time", 0.0))
                bpm_val = float(p.get("bpm", float(self.bpm_var.get())))
            except (TypeError, ValueError):
                continue
            if t < 0 or bpm_val <= 0:
                continue
            sanitized.append({"time": t, "bpm": bpm_val})

        if len(sanitized) < 2:
            sanitized = [
                {"time": 0.0, "bpm": float(self.tempo_mod_start_bpm_var.get())},
                {"time": duration_val, "bpm": float(self.tempo_mod_end_bpm_var.get())}
            ]

        sanitized.sort(key=lambda x: x["time"])

        # Anchor start and end
        if sanitized[0]["time"] != 0.0:
            sanitized[0]["time"] = 0.0
        if sanitized[-1]["time"] <= 0 or abs(sanitized[-1]["time"] - duration_val) > 1e-6:
            sanitized[-1]["time"] = duration_val

        # Clamp BPMs
        min_bpm, max_bpm = self._mod_canvas_min_bpm, self._mod_canvas_max_bpm
        for p in sanitized:
            p["bpm"] = max(min_bpm, min(max_bpm, p["bpm"]))

        return sanitized

    def _sync_mod_duration_to_entry(self):
        """Keep modulation points aligned with the current duration entry."""
        try:
            new_duration = float(self.tempo_mod_duration_var.get())
        except (TypeError, ValueError):
            return
        if new_duration <= 0:
            return
        old_end = self.tempo_mod_points[-1]["time"] if self.tempo_mod_points else new_duration
        if old_end <= 0:
            old_end = new_duration
        scale = new_duration / old_end if old_end else 1.0
        for idx, pt in enumerate(self.tempo_mod_points):
            if idx == 0:
                pt["time"] = 0.0
            elif idx == len(self.tempo_mod_points) - 1:
                pt["time"] = new_duration
            else:
                pt["time"] = pt["time"] * scale
        self.tempo_mod_points = self._sanitize_mod_points(self.tempo_mod_points, new_duration)

    def _get_mod_duration_value(self):
        try:
            return float(self.tempo_mod_duration_var.get())
        except (TypeError, ValueError):
            return self.settings.get("tempo_mod_duration_seconds", 15.0)

    def _draw_tempo_mod_canvas(self):
        """Render the tempo automation graph."""
        if not hasattr(self, "tempo_mod_canvas"):
            return
        canvas = self.tempo_mod_canvas
        canvas.delete("all")
        pad = self._mod_canvas_pad
        w = int(canvas.winfo_width() or 420)
        h = int(canvas.winfo_height() or 170)
        min_bpm = self._mod_canvas_min_bpm
        max_bpm = self._mod_canvas_max_bpm
        duration = max(self._get_mod_duration_value(), 0.001)

        def t_to_x(t):
            return pad + (t / duration) * (w - 2 * pad)

        def bpm_to_y(b):
            norm = (b - min_bpm) / (max_bpm - min_bpm)
            norm = max(0.0, min(1.0, norm))
            return pad + (1 - norm) * (h - 2 * pad)

        # Grid lines
        for i in range(5):
            y = pad + i * (h - 2 * pad) / 4
            canvas.create_line(pad, y, w - pad, y, fill="#202020")
        for i in range(5):
            x = pad + i * (w - 2 * pad) / 4
            canvas.create_line(x, pad, x, h - pad, fill="#202020")

        # Axis labels
        canvas.create_text(pad, pad - 2, text=f"{max_bpm:.0f} BPM", anchor="nw", fill="#888888", font=("Segoe UI", 8))
        canvas.create_text(pad, h - pad + 2, text=f"{min_bpm:.0f} BPM", anchor="sw", fill="#888888", font=("Segoe UI", 8))
        canvas.create_text(w - pad, h - pad + 2, text=f"{duration:.1f}s", anchor="se", fill="#888888", font=("Segoe UI", 8))

        # Polyline and handles
        coords = []
        for pt in self.tempo_mod_points:
            coords.extend([t_to_x(pt["time"]), bpm_to_y(pt["bpm"])])
        if len(coords) >= 4:
            canvas.create_line(*coords, fill="#00ff88", width=2, smooth=True)

        self._mod_handle_map = {}
        self._mod_index_to_handle = {}
        for idx, pt in enumerate(self.tempo_mod_points):
            x = t_to_x(pt["time"])
            y = bpm_to_y(pt["bpm"])
            handle = canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#00ffff", outline="#ffffff")
            self._mod_handle_map[handle] = idx
            self._mod_index_to_handle[idx] = handle

    def _mod_xy_to_time_bpm(self, x, y):
        pad = self._mod_canvas_pad
        w = int(self.tempo_mod_canvas.winfo_width() or 420)
        h = int(self.tempo_mod_canvas.winfo_height() or 170)
        duration = max(self._get_mod_duration_value(), 0.001)
        t = (x - pad) / max(1, (w - 2 * pad)) * duration
        t = max(0.0, min(duration, t))
        norm = 1 - (y - pad) / max(1, (h - 2 * pad))
        bpm_val = self._mod_canvas_min_bpm + norm * (self._mod_canvas_max_bpm - self._mod_canvas_min_bpm)
        bpm_val = max(self._mod_canvas_min_bpm, min(self._mod_canvas_max_bpm, bpm_val))
        return t, bpm_val

    def _find_mod_handle(self, x, y, radius=8):
        """Return index of handle under cursor or None."""
        for handle_id, idx in self._mod_handle_map.items():
            coords = self.tempo_mod_canvas.coords(handle_id)
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            if (cx - x) ** 2 + (cy - y) ** 2 <= radius ** 2:
                return idx
        return None

    def _add_mod_point(self, time_val, bpm_val):
        self.tempo_mod_points.append({"time": time_val, "bpm": bpm_val})
        self.tempo_mod_points.sort(key=lambda p: p["time"])
        self.tempo_mod_points = self._sanitize_mod_points(self.tempo_mod_points)
        self._draw_tempo_mod_canvas()
        self.update_duration_estimate()

    def _remove_mod_point(self, idx):
        if len(self.tempo_mod_points) <= 2:
            return
        if idx == 0 or idx == len(self.tempo_mod_points) - 1:
            return
        self.tempo_mod_points.pop(idx)
        self._draw_tempo_mod_canvas()
        self.update_duration_estimate()

    def _move_mod_point(self, idx, new_time, new_bpm):
        # Keep endpoints locked in time
        duration = self._get_mod_duration_value()
        if idx == 0:
            new_time = 0.0
        elif idx == len(self.tempo_mod_points) - 1:
            new_time = duration
        # Constrain time between neighbors
        prev_t = self.tempo_mod_points[idx - 1]["time"] + 0.02 if idx > 0 else 0.0
        next_t = self.tempo_mod_points[idx + 1]["time"] - 0.02 if idx < len(self.tempo_mod_points) - 1 else duration
        new_time = max(prev_t, min(next_t, new_time))
        new_bpm = max(self._mod_canvas_min_bpm, min(self._mod_canvas_max_bpm, new_bpm))
        self.tempo_mod_points[idx]["time"] = new_time
        self.tempo_mod_points[idx]["bpm"] = new_bpm
        self.tempo_mod_points = self._sanitize_mod_points(self.tempo_mod_points)
        self._draw_tempo_mod_canvas()
        self.update_duration_estimate()

    def on_mod_canvas_click(self, event):
        if not self.tempo_mod_enabled_var.get():
            return
        idx = self._find_mod_handle(event.x, event.y)
        if idx is not None:
            self._mod_drag_index = idx
        else:
            t, bpm_val = self._mod_xy_to_time_bpm(event.x, event.y)
            self._add_mod_point(t, bpm_val)

    def on_mod_canvas_drag(self, event):
        if not self.tempo_mod_enabled_var.get():
            return
        if self._mod_drag_index is None:
            return
        t, bpm_val = self._mod_xy_to_time_bpm(event.x, event.y)
        self._move_mod_point(self._mod_drag_index, t, bpm_val)

    def on_mod_canvas_release(self, event):
        self._mod_drag_index = None

    def on_mod_canvas_double_click(self, event):
        if not self.tempo_mod_enabled_var.get():
            return
        idx = self._find_mod_handle(event.x, event.y)
        if idx is not None:
            self._remove_mod_point(idx)
    
    def toggle_jitter_ui(self):
        """Toggle jitter slider visibility based on checkbox state."""
        if self.jitter_enabled_var.get():
            self.jitter_slider_label.config(state=tk.NORMAL)
            self.jitter_slider.config(state=tk.NORMAL)
            self.jitter_value_label.config(state=tk.NORMAL)
            self.update_jitter_value_label()
        else:
            self.jitter_slider_label.config(state=tk.DISABLED)
            self.jitter_slider.config(state=tk.DISABLED)
            self.jitter_value_label.config(state=tk.DISABLED)
    
    def update_jitter_value_label(self, *args):
        """Update the jitter intensity value label."""
        value = self.jitter_intensity_var.get()
        self.jitter_value_label.config(text=f"{value}%")
    
    def update_duration_estimate(self, *args):
        """Update the duration estimate label when BPM settings change."""
        if not hasattr(self, 'duration_estimate_label'):
            return
            
        # Only show estimate in BPM mode
        if self.length_mode_var.get() != "BPM":
            self.duration_estimate_label.configure(text="")
            return
        
        try:
            # Handle linear tempo modulation preview
            if self.tempo_mod_enabled_var.get():
                bpm_unit_name = self.bpm_unit_var.get()
                # Import BPM_UNITS from config_manager
                from .config_manager import BPM_UNITS
                if bpm_unit_name not in BPM_UNITS:
                    self.duration_estimate_label.configure(text="")
                    return
                
                self._sync_mod_duration_to_entry()
                unit_beats = BPM_UNITS[bpm_unit_name]
                schedule = self.processing_worker.build_graph_modulation_schedule(
                    self.tempo_mod_points,
                    unit_beats
                )
                if not schedule:
                    self.duration_estimate_label.configure(text="")
                    return
                
                total_duration_sec = sum(schedule)
                est_snippets = len(schedule)
                start_bpm = self.tempo_mod_points[0]["bpm"]
                end_bpm = self.tempo_mod_points[-1]["bpm"]
                duration_text = (f"Modulated: {total_duration_sec:.1f}s, {est_snippets} snippets "
                                 f"({start_bpm:.1f}->{end_bpm:.1f} BPM)")
                self.duration_estimate_label.configure(text=duration_text)
                
                # Reflect auto unit count for transparency
                if str(est_snippets) != self.num_units_var.get():
                    self.num_units_var.set(str(est_snippets))
                return
            
            bpm = float(self.bpm_var.get())
            num_units = int(self.num_units_var.get())
            bpm_unit_name = self.bpm_unit_var.get()
            
            # Import BPM_UNITS from config_manager
            from .config_manager import BPM_UNITS
            
            if bpm <= 0 or num_units <= 0 or bpm_unit_name not in BPM_UNITS:
                self.duration_estimate_label.configure(text="")
                return
            
            # Calculate duration
            seconds_per_beat = 60.0 / bpm
            snippet_duration_sec = seconds_per_beat * BPM_UNITS[bpm_unit_name]
            total_duration_sec = snippet_duration_sec * num_units
            
            # Format duration nicely
            if total_duration_sec >= 60:
                minutes = int(total_duration_sec // 60)
                seconds = total_duration_sec % 60
                if seconds == 0:
                    duration_text = f"Estimated duration: {minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    duration_text = f"Estimated duration: {minutes} minute{'s' if minutes != 1 else ''} {seconds:.1f} seconds"
            else:
                duration_text = f"Estimated duration: {total_duration_sec:.1f} seconds"
            
            self.duration_estimate_label.configure(text=duration_text)
            
        except (ValueError, KeyError):
            # Invalid input, hide the estimate
            self.duration_estimate_label.configure(text="")

    def browse_input_files(self):
        """Browse for input video and image files."""
        filetypes = [
            ("Media files", "*.mp4 *.avi *.mov *.mkv *.webm *.png *.jpg *.jpeg *.bmp *.webp *.gif"),
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv"),
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.webp *.gif"),
            ("All files", "*.*")
        ]
        initial_dir = self.last_input_folder if validate_directory_path(self.last_input_folder) else self.config_manager.get_script_dir()

        filepaths = filedialog.askopenfilenames(
            title="Select Input Media Files", 
            initialdir=initial_dir, 
            filetypes=filetypes
        )
        
        if filepaths:
            self.last_input_folder = os.path.dirname(filepaths[0])
            self.add_files_to_queue(filepaths)
            self.update_status(f"Added {len(filepaths)} file(s).")

    def add_files_to_queue(self, filepaths):
        """Add files to the processing queue."""
        # Remove placeholder hint if present
        self.drag_drop_handler.remove_hint()

        current_items = set(self.queue_listbox.get(0, tk.END))

        # Filter out placeholder hint from current items if present
        if self.drag_drop_handler._has_placeholder:
            current_items = {item for item in current_items if "Drag and drop" not in item}
        
        new_items_count = 0
        
        for fp in filepaths:
            normalized_fp = os.path.normpath(fp)
            if normalized_fp not in current_items:
                self.queue_listbox.insert(tk.END, normalized_fp)
                current_items.add(normalized_fp)
                new_items_count += 1
        
        if new_items_count == 0 and filepaths:
            self.update_status("Selected file(s) already in queue.")

    def browse_output_folder(self):
        """Browse for output folder."""
        initial_dir = self.output_folder_var.get() if validate_directory_path(self.output_folder_var.get()) else self.config_manager.get_script_dir()
        
        folder_selected = filedialog.askdirectory(
            title="Select Output Folder", 
            initialdir=initial_dir
        )
        
        if folder_selected:
            self.output_folder_var.set(folder_selected)
            self.update_status(f"Output folder set to: {folder_selected}")
            # Save settings immediately when output folder changes
            self.settings["output_folder"] = folder_selected
            self.config_manager.save_config(self.settings)
            self.logger.info(f"Output folder changed and saved to: {folder_selected}")
    
    def open_output_folder(self):
        """Open the output folder in File Explorer."""
        output_folder = self.output_folder_var.get()
        if output_folder and os.path.exists(output_folder):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(output_folder)
                elif os.name == 'posix':  # macOS and Linux
                    os.system(f'open "{output_folder}"' if sys.platform == 'darwin' else f'xdg-open "{output_folder}"')
                self.update_status(f"Opened folder: {output_folder}")
            except Exception as e:
                self.logger.error(f"Failed to open folder: {e}")
                self.update_status(f"Failed to open folder: {e}")
        else:
            self.update_status("Output folder not set or doesn't exist")

    def clear_selected(self):
        """Clear selected items from the queue."""
        selected_indices = self.queue_listbox.curselection()
        if not selected_indices:
            self.update_status("No items selected to clear.")
            return
        
        for i in sorted(selected_indices, reverse=True):
            self.queue_listbox.delete(i)

        # Add drag and drop hint back if queue becomes empty
        if self.queue_listbox.size() == 0 and self.drag_drop_handler.dnd_available:
            self.drag_drop_handler.add_hint()

        self.update_status("Selected items removed.")

    def clear_all(self):
        """Clear all items from the queue."""
        if self.queue_listbox.size() > 0:
            self.queue_listbox.delete(0, tk.END)
            # Add drag and drop hint back when queue is empty
            if self.drag_drop_handler.dnd_available:
                self.drag_drop_handler.add_hint()
            self.update_status("Queue cleared.")
        else:
            self.update_status("Queue is already empty.")
    
    def open_export_settings(self):
        """Open the export settings dialog."""
        from .export_settings_dialog import ExportSettingsDialog
        
        dialog = ExportSettingsDialog(
            self.root,
            self.config_manager,
            self.aspect_ratio_var.get()
        )
        
        # Wait for dialog to close
        self.root.wait_window(dialog.dialog)
        
        # Get result
        result = dialog.get_result()
        if result:
            self.update_status("Export settings updated.")

    def update_status(self, message):
        """Update the status display with message."""
        try:
            # Update the status bar
            self.status_var.set(message)
            # Also add to the status text area
            self._append_to_status_text(message)
        except tk.TclError:
            safe_print(f"Status update ignored (window closing->): {message}")
    
    def _append_to_status_text(self, message, msg_type="INFO"):
        """Append message to the status text area."""
        try:
            if hasattr(self, 'status_text'):
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Format message based on type
                if msg_type == "ERROR":
                    formatted_message = f"[{timestamp}] ERROR: {message}\n"
                elif msg_type == "WARNING":
                    formatted_message = f"[{timestamp}] WARNING: {message}\n"
                elif msg_type == "SUCCESS":
                    formatted_message = f"[{timestamp}] SUCCESS: {message}\n"
                else:
                    formatted_message = f"[{timestamp}] {message}\n"
                
                self.status_text.config(state=tk.NORMAL)
                self.status_text.insert(tk.END, formatted_message)
                self.status_text.see(tk.END)  # Auto-scroll to bottom
                self.status_text.config(state=tk.DISABLED)
                self.status_text.update()  # Force update
        except (tk.TclError, AttributeError):
            pass  # Ignore if widget is destroyed or doesn't exist
    
    def update_status_error(self, message):
        """Update status with an error message."""
        self.status_var.set(f"ERROR: {message}")
        self._append_to_status_text(message, "ERROR")
    
    def update_status_warning(self, message):
        """Update status with a warning message."""
        self.status_var.set(f"WARNING: {message}")
        self._append_to_status_text(message, "WARNING")
    
    def update_status_success(self, message):
        """Update status with a success message."""
        self.status_var.set(f"SUCCESS: {message}")
        self._append_to_status_text(message, "SUCCESS")

    def enable_generate_button(self, enable=True):
        """Enable or disable the generate button and reset its text."""
        new_state = tk.NORMAL if enable else tk.DISABLED
        try:
            if self.root.winfo_exists():
                if enable:
                    # Reset to Generate button
                    self.root.after(0, lambda: self.generate_button.config(
                        text="GENERATE REMIX",
                        command=self.start_processing_thread,
                        style='Generate.TButton',
                        state=new_state
                    ))
                else:
                    # Change to Abort button
                    self.root.after(0, lambda: self.generate_button.config(
                        text="ABORT PROCESSING",
                        command=self.abort_processing,
                        style='Stop.TButton',
                        state=tk.NORMAL
                    ))
        except tk.TclError:
            safe_print("Generate button state change ignored (window closing->).")

    
    def start_processing_thread(self):
        """Enhanced processing thread starter with queue support for non-continuous mode."""
        # Check if starting continuous mode
        if self.continuous_mode_var.get():
            if not self.continuous_processing:
                self.continuous_processing = True
                self.continuous_count = 0
                self.update_continuous_counter()
            # Process immediately in continuous mode
            self._original_start_processing_thread()
        elif self.run_n_times_enabled_var.get():
            # Run N times mode: process with snapshot settings
            if not self.run_n_processing:
                # Capture snapshot settings at start
                self.run_n_snapshot_settings = self._get_current_settings()
                self.run_n_target = self.run_n_times_var.get()
                self.run_n_current = 0
                self.run_n_processing = True
                self._update_run_n_progress()
                self.logger.info(f"Starting Run N times mode: {self.run_n_target} remixes")
                safe_print(f"[RUN_N] Starting batch of {self.run_n_target} remixes")
            self._process_run_n_times()
        else:
            # Non-continuous mode: Add job to queue
            self._add_job_to_queue()

            # Start queue processor if not already running
            if not self.queue_processor_active and not self.processing_worker.is_processing():
                self.process_next_queued_job()
    
    def _original_start_processing_thread(self):
        """Validates inputs, generates filename, and launches processing thread."""
        if self.processing_worker.is_processing():
            messagebox.showwarning("Busy", "Processing is already in progress.")
            return

        # Check FFmpeg tools
        ffmpeg_found, ffprobe_found = self.processing_worker.get_video_processor().are_tools_available()
        if not ffmpeg_found or not ffprobe_found:
            messagebox.showerror("Missing Dependency", "Cannot process. FFmpeg/FFprobe not found.")
            return

        input_files = list(self.queue_listbox.get(0, tk.END))

        # Filter out placeholder hint if present
        if self.drag_drop_handler._has_placeholder and input_files:
            input_files = [f for f in input_files if "Drag and drop" not in f]
        
        if not input_files:
            messagebox.showwarning("Input Required", "Please add video files to the queue.")
            return

        output_folder = self.output_folder_var.get()
        if not output_folder or not validate_directory_path(output_folder):
            messagebox.showerror("Invalid Path", f"Output folder is invalid or not set:\\n{output_folder}")
            return

        length_mode = self.length_mode_var.get()
        aspect_ratio_selection = self.aspect_ratio_var.get()

        # Validate aspect ratio
        if aspect_ratio_selection not in self.config_manager.get_aspect_ratios():
            messagebox.showerror("Invalid Input", "Invalid Aspect Ratio selected.")
            return

        try:
            # Calculate durations
            settings = {
                "duration_seconds": self.duration_seconds_var.get(),
                "bpm": self.bpm_var.get(),
                "num_units": self.num_units_var.get(),
                "bpm_unit": self.bpm_unit_var.get(),
                "tempo_mod_enabled": self.tempo_mod_enabled_var.get(),
                "tempo_mod_start_bpm": self.tempo_mod_start_bpm_var.get(),
                "tempo_mod_end_bpm": self.tempo_mod_end_bpm_var.get(),
                "tempo_mod_duration_seconds": self.tempo_mod_duration_var.get(),
                "jitter_enabled": self.jitter_enabled_var.get(),
                "jitter_intensity": self.jitter_intensity_var.get()
            }
            
            target_total_duration_sec, snippet_duration_spec = self.processing_worker.calculate_durations(
                length_mode, settings
            )

        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check length/BPM settings:\\n{e}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during setup:\\n{e}")
            return

        # Generate unique filename
        final_output_path = self.processing_worker.generate_output_filename(
            aspect_ratio_selection, output_folder
        )

        # Setup UI for processing
        self.enable_generate_button(False)  # This now changes button to ABORT
        output_msg = f"Output: {os.path.basename(final_output_path)}"
        self.update_status(output_msg)
        # Log output file for launcher log area
        safe_print(f"[VIDEO] {output_msg}")
        self.logger.info(f"Starting video processing - {output_msg}")

        # Small delay before starting, so user sees the name
        self.root.after(500, self._start_thread_delayed, input_files, final_output_path, 
                       target_total_duration_sec, snippet_duration_spec, aspect_ratio_selection, settings)

    def _start_thread_delayed(self, input_files, final_output_path, target_total_duration_sec, 
                             snippet_duration_spec, aspect_ratio_selection, settings):
        """Helper to start the thread after a short GUI delay."""
        start_msg = "Starting processing..."
        self.update_status(start_msg)
        # Log start for launcher log area
        safe_print(f"[START] {start_msg}")
        self.logger.info(f"Processing started: {len(input_files)} input files, target duration: {target_total_duration_sec:.1f}s")
        
        # Define callbacks
        def progress_callback(message):
            self.update_status(message)
            # Also log to stdout so it appears in launcher log area
            safe_print(f"Progress: {message}")
            # And log through the logging system
            self.logger.info(f"Progress: {message}")
        
        def error_callback(error_type, title, message):
            # Log error/warning to stdout for launcher log area
            if error_type == "warning":
                safe_print(f"[WARNING] {title}: {message}")
                self.logger.warning(f"{title}: {message}")
                self.update_status_warning(f"{title}: {message}")
                self.root.after(0, messagebox.showwarning, title, message)
            else:
                safe_print(f"[ERROR] {title}: {message}")
                self.logger.error(f"{title}: {message}")
                self.update_status_error(f"{title}: {message}")
                self.root.after(0, messagebox.showerror, title, message)
        
        def completion_callback(success, output_path):
            if success:
                self.continuous_count += 1
                success_msg = f"Remix #{self.continuous_count} saved: {os.path.basename(output_path)}"
                self.update_status_success(success_msg)
                # Log success to stdout for launcher log area
                safe_print(f"[SUCCESS] {success_msg}")
                self.logger.info(success_msg)
                
                # Update counter display with latest settings 
                self.update_continuous_counter()
                
                # If continuous mode is enabled, start next remix
                if self.continuous_processing and self.continuous_mode_var.get():
                    self.root.after(2000, self.start_next_continuous_remix)  # 2 second delay
                else:
                    self.enable_generate_button(True)
                    self.continuous_processing = False
            else:
                failure_msg = "Processing failed. Check console for details."
                self.update_status_error(failure_msg)
                # Log failure to stdout for launcher log area
                safe_print(f"[FAILED] {failure_msg}")
                self.logger.error(failure_msg)
                self.enable_generate_button(True)
                self.continuous_processing = False

        # Get export settings from config
        export_settings = self.config_manager.get_export_settings().copy()

        # Add jitter settings to export settings
        export_settings["jitter_enabled"] = settings.get("jitter_enabled", False)
        export_settings["jitter_intensity"] = settings.get("jitter_intensity", 50)

        # Add aspect ratio mode and audio preference
        export_settings["aspect_ratio_mode"] = self.aspect_ratio_mode_var.get()
        export_settings["remove_audio"] = self.mute_audio_var.get()

        # Start processing
        self.processing_worker.start_processing_thread(
            input_files, final_output_path, target_total_duration_sec,
            snippet_duration_spec, aspect_ratio_selection,
            export_settings,
            progress_callback, error_callback, completion_callback
        )

    def _process_run_n_times(self):
        """Process a single remix in Run N times mode using snapshot settings."""
        if not self.run_n_processing:
            return

        if self.run_n_current >= self.run_n_target:
            # Batch complete
            self._complete_run_n_times()
            return

        # Check if already processing
        if self.processing_worker.is_processing():
            messagebox.showwarning("Busy", "Processing is already in progress.")
            return

        # Check FFmpeg tools
        ffmpeg_found, ffprobe_found = self.processing_worker.get_video_processor().are_tools_available()
        if not ffmpeg_found or not ffprobe_found:
            messagebox.showerror("Missing Dependency", "Cannot process. FFmpeg/FFprobe not found.")
            self.stop_run_n_times_mode()
            return

        # Use current input files (not snapshot)
        input_files = list(self.queue_listbox.get(0, tk.END))
        if self.drag_drop_handler._has_placeholder and input_files:
            input_files = [f for f in input_files if "Drag and drop" not in f]

        if not input_files:
            messagebox.showwarning("Input Required", "Please add video files to the queue.")
            self.stop_run_n_times_mode()
            return

        # Use snapshot settings for consistency
        settings = self.run_n_snapshot_settings
        output_folder = settings.get("output_folder", self.output_folder_var.get())
        length_mode = settings.get("length_mode", self.length_mode_var.get())
        aspect_ratio_selection = settings.get("aspect_ratio", self.aspect_ratio_var.get())

        if not output_folder or not validate_directory_path(output_folder):
            messagebox.showerror("Invalid Path", f"Output folder is invalid or not set:\n{output_folder}")
            self.stop_run_n_times_mode()
            return

        try:
            # Calculate durations from snapshot settings
            target_total_duration_sec, snippet_duration_spec = self.processing_worker.calculate_durations(
                length_mode, settings
            )
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check settings:\n{e}")
            self.stop_run_n_times_mode()
            return

        # Generate unique filename
        final_output_path = self.processing_worker.generate_output_filename(
            aspect_ratio_selection, output_folder
        )

        # Setup UI
        self.enable_generate_button(False)
        self.run_n_current += 1
        self._update_run_n_progress()

        output_msg = f"Output: {os.path.basename(final_output_path)} ({self.run_n_current}/{self.run_n_target})"
        self.update_status(output_msg)
        safe_print(f"[RUN_N] {output_msg}")
        self.logger.info(f"Run N times: Processing remix {self.run_n_current}/{self.run_n_target}")

        # Small delay then start
        self.root.after(500, self._start_run_n_thread_delayed, input_files, final_output_path,
                        target_total_duration_sec, snippet_duration_spec, aspect_ratio_selection, settings)

    def _start_run_n_thread_delayed(self, input_files, final_output_path,
                                     target_total_duration_sec, snippet_duration_spec,
                                     aspect_ratio_selection, settings):
        """Start a Run N times processing thread."""
        self.update_status(f"Starting remix {self.run_n_current}/{self.run_n_target}...")
        safe_print(f"[RUN_N] Starting remix {self.run_n_current}/{self.run_n_target}")

        # Define callbacks
        def progress_callback(message):
            self.update_status(f"[{self.run_n_current}/{self.run_n_target}] {message}")
            safe_print(f"[RUN_N {self.run_n_current}/{self.run_n_target}] {message}")

        def error_callback(error_type, title, message):
            if error_type == "warning":
                safe_print(f"[WARNING] {title}: {message}")
                self.update_status_warning(f"{title}: {message}")
                self.root.after(0, messagebox.showwarning, title, message)
            else:
                safe_print(f"[ERROR] {title}: {message}")
                self.update_status_error(f"{title}: {message}")
                self.root.after(0, messagebox.showerror, title, message)

        def completion_callback(success, output_path):
            if success:
                success_msg = f"Remix {self.run_n_current}/{self.run_n_target} saved: {os.path.basename(output_path)}"
                self.update_status_success(success_msg)
                safe_print(f"[SUCCESS] {success_msg}")
                self.logger.info(success_msg)

                # Check if more to process
                if self.run_n_processing and self.run_n_current < self.run_n_target:
                    self.root.after(2000, self._process_run_n_times)
                else:
                    self._complete_run_n_times()
            else:
                failure_msg = f"Remix {self.run_n_current}/{self.run_n_target} failed"
                self.update_status_error(failure_msg)
                safe_print(f"[FAILED] {failure_msg}")
                self.logger.error(failure_msg)
                self.enable_generate_button(True)
                self.stop_run_n_times_mode()

        # Build export settings from snapshot
        export_settings = self.config_manager.get_export_settings().copy()
        export_settings["jitter_enabled"] = settings.get("jitter_enabled", False)
        export_settings["jitter_intensity"] = settings.get("jitter_intensity", 50)
        export_settings["aspect_ratio_mode"] = settings.get("aspect_ratio_mode", "Crop to Fill")
        export_settings["remove_audio"] = settings.get("mute_audio", False)

        # Start processing
        self.processing_worker.start_processing_thread(
            input_files, final_output_path, target_total_duration_sec,
            snippet_duration_spec, aspect_ratio_selection,
            export_settings,
            progress_callback, error_callback, completion_callback
        )

    def on_window_configure(self, event):
        """Handle window resize/state changes to show/hide status section."""
        if event.widget == self.root:
            # Check if window is maximized (either by button or by size)
            is_maximized = (self.root.state() == 'zoomed' or 
                          self.root.winfo_width() > 1200 or 
                          self.root.winfo_height() > 800)
            
            if is_maximized != self.window_maximized:
                self.window_maximized = is_maximized
                if is_maximized:
                    # Show status section when maximized
                    self.status_container.pack(fill=tk.BOTH, expand=True, pady=(10,0))
                else:
                    # Hide status section when not maximized
                    self.status_container.pack_forget()
    
    def on_closing(self):
        """Handles window closing: saves settings, prompts if processing."""
        if self.processing_worker.is_processing():
            if not messagebox.askokcancel(
                "Quit", 
                "Processing is active. Quitting now may leave temporary files.\\nAre you sure you want to quit->"
            ):
                return

        # Save current settings
        self.settings["last_input_folder"] = self.last_input_folder
        self.settings["output_folder"] = self.output_folder_var.get()
        self.settings["length_mode"] = self.length_mode_var.get()
        self.settings["aspect_ratio"] = self.aspect_ratio_var.get()
        self.settings["aspect_ratio_mode"] = self.aspect_ratio_mode_var.get()
        self.settings["tempo_mod_enabled"] = self.tempo_mod_enabled_var.get()
        self.settings["tempo_mod_points"] = self.tempo_mod_points
        
        try:
            self.settings["duration_seconds"] = float(self.duration_seconds_var.get())
        except ValueError:
            safe_print("Warning: Invalid duration value not saved.")
            
        try:
            self.settings["bpm"] = float(self.bpm_var.get())
        except ValueError:
            safe_print("Warning: Invalid BPM value not saved.")
            
        try:
            self.settings["tempo_mod_start_bpm"] = float(self.tempo_mod_start_bpm_var.get())
        except ValueError:
            safe_print("Warning: Invalid start BPM value not saved.")
        
        try:
            self.settings["tempo_mod_end_bpm"] = float(self.tempo_mod_end_bpm_var.get())
        except ValueError:
            safe_print("Warning: Invalid end BPM value not saved.")
        
        try:
            self.settings["tempo_mod_duration_seconds"] = float(self.tempo_mod_duration_var.get())
        except ValueError:
            safe_print("Warning: Invalid tempo mod duration value not saved.")
            
        self.settings["bpm_unit"] = self.bpm_unit_var.get()
        
        try:
            self.settings["num_units"] = int(self.num_units_var.get())
        except ValueError:
            safe_print("Warning: Invalid units value not saved.")
            
        # Save continuous mode setting
        self.settings["continuous_mode"] = self.continuous_mode_var.get()
        self.settings["mute_audio"] = self.mute_audio_var.get()

        # Save jitter settings
        self.settings["jitter_enabled"] = self.jitter_enabled_var.get()
        self.settings["jitter_intensity"] = self.jitter_intensity_var.get()

        self.config_manager.save_config(self.settings)
        safe_print("Settings saved. Exiting.")
        self.root.destroy()

    def toggle_run_n_times(self):
        """Toggle Run N times mode on/off."""
        if self.run_n_times_enabled_var.get():
            self.run_n_spinbox.config(state=tk.NORMAL)
            self.update_status("Run N times enabled - click Generate to start batch")
        else:
            self.run_n_spinbox.config(state=tk.DISABLED)
            self.run_n_progress_label.config(text="")
            if self.run_n_processing:
                self.stop_run_n_times_mode()
            self.update_status("Run N times disabled")

    def stop_run_n_times_mode(self):
        """Stop Run N times mode."""
        if self.run_n_processing:
            completed = self.run_n_current
            target = self.run_n_target
            self.run_n_processing = False
            self.enable_generate_button(True)
            self._update_run_n_progress()

            self.update_status(f"Run N times stopped. Completed {completed}/{target} remixes.")
            safe_print(f"[RUN_N] Stopped after {completed}/{target} remixes")
            self.logger.info(f"Run N times stopped: {completed}/{target} completed")

    def _update_run_n_progress(self):
        """Update the Run N times progress label."""
        if self.run_n_processing:
            self.run_n_progress_label.config(
                text=f"Progress: {self.run_n_current}/{self.run_n_target}"
            )
        else:
            self.run_n_progress_label.config(text="")

    def _complete_run_n_times(self):
        """Complete the Run N times batch."""
        total = self.run_n_current
        self.run_n_processing = False
        self.enable_generate_button(True)

        success_msg = f"Batch complete! Created {total} remixes."
        self.update_status_success(success_msg)
        safe_print(f"[RUN_N] {success_msg}")
        self.logger.info(f"Run N times completed: {total} remixes generated")

        # Clear progress display after a delay
        self.root.after(5000, lambda: self.run_n_progress_label.config(text=""))

    def toggle_continuous_mode(self):
        """Toggle continuous mode on/off - only updates UI, doesn't start processing."""
        if self.continuous_mode_var.get():
            # Disable Run N times when continuous mode is enabled
            self.run_n_times_enabled_var.set(False)
            self.run_n_spinbox.config(state=tk.DISABLED)
            self.run_n_frame.pack_forget()

            # Checkbox is checked - just update status, don't start processing
            # Actual processing starts when user clicks Generate button
            self._last_continuous_settings = self._get_current_settings()
            
            # Enhanced status message showing current settings
            if self.length_mode_var.get() == "BPM":
                bpm = self._last_continuous_settings.get("bpm", "N/A")
                units = self._last_continuous_settings.get("num_units", "N/A")
                unit_type = self._last_continuous_settings.get("bpm_unit", "N/A")
                settings_info = f"BPM: {bpm}, {units} {unit_type}s"
            else:
                duration = self._last_continuous_settings.get("duration_seconds", "N/A")
                settings_info = f"Duration: {duration}s"
            
            status_msg = f"Continuous mode enabled ({settings_info}) - click Generate to start"
            self.update_status(status_msg)
            # Don't log as [CONTINUOUS] since we're not actually processing yet
            self.logger.info(f"Continuous mode checkbox checked with settings: {settings_info}")
            
            # Just update counter display, don't change processing state
            if not self.continuous_processing:
                self.continuous_count = 0
                self.update_continuous_counter()
        else:
            self.update_status("Continuous mode disabled - Queue mode active")
            # Only stop processing if it was actually running
            if self.continuous_processing:
                self.continuous_processing = False
            # Generate button is always visible

            # Re-show Run N times frame
            self.run_n_frame.pack(pady=(5, 5))

        # Update queue display based on mode
        self.update_queue_display()
    
    def start_next_continuous_remix(self):
        """Start the next remix in continuous mode with dynamic settings update."""
        if self.continuous_processing and self.continuous_mode_var.get():
            # Capture current settings to detect changes
            current_settings = self._get_current_settings()
            
            # Log current settings for next remix
            if hasattr(self, '_last_continuous_settings'):
                changes = self._detect_setting_changes(self._last_continuous_settings, current_settings)
                if changes:
                    change_msg = f"Settings updated for remix #{self.continuous_count + 1}: {', '.join(changes)}"
                    self.update_status(change_msg)
                    safe_print(f"[CONTINUOUS] {change_msg}")
                    self.logger.info(f"Continuous mode - {change_msg}")
            
            # Store current settings for next comparison
            self._last_continuous_settings = current_settings.copy()
            
            # Create enhanced status message with current settings
            if self.tempo_mod_enabled_var.get():
                start_bpm = current_settings.get("tempo_mod_start_bpm", "N/A")
                end_bpm = current_settings.get("tempo_mod_end_bpm", "N/A")
                mod_duration = current_settings.get("tempo_mod_duration_seconds", "N/A")
                status_msg = (f"Starting remix #{self.continuous_count + 1} "
                              f"(BPM ramp: {start_bpm}->{end_bpm} over {mod_duration}s)...")
            elif self.length_mode_var.get() == "BPM":
                bpm = current_settings.get("bpm", "N/A")
                units = current_settings.get("num_units", "N/A")
                unit_type = current_settings.get("bpm_unit", "N/A")
                status_msg = f"Starting remix #{self.continuous_count + 1} (BPM: {bpm}, {units} {unit_type}s)..."
            else:
                duration = current_settings.get("duration_seconds", "N/A")
                status_msg = f"Starting remix #{self.continuous_count + 1} (Duration: {duration}s)..."
            
            self.update_status(status_msg)
            safe_print(f"[CONTINUOUS] {status_msg}")
            
            # Start the actual processing with fresh settings
            self._original_start_processing_thread()
    
    def _get_current_settings(self):
        """Get current settings from GUI controls."""
        return {
            "output_folder": self.output_folder_var.get(),
            "duration_seconds": self.duration_seconds_var.get(),
            "bpm": self.bpm_var.get(),
            "num_units": self.num_units_var.get(),
            "bpm_unit": self.bpm_unit_var.get(),
            "tempo_mod_enabled": self.tempo_mod_enabled_var.get(),
            "tempo_mod_start_bpm": self.tempo_mod_start_bpm_var.get(),
            "tempo_mod_end_bpm": self.tempo_mod_end_bpm_var.get(),
            "tempo_mod_duration_seconds": self.tempo_mod_duration_var.get(),
            "tempo_mod_points": self.tempo_mod_points.copy(),
            "jitter_enabled": self.jitter_enabled_var.get(),
            "jitter_intensity": self.jitter_intensity_var.get(),
            "length_mode": self.length_mode_var.get(),
            "aspect_ratio": self.aspect_ratio_var.get(),
            "aspect_ratio_mode": self.aspect_ratio_mode_var.get(),
            "mute_audio": self.mute_audio_var.get()
        }

    def get_remixer_settings(self) -> RemixerSettings:
        """Extract current settings from UI variables into typed dataclass."""
        return RemixerSettings(
            output_folder=self.output_folder_var.get(),
            length_mode=self.length_mode_var.get(),
            duration_seconds=float(self.duration_seconds_var.get() or 0),
            bpm=float(self.bpm_var.get() or 120.0),
            bpm_unit=self.bpm_unit_var.get(),
            num_units=int(self.num_units_var.get() or 4),
            aspect_ratio=self.aspect_ratio_var.get(),
            aspect_ratio_mode=self.aspect_ratio_mode_var.get(),
            continuous_mode=self.continuous_mode_var.get(),
            mute_audio=self.mute_audio_var.get(),
            jitter_enabled=self.jitter_enabled_var.get(),
            jitter_intensity=self.jitter_intensity_var.get(),
            tempo_mod_enabled=self.tempo_mod_enabled_var.get(),
            tempo_mod_start_bpm=float(self.tempo_mod_start_bpm_var.get() or 120.0),
            tempo_mod_end_bpm=float(self.tempo_mod_end_bpm_var.get() or 120.0),
            tempo_mod_duration=float(self.tempo_mod_duration_var.get() or 15.0),
        )

    def _detect_setting_changes(self, old_settings, new_settings):
        """Detect and describe changes between settings."""
        changes = []
        
        # Check for important setting changes
        if old_settings.get("bpm") != new_settings.get("bpm"):
            changes.append(f"BPM {old_settings.get('bpm')} -> {new_settings.get('bpm')}")
        
        if old_settings.get("num_units") != new_settings.get("num_units"):
            changes.append(f"Units {old_settings.get('num_units')} -> {new_settings.get('num_units')}")
        
        if old_settings.get("bpm_unit") != new_settings.get("bpm_unit"):
            changes.append(f"Unit type {old_settings.get('bpm_unit')} -> {new_settings.get('bpm_unit')}")
        
        if old_settings.get("duration_seconds") != new_settings.get("duration_seconds"):
            changes.append(f"Duration {old_settings.get('duration_seconds')}s -> {new_settings.get('duration_seconds')}s")

        if old_settings.get("tempo_mod_enabled") != new_settings.get("tempo_mod_enabled"):
            mod_state = "enabled" if new_settings.get("tempo_mod_enabled") else "disabled"
            changes.append(f"Tempo modulation {mod_state}")
        
        if old_settings.get("tempo_mod_start_bpm") != new_settings.get("tempo_mod_start_bpm"):
            changes.append(f"Start BPM {old_settings.get('tempo_mod_start_bpm')} -> {new_settings.get('tempo_mod_start_bpm')}")
        
        if old_settings.get("tempo_mod_end_bpm") != new_settings.get("tempo_mod_end_bpm"):
            changes.append(f"End BPM {old_settings.get('tempo_mod_end_bpm')} -> {new_settings.get('tempo_mod_end_bpm')}")
        
        if old_settings.get("tempo_mod_duration_seconds") != new_settings.get("tempo_mod_duration_seconds"):
            changes.append(f"Mod clip {old_settings.get('tempo_mod_duration_seconds')}s -> {new_settings.get('tempo_mod_duration_seconds')}s")
        
        if old_settings.get("tempo_mod_points") != new_settings.get("tempo_mod_points"):
            changes.append("Tempo graph updated")
        
        if old_settings.get("jitter_enabled") != new_settings.get("jitter_enabled"):
            jitter_state = "enabled" if new_settings.get("jitter_enabled") else "disabled"
            changes.append(f"Jitter {jitter_state}")
        
        if (old_settings.get("jitter_enabled") and new_settings.get("jitter_enabled") and 
            old_settings.get("jitter_intensity") != new_settings.get("jitter_intensity")):
            changes.append(f"Jitter intensity {old_settings.get('jitter_intensity')}% -> {new_settings.get('jitter_intensity')}%")
        
        if old_settings.get("aspect_ratio") != new_settings.get("aspect_ratio"):
            changes.append(f"Aspect ratio {old_settings.get('aspect_ratio')} -> {new_settings.get('aspect_ratio')}")
        
        if old_settings.get("mute_audio") != new_settings.get("mute_audio"):
            audio_state = "muted" if new_settings.get("mute_audio") else "enabled"
            changes.append(f"Audio {audio_state}")
        
        if old_settings.get("length_mode") != new_settings.get("length_mode"):
            changes.append(f"Mode {old_settings.get('length_mode')} -> {new_settings.get('length_mode')}")
        
        return changes

    def stop_continuous_mode(self):
        """Stop continuous mode."""
        self.continuous_processing = False
        self.continuous_mode_var.set(False)
        self.enable_generate_button(True)
        self.update_status(f"Continuous mode stopped. Created {self.continuous_count} remixes.")
    
    def abort_processing(self):
        """Abort the current processing operation."""
        if self.continuous_processing:
            # If in continuous mode, stop continuous mode
            self.stop_continuous_mode()
        elif self.run_n_processing:
            # If in Run N times mode, stop it
            self.stop_run_n_times_mode()
        elif self.processing_worker.is_processing():
            # Single processing - abort it
            self.update_status("Aborting processing...")
            self.processing_worker.abort_processing()
            self.enable_generate_button(True)
    
    def update_continuous_counter(self):
        """Update the continuous mode counter display with current settings."""
        if self.continuous_mode_var.get():
            # Basic counter info
            counter_text = f"Remixes created: {self.continuous_count}"
            
            # Always show current live values from GUI widgets, not cached settings
            if self.tempo_mod_enabled_var.get():
                start_bpm = self.tempo_mod_start_bpm_var.get()
                end_bpm = self.tempo_mod_end_bpm_var.get()
                duration = self.tempo_mod_duration_var.get()
                settings_info = f" | Current: {start_bpm}->{end_bpm} BPM over {duration}s"
            elif self.length_mode_var.get() == "BPM":
                # Read current values directly from GUI
                bpm = self.bpm_var.get()
                units = self.num_units_var.get()
                unit_type = self.bpm_unit_var.get()
                settings_info = f" | Current: {bpm} BPM, {units} {unit_type}s"
            else:
                # Read current duration directly from GUI
                duration = self.duration_seconds_var.get()
                settings_info = f" | Current: {duration}s"
            
            counter_text += settings_info
            self.continuous_label.configure(text=counter_text)
        else:
            self.continuous_label.configure(text="")

    def update_continuous_counter_on_change(self, *args):
        """Update the continuous mode counter display when any relevant setting changes."""
        if self.continuous_mode_var.get():
            self.update_continuous_counter()

    def on_entry_update(self, event=None):
        """Handle immediate updates when user finishes editing input fields (Enter or focus loss)."""
        # Update duration estimate if in BPM mode
        self.update_duration_estimate()
        
        # Update continuous counter display if continuous mode is active
        if self.continuous_mode_var.get():
            self.update_continuous_counter()
            
            # Provide subtle feedback that the change was registered
            if hasattr(self, '_last_continuous_settings'):
                current_settings = self._get_current_settings()
                changes = self._detect_setting_changes(self._last_continuous_settings, current_settings)
                if changes:
                    # Brief status update to show change was registered
                    widget = event.widget if event else None
                    if widget == self.bpm_entry:
                        self.update_status(f"BPM updated to {self.bpm_var.get()} - will apply to next remix")
                    elif widget == self.num_units_entry:
                        self.update_status(f"Units updated to {self.num_units_var.get()} - will apply to next remix")
                    elif widget == self.seconds_entry:
                        self.update_status(f"Duration updated to {self.duration_seconds_var.get()}s - will apply to next remix")
                    elif widget == getattr(self, "tempo_mod_start_entry", None):
                        self.update_status(f"Start BPM updated to {self.tempo_mod_start_bpm_var.get()} - will apply to next remix")
                        if self.tempo_mod_points:
                            self.tempo_mod_points[0]["bpm"] = float(self.tempo_mod_start_bpm_var.get())
                            self._draw_tempo_mod_canvas()
                    elif widget == getattr(self, "tempo_mod_end_entry", None):
                        self.update_status(f"End BPM updated to {self.tempo_mod_end_bpm_var.get()} - will apply to next remix")
                        if self.tempo_mod_points:
                            self.tempo_mod_points[-1]["bpm"] = float(self.tempo_mod_end_bpm_var.get())
                            self._draw_tempo_mod_canvas()
                    elif widget == getattr(self, "tempo_mod_duration_entry", None):
                        self.update_status(f"Clip duration updated to {self.tempo_mod_duration_var.get()}s - will apply to next remix")
                        self._sync_mod_duration_to_entry()
                        self._draw_tempo_mod_canvas()
                    else:
                        self.update_status("Settings updated - will apply to next remix")
                    
                    # Log the change for debugging
                    safe_print(f"[ENTRY_UPDATE] User finished editing: {', '.join(changes)}")
                    self.logger.info(f"Real-time update: {', '.join(changes)}")
        
        # Return focus handling for Enter key (moves to next widget or removes focus)
        if event and event.keysym == 'Return':
            # For better UX, move focus to next logical field or remove focus
            widget = event.widget
            if widget == self.bpm_entry:
                self.num_units_entry.focus()
            elif widget == self.num_units_entry:
                # Clear focus after units entry to apply the change
                self.root.focus()
            elif widget == self.seconds_entry:
                # Clear focus after seconds entry to apply the change
                self.root.focus()
            elif widget == getattr(self, "tempo_mod_start_entry", None):
                self.tempo_mod_end_entry.focus()
            elif widget == getattr(self, "tempo_mod_end_entry", None):
                self.tempo_mod_duration_entry.focus()
            elif widget == getattr(self, "tempo_mod_duration_entry", None):
                self.root.focus()
            else:
                event.widget.tk_focusNext().focus()

    
    def _add_job_to_queue(self):
        """Add a new job to the processing queue with current settings."""
        # Validate inputs first
        if not self._validate_inputs_for_queue():
            return
        
        try:
            # Get current settings
            input_files = list(self.queue_listbox.get(0, tk.END))

            # Filter out placeholder hint if present
            if self.drag_drop_handler._has_placeholder and input_files:
                input_files = [f for f in input_files if "Drag and drop" not in f]

            output_folder = self.output_folder_var.get()
            length_mode = self.length_mode_var.get()
            aspect_ratio_selection = self.aspect_ratio_var.get()
            
            # Calculate durations
            settings = {
                "duration_seconds": self.duration_seconds_var.get(),
                "bpm": self.bpm_var.get(),
                "num_units": self.num_units_var.get(),
                "bpm_unit": self.bpm_unit_var.get(),
                "tempo_mod_enabled": self.tempo_mod_enabled_var.get(),
                "tempo_mod_start_bpm": self.tempo_mod_start_bpm_var.get(),
                "tempo_mod_end_bpm": self.tempo_mod_end_bpm_var.get(),
                "tempo_mod_duration_seconds": self.tempo_mod_duration_var.get(),
                "jitter_enabled": self.jitter_enabled_var.get(),
                "jitter_intensity": self.jitter_intensity_var.get()
            }
            
            target_total_duration_sec, snippet_duration_spec = self.processing_worker.calculate_durations(
                length_mode, settings
            )
            
            # Generate unique filename
            final_output_path = self.processing_worker.generate_output_filename(
                aspect_ratio_selection, output_folder
            )
            
            # Get export settings
            export_settings = self.config_manager.get_export_settings().copy()
            export_settings["jitter_enabled"] = settings.get("jitter_enabled", False)
            export_settings["jitter_intensity"] = settings.get("jitter_intensity", 50)
            export_settings["aspect_ratio_mode"] = self.aspect_ratio_mode_var.get()
            export_settings["remove_audio"] = self.mute_audio_var.get()
            
            # Create job
            job = ProcessingJob(
                input_files=input_files.copy(),
                output_path=final_output_path,
                target_duration=target_total_duration_sec,
                snippet_duration=snippet_duration_spec,
                aspect_ratio=aspect_ratio_selection,
                export_settings=export_settings.copy(),
                length_mode=length_mode,
                bpm=float(self.bpm_var.get()),
                num_units=int(self.num_units_var.get()),
                bpm_unit=self.bpm_unit_var.get(),
                tempo_mod_enabled=self.tempo_mod_enabled_var.get(),
                tempo_mod_start_bpm=float(self.tempo_mod_start_bpm_var.get()),
                tempo_mod_end_bpm=float(self.tempo_mod_end_bpm_var.get()),
                tempo_mod_duration_seconds=float(self.tempo_mod_duration_var.get()),
                tempo_mod_points=self.tempo_mod_points.copy(),
                jitter_enabled=self.jitter_enabled_var.get(),
                jitter_intensity=self.jitter_intensity_var.get()
            )
            
            # Add to queue
            job_id = self.job_queue.add_job(job)
            
            # Show feedback
            queue_status = self.job_queue.get_queue_status()
            self.update_status(f"Added to queue: {job.get_display_name()}")
            safe_print(f"[QUEUE] Job added: {job.get_display_name()}")
            self.logger.info(f"Job {job_id} added to queue: {job.get_duration_text()}")
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check settings:\\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add job to queue:\\n{e}")
    
    def _validate_inputs_for_queue(self):
        """Validate inputs before adding to queue."""
        # Check FFmpeg tools
        ffmpeg_found, ffprobe_found = self.processing_worker.get_video_processor().are_tools_available()
        if not ffmpeg_found or not ffprobe_found:
            messagebox.showerror("Missing Dependency", "Cannot process. FFmpeg/FFprobe not found.")
            return False
        
        input_files = list(self.queue_listbox.get(0, tk.END))

        # Filter out placeholder hint if present
        if self.drag_drop_handler._has_placeholder and input_files:
            input_files = [f for f in input_files if "Drag and drop" not in f]
        
        if not input_files:
            messagebox.showwarning("Input Required", "Please add video files to the queue.")
            return False
        
        output_folder = self.output_folder_var.get()
        if not output_folder or not validate_directory_path(output_folder):
            messagebox.showerror("Invalid Path", f"Output folder is invalid or not set:\\n{output_folder}")
            return False
        
        aspect_ratio_selection = self.aspect_ratio_var.get()
        if aspect_ratio_selection not in self.config_manager.get_aspect_ratios():
            messagebox.showerror("Invalid Input", "Invalid Aspect Ratio selected.")
            return False
        
        return True
    
    def process_next_queued_job(self):
        """Process the next job in the queue."""
        # Check if already processing
        if self.processing_worker.is_processing():
            return
        
        # Get next job
        job = self.job_queue.get_next_job()
        if not job:
            self.queue_processor_active = False
            self.update_status("Queue processing complete")
            return
        
        self.queue_processor_active = True
        
        # Update UI
        self.enable_generate_button(False)  # Changes to ABORT button
        output_msg = f"Processing: {os.path.basename(job.output_path)}"
        self.update_status(output_msg)
        safe_print(f"[QUEUE] Processing job {job.job_id}: {job.get_display_name()}")
        self.logger.info(f"Starting job {job.job_id} from queue")
        
        # Define callbacks for this job
        def progress_callback(message):
            self.job_queue.update_job_progress(message)
            self.update_status(f"[Job {job.job_id}] {message}")
            safe_print(f"[Job {job.job_id}] {message}")
            self.logger.info(f"Job {job.job_id} progress: {message}")
        
        def error_callback(error_type, title, message):
            if error_type == "warning":
                safe_print(f"[WARNING] Job {job.job_id}: {title}: {message}")
                self.logger.warning(f"Job {job.job_id}: {title}: {message}")
                self.update_status_warning(f"Job {job.job_id}: {title}: {message}")
            else:
                safe_print(f"[ERROR] Job {job.job_id}: {title}: {message}")
                self.logger.error(f"Job {job.job_id}: {title}: {message}")
                self.update_status_error(f"Job {job.job_id}: {title}: {message}")
                self.job_queue.complete_current_job(success=False, error_message=message)
        
        def completion_callback(success, output_path):
            self.job_queue.complete_current_job(success=success)
            
            if success:
                success_msg = f"Job {job.job_id} completed: {os.path.basename(output_path)}"
                self.update_status_success(success_msg)
                safe_print(f"[SUCCESS] {success_msg}")
                self.logger.info(success_msg)
            else:
                failure_msg = f"Job {job.job_id} failed"
                self.update_status_error(failure_msg)
                safe_print(f"[FAILED] {failure_msg}")
                self.logger.error(failure_msg)
            
            # Enable button again
            self.enable_generate_button(True)
            
            # Process next job after a short delay
            self.root.after(1000, self.process_next_queued_job)

        # Start processing
        self.processing_worker.start_processing_thread(
            job.input_files, job.output_path, job.target_duration,
            job.snippet_duration, job.aspect_ratio,
            job.export_settings,
            progress_callback, error_callback, completion_callback
        )
    
    def update_queue_display(self):
        """Update the queue status display."""
        status = self.job_queue.get_queue_status()
        
        # Update main queue status
        if status['queue_empty']:
            self.queue_status_label.config(text="Queue: Empty")
            self.queue_details_label.config(text="")
            # Hide details label when empty to save space
            self.queue_details_label.pack_forget()
        else:
            pending = status['pending_count']
            if status['current_job']:
                # Combine into single line to save space
                self.queue_status_label.config(text=f"Queue: Processing ({pending} pending)")
                self.queue_details_label.config(text=status['current_job'])
                self.queue_details_label.pack(pady=(2, 0))
            else:
                if pending == 1:
                    # Single pending job - show on one line
                    pending_jobs = self.job_queue.get_pending_jobs()
                    if pending_jobs:
                        next_job = pending_jobs[0]
                        self.queue_status_label.config(text=f"Queue: 1 job - {next_job.get_display_name()}")
                        self.queue_details_label.config(text="")
                        self.queue_details_label.pack_forget()
                    else:
                        self.queue_status_label.config(text=f"Queue: {pending} jobs pending")
                        self.queue_details_label.config(text="")
                        self.queue_details_label.pack_forget()
                else:
                    # Multiple pending jobs
                    self.queue_status_label.config(text=f"Queue: {pending} jobs pending")
                    pending_jobs = self.job_queue.get_pending_jobs()
                    if pending_jobs:
                        next_job = pending_jobs[0]
                        self.queue_details_label.config(text=f"Next: {next_job.get_display_name()}")
                        self.queue_details_label.pack(pady=(2, 0))
                    else:
                        self.queue_details_label.config(text="")
                        self.queue_details_label.pack_forget()
        
        # Toggle visibility based on mode
        if self.continuous_mode_var.get():
            # Hide queue display in continuous mode
            self.queue_status_label.pack_forget()
            self.queue_details_label.pack_forget()
        else:
            # Show queue display in queue mode
            self.queue_status_label.pack()
    
    def on_job_started(self, job):
        """Callback when a job starts processing."""
        safe_print(f"[QUEUE] Started processing job {job.job_id}")
        self.update_queue_display()
    
    def on_job_completed(self, job):
        """Callback when a job completes."""
        if job.status == JobStatus.COMPLETED:
            safe_print(f"[QUEUE] Job {job.job_id} completed successfully")
        else:
            safe_print(f"[QUEUE] Job {job.job_id} failed: {job.error_message}")
        self.update_queue_display()
    
    def on_job_progress(self, job, message):
        """Callback for job progress updates."""
        # Progress is already handled in progress_callback
        pass


def main():
    """Main entry point for the application."""
    # Create the appropriate root window based on drag and drop availability
    if DND_AVAILABLE:
        try:
            root = TkinterDnD.Tk()
        except Exception:
            root = tk.Tk()
    else:
        root = tk.Tk()
    
    app = VideoRemixerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
