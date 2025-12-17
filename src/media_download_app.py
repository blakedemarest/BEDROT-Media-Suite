import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess # For running yt-dlp, ffmpeg, ffprobe
import json      # For parsing yt-dlp progress AND saving settings
import re        # For parsing time strings
import math      # For aspect ratio comparison tolerance and chopping duration
import datetime  # For timestamp
import random    # For random string
import string    # For random string characters

# --- Define base paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(SCRIPT_DIR, '..', 'config')
SETTINGS_FILENAME = "yt_downloader_gui_settings.json"

# --- Import centralized configuration system ---
try:
    from core import get_config_manager, load_app_config, save_app_config
    from core.env_loader import get_env_var
    from core.path_utils import resolve_config_path, resolve_output_path
    
    # Load environment and configuration
    config_manager = get_config_manager()
    APP_CONFIG = load_app_config('media_download', 'yt_downloader_gui_settings.json')
    SETTINGS_FILE_PATH = str(resolve_config_path('yt_downloader_gui_settings.json'))
    
except ImportError as e:
    print(f"Warning: Could not import core configuration system: {e}")
    print("Falling back to hardcoded paths")
    
    # --- Fallback: Define Settings File Path ---
    SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, SETTINGS_FILENAME)
    
    if not os.path.exists(CONFIG_DIR): # Create config dir if it doesn't exist
        try:
            os.makedirs(CONFIG_DIR)
            print(f"INFO: Created config directory: {CONFIG_DIR}")
        except OSError as e:
            print(f"ERROR: Could not create config directory: {CONFIG_DIR}. Error: {e}")
            SETTINGS_FILE_PATH = os.path.join(SCRIPT_DIR, SETTINGS_FILENAME) # Fallback
    
    config_manager = None
    APP_CONFIG = {}


# --- Common Aspect Ratios ---
ASPECT_RATIOS = [
    "Original", "16:9", "4:3", "1:1", "9:16", "21:9", "2.35:1", "1.85:1"
]

# --- Helper: Time String Parsing ---
def parse_time_to_seconds(time_str):
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
    if ratio_str == "Original":
        return None
    try:
        w_str, h_str = ratio_str.split(':')
        w, h = float(w_str), float(h_str)
        if h == 0: return None
        return w / h
    except ValueError:
        return None

# --- Settings Load/Save Functions ---
def load_settings():
    """Loads settings from the JSON file."""
    # Get default download path from centralized config or fallback
    if config_manager:
        try:
            default_download_path = str(resolve_output_path())
        except Exception as e:
            print(f"Warning: Could not resolve default output path: {e}")
            default_download_path = SCRIPT_DIR
    else:
        default_download_path = SCRIPT_DIR
    
    default_settings = {
        "download_path": default_download_path,
        "video_only": False,
        "enable_cut": False,
        "start_time": "",
        "end_time": "",
        "aspect_ratio": get_env_var('SLIDESHOW_DEFAULT_ASPECT_RATIO', 'Original') if config_manager else "Original",
        "enable_chop": False,
        "chop_interval": "60"
    }
    # Ensure config directory exists before trying to load
    if not os.path.exists(CONFIG_DIR) and CONFIG_DIR != SCRIPT_DIR:
        try:
            os.makedirs(CONFIG_DIR)
            print(f"INFO: Created config directory: {CONFIG_DIR}")
        except OSError as e:
            print(f"ERROR: Could not create config directory: {CONFIG_DIR}. Using script directory for settings. Error: {e}")
            settings_path = os.path.join(SCRIPT_DIR, SETTINGS_FILENAME)
    else:
        settings_path = SETTINGS_FILE_PATH


    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
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
            print(f"Error loading settings file '{settings_path}': {e}. Using defaults.")
            return default_settings.copy()
    else:
        print(f"Settings file '{os.path.basename(settings_path)}' not found. Using defaults.")
        return default_settings.copy()

def save_settings(settings_dict):
    """Saves settings to the JSON file."""
    # Ensure config directory exists before trying to save
    if not os.path.exists(CONFIG_DIR) and CONFIG_DIR != SCRIPT_DIR:
        try:
            os.makedirs(CONFIG_DIR)
            print(f"INFO: Created config directory: {CONFIG_DIR}")
        except OSError as e:
            print(f"ERROR: Could not create config directory: {CONFIG_DIR}. Saving to script directory instead. Error: {e}")
            settings_path = os.path.join(SCRIPT_DIR, SETTINGS_FILENAME)
    else:
        settings_path = SETTINGS_FILE_PATH

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


        with open(settings_path, 'w') as f:
            json.dump(settings_dict, f, indent=4)
    except IOError as e:
        print(f"Error saving settings file '{settings_path}': {e}")
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
            proc_ffprobe_check = subprocess.run([cmd_f, "ffprobe"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
            ffprobe_path_out_check = proc_ffprobe_check.stdout.strip().split('\n')[0]
            if ffprobe_path_out_check:
                ffprobe_path = ffprobe_path_out_check
                ffprobe_found = True # Found it after all
                print(f"INFO: Found FFprobe at: {ffprobe_path}")
        except:
            print("WARNING: FFprobe also not found in system PATH.")
            print("         Aspect ratio adjustment and video chopping require FFprobe.")
            ffprobe_found = False
    elif tool_name == "FFprobe" and not ffmpeg_found:
         try:
            proc_ffmpeg_check = subprocess.run([cmd_f, "ffmpeg"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
            ffmpeg_path_out_check = proc_ffmpeg_check.stdout.strip().split('\n')[0]
            if ffmpeg_path_out_check:
                ffmpeg_path = ffmpeg_path_out_check
                ffmpeg_found = True
                print(f"INFO: Found FFmpeg at: {ffmpeg_path}")
         except:
            print("WARNING: FFmpeg also not found in system PATH.")
            print("         Multiple features require FFmpeg.")
            ffmpeg_found = False


# --- Helper: Get Video Dimensions ---
def get_video_dimensions(filepath):
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

# --- Helper: Generate Unique Suffix ---
def generate_unique_suffix(length=8):
    """Generates a unique suffix string using datetime and random characters."""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"_{timestamp}_{random_part}"

# --- Helper: Expand Playlist/Profile URL ---
def expand_playlist_url(url_to_expand):
    """
    Uses yt-dlp to extract individual video URLs from a playlist or profile URL.
    Returns a list of URLs. Returns [url_to_expand] on failure or if it's likely a single video.
    """
    # Use Python module invocation for yt-dlp
    venv_python = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        command = [
            venv_python, "-m", "yt_dlp"
        ]
    else:
        # Fallback to system yt-dlp
        try:
            cmd_where = "where" if os.name == 'nt' else "which"
            subprocess.run([cmd_where, "yt-dlp"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
            command = [
                "yt-dlp"
            ]
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: yt-dlp not found, cannot expand URL.")
            return [url_to_expand] # Fallback
    
    command.extend([
        "--flat-playlist",
        "--print", "webpage_url",
        "--no-warnings",
        "--skip-download",
        url_to_expand
    ])
    print(f"Attempting to expand URL: {url_to_expand}")
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=True,
                              encoding='utf-8', errors='replace',
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        output_urls = proc.stdout.strip().splitlines()
        output_urls = [u for u in output_urls if u.strip()]

        if not output_urls:
            print(f"INFO: No URLs extracted from '{url_to_expand}'. Treating as single item.")
            return [url_to_expand]
        elif len(output_urls) == 1 and output_urls[0] == url_to_expand:
             print(f"INFO: Expansion returned the original URL. Treating as single item: {url_to_expand}")
             return [url_to_expand]
        else:
            print(f"INFO: Expanded '{url_to_expand}' into {len(output_urls)} items.")
            return output_urls

    except subprocess.CalledProcessError as e:
        stderr_lower = e.stderr.lower() if e.stderr else ""
        if "unavailable" in stderr_lower or "not found" in stderr_lower or "no media found" in stderr_lower:
             print(f"Warning: yt-dlp reported issue expanding '{url_to_expand}', but treating as single item anyway. Stderr: {e.stderr.strip()}")
        else:
             print(f"ERROR: yt-dlp failed to expand URL '{url_to_expand}' (Code: {e.returncode}). Treating as single item. Stderr: {e.stderr.strip()}")
        return [url_to_expand]
    except FileNotFoundError:
        print("ERROR: yt-dlp command not found during expansion.")
        return [url_to_expand]
    except Exception as e:
        print(f"Unexpected error during URL expansion for '{url_to_expand}': {e}")
        return [url_to_expand]


# --- Main Application Class ---
class MediaDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BEDROT MEDIA DOWNLOADER // MP4 & MP3 CONVERTER")
        self.root.configure(bg='#121212')
        
        # Apply BEDROT theme
        self.apply_bedrot_theme()

        self.settings = load_settings()
        initial_path = self.settings.get("download_path", SCRIPT_DIR)

        self.download_queue = []
        self.download_path = tk.StringVar(value=initial_path)
        self.download_format = tk.StringVar(value="mp4")
        
        # Abort functionality
        self.abort_flag = threading.Event()
        self.current_process = None
        self.is_downloading = False

        # Option Variables
        self.video_only_var = tk.BooleanVar(value=self.settings.get("video_only", False))
        self.enable_cut_var = tk.BooleanVar(value=self.settings.get("enable_cut", False))
        self.start_time_var = tk.StringVar(value=self.settings.get("start_time", ""))
        self.end_time_var = tk.StringVar(value=self.settings.get("end_time", ""))
        self.aspect_ratio_var = tk.StringVar(value=self.settings.get("aspect_ratio", "Original"))
        self.enable_chop_var = tk.BooleanVar(value=self.settings.get("enable_chop", False))
        self.chop_interval_var = tk.StringVar(value=self.settings.get("chop_interval", "60"))

        # Traces
        self.enable_cut_var.trace_add("write", self.toggle_time_entries)
        self.enable_chop_var.trace_add("write", self.toggle_chop_entry)
        self.download_format.trace_add("write", self.toggle_video_only_option)

        self.root.geometry("600x750")
        self.create_widgets()
        self.toggle_time_entries()
        self.toggle_chop_entry()
        self.toggle_video_only_option()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.is_adding_to_queue = False

    def apply_bedrot_theme(self):
        """Apply the BEDROT cyberpunk visual theme to all tkinter/ttk widgets."""
        style = ttk.Style()
        
        # Configure ttk styles with BEDROT theme
        style.configure('TFrame', background='#121212', borderwidth=0)
        style.configure('TLabel', background='#121212', foreground='#e0e0e0')
        
        # Entry widget style
        style.configure('TEntry',
                       fieldbackground='#1a1a1a',
                       foreground='#e0e0e0',
                       insertcolor='#00ff88',
                       borderwidth=1)
        style.map('TEntry',
                 fieldbackground=[('focus', '#222222')],
                 bordercolor=[('focus', '#00ffff')])
        
        # Button style
        style.configure('TButton',
                       background='#1a1a1a',
                       foreground='#e0e0e0',
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat')
        style.map('TButton',
                 background=[('active', '#252525'), ('pressed', '#0a0a0a')],
                 foreground=[('active', '#00ff88'), ('pressed', '#00ffff')])
        
        # Radiobutton style
        style.configure('TRadiobutton',
                       background='#121212',
                       foreground='#e0e0e0',
                       focuscolor='none',
                       indicatorcolor='#00ff88')
        style.map('TRadiobutton',
                 background=[('active', '#121212')],
                 foreground=[('active', '#00ff88')])
        
        # Checkbutton style
        style.configure('TCheckbutton',
                       background='#121212',
                       foreground='#e0e0e0',
                       focuscolor='none',
                       indicatorcolor='#00ff88')
        style.map('TCheckbutton',
                 background=[('active', '#121212')],
                 foreground=[('active', '#00ff88')])
        
        # Combobox style
        style.configure('TCombobox',
                       fieldbackground='#1a1a1a',
                       foreground='#e0e0e0',
                       selectbackground='#00ffff',
                       selectforeground='#000000',
                       arrowcolor='#00ff88')
        style.map('TCombobox',
                 fieldbackground=[('focus', '#222222')])
        
        # Scrollbar style
        style.configure('Vertical.TScrollbar',
                       background='#0a0a0a',
                       troughcolor='#0a0a0a',
                       bordercolor='#1a1a1a',
                       arrowcolor='#00ff88',
                       darkcolor='#0a0a0a',
                       lightcolor='#0a0a0a')
        style.map('Vertical.TScrollbar',
                 background=[('active', '#00ff88'), ('pressed', '#00ffff')])

    def create_widgets(self):
        # Input & Folder Frames
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        ttk.Label(input_frame, text="Video/Playlist URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        input_frame.columnconfigure(1, weight=1)
        self.add_button = ttk.Button(input_frame, text="ADD TO QUEUE", command=self.add_to_queue_threaded)
        self.add_button.grid(row=0, column=2, padx=5, pady=5)

        folder_frame = ttk.Frame(self.root, padding="10")
        folder_frame.pack(fill=tk.X)
        ttk.Label(folder_frame, text="Download Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        # Create a frame for the folder path display
        folder_display_frame = tk.Frame(folder_frame, bg='#1a1a1a', highlightbackground='#404040', highlightthickness=1, bd=0)
        self.folder_label = tk.Label(folder_display_frame, textvariable=self.download_path, bg='#1a1a1a', fg='#e0e0e0', padx=5, pady=2)
        self.folder_label.pack(fill=tk.BOTH, expand=True)
        folder_display_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        folder_frame.columnconfigure(1, weight=1)
        browse_button = ttk.Button(folder_frame, text="BROWSE", command=self.choose_folder)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        # Options Frame
        options_outer_frame = ttk.Frame(self.root, padding="10")
        options_outer_frame.pack(fill=tk.X)

        # Format Column
        format_column = ttk.Frame(options_outer_frame)
        format_column.pack(side=tk.LEFT, padx=5, pady=5, anchor='nw', fill=tk.Y)
        
        # Custom frame for Format section
        format_container = tk.Frame(format_column, bg='#121212', bd=0)
        format_container.pack(fill=tk.X)
        format_label = tk.Label(format_container, text=" FORMAT ", bg='#121212', fg='#00ffff', font=('Segoe UI', 10, 'bold'))
        format_label.pack(anchor=tk.W)
        format_border = tk.Frame(format_container, bg='#121212', highlightbackground='#00ffff', highlightthickness=1, bd=0)
        format_border.pack(fill=tk.BOTH, expand=True)
        format_frame = tk.Frame(format_border, bg='#121212', bd=0)
        format_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        mp4_radio = ttk.Radiobutton(format_frame, text="MP4", variable=self.download_format, value="mp4")
        mp4_radio.pack(anchor=tk.W)
        mp3_radio = ttk.Radiobutton(format_frame, text="MP3 (Audio Only)", variable=self.download_format, value="mp3")
        mp3_radio.pack(anchor=tk.W)
        self.video_only_check = ttk.Checkbutton(format_frame, text="Video Only (No Audio)", variable=self.video_only_var)
        self.video_only_check.pack(anchor=tk.W, padx=(15, 0))

        # Processing Column
        processing_column = ttk.Frame(options_outer_frame)
        processing_column.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True, anchor='nw')

        # Cutting Options
        cut_container = tk.Frame(processing_column, bg='#121212', bd=0)
        cut_container.pack(fill=tk.X, pady=(0, 5))
        cut_label = tk.Label(cut_container, text=" TIME RANGE CUT (REQUIRES FFMPEG) ", bg='#121212', fg='#00ffff', font=('Segoe UI', 10, 'bold'))
        cut_label.pack(anchor=tk.W)
        cut_border = tk.Frame(cut_container, bg='#121212', highlightbackground='#00ffff', highlightthickness=1, bd=0)
        cut_border.pack(fill=tk.BOTH, expand=True)
        cut_frame = tk.Frame(cut_border, bg='#121212', bd=0)
        cut_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        enable_cut_check = ttk.Checkbutton(cut_frame, text="Cut to Selected Time Range", variable=self.enable_cut_var)
        enable_cut_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        tk.Label(cut_frame, text="Start:", bg='#121212', fg='#e0e0e0').grid(row=1, column=0, sticky=tk.W)
        self.start_time_entry = ttk.Entry(cut_frame, textvariable=self.start_time_var, width=12)
        self.start_time_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        tk.Label(cut_frame, text="End:", bg='#121212', fg='#e0e0e0').grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        self.end_time_entry = ttk.Entry(cut_frame, textvariable=self.end_time_var, width=12)
        self.end_time_entry.grid(row=1, column=3, padx=5, sticky=tk.W)
        time_format_label = tk.Label(cut_frame, text="(HH:MM:SS or MM:SS or SS)", bg='#121212', fg='#666666')
        time_format_label.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(5,0))

        # Aspect Ratio Frame
        ar_container = tk.Frame(processing_column, bg='#121212', bd=0)
        ar_container.pack(fill=tk.X, pady=(5, 5))
        ar_label = tk.Label(ar_container, text=" ASPECT RATIO (REQUIRES FFMPEG/FFPROBE) ", bg='#121212', fg='#00ffff', font=('Segoe UI', 10, 'bold'))
        ar_label.pack(anchor=tk.W)
        ar_border = tk.Frame(ar_container, bg='#121212', highlightbackground='#00ffff', highlightthickness=1, bd=0)
        ar_border.pack(fill=tk.BOTH, expand=True)
        ar_frame = tk.Frame(ar_border, bg='#121212', bd=0)
        ar_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        tk.Label(ar_frame, text="Adjust to:", bg='#121212', fg='#e0e0e0').pack(side=tk.LEFT, padx=(0, 5))
        self.ar_combobox = ttk.Combobox(ar_frame, textvariable=self.aspect_ratio_var, values=ASPECT_RATIOS, state="readonly", width=15)
        self.ar_combobox.pack(side=tk.LEFT)
        tk.Label(ar_frame, text="(Crop/Pad)", bg='#121212', fg='#666666').pack(side=tk.LEFT, padx=(10, 0))

        # Chopping Frame
        chop_container = tk.Frame(processing_column, bg='#121212', bd=0)
        chop_container.pack(fill=tk.X, pady=(5, 0))
        chop_label = tk.Label(chop_container, text=" CHOP INTO INTERVALS (REQUIRES FFMPEG/FFPROBE) ", bg='#121212', fg='#00ffff', font=('Segoe UI', 10, 'bold'))
        chop_label.pack(anchor=tk.W)
        chop_border = tk.Frame(chop_container, bg='#121212', highlightbackground='#00ffff', highlightthickness=1, bd=0)
        chop_border.pack(fill=tk.BOTH, expand=True)
        chop_frame = tk.Frame(chop_border, bg='#121212', bd=0)
        chop_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        enable_chop_check = ttk.Checkbutton(chop_frame, text="Chop output into segments of:", variable=self.enable_chop_var)
        enable_chop_check.grid(row=0, column=0, sticky=tk.W)
        self.chop_interval_entry = ttk.Entry(chop_frame, textvariable=self.chop_interval_var, width=8)
        self.chop_interval_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        tk.Label(chop_frame, text="seconds", bg='#121212', fg='#e0e0e0').grid(row=0, column=2, sticky=tk.W)

        # Queue Frame
        queue_container = tk.Frame(self.root, bg='#121212', bd=0)
        queue_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5,0))
        queue_label = tk.Label(queue_container, text=" DOWNLOAD QUEUE ", bg='#121212', fg='#00ffff', font=('Segoe UI', 10, 'bold'))
        queue_label.pack(anchor=tk.W)
        queue_border = tk.Frame(queue_container, bg='#121212', highlightbackground='#00ffff', highlightthickness=1, bd=0)
        queue_border.pack(fill=tk.BOTH, expand=True)
        queue_frame = tk.Frame(queue_border, bg='#121212', bd=0)
        queue_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.queue_listbox = tk.Listbox(queue_frame, height=6, bg='#1a1a1a', fg='#e0e0e0', 
                                        selectbackground='#00ffff', selectforeground='#000000',
                                        highlightbackground='#404040', highlightcolor='#00ffff',
                                        highlightthickness=1, bd=0)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=scrollbar.set)

        # Action Buttons Frame
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)
        self.download_button = ttk.Button(action_frame, text="DOWNLOAD QUEUE", command=self.start_download_thread)
        self.download_button.pack(side=tk.LEFT, padx=5)
        self.abort_button = ttk.Button(action_frame, text="ABORT DOWNLOAD", command=self.abort_download, state=tk.DISABLED)
        self.abort_button.pack(side=tk.LEFT, padx=5)
        clear_button = ttk.Button(action_frame, text="CLEAR SELECTED", command=self.clear_selected)
        clear_button.pack(side=tk.LEFT, padx=5)
        clear_all_button = ttk.Button(action_frame, text="CLEAR ALL", command=self.clear_all)
        clear_all_button.pack(side=tk.LEFT, padx=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready (using yt-dlp)")
        status_bar_frame = tk.Frame(self.root, bg='#0a0a0a', highlightbackground='#404040', highlightthickness=1, bd=0)
        status_bar = tk.Label(status_bar_frame, textvariable=self.status_var, bg='#0a0a0a', fg='#00ff88', anchor=tk.W, padx=5, pady=5)
        status_bar.pack(fill=tk.BOTH, expand=True)
        status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)


    # Toggle Control States
    def toggle_time_entries(self, *args):
        state = tk.NORMAL if self.enable_cut_var.get() else tk.DISABLED
        try:
            if self.start_time_entry.winfo_exists() and self.end_time_entry.winfo_exists():
                self.start_time_entry.config(state=state)
                self.end_time_entry.config(state=state)
        except tk.TclError: pass

    def toggle_video_only_option(self, *args):
         try:
              if self.video_only_check.winfo_exists():
                    state = tk.NORMAL if self.download_format.get() == "mp4" else tk.DISABLED
                    self.video_only_check.config(state=state)
                    if state == tk.DISABLED: self.video_only_var.set(False)
         except tk.TclError: pass

    def toggle_chop_entry(self, *args):
         state = tk.NORMAL if self.enable_chop_var.get() else tk.DISABLED
         try:
             if self.chop_interval_entry.winfo_exists():
                 self.chop_interval_entry.config(state=state)
         except tk.TclError: pass


    # GUI action to start expansion thread
    def add_to_queue_threaded(self):
        """Starts the URL expansion and adding process in a separate thread."""
        if self.is_adding_to_queue:
            self.update_status("Already processing previous add request...")
            return

        url = self.url_entry.get().strip()
        if not url:
            self.update_status("Please enter a Video or Playlist/Profile URL.")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
             self.update_status("Please enter a valid URL (starting with http:// or https://).")
             return

        self.is_adding_to_queue = True
        self.add_button.config(state=tk.DISABLED)
        self.update_status(f"Fetching items from URL: {url[:60]}...")

        expansion_thread = threading.Thread(target=self._add_to_queue_worker, args=(url,), daemon=True)
        expansion_thread.start()

    # Worker function for URL expansion and adding
    def _add_to_queue_worker(self, url_to_process):
        """
        Expands the URL and adds results to the queue listbox. Runs in a separate thread.
        """
        expanded_urls = expand_playlist_url(url_to_process)
        added_count = 0
        duplicate_count = 0

        def _update_gui():
            nonlocal added_count, duplicate_count
            current_items = set(self.queue_listbox.get(0, tk.END))

            for individual_url in expanded_urls:
                if individual_url not in current_items:
                    self.queue_listbox.insert(tk.END, individual_url)
                    current_items.add(individual_url)
                    added_count += 1
                else:
                    duplicate_count += 1

            # Update Status
            final_status = ""
            if added_count > 0 and duplicate_count > 0:
                final_status = f"Added {added_count} item(s). Skipped {duplicate_count} duplicates."
            elif added_count > 0:
                final_status = f"Added {added_count} item(s) to the queue."
            elif duplicate_count > 0:
                final_status = f"All {duplicate_count} item(s) from URL are already in the queue."
            else:
                 final_status = f"Failed to add items from URL. Check logs. Treating as single URL '{url_to_process[:60]}...'"
                 if url_to_process not in current_items:
                     self.queue_listbox.insert(tk.END, url_to_process)
                     added_count = 1
                     final_status = f"Expansion failed, added original URL: {url_to_process[:60]}..."

            self.update_status(final_status)
            if added_count > 0 :
                self.url_entry.delete(0, tk.END)

            # Re-enable button and reset flag (ensure it happens even if error)
            self.add_button.config(state=tk.NORMAL)
            self.is_adding_to_queue = False

        # Schedule the GUI update
        self.root.after(0, _update_gui)


    # Other GUI actions
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
        self.update_status("Selected items removed.")

    def clear_all(self):
        self.queue_listbox.delete(0, tk.END)
        self.update_status("Queue cleared.")

    def update_status(self, message):
        try:
            if self.root.winfo_exists():
                 self.root.after(0, self.status_var.set, message)
        except tk.TclError: pass

    # Download Start & Pre-checks
    def start_download_thread(self):
        self.download_queue = list(self.queue_listbox.get(0, tk.END))

        if not self.download_queue:
            messagebox.showwarning("Queue Empty", "Add URLs to the queue first.")
            return

        # Pre-checks (yt-dlp, path, ffmpeg/ffprobe based on OPTIONS)
        yt_dlp_available = False
        venv_python = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            # Check if yt-dlp module is available
            try:
                result = subprocess.run([venv_python, "-m", "yt_dlp", "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    yt_dlp_available = True
            except:
                pass
        
        if not yt_dlp_available:
            try:
                 cmd = "where" if os.name == 'nt' else "which"
                 subprocess.run([cmd, "yt-dlp"], capture_output=True, text=True, check=True, shell=(os.name=='nt'))
                 yt_dlp_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                 pass
        
        if not yt_dlp_available:
             messagebox.showerror("yt-dlp Error", "yt-dlp module not found. Please install yt-dlp in the virtual environment.")
             return

        if not os.path.isdir(self.download_path.get()):
             messagebox.showerror("Invalid Path", f"Download folder is invalid:\n{self.download_path.get()}")
             return

        # Specific FFmpeg/FFprobe checks based on selected options
        is_tiktok_video_only = False
        if self.download_format.get() == "mp4" and self.video_only_var.get():
            if any("tiktok.com" in url for url in self.download_queue):
                is_tiktok_video_only = True

        needs_ffmpeg = (self.enable_cut_var.get() or
                        self.aspect_ratio_var.get() != "Original" or
                        self.download_format.get() == "mp3" or
                        is_tiktok_video_only or
                        self.enable_chop_var.get())

        needs_ffprobe = (self.aspect_ratio_var.get() != "Original" or
                         self.enable_chop_var.get())

        if needs_ffmpeg and not ffmpeg_found:
             messagebox.showerror("FFmpeg Error", "The selected options (Cutting, Aspect Ratio, MP3, TikTok Video-Only, Chopping) require FFmpeg, but it was not found in your PATH.")
             return
        if needs_ffprobe and not ffprobe_found:
             messagebox.showerror("FFprobe Error", "Aspect ratio adjustment or Chopping requires FFprobe, but it was not found in your PATH.")
             return

        # Validate Times and Intervals
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

        selected_ar = self.aspect_ratio_var.get()
        if selected_ar != "Original" and parse_aspect_ratio(selected_ar) is None:
            messagebox.showerror("Invalid Aspect Ratio", f"Selected aspect ratio '{selected_ar}' is invalid.")
            return

        # Start Download
        self.download_button.config(state=tk.DISABLED)
        self.add_button.config(state=tk.DISABLED) # Disable Add button during download
        self.update_status("Starting download...")
        queue_copy = list(self.download_queue)
        time_range = (start_sec, end_sec) if self.enable_cut_var.get() else None
        aspect_ratio_selection = self.aspect_ratio_var.get()
        video_only_state = self.video_only_var.get()
        selected_format_state = self.download_format.get()
        chop_settings = (self.enable_chop_var.get(), chop_interval_sec)

        # Reset abort flag and update UI
        self.abort_flag.clear()
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.abort_button.config(state=tk.NORMAL)
        self.add_button.config(state=tk.DISABLED)
        
        download_thread = threading.Thread(
            target=self.process_queue_sequential,
            args=(queue_copy, time_range, aspect_ratio_selection,
                  video_only_state, selected_format_state, chop_settings),
            daemon=True)
        download_thread.start()

    def abort_download(self):
        """Abort the current download operation."""
        if self.is_downloading:
            self.update_status("Aborting download...")
            self.abort_flag.set()
            
            # Terminate current subprocess if running
            if self.current_process and self.current_process.poll() is None:
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                except Exception as e:
                    print(f"Error terminating process: {e}")
            
            # Update UI
            self.abort_button.config(state=tk.DISABLED)
            self.update_status("Download aborted by user")

    def enable_download_buttons(self):
        """Re-enable download buttons after completion or abort."""
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.abort_button.config(state=tk.DISABLED)
        self.add_button.config(state=tk.NORMAL)

    # --- SEQUENTIAL PROCESSING LOGIC (with SyntaxError fixes) ---
    def process_queue_sequential(self, queue_to_process, time_range, aspect_ratio_selection,
                                 video_only_setting, selected_format_setting, chop_settings):
        """
        Processes queue item by item: Download -> Apply Unique Suffix -> Remove Audio -> Adjust AR -> Cut -> Chop -> Finalize.
        Manages intermediate files. Receives only INDIVIDUAL video URLs.
        """
        path = self.download_path.get()
        selected_format = selected_format_setting
        is_video_only_general_flag = video_only_setting if selected_format == "mp4" else False
        is_cutting = time_range is not None
        is_adjusting_ar = aspect_ratio_selection != "Original"
        is_chopping, chop_interval_seconds = chop_settings

        initial_queue_size = len(queue_to_process)
        processed_count = 0

        for url in queue_to_process:
            # Check abort flag at start of each URL
            if self.abort_flag.is_set():
                self.update_status("Download queue aborted")
                break
                
            processed_count += 1
            progress_prefix = f"[{processed_count}/{initial_queue_size}]"
            self.update_status(f"{progress_prefix} Starting: {url[:70]}...")

            # --- Stage 0: Determine Filenames & Tags ---
            base_title = None
            unique_suffix = generate_unique_suffix()
            initial_download_path = None
            final_extension = ".mp3" if selected_format == "mp3" else ".mp4"

            is_tiktok_url = "tiktok.com" in url
            tiktok_video_only_special_case = is_tiktok_url and selected_format == "mp4" and is_video_only_general_flag
            no_audio_tag = "_NoAudio" if tiktok_video_only_special_case else ""
            ar_tag = ""
            time_tag = ""
            if is_adjusting_ar:
                ar_tag = f"_AR_{aspect_ratio_selection.replace(':', 'x').replace('.', '_')}"
            if is_cutting:
                start_sec, end_sec = time_range
                time_tag = f"_{int(start_sec)}s-{int(end_sec)}s"

            intermediate_output_base = "PLACEHOLDER" # Constructed after title obtained

            # --- Stage 1: Download with yt-dlp ---
            self.update_status(f"{progress_prefix} Downloading...")
            yt_dlp_success = False
            stderr_info = ""
            needs_audio_removal_post_dl = False

            # For MP3, we need to use a different output template without extension since yt-dlp will add it
            if selected_format == "mp3":
                temp_output_base = os.path.join(path, f"TEMP_DOWNLOAD_{unique_suffix.strip('_')}")
                temp_output_template = temp_output_base + ".%(ext)s"
                # Store for later use when finding the file
                self.temp_output_base = temp_output_base
            else:
                temp_output_template = os.path.join(path, f"TEMP_DOWNLOAD_{unique_suffix.strip('_')}{final_extension}")
            
            print(f"DEBUG: Using temp download template: {temp_output_template}")

            # Use Python module invocation for yt-dlp for better compatibility
            venv_python = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
            if os.path.exists(venv_python):
                # Use venv Python with module invocation
                command = [
                    venv_python, "-m", "yt_dlp", url,
                    "--no-playlist", # Critical: Prevent re-interpreting individual URL
                    "--progress",
                    "--progress-template", "download-status:%(progress)j",
                    "--no-warnings",
                    "--no-abort-on-error",  # Continue on errors
                    "--ignore-errors",  # Skip unavailable videos in playlists
                    "-o", temp_output_template,
                    # YouTube-specific options
                    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "--referer", "https://www.youtube.com/"
                ]
            else:
                # Fallback to system yt-dlp
                command = [
                    "yt-dlp", url,
                    "--no-playlist", # Critical: Prevent re-interpreting individual URL
                    "--progress",
                    "--progress-template", "download-status:%(progress)j",
                    "--no-warnings",
                    "--no-abort-on-error",  # Continue on errors
                    "--ignore-errors",  # Skip unavailable videos in playlists
                    "-o", temp_output_template,
                    # YouTube-specific options
                    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "--referer", "https://www.youtube.com/"
                ]
            
            # Add cookies support for age-restricted content
            # Try to use browser cookies if available
            if "youtube.com" in url or "youtu.be" in url:
                # Try Chrome cookies first, then Firefox, then Edge
                for browser in ["chrome", "firefox", "edge"]:
                    try:
                        # Test if browser cookies are accessible
                        if os.path.exists(venv_python):
                            test_cmd = [venv_python, "-m", "yt_dlp", "--cookies-from-browser", browser, "--simulate", "--quiet"]
                        else:
                            test_cmd = ["yt-dlp", "--cookies-from-browser", browser, "--simulate", "--quiet"]
                        test_result = subprocess.run(test_cmd, capture_output=True, timeout=5)
                        if test_result.returncode == 0:
                            command.extend(["--cookies-from-browser", browser])
                            print(f"INFO: Using {browser} cookies for YouTube")
                            break
                    except:
                        continue

            # Determine yt-dlp Format Flags with robust fallbacks
            if tiktok_video_only_special_case:
                command.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4"])
                needs_audio_removal_post_dl = True
                print(f"INFO: ({os.path.basename(url[:50])}...): TikTok+VideoOnly. Downloading with audio first.")
            elif selected_format == "mp3":
                 # More robust MP3 format selection
                 command.extend(["-x", "--audio-format", "mp3", "-f", "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best", "--audio-quality", "0"])
            else: # Standard MP4
                 if is_video_only_general_flag and not is_tiktok_url:
                     # Video only with fallbacks
                     command.extend(["-f", "bestvideo[ext=mp4]/bestvideo[ext=webm]/bestvideo", "--recode-video", "mp4"])
                 else:
                     # Best quality with multiple fallbacks for YouTube
                     command.extend([
                         "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
                         "--merge-output-format", "mp4"
                     ])

            # Execute yt-dlp and Parse Output
            try:
                process = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            text=True, encoding='utf-8', errors='replace', bufsize=1,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 )
                self.current_process = process  # Store for potential abort
                current_status_msg = f"{progress_prefix} Downloading..."
                self.update_status(current_status_msg)
                captured_title_from_progress = None

                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        # Check abort flag during download
                        if self.abort_flag.is_set():
                            process.terminate()
                            break
                            
                        line = line.strip()
                        if not line: continue
                        if line.startswith("download-status:"):
                             try:
                                 json_str = line.split(":", 1)[1]
                                 progress_data = json.loads(json_str)
                                 status = progress_data.get('status', 'N/A')
                                 dl_filename_progress = progress_data.get('filename')
                                 info_dict = progress_data.get('info_dict', {})
                                 if info_dict and not captured_title_from_progress:
                                     captured_title_from_progress = info_dict.get('title')

                                 if status == 'finished' and dl_filename_progress and not initial_download_path:
                                     initial_download_path = dl_filename_progress
                                     print(f"DEBUG: Captured initial_download_path='{initial_download_path}' on finish.")

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
                             except json.JSONDecodeError: pass
                             except Exception as e: print(f"Error parsing progress line: {line} | Error: {e}")

                process.stdout.close() if process.stdout else None
                
                # Check if process was terminated due to abort
                if self.abort_flag.is_set():
                    return_code = -1
                    stderr_output = "Download aborted by user"
                else:
                    return_code = process.wait()
                    stderr_output = process.stderr.read() if process.stderr else ""
                
                process.stderr.close() if process.stderr else None
                stderr_info = stderr_output

                # Check download result
                # For MP3, yt-dlp converts and deletes the original, so we need to check for the MP3 file
                if return_code == 0 and initial_download_path:
                    if selected_format == "mp3":
                        # For MP3, check if the converted file exists
                        base_path = os.path.splitext(initial_download_path)[0]
                        mp3_path = base_path + ".mp3"
                        if os.path.exists(mp3_path):
                            yt_dlp_success = True
                            initial_download_path = mp3_path  # Update to point to the actual MP3
                            print(f"DEBUG: MP3 conversion successful, file at: {mp3_path}")
                        else:
                            yt_dlp_success = False
                            print(f"DEBUG: MP3 file not found after conversion: {mp3_path}")
                    elif os.path.exists(initial_download_path):
                        yt_dlp_success = True
                    else:
                        yt_dlp_success = False
                        print(f"DEBUG: Download file not found: {initial_download_path}")
                    
                    if yt_dlp_success:
                        self.update_status(f"{progress_prefix} Download successful.")

                    # Get Base Title
                    ffprobe_title_cmd = [ ffprobe_path if ffprobe_path else "ffprobe", "-v", "error",
                                          "-show_entries", "format_tags=title", "-of", "default=noprint_wrappers=1:nokey=1",
                                          initial_download_path]
                    try:
                        title_proc = subprocess.run(ffprobe_title_cmd, capture_output=True, text=True, check=False,
                                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        if title_proc.returncode == 0 and title_proc.stdout.strip():
                            base_title = title_proc.stdout.strip()
                            print(f"DEBUG: Got base_title from ffprobe: '{base_title}'")
                        elif captured_title_from_progress:
                            base_title = captured_title_from_progress
                            print(f"DEBUG: Using base_title from yt-dlp progress: '{base_title}'")
                        else:
                            base_title, _ = os.path.splitext(os.path.basename(temp_output_template))
                            base_title = base_title.replace(f"TEMP_DOWNLOAD_{unique_suffix.strip('_')}", "Untitled_Video")
                            print(f"DEBUG: Fallback base_title from temp template: '{base_title}'")
                    except Exception as e:
                         print(f"Warning: Error getting title via ffprobe: {e}. Falling back.")
                         if captured_title_from_progress: base_title = captured_title_from_progress
                         else: base_title, _ = os.path.splitext(os.path.basename(temp_output_template)); base_title = base_title.replace(f"TEMP_DOWNLOAD_{unique_suffix.strip('_')}", "Untitled_Video")

                    base_title = re.sub(r'[\\/*?:"<>|]', '', base_title).strip()
                    if not base_title: base_title = "Untitled_Download"
                    unique_base_title = f"{base_title}{unique_suffix}"
                    print(f"DEBUG: Final unique base title: '{unique_base_title}'")

                else: # Download failed
                    yt_dlp_success = False
                    
                if not yt_dlp_success:
                    # Process failed download
                    error_lines = stderr_info.strip().split('\n')
                    specific_error = f"yt-dlp failed (code {return_code})"
                    error_details = []
                    
                    # Collect all ERROR and WARNING lines for better diagnostics
                    for err_line in error_lines:
                        if "ERROR:" in err_line or "WARNING:" in err_line:
                            error_details.append(err_line.strip())
                        if err_line.strip().startswith("ERROR:"):
                            specific_error = err_line.strip()[6:].strip()
                    
                    # Check for common YouTube-specific errors
                    if "Sign in to confirm" in stderr_info:
                        specific_error = "Video is age-restricted. Consider using browser cookies."
                    elif "Video unavailable" in stderr_info:
                        specific_error = "Video is unavailable or has been removed."
                    elif "429" in stderr_info or "Too Many Requests" in stderr_info:
                        specific_error = "YouTube rate limit hit. Try again later."
                    elif "private video" in stderr_info.lower():
                        specific_error = "Video is private and cannot be downloaded."
                    
                    final_msg = f"{progress_prefix} Download Failed: {specific_error}"
                    print(f"yt-dlp Error Log ({url}):\n{stderr_info}")
                    if error_details:
                        print(f"Detailed errors:\n" + "\n".join(error_details))
                    self.update_status(final_msg)
                    
                    # Clean up any temp files that might exist
                    # For MP3, clean up the temp pattern files
                    if selected_format == "mp3" and temp_output_template:
                        base_pattern = os.path.splitext(temp_output_template)[0]
                        for ext in ['.mp3', '.m4a', '.webm', '.opus']:
                            temp_file = base_pattern + ext
                            if os.path.exists(temp_file):
                                try: 
                                    os.remove(temp_file)
                                    print(f"Cleaned up failed temp file: {temp_file}")
                                except OSError as e: 
                                    print(f"Warning: Could not delete temp file: {e}")
                    elif initial_download_path and os.path.exists(initial_download_path):
                        try: 
                            os.remove(initial_download_path)
                            print(f"Cleaned up failed download: {initial_download_path}")
                        except OSError as e: 
                            print(f"Warning: Could not delete failed download temp file: {e}")
                    continue

            except FileNotFoundError: self.update_status(f"{progress_prefix} Error: yt-dlp command not found!"); self.root.after(0, self.enable_download_buttons); return
            except Exception as e: self.update_status(f"{progress_prefix} Download Error: {e}"); yt_dlp_success = False; continue


            # MP3 file path is already updated in the success check above, no need to search again
            
            # Verify downloaded file
            if yt_dlp_success and initial_download_path:
                if os.path.exists(initial_download_path):
                    file_size = os.path.getsize(initial_download_path)
                    if file_size < 1024:  # Less than 1KB is suspicious
                        print(f"WARNING: Downloaded file is suspiciously small ({file_size} bytes)")
                        yt_dlp_success = False
                        specific_error = "Downloaded file is too small, likely corrupted"
                    else:
                        print(f"INFO: Downloaded file verified: {initial_download_path} ({file_size / (1024*1024):.2f} MB)")
                else:
                    print(f"ERROR: Expected download file not found: {initial_download_path}")
                    yt_dlp_success = False
                    specific_error = "Downloaded file not found"
            
            # Proceed only if download succeeded
            if not yt_dlp_success or not initial_download_path or not unique_base_title:
                self.update_status(f"{progress_prefix} Skipping post-processing due to download issue.")
                if initial_download_path and os.path.exists(initial_download_path):
                    try: os.remove(initial_download_path)
                    except OSError: pass
                continue

            # --- Post-Download Processing ---
            current_file_path = initial_download_path
            processing_error = False
            re_encoding_occurred = False

            intermediate_output_base = f"{unique_base_title}{no_audio_tag}{ar_tag}{time_tag}"
            intermediate_output_path = os.path.join(path, f"{intermediate_output_base}{final_extension}")
            print(f"DEBUG: Intermediate Output Base planned: {intermediate_output_base}")


            # --- Stage 1.5: Remove Audio (if TikTok Video-Only case) ---
            if self.abort_flag.is_set():
                processing_error = True
                self.update_status(f"{progress_prefix} Aborted")
            elif needs_audio_removal_post_dl and not processing_error:
                self.update_status(f"{progress_prefix} Removing audio track...")
                output_noaudio_path = os.path.join(path, f"{unique_base_title}_TEMP_NOAUDIO{final_extension}")
                ffmpeg_an_command = [
                    ffmpeg_path if ffmpeg_path else "ffmpeg",
                    "-hide_banner", "-loglevel", "error",
                    "-i", current_file_path, "-c:v", "copy", "-an", "-map", "0:v:0?",
                    output_noaudio_path
                ]
                try:
                    print(f"Running FFmpeg Remove Audio: {' '.join(ffmpeg_an_command)}")
                    an_proc = subprocess.run(
                        ffmpeg_an_command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    print(f"FFmpeg Remove Audio Output:\n{an_proc.stderr}")
                    self.update_status(f"{progress_prefix} Audio removal successful.")
                    try:
                        print(f"DEBUG: Removing '{current_file_path}' after audio removal.")
                        os.remove(current_file_path)
                    except OSError as e:
                        print(f"Warning: Failed to remove temp file '{current_file_path}': {e}")
                    current_file_path = output_noaudio_path
                    print(f"DEBUG: current_file_path is now '{current_file_path}'")
                except subprocess.CalledProcessError as e:
                    print(f"Error during FFmpeg Audio Removal:\nStderr:\n{e.stderr}")
                    self.update_status(f"{progress_prefix} Error removing audio.")
                    processing_error = True
                    if os.path.exists(output_noaudio_path):
                        try:
                            os.remove(output_noaudio_path)
                            print(f"Cleaned up intermediate file: {output_noaudio_path}")
                        except OSError as clean_e:
                            print(f"Warning: Could not remove intermediate file '{output_noaudio_path}' during audio removal error cleanup: {clean_e}")
                except Exception as e:
                    print(f"Unexpected error during FFmpeg audio removal: {e}")
                    self.update_status(f"{progress_prefix} Error removing audio.")
                    processing_error = True
                    if os.path.exists(output_noaudio_path):
                        try:
                            os.remove(output_noaudio_path)
                            print(f"Cleaned up intermediate file: {output_noaudio_path}")
                        except OSError as clean_e:
                            print(f"Warning: Could not remove intermediate file '{output_noaudio_path}' during audio removal error cleanup: {clean_e}")


            # --- Stage 2: Aspect Ratio Adjustment ---
            if self.abort_flag.is_set():
                processing_error = True
                self.update_status(f"{progress_prefix} Aborted")
            elif is_adjusting_ar and not processing_error:
                self.update_status(f"{progress_prefix} Adjusting Aspect Ratio to {aspect_ratio_selection}...")
                width, height = get_video_dimensions(current_file_path)
                output_ar_path = os.path.join(path, f"{unique_base_title}_TEMP_AR{final_extension}")  # Define path outside try/except
                if width and height:
                    target_ar_val = parse_aspect_ratio(aspect_ratio_selection)
                    source_ar_val = width / height
                    tolerance = 0.01
                    ffmpeg_ar_command = None
                    needs_ar_processing = True

                    if abs(source_ar_val - target_ar_val) < tolerance:
                        self.update_status(f"{progress_prefix} Source AR matches target. Skipping.")
                        needs_ar_processing = False
                    else:
                        common_opts = [
                            ffmpeg_path if ffmpeg_path else "ffmpeg",
                            "-hide_banner", "-loglevel", "error",
                            "-i", current_file_path
                        ]
                        if source_ar_val > target_ar_val:
                            # Crop to target aspect ratio
                            filter_vf = f"crop=w=ih*{target_ar_val:.4f}:h=ih,scale=trunc(iw/2)*2:trunc(ih/2)*2"
                        else:
                            # Pad with black bars to target ratio
                            filter_vf = f"pad=w=ih*{target_ar_val:.4f}:h=ih:x=(ow-iw)/2:y=0:color=black,scale=trunc(iw/2)*2:trunc(ih/2)*2"
                        ffmpeg_ar_command = common_opts + ["-vf", filter_vf]
                        if not needs_audio_removal_post_dl:
                            ffmpeg_ar_command.extend(["-c:a", "copy"])
                        ffmpeg_ar_command.extend(["-map", "0", "-preset", "fast", output_ar_path])

                    if ffmpeg_ar_command and needs_ar_processing:
                        try:
                            print(f"Running FFmpeg AR: {' '.join(ffmpeg_ar_command)}")
                            ar_proc = subprocess.run(
                                ffmpeg_ar_command,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                            print(f"FFmpeg AR Output:\n{ar_proc.stderr}")
                            self.update_status(f"{progress_prefix} Aspect Ratio adjusted.")
                            re_encoding_occurred = True
                            try:
                                print(f"DEBUG: Removing '{current_file_path}' after AR adjust.")
                                os.remove(current_file_path)
                            except OSError as e:
                                print(f"Warning: Failed to remove temp file '{current_file_path}': {e}")
                            current_file_path = output_ar_path
                            print(f"DEBUG: current_file_path is now '{current_file_path}'")
                        except subprocess.CalledProcessError as e:
                            print(f"Error during FFmpeg AR adjustment:\nStderr:\n{e.stderr}")
                            self.update_status(f"{progress_prefix} Error adjusting AR.")
                            processing_error = True
                            if os.path.exists(output_ar_path):
                                try:
                                    os.remove(output_ar_path)
                                    print(f"Cleaned up intermediate file: {output_ar_path}")
                                except OSError as clean_e:
                                    print(f"Warning: Could not remove intermediate file '{output_ar_path}' during AR error cleanup: {clean_e}")
                        except Exception as e:
                            print(f"Unexpected error during FFmpeg AR adjustment: {e}")
                            self.update_status(f"{progress_prefix} Error adjusting AR.")
                            processing_error = True
                            if os.path.exists(output_ar_path):
                                try:
                                    os.remove(output_ar_path)
                                    print(f"Cleaned up intermediate file: {output_ar_path}")
                                except OSError as clean_e:
                                    print(f"Warning: Could not remove intermediate file '{output_ar_path}' during AR error cleanup: {clean_e}")
                else:
                    self.update_status(f"{progress_prefix} Warning: Could not get dimensions. Skipping AR adjustment.")


            # --- Stage 3: Time Cutting ---
            if self.abort_flag.is_set():
                processing_error = True
                self.update_status(f"{progress_prefix} Aborted")
            elif is_cutting and not processing_error:
                self.update_status(f"{progress_prefix} Cutting time range...")
                start_sec, end_sec = time_range
                output_cut_path = os.path.join(path, f"{unique_base_title}_TEMP_CUT{final_extension}")  # Define path outside try/except
                ffmpeg_cut_command = [
                    ffmpeg_path if ffmpeg_path else "ffmpeg", "-hide_banner", "-loglevel", "warning",
                    "-i", current_file_path,
                    "-ss", str(start_sec),
                    "-to", str(end_sec),
                    "-map", "0",
                    "-avoid_negative_ts", "make_zero",
                    "-preset", "fast",
                    *(["-c", "copy"] if not re_encoding_occurred else []),
                    output_cut_path
                ]
                try:
                    print(f"Running FFmpeg Cut: {' '.join(ffmpeg_cut_command)}")
                    cut_proc = subprocess.run(
                        ffmpeg_cut_command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    print(f"FFmpeg Cut Output:\n{cut_proc.stderr}")
                    self.update_status(f"{progress_prefix} Time cutting successful.")
                    if "-c" not in ffmpeg_cut_command:
                        re_encoding_occurred = True
                    try:
                        print(f"DEBUG: Removing '{current_file_path}' after cut.")
                        os.remove(current_file_path)
                    except OSError as e:
                        print(f"Warning: Failed to remove temp file '{current_file_path}': {e}")
                    current_file_path = output_cut_path
                    print(f"DEBUG: current_file_path is now '{current_file_path}'")
                except subprocess.CalledProcessError as e:
                    print(f"Error during FFmpeg time cutting:\nStderr:\n{e.stderr}")
                    self.update_status(f"{progress_prefix} Error cutting time.")
                    processing_error = True
                    if os.path.exists(output_cut_path):
                        try:
                            os.remove(output_cut_path)
                            print(f"Cleaned up intermediate file: {output_cut_path}")
                        except OSError as clean_e:
                            print(f"Warning: Could not remove intermediate file '{output_cut_path}' during cut error cleanup: {clean_e}")
                except Exception as e:
                    print(f"Unexpected error during FFmpeg time cutting: {e}")
                    self.update_status(f"{progress_prefix} Error cutting time.")
                    processing_error = True
                    if os.path.exists(output_cut_path):
                        try:
                            os.remove(output_cut_path)
                            print(f"Cleaned up intermediate file: {output_cut_path}")
                        except OSError as clean_e:
                            print(f"Warning: Could not remove intermediate file '{output_cut_path}' during cut error cleanup: {clean_e}")


            # --- Stage 4: Chopping into Intervals ---
            if self.abort_flag.is_set():
                processing_error = True
                self.update_status(f"{progress_prefix} Aborted")
            elif is_chopping and not processing_error:
                self.update_status(f"{progress_prefix} Preparing to chop into {chop_interval_seconds}s intervals...")
                source_duration = get_video_duration(current_file_path)

                if source_duration is None:
                    self.update_status(f"{progress_prefix} Error: Could not get duration for chopping. Skipping chop.")
                    processing_error = True
                elif source_duration <= 0:
                    self.update_status(f"{progress_prefix} Error: Source duration is zero or negative. Skipping chop.")
                    processing_error = True
                else:
                    num_segments = math.ceil(source_duration / chop_interval_seconds)
                    print(f"DEBUG: Chopping '{current_file_path}' (Duration: {source_duration:.2f}s) into {num_segments} segments of ~{chop_interval_seconds}s")

                    segment_success = True
                    processed_segments = 0
                    for i in range(num_segments):
                        segment_start_time = i * chop_interval_seconds
                        segment_duration = min(chop_interval_seconds, source_duration - segment_start_time)
                        if segment_duration < 0.01:
                            break

                        processed_segments += 1
                        segment_num = i + 1
                        segment_output_path = os.path.join(path, f"{intermediate_output_base}_part_{segment_num}{final_extension}")
                        self.update_status(f"{progress_prefix} Chopping segment {segment_num}/{num_segments}...")

                        ffmpeg_chop_command = [
                            ffmpeg_path if ffmpeg_path else "ffmpeg", "-hide_banner", "-loglevel", "warning",
                            "-i", current_file_path,
                            "-ss", str(segment_start_time),
                            "-t", str(segment_duration),
                            "-map", "0",
                            "-avoid_negative_ts", "make_zero",
                            "-preset", "fast",
                            *(["-c", "copy"] if not re_encoding_occurred else []),
                            segment_output_path
                        ]

                        try:
                            print(f"Running FFmpeg Chop (Segment {segment_num}): {' '.join(ffmpeg_chop_command)}")
                            chop_proc = subprocess.run(
                                ffmpeg_chop_command,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                            if chop_proc.stderr and chop_proc.stderr.strip():
                                print(f"FFmpeg Chop Output (Segment {segment_num}):\n{chop_proc.stderr}")
                        except subprocess.CalledProcessError as e:
                            print(f"Error chopping segment {segment_num} for '{os.path.basename(current_file_path)}':")
                            print(f"Command: {' '.join(e.cmd)}")
                            print(f"Stderr:\n{e.stderr}")
                            self.update_status(f"{progress_prefix} Error chopping segment {segment_num}.")
                            segment_success = False
                            if os.path.exists(segment_output_path):
                                try:
                                    os.remove(segment_output_path)
                                    print(f"Cleaned up failed segment file: {segment_output_path}")
                                except OSError as clean_e:
                                    print(f"Warning: Could not remove failed segment file '{segment_output_path}' during chop error cleanup: {clean_e}")
                            break
                        except Exception as e:
                            print(f"Unexpected error chopping segment {segment_num}: {e}")
                            self.update_status(f"{progress_prefix} Error chopping segment {segment_num}.")
                            segment_success = False
                            if os.path.exists(segment_output_path):
                                try:
                                    os.remove(segment_output_path)
                                    print(f"Cleaned up failed segment file: {segment_output_path}")
                                except OSError as clean_e:
                                    print(f"Warning: Could not remove failed segment file '{segment_output_path}' during chop error cleanup: {clean_e}")
                            break

                    if segment_success and processed_segments > 0:
                        self.update_status(f"{progress_prefix} Successfully chopped into {processed_segments} segments.")
                        try:
                            print(f"DEBUG: Removing '{current_file_path}' after successful chopping.")
                            os.remove(current_file_path)
                            current_file_path = None
                        except OSError as e:
                            print(f"Warning: Failed to remove source file '{current_file_path}' after chopping: {e}")
                        processing_error = False
                        self.root.after(0, self.remove_url_from_gui_and_internal, url)
                        continue  # Go to the next URL (chopping is the final step)
                    else:
                        if processed_segments == 0 and segment_success:
                            self.update_status(f"{progress_prefix} No segments generated (source too short?). Keeping original.")
                        else:
                            self.update_status(f"{progress_prefix} Chopping failed. Keeping intermediate file.")
                            processing_error = True


            # --- Stage 5: Finalization (Only if NOT chopping, or if chopping failed/skipped) ---
            if not processing_error and current_file_path:
                if current_file_path != intermediate_output_path:
                    try:
                        print(f"Finalizing: Renaming '{current_file_path}' to '{intermediate_output_path}'")
                        os.makedirs(os.path.dirname(intermediate_output_path), exist_ok=True)
                        if os.path.exists(intermediate_output_path): print(f"Warning: Final target path already exists, overwriting: {intermediate_output_path}")
                        os.rename(current_file_path, intermediate_output_path)
                        self.update_status(f"{progress_prefix} Success: {os.path.basename(intermediate_output_path)}")
                        self.root.after(0, self.remove_url_from_gui_and_internal, url)
                    except OSError as e:
                        print(f"Error renaming final file: {e}"); self.update_status(f"{progress_prefix} Error finalizing file (rename failed)."); processing_error = True
                else: # current_file_path is already the intended final path
                    if os.path.exists(intermediate_output_path):
                         self.update_status(f"{progress_prefix} Success: {os.path.basename(intermediate_output_path)}")
                         self.root.after(0, self.remove_url_from_gui_and_internal, url)
                    else:
                         print(f"Error: Final file path '{intermediate_output_path}' does not exist, but was expected."); self.update_status(f"{progress_prefix} Error finalizing file (missing)."); processing_error = True


            # --- Cleanup on Error during post-processing ---
            if processing_error and current_file_path and os.path.exists(current_file_path):
                self.update_status(f"{progress_prefix} Failed processing '{url[:70]}...'. Check console.")
                print(f"Keeping intermediate file due to error: {current_file_path}")
                try:
                    error_filename = os.path.join(path, f"{unique_base_title}_PROCESSING_ERROR{final_extension}")
                    print(f"Attempting to rename failed intermediate to: {error_filename}")
                    # Avoid overwriting an existing error file from a previous run if possible
                    if os.path.exists(error_filename):
                        error_filename = os.path.join(path, f"{unique_base_title}_PROCESSING_ERROR_{random.randint(100,999)}{final_extension}")
                    os.rename(current_file_path, error_filename)
                except OSError as rename_err:
                    print(f"Could not rename errored intermediate file: {rename_err}")
            elif processing_error: # Error occurred, but current_file_path is None (e.g., chop duration failed)
                self.update_status(f"{progress_prefix} Failed processing '{url[:70]}...'. No intermediate file to keep.")


        # --- Loop finished ---
        self.current_process = None  # Clear process reference
        self.root.after(0, self.enable_download_buttons)
        remaining_items = self.queue_listbox.get(0, tk.END)
        if not remaining_items:
            self.update_status("Download queue finished. All items processed.")
        else:
             failed_count = len(remaining_items)
             successful_count = initial_queue_size - failed_count # Approximate success count
             self.update_status(f"Queue finished. {successful_count} item(s) likely processed, {failed_count} failed or skipped.")


    # GUI Update Helper
    def remove_url_from_gui_and_internal(self, url):
        try:
            if self.root.winfo_exists():
                items = list(self.queue_listbox.get(0, tk.END))
                if url in items:
                    index = items.index(url)
                    self.queue_listbox.delete(index)
        except ValueError: print(f"Warning: URL {url} not found in GUI for removal.")
        except Exception as e: print(f"Error removing URL from GUI: {e}")


    # Combined Button Enabling
    def enable_download_button_and_add(self):
        """Enables both Download and Add buttons."""
        try:
            if self.root.winfo_exists():
                self.download_button.config(state=tk.NORMAL)
                if not self.is_adding_to_queue: # Only enable if not currently adding
                    self.add_button.config(state=tk.NORMAL)
        except tk.TclError: pass

    # Modified on_closing
    def on_closing(self):
        """Called when the user tries to close the window."""
        current_path = self.download_path.get()
        if isinstance(current_path, str) and os.path.isdir(current_path):
            self.settings["download_path"] = current_path
        else:
             print(f"Warning: Download path invalid on close. Saving script directory.")
             self.settings["download_path"] = SCRIPT_DIR

        self.settings["video_only"] = self.video_only_var.get()
        self.settings["enable_cut"] = self.enable_cut_var.get()
        self.settings["start_time"] = self.start_time_var.get()
        self.settings["end_time"] = self.end_time_var.get()
        self.settings["aspect_ratio"] = self.aspect_ratio_var.get()
        self.settings["enable_chop"] = self.enable_chop_var.get()
        self.settings["chop_interval"] = self.chop_interval_var.get()

        save_settings(self.settings)
        print("Settings saved. Exiting.")
        self.root.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    # Check for yt-dlp on startup
    try:
        cmd_where = "where" if os.name == 'nt' else "which"
        subprocess.run([cmd_where, "yt-dlp"], capture_output=True, text=True, check=True, shell=(os.name == 'nt'), creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        print("INFO: Found yt-dlp.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: yt-dlp command not found in system PATH.")
        root_temp = tk.Tk()
        root_temp.withdraw()
        messagebox.showerror("Missing Dependency", "yt-dlp was not found in your system's PATH.\n\nPlease install yt-dlp and ensure it's accessible from the command line.\n\nThe application will close now.")
        root_temp.destroy()
        sys.exit(1)

    root = tk.Tk()
    app = MediaDownloaderApp(root)
    root.mainloop()
