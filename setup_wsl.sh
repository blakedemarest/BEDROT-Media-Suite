#!/bin/bash
# WSL Setup Script for Slideshow Editor
# Run this script to set up the development environment on WSL

set -e  # Exit on any error

echo "Setting up Slideshow Editor for WSL..."
echo "======================================="

# Check if running in WSL
if ! grep -q microsoft /proc/version; then
    echo "Warning: This script is designed for WSL. Continuing anyway..."
fi

# Update system packages
echo "Updating system packages..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
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
    x11-utils \
    git

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python packages
echo "Installing Python packages..."
if [ -f "requirements-wsl.txt" ]; then
    pip install -r requirements-wsl.txt
else
    echo "requirements-wsl.txt not found, using requirements.txt (may have issues)..."
    pip install -r requirements.txt || echo "Some packages failed to install (expected for Windows-specific packages)"
fi

# Set up environment variables
echo "Setting up environment variables..."
if ! grep -q "DISPLAY" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# WSL Display settings for GUI applications" >> ~/.bashrc
    echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk "{print $2}"):0.0' >> ~/.bashrc
    echo 'export LIBGL_ALWAYS_INDIRECT=1' >> ~/.bashrc
    echo 'export PULSE_SERVER="tcp:$(cat /etc/resolv.conf | grep nameserver | awk "{print $2}"):4713"' >> ~/.bashrc
fi

# Create test script for GUI
echo "Creating GUI test script..."
cat > test_gui_wsl.py << 'EOF'
#!/usr/bin/env python3
"""Test GUI functionality in WSL"""
import os
import sys

def test_display():
    """Test if DISPLAY is set"""
    display = os.environ.get('DISPLAY')
    if not display:
        print("❌ DISPLAY environment variable not set")
        print("Run: export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0")
        return False
    print(f"✅ DISPLAY set to: {display}")
    return True

def test_xvfb():
    """Test virtual framebuffer"""
    try:
        import subprocess
        result = subprocess.run(['which', 'xvfb-run'], capture_output=True)
        if result.returncode == 0:
            print("✅ Xvfb available for headless testing")
            return True
        else:
            print("❌ Xvfb not found")
            return False
    except Exception as e:
        print(f"❌ Error checking Xvfb: {e}")
        return False

def test_tkinter():
    """Test tkinter import"""
    try:
        import tkinter as tk
        print("✅ tkinter import successful")
        return True
    except ImportError as e:
        print(f"❌ tkinter import failed: {e}")
        return False

def test_pyqt5():
    """Test PyQt5 import"""
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5 import successful")
        return True
    except ImportError as e:
        print(f"❌ PyQt5 import failed: {e}")
        print("Install with: sudo apt install python3-pyqt5")
        return False

def test_moviepy():
    """Test moviepy and ffmpeg"""
    try:
        import moviepy
        print("✅ MoviePy import successful")
        
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode == 0:
            print("✅ FFmpeg available")
            return True
        else:
            print("❌ FFmpeg not found")
            return False
    except ImportError as e:
        print(f"❌ MoviePy import failed: {e}")
        return False

if __name__ == "__main__":
    print("WSL GUI Environment Test")
    print("=" * 30)
    
    tests = [
        test_display,
        test_xvfb,
        test_tkinter,
        test_pyqt5,
        test_moviepy
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    if passed == total:
        print("🎉 All tests passed! Your WSL environment is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
        
    print("\nTo run tests with virtual display:")
    print("xvfb-run -a python3 tests/test_pyqt5.py")
EOF

chmod +x test_gui_wsl.py

# Create launcher script for WSL
echo "Creating WSL launcher script..."
cat > start_wsl.sh << 'EOF'
#!/bin/bash
# WSL Launcher Script

# Set up display
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
export LIBGL_ALWAYS_INDIRECT=1

# Activate virtual environment
source venv/bin/activate

# Check if X server is running (optional)
if ! xset q &>/dev/null; then
    echo "Warning: X server not detected. GUI applications may not work."
    echo "Start an X server (like VcXsrv) on Windows and ensure it allows connections."
    echo ""
    echo "For headless testing, use: xvfb-run -a python3 <script>"
    echo ""
fi

# Run the launcher
python3 launcher.py
EOF

chmod +x start_wsl.sh

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Install an X server on Windows (VcXsrv recommended)"
echo "2. Start the X server with 'Disable access control' checked"
echo "3. Run: source ~/.bashrc (or restart terminal)"
echo "4. Test setup: python3 test_gui_wsl.py"
echo "5. Start application: ./start_wsl.sh"
echo ""
echo "For headless testing:"
echo "xvfb-run -a python3 tests/test_pyqt5.py"
echo ""
echo "Troubleshooting:"
echo "- If GUI doesn't work, check X server is running on Windows"
echo "- For permission issues: chmod +x *.sh"
echo "- Check firewall settings if X server connection fails"
EOF 