@echo off
REM Detect directory of this script (the codebase root)
SET "BASEDIR=%~dp0"
CD /D "%BASEDIR%"

REM Clear any conflicting Python paths
SET PYTHONPATH=
SET VIRTUAL_ENV=

REM Check for virtual environment (use venv as primary for Windows)
IF EXIST "%BASEDIR%venv\Scripts\activate.bat" (
    echo Virtual environment found at venv
    SET "VENV_PATH=%BASEDIR%venv"
    SET "VENV_PYTHON=%BASEDIR%venv\Scripts\python.exe"
    SET "VENV_PIP=%BASEDIR%venv\Scripts\pip.exe"
) ELSE (
    echo Virtual environment not found. Creating venv...
    REM Use explicit python path to avoid conflicts
    python -m venv venv
    IF EXIST "%BASEDIR%venv\Scripts\activate.bat" (
        echo venv created successfully.
        SET "VENV_PATH=%BASEDIR%venv"
        SET "VENV_PYTHON=%BASEDIR%venv\Scripts\python.exe"
        SET "VENV_PIP=%BASEDIR%venv\Scripts\pip.exe"
    ) ELSE (
        echo Failed to create venv. Make sure Python is installed and in PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment with explicit paths
CALL "%VENV_PATH%\Scripts\activate.bat"
IF EXIST "%BASEDIR%requirements.txt" (
    echo Installing requirements...
    echo Using pip at: %VENV_PIP%
    "%VENV_PYTHON%" -m pip install --upgrade pip
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        echo Failed to install some dependencies. Continuing anyway...
    )
    echo.
    echo [INFO] Lyric Video Uploader requires additional CUDA/Demucs packages detailed in docs/lyric_video_uploader/.
    echo [INFO] Run "%VENV_PYTHON%" -m src.lyric_video_uploader.cli <project_dir> --ensure-structure after setup to stage workspaces.
) ELSE (
    echo requirements.txt not found!
    pause
    exit /b 1
)

REM Launch launcher.py with explicit python path
echo Launching application...
"%VENV_PYTHON%" launcher.py
