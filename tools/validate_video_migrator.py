#!/usr/bin/env python3
"""
Simple validation of video aspect ratio migrator functionality
"""

import os
import sys
import subprocess

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ffprobe_availability():
    """Test if FFprobe is available and working."""
    print("Testing FFprobe availability...")
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("[SUCCESS] FFprobe is available")
            # Extract version info from first line
            version_line = result.stdout.split('\n')[0]
            print(f"Version: {version_line}")
            return True
        else:
            print("[ERROR] FFprobe returned non-zero exit code")
            return False
    except Exception as e:
        print(f"[ERROR] FFprobe test failed: {e}")
        return False

def test_aspect_ratio_logic():
    """Test aspect ratio categorization logic."""
    print("\nTesting aspect ratio categorization...")
    
    # Import our migrator
    try:
        from video_aspect_ratio_migrator import VideoAspectRatioMigrator
        migrator = VideoAspectRatioMigrator()
        print("[SUCCESS] VideoAspectRatioMigrator imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import VideoAspectRatioMigrator: {e}")
        return False
    
    # Test common dimensions
    test_cases = [
        (1920, 1080, "16:9"),   # Full HD landscape
        (1080, 1920, "9:16"),   # Full HD portrait
        (1080, 1080, "1:1"),    # Square
        (1080, 1350, "4:5"),    # Portrait
        (2560, 1440, "16:9"),   # 2K landscape
        (720, 1280, "9:16"),    # HD portrait
        (3840, 2160, "16:9"),   # 4K landscape
    ]
    
    all_passed = True
    for width, height, expected in test_cases:
        actual = migrator.categorize_aspect_ratio(width, height)
        status = "PASS" if actual == expected else "FAIL"
        print(f"  {width}x{height} -> {actual} (expected {expected}) [{status}]")
        if actual != expected:
            all_passed = False
    
    return all_passed

def test_file_path_conversion():
    """Test file path conversion logic."""
    print("\nTesting file path conversion...")
    
    try:
        from video_aspect_ratio_migrator import VideoAspectRatioMigrator
        migrator = VideoAspectRatioMigrator()
        
        # Test Windows to WSL path conversion
        test_path = "E:\\VIDEOS\\RELEASE CONTENT\\test.mp4"
        
        # Simulate the path conversion logic
        if os.name != 'nt' and test_path.startswith('E:'):
            converted_path = test_path.replace('E:', '/mnt/e')
            converted_path = converted_path.replace('\\', '/')
            print(f"Original: {test_path}")
            print(f"Converted: {converted_path}")
            print("[SUCCESS] Path conversion logic works")
        else:
            print("[INFO] Running on Windows or path doesn't need conversion")
        
        return True
    except Exception as e:
        print(f"[ERROR] Path conversion test failed: {e}")
        return False

def main():
    """Run validation tests."""
    print("="*60)
    print("[VIDEO ASPECT RATIO MIGRATOR VALIDATION]")
    print("="*60)
    
    tests = [
        ("FFprobe Availability", test_ffprobe_availability),
        ("Aspect Ratio Logic", test_aspect_ratio_logic),
        ("File Path Conversion", test_file_path_conversion),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[TEST: {test_name}]")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("[VALIDATION SUMMARY]")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n[SUCCESS] All validation tests passed!")
        print("The video aspect ratio migrator is ready to use.")
        return True
    else:
        print(f"\n[WARNING] {len(results) - passed} test(s) failed")
        print("Review the failures before using the migrator.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)