#!/usr/bin/env python3
"""
Script to rename concentration files from underscore format to dot format
- 0_5mM -> 0.5mM
- 1_0mM -> 1.0mM  
- 5_0mM -> 5.0mM
- 10_0mM -> 10.0mM (if any)
Also rename directories
"""

import os
import re
import shutil
from pathlib import Path

def rename_concentration_files(base_path):
    """Rename files and directories with concentration patterns"""
    base_path = Path(base_path)
    
    # Patterns to replace
    patterns = [
        (r'(\d+)_(\d+)mM', r'\1.\2mM'),  # X_YmM -> X.YmM
    ]
    
    renamed_count = 0
    
    # First pass: rename files (bottom-up to avoid path issues)
    for root, dirs, files in os.walk(base_path, topdown=False):
        root_path = Path(root)
        
        # Rename files first
        for file in files:
            if file.endswith('.csv'):
                old_file_path = root_path / file
                new_filename = file
                
                # Apply all patterns
                for pattern, replacement in patterns:
                    new_filename = re.sub(pattern, replacement, new_filename)
                
                if new_filename != file:
                    new_file_path = root_path / new_filename
                    try:
                        shutil.move(str(old_file_path), str(new_file_path))
                        print(f"Renamed file: {file} -> {new_filename}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"Error renaming file {file}: {e}")
        
        # Then rename directories
        for dir_name in dirs:
            old_dir_path = root_path / dir_name
            new_dir_name = dir_name
            
            # Apply all patterns to directory names
            for pattern, replacement in patterns:
                new_dir_name = re.sub(pattern, replacement, new_dir_name)
            
            if new_dir_name != dir_name:
                new_dir_path = root_path / new_dir_name
                try:
                    shutil.move(str(old_dir_path), str(new_dir_path))
                    print(f"Renamed directory: {dir_name} -> {new_dir_name}")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming directory {dir_name}: {e}")
    
    return renamed_count

def preview_renames(base_path):
    """Preview what would be renamed without actually renaming"""
    base_path = Path(base_path)
    
    patterns = [
        (r'(\d+)_(\d+)mM', r'\1.\2mM'),
    ]
    
    preview_count = 0
    
    print("=== PREVIEW MODE ===")
    print("Files that would be renamed:")
    
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        
        # Preview file renames
        for file in files:
            if file.endswith('.csv'):
                new_filename = file
                for pattern, replacement in patterns:
                    new_filename = re.sub(pattern, replacement, new_filename)
                
                if new_filename != file:
                    print(f"FILE: {root_path / file} -> {root_path / new_filename}")
                    preview_count += 1
        
        # Preview directory renames
        for dir_name in dirs:
            new_dir_name = dir_name
            for pattern, replacement in patterns:
                new_dir_name = re.sub(pattern, replacement, new_dir_name)
            
            if new_dir_name != dir_name:
                print(f"DIR:  {root_path / dir_name} -> {root_path / new_dir_name}")
                preview_count += 1
    
    print(f"\nTotal items that would be renamed: {preview_count}")
    return preview_count

if __name__ == "__main__":
    base_paths = [
        "data_logs/csv",
        "Test_data", 
        "temp_data"
    ]
    
    # Preview first
    total_preview = 0
    for path in base_paths:
        if Path(path).exists():
            print(f"\n--- Previewing {path} ---")
            count = preview_renames(path)
            total_preview += count
    
    print(f"\n=== SUMMARY ===")
    print(f"Total items to rename: {total_preview}")
    
    if total_preview > 0:
        response = input("\nProceed with renaming? (y/N): ")
        if response.lower() == 'y':
            total_renamed = 0
            for path in base_paths:
                if Path(path).exists():
                    print(f"\n--- Renaming in {path} ---")
                    count = rename_concentration_files(path)
                    total_renamed += count
            
            print(f"\n=== COMPLETED ===")
            print(f"Total items renamed: {total_renamed}")
        else:
            print("Rename cancelled.")
    else:
        print("No files need renaming.")
