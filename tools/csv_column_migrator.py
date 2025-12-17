#!/usr/bin/env python3
"""
CSV Column Migration Tool for Reel Tracker

A generic, reusable framework for adding new columns to CSV files with:
- Idempotent operations (safe to run multiple times)
- Backfill logic with configurable strategies
- Non-destructive by default (creates backups)
- Validation and reporting
- Extensible for future column additions

Author: BEDROT PRODUCTIONS
Version: 1.0.0
"""

import os
import sys
import json
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Tuple
from fractions import Fraction
import re
import logging
from dataclasses import dataclass
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@dataclass
class MigrationResult:
    """Results of a column migration operation."""
    total_rows: int
    rows_added: int
    rows_updated: int
    rows_unchanged: int
    rows_unknown: int
    backup_path: Optional[str]
    output_path: str
    column_name: str
    value_distribution: Dict[str, int]
    errors: List[str]
    warnings: List[str]


class ColumnMigrator:
    """
    Generic column migration utility for CSV files.
    
    Provides a framework for adding new columns with backfill logic,
    validation, and idempotent operations.
    """
    
    def __init__(self, csv_path: str, backup_dir: Optional[str] = None):
        """
        Initialize the migrator with a CSV file.
        
        Args:
            csv_path: Path to the CSV file to migrate
            backup_dir: Directory for backups (default: same as CSV)
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.backup_dir = Path(backup_dir) if backup_dir else self.csv_path.parent
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load the CSV
        self.df = self._load_csv()
        self.original_columns = list(self.df.columns)
        
    def _load_csv(self) -> pd.DataFrame:
        """Load CSV with proper encoding handling."""
        try:
            # Try UTF-8 with BOM first
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            # Fallback to latin-1
            df = pd.read_csv(self.csv_path, encoding='latin-1')
        
        # Handle empty values
        df = df.fillna('')
        return df
    
    def _create_backup(self) -> str:
        """Create a timestamped backup of the original CSV."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{self.csv_path.stem}_backup_{timestamp}.csv"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(self.csv_path, backup_path)
        self.logger.info(f"Created backup: {backup_path}")
        return str(backup_path)
    
    def add_column(
        self,
        column_name: str,
        default_value: Any = '',
        backfill_func: Optional[Callable] = None,
        overwrite_existing: bool = False,
        save_to: Optional[str] = None,
        create_backup: bool = True
    ) -> MigrationResult:
        """
        Add a new column to the CSV with optional backfill logic.
        
        Args:
            column_name: Name of the column to add
            default_value: Default value for new column
            backfill_func: Function to compute values for existing rows
                          Should accept a row (pd.Series) and return a value
            overwrite_existing: If True, overwrite existing column values
            save_to: Output path (default: overwrite original)
            create_backup: Whether to create a backup before modifying
            
        Returns:
            MigrationResult with statistics and paths
        """
        result = MigrationResult(
            total_rows=len(self.df),
            rows_added=0,
            rows_updated=0,
            rows_unchanged=0,
            rows_unknown=0,
            backup_path=None,
            output_path=save_to or str(self.csv_path),
            column_name=column_name,
            value_distribution={},
            errors=[],
            warnings=[]
        )
        
        # Create backup if requested
        if create_backup:
            result.backup_path = self._create_backup()
        
        # Check if column exists
        column_exists = column_name in self.df.columns
        
        if column_exists and not overwrite_existing:
            result.warnings.append(f"Column '{column_name}' already exists. Skipping addition.")
            result.rows_unchanged = len(self.df)
            
            # Still apply backfill to empty values if function provided
            if backfill_func:
                empty_mask = self.df[column_name].astype(str).str.strip() == ''
                empty_count = empty_mask.sum()
                
                if empty_count > 0:
                    self.logger.info(f"Found {empty_count} empty values to backfill")
                    for idx in self.df[empty_mask].index:
                        try:
                            new_value = backfill_func(self.df.loc[idx])
                            if new_value and new_value != default_value:
                                self.df.at[idx, column_name] = new_value
                                result.rows_updated += 1
                            else:
                                result.rows_unknown += 1
                        except Exception as e:
                            result.errors.append(f"Row {idx}: {str(e)}")
                            result.rows_unknown += 1
                    
                    result.rows_unchanged = len(self.df) - result.rows_updated - result.rows_unknown
        else:
            # Add new column or overwrite existing
            if not column_exists:
                self.df[column_name] = default_value
                result.rows_added = len(self.df)
                self.logger.info(f"Added column '{column_name}' with default value: {default_value}")
            else:
                self.logger.info(f"Overwriting existing column '{column_name}'")
                self.df[column_name] = default_value
                result.rows_added = len(self.df)
            
            # Apply backfill function if provided
            if backfill_func:
                for idx, row in self.df.iterrows():
                    try:
                        computed_value = backfill_func(row)
                        if computed_value and computed_value != default_value:
                            self.df.at[idx, column_name] = computed_value
                            result.rows_updated += 1
                        elif computed_value == default_value:
                            result.rows_unknown += 1
                    except Exception as e:
                        result.errors.append(f"Row {idx}: {str(e)}")
                        self.df.at[idx, column_name] = default_value
                        result.rows_unknown += 1
                
                result.rows_unchanged = 0  # All rows were processed
        
        # Calculate value distribution
        value_counts = self.df[column_name].value_counts()
        result.value_distribution = value_counts.to_dict()
        
        # Save the modified CSV
        output_path = Path(save_to) if save_to else self.csv_path
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"Saved modified CSV to: {output_path}")
        
        return result
    
    def validate_column(self, column_name: str, validation_func: Callable) -> Dict[str, Any]:
        """
        Validate values in a column using a custom function.
        
        Args:
            column_name: Column to validate
            validation_func: Function that accepts a value and returns (is_valid, error_msg)
            
        Returns:
            Validation report dictionary
        """
        if column_name not in self.df.columns:
            return {"error": f"Column '{column_name}' not found"}
        
        results = {
            "total": len(self.df),
            "valid": 0,
            "invalid": 0,
            "invalid_rows": [],
            "error_messages": {}
        }
        
        for idx, value in self.df[column_name].items():
            is_valid, error_msg = validation_func(value)
            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["invalid_rows"].append(idx)
                if error_msg not in results["error_messages"]:
                    results["error_messages"][error_msg] = []
                results["error_messages"][error_msg].append(idx)
        
        return results


class AspectRatioMigrator:
    """
    Specialized migrator for adding aspect_ratio column with intelligent backfill.
    """
    
    # Common aspect ratios and their canonical representations
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
    }
    
    # Platform hints for aspect ratio defaults
    PLATFORM_HINTS = {
        'reel': '9:16',
        'reels': '9:16',
        'short': '9:16',
        'shorts': '9:16',
        'tiktok': '9:16',
        'story': '9:16',
        'stories': '9:16',
        'igtv': '9:16',
        'youtube': '16:9',
        'landscape': '16:9',
        'horizontal': '16:9',
        'square': '1:1',
        'post': '4:5',
        'feed': '4:5',
    }
    
    # Common resolution patterns
    RESOLUTION_PATTERNS = [
        r'(\d+)\s*[xX×]\s*(\d+)',  # 1920x1080, 1920X1080, 1920×1080
        r'(\d+)\s*[,]\s*(\d+)',     # 1920,1080
        r'w[idth]*\s*[:=]\s*(\d+).*h[eight]*\s*[:=]\s*(\d+)',  # width:1920 height:1080
        r'h[eight]*\s*[:=]\s*(\d+).*w[idth]*\s*[:=]\s*(\d+)',  # height:1080 width:1920
    ]
    
    @staticmethod
    def simplify_ratio(width: int, height: int) -> Tuple[int, int]:
        """Reduce aspect ratio to simplest terms."""
        if width == 0 or height == 0:
            return (0, 0)
        
        # Use Fraction for accurate simplification
        frac = Fraction(width, height)
        return (frac.numerator, frac.denominator)
    
    @staticmethod
    def get_canonical_ratio(width: int, height: int) -> str:
        """Get canonical representation of aspect ratio."""
        simplified = AspectRatioMigrator.simplify_ratio(width, height)
        
        # Check for exact match in canonical ratios
        if simplified in AspectRatioMigrator.CANONICAL_RATIOS:
            return AspectRatioMigrator.CANONICAL_RATIOS[simplified]
        
        # Check if close to a canonical ratio (within 5% tolerance)
        if width > 0 and height > 0:
            ratio = width / height
            for (w, h), canonical in AspectRatioMigrator.CANONICAL_RATIOS.items():
                canonical_ratio = w / h
                if abs(ratio - canonical_ratio) / canonical_ratio < 0.05:
                    return canonical
        
        # Return simplified ratio if no canonical match
        if simplified != (0, 0):
            return f"{simplified[0]}:{simplified[1]}"
        
        return "unknown"
    
    @staticmethod
    def extract_from_resolution_string(text: str) -> Optional[Tuple[int, int]]:
        """Extract width and height from various resolution string formats."""
        if not text or not isinstance(text, str):
            return None
        
        text = str(text).strip()
        
        for pattern in AspectRatioMigrator.RESOLUTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if 'width' in pattern.lower() or 'height' in pattern.lower():
                        # Named groups pattern
                        if 'width' in pattern.lower() and pattern.index('width') < pattern.index('height'):
                            width, height = int(match.group(1)), int(match.group(2))
                        else:
                            height, width = int(match.group(1)), int(match.group(2))
                    else:
                        # Simple pattern - assume width x height
                        width, height = int(match.group(1)), int(match.group(2))
                    
                    return (width, height)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @staticmethod
    def infer_from_platform_hints(row: pd.Series) -> Optional[str]:
        """Infer aspect ratio from platform or format hints in the data."""
        # Check multiple columns for hints
        hint_columns = ['Reel Type', 'Platform', 'Format', 'Description', 'Caption', 'Clip Filename']
        
        for col in hint_columns:
            if col in row and row[col]:
                text = str(row[col]).lower()
                for keyword, ratio in AspectRatioMigrator.PLATFORM_HINTS.items():
                    if keyword in text:
                        return ratio
        
        return None
    
    @staticmethod
    def backfill_aspect_ratio(row: pd.Series) -> str:
        """
        Intelligent backfill function for aspect_ratio column.
        
        Priority order:
        1. Explicit width/height columns
        2. Resolution/dimensions string parsing
        3. Platform/format hints
        4. Default to 'unknown'
        """
        # Priority 1: Check for explicit width/height columns
        width_cols = ['width', 'Width', 'video_width', 'frame_width']
        height_cols = ['height', 'Height', 'video_height', 'frame_height']
        
        width = None
        height = None
        
        for w_col in width_cols:
            if w_col in row and row[w_col]:
                try:
                    width = int(row[w_col])
                    break
                except (ValueError, TypeError):
                    continue
        
        for h_col in height_cols:
            if h_col in row and row[h_col]:
                try:
                    height = int(row[h_col])
                    break
                except (ValueError, TypeError):
                    continue
        
        if width and height:
            return AspectRatioMigrator.get_canonical_ratio(width, height)
        
        # Priority 2: Look for resolution strings in various columns
        resolution_cols = ['resolution', 'Resolution', 'dimensions', 'Dimensions', 
                          'size', 'Size', 'video_info', 'metadata']
        
        for col in resolution_cols:
            if col in row and row[col]:
                dims = AspectRatioMigrator.extract_from_resolution_string(str(row[col]))
                if dims:
                    return AspectRatioMigrator.get_canonical_ratio(dims[0], dims[1])
        
        # Also check the filename for resolution hints (e.g., "video_1920x1080.mp4")
        if 'Clip Filename' in row and row['Clip Filename']:
            dims = AspectRatioMigrator.extract_from_resolution_string(str(row['Clip Filename']))
            if dims:
                return AspectRatioMigrator.get_canonical_ratio(dims[0], dims[1])
        
        # Priority 3: Platform/format hints
        platform_ratio = AspectRatioMigrator.infer_from_platform_hints(row)
        if platform_ratio:
            return platform_ratio
        
        # Priority 4: Default to unknown
        return "unknown"


def print_migration_report(result: MigrationResult):
    """Print a formatted migration report."""
    print("\n" + "="*60)
    print("[MIGRATION REPORT]")
    print("="*60)
    
    print(f"\nColumn: {result.column_name}")
    print(f"Total Rows: {result.total_rows}")
    print(f"Rows Added: {result.rows_added}")
    print(f"Rows Updated: {result.rows_updated}")
    print(f"Rows Unchanged: {result.rows_unchanged}")
    print(f"Rows Unknown: {result.rows_unknown}")
    
    if result.rows_updated > 0:
        success_rate = (result.rows_updated / (result.rows_updated + result.rows_unknown)) * 100
        print(f"Backfill Success Rate: {success_rate:.1f}%")
    
    print(f"\nOutput Path: {result.output_path}")
    if result.backup_path:
        print(f"Backup Path: {result.backup_path}")
    
    print("\n[VALUE DISTRIBUTION]")
    sorted_dist = sorted(result.value_distribution.items(), key=lambda x: x[1], reverse=True)
    for value, count in sorted_dist[:10]:  # Show top 10
        percentage = (count / result.total_rows) * 100
        print(f"  {value}: {count} ({percentage:.1f}%)")
    
    if len(sorted_dist) > 10:
        print(f"  ... and {len(sorted_dist) - 10} more unique values")
    
    if result.warnings:
        print("\n[WARNINGS]")
        for warning in result.warnings[:5]:
            print(f"  - {warning}")
    
    if result.errors:
        print("\n[ERRORS]")
        for error in result.errors[:5]:
            print(f"  - {error}")
        if len(result.errors) > 5:
            print(f"  ... and {len(result.errors) - 5} more errors")
    
    print("\n" + "="*60)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="CSV Column Migration Tool - Add new columns with intelligent backfill"
    )
    
    parser.add_argument(
        "csv_path",
        help="Path to the CSV file to migrate"
    )
    
    parser.add_argument(
        "--column",
        default="aspect_ratio",
        help="Name of the column to add (default: aspect_ratio)"
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
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    
    try:
        # Initialize migrator
        migrator = ColumnMigrator(args.csv_path)
        
        # Determine backfill function based on column
        if args.column == "aspect_ratio":
            backfill_func = AspectRatioMigrator.backfill_aspect_ratio
            default_value = "unknown"
        else:
            # For other columns, no backfill by default
            backfill_func = None
            default_value = ""
        
        # Perform migration
        if args.dry_run:
            print("[DRY RUN MODE] - No changes will be saved")
            # Create a copy for dry run
            migrator.df = migrator.df.copy()
        
        result = migrator.add_column(
            column_name=args.column,
            default_value=default_value,
            backfill_func=backfill_func,
            overwrite_existing=args.overwrite,
            save_to=args.output if not args.dry_run else None,
            create_backup=not args.no_backup and not args.dry_run
        )
        
        # Print report
        print_migration_report(result)
        
        if args.dry_run:
            print("\n[DRY RUN COMPLETE] - No files were modified")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()