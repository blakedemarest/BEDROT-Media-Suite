#!/usr/bin/env python3
"""
Enhanced Video-Based Aspect Ratio Migration Tool
================================================

This module provides video-based aspect ratio detection that scans actual video files
to determine their true dimensions, rather than relying on filename or keyword heuristics.

Features:
- FFprobe integration for accurate video dimension scanning
- Robust error handling for missing/inaccessible files
- Comprehensive aspect ratio categorization
- Fallback to heuristics when video scanning fails
- Detailed progress tracking and reporting
- Idempotent operation with backup support

Author: BEDROT PRODUCTIONS
Version: 2.0.0
"""

import os
import sys
import json
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from fractions import Fraction
import logging
from dataclasses import dataclass
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the existing migrator for fallback functionality
from csv_column_migrator import (
    ColumnMigrator, 
    AspectRatioMigrator, 
    MigrationResult, 
    print_migration_report
)


@dataclass
class VideoScanResult:
    """Results of video file scanning operation."""
    total_files: int
    scanned_successfully: int  
    scan_failures: int
    missing_files: int
    heuristic_fallbacks: int
    processing_time: float
    scan_details: Dict[str, Dict[str, Any]]
    error_summary: Dict[str, int]


class VideoAspectRatioMigrator(AspectRatioMigrator):
    """
    Enhanced aspect ratio migrator that scans actual video files for dimensions.
    
    Inherits from AspectRatioMigrator to maintain compatibility with existing 
    heuristic-based detection while adding video file scanning capabilities.
    """
    
    # Enhanced canonical ratios with more precision
    CANONICAL_RATIOS = {
        (9, 16): "9:16",   # Vertical - Reels, Shorts, TikTok
        (16, 9): "16:9",   # Horizontal - YouTube, landscape
        (1, 1): "1:1",     # Square - Instagram posts
        (4, 5): "4:5",     # Portrait - Instagram posts
        (5, 4): "5:4",     # Landscape alternative
        (3, 4): "3:4",     # Portrait alternative
        (4, 3): "4:3",     # Traditional TV
        (21, 9): "21:9",   # Ultrawide
        (2, 3): "2:3",     # Portrait
        (3, 2): "3:2",     # Landscape photo
        (16, 10): "16:10", # Computer monitor
        (9, 21): "9:21",   # Ultra-tall mobile
        (18, 9): "18:9",   # Modern mobile
    }
    
    # Common video resolutions and their expected ratios
    COMMON_RESOLUTIONS = {
        (1920, 1080): "16:9",
        (1280, 720): "16:9",
        (1080, 1920): "9:16",
        (720, 1280): "9:16",
        (1080, 1080): "1:1",
        (1024, 1024): "1:1",
        (1080, 1350): "4:5",
        (1350, 1080): "5:4",
        (2560, 1440): "16:9",
        (3840, 2160): "16:9",  # 4K
        (1440, 2560): "9:16",  # Vertical 2K
        (2160, 3840): "9:16",  # Vertical 4K
    }
    
    def __init__(self):
        """Initialize the video aspect ratio migrator."""
        super().__init__()
        self.ffprobe_path = self._find_ffprobe()
        self.ffprobe_available = self.ffprobe_path is not None
        self.scan_cache = {}  # Cache for video scan results
        self.logger = logging.getLogger(__name__)
        
        if not self.ffprobe_available:
            self.logger.warning("FFprobe not found. Will use heuristic fallback for all files.")
    
    def _find_ffprobe(self) -> Optional[str]:
        """Find FFprobe executable in PATH."""
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                return 'ffprobe'
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        # Try common Windows locations
        if os.name == 'nt':
            common_paths = [
                'C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe',
                'C:\\ffmpeg\\bin\\ffprobe.exe',
                'C:\\Program Files (x86)\\ffmpeg\\bin\\ffprobe.exe',
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def scan_video_file(self, file_path: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Scan a video file to get its actual dimensions.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Tuple of (width, height, error_message)
            Returns (None, None, error_msg) if scanning fails
        """
        if not self.ffprobe_available:
            return None, None, "FFprobe not available"
        
        # Check cache first
        if file_path in self.scan_cache:
            cached = self.scan_cache[file_path]
            return cached.get('width'), cached.get('height'), cached.get('error')
        
        # Convert Windows paths if needed
        scan_path = file_path
        if os.name != 'nt' and file_path.startswith('E:'):
            # Convert Windows E: path to WSL mount
            scan_path = file_path.replace('E:', '/mnt/e')
            scan_path = scan_path.replace('\\', '/')
        
        # Check if file exists
        if not os.path.exists(scan_path):
            error = f"File not found: {scan_path}"
            self.scan_cache[file_path] = {'width': None, 'height': None, 'error': error}
            return None, None, error
        
        # Build FFprobe command
        command = [
            self.ffprobe_path,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            scan_path
        ]
        
        try:
            # Set creation flags for Windows to hide console
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=creationflags,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                error = f"FFprobe error: {result.stderr.strip()}"
                self.scan_cache[file_path] = {'width': None, 'height': None, 'error': error}
                return None, None, error
            
            # Parse output: should be "width,height"
            output = result.stdout.strip()
            if ',' not in output:
                error = f"Unexpected FFprobe output: {output}"
                self.scan_cache[file_path] = {'width': None, 'height': None, 'error': error}
                return None, None, error
            
            try:
                width_str, height_str = output.split(',')
                width = int(width_str.strip())
                height = int(height_str.strip())
                
                # Cache successful result
                self.scan_cache[file_path] = {'width': width, 'height': height, 'error': None}
                return width, height, None
                
            except (ValueError, AttributeError) as e:
                error = f"Failed to parse dimensions: {e}"
                self.scan_cache[file_path] = {'width': None, 'height': None, 'error': error}
                return None, None, error
        
        except subprocess.TimeoutExpired:
            error = "FFprobe timeout (30s)"
            self.scan_cache[file_path] = {'width': None, 'height': None, 'error': error}
            return None, None, error
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            self.scan_cache[file_path] = {'width': None, 'height': None, 'error': error}
            return None, None, error
    
    def categorize_aspect_ratio(self, width: int, height: int) -> str:
        """
        Categorize aspect ratio with enhanced precision.
        
        Args:
            width: Video width in pixels
            height: Video height in pixels
            
        Returns:
            Canonical aspect ratio string
        """
        if width <= 0 or height <= 0:
            return "unknown"
        
        # Check for exact resolution matches first
        if (width, height) in self.COMMON_RESOLUTIONS:
            return self.COMMON_RESOLUTIONS[(width, height)]
        
        # Calculate simplified ratio
        simplified = self.simplify_ratio(width, height)
        
        # Check for exact canonical ratio match
        if simplified in self.CANONICAL_RATIOS:
            return self.CANONICAL_RATIOS[simplified]
        
        # Calculate decimal ratio for tolerance matching
        ratio = width / height
        
        # Check against canonical ratios with tolerance
        best_match = None
        min_error = float('inf')
        
        for (w, h), canonical in self.CANONICAL_RATIOS.items():
            canonical_ratio = w / h
            error = abs(ratio - canonical_ratio) / canonical_ratio
            
            if error < 0.05 and error < min_error:  # 5% tolerance
                min_error = error
                best_match = canonical
        
        if best_match:
            return best_match
        
        # If no close match, return simplified ratio
        return f"{simplified[0]}:{simplified[1]}"
    
    def scan_video_dimensions(self, file_path: str) -> str:
        """
        Scan video file and return aspect ratio.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Aspect ratio string or "unknown" if scanning fails
        """
        width, height, error = self.scan_video_file(file_path)
        
        if width and height:
            return self.categorize_aspect_ratio(width, height)
        else:
            # Log scanning failure for reporting
            self.logger.debug(f"Video scan failed for {file_path}: {error}")
            return "unknown"
    
    @staticmethod
    def enhanced_backfill_aspect_ratio(row: pd.Series, migrator_instance=None) -> str:
        """
        Enhanced backfill function that prioritizes video file scanning.
        
        Priority order:
        1. Scan actual video file dimensions (NEW)
        2. Explicit width/height columns
        3. Resolution/dimensions string parsing  
        4. Platform/format hints
        5. Default to 'unknown'
        
        Args:
            row: DataFrame row
            migrator_instance: VideoAspectRatioMigrator instance for video scanning
            
        Returns:
            Aspect ratio string
        """
        # Priority 1: Scan actual video file if available
        if migrator_instance and migrator_instance.ffprobe_available:
            # Look for file path in common columns
            file_path_columns = ['FilePath', 'File Path', 'Clip Filename', 'filename', 'path']
            
            for col in file_path_columns:
                if col in row and row[col] and str(row[col]).strip():
                    file_path = str(row[col]).strip()
                    if file_path and file_path.lower() != 'nan':
                        aspect_ratio = migrator_instance.scan_video_dimensions(file_path)
                        if aspect_ratio != "unknown":
                            return aspect_ratio
        
        # Priority 2-4: Fall back to existing heuristic methods
        return AspectRatioMigrator.backfill_aspect_ratio(row)
    
    def migrate_with_video_scanning(self, csv_path: str, **kwargs) -> Tuple[MigrationResult, VideoScanResult]:
        """
        Perform migration with video file scanning.
        
        Args:
            csv_path: Path to CSV file
            **kwargs: Additional arguments for ColumnMigrator.add_column()
            
        Returns:
            Tuple of (MigrationResult, VideoScanResult)
        """
        start_time = time.time()
        
        # Initialize migrator
        migrator = ColumnMigrator(csv_path)
        
        # Prepare enhanced backfill function with self reference
        def backfill_func(row):
            return self.enhanced_backfill_aspect_ratio(row, migrator_instance=self)
        
        # Perform migration
        migration_result = migrator.add_column(
            column_name="Aspect Ratio",
            default_value="unknown",
            backfill_func=backfill_func,
            **kwargs
        )
        
        # Calculate video scan statistics
        total_files = len([path for path in self.scan_cache.keys()])
        successful_scans = len([r for r in self.scan_cache.values() if r['error'] is None])
        failed_scans = total_files - successful_scans
        
        # Count error types
        error_summary = {}
        for result in self.scan_cache.values():
            if result['error']:
                error_type = result['error'].split(':')[0]  # Get error category
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        # Create scan result
        scan_result = VideoScanResult(
            total_files=total_files,
            scanned_successfully=successful_scans,
            scan_failures=failed_scans,
            missing_files=error_summary.get('File not found', 0),
            heuristic_fallbacks=migration_result.rows_unknown if migration_result.rows_unknown > 0 else 0,
            processing_time=time.time() - start_time,
            scan_details=dict(self.scan_cache),
            error_summary=error_summary
        )
        
        return migration_result, scan_result


def print_video_scan_report(scan_result: VideoScanResult):
    """Print detailed video scanning report."""
    print("\n" + "="*60)
    print("[VIDEO SCANNING REPORT]")
    print("="*60)
    
    print(f"\nTotal Files Processed: {scan_result.total_files}")
    print(f"Successfully Scanned: {scan_result.scanned_successfully}")
    print(f"Scan Failures: {scan_result.scan_failures}")
    print(f"Missing Files: {scan_result.missing_files}")
    print(f"Heuristic Fallbacks: {scan_result.heuristic_fallbacks}")
    print(f"Processing Time: {scan_result.processing_time:.2f} seconds")
    
    if scan_result.total_files > 0:
        success_rate = (scan_result.scanned_successfully / scan_result.total_files) * 100
        print(f"Video Scan Success Rate: {success_rate:.1f}%")
    
    if scan_result.error_summary:
        print(f"\n[ERROR BREAKDOWN]")
        for error_type, count in sorted(scan_result.error_summary.items()):
            print(f"  {error_type}: {count} files")
    
    # Show sample of scan details (first 5 successful and 5 failed)
    successful_samples = [(path, details) for path, details in scan_result.scan_details.items() 
                         if details['error'] is None][:5]
    failed_samples = [(path, details) for path, details in scan_result.scan_details.items() 
                     if details['error'] is not None][:5]
    
    if successful_samples:
        print(f"\n[SUCCESSFUL SCANS - Sample]")
        for path, details in successful_samples:
            filename = os.path.basename(path)
            print(f"  {filename}: {details['width']}x{details['height']}")
    
    if failed_samples:
        print(f"\n[FAILED SCANS - Sample]")
        for path, details in failed_samples:
            filename = os.path.basename(path)
            error = details['error'][:50] + "..." if len(details['error']) > 50 else details['error']
            print(f"  {filename}: {error}")
    
    print("\n" + "="*60)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Video-Based Aspect Ratio Migration - Scan actual video files for true dimensions"
    )
    
    parser.add_argument(
        "csv_path",
        help="Path to the CSV file to migrate"
    )
    
    parser.add_argument(
        "--output",
        help="Output path for modified CSV (default: overwrite original)"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing column values"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(message)s'
    )
    
    try:
        print("="*60)
        print("[ENHANCED VIDEO ASPECT RATIO MIGRATION]")
        print("="*60)
        print(f"Target CSV: {args.csv_path}")
        print(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
        
        # Initialize enhanced migrator
        video_migrator = VideoAspectRatioMigrator()
        
        if not video_migrator.ffprobe_available:
            print(f"\n[WARNING] FFprobe not found - using heuristic fallback only")
        else:
            print(f"[INFO] FFprobe available - will scan actual video files")
        
        # Perform migration
        migration_kwargs = {
            'overwrite_existing': args.overwrite,
            'save_to': args.output if not args.dry_run else None,
            'create_backup': not args.no_backup and not args.dry_run
        }
        
        if args.dry_run:
            print("\n[DRY RUN MODE] - No changes will be saved")
        
        migration_result, scan_result = video_migrator.migrate_with_video_scanning(
            args.csv_path, 
            **migration_kwargs
        )
        
        # Print reports
        print_migration_report(migration_result)
        print_video_scan_report(scan_result)
        
        if args.dry_run:
            print("\n[DRY RUN COMPLETE] - No files were modified")
        else:
            print("\n[SUCCESS] Enhanced migration completed!")
            if migration_result.backup_path:
                print(f"Backup saved to: {migration_result.backup_path}")
            print(f"Updated CSV: {migration_result.output_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()