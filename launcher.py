import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext # Import scrolledtext
import subprocess
import sys
import os
import threading
import time
import datetime # Import datetime for timestamps

# --- Add src to path for core module imports ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))

# --- Import centralized configuration system ---
try:
    from core import get_config_manager, load_environment, resolve_path
    from core.env_loader import get_env_var
    from core.path_utils import get_path_resolver
    
    # Load environment variables
    load_environment()
    
    # Get configuration manager
    config_manager = get_config_manager()
    path_resolver = get_path_resolver()
    
except ImportError as e:
    print(f"Warning: Could not import core configuration system: {e}")
    print("Falling back to hardcoded paths")
    config_manager = None
    path_resolver = None

# --- Configuration ---
def get_script_path(script_key, fallback_path):
    """Get script path with fallback to hardcoded path."""
    if config_manager:
        try:
            return str(config_manager.get_script_path(script_key))
        except Exception as e:
            print(f"Warning: Could not resolve script path for {script_key}: {e}")
    
    # Fallback to hardcoded path
    return os.path.join(SCRIPT_DIR, fallback_path)

# Script paths with environment variable support and fallbacks
SCRIPT_1_PATH = get_script_path('media_download', 'src/media_download_app.py')
SCRIPT_2_PATH = get_script_path('snippet_remixer', 'src/snippet_remixer.py') 
SCRIPT_3_PATH = get_script_path('random_slideshow', 'src/random_slideshow/main.py')
SCRIPT_4_PATH = get_script_path('reel_tracker', 'src/reel_tracker_modular.py')

PYTHON_EXECUTABLE = sys.executable

# --- Globals for Process Management ---
active_processes = []
process_lock = threading.Lock()

# --- Helper Function to Update Log Area Safely ---
def _insert_log_text(log_widget, text):
    """Performs the actual insertion in the main thread. (Internal use)"""
    try:
        log_widget.config(state='normal')
        log_widget.insert(tk.END, text)
        log_widget.config(state='disabled')
        log_widget.see(tk.END) # Auto-scroll
    except tk.TclError:
        # Window might have been destroyed between scheduling and execution
        print("(Log Insert Failed - Window Destroyed?)")
        pass # Ignore if widget is gone

def update_log(log_widget, text):
    """Safely appends timestamped text to the ScrolledText widget from any thread."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Ensure text ends with a newline for proper formatting in the log
    formatted_text = f"[{now}] {text.strip()}\n"
    try:
        # Schedule the GUI update to run in the main thread
        # Use winfo_toplevel() to get the root window reliably for .after()
        if log_widget.winfo_exists(): # Check if widget still exists
            log_widget.winfo_toplevel().after(0, lambda w=log_widget, t=formatted_text: _insert_log_text(w, t))
        else:
             print(f"(Log Skipped - Widget Destroyed) {formatted_text.strip()}")
    except (tk.TclError, AttributeError, RuntimeError) as e:
        # Handle case where the window/widget might be closing/destroyed or root gone
        print(f"(Log Skipped - GUI Update Failed: {e}) {formatted_text.strip()}")

# --- Functions to run the scripts ---
def run_script(script_path, status_label, log_widget): # Added log_widget
    """Runs the specified Python script in a separate thread and logs output."""

    if not os.path.exists(script_path):
        err_msg = f"Script not found:\n{script_path}"
        messagebox.showerror("Error", err_msg)
        if status_label.winfo_exists():
            status_label.config(text="Status: Script not found!")
        update_log(log_widget, f"ERROR: {err_msg}") # Log error
        return

    script_name = os.path.basename(script_path)
    script_dir = os.path.dirname(script_path)

    def task():
        process = None
        try:
            # Log start
            if status_label.winfo_exists():
                status_label.config(text=f"Status: Running {script_name}...")
            update_log(log_widget, f"Attempting to run {script_name}...")
            update_log(log_widget, f"  Command: {PYTHON_EXECUTABLE} -u \"{script_path}\"") # Add -u for unbuffered output
            update_log(log_widget, f"  Directory: {script_dir}")

            # Using '-u' flag with python might help with output buffering issues
            process = subprocess.Popen(
                [PYTHON_EXECUTABLE, "-u", script_path], # Added -u flag
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decodes stdout/stderr as text
                cwd=script_dir, # Set working directory
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0, # For terminating process tree on Win
                start_new_session=True if os.name != 'nt' else False, # For terminating on Unix-like
                bufsize=1, # Line buffered
                universal_newlines=True # Ensures text mode across platforms (redundant with text=True, but doesn't hurt)
            )

            with process_lock:
                active_processes.append(process)
            update_log(log_widget, f"Process {script_name} (PID: {process.pid}) started.")

            # --- Stream Output (More responsive for long scripts) ---
            stdout_lines = []
            stderr_lines = []

            # Non-blocking read using threads
            def stream_reader(pipe, output_list, log_prefix):
                try:
                    # Read line by line until the pipe closes
                    for line in iter(pipe.readline, ''):
                        line_strip = line.strip()
                        if line_strip: # Avoid logging empty lines from readline
                            output_list.append(line_strip)
                            update_log(log_widget, f"[{log_prefix}] {line_strip}")
                except Exception as e:
                     update_log(log_widget, f"ERROR reading {log_prefix} stream: {e}")
                finally:
                    # Ensure pipe is closed even if errors occur during reading
                    try:
                         pipe.close()
                    except Exception as e_close:
                         update_log(log_widget, f"Warning: Error closing {log_prefix} pipe: {e_close}")


            stdout_thread = threading.Thread(target=stream_reader, args=(process.stdout, stdout_lines, "stdout"), daemon=True)
            stderr_thread = threading.Thread(target=stream_reader, args=(process.stderr, stderr_lines, "stderr"), daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            stdout_thread.join() # Wait for stdout reader to finish
            stderr_thread.join() # Wait for stderr reader to finish
            return_code = process.wait() # Wait for process to exit & get code

            # --- End Streaming ---

            update_log(log_widget, f"Process {script_name} (PID: {process.pid}) finished.")

            # Update status label and log final status (check if widget exists)
            if status_label.winfo_exists():
                if return_code == 0:
                    final_msg = f"{script_name} finished successfully (Exit Code: 0)."
                    status_label.config(text=f"Status: {script_name} finished successfully.")
                else:
                    final_msg = f"{script_name} finished with errors (Exit Code: {return_code})."
                    status_label.config(text=f"Status: {script_name} finished with errors (Code: {return_code}).")
                update_log(log_widget, f"--- {final_msg} ---")
            else:
                 update_log(log_widget, f"--- {script_name} finished (Status label gone). Exit Code: {return_code} ---")


        except FileNotFoundError:
            err_msg = f"ERROR: Python executable or script not found.\nPython: {PYTHON_EXECUTABLE}\nScript: {script_path}"
            if status_label.winfo_exists():
                status_label.config(text="Status: Error - File not found!")
            messagebox.showerror("Execution Error", err_msg)
            update_log(log_widget, err_msg)
        except Exception as e:
            err_msg = f"ERROR: An unexpected error occurred while running {script_name}:\n{e}"
            if status_label.winfo_exists():
                status_label.config(text="Status: Runtime error!")
            # Don't show messagebox here as it might block the thread, just log it
            print(f"RUNTIME ERROR: {err_msg}") # Print to console for debugging
            update_log(log_widget, err_msg)
        finally:
            if process:
                with process_lock:
                    if process in active_processes:
                        active_processes.remove(process)
                        # update_log(log_widget, f"Removed process {script_name} (PID: {process.pid}) from tracked list.") # Optional: uncomment for verbose logging

            # Update status if it seems stuck on "Running" and widget exists
            if status_label.winfo_exists():
                current_status = status_label.cget("text")
                if f"Running {script_name}" in current_status:
                    final_status_msg = f"{script_name} ended (check log)."
                    status_label.config(text=f"Status: {final_status_msg}")
                    update_log(log_widget, final_status_msg)


    # Start the task in a daemon thread so it doesn't block exit if main thread finishes
    thread = threading.Thread(target=task)
    thread.daemon = True
    thread.start()

# --- Function to handle window closing (Modified to log termination) ---
def on_closing():
    """Handles window close event, terminates running scripts, logs actions."""
    with process_lock:
        if not active_processes:
            print("No active scripts to terminate. Closing.")
            # Update log only if log_area still exists
            if 'log_area' in globals() and log_area.winfo_exists():
                update_log(log_area, "Exit: No active scripts running.")
            root.destroy()
            return

        if messagebox.askokcancel("Quit", f"There {'is' if len(active_processes) == 1 else 'are'} {len(active_processes)} script(s) potentially running.\nTerminate running scripts and quit?"):
            log_msg = f"Exit: User confirmed quit. Attempting to terminate {len(active_processes)} script(s)..."
            print(log_msg)
            if 'log_area' in globals() and log_area.winfo_exists():
                update_log(log_area, log_msg) # Log action

            processes_to_terminate = list(active_processes) # Copy list before iterating
            terminated_count = 0
            for proc in processes_to_terminate:
                try:
                    # Check if the process is still running
                    if proc.poll() is None:
                        term_msg = f"Terminating process PID: {proc.pid}..."
                        print(term_msg)
                        if 'log_area' in globals() and log_area.winfo_exists():
                           update_log(log_area, term_msg) # Log action
                        proc.terminate() # Send SIGTERM
                        # Optionally wait a very short time and check again, then use kill if needed
                        try:
                            proc.wait(timeout=0.5) # Brief wait
                            print(f"Process PID: {proc.pid} terminated.")
                        except subprocess.TimeoutExpired:
                            print(f"Process PID: {proc.pid} did not terminate quickly, trying kill...")
                            proc.kill() # Force kill if terminate didn't work fast
                        terminated_count += 1
                    else:
                        info_msg = f"Info: Process PID {proc.pid} already finished."
                        print(info_msg)
                        if 'log_area' in globals() and log_area.winfo_exists():
                            update_log(log_area, info_msg)
                except ProcessLookupError:
                    info_msg = f"Info: Process PID: {proc.pid} was not found (already finished/terminated)."
                    print(info_msg)
                    if 'log_area' in globals() and log_area.winfo_exists():
                        update_log(log_area, info_msg)
                except Exception as e:
                    err_log = f"Error terminating/checking process PID {proc.pid}: {e}"
                    print(err_log, file=sys.stderr)
                    if 'log_area' in globals() and log_area.winfo_exists():
                       update_log(log_area, f"ERROR: {err_log}")

            active_processes.clear() # Clear the list after attempting termination
            final_log = f"--- Termination attempt finished ({terminated_count} processes signaled). Closing window. ---"
            print(final_log)
            if 'log_area' in globals() and log_area.winfo_exists():
               update_log(log_area, final_log) # Log final action
            # Give log a moment to update visually before destroying
            root.after(100, root.destroy) # Short delay then destroy
        else:
            cancel_msg = "Quit cancelled by user."
            print(cancel_msg)
            if 'log_area' in globals() and log_area.winfo_exists():
               update_log(log_area, f"Info: {cancel_msg}") # Log cancellation
    # Lock is released automatically here


# --- Function to clear the log ---
def clear_log():
    """Clears the content of the log area."""
    try:
        if log_area.winfo_exists():
            log_area.config(state='normal')
            log_area.delete('1.0', tk.END)
            log_area.config(state='disabled')
            update_log(log_area, "Log cleared.") # Add a confirmation message
    except (tk.TclError, NameError):
        # Handle cases where log_area might not be defined yet or destroyed
        print("Could not clear log - widget destroyed or not initialized?")

# --- GUI Setup ---
root = tk.Tk()
root.title("Script Launcher")
# Increased height slightly for the new tab potentially
root.geometry("600x550") # Adjust size as needed

style = ttk.Style()
try:
    # Attempt to use platform-specific themes for a better look
    if sys.platform == "win32": style.theme_use('vista')
    elif sys.platform == "darwin": style.theme_use('aqua')
    else: style.theme_use('clam') # A decent cross-platform default
except tk.TclError:
    print("Chosen theme not available, using default.")
    # Fallback to default theme if others fail
    try:
       style.theme_use('default')
    except tk.TclError:
        print("Default theme also not available. Styling might be basic.")


# --- Top Frame for Tabs ---
notebook_frame = ttk.Frame(root)
notebook_frame.pack(pady=(10, 0), padx=10, fill="x", expand=False)

notebook = ttk.Notebook(notebook_frame)

# --- Log Area Frame (Defined earlier so it can be passed to buttons) ---
log_frame = ttk.LabelFrame(root, text="Log Output", padding="5")
log_frame.pack(pady=10, padx=10, fill='both', expand=True)

log_area = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD, state='disabled', bd=0) # Set border width if needed
log_area.pack(fill='both', expand=True)


# --- Tab 1: Media Downloader ---
tab1 = ttk.Frame(notebook, padding="10")
notebook.add(tab1, text='MP4 downloader/MP3 Converter')
label1 = ttk.Label(tab1, text="Run the Media Downloader script.")
label1.pack(pady=10)
status_label1 = ttk.Label(tab1, text="Status: Idle", width=50, anchor="w") # Give status labels more width
status_label1.pack(pady=5)
# Button command now passes log_area
run_button1 = ttk.Button(
    tab1,
    text="Run Media Downloader",
    command=lambda: run_script(SCRIPT_1_PATH, status_label1, log_area) # Pass log_area
)
run_button1.pack(pady=20)

# --- Tab 2: Snippet Remixer ---
tab2 = ttk.Frame(notebook, padding="10")
notebook.add(tab2, text='Snippet Remixer')
label2 = ttk.Label(tab2, text="Run the Snippet Remixer script.")
label2.pack(pady=10)
status_label2 = ttk.Label(tab2, text="Status: Idle", width=50, anchor="w")
status_label2.pack(pady=5)
# Button command now passes log_area
run_button2 = ttk.Button(
    tab2,
    text="Run Snippet Remixer",
    command=lambda: run_script(SCRIPT_2_PATH, status_label2, log_area) # Pass log_area
)
run_button2.pack(pady=20)

# --- Tab 3: Random Slideshow ---
tab3 = ttk.Frame(notebook, padding="10")
notebook.add(tab3, text='Random Slideshow') # Set Tab Title
label3 = ttk.Label(tab3, text="Run the Random Slideshow Generator script.")
label3.pack(pady=10)
status_label3 = ttk.Label(tab3, text="Status: Idle", width=50, anchor="w") # Create unique status label
status_label3.pack(pady=5)
# Button command uses SCRIPT_3_PATH and status_label3
run_button3 = ttk.Button(
    tab3,
    text="Run Random Slideshow",
    command=lambda: run_script(SCRIPT_3_PATH, status_label3, log_area) # Pass correct path and status label
)
run_button3.pack(pady=20)

# --- Tab 4: Reel Tracker ---
tab4 = ttk.Frame(notebook, padding="10")
notebook.add(tab4, text='Reel Tracker') # Set Tab Title
label4 = ttk.Label(tab4, text="Run the Reel Tracker application for CSV-based reel management.")
label4.pack(pady=10)
status_label4 = ttk.Label(tab4, text="Status: Idle", width=50, anchor="w") # Create unique status label
status_label4.pack(pady=5)
# Button command uses SCRIPT_4_PATH and status_label4
run_button4 = ttk.Button(
    tab4,
    text="Run Reel Tracker",
    command=lambda: run_script(SCRIPT_4_PATH, status_label4, log_area) # Pass correct path and status label
)
run_button4.pack(pady=20)
# --- END OF REEL TRACKER TAB ---


notebook.pack(expand=True, fill='both') # Pack notebook after adding all tabs


# --- Bottom Frame for Clear Button ---
bottom_frame = ttk.Frame(root)
bottom_frame.pack(pady=(0, 10), padx=10, fill='x', side=tk.BOTTOM) # Pack bottom frame last

clear_button = ttk.Button(bottom_frame, text="Clear Log", command=clear_log)
# Pack to the right side
clear_button.pack(side=tk.RIGHT)

# --- Register the closing handler ---
root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Initial Log Message ---
# Defer initial logging until log_area is definitely created
def initial_log():
    update_log(log_area, "Launcher GUI started.")
    update_log(log_area, f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}") # Add timezone if possible
    update_log(log_area, f"Location: Long Beach, CA") # Adding location context
# Schedule the initial log slightly after mainloop starts
root.after(50, initial_log)

# Start the Tkinter event loop
root.mainloop()