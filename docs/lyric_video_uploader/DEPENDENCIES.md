# Lyric Video Uploader Dependencies (Windows / CUDA)

The Lyric Video Uploader depends on GPU-accelerated audio separation and subtitle tooling. Install everything **inside the project virtual environment** created by `start_launcher.bat`.

## CUDA & NVIDIA Drivers
- Install NVIDIA drivers that ship with CUDA 12.x support (tested with RTX 4090 / CUDA 12.1).
- Verify NVENC availability with `ffmpeg -encoders | findstr /i nvenc`.

## Python Packages
```powershell
# From the activated venv
python -m pip install --upgrade pip
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
python -m pip install demucs pysubs2 typer tqdm moviepy
```

> **Important:** CPU-only Torch builds are not supported. If the CUDA wheel fails to install, resolve driver/toolkit issues instead of falling back.

## External Tools
- **FFmpeg**: Install an NVENC-enabled build (e.g., gyan.dev) and add it to `PATH`.
- **Demucs CLI**: Installed automatically with the `demucs` pip package; confirm via `demucs --help`.
- **ElevenLabs API Key**: Set `ELEVENLABS_API_KEY` in `.env` or the Windows environment. The client fails fast if missing.

## Validation Checklist
1. `python -m src.lyric_video_uploader.cli C:\Projects\Lyrics --ensure-structure`
2. `python -c "import torch; assert torch.cuda.is_available()"`
3. `ffmpeg -encoders | find "h264_nvenc"`
4. `demucs --help`
5. `echo %ELEVENLABS_API_KEY%` (or use `python - <<<'import os; print(os.getenv("ELEVENLABS_API_KEY"))'`)

All checks must pass before the full workflow is enabled.
