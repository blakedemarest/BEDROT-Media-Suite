#!/usr/bin/env python3
"""
Diagnostic script for Random Slideshow module issues.
Run this to check dependencies and import paths.
"""

import sys
import os
import subprocess

print("=" * 60)
print("Random Slideshow Diagnostic Tool")
print("=" * 60)

# Check Python version
print(f"\n1. Python Version: {sys.version}")

# Check current working directory
print(f"\n2. Current Directory: {os.getcwd()}")

# Check sys.path
print(f"\n3. Python Path (first 5):")
for i, path in enumerate(sys.path[:5]):
    print(f"   [{i}] {path}")

# Check for required modules
print("\n4. Checking Required Modules:")
required_modules = [
    'numpy',
    'PyQt5',
    'moviepy',
    'PIL',
    'pandas',
    'psutil'
]

missing_modules = []
for module in required_modules:
    try:
        __import__(module)
        print(f"   ✓ {module} - OK")
    except ImportError as e:
        print(f"   ✗ {module} - MISSING ({e})")
        missing_modules.append(module)

# Check FFmpeg
print("\n5. Checking FFmpeg:")
try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✓ FFmpeg is installed")
        first_line = result.stdout.split('\n')[0]
        print(f"   Version: {first_line}")
    else:
        print("   ✗ FFmpeg returned error")
except FileNotFoundError:
    print("   ✗ FFmpeg not found in PATH")

# Try importing random_slideshow module
print("\n6. Testing Random Slideshow imports:")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from random_slideshow._import_helper import setup_imports
    print("   ✓ _import_helper imported successfully")
    setup_imports()
except Exception as e:
    print(f"   ✗ _import_helper failed: {e}")

try:
    from random_slideshow.config_manager import ConfigManager
    print("   ✓ ConfigManager imported successfully")
except Exception as e:
    print(f"   ✗ ConfigManager import failed: {e}")

try:
    from random_slideshow.main_app import RandomSlideshowEditor
    print("   ✓ RandomSlideshowEditor imported successfully")
except Exception as e:
    print(f"   ✗ RandomSlideshowEditor import failed: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY:")
if missing_modules:
    print(f"Missing modules: {', '.join(missing_modules)}")
    print("\nTo fix, run:")
    print("  pip install -r requirements.txt")
else:
    print("All required modules are installed.")
print("=" * 60)