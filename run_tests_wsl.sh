#!/bin/bash
# WSL Test Runner Script
# Handles GUI tests properly in WSL environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}WSL Test Runner for Slideshow Editor${NC}"
echo "===================================="

# Check if we're in WSL
if ! grep -q microsoft /proc/version; then
    echo -e "${YELLOW}Warning: Not running in WSL${NC}"
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo -e "${YELLOW}Warning: No virtual environment found${NC}"
fi

# Set up display for headless testing
export DISPLAY=:99
export LIBGL_ALWAYS_INDIRECT=1

# Check if Xvfb is available
if ! command -v xvfb-run &> /dev/null; then
    echo -e "${RED}Error: xvfb-run not found. Install with: sudo apt install xvfb${NC}"
    exit 1
fi

# Function to run a test
run_test() {
    local test_file="$1"
    local test_name="$2"
    local use_xvfb="$3"
    
    echo -e "\n${BLUE}Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if [ ! -f "$test_file" ]; then
        echo -e "${RED}❌ Test file not found: $test_file${NC}"
        return 1
    fi
    
    if [ "$use_xvfb" = "true" ]; then
        echo "Using virtual framebuffer (headless mode)..."
        if xvfb-run -a -s "-screen 0 1024x768x24" python3 "$test_file"; then
            echo -e "${GREEN}✅ $test_name passed${NC}"
            return 0
        else
            echo -e "${RED}❌ $test_name failed${NC}"
            return 1
        fi
    else
        echo "Running without virtual framebuffer..."
        if python3 "$test_file"; then
            echo -e "${GREEN}✅ $test_name passed${NC}"
            return 0
        else
            echo -e "${RED}❌ $test_name failed${NC}"
            return 1
        fi
    fi
}

# Function to run all tests
run_all_tests() {
    local failed_tests=0
    local total_tests=0
    
    # List of tests to run (name, file, use_xvfb)
    tests=(
        "Environment Test,test_gui_wsl.py,false"
        "PyQt5 Basic Test,tests/test_pyqt5.py,true"
        "Config System Test,tests/test_config_system.py,false"
        "Threading Fixes Test,tests/test_threading_fixes.py,false"
        "Video Logging Test,tests/test_video_logging.py,false"
        "Crop Fix Test,tests/test_crop_fix.py,false"
        "Output Verification Test,tests/test_output_verification.py,false"
    )
    
    for test_entry in "${tests[@]}"; do
        IFS=',' read -r test_name test_file use_xvfb <<< "$test_entry"
        total_tests=$((total_tests + 1))
        
        if ! run_test "$test_file" "$test_name" "$use_xvfb"; then
            failed_tests=$((failed_tests + 1))
        fi
    done
    
    echo -e "\n${BLUE}Test Summary${NC}"
    echo "============="
    echo "Total tests: $total_tests"
    echo "Passed: $((total_tests - failed_tests))"
    echo "Failed: $failed_tests"
    
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}⚠️  $failed_tests test(s) failed${NC}"
        return 1
    fi
}

# Function to test specific GUI functionality
test_gui_specific() {
    echo -e "\n${BLUE}Testing GUI Components Specifically${NC}"
    echo "====================================="
    
    # Create a comprehensive GUI test
    cat > temp_gui_test.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all GUI-related imports"""
    print("Testing imports...")
    
    try:
        import tkinter as tk
        print("✅ tkinter import OK")
    except ImportError as e:
        print(f"❌ tkinter import failed: {e}")
        return False
    
    try:
        from PyQt5.QtWidgets import QApplication, QWidget
        from PyQt5.QtCore import QCoreApplication
        print("✅ PyQt5 imports OK")
    except ImportError as e:
        print(f"❌ PyQt5 import failed: {e}")
        return False
    
    try:
        import customtkinter
        print("✅ customtkinter import OK")
    except ImportError as e:
        print(f"⚠️  customtkinter import failed: {e}")
        # Not critical, continue
    
    return True

def test_pyqt5_app():
    """Test PyQt5 application creation"""
    print("\nTesting PyQt5 application...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QWidget, QLabel
        from PyQt5.QtCore import QCoreApplication
        
        # Set application attributes for headless mode
        QCoreApplication.setAttribute(0x20)  # AA_DisableWindowContextHelpButton
        
        app = QApplication(sys.argv)
        
        widget = QWidget()
        widget.setWindowTitle("Test Window")
        widget.resize(200, 100)
        
        label = QLabel("Test Label", widget)
        label.move(50, 30)
        
        print("✅ PyQt5 widget creation OK")
        
        # Don't show the widget in headless mode
        # widget.show()
        
        # Clean up
        app.quit()
        del app
        
        return True
        
    except Exception as e:
        print(f"❌ PyQt5 application test failed: {e}")
        return False

def test_tkinter_app():
    """Test tkinter application creation"""
    print("\nTesting tkinter application...")
    
    try:
        import tkinter as tk
        
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("200x100")
        
        label = tk.Label(root, text="Test Label")
        label.pack()
        
        print("✅ tkinter widget creation OK")
        
        # Don't call mainloop in headless mode
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ tkinter application test failed: {e}")
        return False

if __name__ == "__main__":
    print("Comprehensive GUI Test")
    print("=" * 25)
    
    tests = [test_imports, test_pyqt5_app, test_tkinter_app]
    results = []
    
    for test in tests:
        results.append(test())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nGUI Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All GUI tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some GUI tests failed")
        sys.exit(1)
EOF
    
    # Run the comprehensive GUI test
    run_test "temp_gui_test.py" "Comprehensive GUI Test" "true"
    
    # Clean up
    rm -f temp_gui_test.py
}

# Parse command line arguments
case "${1:-all}" in
    "all")
        echo "Running all tests..."
        run_all_tests
        ;;
    "gui")
        echo "Running GUI-specific tests..."
        test_gui_specific
        ;;
    "env")
        echo "Testing environment setup..."
        run_test "test_gui_wsl.py" "Environment Test" "false"
        ;;
    "pyqt")
        echo "Testing PyQt5..."
        run_test "tests/test_pyqt5.py" "PyQt5 Test" "true"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [all|gui|env|pyqt|help]"
        echo ""
        echo "Options:"
        echo "  all   - Run all tests (default)"
        echo "  gui   - Run GUI-specific tests"
        echo "  env   - Test environment setup"
        echo "  pyqt  - Test PyQt5 specifically"
        echo "  help  - Show this help"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 