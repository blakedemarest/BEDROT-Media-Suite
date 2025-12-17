"""
Health Check System for Slideshow Editor Application

This module provides comprehensive health checks for the application, including:
- External tool availability (FFmpeg, yt-dlp)
- Python package dependencies
- File system permissions
- Disk space availability
- Python version compatibility
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import importlib.metadata
from importlib.metadata import PackageNotFoundError
import psutil
import socket
import urllib.request
import urllib.error

from .env_loader import get_env_var, load_environment
from .path_utils import resolve_output_path, resolve_config_path, get_project_root
from .config_manager import get_config_manager


class HealthCheckResult:
    """Container for health check results"""
    
    def __init__(self, name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.name = name
        self.status = status  # 'ok', 'warning', 'error'
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class HealthChecker:
    """Main health check system"""
    
    def __init__(self, cache_results: bool = True):
        self.cache_results = cache_results
        self._cache: Dict[str, HealthCheckResult] = {}
        self._cache_timeout = 300  # 5 minutes
        
        # Required Python packages with minimum versions
        self.required_packages = {
            'PyQt5': '5.0.0',
            'pandas': '1.0.0',
            'Pillow': '8.0.0',
            'moviepy': '1.0.0',
            'numpy': None,  # Any version
            'requests': None,
            'python-dotenv': None
        }
        
        # Optional packages that enhance functionality
        self.optional_packages = {
            'yt-dlp': None,
            'opencv-python': None,
            'scipy': None,
            'psutil': None  # For system resource monitoring
        }
    
    def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks"""
        results = []
        
        # System checks
        results.append(self.check_python_version())
        results.append(self.check_ffmpeg())
        results.append(self.check_ytdlp())
        
        # Package checks
        for package, min_version in self.required_packages.items():
            results.append(self.check_python_package(package, min_version, required=True))
        
        for package, min_version in self.optional_packages.items():
            results.append(self.check_python_package(package, min_version, required=False))
        
        # File system checks
        results.append(self.check_output_directory_permissions())
        results.append(self.check_disk_space())
        
        # PyQt5 specific check
        results.append(self.check_pyqt5_installation())
        
        # System resource checks
        results.append(self.check_system_resources())
        
        # Configuration checks
        results.append(self.check_configuration_files())
        results.append(self.check_environment_variables())
        
        # Network connectivity (optional)
        results.append(self.check_network_connectivity())
        
        return results
    
    def check_python_version(self) -> HealthCheckResult:
        """Check Python version compatibility"""
        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        
        if version_info.major < 3:
            return HealthCheckResult(
                "Python Version",
                "error",
                f"Python 3.x required, found {version_str}",
                {"version": version_str, "required": "3.x"}
            )
        
        if version_info.minor < 7:
            return HealthCheckResult(
                "Python Version",
                "warning",
                f"Python 3.7+ recommended, found {version_str}",
                {"version": version_str, "recommended": "3.7+"}
            )
        
        return HealthCheckResult(
            "Python Version",
            "ok",
            f"Python {version_str} is compatible",
            {"version": version_str}
        )
    
    def check_ffmpeg(self) -> HealthCheckResult:
        """Check FFmpeg availability and version"""
        cache_key = "ffmpeg"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            # Try to run ffmpeg -version
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Extract version from output
                output_lines = result.stdout.split('\n')
                version_line = output_lines[0] if output_lines else "Unknown version"
                
                # Also check ffprobe
                ffprobe_result = subprocess.run(
                    ["ffprobe", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                ffprobe_available = ffprobe_result.returncode == 0
                
                check_result = HealthCheckResult(
                    "FFmpeg",
                    "ok",
                    "FFmpeg is installed and accessible",
                    {
                        "version": version_line,
                        "ffprobe_available": ffprobe_available,
                        "path": shutil.which("ffmpeg")
                    }
                )
            else:
                check_result = HealthCheckResult(
                    "FFmpeg",
                    "error",
                    "FFmpeg is installed but returned an error",
                    {"stderr": result.stderr}
                )
        
        except subprocess.TimeoutExpired:
            check_result = HealthCheckResult(
                "FFmpeg",
                "error",
                "FFmpeg check timed out",
                {"timeout": 5}
            )
        
        except FileNotFoundError:
            check_result = HealthCheckResult(
                "FFmpeg",
                "error",
                "FFmpeg not found in PATH",
                {
                    "fix": "Install FFmpeg from https://ffmpeg.org/download.html",
                    "path_checked": os.environ.get('PATH', '')
                }
            )
        
        except Exception as e:
            check_result = HealthCheckResult(
                "FFmpeg",
                "error",
                f"Error checking FFmpeg: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
        
        if self.cache_results:
            self._cache[cache_key] = check_result
        
        return check_result
    
    def check_ytdlp(self) -> HealthCheckResult:
        """Check yt-dlp availability and version"""
        cache_key = "ytdlp"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            # Try to run yt-dlp --version
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                check_result = HealthCheckResult(
                    "yt-dlp",
                    "ok",
                    "yt-dlp is installed and accessible",
                    {
                        "version": version,
                        "path": shutil.which("yt-dlp")
                    }
                )
            else:
                check_result = HealthCheckResult(
                    "yt-dlp",
                    "warning",
                    "yt-dlp is installed but returned an error",
                    {"stderr": result.stderr}
                )
        
        except FileNotFoundError:
            # Check if it's available as a Python module
            try:
                import yt_dlp
                check_result = HealthCheckResult(
                    "yt-dlp",
                    "ok",
                    "yt-dlp available as Python module",
                    {"module_version": getattr(yt_dlp, '__version__', 'Unknown')}
                )
            except ImportError:
                check_result = HealthCheckResult(
                    "yt-dlp",
                    "warning",
                    "yt-dlp not found (media download will be unavailable)",
                    {
                        "fix": "Install with: pip install yt-dlp",
                        "impact": "Media download functionality will not work"
                    }
                )
        
        except subprocess.TimeoutExpired:
            check_result = HealthCheckResult(
                "yt-dlp",
                "warning",
                "yt-dlp check timed out",
                {"timeout": 5}
            )
        
        except Exception as e:
            check_result = HealthCheckResult(
                "yt-dlp",
                "warning",
                f"Error checking yt-dlp: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
        
        if self.cache_results:
            self._cache[cache_key] = check_result
        
        return check_result
    
    def check_python_package(self, package_name: str, min_version: Optional[str] = None, 
                           required: bool = True) -> HealthCheckResult:
        """Check if a Python package is installed with the correct version"""
        cache_key = f"package_{package_name}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            # Get package version using importlib.metadata
            version = importlib.metadata.version(package_name)
            
            # Check minimum version if specified
            if min_version:
                from packaging import version as pkg_version
                if pkg_version.parse(version) < pkg_version.parse(min_version):
                    status = "error" if required else "warning"
                    check_result = HealthCheckResult(
                        f"Package: {package_name}",
                        status,
                        f"{package_name} version {version} is below minimum {min_version}",
                        {
                            "installed_version": version,
                            "minimum_version": min_version,
                            "fix": f"Upgrade with: pip install --upgrade {package_name}>={min_version}"
                        }
                    )
                else:
                    check_result = HealthCheckResult(
                        f"Package: {package_name}",
                        "ok",
                        f"{package_name} {version} meets requirements",
                        {"version": version}
                    )
            else:
                check_result = HealthCheckResult(
                    f"Package: {package_name}",
                    "ok",
                    f"{package_name} {version} is installed",
                    {"version": version}
                )
        
        except PackageNotFoundError:
            status = "error" if required else "warning"
            impact = "Application may not function correctly" if required else "Some features may be unavailable"
            check_result = HealthCheckResult(
                f"Package: {package_name}",
                status,
                f"{package_name} is not installed",
                {
                    "fix": f"Install with: pip install {package_name}",
                    "required": required,
                    "impact": impact
                }
            )
        
        except Exception as e:
            check_result = HealthCheckResult(
                f"Package: {package_name}",
                "warning",
                f"Error checking {package_name}: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
        
        if self.cache_results:
            self._cache[cache_key] = check_result
        
        return check_result
    
    def check_pyqt5_installation(self) -> HealthCheckResult:
        """Special check for PyQt5 functionality"""
        cache_key = "pyqt5_functional"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            # Try to import key PyQt5 modules
            from PyQt5 import QtCore, QtGui, QtWidgets
            
            # Check Qt version
            qt_version = QtCore.QT_VERSION_STR
            pyqt_version = QtCore.PYQT_VERSION_STR
            
            check_result = HealthCheckResult(
                "PyQt5 Functionality",
                "ok",
                "PyQt5 is fully functional",
                {
                    "qt_version": qt_version,
                    "pyqt_version": pyqt_version,
                    "platform_plugin": os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH', 'Not set')
                }
            )
        
        except ImportError as e:
            check_result = HealthCheckResult(
                "PyQt5 Functionality",
                "error",
                f"PyQt5 import failed: {str(e)}",
                {
                    "fix": "Reinstall PyQt5: pip install --force-reinstall PyQt5",
                    "module": str(e.name) if hasattr(e, 'name') else 'Unknown'
                }
            )
        
        except Exception as e:
            check_result = HealthCheckResult(
                "PyQt5 Functionality",
                "error",
                f"Error checking PyQt5: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
        
        if self.cache_results:
            self._cache[cache_key] = check_result
        
        return check_result
    
    def check_output_directory_permissions(self) -> HealthCheckResult:
        """Check if we can write to the output directory"""
        try:
            output_dir = resolve_output_path()
            
            # Create directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to create a temporary file
            test_file = output_dir / f".health_check_{os.getpid()}.tmp"
            try:
                test_file.write_text("Health check test")
                test_file.unlink()  # Clean up
                
                return HealthCheckResult(
                    "Output Directory",
                    "ok",
                    f"Write permissions verified for {output_dir}",
                    {"path": str(output_dir)}
                )
            
            except Exception as e:
                return HealthCheckResult(
                    "Output Directory",
                    "error",
                    f"Cannot write to output directory: {str(e)}",
                    {
                        "path": str(output_dir),
                        "fix": f"Check permissions for: {output_dir}"
                    }
                )
        
        except Exception as e:
            return HealthCheckResult(
                "Output Directory",
                "error",
                f"Error checking output directory: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
    
    def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space"""
        try:
            output_dir = resolve_output_path()
            
            # Get disk usage statistics
            stat = shutil.disk_usage(output_dir)
            
            # Convert to GB
            total_gb = stat.total / (1024 ** 3)
            free_gb = stat.free / (1024 ** 3)
            used_percent = (stat.used / stat.total) * 100
            
            # Warning if less than 5GB free or more than 90% used
            if free_gb < 5 or used_percent > 90:
                return HealthCheckResult(
                    "Disk Space",
                    "warning",
                    f"Low disk space: {free_gb:.1f}GB free ({used_percent:.1f}% used)",
                    {
                        "free_gb": round(free_gb, 2),
                        "total_gb": round(total_gb, 2),
                        "used_percent": round(used_percent, 2),
                        "path": str(output_dir)
                    }
                )
            
            return HealthCheckResult(
                "Disk Space",
                "ok",
                f"Sufficient disk space: {free_gb:.1f}GB free",
                {
                    "free_gb": round(free_gb, 2),
                    "total_gb": round(total_gb, 2),
                    "used_percent": round(used_percent, 2),
                    "path": str(output_dir)
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                "Disk Space",
                "warning",
                f"Could not check disk space: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Check CPU and memory resources"""
        try:
            # Check if psutil is available
            try:
                import psutil
            except ImportError:
                return HealthCheckResult(
                    "System Resources",
                    "warning",
                    "psutil not installed - cannot check system resources",
                    {"fix": "Install with: pip install psutil"}
                )
            
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Convert memory to GB
            total_memory_gb = memory.total / (1024 ** 3)
            available_memory_gb = memory.available / (1024 ** 3)
            memory_percent = memory.percent
            
            # Check thresholds
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            if available_memory_gb < 1:
                issues.append(f"Low available memory: {available_memory_gb:.1f}GB")
            
            if issues:
                return HealthCheckResult(
                    "System Resources",
                    "warning",
                    "; ".join(issues),
                    {
                        "cpu_percent": round(cpu_percent, 1),
                        "memory_total_gb": round(total_memory_gb, 2),
                        "memory_available_gb": round(available_memory_gb, 2),
                        "memory_percent": round(memory_percent, 1)
                    }
                )
            
            return HealthCheckResult(
                "System Resources",
                "ok",
                f"System resources adequate: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%",
                {
                    "cpu_percent": round(cpu_percent, 1),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": round(total_memory_gb, 2),
                    "memory_available_gb": round(available_memory_gb, 2),
                    "memory_percent": round(memory_percent, 1)
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                "System Resources",
                "warning",
                f"Could not check system resources: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
    
    def check_configuration_files(self) -> HealthCheckResult:
        """Check validity of configuration files"""
        try:
            config_manager = get_config_manager()
            config_files = [
                "config.json",
                "yt_downloader_gui_settings.json",
                "video_remixer_settings.json",
                "reel_tracker_config.json"
            ]
            
            invalid_files = []
            missing_files = []
            
            for config_file in config_files:
                try:
                    config_path = resolve_config_path(config_file)
                    if not config_path.exists():
                        missing_files.append(config_file)
                    else:
                        # Try to load and parse the JSON
                        config_path.read_text()
                        json.loads(config_path.read_text())
                except json.JSONDecodeError:
                    invalid_files.append(config_file)
                except Exception:
                    # File might not exist, which is okay for some configs
                    pass
            
            if invalid_files:
                return HealthCheckResult(
                    "Configuration Files",
                    "error",
                    f"Invalid JSON in config files: {', '.join(invalid_files)}",
                    {
                        "invalid_files": invalid_files,
                        "fix": "Check and fix JSON syntax in the listed files"
                    }
                )
            elif missing_files:
                # Missing files are okay - they'll be created when needed
                return HealthCheckResult(
                    "Configuration Files",
                    "ok",
                    f"Configuration files valid ({len(missing_files)} will be created on first use)",
                    {"missing_files": missing_files}
                )
            else:
                return HealthCheckResult(
                    "Configuration Files",
                    "ok",
                    "All configuration files are valid",
                    {"checked_files": config_files}
                )
        
        except Exception as e:
            return HealthCheckResult(
                "Configuration Files",
                "warning",
                f"Could not check configuration files: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
    
    def check_environment_variables(self) -> HealthCheckResult:
        """Check if expected environment variables are set"""
        try:
            # Load environment if not already loaded
            load_environment()
            
            important_env_vars = [
                "SLIDESHOW_PROJECT_ROOT",
                "SLIDESHOW_CONFIG_DIR",
                "SLIDESHOW_SRC_DIR",
                "SLIDESHOW_TOOLS_DIR",
                "SLIDESHOW_DEFAULT_OUTPUT_DIR"
            ]
            
            missing_vars = []
            configured_vars = {}
            
            for var in important_env_vars:
                value = get_env_var(var)
                if value:
                    configured_vars[var] = value
                else:
                    missing_vars.append(var)
            
            # Check if .env file exists
            env_file = get_project_root() / ".env"
            env_exists = env_file.exists()
            
            if missing_vars:
                return HealthCheckResult(
                    "Environment Variables",
                    "warning",
                    f"Some environment variables not set: {', '.join(missing_vars)}",
                    {
                        "missing_vars": missing_vars,
                        "configured_vars": configured_vars,
                        "env_file_exists": env_exists,
                        "fix": "Copy .env.example to .env and configure as needed"
                    }
                )
            else:
                return HealthCheckResult(
                    "Environment Variables",
                    "ok",
                    "All expected environment variables are configured",
                    {
                        "configured_vars": configured_vars,
                        "env_file_exists": env_exists
                    }
                )
        
        except Exception as e:
            return HealthCheckResult(
                "Environment Variables",
                "warning",
                f"Could not check environment variables: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
    
    def check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity for downloads"""
        cache_key = "network"
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            # Try to connect to common download sites
            test_urls = [
                ("https://www.youtube.com", "YouTube"),
                ("https://github.com", "GitHub")
            ]
            
            failed_sites = []
            successful_sites = []
            
            for url, name in test_urls:
                try:
                    # Simple HEAD request with timeout
                    req = urllib.request.Request(url, method='HEAD')
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            successful_sites.append(name)
                        else:
                            failed_sites.append((name, f"Status: {response.status}"))
                except Exception as e:
                    failed_sites.append((name, str(e)))
            
            if not successful_sites:
                check_result = HealthCheckResult(
                    "Network Connectivity",
                    "warning",
                    "No network connectivity detected",
                    {
                        "failed_sites": failed_sites,
                        "impact": "Media download features will not work"
                    }
                )
            elif failed_sites:
                check_result = HealthCheckResult(
                    "Network Connectivity",
                    "warning",
                    f"Partial connectivity: {len(failed_sites)} sites unreachable",
                    {
                        "successful_sites": successful_sites,
                        "failed_sites": failed_sites
                    }
                )
            else:
                check_result = HealthCheckResult(
                    "Network Connectivity",
                    "ok",
                    "Network connectivity verified",
                    {"tested_sites": successful_sites}
                )
        
        except Exception as e:
            check_result = HealthCheckResult(
                "Network Connectivity",
                "warning",
                f"Could not check network connectivity: {str(e)}",
                {"exception": str(type(e).__name__)}
            )
        
        if self.cache_results:
            self._cache[cache_key] = check_result
        
        return check_result
    
    def _is_cached(self, key: str) -> bool:
        """Check if a result is cached and still valid"""
        if not self.cache_results or key not in self._cache:
            return False
        
        cached_result = self._cache[key]
        age = (datetime.now() - cached_result.timestamp).total_seconds()
        return age < self._cache_timeout
    
    def generate_report(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate a comprehensive health check report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version
            },
            "summary": {
                "total_checks": len(results),
                "passed": sum(1 for r in results if r.status == "ok"),
                "warnings": sum(1 for r in results if r.status == "warning"),
                "errors": sum(1 for r in results if r.status == "error")
            },
            "results": [r.to_dict() for r in results]
        }
        
        # Add overall status
        if report["summary"]["errors"] > 0:
            report["overall_status"] = "error"
            report["overall_message"] = "Critical issues found that need to be resolved"
        elif report["summary"]["warnings"] > 0:
            report["overall_status"] = "warning"
            report["overall_message"] = "Some optional features may not work correctly"
        else:
            report["overall_status"] = "ok"
            report["overall_message"] = "All checks passed successfully"
        
        # Add quick fixes if available
        report["quick_fixes"] = self._generate_quick_fixes(results)
        
        return report
    
    def _generate_quick_fixes(self, results: List[HealthCheckResult]) -> List[Dict[str, str]]:
        """Generate quick fix commands for common issues"""
        quick_fixes = []
        
        for result in results:
            if result.status in ["error", "warning"] and "fix" in result.details:
                quick_fixes.append({
                    "check": result.name,
                    "issue": result.message,
                    "fix": result.details["fix"]
                })
        
        return quick_fixes
    
    def save_report(self, report: Dict[str, Any], filepath: Optional[Path] = None) -> Path:
        """Save health check report to a file"""
        if filepath is None:
            # Default to project root
            from .path_utils import get_project_root
            project_root = get_project_root()
            reports_dir = project_root / "health_check_reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = reports_dir / f"health_check_{timestamp}.json"
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(report, indent=2))
        
        return filepath
    
    def print_report(self, results: List[HealthCheckResult], verbose: bool = False):
        """Print a human-readable health check report"""
        print("\n" + "="*60)
        print("SLIDESHOW EDITOR HEALTH CHECK REPORT")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version.split()[0]}")
        print("="*60 + "\n")
        
        # Group results by status
        errors = [r for r in results if r.status == "error"]
        warnings = [r for r in results if r.status == "warning"]
        ok = [r for r in results if r.status == "ok"]
        
        # Print errors first
        if errors:
            print("❌ ERRORS (Must be fixed):")
            print("-" * 40)
            for result in errors:
                print(f"  • {result.name}: {result.message}")
                if verbose and result.details.get('fix'):
                    print(f"    Fix: {result.details['fix']}")
            print()
        
        # Print warnings
        if warnings:
            print("⚠️  WARNINGS (Optional fixes):")
            print("-" * 40)
            for result in warnings:
                print(f"  • {result.name}: {result.message}")
                if verbose and result.details.get('fix'):
                    print(f"    Fix: {result.details['fix']}")
            print()
        
        # Print successes (in verbose mode)
        if verbose and ok:
            print("✅ PASSED:")
            print("-" * 40)
            for result in ok:
                print(f"  • {result.name}: {result.message}")
            print()
        
        # Summary
        print("="*60)
        print(f"SUMMARY: {len(ok)} passed, {len(warnings)} warnings, {len(errors)} errors")
        
        if errors:
            print("\n⚠️  CRITICAL: Please fix the errors above before running the application.")
        elif warnings:
            print("\n✓ The application should work, but some features may be limited.")
        else:
            print("\n✓ All checks passed! The application is ready to use.")
        print("="*60 + "\n")
    
    def get_gui_friendly_results(self, results: List[HealthCheckResult]) -> List[Dict[str, Any]]:
        """Convert results to GUI-friendly format"""
        gui_results = []
        
        for result in results:
            gui_result = {
                "name": result.name,
                "status": result.status,
                "message": result.message,
                "details": result.details,
                "timestamp": result.timestamp.strftime("%H:%M:%S"),
                "icon": self._get_status_icon(result.status),
                "color": self._get_status_color(result.status)
            }
            gui_results.append(gui_result)
        
        return gui_results
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {
            "ok": "✓",
            "warning": "⚠",
            "error": "✗"
        }
        return icons.get(status, "?")
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors = {
            "ok": "#28a745",      # Green
            "warning": "#ffc107",  # Yellow
            "error": "#dc3545"     # Red
        }
        return colors.get(status, "#6c757d")  # Gray default


# Convenience functions
def run_health_check(verbose: bool = False, save_report: bool = False) -> Dict[str, Any]:
    """Run a complete health check and return the report"""
    checker = HealthChecker()
    results = checker.run_all_checks()
    report = checker.generate_report(results)
    
    # Print report to console
    checker.print_report(results, verbose=verbose)
    
    # Save report if requested
    if save_report:
        filepath = checker.save_report(report)
        print(f"Report saved to: {filepath}")
    
    return report


def check_critical_dependencies() -> bool:
    """Quick check of critical dependencies only"""
    checker = HealthChecker()
    
    # Check only critical items
    critical_checks = [
        checker.check_python_version(),
        checker.check_ffmpeg(),
        checker.check_python_package('PyQt5', required=True),
        checker.check_output_directory_permissions()
    ]
    
    # Return True if all critical checks pass
    return all(result.status != "error" for result in critical_checks)


if __name__ == "__main__":
    # Run health check when module is executed directly
    import argparse
    
    parser = argparse.ArgumentParser(description="Run health checks for Slideshow Editor")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("-s", "--save", action="store_true", help="Save report to file")
    
    args = parser.parse_args()
    
    run_health_check(verbose=args.verbose, save_report=args.save)
