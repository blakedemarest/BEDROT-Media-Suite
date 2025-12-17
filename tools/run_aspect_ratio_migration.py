#!/usr/bin/env python3
"""
Run Aspect Ratio Migration for Reel Tracker CSV

This script runs the aspect ratio migration on the production Reel Tracker CSV.
It performs a dry run first, then asks for confirmation before applying changes.

Usage:
    python run_aspect_ratio_migration.py
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csv_column_migrator import ColumnMigrator, AspectRatioMigrator, print_migration_report


def main():
    """Run the aspect ratio migration with safety checks."""
    
    # Production CSV path (use Windows path when running with Windows Python)
    if sys.platform == "win32":
        csv_path = r"E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv"
    else:
        csv_path = "/mnt/e/VIDEOS/RELEASE CONTENT/bedrot-reel-tracker.csv"
    
    # Verify CSV exists
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        print("Please ensure the file exists at: E:\\VIDEOS\\RELEASE CONTENT\\bedrot-reel-tracker.csv")
        sys.exit(1)
    
    print("="*60)
    print("[ASPECT RATIO MIGRATION TOOL]")
    print("="*60)
    print(f"\nTarget CSV: {csv_path}")
    
    # Get file info
    file_size = os.path.getsize(csv_path) / 1024  # KB
    print(f"File Size: {file_size:.1f} KB")
    
    # Count rows
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        row_count = sum(1 for line in f) - 1  # Subtract header
    print(f"Data Rows: {row_count}")
    
    # Step 1: Dry Run
    print("\n" + "-"*40)
    print("[STEP 1: DRY RUN]")
    print("-"*40)
    print("Performing dry run to preview changes...")
    
    try:
        # Create temporary copy for dry run
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_csv = os.path.join(temp_dir, f"reel_tracker_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        shutil.copy2(csv_path, temp_csv)
        
        # Run migration on temp file
        migrator = ColumnMigrator(temp_csv)
        result = migrator.add_column(
            column_name="Aspect Ratio",
            default_value="unknown",
            backfill_func=AspectRatioMigrator.backfill_aspect_ratio,
            overwrite_existing=False,
            create_backup=False
        )
        
        # Show results
        print_migration_report(result)
        
        # Calculate success rate
        total_processed = result.rows_updated + result.rows_unknown
        if total_processed > 0:
            success_rate = (result.rows_updated / total_processed) * 100
            
            if success_rate >= 95:
                print(f"\n[SUCCESS] Achieved {success_rate:.1f}% backfill rate!")
            elif success_rate >= 80:
                print(f"\n[GOOD] Achieved {success_rate:.1f}% backfill rate")
            else:
                print(f"\n[WARNING] Only {success_rate:.1f}% backfill rate")
        
        # Clean up temp file
        os.remove(temp_csv)
        
    except Exception as e:
        print(f"[ERROR] Dry run failed: {str(e)}")
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        sys.exit(1)
    
    # Step 2: Ask for confirmation
    print("\n" + "-"*40)
    print("[STEP 2: CONFIRMATION]")
    print("-"*40)
    
    response = input("\nDo you want to apply these changes to the production CSV? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n[CANCELLED] Migration cancelled by user")
        sys.exit(0)
    
    # Step 3: Create backup directory
    backup_dir = Path(csv_path).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Step 4: Apply migration
    print("\n" + "-"*40)
    print("[STEP 3: APPLYING MIGRATION]")
    print("-"*40)
    
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
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        print("Your original CSV has not been modified.")
        sys.exit(1)
    
    # Step 5: Test idempotency
    print("\n" + "-"*40)
    print("[STEP 4: IDEMPOTENCY TEST]")
    print("-"*40)
    print("Testing that re-running migration doesn't change data...")
    
    try:
        # Create another temp copy
        temp_csv2 = os.path.join(temp_dir, f"reel_tracker_idempotent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        shutil.copy2(csv_path, temp_csv2)
        
        # Run migration again
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
        
    except Exception as e:
        print(f"[WARNING] Idempotency test failed: {str(e)}")
        if os.path.exists(temp_csv2):
            os.remove(temp_csv2)
    
    print("\n" + "="*60)
    print("[MIGRATION COMPLETE]")
    print("="*60)
    print("\nNext Steps:")
    print("1. Open Reel Tracker application to verify the new column displays correctly")
    print("2. Check that dropdown values work for Aspect Ratio column")
    print("3. Test adding new reels with aspect ratio values")
    print("\nTo restore original if needed:")
    print(f"  cp '{result.backup_path}' '{csv_path}'")


if __name__ == "__main__":
    main()