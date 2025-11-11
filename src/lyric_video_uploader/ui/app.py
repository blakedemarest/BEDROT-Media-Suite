# -*- coding: utf-8 -*-
"""
Tkinter GUI for the Lyric Video Uploader pipeline.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .. import ProjectContext, get_package_logger
from ..bridge_snippets.publisher import publish as publish_bridge
from ..export.packager import package_exports
from ..render.ffmpeg_renderer import FFmpegRenderer
from ..render.preset_manager import PresetManager
from ..schemas import LineSegment, coerce_word_tokens
from ..stems.service import separate as separate_stems
from ..stt import build_client_from_config
from ..tempo.manual_input import build_settings
from ..tempo.service import build_manual_grid, load_persisted_beat_grid, persist_beat_grid
from ..timing.alignment import build_document, snap_words_to_beats, write_outputs

LOGGER = get_package_logger("lyric_video.ui")


def _load_transcript(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found at {path}. Run the Transcribe step first.")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class LyricVideoUploaderApp:
    """Main Tkinter application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lyric Video Uploader")
        self.root.geometry("820x720")

        self.project_var = tk.StringVar()
        self.audio_var = tk.StringVar()
        self.preset_var = tk.StringVar(value="default")
        self.bpm_var = tk.StringVar(value="120")
        self.offset_var = tk.StringVar(value="0.0")
        self.snap_var = tk.BooleanVar(value=False)

        self._preset_manager = PresetManager()
        self._build_layout()

    # UI layout -----------------------------------------------------------------

    def _build_layout(self) -> None:
        content = ttk.Frame(self.root, padding=16)
        content.pack(fill="both", expand=True)

        # Project row
        project_row = ttk.Frame(content)
        project_row.pack(fill="x", pady=4)
        ttk.Label(project_row, text="Project Directory").pack(side="left")
        project_entry = ttk.Entry(project_row, textvariable=self.project_var, width=60)
        project_entry.pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(project_row, text="Browse", command=self._select_project).pack(side="right")

        # Audio row
        audio_row = ttk.Frame(content)
        audio_row.pack(fill="x", pady=4)
        ttk.Label(audio_row, text="Audio File").pack(side="left")
        audio_entry = ttk.Entry(audio_row, textvariable=self.audio_var, width=60)
        audio_entry.pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(audio_row, text="Browse", command=self._select_audio).pack(side="right")

        # Preset row
        preset_row = ttk.Frame(content)
        preset_row.pack(fill="x", pady=4)
        ttk.Label(preset_row, text="Render Preset").pack(side="left")
        preset_combo = ttk.Combobox(
            preset_row,
            textvariable=self.preset_var,
            values=list(self._preset_manager.list_presets().keys()),
            state="readonly",
        )
        preset_combo.pack(side="left", padx=6)

        # Tempo row
        tempo_row = ttk.Frame(content)
        tempo_row.pack(fill="x", pady=4)
        ttk.Label(tempo_row, text="Manual BPM").pack(side="left")
        ttk.Entry(tempo_row, width=8, textvariable=self.bpm_var).pack(side="left", padx=(4, 12))
        ttk.Label(tempo_row, text="Offset (s)").pack(side="left")
        ttk.Entry(tempo_row, width=8, textvariable=self.offset_var).pack(side="left", padx=4)
        ttk.Checkbutton(tempo_row, text="Snap to beats", variable=self.snap_var).pack(side="left", padx=12)

        # Buttons row
        button_row = ttk.Frame(content)
        button_row.pack(fill="x", pady=8)
        ttk.Button(button_row, text="Ensure Structure", command=self.ensure_structure).pack(side="left", padx=4)
        ttk.Button(button_row, text="Separate Stems", command=self.run_stems).pack(side="left", padx=4)
        ttk.Button(button_row, text="Transcribe", command=self.run_transcribe).pack(side="left", padx=4)
        ttk.Button(button_row, text="Beat Grid", command=self.run_beatgrid).pack(side="left", padx=4)
        ttk.Button(button_row, text="Generate Timing", command=self.run_timing).pack(side="left", padx=4)
        ttk.Button(button_row, text="Render", command=self.run_render).pack(side="left", padx=4)
        ttk.Button(button_row, text="Package", command=self.run_package).pack(side="left", padx=4)

        # Log area
        self.log_widget = ScrolledText(content, height=20, state="disabled")
        self.log_widget.pack(fill="both", expand=True, pady=(8, 0))

    # Helper methods ------------------------------------------------------------

    def _select_project(self) -> None:
        directory = filedialog.askdirectory(title="Select Project Directory")
        if directory:
            self.project_var.set(directory)

    def _select_audio(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a"), ("All files", "*.*")],
        )
        if file_path:
            self.audio_var.set(file_path)

    def _context(self) -> ProjectContext:
        project_dir = self.project_var.get().strip()
        if not project_dir:
            raise ValueError("Project directory is required.")
        context = ProjectContext(root=Path(project_dir))
        context.ensure_structure()
        return context

    def _audio_path(self) -> Path:
        audio_path = Path(self.audio_var.get().strip())
        if not audio_path.exists():
            raise FileNotFoundError("Audio file not selected or missing.")
        return audio_path.resolve()

    def _log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", f"{message}\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def _run_async(self, target, *args) -> None:
        threading.Thread(target=self._task_wrapper, args=(target, *args), daemon=True).start()

    def _task_wrapper(self, target, *args) -> None:
        try:
            target(*args)
        except Exception as exc:  # noqa: broad-except intentional for UI
            LOGGER.exception("Task failed")
            self._log(f"[ERROR] {exc}")
            messagebox.showerror("Lyric Video Uploader", str(exc))

    # Command handlers ----------------------------------------------------------

    def ensure_structure(self) -> None:
        try:
            context = self._context()
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return
        self._log(f"[INFO] Ensured structure at {context.root}")

    def run_stems(self) -> None:
        try:
            context = self._context()
            audio_path = self._audio_path()
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return
        self._run_async(self._task_stems, context, audio_path)

    def _task_stems(self, context: ProjectContext, audio_path: Path) -> None:
        result = separate_stems(audio_path=audio_path, context=context, force=False)
        for stem, path in result.items():
            self._log(f"[INFO] {stem} -> {path}")

    def run_transcribe(self) -> None:
        try:
            context = self._context()
            audio_path = self._audio_path()
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return
        self._run_async(self._task_transcribe, context, audio_path)

    def _task_transcribe(self, context: ProjectContext, audio_path: Path) -> None:
        client = build_client_from_config()
        result = client.transcribe(audio_path=audio_path, context=context)
        transcript_path = context.timing_dir / "transcript.json"
        payload = {
            "audio_path": str(audio_path),
            "words": [word.to_dict() for word in result.words],
            "lines": [line.to_dict() for line in result.lines],
            "raw": result.raw,
        }
        with transcript_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self._log(f"[INFO] Transcript saved to {transcript_path}")

    def run_beatgrid(self) -> None:
        try:
            context = self._context()
            bpm_value = float(self.bpm_var.get())
            offset_value = float(self.offset_var.get())
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return
        self._run_async(self._task_beatgrid, context, bpm_value, offset_value)

    def _task_beatgrid(self, context: ProjectContext, bpm: float, offset: float) -> None:
        settings = build_settings(str(bpm), str(offset))
        grid = build_manual_grid(settings)
        result = persist_beat_grid(grid, context)
        self._log(f"[INFO] Beat grid stored at {result.destination}")

    def run_timing(self) -> None:
        try:
            context = self._context()
            transcript_path = context.timing_dir / "transcript.json"
            transcript = _load_transcript(transcript_path)
            audio_path = Path(transcript.get("audio_path", self.audio_var.get())).resolve()
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return
        self._run_async(self._task_timing, context, transcript, audio_path, self.snap_var.get())

    def _task_timing(self, context: ProjectContext, transcript: Dict, audio_path: Path, snap_to_beats: bool) -> None:
        words = coerce_word_tokens(transcript.get("words", []))
        line_payload = transcript.get("lines", [])
        lines = [
            LineSegment(
                words=coerce_word_tokens(item.get("words", [])),
                text=item.get("text", ""),
                start=float(item.get("start", 0.0)),
                end=float(item.get("end", 0.0)),
            )
            for item in line_payload
        ]

        beat_grid_path = context.timing_dir / "beatgrid.json"
        beat_grid = load_persisted_beat_grid(beat_grid_path) if beat_grid_path.exists() else None
        processed_words = snap_words_to_beats(words, beat_grid) if snap_to_beats and beat_grid else words

        doc = build_document(audio_path=audio_path, words=processed_words, lines=lines, beat_grid=beat_grid)
        outputs = write_outputs(doc, context)
        publish_bridge(doc, context)
        self._log(f"[INFO] Timing outputs generated: {outputs}")

    def run_render(self) -> None:
        try:
            context = self._context()
            audio_path = self._audio_path()
            preset_obj = self._preset_manager.get_preset(self.preset_var.get())
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return
        self._run_async(self._task_render, context, audio_path, preset_obj)

    def _task_render(self, context: ProjectContext, audio_path: Path, preset) -> None:
        ass_path = context.timing_dir / "lyrics.ass"
        if not ass_path.exists():
            raise FileNotFoundError("ASS subtitle file not found. Run the timing step first.")

        renderer = FFmpegRenderer()
        render_dir = context.renders_dir / preset.name
        render_dir.mkdir(parents=True, exist_ok=True)
        output_path = render_dir / "final.mp4"
        renderer.render(
            ass_path=ass_path,
            audio_path=audio_path,
            background_path=preset.background,
            output_path=output_path,
            preset=preset,
        )
        self._log(f"[INFO] Render complete: {output_path}")

    def run_package(self) -> None:
        try:
            context = self._context()
            render_path = filedialog.askopenfilename(
                title="Select Rendered Video",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            )
            if not render_path:
                return
            metadata_path = filedialog.askopenfilename(
                title="Select Metadata JSON",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
            if not metadata_path:
                return
            with open(metadata_path, "r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except Exception as exc:
            messagebox.showerror("Lyric Video Uploader", str(exc))
            return

        caption_paths = {
            "words": context.timing_dir / "words.srt",
            "lines": context.timing_dir / "lines.srt",
            "ass": context.timing_dir / "lyrics.ass",
            "json": context.timing_dir / "lyrics.json",
        }
        extra_files = []
        beat_grid_path = context.timing_dir / "beatgrid.json"
        if beat_grid_path.exists():
            extra_files.append(beat_grid_path)
        snippet_bridge_dir = context.exports_dir / "snippet_bridge"
        if snippet_bridge_dir.exists():
            extra_files.extend(path for path in snippet_bridge_dir.iterdir() if path.is_file())

        self._run_async(
            self._task_package,
            context,
            Path(render_path),
            metadata,
            caption_paths,
            extra_files,
        )

    def _task_package(
        self,
        context: ProjectContext,
        render_path: Path,
        metadata: Dict[str, str],
        caption_paths: Dict[str, Path],
        extra_files,
    ) -> None:
        ready_dir = package_exports(
            context,
            metadata,
            render_path=render_path,
            caption_paths=caption_paths,
            extra_files=extra_files,
        )
        self._log(f"[INFO] Export bundle ready at {ready_dir}")


def main() -> None:
    root = tk.Tk()
    app = LyricVideoUploaderApp(root)
    root.mainloop()


__all__ = ["main", "LyricVideoUploaderApp"]
