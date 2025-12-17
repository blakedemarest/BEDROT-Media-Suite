#!/usr/bin/env python3
"""
Apply Video-Based Aspect Ratio Migration
========================================

This script applies the enhanced video-based aspect ratio migration to the 
production Reel Tracker CSV, scanning actual video files to determine their
true dimensions rather than relying on filename heuristics.

Usage:
    python apply_video_aspect_ratio_migration.py [--dry-run] [--verbose]
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_aspect_ratio_migrator import (
    VideoAspectRatioMigrator, 
    print_video_scan_report
)
from csv_column_migrator import print_migration_report


def main():
    """Apply the enhanced video-based aspect ratio migration."""
    
    parser = argparse.ArgumentParser(
        description="Apply video-based aspect ratio migration to Reel Tracker CSV"
    )
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run only")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing Aspect Ratio column")
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(message)s'
    )
    
    # Production CSV path (use Windows path when running with Windows Python)
    if sys.platform == "win32":
        csv_path = r"E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv"
    else:
        csv_path = "/mnt/e/VIDEOS/RELEASE CONTENT/bedrot-reel-tracker.csv"
    
    # Verify CSV exists
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        sys.exit(1)
    
    print("="*80)
    print("[ENHANCED VIDEO-BASED ASPECT RATIO MIGRATION]")
    print("="*80)
    print(f"\nTarget CSV: {csv_path}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    print(f"Overwrite existing: {'Yes' if args.overwrite else 'No'}")
    
    # Get file info
    file_size = os.path.getsize(csv_path) / 1024  # KB
    print(f"File Size: {file_size:.1f} KB")
    
    # Count rows
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        row_count = sum(1 for line in f) - 1  # Subtract header
    print(f"Data Rows: {row_count}")
    
    # Initialize enhanced migrator
    print(f"\n[INITIALIZATION]")
    video_migrator = VideoAspectRatioMigrator()
    
    if video_migrator.ffprobe_available:
        print(f"[SUCCESS] FFprobe found at: {video_migrator.ffprobe_path}")
        print(f"[INFO] Will scan actual video files for dimensions")
    else:
        print(f"[WARNING] FFprobe not available - using heuristic fallback only")
        print(f"[INFO] Install FFmpeg to enable video file scanning")
    
    if args.dry_run:
        # Dry run mode
        print(f"\n[DRY RUN MODE] - No changes will be saved")
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_csv = os.path.join(temp_dir, f"reel_tracker_video_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        shutil.copy2(csv_path, temp_csv)
        
        try:
            migration_result, scan_result = video_migrator.migrate_with_video_scanning(
                temp_csv,
                overwrite_existing=args.overwrite,
                create_backup=False
            )
            
            print_migration_report(migration_result)
            print_video_scan_report(scan_result)
            
            # Calculate success rates
            if migration_result.rows_updated + migration_result.rows_unknown > 0:
                total_processed = migration_result.rows_updated + migration_result.rows_unknown
                backfill_rate = (migration_result.rows_updated / total_processed) * 100
                print(f"\n[BACKFILL RESULTS]")
                print(f"Total rows processed: {total_processed}")
                print(f"Successfully backfilled: {migration_result.rows_updated}")
                print(f"Backfill success rate: {backfill_rate:.1f}%")
            
            if scan_result.total_files > 0:
                video_success_rate = (scan_result.scanned_successfully / scan_result.total_files) * 100
                print(f"Video scanning success rate: {video_success_rate:.1f}%")
            
            os.remove(temp_csv)
            
        except Exception as e:
            print(f"[ERROR] Dry run failed: {str(e)}")
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
            sys.exit(1)
    
    else:
        # Production mode
        print(f"\n[PRODUCTION MODE] - Applying changes")
        
        # Create backup directory
        backup_dir = Path(csv_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        print(f"Backup directory: {backup_dir}")
        
        try:
            migration_result, scan_result = video_migrator.migrate_with_video_scanning(
                csv_path,
                overwrite_existing=args.overwrite,
                create_backup=True
            )
            
            print_migration_report(migration_result)
            print_video_scan_report(scan_result)
            
            print(f"\n[SUCCESS] Enhanced migration completed successfully!")
            print(f"Backup saved to: {migration_result.backup_path}")
            print(f"Updated CSV: {migration_result.output_path}")
            
            # Performance summary
            print(f"\n[PERFORMANCE SUMMARY]")
            print(f"Total processing time: {scan_result.processing_time:.2f} seconds")
            if scan_result.total_files > 0:
                avg_time_per_file = scan_result.processing_time / scan_result.total_files
                print(f"Average time per file: {avg_time_per_file:.3f} seconds")
            
            # Test idempotency if we made changes
            if migration_result.rows_updated > 0:
                print(f"\n[IDEMPOTENCY TEST]")
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_csv2 = os.path.join(temp_dir, f"reel_tracker_video_idempotent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                shutil.copy2(csv_path, temp_csv2)
                
                # Create new migrator for idempotency test
                test_migrator = VideoAspectRatioMigrator()
                result2, scan2 = test_migrator.migrate_with_video_scanning(
                    temp_csv2,
                    overwrite_existing=False,
                    create_backup=False
                )
                
                if result2.rows_updated == 0 and result2.rows_unchanged > 0:
                    print(f"[SUCCESS] Idempotency verified - no changes on re-run")
                else:
                    print(f"[WARNING] {result2.rows_updated} rows changed on re-run")
                
                os.remove(temp_csv2)
            
            print(f"\n" + "="*80)
            print(f"[MIGRATION COMPLETE]")
            print(f"="*80)
            
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {str(e)}")
            import traceback
            if args.verbose:
                print(f"[DEBUG] Full traceback:")
                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()