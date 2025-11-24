# -*- coding: utf-8 -*-
"""
Tkinter GUI for the Bedrot Video Splitter module.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from typing import Iterable, List

from .config_manager import ConfigManager
from .drag_drop import create_root, setup_drop_target, DND_AVAILABLE
from .logging_config import setup_logger
from .models import SplitJob
from .split_worker import SplitWorker
from .utils import collect_video_files, ensure_directory, safe_print


class VideoSplitterApp:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BEDROT VIDEO SPLITTER // CLIP ENGINE")
        self.logger = setup_logger()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.get_all()
        self.colors = self.apply_bedrot_theme()

        self.video_files: List[str] = []
        self.list_var = tk.StringVar(value=[])

        self.output_dir_var = tk.StringVar(value=self.settings["output_dir"])
        self.clip_length_var = tk.DoubleVar(value=float(self.settings["clip_length_seconds"]))
        self.jitter_var = tk.IntVar(value=int(self.settings["jitter_percent"]))
        self.min_clip_var = tk.DoubleVar(value=float(self.settings["min_clip_length"]))
        self.per_clip_var = tk.BooleanVar(value=bool(self.settings["per_clip_jitter"]))
        self.reset_ts_var = tk.BooleanVar(value=bool(self.settings["reset_timestamps"]))
        self.overwrite_var = tk.BooleanVar(value=bool(self.settings["overwrite_existing"]))

        self.status_var = tk.StringVar(value="[INFO] Ready")
        self.progress_var = tk.DoubleVar(value=0.0)

        self.worker = SplitWorker(log_callback=self.thread_safe_log, progress_callback=self.thread_safe_progress)
        self.total_jobs = 0

        self._build_ui()
        self._bind_variable_traces()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        colors = self.colors

        source_frame = ttk.LabelFrame(self.root, text="SOURCE VIDEOS")
        source_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        source_frame.columnconfigure(0, weight=1)
        source_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(
            source_frame,
            listvariable=self.list_var,
            selectmode=tk.EXTENDED,
            height=8,
            activestyle="none",
            font=("Segoe UI", 10),
            highlightthickness=1,
            relief=tk.FLAT,
            borderwidth=1,
        )
        listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox = listbox
        self.listbox.configure(
            bg=colors["bg_secondary"],
            fg=colors["fg"],
            selectbackground=colors["accent_cyan"],
            selectforeground="#000000",
            highlightbackground=colors["border"],
            highlightcolor=colors["accent_cyan"],
            insertbackground=colors["accent_cyan"],
        )

        scrollbar = ttk.Scrollbar(source_frame, orient="vertical", command=listbox.yview, style="Bedrot.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns")
        listbox.config(yscrollcommand=scrollbar.set)

        hint_label = ttk.Label(source_frame, text="Drag + drop files or folders here", style="Hint.TLabel")
        hint_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        buttons_frame = ttk.Frame(source_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        for idx in range(4):
            buttons_frame.columnconfigure(idx, weight=1)

        self.btn_add_files = ttk.Button(buttons_frame, text="ADD FILES", command=self.add_files_dialog, style="Secondary.TButton")
        self.btn_add_files.grid(row=0, column=0, padx=2, sticky="ew")
        self.btn_add_folder = ttk.Button(buttons_frame, text="ADD FOLDER", command=self.add_folder_dialog, style="Secondary.TButton")
        self.btn_add_folder.grid(row=0, column=1, padx=2, sticky="ew")
        self.btn_remove_selected = ttk.Button(
            buttons_frame, text="REMOVE SELECTED", command=self.remove_selected, style="Secondary.TButton"
        )
        self.btn_remove_selected.grid(row=0, column=2, padx=2, sticky="ew")
        self.btn_clear_list = ttk.Button(buttons_frame, text="CLEAR LIST", command=self.clear_files, style="Secondary.TButton")
        self.btn_clear_list.grid(row=0, column=3, padx=2, sticky="ew")

        if setup_drop_target(self.listbox, self.handle_drop):
            hint_label.config(text="Drag + drop video files or folders anywhere in this list")
        elif DND_AVAILABLE:
            hint_label.config(text="Drag + drop not supported on this window")

        config_frame = ttk.LabelFrame(self.root, text="OUTPUT & CLIP SETTINGS")
        config_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="Output Folder").grid(row=0, column=0, sticky="w", pady=2, padx=2)
        output_entry = ttk.Entry(config_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(config_frame, text="BROWSE", command=self.choose_output_dir, style="Secondary.TButton").grid(
            row=0, column=2, padx=2, pady=2
        )

        controls_frame = ttk.Frame(config_frame)
        controls_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        for idx in range(4):
            controls_frame.columnconfigure(idx, weight=1)

        ttk.Label(controls_frame, text="Clip Length (s)").grid(row=0, column=0, sticky="w")
        clip_entry = ttk.Spinbox(
            controls_frame,
            from_=1.0,
            to=600.0,
            increment=0.5,
            textvariable=self.clip_length_var,
            width=10,
        )
        clip_entry.grid(row=1, column=0, sticky="ew", padx=2)

        ttk.Label(controls_frame, text="Min Clip (s)").grid(row=0, column=1, sticky="w")
        min_entry = ttk.Spinbox(
            controls_frame,
            from_=0.5,
            to=120.0,
            increment=0.5,
            textvariable=self.min_clip_var,
            width=10,
        )
        min_entry.grid(row=1, column=1, sticky="ew", padx=2)

        ttk.Label(controls_frame, text="Jitter (%)").grid(row=0, column=2, sticky="w")
        jitter_slider = ttk.Scale(
            controls_frame,
            from_=0,
            to=50,
            variable=self.jitter_var,
            command=lambda _evt=None: self._update_jitter_label(),
            style="Bedrot.Horizontal.TScale",
        )
        jitter_slider.grid(row=1, column=2, sticky="ew", padx=2)
        self.jitter_label = ttk.Label(controls_frame, text="", style="Accent.TLabel")
        self.jitter_label.grid(row=2, column=2, sticky="w")
        self._update_jitter_label()

        checkbox_frame = ttk.Frame(config_frame)
        checkbox_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        ttk.Checkbutton(checkbox_frame, text="Randomize each clip", variable=self.per_clip_var, style="Bedrot.TCheckbutton").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(
            checkbox_frame, text="Reset timestamps", variable=self.reset_ts_var, style="Bedrot.TCheckbutton"
        ).grid(row=0, column=1, sticky="w", padx=10)
        ttk.Checkbutton(
            checkbox_frame, text="Overwrite existing files", variable=self.overwrite_var, style="Bedrot.TCheckbutton"
        ).grid(
            row=0, column=2, sticky="w"
        )

        progress_frame = ttk.Frame(self.root)
        progress_frame.grid(row=2, column=0, sticky="ew", padx=10)
        progress_frame.columnconfigure(0, weight=1)
        ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, style="Bedrot.Horizontal.TProgressbar").grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Label(progress_frame, textvariable=self.status_var, style="Status.TLabel").grid(row=1, column=0, sticky="w", pady=4)

        actions_frame = ttk.Frame(self.root)
        actions_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        self.start_button = ttk.Button(actions_frame, text="START SPLITTING", command=self.start_processing, style="Primary.TButton")
        self.stop_button = ttk.Button(
            actions_frame, text="STOP", command=self.stop_processing, state=tk.DISABLED, style="Danger.TButton"
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=4)
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=4)

        log_frame = ttk.LabelFrame(self.root, text="LOG OUTPUT")
        log_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_widget = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            state=tk.DISABLED,
            font=("Consolas", 10),
            background=colors["bg_secondary"],
            foreground=colors["accent_green"],
            insertbackground=colors["accent_cyan"],
            borderwidth=1,
            relief=tk.FLAT,
        )
        self.log_widget.grid(row=0, column=0, sticky="nsew")

        vsb = getattr(self.log_widget, "vbar", None)
        if vsb:
            vsb.configure(style="Bedrot.Vertical.TScrollbar")

    def _bind_variable_traces(self) -> None:
        self.output_dir_var.trace_add("write", lambda *_: self._persist_setting("output_dir", self.output_dir_var.get()))
        self.clip_length_var.trace_add(
            "write", lambda *_: self._persist_setting("clip_length_seconds", float(self.clip_length_var.get()))
        )
        self.min_clip_var.trace_add(
            "write", lambda *_: self._persist_setting("min_clip_length", float(self.min_clip_var.get()))
        )
        self.jitter_var.trace_add("write", lambda *_: self._persist_setting("jitter_percent", float(self.jitter_var.get())))
        self.per_clip_var.trace_add("write", lambda *_: self._persist_setting("per_clip_jitter", bool(self.per_clip_var.get())))
        self.reset_ts_var.trace_add(
            "write", lambda *_: self._persist_setting("reset_timestamps", bool(self.reset_ts_var.get()))
        )
        self.overwrite_var.trace_add(
            "write", lambda *_: self._persist_setting("overwrite_existing", bool(self.overwrite_var.get()))
        )

    def apply_bedrot_theme(self) -> dict:
        """Configure Tkinter styles according to the BEDROT visual guidelines."""
        colors = {
            "bg": "#121212",
            "bg_secondary": "#1a1a1a",
            "bg_tertiary": "#202020",
            "bg_hover": "#252525",
            "bg_active": "#2a2a2a",
            "fg": "#e0e0e0",
            "fg_secondary": "#cccccc",
            "text_muted": "#888888",
            "border": "#404040",
            "accent_green": "#00ff88",
            "accent_cyan": "#00ffff",
            "accent_red": "#ff0066",
        }

        colors["accent_green_hover"] = "#00ffaa"
        colors["accent_green_pressed"] = "#00cc66"
        colors["accent_red_hover"] = "#ff3388"
        colors["accent_red_pressed"] = "#cc0044"

        style = ttk.Style()
        style.theme_use("clam")

        self.root.configure(bg=colors["bg"])
        self.root.option_add("*Font", "Segoe UI 10")

        style.configure("TFrame", background=colors["bg"], borderwidth=0)
        style.configure(
            "TLabelFrame",
            background=colors["bg"],
            foreground=colors["accent_cyan"],
            bordercolor=colors["accent_cyan"],
            labelmargins=10,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelFrame.Label",
            background=colors["bg"],
            foreground=colors["accent_cyan"],
            font=("Segoe UI", 10, "bold"),
        )

        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"], font=("Segoe UI", 10))
        style.configure(
            "Hint.TLabel",
            background=colors["bg"],
            foreground=colors["text_muted"],
            font=("Segoe UI", 9, "italic"),
        )
        style.configure(
            "Status.TLabel", background=colors["bg"], foreground=colors["accent_green"], font=("Segoe UI", 9, "bold")
        )
        style.configure(
            "Accent.TLabel",
            background=colors["bg"],
            foreground=colors["accent_cyan"],
            font=("Segoe UI", 9, "bold"),
        )

        style.configure(
            "TEntry",
            fieldbackground=colors["bg_secondary"],
            background=colors["bg_secondary"],
            foreground=colors["fg"],
            insertcolor=colors["accent_cyan"],
            borderwidth=1,
            relief="solid",
        )
        style.map("TEntry", fieldbackground=[("focus", colors["bg_tertiary"])])

        style.configure(
            "TSpinbox",
            fieldbackground=colors["bg_secondary"],
            background=colors["bg_secondary"],
            foreground=colors["fg"],
            arrowsize=14,
            insertcolor=colors["accent_cyan"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Secondary.TButton",
            background=colors["bg_secondary"],
            foreground=colors["fg"],
            borderwidth=1,
            relief="solid",
            padding=(8, 8),
            font=("Segoe UI", 11, "bold"),
            focuscolor=colors["bg_active"],
        )
        style.map(
            "Secondary.TButton",
            background=[("active", colors["bg_hover"]), ("pressed", colors["bg_active"])],
            foreground=[("disabled", colors["text_muted"])],
        )

        style.configure(
            "Primary.TButton",
            background=colors["accent_green"],
            foreground="#000000",
            borderwidth=0,
            padding=(10, 8),
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", colors["accent_green_hover"]), ("pressed", colors["accent_green_pressed"])],
            foreground=[("disabled", "#444444"), ("pressed", "#000000")],
        )

        style.configure(
            "Danger.TButton",
            background=colors["accent_red"],
            foreground="#ffffff",
            borderwidth=0,
            padding=(10, 8),
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "Danger.TButton",
            background=[("active", colors["accent_red_hover"]), ("pressed", colors["accent_red_pressed"])],
            foreground=[("disabled", "#555555"), ("pressed", "#ffffff")],
        )

        style.configure(
            "Bedrot.TCheckbutton",
            background=colors["bg"],
            foreground=colors["fg_secondary"],
            font=("Segoe UI", 10),
        )
        style.map("Bedrot.TCheckbutton", foreground=[("active", colors["fg"])])

        style.configure(
            "Bedrot.Horizontal.TProgressbar",
            troughcolor=colors["bg_secondary"],
            background=colors["accent_cyan"],
            bordercolor=colors["border"],
            lightcolor=colors["accent_cyan"],
            darkcolor=colors["bg_active"],
            thickness=16,
        )

        style.configure(
            "Bedrot.Horizontal.TScale",
            background=colors["bg"],
            troughcolor=colors["bg_secondary"],
            bordercolor=colors["border"],
            sliderlength=18,
            sliderthickness=12,
        )

        style.configure(
            "Bedrot.Vertical.TScrollbar",
            background=colors["bg_secondary"],
            troughcolor=colors["bg"],
            bordercolor=colors["border"],
            arrowcolor=colors["accent_cyan"],
        )
        style.map(
            "Bedrot.Vertical.TScrollbar",
            background=[("active", colors["bg_hover"])],
            arrowcolor=[("active", colors["accent_green"])],
        )

        return colors

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------
    def refresh_list(self) -> None:
        self.list_var.set(self.video_files)
        self.status_var.set(f"[INFO] {len(self.video_files)} file(s) queued")

    def add_files_dialog(self) -> None:
        initial_dir = self.settings.get("last_source_dir") or str(Path.home())
        paths = filedialog.askopenfilenames(
            title="Select video files",
            initialdir=initial_dir,
            filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.ts *.flv")],
        )
        if paths:
            self.settings["last_source_dir"] = str(Path(paths[0]).parent)
            self.config_manager.update("last_source_dir", self.settings["last_source_dir"])
            self.add_files(paths)

    def add_folder_dialog(self) -> None:
        initial_dir = self.settings.get("last_source_dir") or str(Path.home())
        folder = filedialog.askdirectory(title="Select folder", initialdir=initial_dir)
        if folder:
            self.settings["last_source_dir"] = folder
            self.config_manager.update("last_source_dir", folder)
            self.add_files([folder])

    def remove_selected(self) -> None:
        selected = list(self.listbox.curselection())
        if not selected:
            return
        for index in reversed(selected):
            self.video_files.pop(index)
        self.refresh_list()

    def clear_files(self) -> None:
        self.video_files.clear()
        self.refresh_list()

    def handle_drop(self, data: str) -> None:
        paths = self.root.tk.splitlist(data)
        self.add_files(paths)

    def add_files(self, paths: Iterable[str]) -> None:
        new_files = collect_video_files(paths)
        added = 0
        for file_path in new_files:
            if file_path not in self.video_files:
                self.video_files.append(file_path)
                added += 1

        if added:
            self.refresh_list()
            recent = (self.settings.get("recent_files") or []) + new_files
            self.config_manager.update("recent_files", recent[-20:])
            self.log(f"[video_splitter] Added {added} video(s)")
        else:
            self.log("[video_splitter] No new video files detected")

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------
    def start_processing(self) -> None:
        if not self.video_files:
            messagebox.showwarning("Video Splitter", "Add at least one video before starting.")
            return

        try:
            clip_length = float(self.clip_length_var.get())
            min_clip = float(self.min_clip_var.get())
        except (TypeError, tk.TclError, ValueError):
            messagebox.showerror("Video Splitter", "Clip length values must be numeric.")
            return

        if clip_length <= 0 or min_clip <= 0:
            messagebox.showerror("Video Splitter", "Clip lengths must be greater than zero.")
            return

        output_dir = Path(self.output_dir_var.get())
        try:
            output_dir = ensure_directory(output_dir)
        except Exception as exc:
            messagebox.showerror("Video Splitter", f"Cannot use output directory: {exc}")
            return

        jobs: List[SplitJob] = []
        for file_path in self.video_files:
            jobs.append(
                SplitJob(
                    source_path=Path(file_path),
                    output_dir=output_dir,
                    clip_length=clip_length,
                    jitter_percent=float(self.jitter_var.get()),
                    per_clip_jitter=bool(self.per_clip_var.get()),
                    min_clip_length=min_clip,
                    reset_timestamps=bool(self.reset_ts_var.get()),
                    overwrite_existing=bool(self.overwrite_var.get()),
                )
            )

        if not self.worker.start(jobs, on_complete=self.on_worker_complete):
            messagebox.showinfo("Video Splitter", "Video splitter is already running.")
            return

        self.total_jobs = len(jobs)
        self._set_running_state(True)
        self.progress_var.set(0)
        self.status_var.set("[INFO] Splitting videos...")
        self.log(f"[video_splitter] Started processing {len(jobs)} video(s)")

    def stop_processing(self) -> None:
        if self.worker.is_running:
            self.worker.stop()
            self.status_var.set("[INFO] Stop requested...")

    def on_worker_complete(self, success: bool) -> None:
        def finalize():
            self._set_running_state(False)
            self.progress_var.set(0 if not success else 100)
            msg = "[INFO] Video splitting complete" if success else "[ERROR] Video splitting canceled or failed"
            self.status_var.set(msg)
            self.log(f"[video_splitter] {msg}")

        self.root.after(0, finalize)

    def thread_safe_log(self, message: str) -> None:
        self.root.after(0, lambda: self.log(message))

    def log(self, message: str) -> None:
        if self.logger:
            self.logger.info(message)
        safe_print(message)
        if not self.log_widget:
            return
        self.log_widget.config(state=tk.NORMAL)
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.config(state=tk.DISABLED)

    def thread_safe_progress(self, payload: dict) -> None:
        self.root.after(0, lambda: self._handle_progress(payload))

    def _handle_progress(self, payload: dict) -> None:
        event_type = payload.get("type")

        if event_type == "segment_complete":
            total_segments = payload.get("total_segments", 1)
            segment_index = payload.get("segment_index", 0)
            percent = ((segment_index + 1) / max(total_segments, 1)) * 100
            self.progress_var.set(min(100, percent))
            self.status_var.set(f"[INFO] Segment {segment_index + 1}/{total_segments} complete")
        elif event_type == "job_complete":
            job_index = payload.get("job_index", 0)
            percent = (job_index / max(self.total_jobs, 1)) * 100
            self.progress_var.set(min(100, percent))
            self.status_var.set(f"[INFO] Finished video {job_index}/{self.total_jobs}")
        elif event_type == "job_error":
            self.status_var.set(f"[ERROR] {payload.get('message')}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _persist_setting(self, key: str, value) -> None:
        self.settings[key] = value
        self.config_manager.update(key, value)

    def choose_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="Select output folder", initialdir=self.output_dir_var.get() or str(Path.home()))
        if folder:
            self.output_dir_var.set(folder)

    def _update_jitter_label(self) -> None:
        value = float(self.jitter_var.get())
        self.jitter_label.config(text=f"±{value:.0f}%")

    def _set_running_state(self, running: bool) -> None:
        state = tk.DISABLED if running else tk.NORMAL
        for widget in (
            self.listbox,
            self.btn_add_files,
            self.btn_add_folder,
            self.btn_remove_selected,
            self.btn_clear_list,
        ):
            widget.config(state=state)
        self.start_button.config(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL if running else tk.DISABLED)

    def on_close(self) -> None:
        if self.worker.is_running:
            if not messagebox.askyesno("Video Splitter", "Splitting in progress. Stop and exit?"):
                return
            self.worker.stop()
        self.root.destroy()


def main() -> None:
    root = create_root()
    app = VideoSplitterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
