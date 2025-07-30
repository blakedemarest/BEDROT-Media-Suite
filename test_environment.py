import sys
import os

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Virtual environment:", os.environ.get('VIRTUAL_ENV', 'Not in venv'))
print("\nTesting imports:")

try:
    import pyqt5
    print("✓ PyQt5 imported successfully")
except ImportError as e:
    print("✗ PyQt5 import failed:", e)

try:
    import PyQt6
    print("✓ PyQt6 imported successfully")
except ImportError as e:
    print("✗ PyQt6 import failed:", e)

try:
    import pandas
    print("✓ pandas imported successfully")
except ImportError as e:
    print("✗ pandas import failed:", e)

try:
    import pywin32
    print("✓ pywin32 imported successfully")
except ImportError as e:
    print("✗ pywin32 import failed:", e)

print("\nEnvironment test complete.")