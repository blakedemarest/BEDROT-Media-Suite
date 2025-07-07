# Bedrot Productions - Media Tool Suite

This suite provides a collection of Python-based tools for downloading, remixing, and generating video content, all managed through a central graphical user interface (GUI) launcher (`launcher.py`).

## Directory Structure

The codebase is organized as follows:

* `launcher.py`: The main application entry point (run this file).
* `readme.md`: This documentation file.
* `requirements.txt`: Lists the required Python libraries.
* `config/`: Contains all JSON configuration files for the tools.
    * `yt_downloader_gui_settings.json`: Settings for the Media Downloader.
    * `video_remixer_settings.json`: Settings for the Snippet Remixer.
    * `combined_random_config.json`: Settings for the Random Slideshow Generator.
    * `config.json`: Settings for the Slideshow Editor.
* `src/`: Contains the core Python source code for the tools.
    * `media_download_app.py`: Media Downloader tool.
    * `snippet_remixer.py`: Snippet Remixer tool.
    * `random_slideshow.py`: Random Slideshow Generator tool.
    * `slideshow_editor.py`: A separate tool for creating single slideshows.
* `tools/`: Contains utility scripts.
    * `xyimagescaler.py`: A simple image scaling/cropping utility.

**Core Components:**

1.  **Launcher (`launcher.py`):** A Tkinter GUI to run and monitor the other tools located in the `src/` directory.
2.  **Media Downloader (`src/media_download_app.py`):** Downloads video/audio using `yt-dlp` with post-processing options. Uses settings from `config/yt_downloader_gui_settings.json`.
3.  **Snippet Remixer (`src/snippet_remixer.py`):** Creates new videos by randomly combining short snippets. Uses settings from `config/video_remixer_settings.json`.
4.  **Random Slideshow Generator (`src/random_slideshow.py`):** Continuously generates short, randomized video slideshows. Uses settings from `config/combined_random_config.json`.

---

## 1. The Launcher (`launcher.py`)

This application, run from the project root directory, provides the main interface to launch and monitor the media tools found in the `src/` directory.

### Launcher Features

* **Tabbed Interface:** Uses a `ttk.Notebook` to provide separate controls for launching each target script.
* **Simple Launch Buttons:** Dedicated buttons on each tab to run the corresponding script.
* **Independent Processes:** Each script is launched as a separate process using Python's `subprocess` module.
* **Relative Pathing:** Automatically locates the scripts within the `src/` directory relative to its own position. No manual path configuration is needed.
* **Real-time Log Output:** Captures both standard output (`stdout`) and standard error (`stderr`) streams from the launched scripts.
* **Timestamped Logging:** Displays the captured output in a shared, scrollable text area, with each line prefixed by a timestamp.
* **Background Execution:** Script execution and output streaming are handled in background threads (`threading`) to keep the main GUI responsive.
* **Status Indicators:** Each tab displays the current status (Idle, Running, Finished Successfully, Finished with Errors) of the script it controls.
* **Process Management:** Tracks the processes of actively running scripts.
* **Graceful Shutdown:** When closing the launcher window, it checks for active script processes, prompts the user for confirmation, and attempts to terminate (`terminate`/`kill`) any running scripts before exiting.
* **Log Clearing:** A button is provided to clear the contents of the log display area.
* **Cross-Platform Considerations:** Attempts to use platform-appropriate UI themes and process termination methods.

---

## 2. Installation & Setup (Overall)

Follow these steps to set up the entire suite:

1.  **Python:** Ensure you have Python 3.x installed. Download from [python.org](https://www.python.org/) if needed.
2.  **Clone/Download:** Obtain the project files and navigate to the root project directory (`blakedemarest-bedrot-media-suite.git/`) in your terminal.
3.  **Create Virtual Environment (Recommended):**
    * Navigate to the project root directory.
    * Create a virtual environment: `python -m venv venv`
    * Activate it:
        * Windows: `.\venv\Scripts\activate`
        * macOS/Linux: `source venv/bin/activate`
4.  **Install Python Libraries:** Install all necessary Python packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Tkinter is usually included with Python).*
5.  **Install External Tools (FFmpeg/FFprobe):**
    * Download `ffmpeg` from the official website: [ffmpeg.org](https://ffmpeg.org/download.html). `ffprobe` is typically included.
    * Follow their installation instructions for your operating system.
    * **Crucially, ensure the directory containing the `ffmpeg` and `ffprobe` executables is added to your system's PATH environment variable.** The tools rely on calling these commands directly. You may need to restart your terminal or computer after modifying the PATH.
    * *Alternative (Package Managers):* `sudo apt update && sudo apt install ffmpeg` (Debian/Ubuntu), `brew install ffmpeg` (macOS), `choco install ffmpeg` (Windows - verify PATH).
6.  **Configuration Files:** Settings for each tool (e.g., default folders, options) are stored in `.json` files within the `config/` directory. You can modify these directly if needed, but the tools should also save your preferences there during use.

---

## 3. How to Run

1.  Ensure you have completed all steps in the "Installation & Setup" section, especially activating your virtual environment (if used).
2.  Open your terminal or command prompt.
3.  **Navigate to the root project directory** (the one containing `launcher.py`, `src/`, `config/`, etc.).
4.  Run the launcher application:
    ```bash
    python launcher.py
    ```
5.  The main launcher window will appear with tabs for each tool.

---

## 4. Using the Suite

1.  **Run the Launcher:** Start `launcher.py` from the project root as described above.
2.  **Select a Tool:** Click the tab corresponding to the tool you want to use (e.g., "MP4 downloader/MP3 Converter", "Snippet Remixer", "Random Slideshow").
3.  **Launch the Tool:** Click the "Run..." button on the selected tab. This will open the chosen tool's window.
4.  **Use the Tool:** Interact with the specific tool's GUI as needed (see detailed guides below). Settings are loaded from/saved to the corresponding JSON file in the `config/` directory.
5.  **Monitor Status & Logs:**
    * The "Status:" label on the launcher's tab for that tool will update (Idle, Running, Finished...).
    * The main "Log Output" area at the bottom of the launcher shows timestamped `stdout` and `stderr` messages from all launched scripts. Errors often appear here prefixed with `[stderr]`.
6.  **Launch Multiple Tools:** You can run multiple tools concurrently; their output will be interleaved in the log area.
7.  **Clear Log:** Click the "Clear Log" button in the launcher to empty the log display.
8.  **Close Launcher:** Click the launcher window's close button. If any tools are still running, you will be asked to confirm termination before the launcher exits.

---

## 5. Included Tools - Details

### 5.1 Media Downloader GUI (`src/media_download_app.py`)

Downloads videos/audio using `yt-dlp` with post-processing options.

* **Features:** GUI (Tkinter), URL Queue, MP4/MP3 format, Video-Only option, Time Cutting, Aspect Ratio adjustment, Video Chopping, Persistent Settings (in `config/yt_downloader_gui_settings.json`), Status/Progress updates.
* **Dependencies:** Python, Tkinter, `yt-dlp`, `ffmpeg`, `ffprobe`.
* **Usage Guide:** (Refer to original guide - functionality unchanged)
* **Troubleshooting:** Ensure `yt-dlp`, `ffmpeg`, `ffprobe` are in PATH. Check launcher log for specific errors. Check permissions for the output folder specified in the tool's GUI or `config/yt_downloader_gui_settings.json`.

### 5.2 Video Snippet Remixer (`src/snippet_remixer.py`)

Creates remixes by combining random short snippets from source videos.

* **Features:** GUI (Tkinter), Multi-file input, Output naming control (unique `(n)` suffix), Length definition (Seconds or BPM), Random snippet selection, Intermediate transcoding (`.ts`), Reliable concatenation, Aspect Ratio adjustment, Background processing, Persistent Settings (in `config/video_remixer_settings.json`), Temp file management (in `remixer_temp_snippets` subdirectory).
* **Dependencies:** Python, Tkinter, `ffmpeg`, `ffprobe`.
* **Usage Guide:** (Refer to original guide - functionality unchanged)
* **Troubleshooting:** Ensure `ffmpeg`/`ffprobe` are in PATH. Input videos must be longer than the calculated snippet duration. Check launcher log for `ffmpeg` errors. Temp folder (`remixer_temp_snippets`) should be auto-deleted; check if script crashes. Check permissions for the output folder specified in the tool's GUI or `config/video_remixer_settings.json`.

### 5.3 Random Slideshow Generator (`src/random_slideshow.py`)

Continuously generates short, randomized video slideshows from images.

* **Features:** GUI (PyQt5), Folder selection (input/output), Aspect Ratio options (16:9 Landscape / 9:16 Portrait), Randomized duration/timing, Continuous generation loop, Background processing (QThread), Status updates & count, Persistent Settings (in `config/combined_random_config.json`), Error handling.
* **Dependencies:** Python, `PyQt5`, `MoviePy`, `NumPy`, `Pillow`.
* **Usage Guide:** (Refer to original guide - functionality unchanged)
* **Troubleshooting:** Ensure dependencies are installed (`pip install -r requirements.txt`). Requires valid image files. Processing can be resource-intensive. Check permissions for input/output folders specified in the tool's GUI or `config/combined_random_config.json`.

---

## 6. Other Included Tools

* **Slideshow Editor (`tools/slideshow_editor.py`):** A PyQt5 tool for creating single slideshow videos from dragged-and-dropped images with specific duration and aspect ratio settings. Uses `config/config.json` for output folder history. (Can be launched via the launcher).
* **XY Image Scaler (`tools/xyimagescaler.py`):** A simple Tkinter utility to scale and crop an image to a target width and height (defaults to 1632x2912). This needs to be run separately (`python tools/xyimagescaler.py`).

---

## 7. Overall Troubleshooting

* **Launcher Errors:** Ensure `launcher.py` is run from the project's root directory. If scripts don't launch, check the console for errors related to finding the `src` directory or the scripts within it.
* **Errors Running Tools:** If a tool fails after being launched, check the **"Log Output"** area in the **launcher window**. Errors prefixed with `[stderr]` often indicate problems within the launched tool itself or its dependencies. Common issues include:
    * Missing Python libraries (`pip install -r requirements.txt`).
    * External tools (`ffmpeg`, `ffprobe`, `yt-dlp`) not installed or not found in the system PATH. Re-check PATH configuration.
    * Invalid input provided in the tool's own GUI (e.g., incorrect URL, non-existent folder, invalid time format). Check the relevant `.json` file in `config/` for saved invalid paths.
    * Permissions issues (cannot write to output folder, cannot read input files).
    * Bugs within the specific tool's script in the `src/` directory.
* **Process Termination:** The launcher attempts to stop scripts gracefully, but unresponsive scripts might require manual termination via your OS Task Manager / Activity Monitor.

---

