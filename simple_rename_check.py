#!/usr/bin/env python3
"""
Simple rename script for concentration files
"""

import os
from pathlib import Path

def main():
    base_dir = Path("d:/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web")
    
    # Find all CSV files with underscore patterns
    patterns_to_find = ["*0_5mM*.csv", "*1_0mM*.csv", "*5_0mM*.csv"]
    
    files_to_rename = []
    for pattern in patterns_to_find:
        files_found = list(base_dir.rglob(pattern))
        files_to_rename.extend(files_found)
    
    print(f"Found {len(files_to_rename)} files to rename:")
    
    # Preview
    for i, file_path in enumerate(files_to_rename[:10]):  # Show first 10
        old_name = file_path.name
        new_name = old_name.replace("_5mM", ".5mM").replace("_0mM", ".0mM")
        print(f"{i+1}. {old_name} -> {new_name}")
    
    if len(files_to_rename) > 10:
        print(f"... and {len(files_to_rename) - 10} more files")
    
    return len(files_to_rename)

if __name__ == "__main__":
    count = main()
    print(f"\nTotal files that need renaming: {count}")
