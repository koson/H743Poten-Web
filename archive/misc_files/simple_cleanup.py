#!/usr/bin/env python3
"""
Simple Project Cleanup Script
Moves development files to organized archive folders
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

def move_files_by_pattern(source_dir, dest_dir, patterns, exclude=None):
    """Move files matching patterns to destination directory"""
    moved_count = 0
    exclude = exclude or []
    
    for pattern in patterns:
        for file_path in Path(source_dir).glob(pattern):
            if file_path.is_file() and file_path.name not in exclude:
                try:
                    # Create destination if it doesn't exist
                    dest_path = Path(dest_dir)
                    dest_path.mkdir(parents=True, exist_ok=True)
                    
                    # Handle name conflicts
                    dest_file = dest_path / file_path.name
                    counter = 1
                    while dest_file.exists():
                        stem = file_path.stem
                        suffix = file_path.suffix
                        dest_file = dest_path / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    # Move the file
                    shutil.move(str(file_path), str(dest_file))
                    print(f"✅ {file_path.name} → {dest_file.relative_to(source_dir)}")
                    moved_count += 1
                    
                except Exception as e:
                    print(f"❌ Error moving {file_path.name}: {e}")
    
    return moved_count

def main():
    project_root = Path("D:/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web")
    archive_root = project_root / "archive"
    
    print("🧹 Starting Simple Project Cleanup...")
    total_moved = 0
    
    # Create archive directories
    archive_dirs = {
        "test_scripts": archive_root / "test_scripts",
        "analysis_scripts": archive_root / "analysis_scripts", 
        "debug_scripts": archive_root / "debug_scripts",
        "batch_scripts": archive_root / "batch_scripts",
        "output_files": archive_root / "output_files",
        "backup_scripts": archive_root / "backup_scripts"
    }
    
    for dir_path in archive_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Move test scripts
    print("\n🧪 Moving test scripts...")
    test_patterns = ["test_*.py", "*_test.py", "quick_test*.py", "simple_test*.py"]
    moved = move_files_by_pattern(project_root, archive_dirs["test_scripts"], test_patterns)
    total_moved += moved
    print(f"Moved {moved} test scripts")
    
    # Move analysis scripts  
    print("\n📊 Moving analysis scripts...")
    analysis_patterns = ["*_analysis.py", "*_analyzer.py", "analyze_*.py", "*_comparison.py", "compare_*.py"]
    moved = move_files_by_pattern(project_root, archive_dirs["analysis_scripts"], analysis_patterns)
    total_moved += moved
    print(f"Moved {moved} analysis scripts")
    
    # Move debug scripts
    print("\n🐛 Moving debug scripts...")
    debug_patterns = ["debug_*.py", "fix_*.py", "check_*.py", "verify_*.py", "convert_*.py"]
    moved = move_files_by_pattern(project_root, archive_dirs["debug_scripts"], debug_patterns)
    total_moved += moved
    print(f"Moved {moved} debug scripts")
    
    # Move batch scripts
    print("\n📦 Moving batch/shell scripts...")
    batch_patterns = ["*.bat", "*.sh", "run_*.py", "launch_*.py", "setup_*.py"]
    exclude_batch = ["auto_dev.py", "main.py", "main_dev.py"]
    moved = move_files_by_pattern(project_root, archive_dirs["batch_scripts"], batch_patterns, exclude_batch)
    total_moved += moved
    print(f"Moved {moved} batch scripts")
    
    # Move output files
    print("\n🖼️ Moving output files...")
    output_patterns = ["*.png", "*_report_*.json", "*_results_*.json", "*_20250*.csv"]
    moved = move_files_by_pattern(project_root, archive_dirs["output_files"], output_patterns)
    total_moved += moved
    print(f"Moved {moved} output files")
    
    # Move backup scripts
    print("\n📤 Moving backup scripts...")
    backup_patterns = ["extract_*.py", "labplot2_*.py", "*_export*.py", "cleanup*.py"]
    exclude_backup = ["extract_score_plot_data.py"]  # Keep latest
    moved = move_files_by_pattern(project_root, archive_dirs["backup_scripts"], backup_patterns, exclude_backup)
    total_moved += moved
    print(f"Moved {moved} backup scripts")
    
    # Create archive documentation
    print("\n📑 Creating archive documentation...")
    
    index_data = {
        "cleanup_timestamp": datetime.now().isoformat(),
        "total_files_moved": total_moved,
        "archive_structure": {}
    }
    
    # Count files in each directory
    for name, dir_path in archive_dirs.items():
        if dir_path.exists():
            files = [f.name for f in dir_path.iterdir() if f.is_file()]
            index_data["archive_structure"][name] = {
                "file_count": len(files),
                "files": files
            }
    
    # Save index
    with open(archive_root / "ARCHIVE_INDEX.json", 'w') as f:
        json.dump(index_data, f, indent=2)
    
    # Create README
    readme_content = f"""# Project Archive

Files organized by type for better project structure.

## Summary
- **Total files moved**: {total_moved}
- **Cleanup date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Directories

### test_scripts/
Test and debugging scripts

### analysis_scripts/  
Data analysis and comparison scripts

### debug_scripts/
Debug, fix, and utility scripts

### batch_scripts/
Batch files and shell scripts

### output_files/
Generated plots, reports, and result files

### backup_scripts/
Backup and extraction scripts

## Search Instructions

All files remain searchable via GitHub Copilot:
- Use `semantic_search` in the archive/ folder
- Use `grep_search` with specific patterns
- Check `ARCHIVE_INDEX.json` for complete listings

Files are organized but still accessible!
"""
    
    with open(archive_root / "README.md", 'w') as f:
        f.write(readme_content)
    
    print(f"\n🎉 Cleanup Complete!")
    print(f"📊 Total files moved: {total_moved}")
    print(f"📁 Archive location: {archive_root}")
    print(f"🔍 All files remain searchable in archive/ folder")

if __name__ == "__main__":
    main()
