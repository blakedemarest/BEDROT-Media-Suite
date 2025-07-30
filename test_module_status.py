#!/usr/bin/env python3
"""
Module Status Test for Bedrot Media Suite
Tests all modules by launching them concurrently and monitoring for errors.
"""

import os
import sys
import subprocess
import threading
import time
import queue
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / 'src'))

# Module definitions
MODULES = {
    'Media Download App': {
        'script': 'src/media_download_app.py',
        'type': 'tkinter',
        'test_duration': 5
    },
    'Snippet Remixer': {
        'script': 'src/snippet_remixer_modular.py',
        'type': 'tkinter', 
        'test_duration': 5
    },
    'Random Slideshow': {
        'script': 'src/random_slideshow/main.py',
        'type': 'pyqt5',
        'test_duration': 5
    },
    'Video Caption Generator': {
        'script': 'src/video_caption_generator/main_app.py',
        'type': 'pyqt5',
        'test_duration': 5
    },
    'Reel Tracker': {
        'script': 'src/reel_tracker_modular.py',
        'type': 'pyqt5',
        'test_duration': 5
    },
    'Release Calendar': {
        'script': 'src/release_calendar_modular.py',
        'type': 'pyqt6',
        'test_duration': 5
    }
}

class ModuleTestResult:
    def __init__(self, name):
        self.name = name
        self.status = 'pending'
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.errors = []
        self.warnings = []
        self.stdout = []
        self.stderr = []
        self.exit_code = None
        self.process_id = None
        self.terminated_cleanly = False

class ModuleTester:
    def __init__(self):
        self.results = {}
        self.active_processes = {}
        self.output_queue = queue.Queue()
        self.lock = threading.Lock()
        
    def capture_output(self, pipe, result, stream_type):
        """Capture output from a subprocess pipe."""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    line = line.strip()
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    formatted_line = f"[{timestamp}] {line}"
                    
                    if stream_type == 'stdout':
                        result.stdout.append(formatted_line)
                    else:
                        result.stderr.append(formatted_line)
                        # Check for common error patterns
                        if any(err in line.lower() for err in ['error', 'exception', 'failed', 'traceback']):
                            result.errors.append(formatted_line)
                        elif any(warn in line.lower() for warn in ['warning', 'warn']):
                            result.warnings.append(formatted_line)
        except Exception as e:
            result.errors.append(f"Error capturing {stream_type}: {str(e)}")
        finally:
            pipe.close()

    def test_module(self, name, module_info):
        """Test a single module in a separate thread."""
        result = ModuleTestResult(name)
        result.start_time = datetime.now()
        
        script_path = SCRIPT_DIR / module_info['script']
        
        # Check if script exists
        if not script_path.exists():
            result.status = 'failed'
            result.errors.append(f"Script not found: {script_path}")
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            with self.lock:
                self.results[name] = result
            return
        
        try:
            # Launch the module
            env = os.environ.copy()
            # Set environment to minimize GUI warnings
            env['QT_LOGGING_RULES'] = '*.debug=false;*.warning=false'
            
            # Use venv Python if available
            venv_python = SCRIPT_DIR / 'venv' / 'Scripts' / 'python.exe'
            if venv_python.exists():
                python_exe = str(venv_python)
            else:
                python_exe = sys.executable
                
            process = subprocess.Popen(
                [python_exe, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                cwd=str(SCRIPT_DIR)
            )
            
            result.process_id = process.pid
            result.status = 'running'
            
            with self.lock:
                self.active_processes[name] = process
                self.results[name] = result
            
            # Start output capture threads
            stdout_thread = threading.Thread(
                target=self.capture_output,
                args=(process.stdout, result, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self.capture_output,
                args=(process.stderr, result, 'stderr'),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for test duration
            test_duration = module_info.get('test_duration', 5)
            time.sleep(test_duration)
            
            # Check if process is still running
            if process.poll() is None:
                # Process is still running, try to terminate gracefully
                result.status = 'terminating'
                process.terminate()
                
                # Give it time to terminate
                try:
                    process.wait(timeout=5)
                    result.terminated_cleanly = True
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    process.wait()
                    result.errors.append("Process did not terminate gracefully, had to force kill")
            else:
                # Process ended on its own
                result.errors.append(f"Process exited prematurely with code {process.returncode}")
            
            result.exit_code = process.returncode
            
            # Wait for output threads to finish
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Determine final status
            if result.errors:
                result.status = 'failed'
            elif result.warnings:
                result.status = 'warning'
            else:
                result.status = 'success'
                
        except Exception as e:
            result.status = 'failed'
            result.errors.append(f"Exception during test: {str(e)}")
            import traceback
            result.errors.append(traceback.format_exc())
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            with self.lock:
                if name in self.active_processes:
                    del self.active_processes[name]

    def run_all_tests(self):
        """Run all module tests concurrently."""
        print("=" * 80)
        print("BEDROT MEDIA SUITE - MODULE STATUS TEST")
        print("=" * 80)
        print(f"Testing {len(MODULES)} modules concurrently...")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        
        # Start all tests in separate threads
        threads = []
        for name, module_info in MODULES.items():
            print(f"Starting test for: {name}")
            thread = threading.Thread(
                target=self.test_module,
                args=(name, module_info),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            # Small delay to avoid simultaneous startup issues
            time.sleep(0.5)
        
        # Wait for all tests to complete
        print("\nWaiting for all tests to complete...")
        for thread in threads:
            thread.join()
        
        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate and display test report."""
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Summary statistics
        total = len(self.results)
        success = sum(1 for r in self.results.values() if r.status == 'success')
        warnings = sum(1 for r in self.results.values() if r.status == 'warning')
        failed = sum(1 for r in self.results.values() if r.status == 'failed')
        
        print(f"\nTotal Modules Tested: {total}")
        print(f"[SUCCESS] Success: {success}")
        print(f"[WARNING] Warnings: {warnings}")
        print(f"[FAILED] Failed: {failed}")
        
        # Detailed results for each module
        print("\n" + "-" * 80)
        print("DETAILED RESULTS")
        print("-" * 80)
        
        for name, result in sorted(self.results.items()):
            status_icon = "[OK]" if result.status == 'success' else "[WARN]" if result.status == 'warning' else "[FAIL]"
            print(f"\n{status_icon} {name}")
            print(f"   Status: {result.status.upper()}")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Process ID: {result.process_id}")
            print(f"   Exit Code: {result.exit_code}")
            print(f"   Clean Termination: {'Yes' if result.terminated_cleanly else 'No'}")
            
            if result.errors:
                print(f"   Errors ({len(result.errors)}):")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"      - {error}")
                if len(result.errors) > 5:
                    print(f"      ... and {len(result.errors) - 5} more errors")
            
            if result.warnings:
                print(f"   Warnings ({len(result.warnings)}):")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    print(f"      - {warning}")
                if len(result.warnings) > 3:
                    print(f"      ... and {len(result.warnings) - 3} more warnings")
        
        # Save detailed log
        self.save_detailed_log()
        
        # Error analysis
        self.analyze_errors()

    def save_detailed_log(self):
        """Save detailed test results to a JSON file."""
        log_file = SCRIPT_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert results to serializable format
        log_data = {
            'test_time': datetime.now().isoformat(),
            'modules': {}
        }
        
        for name, result in self.results.items():
            log_data['modules'][name] = {
                'status': result.status,
                'duration': result.duration,
                'exit_code': result.exit_code,
                'process_id': result.process_id,
                'terminated_cleanly': result.terminated_cleanly,
                'errors': result.errors,
                'warnings': result.warnings,
                'stdout_lines': len(result.stdout),
                'stderr_lines': len(result.stderr)
            }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\nDetailed log saved to: {log_file}")

    def analyze_errors(self):
        """Analyze common error patterns across modules."""
        print("\n" + "-" * 80)
        print("ERROR ANALYSIS")
        print("-" * 80)
        
        # Collect all errors
        all_errors = []
        for result in self.results.values():
            all_errors.extend(result.errors)
        
        if not all_errors:
            print("No errors found across all modules!")
            return
        
        # Common error patterns
        patterns = {
            'Import Error': ['importerror', 'no module named', 'cannot import'],
            'File Not Found': ['filenotfounderror', 'no such file', 'not found'],
            'Permission Error': ['permissionerror', 'access denied', 'permission denied'],
            'Configuration Error': ['config', 'configuration', 'settings'],
            'GUI Error': ['qt', 'tkinter', 'gui', 'widget', 'window'],
            'FFmpeg Error': ['ffmpeg', 'ffprobe', 'avconv'],
            'Dependency Error': ['dependency', 'requirement', 'package']
        }
        
        error_categories = {category: [] for category in patterns}
        uncategorized = []
        
        for error in all_errors:
            error_lower = error.lower()
            categorized = False
            
            for category, keywords in patterns.items():
                if any(keyword in error_lower for keyword in keywords):
                    error_categories[category].append(error)
                    categorized = True
                    break
            
            if not categorized:
                uncategorized.append(error)
        
        # Display categorized errors
        for category, errors in error_categories.items():
            if errors:
                print(f"\n{category} ({len(errors)} occurrences):")
                for error in errors[:2]:  # Show first 2 of each category
                    print(f"  - {error}")
                if len(errors) > 2:
                    print(f"  ... and {len(errors) - 2} more")
        
        if uncategorized:
            print(f"\nUncategorized Errors ({len(uncategorized)}):")
            for error in uncategorized[:3]:
                print(f"  - {error}")

    def cleanup(self):
        """Clean up any remaining processes."""
        for name, process in self.active_processes.items():
            if process.poll() is None:
                print(f"Cleaning up {name} (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

def main():
    """Run the module status test."""
    tester = ModuleTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user!")
    finally:
        tester.cleanup()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()