# Bedrot Productions - Media Tool Suite

This suite provides a collection of Python-based tools for downloading, remixing, and generating video content, all managed through a central graphical user interface (GUI) launcher.

**Core Components:**

1.  **Launcher (`launcher.py`):** A Tkinter GUI to run and monitor the other tools.
2.  **Media Downloader (`media_download_app.py`):** Downloads video/audio using `yt-dlp` with post-processing options (format conversion, cutting, aspect ratio, chopping via FFmpeg).
3.  **Snippet Remixer (`snippet_remixer.py`):** Creates new videos by randomly combining short snippets from multiple source videos (uses FFmpeg).
4.  **Random Slideshow Generator (`random_slideshow.py`):** Continuously generates short, randomized video slideshows from a folder of images (uses PyQt5, MoviePy, Pillow).

---

## 1. The Launcher (`launcher.py`)

This application provides the main interface to launch and monitor the three media tools.

### Launcher Features

* **Tabbed Interface:** Uses a `ttk.Notebook` to provide separate controls for launching each target script.
* **Simple Launch Buttons:** Dedicated buttons on each tab to run the corresponding script.
* **Independent Processes:** Each script is launched as a separate process using Python's `subprocess` module.
* **Real-time Log Output:** Captures both standard output (`stdout`) and standard error (`stderr`) streams from the launched scripts.
* **Timestamped Logging:** Displays the captured output in a shared, scrollable text area, with each line prefixed by a timestamp.
* **Background Execution:** Script execution and output streaming are handled in background threads (`threading`) to keep the main GUI responsive.
* **Status Indicators:** Each tab displays the current status (Idle, Running, Finished Successfully, Finished with Errors) of the script it controls.
* **Process Management:** Tracks the processes of actively running scripts.
* **Graceful Shutdown:** When closing the launcher window, it checks for active script processes, prompts the user for confirmation, and attempts to terminate (`terminate`/`kill`) any running scripts before exiting.
* **Log Clearing:** A button is provided to clear the contents of the log display area.
* **Configurable Paths (Hardcoded):** The paths to the target scripts are defined as constants within the `launcher.py` file.
* **Cross-Platform Considerations:** Attempts to use platform-appropriate UI themes and process termination methods.

---

## 2. Installation & Setup (Overall)

Follow these steps to set up the entire suite:

1.  **Python:** Ensure you have Python 3.x installed. Download from [python.org](https://www.python.org/) if needed.
2.  **Create Virtual Environment (Recommended):**
    * Navigate to the project directory in your terminal.
    * Create a virtual environment: `python -m venv venv`
    * Activate it:
        * Windows: `.\venv\Scripts\activate`
        * macOS/Linux: `source venv/bin/activate`
3.  **Install Python Libraries:** Install all necessary Python packages using pip:
    ```bash
    pip install -U yt-dlp PyQt5 moviepy numpy Pillow
    ```
    *(Note: Tkinter is usually included with Python and does not need separate installation via pip).*
4.  **Install External Tools (FFmpeg/FFprobe):**
    * Download `ffmpeg` from the official website: [ffmpeg.org](https://ffmpeg.org/download.html). `ffprobe` is typically included in the download.
    * Follow their installation instructions for your operating system.
    * **Crucially, ensure the directory containing the `ffmpeg` and `ffprobe` executables is added to your system's PATH environment variable.** All three tools rely on being able to call these commands directly. You may need to restart your terminal or computer after modifying the PATH.
    * *Alternative (Package Managers):* `sudo apt update && sudo apt install ffmpeg` (Debian/Ubuntu), `brew install ffmpeg` (macOS), `choco install ffmpeg` (Windows - verify PATH).
5.  **Configure Launcher Paths:**
    * Open the `launcher.py` script in a text editor.
    * Locate the `SCRIPT_1_PATH`, `SCRIPT_2_PATH`, and `SCRIPT_3_PATH` variables near the top.
    * **Modify these paths** to point to the exact locations where you have saved `media_download_app.py`, `snippet_remixer.py`, and `random_slideshow.py`, respectively. Use raw strings (e.g., `r"C:\Users\..."`) for Windows paths if they contain backslashes.
    ```python
    # --- Configuration ---
    # Script paths (Use raw strings 'r' for Windows paths if needed)
    SCRIPT_1_PATH = r"C:\path\to\your\media_download_app.py"
    SCRIPT_2_PATH = r"C:\path\to\your\snippet_remixer.py"
    SCRIPT_3_PATH = r"C:\path\to\your\random_slideshow.py"
    ```

---

## 3. How to Run

1.  Ensure you have completed all steps in the "Installation & Setup" section, especially activating your virtual environment (if used) and configuring the paths in `launcher.py`.
2.  Open your terminal or command prompt.
3.  Navigate to the directory containing `launcher.py`.
4.  Run the launcher application:
    ```bash
    python launcher.py
    ```
5.  The main launcher window will appear with tabs for each tool.

---

## 4. Using the Suite

1.  **Run the Launcher:** Start `launcher.py` as described above.
2.  **Select a Tool:** Click the tab corresponding to the tool you want to use (e.g., "MP4 downloader/MP3 Converter", "Snippet Remixer", "Random Slideshow").
3.  **Launch the Tool:** Click the "Run..." button on the selected tab. This will open the chosen tool in its own window (or start its process).
4.  **Use the Tool:** Interact with the specific tool's GUI as needed (see detailed guides below).
5.  **Monitor Status & Logs:**
    * The "Status:" label on the launcher's tab for that tool will update (Idle, Running, Finished...).
    * The main "Log Output" area at the bottom of the launcher shows timestamped `stdout` and `stderr` messages from all launched scripts. Errors often appear here prefixed with `[stderr]`.
6.  **Launch Multiple Tools:** You can run multiple tools concurrently; their output will be interleaved in the log area.
7.  **Clear Log:** Click the "Clear Log" button in the launcher to empty the log display.
8.  **Close Launcher:** Click the launcher window's close button. If any tools are still running, you will be asked to confirm termination before the launcher exits.

---

## 5. Included Tools - Details

### 5.1 Media Downloader GUI (`media_download_app.py`)

Downloads videos/audio using `yt-dlp` with post-processing options.

* **Features:** GUI (Tkinter), URL Queue, MP4/MP3 format, Video-Only option, Time Cutting, Aspect Ratio adjustment, Video Chopping, Persistent Settings (`yt_downloader_gui_settings.json`), Status/Progress updates.
* **Dependencies:** Python, Tkinter, `yt-dlp`, `ffmpeg`, `ffprobe`.
* **Usage Guide:**
    1.  **Video URL:** Paste URL, click "Add to Queue".
    2.  **Download Folder:** Browse to select destination.
    3.  **Format Options:** Choose MP4/MP3, optionally check "Video Only".
    4.  **Processing Options:** Enable and configure Time Cut, Aspect Ratio, or Chopping as needed (requires FFmpeg/FFprobe).
    5.  **Download Queue:** View and manage URLs.
    6.  **Action Buttons:** Use "Download Queue", "Clear Selected", "Clear All".
    7.  **Status Bar:** Monitor progress and results within the downloader window. Check launcher log for details.
* **Troubleshooting:** Ensure `yt-dlp`, `ffmpeg`, `ffprobe` are in PATH. Check launcher log for specific `yt-dlp` or `ffmpeg` errors.

### 5.2 Video Snippet Remixer (`snippet_remixer.py`)

Creates remixes by combining random short snippets from source videos.

* **Features:** GUI (Tkinter), Multi-file input, Output naming control (unique `(n)` suffix), Length definition (Seconds or BPM), Random snippet selection, Intermediate transcoding (`.ts`), Reliable concatenation, Aspect Ratio adjustment, Background processing, Persistent Settings (`video_remixer_settings.json`), Temp file management.
* **Dependencies:** Python, Tkinter, `ffmpeg`, `ffprobe`.
* **Usage Guide:**
    1.  **Input Videos:** Browse to add source video files.
    2.  **Output Settings:** Select folder, enter filename, choose final Aspect Ratio ("Original" keeps intermediate 720p).
    3.  **Remix Length:** Choose "Seconds" mode (enter total duration) or "BPM" mode (enter BPM, unit, total units).
    4.  **Generate Remix:** Click to start processing. Monitor status bar and launcher log.
* **Troubleshooting:** Ensure `ffmpeg`/`ffprobe` are in PATH. Input videos must be longer than the calculated snippet duration. Check launcher log for `ffmpeg` errors during cutting or concatenation. Temp folder (`remixer_temp_snippets`) should be auto-deleted; check if script crashes.

### 5.3 Random Slideshow Generator (`random_slideshow.py`)

Continuously generates short, randomized video slideshows from images.

* **Features:** GUI (PyQt5), Folder selection (input/output), Aspect Ratio options (16:9 Landscape / 9:16 Portrait with specific processing), Randomized duration/image timing, Continuous generation loop, Background processing (QThread), Status updates & generation count, Persistent Settings (`combined_random_config.json`), Error handling.
* **Dependencies:** Python, `PyQt5`, `MoviePy`, `NumPy`, `Pillow`.
* **Usage Guide:**
    1.  **Image Folder:** Browse to select folder with source images.
    2.  **Output Folder:** Browse to select destination for MP4 videos.
    3.  **Output Aspect Ratio:** Choose 16:9 (letterboxed) or 9:16 (scaled/cropped).
    4.  **Start/Stop Button:** Toggle the continuous generation process.
    5.  **Status/Generation Labels:** Monitor progress within the slideshow window. Check launcher log for details.
* **Troubleshooting:** Ensure `PyQt5`, `MoviePy`, `NumPy`, `Pillow` are installed. Requires valid image files. Processing can be resource-intensive.

---

## 6. Overall Troubleshooting

* **Launcher "Script not found" Error:** Verify the `SCRIPT_X_PATH` variables in `launcher.py` point to the correct locations of the target `.py` files.
* **Errors Running Tools:** If a tool fails after being launched, check the **"Log Output"** area in the **launcher window**. Errors prefixed with `[stderr]` often indicate problems within the launched tool itself or its dependencies. Common issues include:
    * Missing Python libraries for the specific tool (e.g., `pip install moviepy`).
    * External tools (`ffmpeg`, `ffprobe`, `yt-dlp`) not installed or not found in the system PATH. Re-check PATH configuration.
    * Invalid input provided in the tool's own GUI (e.g., incorrect URL, non-existent folder, invalid time format).
    * Permissions issues (cannot write to output folder, cannot read input files).
    * Bugs within the specific tool's script.
* **Process Termination:** The launcher attempts to stop scripts gracefully when closed, but unresponsive scripts might require manual termination via your OS Task Manager / Activity Monitor.

---
