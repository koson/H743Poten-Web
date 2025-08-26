#!/usr/bin/env python3
"""
Dataset Analysis Scanner
========================
Analyze the consistency and patterns in the large dataset of STM32 CV files
"""

import pandas as pd
import numpy as np
import os
import re
from pathlib import Path
from collections import defaultdict, Counter
import json
import logging
from typing import Dict, List, Tuple, Set
import matplotlib.pyplot as plt

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DatasetAnalyzer:
    """Analyze the consistency and patterns in the CV dataset"""
    
    def __init__(self, data_dir: str = "test_data/raw_stm32"):
        self.data_dir = Path(data_dir)
        self.analysis_results = {}
        
    def scan_dataset_patterns(self) -> Dict:
        """Comprehensive scan of dataset patterns"""
        logger.info("🔍 Starting comprehensive dataset analysis...")
        
        csv_files = list(self.data_dir.glob("*.csv"))
        logger.info(f"📊 Found {len(csv_files)} CSV files to analyze")
        
        # Analysis containers
        concentration_patterns = Counter()
        scan_rate_patterns = Counter()
        electrode_patterns = Counter()
        scan_number_patterns = Counter()
        file_size_distribution = []
        header_patterns = defaultdict(int)
        unit_patterns = defaultdict(int)
        
        # Metadata patterns
        filename_structures = defaultdict(int)
        
        logger.info("📈 Analyzing file patterns...")
        
        for i, csv_file in enumerate(csv_files):
            if i % 100 == 0:
                logger.info(f"   Progress: {i}/{len(csv_files)} ({i/len(csv_files)*100:.1f}%)")
            
            try:
                # File size
                file_size = csv_file.stat().st_size
                file_size_distribution.append(file_size)
                
                # Filename analysis
                filename = csv_file.name
                
                # Extract concentration
                conc = self.extract_concentration_from_filename(filename)
                if conc:
                    concentration_patterns[conc] += 1
                
                # Extract scan rate
                scan_rate = self.extract_scan_rate_from_filename(filename)
                if scan_rate:
                    scan_rate_patterns[scan_rate] += 1
                
                # Extract electrode
                electrode = self.extract_electrode_from_filename(filename)
                if electrode:
                    electrode_patterns[electrode] += 1
                
                # Extract scan number
                scan_num = self.extract_scan_number_from_filename(filename)
                if scan_num:
                    scan_number_patterns[scan_num] += 1
                
                # Filename structure pattern
                structure = self.analyze_filename_structure(filename)
                filename_structures[structure] += 1
                
                # Quick header analysis (first few files only for speed)
                if i < 50:
                    headers, units = self.analyze_file_header(csv_file)
                    if headers:
                        header_key = tuple(sorted(headers))
                        header_patterns[header_key] += 1
                    if units:
                        for unit in units:
                            unit_patterns[unit] += 1
                            
            except Exception as e:
                logger.warning(f"⚠️ Error processing {filename}: {e}")
                continue
        
        # Compile results
        results = {
            'total_files': len(csv_files),
            'concentration_distribution': dict(concentration_patterns.most_common()),
            'scan_rate_distribution': dict(scan_rate_patterns.most_common()),
            'electrode_distribution': dict(electrode_patterns.most_common()),
            'scan_number_distribution': dict(scan_number_patterns.most_common()),
            'filename_structures': dict(Counter(filename_structures).most_common()),
            'header_patterns': {str(k): v for k, v in header_patterns.items()},
            'unit_patterns': dict(Counter(unit_patterns).most_common()),
            'file_size_stats': {
                'min': min(file_size_distribution) if file_size_distribution else 0,
                'max': max(file_size_distribution) if file_size_distribution else 0,
                'mean': np.mean(file_size_distribution) if file_size_distribution else 0,
                'median': np.median(file_size_distribution) if file_size_distribution else 0,
                'std': np.std(file_size_distribution) if file_size_distribution else 0
            }
        }
        
        self.analysis_results = results
        return results
    
    def extract_concentration_from_filename(self, filename: str) -> float:
        """Extract concentration from filename"""
        filename_lower = filename.lower()
        
        patterns = [
            r'(\d+\.?\d*)\s*mm',
            r'ferro[_\-](\d+)[_\-](\d+)mm',  # Handle 20mM, 50mM patterns
            r'ferro[_\-](\d+\.?\d*)[_\-]?mm'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    if len(match.groups()) == 2:  # Handle ferro_5_0mM pattern
                        return float(match.group(1)) + float(match.group(2)) / 10
                    else:
                        return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def extract_scan_rate_from_filename(self, filename: str) -> float:
        """Extract scan rate from filename"""
        filename_lower = filename.lower()
        
        patterns = [
            r'(\d+\.?\d*)\s*mvps',
            r'(\d+\.?\d*)\s*mv[\/\-_]?s'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def extract_electrode_from_filename(self, filename: str) -> str:
        """Extract electrode designation from filename"""
        match = re.search(r'_E(\d+)_', filename)
        if match:
            return f"E{match.group(1)}"
        return None
    
    def extract_scan_number_from_filename(self, filename: str) -> int:
        """Extract scan number from filename"""
        match = re.search(r'scan_(\d+)', filename)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def analyze_filename_structure(self, filename: str) -> str:
        """Analyze the structure pattern of filename"""
        # Replace specific values with placeholders
        pattern = filename
        pattern = re.sub(r'\\d+\\.?\\d*mm', 'XXmM', pattern, flags=re.IGNORECASE)
        pattern = re.sub(r'\\d+\\.?\\d*mvps', 'XXmVpS', pattern, flags=re.IGNORECASE)
        pattern = re.sub(r'_E\\d+_', '_EX_', pattern)
        pattern = re.sub(r'scan_\\d+', 'scan_XX', pattern)
        return pattern
    
    def analyze_file_header(self, filepath: Path) -> Tuple[List[str], List[str]]:
        """Analyze file header structure and units"""
        try:
            # Read just the header
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                header_line = f.readline().strip()
            
            headers = [col.strip() for col in header_line.split(',')]
            
            # Extract units from headers
            units = []
            for header in headers:
                unit_match = re.search(r'\\(([^)]+)\\)', header)
                if unit_match:
                    units.append(unit_match.group(1))
            
            return headers, units
            
        except Exception as e:
            return [], []
    
    def identify_data_completeness(self) -> Dict:
        """Identify data completeness and potential gaps"""
        logger.info("📋 Analyzing data completeness...")
        
        results = self.analysis_results
        if not results:
            logger.error("❌ No analysis results found. Run scan_dataset_patterns() first.")
            return {}
        
        # Expected experimental design analysis
        concentrations = set(results['concentration_distribution'].keys())
        scan_rates = set(results['scan_rate_distribution'].keys())
        electrodes = set(results['electrode_distribution'].keys())
        scan_numbers = set(results['scan_number_distribution'].keys())
        
        # Calculate expected vs actual file counts
        expected_combinations = len(concentrations) * len(scan_rates) * len(electrodes) * len(scan_numbers)
        actual_files = results['total_files']
        
        completeness = {
            'concentrations_found': sorted(concentrations),
            'scan_rates_found': sorted(scan_rates),
            'electrodes_found': sorted(electrodes),
            'scan_numbers_found': sorted(scan_numbers),
            'expected_combinations': expected_combinations,
            'actual_files': actual_files,
            'completeness_ratio': actual_files / expected_combinations if expected_combinations > 0 else 0,
            'potential_replicates': actual_files / (len(concentrations) * len(scan_rates)) if concentrations and scan_rates else 0
        }
        
        # Identify potential missing combinations
        missing_patterns = []
        for conc in concentrations:
            for sr in scan_rates:
                expected_files = len(electrodes) * len(scan_numbers)
                # This is a simplified check - would need more detailed analysis for exact missing files
                
        completeness['analysis_summary'] = {
            'total_concentration_levels': len(concentrations),
            'total_scan_rates': len(scan_rates),
            'total_electrodes': len(electrodes),
            'scans_per_condition': len(scan_numbers)
        }
        
        return completeness
    
    def check_unit_conversion_needs(self) -> Dict:
        """Check which files need unit conversion"""
        logger.info("🔧 Checking unit conversion requirements...")
        
        csv_files = list(self.data_dir.glob("*.csv"))
        conversion_stats = {
            'files_needing_conversion': 0,
            'files_already_correct': 0,
            'files_with_unknown_units': 0,
            'unit_distribution': defaultdict(int)
        }
        
        # Sample analysis on subset of files
        sample_size = min(100, len(csv_files))
        sample_files = csv_files[:sample_size]
        
        logger.info(f"🧪 Sampling {sample_size} files for unit analysis...")
        
        for csv_file in sample_files:
            try:
                headers, units = self.analyze_file_header(csv_file)
                
                needs_conversion = False
                has_units = False
                
                for header in headers:
                    if 'current' in header.lower() or header.lower().startswith('i') or 'ua' in header.lower():
                        has_units = True
                        if re.search(r'\(\s*A\s*\)', header, re.IGNORECASE):
                            needs_conversion = True
                            conversion_stats['unit_distribution']['A'] += 1
                        elif re.search(r'\(\s*[µμ]A\s*\)', header, re.IGNORECASE) or 'ua' in header.lower():
                            conversion_stats['unit_distribution']['µA'] += 1
                        elif re.search(r'\(\s*mA\s*\)', header, re.IGNORECASE):
                            conversion_stats['unit_distribution']['mA'] += 1
                        else:
                            conversion_stats['unit_distribution']['unknown'] += 1
                
                if needs_conversion:
                    conversion_stats['files_needing_conversion'] += 1
                elif has_units:
                    conversion_stats['files_already_correct'] += 1
                else:
                    conversion_stats['files_with_unknown_units'] += 1
                    
            except Exception as e:
                conversion_stats['files_with_unknown_units'] += 1
                continue
        
        # Extrapolate to full dataset
        total_files = len(csv_files)
        conversion_stats['estimated_total_needing_conversion'] = int(
            (conversion_stats['files_needing_conversion'] / sample_size) * total_files
        )
        
        return dict(conversion_stats)
    
    def generate_analysis_report(self, save_to_file: bool = True) -> str:
        """Generate comprehensive analysis report"""
        logger.info("📄 Generating analysis report...")
        
        # Run all analyses
        scan_results = self.scan_dataset_patterns()
        completeness = self.identify_data_completeness()
        conversion_needs = self.check_unit_conversion_needs()
        
        # Generate report
        report = f"""
# STM32 CV Dataset Analysis Report
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Dataset Overview
- **Total Files**: {scan_results['total_files']:,}
- **File Size Range**: {scan_results['file_size_stats']['min']/1024:.1f} KB - {scan_results['file_size_stats']['max']/1024:.1f} KB
- **Average File Size**: {scan_results['file_size_stats']['mean']/1024:.1f} KB

## 🧪 Experimental Conditions Found

### Concentrations (mM):
{self._format_distribution(scan_results['concentration_distribution'])}

### Scan Rates (mV/s):
{self._format_distribution(scan_results['scan_rate_distribution'])}

### Electrodes:
{self._format_distribution(scan_results['electrode_distribution'])}

### Scan Numbers:
{self._format_distribution(scan_results['scan_number_distribution'])}

## 📈 Data Completeness Analysis
- **Concentration Levels**: {completeness['analysis_summary']['total_concentration_levels']}
- **Scan Rates**: {completeness['analysis_summary']['total_scan_rates']}  
- **Electrodes**: {completeness['analysis_summary']['total_electrodes']}
- **Scans per Condition**: {completeness['analysis_summary']['scans_per_condition']}
- **Expected Combinations**: {completeness['expected_combinations']:,}
- **Actual Files**: {completeness['actual_files']:,}
- **Completeness Ratio**: {completeness['completeness_ratio']:.1%}

## 🔧 Unit Conversion Analysis
- **Files Needing Conversion**: ~{conversion_needs['estimated_total_needing_conversion']:,} ({conversion_needs['estimated_total_needing_conversion']/scan_results['total_files']*100:.1f}%)
- **Unit Distribution**: {dict(conversion_needs['unit_distribution'])}

## 🎯 Data Quality Assessment

### ✅ Strengths:
1. **Large Dataset**: {scan_results['total_files']:,} files provide excellent statistical power
2. **Systematic Naming**: Consistent filename patterns enable automatic processing
3. **Multiple Conditions**: {completeness['analysis_summary']['total_concentration_levels']} concentration levels × {completeness['analysis_summary']['total_scan_rates']} scan rates
4. **Replication**: Average {completeness['potential_replicates']:.1f} replicates per condition

### ⚠️ Potential Issues:
1. **Unit Inconsistency**: Some files may have A units instead of µA
2. **File Size Variation**: CV range {scan_results['file_size_stats']['std']/1024:.1f} KB suggests potential data quality differences

## 💡 Recommendations for Enhanced Analysis:

### 🚀 Immediate Actions:
1. **Run Unit Conversion**: Convert {conversion_needs['estimated_total_needing_conversion']:,} files from A to µA
2. **Quality Check**: Validate files with unusual sizes
3. **Batch Processing**: Use enhanced CV calibration system for all {scan_results['total_files']:,} files

### 📊 Statistical Power:
- **Concentration Range**: {min(completeness['concentrations_found'])} - {max(completeness['concentrations_found'])} mM
- **Scan Rate Range**: {min(completeness['scan_rates_found'])} - {max(completeness['scan_rates_found'])} mV/s
- **Expected R² Improvement**: High confidence calibration curves with {completeness['potential_replicates']:.0f}+ replicates per point

### 🎯 Confidence Enhancement:
1. **Cross-Validation**: Use multiple electrodes for robustness testing
2. **Outlier Detection**: Systematic identification of anomalous measurements
3. **Baseline Consistency**: Apply advanced baseline detection across all conditions
"""
        
        if save_to_file:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"dataset_analysis_report_{timestamp}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📁 Report saved to: {report_file}")
        
        return report
    
    def _format_distribution(self, distribution: Dict) -> str:
        """Format distribution for report"""
        if not distribution:
            return "  - None found"
        
        lines = []
        for key, count in distribution.items():
            lines.append(f"  - {key}: {count:,} files")
        return "\\n".join(lines[:10])  # Limit to top 10
    
    def create_overview_plots(self):
        """Create overview plots of the dataset"""
        logger.info("📊 Creating dataset overview plots...")
        
        results = self.analysis_results
        if not results:
            logger.error("❌ No analysis results found. Run scan_dataset_patterns() first.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Concentration distribution
        ax1 = axes[0, 0]
        conc_data = results['concentration_distribution']
        if conc_data:
            concentrations = list(conc_data.keys())
            counts = list(conc_data.values())
            ax1.bar(concentrations, counts)
            ax1.set_xlabel('Concentration (mM)')
            ax1.set_ylabel('Number of Files')
            ax1.set_title('Distribution of Concentration Levels')
            ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Scan rate distribution  
        ax2 = axes[0, 1]
        sr_data = results['scan_rate_distribution']
        if sr_data:
            scan_rates = list(sr_data.keys())
            counts = list(sr_data.values())
            ax2.bar(scan_rates, counts)
            ax2.set_xlabel('Scan Rate (mV/s)')
            ax2.set_ylabel('Number of Files')
            ax2.set_title('Distribution of Scan Rates')
        
        # Plot 3: Electrode distribution
        ax3 = axes[1, 0]
        elec_data = results['electrode_distribution']
        if elec_data:
            electrodes = list(elec_data.keys())
            counts = list(elec_data.values())
            ax3.bar(electrodes, counts)
            ax3.set_xlabel('Electrode')
            ax3.set_ylabel('Number of Files')
            ax3.set_title('Distribution by Electrode')
        
        # Plot 4: File size distribution
        ax4 = axes[1, 1]
        # Would need raw data for histogram - simplified version
        ax4.text(0.5, 0.5, f"File Size Stats:\\nMean: {results['file_size_stats']['mean']/1024:.1f} KB\\nStd: {results['file_size_stats']['std']/1024:.1f} KB", 
                ha='center', va='center', transform=ax4.transAxes, fontsize=12, 
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        ax4.set_title('File Size Statistics')
        ax4.axis('off')
        
        plt.tight_layout()
        
        # Save plot
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        plot_file = f"dataset_overview_{timestamp}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Overview plots saved to: {plot_file}")
        plt.show()

def main():
    """Main analysis function"""
    analyzer = DatasetAnalyzer()
    
    # Generate comprehensive report
    report = analyzer.generate_analysis_report()
    
    # Create overview plots
    analyzer.create_overview_plots()
    
    logger.info("✅ Dataset analysis complete!")
    print("\\n" + "="*60)
    print("📈 DATASET ANALYSIS SUMMARY")
    print("="*60)
    print(report.split("## 🎯 Data Quality Assessment")[0])

if __name__ == "__main__":
    main()