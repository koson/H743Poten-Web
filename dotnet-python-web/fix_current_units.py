#!/usr/bin/env python3
"""
CV Data Current Unit Conversion Script
=====================================

This script fixes the current unit mismatch in Pipot CV data files.

Problem:
- Header says "uA" (microAmpere) but values are actually in Ampere
- Values are 1,000,000 times smaller than they should be
- Causes confusion and incorrect analysis

Solution:
- Multiply current values by 1e6 to convert from A to uA
- Keep header as "uA" for consistency
- Backup original files before modification

Usage:
    python fix_current_units.py [path_to_cv_folder]
"""

import os
import sys
import csv
import shutil
from pathlib import Path
import argparse
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def is_cv_file(file_path):
    """Check if file is a CV data file"""
    if not file_path.suffix.lower() == '.csv':
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to check format
            lines = []
            for i, line in enumerate(f):
                lines.append(line.strip())
                if i >= 5:  # Read first 6 lines
                    break
            
            # Look for header pattern
            for line in lines:
                if 'V,uA' in line or 'Voltage,uA' in line or 'V(V),I(uA)' in line:
                    return True
                    
        return False
    except Exception:
        return False

def fix_current_values(file_path, dry_run=False):
    """Fix current values in a CV file by multiplying by 1e6"""
    
    print(f"Processing: {file_path}")
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ERROR: Could not read file - {e}")
        return False
    
    if len(lines) < 2:
        print(f"  SKIP: File too short")
        return False
    
    # Find header line
    header_line_idx = -1
    for i, line in enumerate(lines):
        if 'V,uA' in line or 'Voltage,uA' in line or 'V(V),I(uA)' in line:
            header_line_idx = i
            break
    
    if header_line_idx == -1:
        print(f"  SKIP: No uA header found")
        return False
    
    # Process data lines
    modified_lines = []
    data_rows_processed = 0
    conversion_factor = 1e6
    
    for i, line in enumerate(lines):
        if i <= header_line_idx:
            # Keep metadata and header as-is
            modified_lines.append(line)
        else:
            # Process data lines
            line = line.strip()
            if not line:
                modified_lines.append(line + '\n')
                continue
                
            try:
                # Split by comma
                parts = line.split(',')
                if len(parts) >= 2:
                    voltage_str = parts[0].strip()
                    current_str = parts[1].strip()
                    
                    # Parse current value
                    current_value = float(current_str)
                    
                    # Convert from A to uA (multiply by 1e6)
                    current_ua = current_value * conversion_factor
                    
                    # Reconstruct line with converted current
                    if len(parts) == 2:
                        new_line = f"{voltage_str},{current_ua:.6e}\n"
                    else:
                        # Handle additional columns
                        other_parts = ','.join(parts[2:])
                        new_line = f"{voltage_str},{current_ua:.6e},{other_parts}\n"
                    
                    modified_lines.append(new_line)
                    data_rows_processed += 1
                else:
                    # Keep line as-is if format is unexpected
                    modified_lines.append(line + '\n')
                    
            except ValueError as e:
                # Keep line as-is if parsing fails
                modified_lines.append(line + '\n')
                print(f"  WARNING: Could not parse line {i+1}: {line[:50]}...")
    
    if data_rows_processed == 0:
        print(f"  SKIP: No data rows processed")
        return False
    
    print(f"  INFO: Processed {data_rows_processed} data rows")
    
    if dry_run:
        print(f"  DRY RUN: Would multiply current values by {conversion_factor:.0e}")
        return True
    
    # Backup original file
    try:
        backup_path = backup_file(file_path)
        print(f"  BACKUP: Created {os.path.basename(backup_path)}")
    except Exception as e:
        print(f"  ERROR: Could not create backup - {e}")
        return False
    
    # Write modified file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        print(f"  SUCCESS: Fixed current units (×{conversion_factor:.0e})")
        return True
    except Exception as e:
        print(f"  ERROR: Could not write file - {e}")
        return False

def process_folder(folder_path, dry_run=False, recursive=True):
    """Process all CV files in a folder"""
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"ERROR: Folder not found: {folder_path}")
        return
    
    print(f"Scanning folder: {folder_path}")
    print(f"Recursive: {recursive}")
    print(f"Dry run: {dry_run}")
    print("-" * 60)
    
    # Find all CSV files
    if recursive:
        csv_files = list(folder.rglob('*.csv'))
    else:
        csv_files = list(folder.glob('*.csv'))
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Filter CV files
    cv_files = []
    for csv_file in csv_files:
        if is_cv_file(csv_file):
            cv_files.append(csv_file)
    
    print(f"Identified {len(cv_files)} CV data files")
    print("-" * 60)
    
    if len(cv_files) == 0:
        print("No CV files found to process")
        return
    
    # Process files
    successful = 0
    failed = 0
    
    for cv_file in cv_files:
        try:
            if fix_current_values(cv_file, dry_run):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR: Unexpected error - {e}")
            failed += 1
        print()  # Empty line for readability
    
    # Summary
    print("=" * 60)
    print("SUMMARY:")
    print(f"  Total CV files found: {len(cv_files)}")
    print(f"  Successfully processed: {successful}")
    print(f"  Failed/Skipped: {failed}")
    
    if not dry_run and successful > 0:
        print("\nIMPORTANT:")
        print("- Original files have been backed up with timestamp")
        print("- Current values have been multiplied by 1e6 (A → uA)")
        print("- Headers remain as 'uA' for consistency")
        print("- Please verify the results before deleting backups")

def main():
    parser = argparse.ArgumentParser(description='Fix current unit mismatch in CV data files')
    parser.add_argument('folder', nargs='?', 
                       default='/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Research/Test_Data_CV/pipot',
                       help='Path to folder containing CV files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without modifying files')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not process subfolders recursively')
    
    args = parser.parse_args()
    
    print("CV Data Current Unit Conversion Script")
    print("====================================")
    print(f"Target folder: {args.folder}")
    
    if args.dry_run:
        print("*** DRY RUN MODE - NO FILES WILL BE MODIFIED ***")
    
    print()
    
    process_folder(args.folder, 
                  dry_run=args.dry_run, 
                  recursive=not args.no_recursive)

if __name__ == '__main__':
    main()