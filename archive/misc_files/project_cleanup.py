#!/usr/bin/env python3
"""
Project Cleanup Script
Organizes development files into archive folders for better project structure
while maintaining searchability by Copilot.
"""

import os
import shutil
import glob
from pathlib import Path
import json
from datetime import datetime

class ProjectCleanup:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.archive_root = self.project_root / "archive"
        self.moved_files = []
        
    def create_archive_structure(self):
        """Create organized archive structure"""
        archive_dirs = [
            "analysis_scripts",
            "test_scripts", 
            "baseline_experiments",
            "pls_experiments",
            "calibration_tests",
            "debug_scripts",
            "output_files",
            "legacy_batch_scripts",
            "images_and_plots",
            "old_results",
            "backup_scripts"
        ]
        
        for dir_name in archive_dirs:
            archive_dir = self.archive_root / dir_name
            archive_dir.mkdir(parents=True, exist_ok=True)
            
    def move_file(self, source, destination_dir, reason=""):
        """Move file to archive with logging"""
        try:
            if isinstance(source, str):
                source_path = Path(source)
            else:
                source_path = source
                
            if not source_path.is_absolute():
                source_path = self.project_root / source_path
                
            if not source_path.exists():
                print(f"⚠️ File not found: {source_path}")
                return False
                
            dest_dir = self.archive_root / destination_dir
            dest_path = dest_dir / source_path.name
            
            # Handle name conflicts
            counter = 1
            while dest_path.exists():
                stem = source_path.stem
                suffix = source_path.suffix
                dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
                
            shutil.move(str(source_path), str(dest_path))
            
            self.moved_files.append({
                "source": str(source_path.relative_to(self.project_root)),
                "destination": str(dest_path.relative_to(self.project_root)),
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"✅ Moved: {source_path.name} → {dest_path.relative_to(self.project_root)}")
            return True
            
        except Exception as e:
            print(f"❌ Error moving {source}: {e}")
            return False
    
    def cleanup_test_scripts(self):
        """Move test scripts to archive"""
        print("\n🧪 Moving test scripts...")
        
        test_patterns = [
            "test_*.py",
            "*_test.py", 
            "quick_test*.py",
            "simple_test*.py",
            "debug_*.py",
            "minimal_test.py",
            "combined_test.py",
            "comprehensive_test.py"
        ]
        
        for pattern in test_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and file_path.name not in ["tests/"]:
                    self.move_file(file_path, "test_scripts", "Test script")
    
    def cleanup_analysis_scripts(self):
        """Move analysis scripts to archive"""
        print("\n📊 Moving analysis scripts...")
        
        analysis_patterns = [
            "*_analysis.py",
            "*_analyzer.py", 
            "analyze_*.py",
            "*_comparison.py",
            "compare_*.py",
            "dataset_*.py",
            "survey_*.py",
            "precision_demo.py",
            "ml_demo.py",
            "ai_demo.py",
            "quick_ai_test.py",
            "simple_ai_test.py"
        ]
        
        for pattern in analysis_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    self.move_file(file_path, "analysis_scripts", "Analysis script")
    
    def cleanup_baseline_experiments(self):
        """Move baseline detection experiments"""
        print("\n📈 Moving baseline experiments...")
        
        baseline_patterns = [
            "baseline_*.py",
            "*baseline*.py",
            "enhanced_detector*.py",
            "improved_baseline*.py",
            "extended_baseline*.py",
            "optimized_baseline*.py",
            "interactive_baseline*.py",
            "precision_peak_baseline*.py"
        ]
        
        for pattern in baseline_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                # Keep essential baseline files in main directory
                if file_name not in ["baseline_detector_v4.py"]:
                    self.move_file(file_name, "baseline_experiments", "Baseline experiment")
    
    def cleanup_pls_experiments(self):
        """Move PLS experiments"""
        print("\n🧬 Moving PLS experiments...")
        
        pls_patterns = [
            "pls_*.py",
            "*_pls_*.py",
            "advanced_pls*.py",
            "palmsens_pls*.py",
            "comprehensive_pls*.py",
            "precision_pls*.py"
        ]
        
        exclude_files = [
            "comprehensive_pls_analysis.py",  # Keep main analysis
            "improved_pls_visualizer.py"     # Keep main visualizer
        ]
        
        for pattern in pls_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                if file_name not in exclude_files:
                    self.move_file(file_name, "pls_experiments", "PLS experiment")
    
    def cleanup_calibration_tests(self):
        """Move calibration test scripts"""
        print("\n⚖️ Moving calibration tests...")
        
        calibration_patterns = [
            "*calibration*.py",
            "cv_*.py",
            "scan_rate*.py",
            "simple_cross*.py",
            "stm32_vs_palmsens*.py",
            "enhanced_cv*.py",
            "advanced_calibration*.py"
        ]
        
        for pattern in calibration_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                self.move_file(file_name, "calibration_tests", "Calibration test")
    
    def cleanup_debug_scripts(self):
        """Move debug scripts"""
        print("\n🐛 Moving debug scripts...")
        
        debug_patterns = [
            "debug_*.py",
            "fix_*.py",
            "manual_fix.py",
            "auto_fix*.py",
            "simple_fix.py",
            "check_*.py",
            "verify_*.py",
            "validate_*.py",
            "explore_*.py",
            "convert_*.py",
            "import_*.py"
        ]
        
        for pattern in debug_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                self.move_file(file_name, "debug_scripts", "Debug script")
    
    def cleanup_batch_scripts(self):
        """Move batch/shell scripts"""
        print("\n📦 Moving batch scripts...")
        
        batch_patterns = [
            "*.bat",
            "*.sh",
            "run_*.py",
            "launch_*.py",
            "setup_*.py",
            "cleanup_*.py",
            "*_terminal*.py"
        ]
        
        exclude_files = [
            "auto_dev.py",        # Keep main dev script
            "main.py",           # Keep main entry point
            "main_dev.py"        # Keep dev entry point
        ]
        
        for pattern in batch_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                if file_name not in exclude_files:
                    self.move_file(file_name, "legacy_batch_scripts", "Batch/shell script")
    
    def cleanup_output_files(self):
        """Move output files and plots"""
        print("\n🖼️ Moving output files...")
        
        # Move PNG files (plots)
        for file in glob.glob(str(self.project_root / "*.png")):
            file_name = Path(file).name
            self.move_file(file_name, "images_and_plots", "Generated plot")
        
        # Move JSON result files
        json_patterns = [
            "*_report_*.json",
            "*_results_*.json", 
            "*_comparison_*.json",
            "*_analysis_*.json"
        ]
        
        for pattern in json_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                self.move_file(file_name, "old_results", "JSON result file")
        
        # Move CSV result files (but keep templates)
        csv_patterns = [
            "*_20250*.csv",  # Date-stamped files
            "test_*.csv",
            "*_data_*.csv",
            "*_reference_*.csv",
            "*_target_*.csv"
        ]
        
        for pattern in csv_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                self.move_file(file_name, "old_results", "CSV result file")
    
    def cleanup_old_extractors(self):
        """Move extraction scripts"""
        print("\n📤 Moving extraction scripts...")
        
        extractor_patterns = [
            "extract_*.py",
            "labplot2_*.py",
            "*_export*.py"
        ]
        
        # Keep the latest extractor scripts
        exclude_files = [
            "extract_score_plot_data.py"  # Keep latest score plot extractor
        ]
        
        for pattern in extractor_patterns:
            for file in glob.glob(str(self.project_root / pattern)):
                file_name = Path(file).name
                if file_name not in exclude_files:
                    self.move_file(file_name, "backup_scripts", "Extraction script")
    
    def cleanup_misc_files(self):
        """Move miscellaneous files"""
        print("\n🗂️ Moving miscellaneous files...")
        
        misc_files = [
            "algorithm_improvements.py",
            "parameter_log.db",
            "data_mapping.json",
            "cv_data_mapping.json",
            "batch_results.log",
            "debug_api.log",
            "conc",  # Seems like a test file
            "No"     # Seems like a test file
        ]
        
        for file_name in misc_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                if file_name.endswith(('.py', '.log')):
                    self.move_file(file_name, "backup_scripts", "Miscellaneous script")
                else:
                    self.move_file(file_name, "old_results", "Miscellaneous file")
    
    def create_archive_index(self):
        """Create an index of all archived files"""
        print("\n📑 Creating archive index...")
        
        index_data = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "total_files_moved": len(self.moved_files),
            "archive_structure": {},
            "moved_files": self.moved_files,
            "search_instructions": {
                "copilot_search": "Use semantic_search or grep_search in the archive/ folder",
                "file_patterns": "Files organized by type in archive/ subdirectories",
                "original_locations": "Check moved_files list for original paths"
            }
        }
        
        # Count files in each archive directory
        for archive_dir in self.archive_root.iterdir():
            if archive_dir.is_dir():
                files = list(archive_dir.glob("*"))
                index_data["archive_structure"][archive_dir.name] = {
                    "file_count": len(files),
                    "files": [f.name for f in files if f.is_file()]
                }
        
        # Save index
        index_file = self.archive_root / "ARCHIVE_INDEX.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Archive index created: {index_file}")
        
        # Create README for archive
        readme_content = f"""# Project Archive

This directory contains archived development files organized for better project structure.

## Directory Structure

"""
        
        for dir_name, info in index_data["archive_structure"].items():
            readme_content += f"### {dir_name}/ ({info['file_count']} files)\n"
            if dir_name == "analysis_scripts":
                readme_content += "Data analysis and comparison scripts\n\n"
            elif dir_name == "test_scripts":
                readme_content += "Test and debugging scripts\n\n"
            elif dir_name == "baseline_experiments":
                readme_content += "Baseline detection algorithm experiments\n\n"
            elif dir_name == "pls_experiments":
                readme_content += "PLS analysis experiments and prototypes\n\n"
            elif dir_name == "calibration_tests":
                readme_content += "Calibration and cross-validation tests\n\n"
            elif dir_name == "debug_scripts":
                readme_content += "Debug, fix, and utility scripts\n\n"
            elif dir_name == "legacy_batch_scripts":
                readme_content += "Batch files and shell scripts\n\n"
            elif dir_name == "images_and_plots":
                readme_content += "Generated plots and visualization outputs\n\n"
            elif dir_name == "old_results":
                readme_content += "JSON/CSV result files and reports\n\n"
            elif dir_name == "backup_scripts":
                readme_content += "Backup and extraction scripts\n\n"
        
        readme_content += f"""
## Search Instructions

### For GitHub Copilot:
- Use `semantic_search` with query terms in the archive/ folder
- Use `grep_search` with specific patterns
- Check `ARCHIVE_INDEX.json` for complete file listings

### Total Files Archived: {len(self.moved_files)}
### Cleanup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

All files remain searchable and accessible, just better organized!
"""
        
        readme_file = self.archive_root / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ Archive README created: {readme_file}")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 Starting Project Cleanup...")
        print(f"Project root: {self.project_root}")
        print(f"Archive root: {self.archive_root}")
        
        # Create archive structure
        self.create_archive_structure()
        
        # Run cleanup functions
        self.cleanup_test_scripts()
        self.cleanup_analysis_scripts()
        self.cleanup_baseline_experiments()
        self.cleanup_pls_experiments()
        self.cleanup_calibration_tests()
        self.cleanup_debug_scripts()
        self.cleanup_batch_scripts()
        self.cleanup_output_files()
        self.cleanup_old_extractors()
        self.cleanup_misc_files()
        
        # Create documentation
        self.create_archive_index()
        
        print(f"\n🎉 Cleanup Complete!")
        print(f"📊 Total files moved: {len(self.moved_files)}")
        print(f"📁 Archive location: {self.archive_root}")
        print(f"🔍 Files remain searchable via Copilot in archive/ folder")
        
        return len(self.moved_files)

def main():
    project_root = "D:/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web"
    
    cleanup = ProjectCleanup(project_root)
    files_moved = cleanup.run_cleanup()
    
    print(f"\n✅ Project cleanup completed successfully!")
    print(f"📈 {files_moved} files organized into archive structure")
    print(f"🎯 Project root is now much cleaner and more maintainable")

if __name__ == "__main__":
    main()
