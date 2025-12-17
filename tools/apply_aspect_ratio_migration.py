#!/usr/bin/env python3
"""
Apply Aspect Ratio Migration (Non-Interactive)

This script applies the aspect ratio migration to the production Reel Tracker CSV
without requiring user interaction.

Usage:
    python apply_aspect_ratio_migration.py [--dry-run]
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csv_column_migrator import ColumnMigrator, AspectRatioMigrator, print_migration_report


def main():
    """Apply the aspect ratio migration."""
    
    parser = argparse.ArgumentParser(description="Apply aspect ratio migration to Reel Tracker CSV")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run only")
    args = parser.parse_args()
    
    # Production CSV path (use Windows path when running with Windows Python)
    if sys.platform == "win32":
        csv_path = r"E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv"
    else:
        csv_path = "/mnt/e/VIDEOS/RELEASE CONTENT/bedrot-reel-tracker.csv"
    
    # Verify CSV exists
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        sys.exit(1)
    
    print("="*60)
    print("[ASPECT RATIO MIGRATION]")
    print("="*60)
    print(f"\nTarget CSV: {csv_path}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    
    # Get file info
    file_size = os.path.getsize(csv_path) / 1024  # KB
    print(f"File Size: {file_size:.1f} KB")
    
    # Count rows
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        row_count = sum(1 for line in f) - 1  # Subtract header
    print(f"Data Rows: {row_count}")
    
    if args.dry_run:
        # Dry run mode
        print("\n[DRY RUN MODE] - No changes will be saved")
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_csv = os.path.join(temp_dir, f"reel_tracker_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        shutil.copy2(csv_path, temp_csv)
        
        try:
            migrator = ColumnMigrator(temp_csv)
            result = migrator.add_column(
                column_name="Aspect Ratio",
                default_value="unknown",
                backfill_func=AspectRatioMigrator.backfill_aspect_ratio,
                overwrite_existing=False,
                create_backup=False
            )
            
            print_migration_report(result)
            
            # Calculate success rate
            total_processed = result.rows_updated + result.rows_unknown
            if total_processed > 0:
                success_rate = (result.rows_updated / total_processed) * 100
                print(f"\n[RESULT] Achieved {success_rate:.1f}% backfill rate")
            
            os.remove(temp_csv)
            
        except Exception as e:
            print(f"[ERROR] Dry run failed: {str(e)}")
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
            sys.exit(1)
    
    else:
        # Production mode
        print("\n[PRODUCTION MODE] - Applying changes")
        
        # Create backup directory
        backup_dir = Path(csv_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        try:
            migrator = ColumnMigrator(csv_path, backup_dir=str(backup_dir))
            
            result = migrator.add_column(
                column_name="Aspect Ratio",
                default_value="unknown",
                backfill_func=AspectRatioMigrator.backfill_aspect_ratio,
                overwrite_existing=False,
                create_backup=True
            )
            
            print_migration_report(result)
            
            print("\n[SUCCESS] Migration completed successfully!")
            print(f"Backup saved to: {result.backup_path}")
            print(f"Updated CSV: {result.output_path}")
            
            # Test idempotency
            print("\n[IDEMPOTENCY TEST]")
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_csv2 = os.path.join(temp_dir, f"reel_tracker_idempotent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            shutil.copy2(csv_path, temp_csv2)
            
            migrator2 = ColumnMigrator(temp_csv2)
            result2 = migrator2.add_column(
                column_name="Aspect Ratio",
                default_value="unknown",
                backfill_func=AspectRatioMigrator.backfill_aspect_ratio,
                overwrite_existing=False,
                create_backup=False
            )
            
            if result2.rows_updated == 0 and result2.rows_unchanged > 0:
                print("[SUCCESS] Idempotency verified - no changes on re-run")
            else:
                print(f"[WARNING] {result2.rows_updated} rows changed on re-run")
            
            os.remove(temp_csv2)
            
            print("\n" + "="*60)
            print("[MIGRATION COMPLETE]")
            print("="*60)
            
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()