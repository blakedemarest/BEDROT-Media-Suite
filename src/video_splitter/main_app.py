# -*- coding: utf-8 -*-
"""
Tkinter GUI for the Bedrot Video Splitter module.

Refactored to use reusable UI components.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List

from .components import (
    FileListComponent,
    LogPanelComponent,
    ProgressComponent,
    SettingsPanelComponent,
)
from .config_manager import ConfigManager
from .drag_drop import create_root, setup_drop_target, DND_AVAILABLE
from .logging_config import setup_logger
from .models import SplitJob, SplitterSettings
from .split_worker import SplitWorker
from .theme import apply_bedrot_theme
from .utils import collect_video_files, ensure_directory, safe_print


class VideoSplitterApp:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BEDROT VIDEO SPLITTER // CLIP ENGINE")
        self.logger = setup_logger()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.get_all()
        self.colors = apply_bedrot_theme(self.root)

        self.worker = SplitWorker(
            log_callback=self.thread_safe_log,
            progress_callback=self.thread_safe_progress,
        )
        self.total_jobs = 0

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)  # Log panel expands

        # File List Component
        self.file_list = FileListComponent(
            parent=self.root,
            colors=self.colors,
            on_add_files=self.add_files_dialog,
            on_add_folder=self.add_folder_dialog,
            on_remove_selected=self._remove_selected,
            on_clear=self._clear_files,
        )
        self.file_list.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Setup drag-drop on the listbox
        if setup_drop_target(self.file_list.listbox, self.handle_drop):
            self.file_list.set_hint_text("Drag + drop video files or folders anywhere in this list")
        elif DND_AVAILABLE:
            self.file_list.set_hint_text("Drag + drop not supported on this window")

        # Settings Panel Component
        initial_settings = SplitterSettings(
            output_dir=self.settings.get("output_dir", ""),
            clip_length_seconds=float(self.settings.get("clip_length_seconds", 30.0)),
            jitter_percent=float(self.settings.get("jitter_percent", 0)),
            min_clip_length=float(self.settings.get("min_clip_length", 1.0)),
            per_clip_jitter=bool(self.settings.get("per_clip_jitter", False)),
            reset_timestamps=bool(self.settings.get("reset_timestamps", False)),
            overwrite_existing=bool(self.settings.get("overwrite_existing", False)),
        )
        self.settings_panel = SettingsPanelComponent(
            parent=self.root,
            colors=self.colors,
            initial_settings=initial_settings,
            on_browse_output=self.choose_output_dir,
            on_setting_changed=self._persist_setting,
        )
        self.settings_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Progress Component
        self.progress = ProgressComponent(
            parent=self.root,
            colors=self.colors,
            on_start=self.start_processing,
            on_stop=self.stop_processing,
        )
        self.progress.grid(row=2, column=0, sticky="ew")

        # Log Panel Component
        self.log_panel = LogPanelComponent(parent=self.root, colors=self.colors)
        self.log_panel.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------
    def _refresh_status(self) -> None:
        count = self.file_list.file_count()
        self.progress.set_status(f"[INFO] {count} file(s) queued")

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
            self._add_files(paths)

    def add_folder_dialog(self) -> None:
        initial_dir = self.settings.get("last_source_dir") or str(Path.home())
        folder = filedialog.askdirectory(title="Select folder", initialdir=initial_dir)
        if folder:
            self.settings["last_source_dir"] = folder
            self.config_manager.update("last_source_dir", folder)
            self._add_files([folder])

    def _remove_selected(self) -> None:
        removed = self.file_list.remove_selected()
        if removed:
            self._refresh_status()

    def _clear_files(self) -> None:
        self.file_list.clear()
        self._refresh_status()

    def handle_drop(self, data: str) -> None:
        paths = self.root.tk.splitlist(data)
        self._add_files(paths)

    def _add_files(self, paths) -> None:
        new_files = collect_video_files(paths)
        added = self.file_list.add_files(new_files)

        if added:
            self._refresh_status()
            recent = (self.settings.get("recent_files") or []) + list(new_files)
            self.config_manager.update("recent_files", recent[-20:])
            self.log(f"[video_splitter] Added {added} video(s)")
        else:
            self.log("[video_splitter] No new video files detected")

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------
    def start_processing(self) -> None:
        video_files = self.file_list.get_files()
        if not video_files:
            messagebox.showwarning("Video Splitter", "Add at least one video before starting.")
            return

        settings = self.settings_panel.get_settings()

        try:
            clip_length = settings.clip_length_seconds
            min_clip = settings.min_clip_length
        except (TypeError, ValueError):
            messagebox.showerror("Video Splitter", "Clip length values must be numeric.")
            return

        if clip_length <= 0 or min_clip <= 0:
            messagebox.showerror("Video Splitter", "Clip lengths must be greater than zero.")
            return

        output_dir = Path(settings.output_dir)
        try:
            output_dir = ensure_directory(output_dir)
        except Exception as exc:
            messagebox.showerror("Video Splitter", f"Cannot use output directory: {exc}")
            return

        jobs: List[SplitJob] = []
        for file_path in video_files:
            jobs.append(
                SplitJob(
                    source_path=Path(file_path),
                    output_dir=output_dir,
                    clip_length=clip_length,
                    jitter_percent=settings.jitter_percent,
                    per_clip_jitter=settings.per_clip_jitter,
                    min_clip_length=min_clip,
                    reset_timestamps=settings.reset_timestamps,
                    overwrite_existing=settings.overwrite_existing,
                )
            )

        if not self.worker.start(jobs, on_complete=self.on_worker_complete):
            messagebox.showinfo("Video Splitter", "Video splitter is already running.")
            return

        self.total_jobs = len(jobs)
        self._set_running_state(True)
        self.progress.set_progress(0)
        self.progress.set_status("[INFO] Splitting videos...")
        self.log(f"[video_splitter] Started processing {len(jobs)} video(s)")

    def stop_processing(self) -> None:
        if self.worker.is_running:
            self.worker.stop()
            self.progress.set_status("[INFO] Stop requested...")

    def on_worker_complete(self, success: bool) -> None:
        def finalize():
            self._set_running_state(False)
            self.progress.set_progress(0 if not success else 100)
            msg = "[INFO] Video splitting complete" if success else "[ERROR] Video splitting canceled or failed"
            self.progress.set_status(msg)
            self.log(f"[video_splitter] {msg}")

        self.root.after(0, finalize)

    def thread_safe_log(self, message: str) -> None:
        self.root.after(0, lambda: self.log(message))

    def log(self, message: str) -> None:
        if self.logger:
            self.logger.info(message)
        safe_print(message)
        self.log_panel.log(message)

    def thread_safe_progress(self, payload: dict) -> None:
        self.root.after(0, lambda: self._handle_progress(payload))

    def _handle_progress(self, payload: dict) -> None:
        event_type = payload.get("type")

        if event_type == "segment_complete":
            total_segments = payload.get("total_segments", 1)
            segment_index = payload.get("segment_index", 0)
            percent = ((segment_index + 1) / max(total_segments, 1)) * 100
            self.progress.set_progress(min(100, percent))
            self.progress.set_status(f"[INFO] Segment {segment_index + 1}/{total_segments} complete")
        elif event_type == "job_complete":
            job_index = payload.get("job_index", 0)
            percent = (job_index / max(self.total_jobs, 1)) * 100
            self.progress.set_progress(min(100, percent))
            self.progress.set_status(f"[INFO] Finished video {job_index}/{self.total_jobs}")
        elif event_type == "job_error":
            self.progress.set_status(f"[ERROR] {payload.get('message')}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _persist_setting(self, key: str, value) -> None:
        self.settings[key] = value
        self.config_manager.update(key, value)

    def choose_output_dir(self) -> None:
        current = self.settings_panel.output_dir_var.get()
        folder = filedialog.askdirectory(
            title="Select output folder",
            initialdir=current or str(Path.home()),
        )
        if folder:
            self.settings_panel.set_output_dir(folder)

    def _set_running_state(self, running: bool) -> None:
        self.file_list.set_enabled(not running)
        self.progress.set_running_state(running)

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
