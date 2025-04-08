import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess # For running ffprobe and ffmpeg
import json       # For saving/loading settings
import random
import math
import shutil     # For removing temporary directory
import time       # For small sleeps if needed

# --- Constants ---
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # 'src' directory
CONFIG_DIR = os.path.join(SCRIPT_DIR, '..', 'config') # Relative path to config
SETTINGS_FILENAME = "video_remixer_settings.json" # Original filename
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, SETTINGS_FILENAME)
TEMP_DIR_NAME = "remixer_temp_snippets" # Keep temp dir relative to script or root? Decide. If root: os.path.join(SCRIPT_DIR, '..', TEMP_DIR_NAME)
TEMP_CONCAT_FILENAME = "_temp_concat.mp4"

# BPM Units for Combobox and Calculation (Based on provided image)
BPM_UNITS = {
    "1/6 Beat": 1.0/6.0,
    "1/4 Beat": 1.0/4.0,
    "1/3 Beat": 1.0/3.0,
    "1/2 Beat": 1.0/2.0,
    "Beat": 1.0,
    "Bar": 4.0 # Assuming 4 beats per bar (common time signature)
}
DEFAULT_BPM_UNIT = "Beat"

# Common Aspect Ratios for Combobox
ASPECT_RATIOS = [
    "Original", # Special value meaning "Keep intermediate resolution"
    "16:9",  # Widescreen TV
    "4:3",   # Standard TV
    "1:1",   # Square (Instagram)
    "9:16",  # Vertical Video (Stories/Reels/TikTok)
    "21:9",  # Ultrawide / Cinemascope (approx)
    "2.35:1",# Cinemascope (more precise)
    "1.85:1" # Widescreen Film
]
DEFAULT_ASPECT_RATIO = "Original"

# --- Customizable Intermediate Format ---
# Using a common resolution helps ensure snippets concatenate smoothly.
# Using .ts (Transport Stream) intermediate format is often more robust for concat.
DEFAULT_INTERMEDIATE_RESOLUTION = "1280:720" # e.g., 720p
DEFAULT_INTERMEDIATE_FPS = "30"
INTERMEDIATE_EXTENSION = ".ts" # Use .ts for better concat reliability

# --- Helper: Aspect Ratio String Parsing ---
def parse_aspect_ratio(ratio_str):
    """Parses 'W:H' string into a float W/H. Returns None if invalid or 'Original'."""
    if ratio_str == "Original":
        return None # Special case indicates no change needed from intermediate
    try:
        # Handle formats like '2.35:1'
        w_str, h_str = ratio_str.split(':')
        w, h = float(w_str), float(h_str)
        if h == 0:
            return None # Avoid division by zero
        return w / h
    except (ValueError, TypeError):
        print(f"Warning: Could not parse aspect ratio string: {ratio_str}")
        return None # Invalid format

# --- Helper: Unique Filename Generation (New) ---
def get_unique_filepath(desired_path):
    """
    Checks if a file path exists. If it does, appends ' (n)' before the
    extension until a unique path is found.
    """
    if not os.path.exists(desired_path):
        return desired_path # Path is already unique

    directory, filename = os.path.split(desired_path)
    base, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{base} ({counter}){ext}"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            print(f"Info: Output file '{filename}' exists. Using '{new_filename}' instead.")
            return new_path
        counter += 1
        if counter > 999: # Safety break to prevent infinite loops
             print(f"Warning: Could not find unique filename for {base} after 999 attempts.")
             # Fallback: append timestamp (less clean but avoids infinite loop)
             timestamp = time.strftime("%Y%m%d%H%M%S")
             new_filename = f"{base}_{timestamp}{ext}"
             new_path = os.path.join(directory, new_filename)
             # Check one last time, though collision is unlikely
             if not os.path.exists(new_path):
                 return new_path
             else: # Extremely unlikely case
                 return desired_path # Give up and return original, likely overwriting


# --- Settings Load/Save ---
def load_settings():
    """Loads settings from the JSON file."""
    default_settings = {
        "last_input_folder": SCRIPT_DIR,
        "output_folder": SCRIPT_DIR,
        "output_filename": "remix_output.mp4",
        "length_mode": "Seconds", # "Seconds" or "BPM"
        "duration_seconds": 15.0, # Use float for seconds
        "bpm": 120.0,             # Use float for bpm
        "bpm_unit": DEFAULT_BPM_UNIT,
        "num_units": 16,           # Use int for units
        "aspect_ratio": DEFAULT_ASPECT_RATIO # New setting
    }
    if os.path.exists(SETTINGS_FILE_PATH):
        try:
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Validate paths and types, falling back to defaults
                for key, default_val in default_settings.items():
                    if key not in settings or not isinstance(settings[key], type(default_val)):
                        settings[key] = default_val
                        print(f"Warning: Setting '{key}' missing or wrong type, using default: {default_val}")

                    # Specific validation logic
                    if key in ["last_input_folder", "output_folder"]:
                        if isinstance(settings[key], str):
                            if not os.path.isdir(settings[key]):
                                print(f"Warning: Saved path '{settings[key]}' for {key} invalid. Using script directory.")
                                settings[key] = SCRIPT_DIR
                        else:
                             print(f"Warning: Saved path for {key} is not a string. Using script directory.")
                             settings[key] = SCRIPT_DIR
                    elif key == "length_mode" and settings[key] not in ["Seconds", "BPM"]:
                         settings[key] = default_settings["length_mode"]
                    elif key == "bpm_unit" and settings[key] not in BPM_UNITS:
                        settings[key] = default_settings["bpm_unit"]
                    elif key == "aspect_ratio" and settings[key] not in ASPECT_RATIOS: # Validate aspect ratio
                        print(f"Warning: Invalid aspect_ratio '{settings[key]}', using default.")
                        settings[key] = default_settings["aspect_ratio"]
                    # Ensure numbers are positive where applicable
                    elif key in ["duration_seconds", "bpm"]:
                         if isinstance(settings[key], (int, float)) and settings[key] <= 0:
                            settings[key] = default_settings[key]
                         elif not isinstance(settings[key], (int, float)):
                             settings[key] = default_settings[key]
                    elif key == "num_units":
                         if isinstance(settings[key], int) and settings[key] <= 0:
                             settings[key] = default_settings[key]
                         elif not isinstance(settings[key], int):
                             settings[key] = default_settings[key]

                return settings
        except (json.JSONDecodeError, IOError, TypeError) as e:
            print(f"Error loading settings file '{SETTINGS_FILE_PATH}': {e}. Using defaults.")
            return default_settings.copy()
    else:
        print(f"Settings file '{SETTINGS_FILENAME}' not found. Using defaults.")
        return default_settings.copy()

def save_settings(settings_dict):
    """Saves settings to the JSON file."""
    try:
        # Basic validation before saving
        for key in ["last_input_folder", "output_folder"]:
             path_to_check = settings_dict.get(key, SCRIPT_DIR)
             if not isinstance(path_to_check, str) or not os.path.isdir(path_to_check):
                 print(f"Warning: Path '{path_to_check}' for {key} doesn't exist or is invalid. Saving setting but it might be invalid.")

        if settings_dict.get("length_mode") not in ["Seconds", "BPM"]:
            settings_dict["length_mode"] = "Seconds"
        if settings_dict.get("bpm_unit") not in BPM_UNITS:
             settings_dict["bpm_unit"] = DEFAULT_BPM_UNIT
        if settings_dict.get("aspect_ratio") not in ASPECT_RATIOS: # Validate aspect ratio
             settings_dict["aspect_ratio"] = DEFAULT_ASPECT_RATIO

        # Ensure numeric types are correct before saving
        try: settings_dict["duration_seconds"] = float(settings_dict.get("duration_seconds", 15.0))
        except (ValueError, TypeError): settings_dict["duration_seconds"] = 15.0
        try: settings_dict["bpm"] = float(settings_dict.get("bpm", 120.0))
        except (ValueError, TypeError): settings_dict["bpm"] = 120.0
        try: settings_dict["num_units"] = int(settings_dict.get("num_units", 16))
        except (ValueError, TypeError): settings_dict["num_units"] = 16

        # Ensure numbers are positive
        if settings_dict["duration_seconds"] <= 0: settings_dict["duration_seconds"] = 15.0
        if settings_dict["bpm"] <= 0: settings_dict["bpm"] = 120.0
        if settings_dict["num_units"] <= 0: settings_dict["num_units"] = 16

        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=4)
    except IOError as e:
        print(f"Error saving settings file '{SETTINGS_FILE_PATH}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred saving settings: {e}")

# --- FFmpeg & FFprobe Check ---
def check_ffmpeg_tools():
    """Checks for ffmpeg and ffprobe in PATH and returns their paths if found."""
    global ffmpeg_path, ffmpeg_found, ffprobe_path, ffprobe_found
    ffmpeg_path, ffmpeg_found = None, False
    ffprobe_path, ffprobe_found = None, False
    cmd_f = "where" if os.name == 'nt' else "which"

    try:
        proc_ffmpeg = subprocess.run([cmd_f, "ffmpeg"], capture_output=True, text=True, check=True, shell=(os.name=='nt'), encoding='utf-8', errors='ignore')
        ffmpeg_path_out = proc_ffmpeg.stdout.strip().split('\n')[0]
        if ffmpeg_path_out and os.path.isfile(ffmpeg_path_out) and os.access(ffmpeg_path_out, os.X_OK):
             ffmpeg_path = ffmpeg_path_out; ffmpeg_found = True
             print(f"INFO: Found FFmpeg at: {ffmpeg_path}")
        else: print(f"WARNING: 'which/where ffmpeg' found '{ffmpeg_path_out}', but it's not a valid executable file.")
    except Exception: print("WARNING: FFmpeg not found in system PATH or error checking.")

    try:
        proc_ffprobe = subprocess.run([cmd_f, "ffprobe"], capture_output=True, text=True, check=True, shell=(os.name=='nt'), encoding='utf-8', errors='ignore')
        ffprobe_path_out = proc_ffprobe.stdout.strip().split('\n')[0]
        if ffprobe_path_out and os.path.isfile(ffprobe_path_out) and os.access(ffprobe_path_out, os.X_OK):
            ffprobe_path = ffprobe_path_out; ffprobe_found = True
            print(f"INFO: Found FFprobe at: {ffprobe_path}")
        else: print(f"WARNING: 'which/where ffprobe' found '{ffprobe_path_out}', but it's not a valid executable file.")
    except Exception: print("WARNING: FFprobe not found in system PATH or error checking.")

    return ffmpeg_found, ffprobe_found

# --- Helper: Get Video Dimensions/Duration ---
def get_video_info(filepath):
    """Uses ffprobe to get width, height, and duration."""
    if not ffprobe_found or not os.path.exists(filepath):
        print(f"Debug: ffprobe not found or path invalid for info check: {filepath}")
        return None, None, None
    command = [
        ffprobe_path if ffprobe_path else "ffprobe",
        "-v", "error",
        "-select_streams", "v:0", # Select video stream 0
        "-show_entries", "stream=width,height:format=duration", # Get W, H, Duration
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        proc = subprocess.run(command, capture_output=True, text=True, check=True,
                              encoding='utf-8', errors='ignore', creationflags=creationflags)
        output_lines = proc.stdout.strip().split('\n')
        # Expected output: width, height, duration (each on new line)
        if len(output_lines) >= 3:
             # Handle potential empty strings or non-numeric values gracefully
            try: width = int(output_lines[0])
            except ValueError: width = None
            try: height = int(output_lines[1])
            except ValueError: height = None
            duration_str = output_lines[2]
            if duration_str.lower() == 'n/a': duration = None
            else:
                try: duration = float(duration_str)
                except ValueError: duration = None
            # Only return if all essential values (W, H, D) are valid
            if width is not None and height is not None and duration is not None:
                return width, height, duration
            else:
                 print(f"Warning: Could not parse all info for '{os.path.basename(filepath)}': W={width}, H={height}, D={duration}")
                 return None, None, None
        else:
            print(f"Warning: Unexpected ffprobe output for '{os.path.basename(filepath)}': {output_lines}")
            return None, None, None # Fallback if output format is wrong

    except subprocess.CalledProcessError as e:
        print(f"Error getting info for '{os.path.basename(filepath)}' (CalledProcessError): {e}")
        if e.stderr: print(f"FFprobe stderr:\n{e.stderr}")
        return None, None, None
    except (ValueError, TypeError) as e:
        # This might catch errors during int/float conversion if output is unexpected
        print(f"Error parsing info for '{os.path.basename(filepath)}': {e} (Output: '{proc.stdout.strip()}')")
        return None, None, None
    except FileNotFoundError:
        print(f"Error: ffprobe command not found while trying to get info.")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error getting info for '{os.path.basename(filepath)}': {e}")
        return None, None, None


# --- Main Application Class ---
class VideoRemixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Snippet Remixer")
        check_ffmpeg_tools()
        self.settings = load_settings()

        # --- GUI Variables ---
        self.input_file_paths = tk.Variable(value=[])
        self.output_folder_var = tk.StringVar(value=self.settings["output_folder"])
        self.output_filename_var = tk.StringVar(value=self.settings["output_filename"])
        self.length_mode_var = tk.StringVar(value=self.settings["length_mode"])
        self.duration_seconds_var = tk.StringVar(value=f"{self.settings['duration_seconds']:.1f}")
        self.bpm_var = tk.StringVar(value=f"{self.settings['bpm']:.1f}")
        self.bpm_unit_var = tk.StringVar(value=self.settings["bpm_unit"])
        self.num_units_var = tk.StringVar(value=str(self.settings["num_units"]))
        self.aspect_ratio_var = tk.StringVar(value=self.settings["aspect_ratio"])
        self.status_var = tk.StringVar(value="Ready")

        # --- Internal state ---
        self.last_input_folder = self.settings["last_input_folder"]
        self.processing_active = False
        self.temp_snippet_dir = os.path.join(SCRIPT_DIR, TEMP_DIR_NAME)

        # --- Bindings ---
        self.length_mode_var.trace_add("write", self.toggle_length_mode_ui)

        # --- Window Setup ---
        self.root.geometry("700x700")
        self.create_widgets()
        self.toggle_length_mode_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if not ffmpeg_found or not ffprobe_found:
            missing = []
            if not ffmpeg_found: missing.append("FFmpeg")
            if not ffprobe_found: missing.append("FFprobe")
            messagebox.showwarning("Dependency Missing",
                                   f"{' and '.join(missing)} not found in PATH.\n\n"
                                   "Please install FFmpeg and add it to your system's PATH.\n"
                                   "Remix generation will fail.")
            self.status_var.set(f"Error: {'/'.join(missing)} not found!")


    def create_widgets(self):
        """Creates and arranges all the GUI elements."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Files Section
        input_frame = ttk.LabelFrame(main_frame, text="Input Videos", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        input_list_frame = ttk.Frame(input_frame)
        input_list_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP, pady=(0, 5))
        self.queue_listbox = tk.Listbox(input_list_frame, listvariable=self.input_file_paths, height=8, selectmode=tk.EXTENDED)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(input_list_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=scrollbar.set)
        input_button_frame = ttk.Frame(input_frame)
        input_button_frame.pack(fill=tk.X)
        browse_button = ttk.Button(input_button_frame, text="Browse Files...", command=self.browse_input_files)
        browse_button.pack(side=tk.LEFT, padx=(0, 5))
        clear_button = ttk.Button(input_button_frame, text="Clear Selected", command=self.clear_selected)
        clear_button.pack(side=tk.LEFT, padx=5)
        clear_all_button = ttk.Button(input_button_frame, text="Clear All", command=self.clear_all)
        clear_all_button.pack(side=tk.LEFT, padx=5)

        # Output Options Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        output_frame.columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_label = ttk.Label(output_frame, textvariable=self.output_folder_var, relief=tk.SUNKEN, anchor=tk.W)
        self.folder_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        browse_output_button = ttk.Button(output_frame, text="Browse...", command=self.browse_output_folder)
        browse_output_button.grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(output_frame, text="Output Filename:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_filename_entry = ttk.Entry(output_frame, textvariable=self.output_filename_var)
        self.output_filename_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(output_frame, text="Aspect Ratio:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.ar_combobox = ttk.Combobox(output_frame, textvariable=self.aspect_ratio_var, values=ASPECT_RATIOS, state="readonly", width=15)
        self.ar_combobox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(output_frame, text="(Crop if wider, Pad if narrower)").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)

        # Length Control Section
        length_frame = ttk.LabelFrame(main_frame, text="Remix Length", padding="10")
        length_frame.pack(fill=tk.X, pady=5)
        mode_frame = ttk.Frame(length_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        self.seconds_radio = ttk.Radiobutton(mode_frame, text="Length in Seconds:", variable=self.length_mode_var, value="Seconds")
        self.seconds_radio.pack(side=tk.LEFT, padx=5)
        self.bpm_radio = ttk.Radiobutton(mode_frame, text="Length by BPM:", variable=self.length_mode_var, value="BPM")
        self.bpm_radio.pack(side=tk.LEFT, padx=20)
        self.seconds_input_frame = ttk.Frame(length_frame)
        ttk.Label(self.seconds_input_frame, text="Total Duration (s):").pack(side=tk.LEFT, padx=5)
        self.seconds_entry = ttk.Entry(self.seconds_input_frame, textvariable=self.duration_seconds_var, width=10)
        self.seconds_entry.pack(side=tk.LEFT, padx=5)
        self.bpm_input_frame = ttk.Frame(length_frame)
        ttk.Label(self.bpm_input_frame, text="BPM:").pack(side=tk.LEFT, padx=5)
        self.bpm_entry = ttk.Entry(self.bpm_input_frame, textvariable=self.bpm_var, width=6)
        self.bpm_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.bpm_input_frame, text="Snippet Unit:").pack(side=tk.LEFT, padx=(15,5))
        self.bpm_unit_combo = ttk.Combobox(self.bpm_input_frame, textvariable=self.bpm_unit_var, values=list(BPM_UNITS.keys()), state="readonly", width=10)
        self.bpm_unit_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.bpm_input_frame, text="Total Units:").pack(side=tk.LEFT, padx=(15, 5))
        self.num_units_entry = ttk.Entry(self.bpm_input_frame, textvariable=self.num_units_var, width=6)
        self.num_units_entry.pack(side=tk.LEFT, padx=5)

        # Process Button
        process_button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        process_button_frame.pack(fill=tk.X)
        self.generate_button = ttk.Button(process_button_frame, text="Generate Remix", command=self.start_processing_thread)
        self.generate_button.pack(pady=10)

        # Status Bar
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0))


    def toggle_length_mode_ui(self, *args):
        """Shows/hides the relevant input fields based on the selected length mode."""
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

    # --- browse_input_files, add_files_to_queue, browse_output_folder ---
    # --- clear_selected, clear_all, update_status, enable_generate_button ---
    # (No changes needed in these helper methods)
    def browse_input_files(self):
        filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv"), ("All files", "*.*")]
        filepaths = filedialog.askopenfilenames(title="Select Input Video Files", initialdir=self.last_input_folder, filetypes=filetypes)
        if filepaths:
            self.last_input_folder = os.path.dirname(filepaths[0])
            self.add_files_to_queue(filepaths)
            self.update_status(f"Added {len(filepaths)} file(s).")

    def add_files_to_queue(self, filepaths):
        current_items = set(self.queue_listbox.get(0, tk.END))
        new_items_count = 0
        for fp in filepaths:
            normalized_fp = os.path.normpath(fp)
            if normalized_fp not in current_items:
                self.queue_listbox.insert(tk.END, normalized_fp)
                current_items.add(normalized_fp)
                new_items_count += 1
        if new_items_count == 0 and filepaths: self.update_status("Selected file(s) already in queue.")

    def browse_output_folder(self):
        folder_selected = filedialog.askdirectory(title="Select Output Folder", initialdir=self.output_folder_var.get())
        if folder_selected: self.output_folder_var.set(folder_selected); self.update_status(f"Output folder set to: {folder_selected}")

    def clear_selected(self):
        selected_indices = self.queue_listbox.curselection()
        if not selected_indices: self.update_status("No items selected to clear."); return
        for i in sorted(selected_indices, reverse=True): self.queue_listbox.delete(i)
        self.update_status("Selected items removed.")

    def clear_all(self):
        if self.queue_listbox.size() > 0: self.queue_listbox.delete(0, tk.END); self.update_status("Queue cleared.")
        else: self.update_status("Queue is already empty.")

    def update_status(self, message):
        try:
            if self.root.winfo_exists(): self.root.after(0, self.status_var.set, message)
        except tk.TclError: print(f"Status update ignored (window closing?): {message}")

    def enable_generate_button(self, enable=True):
         new_state = tk.NORMAL if enable else tk.DISABLED
         try:
             if self.root.winfo_exists(): self.root.after(0, self.generate_button.config, {'state': new_state})
         except tk.TclError: print("Generate button state change ignored (window closing?).")

    def start_processing_thread(self):
        """Validates inputs and launches the video processing in a separate thread."""
        if self.processing_active: messagebox.showwarning("Busy", "Processing is already in progress."); return
        if not ffmpeg_found or not ffprobe_found: messagebox.showerror("Missing Dependency", "Cannot process. FFmpeg/FFprobe not found."); return

        input_files = list(self.queue_listbox.get(0, tk.END))
        if not input_files: messagebox.showwarning("Input Required", "Please add video files to the queue."); return

        output_folder = self.output_folder_var.get()
        output_filename = self.output_filename_var.get()
        if not output_folder or not output_filename: messagebox.showwarning("Output Required", "Select output folder/filename."); return
        if not os.path.isdir(output_folder): messagebox.showerror("Invalid Path", f"Output folder does not exist:\n{output_folder}"); return
        if not output_filename or output_filename.startswith('.'): messagebox.showerror("Invalid Filename", "Enter valid output filename."); return
        # Auto-append .mp4 if needed
        base_name, ext = os.path.splitext(output_filename)
        if not ext.lower() in ['.mp4', '.mov', '.mkv', '.avi', '.webm']:
             output_filename = base_name + ".mp4"
             self.output_filename_var.set(output_filename)
             print(f"Info: Appended '.mp4' to output filename.")
        initial_final_output_path = os.path.join(output_folder, output_filename)

        # --- Get Unique Output Path (New) ---
        actual_final_output_path = get_unique_filepath(initial_final_output_path)
        # If the name changed, update the GUI entry field for user feedback
        if actual_final_output_path != initial_final_output_path:
             self.output_filename_var.set(os.path.basename(actual_final_output_path))

        length_mode = self.length_mode_var.get()
        aspect_ratio_selection = self.aspect_ratio_var.get()
        target_total_duration_sec = 0.0
        snippet_duration_sec = 0.0

        try:
            # Calculate target/snippet durations
            if length_mode == "Seconds":
                target_total_duration_sec = float(self.duration_seconds_var.get())
                if target_total_duration_sec <= 0: raise ValueError("Duration (s) must be positive.")
                snippet_duration_sec = 1.0
                if snippet_duration_sec > target_total_duration_sec: snippet_duration_sec = target_total_duration_sec
                if snippet_duration_sec <= 0: raise ValueError("Snippet duration invalid.")
            elif length_mode == "BPM":
                bpm = float(self.bpm_var.get())
                num_units = int(self.num_units_var.get())
                bpm_unit_name = self.bpm_unit_var.get()
                if bpm <= 0: raise ValueError("BPM must be positive.")
                if num_units <= 0: raise ValueError("Units must be positive.")
                if bpm_unit_name not in BPM_UNITS: raise ValueError("Invalid BPM unit.")
                seconds_per_beat = 60.0 / bpm
                snippet_duration_sec = seconds_per_beat * BPM_UNITS[bpm_unit_name]
                target_total_duration_sec = snippet_duration_sec * num_units
                if snippet_duration_sec <= 0: raise ValueError("Snippet duration invalid.")
            else: raise ValueError("Invalid length mode.")

            if target_total_duration_sec <= 0 or snippet_duration_sec <= 0: raise ValueError("Durations invalid.")
            if aspect_ratio_selection not in ASPECT_RATIOS: raise ValueError("Invalid Aspect Ratio.")

        except ValueError as e: messagebox.showerror("Invalid Input", f"Check length/BPM settings:\n{e}"); return
        except Exception as e: messagebox.showerror("Error", f"Setup error:\n{e}"); return

        # --- Launch Thread ---
        self.processing_active = True
        self.enable_generate_button(False)
        self.update_status("Starting processing...")

        process_thread = threading.Thread(
            target=self.process_queue,
            # Pass the *actual* unique final path to the thread
            args=(input_files, actual_final_output_path, target_total_duration_sec, snippet_duration_sec, aspect_ratio_selection),
            daemon=True
        )
        process_thread.start()


    # --- Core Processing Logic (Runs in Background Thread) ---
    def process_queue(self, input_files, final_output_path, target_total_duration_sec, snippet_duration_sec, aspect_ratio_selection):
        """
        Analyzes videos, selects snippets, cuts, concatenates, and adjusts aspect ratio.
        Writes to the pre-determined unique final_output_path.
        """
        valid_inputs = {}
        files_too_short = []
        # Use a temporary file path within the temp directory for the concatenated output before final AR adjustment/rename
        temp_concat_path = os.path.join(self.temp_snippet_dir, TEMP_CONCAT_FILENAME)

        # --- Stage 1: Analyze Durations ---
        self.update_status("Analyzing input video durations...")
        for i, filepath in enumerate(input_files):
            if (i + 1) % 5 == 0 or i == 0 or i == len(input_files) - 1:
                 self.update_status(f"Analyzing ({i+1}/{len(input_files)}): {os.path.basename(filepath)}")
            _, _, duration = get_video_info(filepath)
            if duration is not None and duration > 0:
                if duration >= snippet_duration_sec: valid_inputs[filepath] = duration
                else: files_too_short.append(os.path.basename(filepath)); print(f"Skipping '{os.path.basename(filepath)}': Duration ({duration:.2f}s) < snippet length ({snippet_duration_sec:.2f}s).")
            else: print(f"Warning: Could not get duration for '{os.path.basename(filepath)}'. Skipping.")

        if files_too_short: self.root.after(0, messagebox.showwarning, "Files Skipped", f"Skipped files (duration < {snippet_duration_sec:.2f}s):\n" + "\n".join(files_too_short))
        if not valid_inputs: self.update_status("Error: No valid input videos found or none are long enough."); self.enable_generate_button(True); self.processing_active = False; return

        # --- Stage 2: Generate Snippet List ---
        self.update_status("Generating random snippet list...")
        num_snippets_needed = math.ceil(target_total_duration_sec / snippet_duration_sec)
        if num_snippets_needed == 0: self.update_status("Error: Snippets needed is zero."); self.enable_generate_button(True); self.processing_active = False; return
        snippet_definitions = []
        available_files = list(valid_inputs.keys())
        print(f"Need {num_snippets_needed} snippets of {snippet_duration_sec:.3f}s each.")
        for _ in range(num_snippets_needed): # Use _ if loop variable i isn't needed
            if not available_files: self.update_status("Error: Not enough source material."); self.enable_generate_button(True); self.processing_active = False; return
            chosen_file = random.choice(available_files)
            max_start_time = max(0, valid_inputs[chosen_file] - snippet_duration_sec)
            random_start = random.uniform(0, max_start_time)
            snippet_definitions.append((chosen_file, random_start, snippet_duration_sec))

        # --- Stage 3: Create Temp Dir & Cut Snippets ---
        if os.path.exists(self.temp_snippet_dir):
            try: shutil.rmtree(self.temp_snippet_dir)
            except OSError as e: print(f"Warning: Could not remove existing temp dir '{self.temp_snippet_dir}': {e}")
        try: os.makedirs(self.temp_snippet_dir, exist_ok=True)
        except OSError as e: self.update_status(f"Error: Could not create temp dir: {e}"); self.enable_generate_button(True); self.processing_active = False; return

        snippet_files = []
        concat_list_path = os.path.join(self.temp_snippet_dir, "mylist.txt")
        processing_failed = False

        try: # Wrap all FFmpeg stages
            for i, (filepath, start, duration) in enumerate(snippet_definitions):
                self.update_status(f"Cutting snippet {i+1}/{num_snippets_needed}...")
                temp_snippet_path = os.path.join(self.temp_snippet_dir, f"snippet_{i:04d}{INTERMEDIATE_EXTENSION}")
                vf_filter = f"fps={DEFAULT_INTERMEDIATE_FPS},scale={DEFAULT_INTERMEDIATE_RESOLUTION}:force_original_aspect_ratio=decrease,pad={DEFAULT_INTERMEDIATE_RESOLUTION}:-1:-1:color=black"
                cut_command = [
                    ffmpeg_path or "ffmpeg", "-hide_banner", "-loglevel", "error",
                    "-i", filepath, "-ss", str(start), "-t", str(duration),
                    "-vf", vf_filter, "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-avoid_negative_ts", "make_zero", "-y",
                    temp_snippet_path
                ]
                try:
                    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    subprocess.run(cut_command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', creationflags=creationflags)
                    snippet_files.append(temp_snippet_path)
                except subprocess.CalledProcessError as e: print(f"Error cutting snippet {i+1}:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}"); self.update_status(f"Error cutting snippet {i+1}. Aborting."); processing_failed = True; break
                except Exception as e: print(f"Unexpected error cutting snippet {i+1}: {e}"); self.update_status(f"Error cutting snippet {i+1}. Aborting."); processing_failed = True; break

            if processing_failed: raise Exception("Snippet cutting failed")
            if not snippet_files: raise Exception("No snippets were successfully cut.")

            # --- Stage 4: Create Concat List File ---
            self.update_status("Preparing concatenation list...")
            try:
                with open(concat_list_path, 'w', encoding='utf-8') as f:
                    for snip_path in snippet_files: safe_path = snip_path.replace("\\", "/").replace("'", "'\\''"); f.write(f"file '{safe_path}'\n")
            except IOError as e: print(f"Error writing concat list file: {e}"); raise Exception("Failed to write concat list file.")

            # --- Stage 5: Concatenate Snippets to Temporary File ---
            self.update_status("Concatenating snippets...")
            concat_command = [
                ffmpeg_path or "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", concat_list_path,
                "-c", "copy", "-y", temp_concat_path
            ]
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.run(concat_command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', creationflags=creationflags)
            except subprocess.CalledProcessError as e: print(f"Error concatenating snippets:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}"); self.update_status("Error during concatenation."); processing_failed = True; raise Exception("Concatenation failed")
            except Exception as e: print(f"Unexpected error during concatenation: {e}"); self.update_status("Error during concatenation."); processing_failed = True; raise Exception("Unexpected concatenation error")

            if processing_failed: raise Exception("Concatenation failed")
            if not os.path.exists(temp_concat_path): raise Exception("Concatenated temp file not found.") # Sanity check

            # --- Stage 6: Aspect Ratio Adjustment ---
            if aspect_ratio_selection == "Original":
                self.update_status("Finalizing (Original Aspect Ratio)...")
                try:
                    # Move directly to the final (unique) path
                    shutil.move(temp_concat_path, final_output_path)
                    self.update_status(f"Remix saved (Original AR): {os.path.basename(final_output_path)}")
                except (IOError, OSError) as e: print(f"Error moving temp concat file: {e}"); self.update_status("Error finalizing file."); processing_failed = True
            else:
                self.update_status(f"Adjusting Aspect Ratio to {aspect_ratio_selection}...")
                width, height, _ = get_video_info(temp_concat_path)
                target_ar_val = parse_aspect_ratio(aspect_ratio_selection)
                ar_filter_vf = None

                if width and height and target_ar_val:
                    source_ar_val = width / height
                    tolerance = 0.01
                    if abs(source_ar_val - target_ar_val) < tolerance:
                        self.update_status("Intermediate matches target AR. Finalizing...")
                        try: shutil.move(temp_concat_path, final_output_path) # Move if AR matches
                        except (IOError, OSError) as e: print(f"Error moving temp concat file: {e}"); self.update_status("Error finalizing file."); processing_failed = True
                    elif source_ar_val > target_ar_val: ar_filter_vf = f"crop=w=ih*{target_ar_val:.4f}:h=ih"; print(f"AR Filter (Crop): {ar_filter_vf}")
                    else: ar_filter_vf = f"pad=w=ih*{target_ar_val:.4f}:h=ih:x=(ow-iw)/2:y=0:color=black"; print(f"AR Filter (Pad): {ar_filter_vf}")

                    if ar_filter_vf and not processing_failed: # Only run if filter needed and no prior errors
                        ar_command = [
                            ffmpeg_path or "ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-i", temp_concat_path, "-vf", ar_filter_vf,
                            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                            "-c:a", "copy", "-y", final_output_path # Output to final path
                        ]
                        try:
                            print(f"Running FFmpeg AR Adjust: {' '.join(ar_command)}")
                            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            subprocess.run(ar_command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', creationflags=creationflags)
                            self.update_status(f"Remix saved ({aspect_ratio_selection}): {os.path.basename(final_output_path)}")
                            try: os.remove(temp_concat_path) # Clean up temp concat file after successful AR adjust
                            except OSError as e: print(f"Warning: Could not remove temp concat file: {e}")
                        except subprocess.CalledProcessError as e: print(f"Error adjusting aspect ratio:\nCMD: {' '.join(e.cmd)}\nStderr:\n{e.stderr}"); self.update_status("Error adjusting aspect ratio."); processing_failed = True
                        except Exception as e: print(f"Unexpected error adjusting aspect ratio: {e}"); self.update_status("Error adjusting aspect ratio."); processing_failed = True
                    elif not processing_failed and not ar_filter_vf: # Case where AR matched, move already happened
                         self.update_status(f"Remix saved (AR matched): {os.path.basename(final_output_path)}")

                else: # Failed to get info or parse AR
                    self.update_status("Error: Cannot adjust AR (invalid info/target). Saving intermediate.")
                    try: shutil.move(temp_concat_path, final_output_path) # Fallback: save intermediate
                    except (IOError, OSError) as e: print(f"Error moving temp concat file: {e}"); self.update_status("Error finalizing file."); processing_failed = True

        except Exception as e: # Catch errors from stages 3-6
             print(f"Processing stopped due to error: {e}")
             # Status likely updated by the stage that failed

        finally:
            # --- Stage 7: Cleanup ---
            status_before_cleanup = self.status_var.get().split('|')[0].strip()
            self.update_status(status_before_cleanup + " | Cleaning up...")
            if os.path.exists(self.temp_snippet_dir):
                try:
                    shutil.rmtree(self.temp_snippet_dir)
                    print(f"Successfully removed temporary directory: {self.temp_snippet_dir}")
                    self.update_status(status_before_cleanup + " | Cleanup done.")
                except OSError as e:
                    print(f"Error removing temporary directory '{self.temp_snippet_dir}': {e}")
                    self.update_status(status_before_cleanup + " | Cleanup failed.")
            else:
                 self.update_status(status_before_cleanup + " | No temp files to clean.")

            self.enable_generate_button(True)
            self.processing_active = False


    def on_closing(self):
        """Handles window closing: saves settings, prompts if processing."""
        if self.processing_active:
            if not messagebox.askokcancel("Quit", "Processing is active. Quitting now may leave temporary files.\nAre you sure you want to quit?"):
                return

        # Save current settings
        self.settings["last_input_folder"] = self.last_input_folder
        self.settings["output_folder"] = self.output_folder_var.get()
        self.settings["output_filename"] = self.output_filename_var.get()
        self.settings["length_mode"] = self.length_mode_var.get()
        self.settings["aspect_ratio"] = self.aspect_ratio_var.get()
        try: self.settings["duration_seconds"] = float(self.duration_seconds_var.get())
        except ValueError: print("Warning: Invalid duration value not saved.")
        try: self.settings["bpm"] = float(self.bpm_var.get())
        except ValueError: print("Warning: Invalid BPM value not saved.")
        self.settings["bpm_unit"] = self.bpm_unit_var.get()
        try: self.settings["num_units"] = int(self.num_units_var.get())
        except ValueError: print("Warning: Invalid units value not saved.")

        save_settings(self.settings)
        print("Settings saved. Exiting.")
        self.root.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoRemixerApp(root)
    root.mainloop()
