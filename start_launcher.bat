@echo off
REM Detect directory of this script (the codebase root)
SET "BASEDIR=%~dp0"
CD /D "%BASEDIR%"

REM Check for venv directory
IF EXIST "%BASEDIR%venv\Scripts\activate.bat" (
    echo Virtual environment found.
) ELSE (
    echo Virtual environment not found. Creating venv...
    python -m venv venv
    IF EXIST "%BASEDIR%venv\Scripts\activate.bat" (
        echo venv created successfully.
    ) ELSE (
        echo Failed to create venv. Make sure Python is installed and in PATH.
        pause
        exit /b 1
    )
)

REM Activate venv and install requirements
CALL "%BASEDIR%venv\Scripts\activate.bat"
IF EXIST "%BASEDIR%requirements.txt" (
    echo Installing requirements...
    pip install --upgrade pip
    pip install -r requirements.txt
) ELSE (
    echo requirements.txt not found!
    pause
    exit /b 1
)

REM Launch launcher.py
python launcher.py
