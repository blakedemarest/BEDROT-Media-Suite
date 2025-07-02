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
import logging
from .config_manager import ConfigManager
from .processing_worker import ProcessingWorker
from .utils import safe_print, validate_directory_path
from .logging_config import setup_logging, get_logger


class VideoRemixerApp:
    """
    Main application window for the Video Snippet Remixer.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video Snippet Remixer")
        
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
        self.aspect_ratio_var = tk.StringVar(value=self.settings["aspect_ratio"])
        self.aspect_ratio_mode_var = tk.StringVar(value=self.settings.get("aspect_ratio_mode", "Crop to Fill"))
        self.status_var = tk.StringVar(value="Ready")
        self.continuous_mode_var = tk.BooleanVar(value=self.settings.get("continuous_mode", False))

        # Internal state
        self.last_input_folder = self.settings["last_input_folder"]
        self.continuous_processing = False
        self.continuous_count = 0

        # Bindings
        self.length_mode_var.trace_add("write", self.toggle_length_mode_ui)
        
        # Add bindings for BPM duration estimate updates
        self.bpm_var.trace_add("write", self.update_duration_estimate)
        self.bpm_unit_var.trace_add("write", self.update_duration_estimate)
        self.num_units_var.trace_add("write", self.update_duration_estimate)

        # Window Setup
        self.root.geometry("700x650")
        self.create_widgets()
        self.toggle_length_mode_ui()
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
        main_frame = ttk.Frame(self.root, padding="10")
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
        input_frame = ttk.LabelFrame(parent, text="Input Videos", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        input_list_frame = ttk.Frame(input_frame)
        input_list_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP, pady=(0, 5))
        
        self.queue_listbox = tk.Listbox(
            input_list_frame, 
            listvariable=self.input_file_paths, 
            height=8, 
            selectmode=tk.EXTENDED
        )
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(input_list_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=scrollbar.set)
        
        input_button_frame = ttk.Frame(input_frame)
        input_button_frame.pack(fill=tk.X)
        
        browse_button = ttk.Button(
            input_button_frame, 
            text="Browse Files...", 
            command=self.browse_input_files
        )
        browse_button.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_button = ttk.Button(
            input_button_frame, 
            text="Clear Selected", 
            command=self.clear_selected
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        clear_all_button = ttk.Button(
            input_button_frame, 
            text="Clear All", 
            command=self.clear_all
        )
        clear_all_button.pack(side=tk.LEFT, padx=5)

    def create_output_section(self, parent):
        """Create the output settings section."""
        output_frame = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        output_frame.columnconfigure(1, weight=1)
        
        # Output Folder
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_label = ttk.Label(
            output_frame, 
            textvariable=self.output_folder_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.folder_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        browse_output_button = ttk.Button(
            output_frame, 
            text="Browse...", 
            command=self.browse_output_folder
        )
        browse_output_button.grid(row=0, column=2, padx=5, pady=5)

        # Aspect Ratio
        ttk.Label(output_frame, text="Aspect Ratio:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ar_combobox = ttk.Combobox(
            output_frame, 
            textvariable=self.aspect_ratio_var, 
            values=self.config_manager.get_aspect_ratios(), 
            state="readonly", 
            width=25
        )
        self.ar_combobox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Export Settings Button
        self.export_settings_button = ttk.Button(
            output_frame,
            text="Export Settings",
            command=self.open_export_settings
        )
        self.export_settings_button.grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(output_frame, text="(All videos will be HD quality)").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Aspect Ratio Mode
        ttk.Label(output_frame, text="Aspect Ratio Mode:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Radio buttons frame
        mode_frame = ttk.Frame(output_frame)
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
        length_frame = ttk.LabelFrame(parent, text="Remix Length", padding="10")
        length_frame.pack(fill=tk.X, pady=5)
        
        mode_frame = ttk.Frame(length_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.seconds_radio = ttk.Radiobutton(
            mode_frame, 
            text="Length in Seconds:", 
            variable=self.length_mode_var, 
            value="Seconds"
        )
        self.seconds_radio.pack(side=tk.LEFT, padx=5)
        
        self.bpm_radio = ttk.Radiobutton(
            mode_frame, 
            text="Length by BPM:", 
            variable=self.length_mode_var, 
            value="BPM"
        )
        self.bpm_radio.pack(side=tk.LEFT, padx=20)
        
        # Seconds input frame
        self.seconds_input_frame = ttk.Frame(length_frame)
        ttk.Label(self.seconds_input_frame, text="Total Duration (s):").pack(side=tk.LEFT, padx=5)
        self.seconds_entry = ttk.Entry(
            self.seconds_input_frame, 
            textvariable=self.duration_seconds_var, 
            width=10
        )
        self.seconds_entry.pack(side=tk.LEFT, padx=5)
        
        # BPM input frame
        self.bpm_input_frame = ttk.Frame(length_frame)
        ttk.Label(self.bpm_input_frame, text="BPM:").pack(side=tk.LEFT, padx=5)
        self.bpm_entry = ttk.Entry(self.bpm_input_frame, textvariable=self.bpm_var, width=6)
        self.bpm_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.bpm_input_frame, text="Snippet Unit:").pack(side=tk.LEFT, padx=(15,5))
        self.bpm_unit_combo = ttk.Combobox(
            self.bpm_input_frame, 
            textvariable=self.bpm_unit_var, 
            values=list(self.config_manager.get_bpm_units().keys()), 
            state="readonly", 
            width=10
        )
        self.bpm_unit_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.bpm_input_frame, text="Total Units:").pack(side=tk.LEFT, padx=(15, 5))
        self.num_units_entry = ttk.Entry(
            self.bpm_input_frame, 
            textvariable=self.num_units_var, 
            width=6
        )
        self.num_units_entry.pack(side=tk.LEFT, padx=5)
        
        # Add duration estimate label
        self.duration_estimate_label = ttk.Label(
            self.bpm_input_frame, 
            text="",
            foreground="blue"
        )
        self.duration_estimate_label.pack(side=tk.LEFT, padx=(15, 5))
        
        # Jitter controls frame
        jitter_frame = ttk.Frame(length_frame)
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
        self.jitter_slider_label = ttk.Label(jitter_frame, text="Intensity:")
        self.jitter_slider_label.pack(side=tk.LEFT, padx=(10, 5))
        
        self.jitter_slider = ttk.Scale(
            jitter_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.jitter_intensity_var,
            length=200
        )
        self.jitter_slider.pack(side=tk.LEFT, padx=5)
        
        self.jitter_value_label = ttk.Label(jitter_frame, text="50%")
        self.jitter_value_label.pack(side=tk.LEFT, padx=5)
        
        # Bind slider changes to update the value label
        self.jitter_intensity_var.trace_add("write", self.update_jitter_value_label)
        
        # Initialize jitter UI state
        self.toggle_jitter_ui()

    def create_process_section(self, parent):
        """Create the process button section."""
        process_button_frame = ttk.Frame(parent, padding=(0, 10, 0, 0))
        process_button_frame.pack(fill=tk.X)
        
        # Continuous mode toggle
        continuous_frame = ttk.Frame(process_button_frame)
        continuous_frame.pack(pady=(0, 10))
        
        self.continuous_check = ttk.Checkbutton(
            continuous_frame,
            text="[Continuous Mode] Keep making videos",
            variable=self.continuous_mode_var,
            command=self.toggle_continuous_mode
        )
        self.continuous_check.pack()
        
        # Counter display for continuous mode
        self.continuous_label = ttk.Label(
            continuous_frame,
            text="",
            foreground="blue"
        )
        self.continuous_label.pack(pady=(5, 0))
        
        # Generate button
        self.generate_button = ttk.Button(
            process_button_frame, 
            text="Generate Remix", 
            command=self.start_processing_thread
        )
        self.generate_button.pack(pady=10)
        
        # Stop button (initially hidden)
        self.stop_button = ttk.Button(
            process_button_frame,
            text="[STOP] Stop Continuous Mode",
            command=self.stop_continuous_mode
        )
        # Don't pack initially

    def create_status_section(self, parent):
        """Create the status display section."""
        # Create a simple frame for the status area
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(10,0))
        
        # Create a simple text widget for status messages
        import tkinter.scrolledtext as scrolledtext
        self.status_text = scrolledtext.ScrolledText(
            status_frame, 
            height=8, 
            wrap=tk.WORD, 
            state=tk.NORMAL,  # Start as normal so we can add initial text
            font=('Courier', 9),
            bg='white',
            fg='black'
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add initial message directly
        self.status_text.insert(tk.END, "=== Snippet Remixer Status ===\n")
        self.status_text.insert(tk.END, "Ready to process videos\n")
        self.status_text.config(state=tk.DISABLED)
        
        # Simple status bar at bottom
        self.status_bar = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            padding=5
        )
        self.status_bar.pack(fill=tk.X, pady=(5,0))
        
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
        """Browse for input video files."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv"), 
            ("All files", "*.*")
        ]
        initial_dir = self.last_input_folder if validate_directory_path(self.last_input_folder) else self.config_manager.get_script_dir()
        
        filepaths = filedialog.askopenfilenames(
            title="Select Input Video Files", 
            initialdir=initial_dir, 
            filetypes=filetypes
        )
        
        if filepaths:
            self.last_input_folder = os.path.dirname(filepaths[0])
            self.add_files_to_queue(filepaths)
            self.update_status(f"Added {len(filepaths)} file(s).")

    def add_files_to_queue(self, filepaths):
        """Add files to the processing queue."""
        current_items = set(self.queue_listbox.get(0, tk.END))
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

    def clear_selected(self):
        """Clear selected items from the queue."""
        selected_indices = self.queue_listbox.curselection()
        if not selected_indices:
            self.update_status("No items selected to clear.")
            return
        
        for i in sorted(selected_indices, reverse=True):
            self.queue_listbox.delete(i)
        self.update_status("Selected items removed.")

    def clear_all(self):
        """Clear all items from the queue."""
        if self.queue_listbox.size() > 0:
            self.queue_listbox.delete(0, tk.END)
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
            safe_print(f"Status update ignored (window closing?): {message}")
    
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
        """Enable or disable the generate button."""
        new_state = tk.NORMAL if enable else tk.DISABLED
        try:
            if self.root.winfo_exists():
                self.root.after(0, self.generate_button.config, {'state': new_state})
        except tk.TclError:
            safe_print("Generate button state change ignored (window closing?).")

    def start_processing_thread(self):
        """Enhanced processing thread starter with continuous mode support."""
        # Check if starting continuous mode
        if self.continuous_mode_var.get() and not self.continuous_processing:
            self.continuous_processing = True
            self.continuous_count = 0
            self.stop_button.pack(pady=(0, 10))
            self.generate_button.pack_forget()
            self.update_continuous_counter()
        
        # Original processing logic
        self._original_start_processing_thread()
    
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
                "jitter_enabled": self.jitter_enabled_var.get(),
                "jitter_intensity": self.jitter_intensity_var.get()
            }
            
            target_total_duration_sec, snippet_duration_sec = self.processing_worker.calculate_durations(
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
        self.enable_generate_button(False)
        output_msg = f"Output: {os.path.basename(final_output_path)}"
        self.update_status(output_msg)
        # Log output file for launcher log area
        safe_print(f"[VIDEO] {output_msg}")
        self.logger.info(f"Starting video processing - {output_msg}")

        # Small delay before starting, so user sees the name
        self.root.after(500, self._start_thread_delayed, input_files, final_output_path, 
                       target_total_duration_sec, snippet_duration_sec, aspect_ratio_selection, settings)

    def _start_thread_delayed(self, input_files, final_output_path, target_total_duration_sec, 
                             snippet_duration_sec, aspect_ratio_selection, settings):
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
        export_settings = self.config_manager.get_export_settings()
        
        # Add jitter settings to export settings
        export_settings["jitter_enabled"] = settings.get("jitter_enabled", False)
        export_settings["jitter_intensity"] = settings.get("jitter_intensity", 50)
        
        # Add aspect ratio mode to export settings
        export_settings["aspect_ratio_mode"] = self.aspect_ratio_mode_var.get()
        
        # Start processing
        self.processing_worker.start_processing_thread(
            input_files, final_output_path, target_total_duration_sec,
            snippet_duration_sec, aspect_ratio_selection,
            export_settings,
            progress_callback, error_callback, completion_callback
        )

    def on_closing(self):
        """Handles window closing: saves settings, prompts if processing."""
        if self.processing_worker.is_processing():
            if not messagebox.askokcancel(
                "Quit", 
                "Processing is active. Quitting now may leave temporary files.\\nAre you sure you want to quit?"
            ):
                return

        # Save current settings
        self.settings["last_input_folder"] = self.last_input_folder
        self.settings["output_folder"] = self.output_folder_var.get()
        self.settings["length_mode"] = self.length_mode_var.get()
        self.settings["aspect_ratio"] = self.aspect_ratio_var.get()
        self.settings["aspect_ratio_mode"] = self.aspect_ratio_mode_var.get()
        
        try:
            self.settings["duration_seconds"] = float(self.duration_seconds_var.get())
        except ValueError:
            safe_print("Warning: Invalid duration value not saved.")
            
        try:
            self.settings["bpm"] = float(self.bpm_var.get())
        except ValueError:
            safe_print("Warning: Invalid BPM value not saved.")
            
        self.settings["bpm_unit"] = self.bpm_unit_var.get()
        
        try:
            self.settings["num_units"] = int(self.num_units_var.get())
        except ValueError:
            safe_print("Warning: Invalid units value not saved.")
            
        # Save continuous mode setting
        self.settings["continuous_mode"] = self.continuous_mode_var.get()
        
        # Save jitter settings
        self.settings["jitter_enabled"] = self.jitter_enabled_var.get()
        self.settings["jitter_intensity"] = self.jitter_intensity_var.get()

        self.config_manager.save_config(self.settings)
        safe_print("Settings saved. Exiting.")
        self.root.destroy()
    
    def toggle_continuous_mode(self):
        """Toggle continuous mode on/off."""
        if self.continuous_mode_var.get():
            self.update_status("Continuous mode enabled - will keep generating remixes")
            if not self.continuous_processing:
                self.continuous_count = 0
                self.update_continuous_counter()
        else:
            self.update_status("Continuous mode disabled")
            self.continuous_processing = False
            self.stop_button.pack_forget()
            self.generate_button.pack(pady=10)
    
    def start_next_continuous_remix(self):
        """Start the next remix in continuous mode."""
        if self.continuous_processing and self.continuous_mode_var.get():
            self.update_status(f"Starting remix #{self.continuous_count + 1}...")
            self._original_start_processing_thread()
    
    def stop_continuous_mode(self):
        """Stop continuous mode."""
        self.continuous_processing = False
        self.continuous_mode_var.set(False)
        self.stop_button.pack_forget()
        self.generate_button.pack(pady=10)
        self.enable_generate_button(True)
        self.update_status(f"Continuous mode stopped. Created {self.continuous_count} remixes.")
    
    def update_continuous_counter(self):
        """Update the continuous mode counter display."""
        if self.continuous_mode_var.get():
            self.continuous_label.configure(text=f"Remixes created: {self.continuous_count}")
        else:
            self.continuous_label.configure(text="")


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = VideoRemixerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()