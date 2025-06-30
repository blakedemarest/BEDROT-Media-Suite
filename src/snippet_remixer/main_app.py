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
from .config_manager import ConfigManager
from .processing_worker import ProcessingWorker
from .utils import safe_print, validate_directory_path


class VideoRemixerApp:
    """
    Main application window for the Video Snippet Remixer.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video Snippet Remixer")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.processing_worker = ProcessingWorker(self.config_manager.get_script_dir())
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
        self.status_var = tk.StringVar(value="Ready")

        # Internal state
        self.last_input_folder = self.settings["last_input_folder"]

        # Bindings
        self.length_mode_var.trace_add("write", self.toggle_length_mode_ui)

        # Window Setup
        self.root.geometry("700x650")
        self.create_widgets()
        self.toggle_length_mode_ui()
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

    def create_process_section(self, parent):
        """Create the process button section."""
        process_button_frame = ttk.Frame(parent, padding=(0, 10, 0, 0))
        process_button_frame.pack(fill=tk.X)
        
        self.generate_button = ttk.Button(
            process_button_frame, 
            text="Generate Remix", 
            command=self.start_processing_thread
        )
        self.generate_button.pack(pady=10)

    def create_status_section(self, parent):
        """Create the status bar section."""
        self.status_bar = ttk.Label(
            parent, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            padding=5
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0))

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
            else:
                self.seconds_input_frame.pack_forget()
                self.bpm_input_frame.pack_forget()

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
        """Update the status bar message."""
        try:
            if self.root.winfo_exists():
                self.root.after(0, self.status_var.set, message)
        except tk.TclError:
            safe_print(f"Status update ignored (window closing?): {message}")

    def enable_generate_button(self, enable=True):
        """Enable or disable the generate button."""
        new_state = tk.NORMAL if enable else tk.DISABLED
        try:
            if self.root.winfo_exists():
                self.root.after(0, self.generate_button.config, {'state': new_state})
        except tk.TclError:
            safe_print("Generate button state change ignored (window closing?).")

    def start_processing_thread(self):
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
                "bpm_unit": self.bpm_unit_var.get()
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
        self.update_status(f"Output: {os.path.basename(final_output_path)}")

        # Small delay before starting, so user sees the name
        self.root.after(500, self._start_thread_delayed, input_files, final_output_path, 
                       target_total_duration_sec, snippet_duration_sec, aspect_ratio_selection)

    def _start_thread_delayed(self, input_files, final_output_path, target_total_duration_sec, 
                             snippet_duration_sec, aspect_ratio_selection):
        """Helper to start the thread after a short GUI delay."""
        self.update_status("Starting processing...")
        
        # Define callbacks
        def progress_callback(message):
            self.update_status(message)
        
        def error_callback(error_type, title, message):
            if error_type == "warning":
                self.root.after(0, messagebox.showwarning, title, message)
            else:
                self.root.after(0, messagebox.showerror, title, message)
        
        def completion_callback(success, output_path):
            self.enable_generate_button(True)
            if success:
                self.update_status(f"Success! Remix saved: {os.path.basename(output_path)}")
            else:
                self.update_status("Processing failed. Check console for details.")

        # Get export settings from config
        export_settings = self.config_manager.get_export_settings()
        
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

        self.config_manager.save_config(self.settings)
        safe_print("Settings saved. Exiting.")
        self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = VideoRemixerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()