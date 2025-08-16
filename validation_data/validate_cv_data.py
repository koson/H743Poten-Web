#!/usr/bin/env python3
"""
Peak Detection Validation Framework
Data Validation and Preprocessing Script

Purpose: Validate and preprocess CV data from different instruments
Author: H743Poten Research Team
Date: 2025-08-16
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

class CVDataValidator:
    """Validate and preprocess CV data for peak detection analysis"""
    
    def __init__(self, base_path="validation_data"):
        self.base_path = Path(base_path)
        self.palmsens_path = self.base_path / "reference_cv_data" / "palmsens"
        self.stm32_path = self.base_path / "reference_cv_data" / "stm32h743"
        self.annotations_path = self.base_path / "expert_annotations"
        self.results_path = self.base_path / "analysis_results"
        
        # Create results directory if not exists
        self.results_path.mkdir(parents=True, exist_ok=True)
    
    def validate_cv_data(self, file_path, instrument_type="unknown"):
        """
        Validate CV data file format and content
        
        Args:
            file_path (str): Path to CV data file
            instrument_type (str): 'palmsens' or 'stm32h743'
        
        Returns:
            dict: Validation results
        """
        try:
            # Read CSV data
            df = pd.read_csv(file_path)
            
            validation_results = {
                "file_path": str(file_path),
                "instrument": instrument_type,
                "validation_time": datetime.now().isoformat(),
                "is_valid": True,
                "issues": [],
                "stats": {}
            }
            
            # Check required columns
            required_columns = ['potential', 'current']  # Flexible naming
            
            # Try to identify potential and current columns
            potential_col = None
            current_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in ['potential', 'voltage', 'volt', 'v']):
                    potential_col = col
                elif any(term in col_lower for term in ['current', 'i', 'amp']):
                    current_col = col
            
            if potential_col is None:
                validation_results["issues"].append("Could not identify potential column")
                validation_results["is_valid"] = False
            
            if current_col is None:
                validation_results["issues"].append("Could not identify current column")
                validation_results["is_valid"] = False
            
            if validation_results["is_valid"]:
                # Extract data
                potential = df[potential_col].values
                current = df[current_col].values
                
                # Basic statistics
                validation_results["stats"] = {
                    "data_points": len(potential),
                    "potential_range": {
                        "min": float(np.min(potential)),
                        "max": float(np.max(potential)),
                        "span": float(np.max(potential) - np.min(potential))
                    },
                    "current_range": {
                        "min": float(np.min(current)),
                        "max": float(np.max(current)),
                        "span": float(np.max(current) - np.min(current))
                    },
                    "column_names": {
                        "potential": potential_col,
                        "current": current_col
                    }
                }
                
                # Data quality checks
                if len(potential) < 50:
                    validation_results["issues"].append("Very few data points (< 50)")
                
                if np.any(np.isnan(potential)) or np.any(np.isnan(current)):
                    validation_results["issues"].append("Contains NaN values")
                
                if np.any(np.isinf(potential)) or np.any(np.isinf(current)):
                    validation_results["issues"].append("Contains infinite values")
                
                # Check for reasonable CV ranges
                if abs(validation_results["stats"]["potential_range"]["span"]) < 0.1:
                    validation_results["issues"].append("Very small potential range (< 0.1V)")
                
                if abs(validation_results["stats"]["current_range"]["span"]) < 1e-9:
                    validation_results["issues"].append("Very small current range (< 1nA)")
            
            return validation_results
            
        except Exception as e:
            return {
                "file_path": str(file_path),
                "instrument": instrument_type,
                "validation_time": datetime.now().isoformat(),
                "is_valid": False,
                "issues": [f"Failed to read file: {str(e)}"],
                "stats": {}
            }
    
    def compare_instruments(self, palmsens_file, stm32_file):
        """
        Compare CV data from PalmSens and STM32H743
        
        Args:
            palmsens_file (str): Path to PalmSens data
            stm32_file (str): Path to STM32 data
        
        Returns:
            dict: Comparison results
        """
        # Validate both files
        palmsens_validation = self.validate_cv_data(palmsens_file, "palmsens")
        stm32_validation = self.validate_cv_data(stm32_file, "stm32h743")
        
        if not (palmsens_validation["is_valid"] and stm32_validation["is_valid"]):
            return {
                "comparison_valid": False,
                "palmsens_validation": palmsens_validation,
                "stm32_validation": stm32_validation,
                "message": "One or both files failed validation"
            }
        
        # Load data for comparison
        df_palmsens = pd.read_csv(palmsens_file)
        df_stm32 = pd.read_csv(stm32_file)
        
        # Extract data based on validation results
        palmsens_pot_col = palmsens_validation["stats"]["column_names"]["potential"]
        palmsens_cur_col = palmsens_validation["stats"]["column_names"]["current"]
        stm32_pot_col = stm32_validation["stats"]["column_names"]["potential"]
        stm32_cur_col = stm32_validation["stats"]["column_names"]["current"]
        
        palmsens_pot = df_palmsens[palmsens_pot_col].values
        palmsens_cur = df_palmsens[palmsens_cur_col].values
        stm32_pot = df_stm32[stm32_pot_col].values
        stm32_cur = df_stm32[stm32_cur_col].values
        
        # Compare ranges
        comparison_results = {
            "comparison_valid": True,
            "palmsens_validation": palmsens_validation,
            "stm32_validation": stm32_validation,
            "range_comparison": {
                "potential_overlap": self._calculate_range_overlap(
                    palmsens_validation["stats"]["potential_range"],
                    stm32_validation["stats"]["potential_range"]
                ),
                "current_ratio": abs(
                    stm32_validation["stats"]["current_range"]["span"] /
                    palmsens_validation["stats"]["current_range"]["span"]
                )
            },
            "data_point_comparison": {
                "palmsens_points": len(palmsens_pot),
                "stm32_points": len(stm32_pot),
                "ratio": len(stm32_pot) / len(palmsens_pot)
            }
        }
        
        return comparison_results
    
    def _calculate_range_overlap(self, range1, range2):
        """Calculate overlap percentage between two ranges"""
        start = max(range1["min"], range2["min"])
        end = min(range1["max"], range2["max"])
        
        if start >= end:
            return 0.0  # No overlap
        
        overlap = end - start
        total_range = max(range1["max"], range2["max"]) - min(range1["min"], range2["min"])
        
        return overlap / total_range * 100
    
    def generate_validation_report(self, output_file="validation_report.json"):
        """Generate comprehensive validation report for all data"""
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "palmsens_files": [],
            "stm32_files": [],
            "comparisons": [],
            "summary": {}
        }
        
        # Validate PalmSens files
        if self.palmsens_path.exists():
            for file_path in self.palmsens_path.glob("*.csv"):
                validation = self.validate_cv_data(file_path, "palmsens")
                report["palmsens_files"].append(validation)
        
        # Validate STM32 files
        if self.stm32_path.exists():
            for file_path in self.stm32_path.glob("*.csv"):
                validation = self.validate_cv_data(file_path, "stm32h743")
                report["stm32_files"].append(validation)
        
        # Generate summary
        report["summary"] = {
            "total_palmsens_files": len(report["palmsens_files"]),
            "total_stm32_files": len(report["stm32_files"]),
            "valid_palmsens_files": sum(1 for f in report["palmsens_files"] if f["is_valid"]),
            "valid_stm32_files": sum(1 for f in report["stm32_files"] if f["is_valid"])
        }
        
        # Save report
        output_path = self.results_path / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report saved to: {output_path}")
        return report

def main():
    """Main function for testing the validator"""
    validator = CVDataValidator()
    
    print("🧪 CV Data Validation Framework")
    print("=" * 50)
    
    # Generate validation report
    report = validator.generate_validation_report()
    
    print(f"\n📊 Validation Summary:")
    print(f"PalmSens files: {report['summary']['valid_palmsens_files']}/{report['summary']['total_palmsens_files']} valid")
    print(f"STM32 files: {report['summary']['valid_stm32_files']}/{report['summary']['total_stm32_files']} valid")
    
    print(f"\n✅ Validation complete!")
    print(f"📄 Report saved to: validation_data/analysis_results/validation_report.json")

if __name__ == "__main__":
    main()
