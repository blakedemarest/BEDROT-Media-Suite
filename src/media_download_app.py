import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess # For running yt-dlp, ffmpeg, ffprobe
import json      # For parsing yt-dlp progress AND saving settings
import re        # For parsing time strings
import math      # For aspect ratio comparison tolerance and chopping duration

# --- Define Settings File Path ---
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is now the 'src' directory
CONFIG_DIR = os.path.join(SCRIPT_DIR, '..', 'config') # Go up to root, then into 'config'
SETTINGS_FILENAME = "yt_downloader_gui_settings.json" # Original filename
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, SETTINGS_FILENAME)

# --- Common Aspect Ratios ---
ASPECT_RATIOS = [
    "Original", "16:9", "4:3", "1:1", "9:16", "21:9", "2.35:1", "1.85:1"
]

# --- Helper: Time String Parsing ---
def parse_time_to_seconds(time_str):
    # (No changes needed)
    if not time_str:
        return None
    time_str = time_str.strip()
    parts = re.split(r'[: ]+', time_str) # Allow space as separator too
    try:
        if len(parts) == 3: # HH:MM:SS.ms
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2: # MM:SS.ms
            m, s = map(float, parts)
            return m * 60 + s
        elif len(parts) == 1: # SS.ms
            return float(parts[0])
        else:
            return None
    except ValueError:
        return None

# --- Helper: Aspect Ratio String Parsing ---
def parse_aspect_ratio(ratio_str):
    # (No changes needed)
    if ratio_str == "Original":
        return None
    try:
        w_str, h_str = ratio_str.split(':')
        w, h = float(w_str), float(h_str)
        if h == 0: return None
        return w / h
    except ValueError:
        return None

# --- Settings Load/Save Functions (Modified) ---
def load_settings():
    """Loads settings from the JSON file."""
    default_settings = {
        "download_path": SCRIPT_DIR,
        "video_only": False,
        "enable_cut": False,
        "start_time": "",
        "end_time": "",
        "aspect_ratio": "Original",
        "enable_chop": False,        # NEW Setting
        "chop_interval": "60"        # NEW Setting (default 60 seconds)
    }
    if os.path.exists(SETTINGS_FILE_PATH):
        try:
            with open(SETTINGS_FILE_PATH, 'r') as f:
                settings = json.load(f)
                loaded_path = settings.get("download_path", default_settings["download_path"])
                # Robust path check
                if not isinstance(loaded_path, str) or not os.path.isdir(loaded_path):
                     if isinstance(loaded_path, str): print(f"Warning: Saved path '{loaded_path}' invalid. Using script directory.")
                     else: print(f"Warning: Saved path type invalid. Using script directory.")
                     settings["download_path"] = default_settings["download_path"]

                # Ensure all keys exist with correct types or defaults
                for key, default_val in default_settings.items():
                    if key not in settings or type(settings[key]) != type(default_val):
                        print(f"Warning: Setting '{key}' missing or invalid type. Using default: {default_val}")
                        settings[key] = default_val
                    # Specific check for aspect ratio validity
                    if key == "aspect_ratio" and settings[key] not in ASPECT_RATIOS:
                         print(f"Warning: Saved aspect ratio '{settings[key]}' invalid. Using default.")
                         settings[key] = default_settings["aspect_ratio"]
                    # Specific check for chop_interval validity (should be numeric string)
                    if key == "chop_interval":
                        try:
                            interval_val = float(settings[key])
                            if interval_val <= 0:
                                print(f"Warning: Saved chop interval '{settings[key]}' must be positive. Using default.")
                                settings[key] = default_settings[key]
                        except (ValueError, TypeError):
                            print(f"Warning: Saved chop interval '{settings[key]}' invalid. Using default.")
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
        path_to_save = settings_dict.get("download_path", SCRIPT_DIR)
        if isinstance(path_to_save, str) and not os.path.isdir(path_to_save):
            print(f"Warning: Path '{path_to_save}' doesn't exist. Saving setting but it might be invalid.")
        elif not isinstance(path_to_save, str):
             print(f"Warning: Invalid type for download path. Saving default.")
             settings_dict["download_path"] = SCRIPT_DIR

        if settings_dict.get("aspect_ratio") not in ASPECT_RATIOS:
            print(f"Warning: Invalid aspect ratio '{settings_dict.get('aspect_ratio')}' detected. Resetting.")
            settings_dict["aspect_ratio"] = "Original"

        # Validate chop interval before saving
        try:
            chop_interval_str = settings_dict.get("chop_interval", "60")
            interval = float(chop_interval_str)
            if interval <= 0:
                print(f"Warning: Invalid chop interval '{chop_interval_str}' <= 0 detected. Resetting to default.")
                settings_dict["chop_interval"] = "60"
        except (ValueError, TypeError):
            print(f"Warning: Invalid chop interval '{chop_interval_str}' detected. Resetting to default.")
            settings_dict["chop_interval"] = "60"


        with open(SETTINGS_FILE_PATH, 'w') as f:
            json.dump(settings_dict, f, indent=4)
    except IOError as e:
        print(f"Error saving settings file '{SETTINGS_FILE_PATH}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred saving settings: {e}")


# --- FFmpeg & FFprobe Check ---
ffmpeg_path = None
ffmpeg_found = False
ffprobe_path = None
ffprobe_found = False

try:
    cmd_f = "where" if os.name == 'nt' else "which"
    # Check FFmpeg
    proc_ffmpeg = subprocess.run([cmd_f, "ffmpeg"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
    ffmpeg_path_out = proc_ffmpeg.stdout.strip().split('\n')[0]
    if ffmpeg_path_out:
         ffmpeg_path = ffmpeg_path_out
         ffmpeg_found = True
         print(f"INFO: Found FFmpeg at: {ffmpeg_path}")
    # Check FFprobe
    proc_ffprobe = subprocess.run([cmd_f, "ffprobe"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
    ffprobe_path_out = proc_ffprobe.stdout.strip().split('\n')[0]
    if ffprobe_path_out:
         ffprobe_path = ffprobe_path_out
         ffprobe_found = True
         print(f"INFO: Found FFprobe at: {ffprobe_path}")

except (subprocess.CalledProcessError, FileNotFoundError) as e:
    tool_name = "FFmpeg" if "ffmpeg" in str(e) or not ffmpeg_found else "FFprobe"
    print(f"WARNING: {tool_name} not found in system PATH.")
    if tool_name == "FFmpeg":
        print("         Time range cutting, MP3 conversion, aspect ratio changes, audio removal, video chopping, and best quality MP4 require FFmpeg.")
        ffmpeg_found = False
    if tool_name == "FFprobe":
        print("         Aspect ratio adjustment and video chopping require FFprobe to get video dimensions/duration.")
        ffprobe_found = False
    # Re-check the other tool if the first one failed
    if tool_name == "FFmpeg" and not ffprobe_found:
        try:
            subprocess.run([cmd_f, "ffprobe"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
            ffprobe_found = True # Found it after all
        except:
            print("WARNING: FFprobe also not found in system PATH.")
            print("         Aspect ratio adjustment and video chopping require FFprobe.")
            ffprobe_found = False
    elif tool_name == "FFprobe" and not ffmpeg_found:
         try:
            subprocess.run([cmd_f, "ffmpeg"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
            ffmpeg_found = True
         except:
            print("WARNING: FFmpeg also not found in system PATH.")
            print("         Multiple features require FFmpeg.")
            ffmpeg_found = False


# --- Helper: Get Video Dimensions ---
def get_video_dimensions(filepath):
    # (No changes needed)
    if not ffprobe_found or not os.path.exists(filepath):
        return None, None
    command = [ ffprobe_path if ffprobe_path else "ffprobe", "-v", "error",
                "-select_streams", "v:0", "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0", filepath ]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=True,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        output = proc.stdout.strip()
        if 'x' in output:
            width_str, height_str = output.split('x')
            return int(width_str), int(height_str)
        else:
            print(f"Warning: Could not parse ffprobe dimension output: {output}")
            return None, None
    except Exception as e:
        print(f"Error getting dimensions for '{filepath}': {e}")
        return None, None

# --- Helper: Get Video Duration ---
def get_video_duration(filepath):
    """Uses ffprobe to get the duration of a media file in seconds."""
    if not ffprobe_found or not os.path.exists(filepath):
        return None

    command = [
        ffprobe_path if ffprobe_path else "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=True,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        duration_str = proc.stdout.strip()
        return float(duration_str)
    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe for duration '{filepath}': {e}")
        print(f"FFprobe duration stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print(f"Error: ffprobe command not found during duration check.")
        return None
    except ValueError:
        print(f"Error: Could not parse duration '{duration_str}' as float for '{filepath}'.")
        return None
    except Exception as e:
        print(f"Unexpected error getting duration for '{filepath}': {e}")
        return None


# --- Main Application Class ---
class MediaDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Downloader (yt-dlp)")

        self.settings = load_settings()
        initial_path = self.settings.get("download_path", SCRIPT_DIR)

        self.download_queue = []
        self.download_path = tk.StringVar(value=initial_path)
        self.download_format = tk.StringVar(value="mp4") # Default to mp4

        # Option Variables
        self.video_only_var = tk.BooleanVar(value=self.settings.get("video_only", False))
        self.enable_cut_var = tk.BooleanVar(value=self.settings.get("enable_cut", False))
        self.start_time_var = tk.StringVar(value=self.settings.get("start_time", ""))
        self.end_time_var = tk.StringVar(value=self.settings.get("end_time", ""))
        self.aspect_ratio_var = tk.StringVar(value=self.settings.get("aspect_ratio", "Original"))
        self.enable_chop_var = tk.BooleanVar(value=self.settings.get("enable_chop", False)) # NEW
        self.chop_interval_var = tk.StringVar(value=self.settings.get("chop_interval", "60")) # NEW

        # Traces for enabling/disabling related fields
        self.enable_cut_var.trace_add("write", self.toggle_time_entries)
        self.enable_chop_var.trace_add("write", self.toggle_chop_entry) # NEW Trace
        self.download_format.trace_add("write", self.toggle_video_only_option)

        self.root.geometry("600x750") # Increased height for chopping option
        self.create_widgets()
        self.toggle_time_entries() # Initial state sync
        self.toggle_chop_entry() # NEW Initial state sync
        self.toggle_video_only_option() # Initial state sync

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- Input & Folder Frames (remain the same) ---
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        ttk.Label(input_frame, text="Video URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        input_frame.columnconfigure(1, weight=1)
        add_button = ttk.Button(input_frame, text="Add to Queue", command=self.add_to_queue)
        add_button.grid(row=0, column=2, padx=5, pady=5)

        folder_frame = ttk.Frame(self.root, padding="10")
        folder_frame.pack(fill=tk.X)
        ttk.Label(folder_frame, text="Download Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_label = ttk.Label(folder_frame, textvariable=self.download_path, relief=tk.SUNKEN, padding=2)
        self.folder_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        folder_frame.columnconfigure(1, weight=1)
        browse_button = ttk.Button(folder_frame, text="Browse...", command=self.choose_folder)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        # --- *** Options Frame (Container for Format, Cut, AR, Chop) *** ---
        options_outer_frame = ttk.Frame(self.root, padding="10")
        options_outer_frame.pack(fill=tk.X)

        # -- Column 1: Format & MP4 Options --
        format_column = ttk.Frame(options_outer_frame)
        format_column.pack(side=tk.LEFT, padx=5, pady=5, anchor='nw', fill=tk.Y)

        format_frame = ttk.LabelFrame(format_column, text="Format", padding="5")
        format_frame.pack(fill=tk.X)
        mp4_radio = ttk.Radiobutton(format_frame, text="MP4", variable=self.download_format, value="mp4")
        mp4_radio.pack(anchor=tk.W)
        mp3_radio = ttk.Radiobutton(format_frame, text="MP3 (Audio Only)", variable=self.download_format, value="mp3")
        mp3_radio.pack(anchor=tk.W)
        self.video_only_check = ttk.Checkbutton(format_frame, text="Video Only (No Audio)", variable=self.video_only_var)
        self.video_only_check.pack(anchor=tk.W, padx=(15, 0))

        # -- Column 2: Processing (Cutting, Aspect Ratio, Chopping) --
        processing_column = ttk.Frame(options_outer_frame)
        processing_column.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True, anchor='nw')

        # -- Cutting Options --
        cut_frame = ttk.LabelFrame(processing_column, text="Time Range Cut (Requires FFmpeg)", padding="5")
        cut_frame.pack(fill=tk.X, pady=(0, 5))
        enable_cut_check = ttk.Checkbutton(cut_frame, text="Cut to Selected Time Range", variable=self.enable_cut_var)
        enable_cut_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        ttk.Label(cut_frame, text="Start:").grid(row=1, column=0, sticky=tk.W)
        self.start_time_entry = ttk.Entry(cut_frame, textvariable=self.start_time_var, width=12)
        self.start_time_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        ttk.Label(cut_frame, text="End:").grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        self.end_time_entry = ttk.Entry(cut_frame, textvariable=self.end_time_var, width=12)
        self.end_time_entry.grid(row=1, column=3, padx=5, sticky=tk.W)
        time_format_label = ttk.Label(cut_frame, text="(HH:MM:SS or MM:SS or SS)")
        time_format_label.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(5,0))

        # --- Aspect Ratio Frame ---
        ar_frame = ttk.LabelFrame(processing_column, text="Aspect Ratio (Requires FFmpeg/FFprobe)", padding="5")
        ar_frame.pack(fill=tk.X, pady=(5, 5)) # Add padding below
        ttk.Label(ar_frame, text="Adjust to:").pack(side=tk.LEFT, padx=(0, 5))
        self.ar_combobox = ttk.Combobox(ar_frame, textvariable=self.aspect_ratio_var, values=ASPECT_RATIOS, state="readonly", width=15)
        self.ar_combobox.pack(side=tk.LEFT)
        ttk.Label(ar_frame, text="(Crop/Pad)").pack(side=tk.LEFT, padx=(10, 0))

        # --- *** NEW: Chopping Frame *** ---
        chop_frame = ttk.LabelFrame(processing_column, text="Chop into Intervals (Requires FFmpeg/FFprobe)", padding="5")
        chop_frame.pack(fill=tk.X, pady=(5, 0))

        enable_chop_check = ttk.Checkbutton(chop_frame, text="Chop output into segments of:", variable=self.enable_chop_var)
        enable_chop_check.grid(row=0, column=0, sticky=tk.W)

        self.chop_interval_entry = ttk.Entry(chop_frame, textvariable=self.chop_interval_var, width=8)
        self.chop_interval_entry.grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(chop_frame, text="seconds").grid(row=0, column=2, sticky=tk.W)


        # --- Queue Frame ---
        queue_frame = ttk.LabelFrame(self.root, text="Download Queue", padding="10")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5,0))
        self.queue_listbox = tk.Listbox(queue_frame, height=6)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=scrollbar.set)

        # --- Action Buttons Frame ---
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)
        self.download_button = ttk.Button(action_frame, text="Download Queue", command=self.start_download_thread)
        self.download_button.pack(side=tk.LEFT, padx=5)
        clear_button = ttk.Button(action_frame, text="Clear Selected", command=self.clear_selected)
        clear_button.pack(side=tk.LEFT, padx=5)
        clear_all_button = ttk.Button(action_frame, text="Clear All", command=self.clear_all)
        clear_all_button.pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready (using yt-dlp)")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Toggle Control States ---
    def toggle_time_entries(self, *args):
        # (No changes needed)
        state = tk.NORMAL if self.enable_cut_var.get() else tk.DISABLED
        try:
            if self.start_time_entry.winfo_exists() and self.end_time_entry.winfo_exists():
                self.start_time_entry.config(state=state)
                self.end_time_entry.config(state=state)
        except tk.TclError: pass # Widget might not exist yet

    def toggle_video_only_option(self, *args):
         # (No changes needed)
         try:
              if self.video_only_check.winfo_exists():
                    state = tk.NORMAL if self.download_format.get() == "mp4" else tk.DISABLED
                    self.video_only_check.config(state=state)
                    if state == tk.DISABLED: self.video_only_var.set(False)
         except tk.TclError: pass

    # --- *** NEW: Toggle Chop Interval Entry *** ---
    def toggle_chop_entry(self, *args):
         state = tk.NORMAL if self.enable_chop_var.get() else tk.DISABLED
         try:
             if self.chop_interval_entry.winfo_exists():
                 self.chop_interval_entry.config(state=state)
         except tk.TclError: pass # Widget might not exist yet


    # --- GUI actions (add_to_queue, choose_folder, clear_*, etc.) ---
    # (No changes needed in add_to_queue, choose_folder, clear_selected, clear_all, update_status)
    def add_to_queue(self):
        url = self.url_entry.get().strip()
        if url:
            if not (url.startswith("http://") or url.startswith("https://")):
                 self.update_status("Please enter a valid URL (starting with http:// or https://).")
                 return
            current_items = self.queue_listbox.get(0, tk.END)
            if url not in current_items:
                 self.download_queue.append(url) # Not strictly necessary if rebuilt before download, but keep for consistency
                 self.queue_listbox.insert(tk.END, url)
                 self.url_entry.delete(0, tk.END)
                 self.update_status(f"Added: {url}")
            else:
                 self.update_status("URL already in queue.")
        else:
            self.update_status("Please enter a Video URL.")

    def choose_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder_selected:
            self.download_path.set(folder_selected)
            self.update_status(f"Download folder: {folder_selected}")
            self.settings["download_path"] = folder_selected
            save_settings(self.settings)

    def clear_selected(self):
        selected_indices = self.queue_listbox.curselection()
        if not selected_indices:
            self.update_status("No item selected.")
            return
        for i in sorted(selected_indices, reverse=True):
            self.queue_listbox.delete(i)
        # Update internal queue to match listbox
        self.download_queue = list(self.queue_listbox.get(0, tk.END))
        self.update_status("Selected items removed.")

    def clear_all(self):
        self.queue_listbox.delete(0, tk.END)
        self.download_queue.clear()
        self.update_status("Queue cleared.")

    def update_status(self, message):
        try:
            if self.root.winfo_exists():
                 self.root.after(0, self.status_var.set, message)
        except tk.TclError: pass

    # --- *** MODIFIED Download Start & Pre-checks *** ---
    def start_download_thread(self):
        self.download_queue = list(self.queue_listbox.get(0, tk.END)) # Refresh internal queue

        if not self.download_queue:
            messagebox.showwarning("Queue Empty", "Add URLs to the queue first.")
            return

        # --- Pre-checks ---
        try: # yt-dlp check
             cmd = "where" if os.name == 'nt' else "which"
             subprocess.run([cmd, "yt-dlp"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
        except (subprocess.CalledProcessError, FileNotFoundError):
             messagebox.showerror("yt-dlp Error", "yt-dlp command not found in PATH.")
             return

        if not os.path.isdir(self.download_path.get()):
             messagebox.showerror("Invalid Path", f"Download folder is invalid:\n{self.download_path.get()}")
             return

        # --- Specific FFmpeg/FFprobe checks based on selected options ---
        is_tiktok_video_only = False
        if self.download_format.get() == "mp4" and self.video_only_var.get():
            if any("tiktok.com" in url for url in self.download_queue):
                is_tiktok_video_only = True

        needs_ffmpeg = (self.enable_cut_var.get() or
                        self.aspect_ratio_var.get() != "Original" or
                        self.download_format.get() == "mp3" or
                        is_tiktok_video_only or # Audio removal for TikTok requires FFmpeg
                        self.enable_chop_var.get()) # Chopping requires FFmpeg

        needs_ffprobe = (self.aspect_ratio_var.get() != "Original" or # AR needs dimensions
                         self.enable_chop_var.get()) # Chopping needs duration

        if needs_ffmpeg and not ffmpeg_found:
             messagebox.showerror("FFmpeg Error", "The selected options (Cutting, Aspect Ratio, MP3, TikTok Video-Only, Chopping) require FFmpeg, but it was not found in your PATH.")
             return
        if needs_ffprobe and not ffprobe_found:
             messagebox.showerror("FFprobe Error", "Aspect ratio adjustment or Chopping requires FFprobe, but it was not found in your PATH.")
             return

        # --- Validate Times and Intervals ---
        start_sec, end_sec = None, None
        if self.enable_cut_var.get():
            start_str = self.start_time_var.get()
            end_str = self.end_time_var.get()
            start_sec = parse_time_to_seconds(start_str)
            end_sec = parse_time_to_seconds(end_str)
            if start_sec is None: messagebox.showerror("Invalid Time", f"Invalid Start Time: '{start_str}'"); return
            if end_sec is None: messagebox.showerror("Invalid Time", f"Invalid End Time: '{end_str}'"); return
            if start_sec < 0 or end_sec <= 0: messagebox.showerror("Invalid Time", "Times must be positive."); return
            if start_sec >= end_sec: messagebox.showerror("Invalid Time", "Start Time must be less than End Time."); return

        chop_interval_sec = None
        if self.enable_chop_var.get():
            try:
                chop_interval_sec = float(self.chop_interval_var.get())
                if chop_interval_sec <= 0:
                    messagebox.showerror("Invalid Interval", "Chop interval must be a positive number of seconds.")
                    return
            except ValueError:
                messagebox.showerror("Invalid Interval", f"Invalid Chop Interval: '{self.chop_interval_var.get()}'. Must be numeric.")
                return

        # Validate selected aspect ratio format (redundant due to Combobox, but safe)
        selected_ar = self.aspect_ratio_var.get()
        if selected_ar != "Original" and parse_aspect_ratio(selected_ar) is None:
            messagebox.showerror("Invalid Aspect Ratio", f"Selected aspect ratio '{selected_ar}' is invalid.")
            return

        # --- Start Download ---
        self.download_button.config(state=tk.DISABLED)
        self.update_status("Starting download...")
        queue_copy = list(self.download_queue)
        time_range = (start_sec, end_sec) if self.enable_cut_var.get() else None
        aspect_ratio_selection = self.aspect_ratio_var.get()
        video_only_state = self.video_only_var.get()
        selected_format_state = self.download_format.get()
        chop_settings = (self.enable_chop_var.get(), chop_interval_sec) # Pass chop settings

        download_thread = threading.Thread(
            target=self.process_queue_sequential,
            args=(queue_copy, time_range, aspect_ratio_selection,
                  video_only_state, selected_format_state, chop_settings), # Pass chop settings
            daemon=True)
        download_thread.start()


    # --- *** MODIFIED SEQUENTIAL PROCESSING LOGIC *** ---
    def process_queue_sequential(self, queue_to_process, time_range, aspect_ratio_selection,
                                 video_only_setting, selected_format_setting, chop_settings): # Receive chop settings
        """
        Processes queue item by item: Download -> Remove Audio -> Adjust AR -> Cut -> Chop -> Finalize.
        Manages intermediate files.
        """
        path = self.download_path.get()
        selected_format = selected_format_setting
        is_video_only = video_only_setting if selected_format == "mp4" else False
        is_cutting = time_range is not None
        is_adjusting_ar = aspect_ratio_selection != "Original"
        is_chopping, chop_interval_seconds = chop_settings # Unpack chop settings

        initial_queue_size = len(queue_to_process)
        processed_count = 0

        for url in queue_to_process:
            processed_count += 1
            progress_prefix = f"[{processed_count}/{initial_queue_size}]"
            self.update_status(f"{progress_prefix} Starting: {url}")

            # --- Stage 0: Determine Filenames & Tags ---
            base_title = None
            initial_download_path = None
            final_extension = ".mp3" if selected_format == "mp3" else ".mp4"

            # Determine tags for intermediate and final files (excluding chop part number)
            is_tiktok_url = "tiktok.com" in url
            tiktok_video_only_special_case = is_tiktok_url and selected_format == "mp4" and is_video_only
            no_audio_tag = "_NoAudio" if tiktok_video_only_special_case else ""
            ar_tag = ""
            time_tag = ""
            if is_adjusting_ar:
                ar_tag = f"_AR_{aspect_ratio_selection.replace(':', 'x').replace('.', '_')}"
            if is_cutting:
                start_sec, end_sec = time_range
                # Use integer seconds for simpler filenames unless sub-second precision needed
                time_tag = f"_{int(start_sec)}s-{int(end_sec)}s"

            # Base path template for *intermediate* file before potential chopping
            # Or the final path if not chopping
            intermediate_output_base = f"PLACEHOLDER{no_audio_tag}{ar_tag}{time_tag}"


            # --- Stage 1: Download with yt-dlp ---
            self.update_status(f"{progress_prefix} Downloading...")
            yt_dlp_success = False
            stderr_info = ""
            needs_audio_removal = False # Flag for post-processing if TikTok+VideoOnly
            # Ensure temp file has the expected *final* extension for compatibility
            temp_output_template = os.path.join(path, f"%(title)s_TEMP_DOWNLOAD{final_extension}")

            command = [
                "yt-dlp", url, "--no-playlist", "--progress",
                "--progress-template", "download-status:%(progress)j",
                "--no-warnings",
                #"--verbose",
                "-o", temp_output_template,
                "--ffmpeg-location", ffmpeg_path if ffmpeg_path else "ffmpeg"
            ]

            # --- Determine yt-dlp Format Flags ---
            if tiktok_video_only_special_case:
                command.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4"])
                needs_audio_removal = True
                print(f"INFO: ({os.path.basename(url[:50])}...): TikTok+VideoOnly. Downloading with audio first.")
            elif selected_format == "mp3":
                 command.extend(["-x", "--audio-format", "mp3", "-f", "bestaudio/best"])
            else: # Standard MP4
                 if is_video_only: command.extend(["-f", "bestvideo[ext=mp4]/bestvideo", "--recode-video", "mp4"])
                 else: command.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4"])

            # --- Execute yt-dlp and Parse Output ---
            try:
                process = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            text=True, encoding='utf-8', errors='replace', bufsize=1,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 )
                current_status_msg = f"{progress_prefix} Downloading..."
                self.update_status(current_status_msg)

                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if not line: continue
                        if line.startswith("download-status:"):
                             try:
                                 json_str = line.split(":", 1)[1]
                                 progress_data = json.loads(json_str)
                                 status = progress_data.get('status', 'N/A')
                                 dl_filename_progress = progress_data.get('filename')

                                 if status == 'finished' and dl_filename_progress and not initial_download_path:
                                     initial_download_path = dl_filename_progress # Capture actual path
                                     temp_base, _ = os.path.splitext(os.path.basename(initial_download_path))
                                     temp_suffix = f"_TEMP_DOWNLOAD"
                                     if temp_base.endswith(temp_suffix): base_title = temp_base[:-len(temp_suffix)]
                                     else: base_title = temp_base # Fallback
                                     print(f"DEBUG: Captured initial_download_path='{initial_download_path}', base_title='{base_title}'")

                                 percent_str = progress_data.get('_percent_str', 'N/A')
                                 eta_str = progress_data.get('_eta_str', 'N/A')
                                 speed_str = progress_data.get('_speed_str', 'N/A')
                                 display_filename = os.path.basename(dl_filename_progress or 'N/A')
                                 short_filename = display_filename[:30] + "..." if len(display_filename) > 33 else display_filename

                                 if status == 'downloading': current_status_msg = f"{progress_prefix} DL '{short_filename}': {percent_str} ({speed_str}, ETA: {eta_str})"
                                 elif status == 'finished': current_status_msg = f"{progress_prefix} Finished DL '{short_filename}', processing..."
                                 elif status == 'error': current_status_msg = f"{progress_prefix} Error DL: {display_filename}"
                                 else: current_status_msg = f"{progress_prefix} Status '{status}': {short_filename}"
                                 self.update_status(current_status_msg)
                             except json.JSONDecodeError: pass # Ignore non-JSON progress lines
                             except Exception as e: print(f"Error parsing progress line: {line} | Error: {e}")
                        #else: print(f"yt-dlp stdout: {line}") # Debug other output

                process.stdout.close() if process.stdout else None
                return_code = process.wait()
                stderr_output = process.stderr.read() if process.stderr else ""
                process.stderr.close() if process.stderr else None
                stderr_info = stderr_output

                # --- Check download result ---
                if return_code == 0 and initial_download_path and os.path.exists(initial_download_path):
                    yt_dlp_success = True
                    self.update_status(f"{progress_prefix} Download successful.")
                    if not base_title: # Fallback title capture
                         base_title, _ = os.path.splitext(os.path.basename(initial_download_path))
                         temp_suffix = f"_TEMP_DOWNLOAD"; base_title = base_title.replace(temp_suffix, "")
                         print(f"DEBUG: Fallback capture base_title='{base_title}'")
                else:
                    yt_dlp_success = False
                    error_lines = stderr_info.strip().split('\n')
                    specific_error = f"yt-dlp failed (code {return_code})"
                    for err_line in reversed(error_lines):
                        if err_line.strip().startswith("ERROR:"): specific_error = err_line.strip()[6:].strip(); break
                    final_msg = f"{progress_prefix} Download Failed: {specific_error}"
                    print(f"yt-dlp Error Log ({url}):\n{stderr_info}")
                    self.update_status(final_msg)
                    # --- FIX: Use indented try/except for cleanup ---
                    # Cleanup potentially incomplete temp file
                    if initial_download_path and os.path.exists(initial_download_path):
                        try:
                            os.remove(initial_download_path)
                            print(f"Cleaned up failed download: {initial_download_path}")
                        except OSError as e:
                            print(f"Warning: Could not delete failed download temp file: {e}")
                    elif not initial_download_path: # Try pattern if path wasn't captured
                         potential_temps = [f for f in os.listdir(path) if f.endswith(f"_TEMP_DOWNLOAD{final_extension}")]
                         for temp_f in potential_temps:
                             try:
                                 os.remove(os.path.join(path, temp_f))
                                 print(f"Cleaned likely failed temp: {temp_f}")
                             except OSError as e:
                                 print(f"Warning: Could not delete likely failed temp: {e}")
                    continue # Move to next URL

            except FileNotFoundError: self.update_status(f"{progress_prefix} Error: yt-dlp command not found!"); self.root.after(0, self.enable_download_button); return
            except Exception as e: self.update_status(f"{progress_prefix} Download Error: {e}"); yt_dlp_success = False; continue

            # --- Proceed only if download succeeded ---
            if not yt_dlp_success or not initial_download_path or not base_title:
                self.update_status(f"{progress_prefix} Skipping post-processing due to download issue.")
                # --- FIX: Use indented try/except for cleanup ---
                if initial_download_path and os.path.exists(initial_download_path):
                    try:
                        os.remove(initial_download_path)
                    except OSError:
                        pass # Ignore cleanup error here
                continue

            # --- Post-Download Processing ---
            current_file_path = initial_download_path
            processing_error = False
            re_encoding_occurred = False # Track if any step forces re-encoding

            # Update the intermediate base path now that we have the real title
            intermediate_output_base = f"{base_title}{no_audio_tag}{ar_tag}{time_tag}"
            intermediate_output_path = os.path.join(path, f"{intermediate_output_base}{final_extension}")
            print(f"DEBUG: Intermediate Output Base planned: {intermediate_output_base}")


            # --- Stage 1.5: Remove Audio (if TikTok Video-Only case) ---
            if needs_audio_removal and not processing_error:
                 self.update_status(f"{progress_prefix} Removing audio track...")
                 output_noaudio_path = current_file_path.replace("_TEMP_DOWNLOAD", "_TEMP_NOAUDIO")
                 ffmpeg_an_command = [ ffmpeg_path if ffmpeg_path else "ffmpeg", "-hide_banner", "-loglevel", "error",
                                       "-i", current_file_path, "-c:v", "copy", "-an", "-map", "0:v:0?", output_noaudio_path ]
                 try:
                     print(f"Running FFmpeg Remove Audio: {' '.join(ffmpeg_an_command)}")
                     an_proc = subprocess.run(ffmpeg_an_command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                     print(f"FFmpeg Remove Audio Output:\n{an_proc.stderr}")
                     self.update_status(f"{progress_prefix} Audio removal successful.")
                     try: # Keep this simple try/except for removing the previous temp file
                         print(f"DEBUG: Removing '{current_file_path}' after audio removal."); os.remove(current_file_path)
                     except OSError as e: print(f"Warning: Failed to remove temp file '{current_file_path}': {e}")
                     current_file_path = output_noaudio_path
                     print(f"DEBUG: current_file_path is now '{current_file_path}'")
                     # No re-encoding happened here for the video stream
                 except subprocess.CalledProcessError as e:
                     print(f"Error during FFmpeg Audio Removal:\nStderr:\n{e.stderr}"); self.update_status(f"{progress_prefix} Error removing audio."); processing_error = True
                     # --- FIX: Indented try/except for cleanup ---
                     if os.path.exists(output_noaudio_path):
                         try:
                             os.remove(output_noaudio_path)
                         except OSError:
                             pass # Ignore error on cleanup
                 except Exception as e:
                     print(f"Unexpected error during FFmpeg audio removal: {e}"); self.update_status(f"{progress_prefix} Error removing audio."); processing_error = True
                     # --- FIX: Indented try/except for cleanup ---
                     if os.path.exists(output_noaudio_path):
                         try:
                             os.remove(output_noaudio_path)
                         except OSError:
                             pass # Ignore error on cleanup


            # --- Stage 2: Aspect Ratio Adjustment ---
            if is_adjusting_ar and not processing_error:
                 self.update_status(f"{progress_prefix} Adjusting Aspect Ratio to {aspect_ratio_selection}...")
                 width, height = get_video_dimensions(current_file_path)
                 if width and height:
                     target_ar_val = parse_aspect_ratio(aspect_ratio_selection)
                     source_ar_val = width / height
                     tolerance = 0.01
                     ffmpeg_ar_command = None
                     output_ar_path = current_file_path.replace("_TEMP_DOWNLOAD", "_TEMP_AR").replace("_TEMP_NOAUDIO", "_TEMP_AR")
                     needs_ar_processing = True

                     if abs(source_ar_val - target_ar_val) < tolerance: self.update_status(f"{progress_prefix} Source AR matches target. Skipping."); needs_ar_processing = False
                     else:
                         common_opts = [ffmpeg_path if ffmpeg_path else "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", current_file_path]
                         filter_vf = ""
                         if source_ar_val > target_ar_val: # Crop
                             filter_vf = f"crop=w=ih*{target_ar_val:.4f}:h=ih,scale=trunc(iw/2)*2:trunc(ih/2)*2" # Ensure even dims after crop
                             print("AR Filter (Crop):", filter_vf)
                         else: # Pad
                             filter_vf = f"pad=w=ih*{target_ar_val:.4f}:h=ih:x=(ow-iw)/2:y=0:color=black,scale=trunc(iw/2)*2:trunc(ih/2)*2" # Ensure even dims after pad
                             print("AR Filter (Pad):", filter_vf)

                         # Build command, audio copy depends on 'needs_audio_removal' state
                         ffmpeg_ar_command = common_opts + ["-vf", filter_vf]
                         if not needs_audio_removal: ffmpeg_ar_command.extend(["-c:a", "copy"]) # Copy audio if it exists
                         # No -c:v copy here, filters require re-encoding
                         ffmpeg_ar_command.extend(["-map", "0", "-preset", "fast", output_ar_path])


                     if ffmpeg_ar_command and needs_ar_processing:
                         try:
                             print(f"Running FFmpeg AR: {' '.join(ffmpeg_ar_command)}")
                             ar_proc = subprocess.run(ffmpeg_ar_command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                             print(f"FFmpeg AR Output:\n{ar_proc.stderr}")
                             self.update_status(f"{progress_prefix} Aspect Ratio adjusted.")
                             re_encoding_occurred = True # AR adjustment forces re-encoding
                             try: # Keep simple try/except for removing previous temp
                                 print(f"DEBUG: Removing '{current_file_path}' after AR adjust."); os.remove(current_file_path)
                             except OSError as e: print(f"Warning: Failed to remove temp file '{current_file_path}': {e}")
                             current_file_path = output_ar_path
                             print(f"DEBUG: current_file_path is now '{current_file_path}'")
                         except subprocess.CalledProcessError as e:
                             print(f"Error during FFmpeg AR adjustment:\nStderr:\n{e.stderr}"); self.update_status(f"{progress_prefix} Error adjusting AR."); processing_error = True
                             # --- FIX: Indented try/except for cleanup ---
                             if os.path.exists(output_ar_path):
                                 try:
                                     os.remove(output_ar_path)
                                 except OSError:
                                     pass # Ignore error on cleanup
                         except Exception as e:
                             print(f"Unexpected error during FFmpeg AR adjustment: {e}"); self.update_status(f"{progress_prefix} Error adjusting AR."); processing_error = True
                             # --- FIX: Indented try/except for cleanup ---
                             if os.path.exists(output_ar_path):
                                 try:
                                     os.remove(output_ar_path)
                                 except OSError:
                                     pass # Ignore error on cleanup
                 else:
                     self.update_status(f"{progress_prefix} Warning: Could not get dimensions. Skipping AR adjustment.")


            # --- Stage 3: Time Cutting ---
            if is_cutting and not processing_error:
                 self.update_status(f"{progress_prefix} Cutting time range...")
                 start_sec, end_sec = time_range
                 # Define output path for the cut file (could be the final one if no chopping)
                 output_cut_path = current_file_path.replace("_TEMP_DOWNLOAD", "_TEMP_CUT").replace("_TEMP_NOAUDIO", "_TEMP_CUT").replace("_TEMP_AR", "_TEMP_CUT")

                 ffmpeg_cut_command = [
                       ffmpeg_path if ffmpeg_path else "ffmpeg", "-hide_banner", "-loglevel", "warning", # Show warnings for cut
                       "-i", current_file_path, # Use accurate input seeking if possible/needed later
                       "-ss", str(start_sec),   # Specify start time accurately
                       "-to", str(end_sec),     # Specify end time accurately
                       #"-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", # Re-enable if needed, but might slow down -c copy
                       "-map", "0", # Map all streams
                       "-avoid_negative_ts", "make_zero",
                       "-preset", "fast",
                       # Decide on codec copy: Only if no prior re-encoding happened
                       *(["-c", "copy"] if not re_encoding_occurred else []),
                       output_cut_path
                 ]

                 try:
                     print(f"Running FFmpeg Cut: {' '.join(ffmpeg_cut_command)}")
                     cut_proc = subprocess.run(ffmpeg_cut_command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                     print(f"FFmpeg Cut Output:\n{cut_proc.stderr}")
                     self.update_status(f"{progress_prefix} Time cutting successful.")
                     if "-c" not in ffmpeg_cut_command: re_encoding_occurred = True # Mark if re-encoded here
                     try: # Keep simple try/except for removing previous temp
                         print(f"DEBUG: Removing '{current_file_path}' after cut."); os.remove(current_file_path)
                     except OSError as e: print(f"Warning: Failed to remove temp file '{current_file_path}': {e}")
                     current_file_path = output_cut_path
                     print(f"DEBUG: current_file_path is now '{current_file_path}'")
                 except subprocess.CalledProcessError as e:
                     # If -c copy failed, maybe try again without it? For now, just error out.
                     print(f"Error during FFmpeg time cutting:\nStderr:\n{e.stderr}"); self.update_status(f"{progress_prefix} Error cutting time."); processing_error = True
                     # --- FIX: Indented try/except for cleanup ---
                     if os.path.exists(output_cut_path):
                         try:
                             os.remove(output_cut_path)
                         except OSError:
                             pass # Ignore error on cleanup
                 except Exception as e:
                     print(f"Unexpected error during FFmpeg time cutting: {e}"); self.update_status(f"{progress_prefix} Error cutting time."); processing_error = True
                     # --- FIX: Indented try/except for cleanup ---
                     if os.path.exists(output_cut_path):
                         try:
                             os.remove(output_cut_path)
                         except OSError:
                             pass # Ignore error on cleanup


            # --- *** Stage 4: Chopping into Intervals *** ---
            if is_chopping and not processing_error:
                self.update_status(f"{progress_prefix} Preparing to chop into {chop_interval_seconds}s intervals...")
                # Get duration of the *current* file (which might have been cut/AR adjusted)
                source_duration = get_video_duration(current_file_path)

                if source_duration is None:
                    self.update_status(f"{progress_prefix} Error: Could not get duration for chopping. Skipping chop.")
                    # Continue to finalization with the un-chopped file if possible
                elif source_duration <= 0:
                     self.update_status(f"{progress_prefix} Error: Source duration is zero or negative. Skipping chop.")
                else:
                    num_segments = math.ceil(source_duration / chop_interval_seconds)
                    print(f"DEBUG: Chopping '{current_file_path}' (Duration: {source_duration:.2f}s) into {num_segments} segments of ~{chop_interval_seconds}s")

                    segment_success = True
                    processed_segments = 0
                    for i in range(num_segments):
                        segment_start_time = i * chop_interval_seconds
                        # Duration is the interval, unless it's the last segment
                        segment_duration = min(chop_interval_seconds, source_duration - segment_start_time)

                        # Break if calculated duration is negligible (avoids tiny last segments due to float precision)
                        if segment_duration < 0.01: break

                        processed_segments += 1 # Count actual segments processed
                        segment_num = i + 1
                        segment_output_path = os.path.join(path, f"{intermediate_output_base}_part_{segment_num}{final_extension}")

                        self.update_status(f"{progress_prefix} Chopping segment {segment_num}/{num_segments}...")

                        ffmpeg_chop_command = [
                            ffmpeg_path if ffmpeg_path else "ffmpeg", "-hide_banner", "-loglevel", "warning",
                            "-i", current_file_path,
                            "-ss", str(segment_start_time),
                            "-t", str(segment_duration), # Use duration for segment length
                            "-map", "0",
                            "-avoid_negative_ts", "make_zero",
                            "-preset", "fast",
                             # Use codec copy only if no prior re-encoding happened
                            *(["-c", "copy"] if not re_encoding_occurred else []),
                            segment_output_path
                        ]

                        try:
                            print(f"Running FFmpeg Chop (Segment {segment_num}): {' '.join(ffmpeg_chop_command)}")
                            chop_proc = subprocess.run(ffmpeg_chop_command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                            # Limit printing stderr unless it's large or contains 'error'/'warning' ? For now print all warnings.
                            if chop_proc.stderr and chop_proc.stderr.strip(): print(f"FFmpeg Chop Output (Segment {segment_num}):\n{chop_proc.stderr}")
                            # No need to mark re_encoding_occurred here, it depends on prior steps

                        except subprocess.CalledProcessError as e:
                            print(f"Error chopping segment {segment_num} for '{os.path.basename(current_file_path)}':")
                            print(f"Command: {' '.join(e.cmd)}")
                            print(f"Stderr:\n{e.stderr}")
                            self.update_status(f"{progress_prefix} Error chopping segment {segment_num}.")
                            segment_success = False
                            # Clean up failed segment file
                            # --- FIX: Indented try/except for cleanup ---
                            if os.path.exists(segment_output_path):
                                try:
                                    os.remove(segment_output_path)
                                except OSError:
                                    pass # Ignore error on cleanup
                            break # Stop chopping this file on first error
                        except Exception as e:
                            print(f"Unexpected error chopping segment {segment_num}: {e}")
                            self.update_status(f"{progress_prefix} Error chopping segment {segment_num}.")
                            segment_success = False
                            # --- FIX: Indented try/except for cleanup ---
                            if os.path.exists(segment_output_path):
                                try:
                                    os.remove(segment_output_path)
                                except OSError:
                                    pass # Ignore error on cleanup
                            break # Stop chopping

                    # --- After Chopping Loop ---
                    if segment_success and processed_segments > 0:
                        self.update_status(f"{progress_prefix} Successfully chopped into {processed_segments} segments.")
                        # Clean up the source file used for chopping
                        try: # Keep simple try/except for removing chop source file
                            print(f"DEBUG: Removing '{current_file_path}' after successful chopping.")
                            os.remove(current_file_path)
                            current_file_path = None # Indicate the original is gone
                        except OSError as e: print(f"Warning: Failed to remove source file '{current_file_path}' after chopping: {e}")
                        # Set flag to prevent final rename step
                        processing_error = False # Ensure it's false if chopping succeeded
                        # Remove URL from GUI now, as chopping is the final step
                        self.root.after(0, self.remove_url_from_gui_and_internal, url)
                        # Skip the final rename stage
                        continue # Go to the next URL

                    else:
                        # Chopping failed or produced no segments
                        if processed_segments == 0 and segment_success: # e.g. duration was too short?
                             self.update_status(f"{progress_prefix} No segments generated (source duration likely too short). Keeping original.")
                             # Don't mark as error, proceed to finalize the unchopped file
                        else: # Actual error occurred
                            self.update_status(f"{progress_prefix} Chopping failed. Keeping intermediate file.")
                            processing_error = True # Mark as error to prevent deleting intermediate


            # --- Stage 5: Finalization (Only if NOT chopping, or if chopping failed) ---
            if not processing_error and current_file_path: # Ensure file exists and no error stopped us
                # Rename the last intermediate file to its final intended name
                # (intermediate_output_path was calculated based on title and tags earlier)
                if current_file_path != intermediate_output_path:
                    try:
                        print(f"Finalizing: Renaming '{current_file_path}' to '{intermediate_output_path}'")
                        # Ensure target directory exists (should, but safety check)
                        os.makedirs(os.path.dirname(intermediate_output_path), exist_ok=True)
                        os.rename(current_file_path, intermediate_output_path)
                        self.update_status(f"{progress_prefix} Success: {os.path.basename(intermediate_output_path)}")
                        # Remove from GUI only on complete success
                        self.root.after(0, self.remove_url_from_gui_and_internal, url)
                    except OSError as e:
                        print(f"Error renaming final file: {e}")
                        self.update_status(f"{progress_prefix} Error finalizing file (rename failed).")
                        processing_error = True # Mark as error, keep the temp file
                else:
                    # This happens if no post-processing was done at all (dl straight to final name structure)
                    # OR if chopping failed and we are keeping the intermediate file named correctly.
                    if os.path.exists(intermediate_output_path):
                         self.update_status(f"{progress_prefix} Success: {os.path.basename(intermediate_output_path)}")
                         self.root.after(0, self.remove_url_from_gui_and_internal, url)
                    else: # Should not happen if current_file_path == intermediate_output_path
                         self.update_status(f"{progress_prefix} Final file missing unexpectedly.")
                         processing_error = True


            # --- Cleanup on Error during post-processing ---
            if processing_error and current_file_path and os.path.exists(current_file_path):
                # If an error happened *after* download but *before* successful chopping/finalization
                self.update_status(f"{progress_prefix} Failed during post-processing. Check console.")
                print(f"Keeping intermediate file due to error: {current_file_path}")
                # We explicitly DON'T remove the current_file_path here, as it might be useful.


        # --- Loop finished ---
        self.root.after(0, self.enable_download_button)
        remaining_items = self.queue_listbox.get(0, tk.END)
        if not remaining_items:
            self.update_status("Download queue finished. All items processed.")
        else:
             failed_count = len(remaining_items)
             total_processed = initial_queue_size - failed_count
             self.update_status(f"Queue finished. {total_processed} item(s) processed, {failed_count} failed or skipped.")


    def remove_url_from_gui_and_internal(self, url):
        # (No changes needed)
        try:
            if self.root.winfo_exists():
                items = list(self.queue_listbox.get(0, tk.END))
                if url in items:
                    index = items.index(url)
                    self.queue_listbox.delete(index)
        except ValueError: print(f"Warning: URL {url} not found in GUI for removal.")
        except Exception as e: print(f"Error removing URL from GUI: {e}")


    def enable_download_button(self):
        # (No changes needed)
        try:
            if self.root.winfo_exists(): self.download_button.config(state=tk.NORMAL)
        except tk.TclError: pass

    # --- Modified on_closing to save new settings ---
    def on_closing(self):
        """Called when the user tries to close the window."""
        current_path = self.download_path.get()
        if isinstance(current_path, str) and os.path.isdir(current_path):
            self.settings["download_path"] = current_path
        else:
             print(f"Warning: Download path invalid on close. Saving script directory.")
             self.settings["download_path"] = SCRIPT_DIR

        # Save all settings
        self.settings["video_only"] = self.video_only_var.get()
        self.settings["enable_cut"] = self.enable_cut_var.get()
        self.settings["start_time"] = self.start_time_var.get()
        self.settings["end_time"] = self.end_time_var.get()
        self.settings["aspect_ratio"] = self.aspect_ratio_var.get()
        self.settings["enable_chop"] = self.enable_chop_var.get()      # NEW
        self.settings["chop_interval"] = self.chop_interval_var.get() # NEW

        save_settings(self.settings)
        print("Settings saved. Exiting.")
        self.root.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MediaDownloaderApp(root)
    root.mainloop()