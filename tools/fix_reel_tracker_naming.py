#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reel Tracker Naming Convention Fix Script

This script fixes the Reel ID naming convention in CSV files to use 
proper short identifiers instead of full filenames.

Usage:
    python fix_reel_tracker_naming.py [csv_file] [--backup] [--rename-files]
"""

import os
import sys
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import re


def safe_print(message):
    """Print with proper encoding for Windows console."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', 'replace').decode('ascii'))


def generate_short_reel_id(persona, release, index, style="simple"):
    """
    Generate a short Reel ID based on the chosen style.
    
    Args:
        persona: The persona (e.g., "PIG1987")
        release: The release name (e.g., "RENEGADE PIPELINE")
        index: Sequential number
        style: ID style - "simple", "initials", or "dated"
    
    Returns:
        str: Short Reel ID
    """
    if style == "initials":
        # Create initials from release name
        release_parts = release.replace("_", " ").split()
        initials = "".join([part[0] for part in release_parts if part])
        return f"{initials}_{index:03d}"
    elif style == "dated":
        # Use current date
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{date_str}_{index:03d}"
    else:  # simple
        return f"REEL_{index:03d}"


def extract_original_number(reel_id):
    """
    Extract the original sequential number from the old Reel ID if possible.
    
    Args:
        reel_id: Original Reel ID
    
    Returns:
        int or None: Extracted number or None
    """
    # Try to find patterns like "_001_" or "_135_" at the end
    patterns = [
        r"RECOVERED_(\d+)_",  # RECOVERED_001_...
        r"_(\d+)_mp4$",        # ..._135_mp4
        r"_(\d+)$",            # ..._135
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(reel_id))
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return None


def fix_reel_ids(df, style="simple", preserve_numbers=True):
    """
    Fix Reel IDs in the dataframe.
    
    Args:
        df: Pandas DataFrame with reel data
        style: ID generation style
        preserve_numbers: Try to preserve original numbering
    
    Returns:
        DataFrame: Updated dataframe with fixed Reel IDs
    """
    df = df.copy()
    
    # Group by Persona and Release to maintain separate numbering
    groups = df.groupby(['Persona', 'Release'], dropna=False)
    
    for (persona, release), group in groups:
        # Get indices for this group
        indices = group.index
        
        if preserve_numbers:
            # Try to preserve original numbers
            for idx in indices:
                original_id = df.loc[idx, 'Reel ID']
                original_num = extract_original_number(original_id)
                
                if original_num:
                    new_id = generate_short_reel_id(persona, release, original_num, style)
                else:
                    # Fallback to sequential
                    position = list(indices).index(idx) + 1
                    new_id = generate_short_reel_id(persona, release, position, style)
                
                df.loc[idx, 'Reel ID'] = new_id
        else:
            # Simple sequential numbering
            for i, idx in enumerate(indices, 1):
                new_id = generate_short_reel_id(persona, release, i, style)
                df.loc[idx, 'Reel ID'] = new_id
    
    return df


def update_filenames_in_csv(df):
    """
    Update the Clip Filename column to match the new naming convention.
    
    Args:
        df: DataFrame with fixed Reel IDs
    
    Returns:
        DataFrame: Updated dataframe
    """
    df = df.copy()
    
    for idx, row in df.iterrows():
        persona = str(row['Persona']).upper().replace(" ", "_")
        release = str(row['Release']).upper().replace(" ", "_")
        reel_id = row['Reel ID']
        
        # Get original extension
        original_filename = row.get('Clip Filename', '')
        if original_filename and '.' in original_filename:
            extension = Path(original_filename).suffix
        else:
            extension = '.mp4'  # Default
        
        # Generate new filename
        new_filename = f"{persona}_{release}_{reel_id}{extension}"
        df.loc[idx, 'Clip Filename'] = new_filename
        
        # Optionally update FilePath too
        if 'FilePath' in df.columns and pd.notna(row['FilePath']):
            old_path = Path(row['FilePath'])
            if old_path.parent.exists():
                new_path = old_path.parent / new_filename
                df.loc[idx, 'FilePath'] = str(new_path)
    
    return df


def rename_actual_files(df, dry_run=True):
    """
    Rename actual files on disk to match new naming convention.
    
    Args:
        df: DataFrame with updated filenames
        dry_run: If True, only show what would be renamed
    
    Returns:
        list: Results of rename operations
    """
    results = []
    
    for idx, row in df.iterrows():
        if 'FilePath' not in df.columns or pd.isna(row['FilePath']):
            continue
        
        old_path = Path(row['FilePath'])
        
        # Check if old file exists
        if not old_path.exists():
            results.append({
                'reel_id': row['Reel ID'],
                'status': 'not_found',
                'old_path': str(old_path),
                'message': 'Original file not found'
            })
            continue
        
        # Generate new path
        new_filename = row['Clip Filename']
        new_path = old_path.parent / new_filename
        
        if old_path == new_path:
            results.append({
                'reel_id': row['Reel ID'],
                'status': 'unchanged',
                'old_path': str(old_path),
                'message': 'Filename already correct'
            })
            continue
        
        if new_path.exists():
            results.append({
                'reel_id': row['Reel ID'],
                'status': 'conflict',
                'old_path': str(old_path),
                'new_path': str(new_path),
                'message': 'Target filename already exists'
            })
            continue
        
        if dry_run:
            results.append({
                'reel_id': row['Reel ID'],
                'status': 'would_rename',
                'old_path': str(old_path),
                'new_path': str(new_path),
                'message': f'Would rename: {old_path.name} -> {new_path.name}'
            })
        else:
            try:
                old_path.rename(new_path)
                results.append({
                    'reel_id': row['Reel ID'],
                    'status': 'renamed',
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                    'message': f'Successfully renamed: {old_path.name} -> {new_path.name}'
                })
            except Exception as e:
                results.append({
                    'reel_id': row['Reel ID'],
                    'status': 'error',
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                    'message': f'Error renaming: {str(e)}'
                })
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Fix Reel Tracker naming conventions')
    parser.add_argument('csv_file', nargs='?', help='CSV file to fix')
    parser.add_argument('--backup', action='store_true', help='Create backup of original CSV')
    parser.add_argument('--rename-files', action='store_true', help='Actually rename files on disk')
    parser.add_argument('--style', choices=['simple', 'initials', 'dated'], 
                       default='simple', help='Reel ID generation style')
    parser.add_argument('--output', help='Output CSV filename (default: adds _fixed to original)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    # If no CSV file specified, look for common locations
    if not args.csv_file:
        possible_files = [
            'bedrot-reel-tracker.csv',
            'reel_tracker.csv',
            'reels.csv'
        ]
        
        for filename in possible_files:
            if os.path.exists(filename):
                args.csv_file = filename
                safe_print(f"Found CSV file: {filename}")
                break
        else:
            safe_print("Error: No CSV file specified and no default file found")
            safe_print("Usage: python fix_reel_tracker_naming.py [csv_file]")
            return 1
    
    # Check if file exists
    if not os.path.exists(args.csv_file):
        safe_print(f"Error: CSV file not found: {args.csv_file}")
        return 1
    
    # Create backup if requested
    if args.backup:
        backup_name = f"{Path(args.csv_file).stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        shutil.copy2(args.csv_file, backup_name)
        safe_print(f"Created backup: {backup_name}")
    
    # Load CSV
    try:
        df = pd.read_csv(args.csv_file)
        safe_print(f"Loaded {len(df)} rows from {args.csv_file}")
    except Exception as e:
        safe_print(f"Error loading CSV: {e}")
        return 1
    
    # Check required columns
    required_columns = ['Reel ID', 'Persona', 'Release', 'Clip Filename']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        safe_print(f"Error: Missing required columns: {missing_columns}")
        return 1
    
    # Show sample of current data
    safe_print("\nCurrent Reel IDs (first 5):")
    for i, row in df.head().iterrows():
        safe_print(f"  {row['Reel ID']}")
    
    # Fix Reel IDs
    safe_print(f"\nFixing Reel IDs using '{args.style}' style...")
    df_fixed = fix_reel_ids(df, style=args.style)
    
    # Update filenames
    safe_print("Updating filenames to match new convention...")
    df_fixed = update_filenames_in_csv(df_fixed)
    
    # Show sample of fixed data
    safe_print("\nNew Reel IDs and Filenames (first 5):")
    for i, row in df_fixed.head().iterrows():
        safe_print(f"  ID: {row['Reel ID']} -> File: {row['Clip Filename']}")
    
    # Handle file renaming if requested
    if args.rename_files:
        safe_print("\nChecking files to rename...")
        rename_results = rename_actual_files(df_fixed, dry_run=args.dry_run)
        
        # Summary of rename operations
        status_counts = {}
        for result in rename_results:
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if result['status'] in ['would_rename', 'renamed', 'error', 'conflict']:
                safe_print(f"  {result['message']}")
        
        safe_print("\nRename Summary:")
        for status, count in status_counts.items():
            safe_print(f"  {status}: {count}")
    
    # Save fixed CSV
    if not args.dry_run:
        output_file = args.output or f"{Path(args.csv_file).stem}_fixed.csv"
        df_fixed.to_csv(output_file, index=False)
        safe_print(f"\nFixed CSV saved to: {output_file}")
        
        # Show migration summary
        safe_print("\n" + "="*50)
        safe_print("MIGRATION COMPLETE!")
        safe_print("="*50)
        safe_print(f"Total rows processed: {len(df_fixed)}")
        safe_print(f"Output file: {output_file}")
        
        if args.rename_files and not args.dry_run:
            safe_print("\nFiles have been renamed. Make sure to:")
            safe_print("1. Test the reel tracker with the new CSV")
            safe_print("2. Verify files are correctly linked")
            safe_print("3. Update any external references")
    else:
        safe_print("\n[DRY RUN] No changes were made. Remove --dry-run to apply changes.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())