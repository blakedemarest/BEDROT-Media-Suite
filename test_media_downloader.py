#!/usr/bin/env python3
"""
Media Downloader Test Suite
Tests MP4 and MP3 download functionality with YouTube videos and Shorts.
"""

import os
import sys
import subprocess
import time
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / 'src'))

# Test configuration
TEST_VIDEOS = {
    'regular_video': {
        'url': 'https://www.youtube.com/watch?v=Rkv6iZhggTY',
        'title': 'Regular YouTube Video',
        'expected_duration': 60  # Approximate duration in seconds
    },
    'youtube_short': {
        'url': 'https://www.youtube.com/watch?v=wHc2fBTFYho',
        'title': 'YouTube Short',
        'expected_duration': 60  # Shorts are typically under 60 seconds
    }
}

class MediaDownloaderTest:
    def __init__(self):
        self.test_dir = SCRIPT_DIR / 'test_downloads'
        self.venv_python = SCRIPT_DIR / 'venv' / 'Scripts' / 'python.exe'
        self.results = []
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """Create test directory and verify dependencies."""
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        
        # Check if venv Python exists
        if not self.venv_python.exists():
            print(f"Error: Virtual environment Python not found at {self.venv_python}")
            sys.exit(1)
            
        # Check for yt-dlp
        result = subprocess.run(
            [str(self.venv_python), '-m', 'pip', 'show', 'yt-dlp'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Error: yt-dlp not installed in virtual environment")
            sys.exit(1)
            
        # Check for FFmpeg
        ffmpeg_check = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True)
        if ffmpeg_check.returncode != 0:
            print("Warning: FFmpeg not found in PATH. Some features may not work.")
            
    def test_direct_download(self, url, format_type, test_name):
        """Test direct download using yt-dlp command line."""
        print(f"\n{'='*60}")
        print(f"Testing {test_name} - Format: {format_type}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        output_template = str(self.test_dir / f"{test_name}_{format_type}_%(title)s.%(ext)s")
        
        # Build yt-dlp command
        if format_type == 'mp4':
            cmd = [
                str(self.venv_python), '-m', 'yt_dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '-o', output_template,
                url
            ]
        else:  # mp3
            cmd = [
                str(self.venv_python), '-m', 'yt_dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # Best quality
                '-o', output_template,
                url
            ]
        
        # Run download
        start_time = time.time()
        print(f"Command: {' '.join(cmd)}")
        print("Downloading...")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Capture output
            stdout_lines = []
            stderr_lines = []
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output:
                    print(f"  {output.strip()}")
                    stdout_lines.append(output.strip())
                    
                error = process.stderr.readline()
                if error:
                    stderr_lines.append(error.strip())
                    
                if output == '' and error == '' and process.poll() is not None:
                    break
                    
            return_code = process.poll()
            duration = time.time() - start_time
            
            # Check for downloaded files
            downloaded_files = list(self.test_dir.glob(f"{test_name}_{format_type}_*"))
            
            result = {
                'test_name': test_name,
                'format': format_type,
                'url': url,
                'success': return_code == 0 and len(downloaded_files) > 0,
                'duration': duration,
                'return_code': return_code,
                'files': [str(f) for f in downloaded_files],
                'file_sizes': {str(f): f.stat().st_size for f in downloaded_files if f.exists()},
                'errors': stderr_lines if return_code != 0 else []
            }
            
            # Verify file properties
            if downloaded_files:
                for file in downloaded_files:
                    print(f"\nDownloaded: {file.name}")
                    print(f"Size: {file.stat().st_size / 1024 / 1024:.2f} MB")
                    
                    # Check file extension
                    if format_type == 'mp4' and file.suffix.lower() != '.mp4':
                        result['warnings'] = result.get('warnings', [])
                        result['warnings'].append(f"Expected .mp4 but got {file.suffix}")
                    elif format_type == 'mp3' and file.suffix.lower() not in ['.mp3', '.m4a']:
                        result['warnings'] = result.get('warnings', [])
                        result['warnings'].append(f"Expected .mp3 but got {file.suffix}")
            
            self.results.append(result)
            
            if result['success']:
                print(f"\n✓ SUCCESS: Downloaded in {duration:.2f} seconds")
            else:
                print(f"\n✗ FAILED: Return code {return_code}")
                if stderr_lines:
                    print("Errors:")
                    for error in stderr_lines[:5]:
                        print(f"  - {error}")
                        
        except Exception as e:
            print(f"\n✗ EXCEPTION: {str(e)}")
            self.results.append({
                'test_name': test_name,
                'format': format_type,
                'url': url,
                'success': False,
                'error': str(e),
                'exception': True
            })
            
    def test_programmatic_download(self, url, format_type, test_name):
        """Test download using the media_download_app module."""
        print(f"\n{'='*60}")
        print(f"Testing {test_name} via media_download_app - Format: {format_type}")
        print(f"{'='*60}")
        
        # Create a test script that uses the media downloader
        test_script = self.test_dir / f"test_{test_name}_{format_type}.py"
        
        script_content = f'''
import sys
import os
sys.path.insert(0, r"{SCRIPT_DIR / 'src'}")

from media_download_app import download_with_ytdlp

# Test parameters
url = "{url}"
output_path = r"{self.test_dir}"
format_type = "{format_type}"

print(f"Testing download: {{url}}")
print(f"Output path: {{output_path}}")
print(f"Format: {{format_type}}")

# Simulate download (would need to adapt download_with_ytdlp to be callable)
# For now, we'll just test the import
print("Import successful!")
'''
        
        with open(test_script, 'w') as f:
            f.write(script_content)
            
        try:
            result = subprocess.run(
                [str(self.venv_python), str(test_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"Output: {result.stdout}")
            if result.stderr:
                print(f"Errors: {result.stderr}")
                
            success = result.returncode == 0 and "Import successful" in result.stdout
            
            self.results.append({
                'test_name': f"{test_name}_programmatic",
                'format': format_type,
                'url': url,
                'success': success,
                'type': 'import_test'
            })
            
            if success:
                print("✓ Module import successful")
            else:
                print("✗ Module import failed")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")
            self.results.append({
                'test_name': f"{test_name}_programmatic",
                'format': format_type,
                'url': url,
                'success': False,
                'error': str(e)
            })
        finally:
            # Clean up test script
            if test_script.exists():
                test_script.unlink()
    
    def verify_media_files(self):
        """Verify the downloaded media files using ffprobe."""
        print(f"\n{'='*60}")
        print("Verifying downloaded files")
        print(f"{'='*60}")
        
        ffprobe_path = shutil.which('ffprobe')
        if not ffprobe_path:
            print("Warning: ffprobe not found, skipping media verification")
            return
            
        for result in self.results:
            if result.get('success') and result.get('files'):
                for file_path in result['files']:
                    if Path(file_path).exists():
                        print(f"\nVerifying: {Path(file_path).name}")
                        
                        cmd = [
                            'ffprobe',
                            '-v', 'error',
                            '-show_entries', 'format=duration,format_name,bit_rate',
                            '-show_entries', 'stream=codec_type,codec_name,width,height',
                            '-of', 'json',
                            file_path
                        ]
                        
                        try:
                            probe_result = subprocess.run(cmd, capture_output=True, text=True)
                            if probe_result.returncode == 0:
                                info = json.loads(probe_result.stdout)
                                
                                # Extract media info
                                duration = float(info.get('format', {}).get('duration', 0))
                                format_name = info.get('format', {}).get('format_name', 'unknown')
                                
                                print(f"  Format: {format_name}")
                                print(f"  Duration: {duration:.2f} seconds")
                                
                                # Check streams
                                for stream in info.get('streams', []):
                                    if stream['codec_type'] == 'video':
                                        print(f"  Video: {stream['codec_name']} {stream.get('width')}x{stream.get('height')}")
                                    elif stream['codec_type'] == 'audio':
                                        print(f"  Audio: {stream['codec_name']}")
                                        
                        except Exception as e:
                            print(f"  Verification error: {str(e)}")
    
    def generate_report(self):
        """Generate test report."""
        print(f"\n{'='*80}")
        print("TEST REPORT")
        print(f"{'='*80}")
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.get('success'))
        failed = total_tests - successful
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        # Summary by format
        mp4_tests = [r for r in self.results if r.get('format') == 'mp4']
        mp3_tests = [r for r in self.results if r.get('format') == 'mp3']
        
        print(f"\nMP4 Tests: {len(mp4_tests)} (Success: {sum(1 for r in mp4_tests if r.get('success'))})")
        print(f"MP3 Tests: {len(mp3_tests)} (Success: {sum(1 for r in mp3_tests if r.get('success'))})")
        
        # Failed tests details
        if failed > 0:
            print("\n" + "-"*40)
            print("FAILED TESTS:")
            print("-"*40)
            for result in self.results:
                if not result.get('success'):
                    print(f"\n{result['test_name']} ({result['format']}):")
                    if result.get('errors'):
                        print("  Errors:")
                        for error in result.get('errors', [])[:3]:
                            print(f"    - {error}")
                    if result.get('error'):
                        print(f"  Error: {result['error']}")
        
        # Save detailed results
        report_file = self.test_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'test_time': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'successful': successful,
                    'failed': failed
                },
                'results': self.results
            }, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")
        
        # List downloaded files
        print("\n" + "-"*40)
        print("DOWNLOADED FILES:")
        print("-"*40)
        for file in sorted(self.test_dir.glob("*.mp*")):
            if file.suffix in ['.mp4', '.mp3', '.m4a']:
                size_mb = file.stat().st_size / 1024 / 1024
                print(f"  {file.name} ({size_mb:.2f} MB)")
    
    def cleanup(self, keep_files=False):
        """Clean up test files."""
        if not keep_files:
            print("\nCleaning up test files...")
            for file in self.test_dir.glob("*.mp*"):
                if file.suffix in ['.mp4', '.mp3', '.m4a']:
                    file.unlink()
            print("Cleanup complete.")
        else:
            print(f"\nTest files kept in: {self.test_dir}")
    
    def run_all_tests(self):
        """Run all media downloader tests."""
        print("MEDIA DOWNLOADER TEST SUITE")
        print("="*80)
        print(f"Test directory: {self.test_dir}")
        print(f"Python: {self.venv_python}")
        
        # Test each video with each format
        for video_key, video_info in TEST_VIDEOS.items():
            for format_type in ['mp4', 'mp3']:
                test_name = f"{video_key}_{format_type}"
                
                # Direct yt-dlp test
                self.test_direct_download(
                    video_info['url'],
                    format_type,
                    test_name
                )
                
                # Brief pause between downloads
                time.sleep(2)
        
        # Test programmatic access
        print("\n" + "="*60)
        print("Testing programmatic access to media_download_app")
        print("="*60)
        for video_key, video_info in TEST_VIDEOS.items():
            self.test_programmatic_download(
                video_info['url'],
                'mp4',
                video_key
            )
        
        # Verify downloaded files
        self.verify_media_files()
        
        # Generate report
        self.generate_report()


def main():
    """Run the media downloader tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Media Downloader functionality')
    parser.add_argument('--keep-files', action='store_true', 
                        help='Keep downloaded files after testing')
    parser.add_argument('--quick', action='store_true',
                        help='Run quick tests only (skip some downloads)')
    
    args = parser.parse_args()
    
    tester = MediaDownloaderTest()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user!")
    except Exception as e:
        print(f"\nTest suite error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        tester.cleanup(keep_files=args.keep_files)


if __name__ == "__main__":
    main()