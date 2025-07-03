# WSL Setup Guide for Slideshow Editor

This guide will help you set up the Slideshow Editor project to run properly on Windows Subsystem for Linux (WSL).

## Quick Start

1. **Run the setup script:**
   ```bash
   ./setup_wsl.sh
   ```

2. **Test your environment:**
   ```bash
   python3 test_gui_wsl.py
   ```

3. **Run tests:**
   ```bash
   ./run_tests_wsl.sh
   ```

4. **Start the application:**
   ```bash
   ./start_wsl.sh
   ```

## Prerequisites

### 1. WSL2 Installation
Ensure you're using WSL2 for better performance:
```powershell
# Run in Windows PowerShell as Administrator
wsl --set-default-version 2
wsl --list -v
```

### 2. X Server for GUI Applications
Since this project uses GUI frameworks (PyQt5, tkinter), you need an X server:

**Option A: VcXsrv (Recommended)**
1. Download from: https://sourceforge.net/projects/vcxsrv/
2. Install and run with these settings:
   - Multiple windows
   - Start no client
   - ☑️ Disable access control
   - ☑️ Native opengl (optional)

**Option B: X410 (Paid)**
- Available from Microsoft Store
- More modern but costs money

### 3. Windows Firewall Configuration
Allow VcXsrv through Windows Firewall:
1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Add VcXsrv

## Manual Setup (if script fails)

### System Dependencies
```bash
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-pyqt5 \
    python3-pyqt5.qtwebengine \
    ffmpeg \
    libavcodec-extra \
    xvfb \
    x11-utils
```

### Environment Variables
Add to `~/.bashrc`:
```bash
# WSL Display settings
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
export LIBGL_ALWAYS_INDIRECT=1
export PULSE_SERVER="tcp:$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):4713"
```

Then run: `source ~/.bashrc`

### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (WSL-compatible)
pip install -r requirements-wsl.txt
```

## Testing

### Environment Test
```bash
python3 test_gui_wsl.py
```

### Run All Tests
```bash
./run_tests_wsl.sh all
```

### GUI-Specific Tests
```bash
./run_tests_wsl.sh gui
```

### Headless Testing (No X Server needed)
```bash
xvfb-run -a python3 tests/test_pyqt5.py
```

## Common Issues & Solutions

### 1. "Cannot connect to X server"
**Problem:** X server not running or misconfigured
**Solutions:**
- Start VcXsrv on Windows
- Check firewall settings
- Verify DISPLAY variable: `echo $DISPLAY`
- Test X connection: `xset q`

### 2. "PyQt5 not found"
**Problem:** PyQt5 not properly installed
**Solutions:**
```bash
# Try system package first
sudo apt install python3-pyqt5

# If that fails, try pip
pip install PyQt5
```

### 3. "Permission denied" on scripts
**Problem:** Scripts not executable
**Solution:**
```bash
chmod +x *.sh
```

### 4. "FFmpeg not found"
**Problem:** Missing multimedia codecs
**Solution:**
```bash
sudo apt install ffmpeg libavcodec-extra
```

### 5. Tests hang or freeze
**Problem:** GUI tests waiting for user interaction
**Solutions:**
- Use headless testing: `xvfb-run -a python3 <test_file>`
- Run specific tests: `./run_tests_wsl.sh pyqt`
- Check for infinite loops in test code

### 6. "No module named 'core'"
**Problem:** Python path issues
**Solution:**
```bash
# Run from project root
cd /path/to/slideshow_editor
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## Performance Tips

### 1. Use Native Packages When Possible
Install system packages instead of pip packages for better performance:
```bash
sudo apt install python3-pyqt5 python3-tk python3-pil
```

### 2. WSL2 File System
Keep your project files in WSL2 file system (`/home/`) rather than Windows file system (`/mnt/c/`) for better I/O performance.

### 3. Memory Management
For large video processing:
```bash
# Increase swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Development Workflow

### Daily Usage
```bash
# Start development session
cd ~/slideshow_editor
source venv/bin/activate

# Run tests
./run_tests_wsl.sh

# Start application
./start_wsl.sh
```

### Debugging
```bash
# Verbose X11 debugging
export DISPLAY=:0.0
xset q

# Python debugging
python3 -m pdb <script.py>

# GUI debugging (headless)
xvfb-run -a -s "-screen 0 1024x768x24" python3 <script.py>
```

## Alternative: VS Code Dev Containers

For a completely isolated environment, consider using VS Code with Dev Containers:

1. Install VS Code with Remote-Containers extension
2. Create `.devcontainer/devcontainer.json`:
```json
{
    "name": "Slideshow Editor",
    "image": "python:3.9",
    "features": {
        "ghcr.io/devcontainers/features/desktop-lite:1": {}
    },
    "postCreateCommand": "pip install -r requirements-wsl.txt"
}
```

## Troubleshooting Commands

```bash
# Check WSL version
wsl --list -v

# Check display connection
echo $DISPLAY
xset q

# Test basic GUI
xeyes &  # Should show eyes following cursor

# Check audio (if needed)
pulseaudio --check -v

# Monitor processes
ps aux | grep python
ps aux | grep Xvfb

# Check Python environment
which python3
python3 --version
pip list | grep -E "(PyQt5|tkinter|moviepy)"
```

## Resources

- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [VcXsrv Documentation](https://sourceforge.net/projects/vcxsrv/)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [X11 Forwarding Guide](https://wiki.archlinux.org/title/X11_forwarding)

## Getting Help

If you're still having issues:

1. Run the diagnostic: `python3 test_gui_wsl.py`
2. Check the logs in the `logs/` directory
3. Try running individual tests with verbose output
4. Ensure all prerequisites are properly installed

Remember: GUI applications in WSL require an X server running on Windows! 