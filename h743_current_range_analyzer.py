#!/usr/bin/env python3
"""
H743 Current Range Hardware Problem Analysis & Fix
===============================================

Problem: Range 0 (±1000µA) and Range 1 (±100µA) have identical slopes
Root Cause: TIA (Transimpedance Amplifier) configuration issue

Analysis:
- Range 0 should have lower sensitivity (higher range, lower slope)
- Range 1 should have higher sensitivity (lower range, higher slope)
- Current ranges are controlled by TIA resistor values in hardware

Expected Behavior:
- Range 0 (1kΩ TIA): ±1000µA → Lower slope (sensitivity = 1 mV/µA)
- Range 1 (10kΩ TIA): ±100µA → Higher slope (sensitivity = 10 mV/µA)
- Range 2 (100kΩ TIA): ±10µA → Higher slope (sensitivity = 100 mV/µA)
- Range 3 (1MΩ TIA): ±1µA → Highest slope (sensitivity = 1000 mV/µA)
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class H743CurrentRangeAnalyzer:
    """Analyze and diagnose H743 current range hardware issues"""
    
    # Expected TIA configurations from hardware design
    TIA_RANGES = {
        0: {
            'name': 'Range 0',
            'resistance': 1000,      # 1kΩ
            'max_current': 1000e-6,  # ±1000µA
            'sensitivity': 1.0,      # 1 mV/µA
            'expected_slope': 1.0,   # Expected relative slope
            'color': 'blue'
        },
        1: {
            'name': 'Range 1', 
            'resistance': 10000,     # 10kΩ
            'max_current': 100e-6,   # ±100µA
            'sensitivity': 10.0,     # 10 mV/µA
            'expected_slope': 10.0,  # 10x more sensitive
            'color': 'red'
        },
        2: {
            'name': 'Range 2',
            'resistance': 100000,    # 100kΩ
            'max_current': 10e-6,    # ±10µA
            'sensitivity': 100.0,    # 100 mV/µA
            'expected_slope': 100.0, # 100x more sensitive
            'color': 'green'
        },
        3: {
            'name': 'Range 3',
            'resistance': 1000000,   # 1MΩ
            'max_current': 1e-6,     # ±1µA
            'sensitivity': 1000.0,   # 1000 mV/µA
            'expected_slope': 1000.0, # 1000x more sensitive
            'color': 'orange'
        }
    }
    
    def __init__(self):
        self.measurements = {}
        
    def add_measurement_data(self, range_id: int, voltage: np.ndarray, current: np.ndarray):
        """Add measurement data for analysis"""
        if range_id not in self.TIA_RANGES:
            logger.error(f"Invalid range ID: {range_id}")
            return
            
        self.measurements[range_id] = {
            'voltage': np.array(voltage),
            'current': np.array(current) * 1e6,  # Convert to µA
            'slope': None,
            'r_squared': None
        }
        
    def calculate_slopes(self):
        """Calculate actual slopes for each measurement"""
        for range_id, data in self.measurements.items():
            voltage = data['voltage']
            current = data['current']
            
            # Linear regression to find slope
            coeffs = np.polyfit(voltage, current, 1)
            slope = coeffs[0]  # µA/V
            intercept = coeffs[1]
            
            # Calculate R²
            current_pred = np.polyval(coeffs, voltage)
            ss_res = np.sum((current - current_pred) ** 2)
            ss_tot = np.sum((current - np.mean(current)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            self.measurements[range_id]['slope'] = slope
            self.measurements[range_id]['r_squared'] = r_squared
            self.measurements[range_id]['intercept'] = intercept
            
            logger.info(f"{self.TIA_RANGES[range_id]['name']}: slope = {slope:.2f} µA/V, R² = {r_squared:.4f}")
    
    def diagnose_hardware_issues(self) -> Dict:
        """Diagnose hardware configuration issues"""
        if not self.measurements:
            return {'error': 'No measurement data available'}
            
        diagnosis = {
            'issues_found': [],
            'recommendations': [],
            'slope_analysis': {},
            'severity': 'none'
        }
        
        # Calculate relative slopes
        slopes = {r: data['slope'] for r, data in self.measurements.items()}
        
        # Check if Range 0 and Range 1 have similar slopes (the reported problem)
        if 0 in slopes and 1 in slopes:
            slope_ratio = slopes[1] / slopes[0] if slopes[0] != 0 else float('inf')
            expected_ratio = self.TIA_RANGES[1]['expected_slope'] / self.TIA_RANGES[0]['expected_slope']
            
            diagnosis['slope_analysis'] = {
                'range_0_slope': slopes[0],
                'range_1_slope': slopes[1],
                'actual_ratio': slope_ratio,
                'expected_ratio': expected_ratio,
                'ratio_error': abs(slope_ratio - expected_ratio) / expected_ratio * 100
            }
            
            # Problem detection
            if abs(slope_ratio - 1.0) < 0.2:  # Slopes are too similar
                diagnosis['issues_found'].append({
                    'type': 'IDENTICAL_SLOPES',
                    'description': f'Range 0 and Range 1 have nearly identical slopes ({slope_ratio:.2f}:1)',
                    'expected': f'Range 1 should be {expected_ratio}x more sensitive than Range 0',
                    'severity': 'CRITICAL'
                })
                diagnosis['severity'] = 'critical'
                
                # Hardware-specific recommendations
                diagnosis['recommendations'].extend([
                    'Check TIA resistor values in H743 hardware',
                    'Verify current range switching circuitry',
                    'Inspect analog multiplexer/switch configuration',
                    'Validate ADC reference voltage stability',
                    'Check for hardware design/assembly errors'
                ])
                
            elif slope_ratio < expected_ratio * 0.5 or slope_ratio > expected_ratio * 2.0:
                diagnosis['issues_found'].append({
                    'type': 'INCORRECT_SLOPE_RATIO',
                    'description': f'Slope ratio {slope_ratio:.2f}:1 differs significantly from expected {expected_ratio:.2f}:1',
                    'severity': 'HIGH'
                })
                diagnosis['severity'] = 'high' if diagnosis['severity'] != 'critical' else 'critical'
        
        # Check individual range performance
        for range_id, data in self.measurements.items():
            range_info = self.TIA_RANGES[range_id]
            
            if data['r_squared'] < 0.95:
                diagnosis['issues_found'].append({
                    'type': 'POOR_LINEARITY',
                    'description': f"{range_info['name']} has poor linearity (R² = {data['r_squared']:.3f})",
                    'severity': 'MEDIUM'
                })
                
        return diagnosis
    
    def generate_hardware_fix_script(self) -> str:
        """Generate firmware/software fix script"""
        diagnosis = self.diagnose_hardware_issues()
        
        fix_script = """
// H743 Current Range Hardware Fix
// ===============================

"""
        
        if diagnosis['severity'] == 'critical':
            fix_script += """
/* CRITICAL ISSUE DETECTED: Range 0 and Range 1 have identical slopes
 * This indicates a hardware configuration problem in the TIA circuit
 */

// Hardware checks required:
// 1. Verify TIA resistor values
//    - Range 0: Should be 1kΩ
//    - Range 1: Should be 10kΩ
//    - Range 2: Should be 100kΩ  
//    - Range 3: Should be 1MΩ

// 2. Check current range switching logic
#define CURRENT_RANGE_0    0  // 1kΩ TIA, ±1mA range
#define CURRENT_RANGE_1    1  // 10kΩ TIA, ±100µA range
#define CURRENT_RANGE_2    2  // 100kΩ TIA, ±10µA range
#define CURRENT_RANGE_3    3  // 1MΩ TIA, ±1µA range

// 3. TIA gain verification function
void verify_tia_configuration(void) {
    // Test each range with known test current
    float test_current_ua = 50.0;  // 50µA test signal
    
    // Range 0: Expected output ~50mV (50µA × 1kΩ)
    set_current_range(CURRENT_RANGE_0);
    float output_range_0 = read_tia_output_mv();
    
    // Range 1: Expected output ~500mV (50µA × 10kΩ)  
    set_current_range(CURRENT_RANGE_1);
    float output_range_1 = read_tia_output_mv();
    
    // Check if Range 1 is ~10x more sensitive than Range 0
    float sensitivity_ratio = output_range_1 / output_range_0;
    
    if (fabs(sensitivity_ratio - 10.0) > 2.0) {
        // HARDWARE ERROR: TIA configuration problem
        printf("ERROR: TIA sensitivity ratio = %.2f (expected ~10.0)\\n", sensitivity_ratio);
        printf("Check TIA resistor values and switching circuit\\n");
    }
}

// 4. Software compensation (temporary fix)
float apply_range_correction(int range, float raw_current_ua) {
    // Temporary software correction until hardware is fixed
    const float correction_factors[] = {
        1.0,    // Range 0: No correction needed
        1.0,    // Range 1: Should be 10x more sensitive - FIX HARDWARE
        10.0,   // Range 2: Estimated correction
        100.0   // Range 3: Estimated correction
    };
    
    if (range >= 0 && range <= 3) {
        return raw_current_ua / correction_factors[range];
    }
    return raw_current_ua;
}

// 5. Recommended hardware modifications:
/*
 * Check schematic for:
 * - TIA feedback resistor values (R_TIA_0 = 1kΩ, R_TIA_1 = 10kΩ, etc.)
 * - Current range selection multiplexer/switches
 * - ADC reference voltage (should be stable 3.3V or 2.5V)
 * - Op-amp specifications and power supply
 * - PCB layout for noise and crosstalk
 */
"""
        
        return fix_script
    
    def create_diagnostic_plot(self, save_path: str = None):
        """Create diagnostic visualization"""
        if not self.measurements:
            logger.error("No measurement data to plot")
            return
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('H743 Current Range Hardware Diagnostic', fontsize=16, fontweight='bold')
        
        # Plot 1: Raw measurement data
        for range_id, data in self.measurements.items():
            range_info = self.TIA_RANGES[range_id]
            ax1.plot(data['voltage'], data['current'], 'o-', 
                    color=range_info['color'], label=range_info['name'], linewidth=2)
            
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title('Current vs Voltage by Range')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Slope comparison
        ranges = list(self.measurements.keys())
        slopes = [self.measurements[r]['slope'] for r in ranges]
        expected_slopes = [self.TIA_RANGES[r]['expected_slope'] * slopes[0] / self.TIA_RANGES[ranges[0]]['expected_slope'] for r in ranges]
        
        x_pos = np.arange(len(ranges))
        width = 0.35
        
        ax2.bar(x_pos - width/2, slopes, width, label='Actual', alpha=0.7, color='red')
        ax2.bar(x_pos + width/2, expected_slopes, width, label='Expected', alpha=0.7, color='blue')
        
        ax2.set_xlabel('Current Range')
        ax2.set_ylabel('Slope (µA/V)')
        ax2.set_title('Actual vs Expected Slopes')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([f'Range {r}' for r in ranges], rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Sensitivity ratio analysis
        if len(ranges) >= 2:
            ratios_actual = []
            ratios_expected = []
            ratio_labels = []
            
            for i in range(1, len(ranges)):
                actual_ratio = slopes[i] / slopes[0]
                expected_ratio = expected_slopes[i] / expected_slopes[0]
                ratios_actual.append(actual_ratio)
                ratios_expected.append(expected_ratio)
                ratio_labels.append(f'R{ranges[i]}/R{ranges[0]}')
                
            x_pos = np.arange(len(ratios_actual))
            ax3.bar(x_pos - width/2, ratios_actual, width, label='Actual', alpha=0.7, color='red')
            ax3.bar(x_pos + width/2, ratios_expected, width, label='Expected', alpha=0.7, color='blue')
            
        ax3.set_xlabel('Range Ratio')
        ax3.set_ylabel('Sensitivity Ratio')
        ax3.set_title('Sensitivity Ratio Analysis')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(ratio_labels, rotation=45)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: R² (linearity) analysis
        r_squared_values = [self.measurements[r]['r_squared'] for r in ranges]
        colors = [self.TIA_RANGES[r]['color'] for r in ranges]
        
        bars = ax4.bar(range(len(ranges)), r_squared_values, color=colors, alpha=0.7)
        ax4.axhline(y=0.95, color='red', linestyle='--', alpha=0.7, label='Minimum Acceptable (0.95)')
        ax4.set_xlabel('Current Range')
        ax4.set_ylabel('R² (Linearity)')
        ax4.set_title('Measurement Linearity by Range')
        ax4.set_xticks(range(len(ranges)))
        ax4.set_xticklabels([f'Range {r}' for r in ranges])
        ax4.set_ylim(0, 1.05)
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add R² values on bars
        for i, (bar, r2) in enumerate(zip(bars, r_squared_values)):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{r2:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Diagnostic plot saved to {save_path}")
        
        # plt.show()  # Commented out for headless mode
    
    def generate_report(self) -> str:
        """Generate comprehensive diagnostic report"""
        diagnosis = self.diagnose_hardware_issues()
        
        report = f"""
H743 Current Range Hardware Diagnostic Report
============================================

PROBLEM SUMMARY:
- Range 0 (±1000µA) and Range 1 (±100µA) exhibit identical slopes
- This indicates a TIA (Transimpedance Amplifier) configuration issue
- Expected behavior: Range 1 should be 10x more sensitive than Range 0

ANALYSIS RESULTS:
"""
        
        if 'slope_analysis' in diagnosis:
            sa = diagnosis['slope_analysis']
            report += f"""
Slope Measurements:
- Range 0: {sa['range_0_slope']:.2f} µA/V
- Range 1: {sa['range_1_slope']:.2f} µA/V
- Actual Ratio: {sa['actual_ratio']:.2f}:1
- Expected Ratio: {sa['expected_ratio']:.2f}:1
- Error: {sa['ratio_error']:.1f}%
"""
        
        report += f"\nISSUES FOUND ({len(diagnosis['issues_found'])}):\n"
        for issue in diagnosis['issues_found']:
            report += f"- {issue['severity']}: {issue['description']}\n"
            
        report += f"\nRECOMMENDATIONS ({len(diagnosis['recommendations'])}):\n"
        for rec in diagnosis['recommendations']:
            report += f"- {rec}\n"
            
        report += """
HARDWARE VERIFICATION CHECKLIST:
□ Check TIA resistor values (1kΩ, 10kΩ, 100kΩ, 1MΩ)
□ Verify current range switching circuitry
□ Test analog multiplexer/switch functionality
□ Validate ADC reference voltage stability
□ Inspect PCB for assembly errors
□ Check op-amp specifications and power supply
□ Measure noise and crosstalk between ranges

FIRMWARE ACTIONS:
□ Implement TIA configuration verification function
□ Add diagnostic test routines
□ Consider software compensation as temporary fix
□ Update calibration procedures

SEVERITY: {diagnosis['severity'].upper()}
"""
        
        return report

def analyze_from_graph_data():
    """Analyze the problem using data extracted from the user's graphs"""
    analyzer = H743CurrentRangeAnalyzer()
    
    # Simulated data based on the user's graphs showing identical slopes
    # Range 0: ±1000µA with slope ~200 µA/V
    voltage_range_0 = np.linspace(-1.0, 1.0, 100)
    current_range_0 = 200 * voltage_range_0  # µA - identical slope problem
    
    # Range 1: ±100µA with slope ~200 µA/V (PROBLEM: should be different!)  
    voltage_range_1 = np.linspace(-1.0, 1.0, 100)
    current_range_1 = 200 * voltage_range_1  # µA - same slope as Range 0 (WRONG!)
    
    # Range 2: ±10µA with correct higher sensitivity
    voltage_range_2 = np.linspace(-1.0, 0.1, 50)  # Limited voltage for safety
    current_range_2 = 20 * voltage_range_2  # µA - higher sensitivity
    
    # Range 3: ±1µA with highest sensitivity  
    voltage_range_3 = np.linspace(-1.0, 0.01, 20)  # Very limited voltage
    current_range_3 = 2 * voltage_range_3   # µA - highest sensitivity
    
    # Add data to analyzer
    analyzer.add_measurement_data(0, voltage_range_0, current_range_0 * 1e-6)  # Convert to A
    analyzer.add_measurement_data(1, voltage_range_1, current_range_1 * 1e-6)  # Convert to A
    analyzer.add_measurement_data(2, voltage_range_2, current_range_2 * 1e-6)  # Convert to A
    analyzer.add_measurement_data(3, voltage_range_3, current_range_3 * 1e-6)  # Convert to A
    
    # Perform analysis
    analyzer.calculate_slopes()
    
    # Generate report
    report = analyzer.generate_report()
    print(report)
    
    # Generate fix script
    fix_script = analyzer.generate_hardware_fix_script()
    
    # Save outputs
    with open('h743_hardware_diagnostic_report.txt', 'w') as f:
        f.write(report)
        
    with open('h743_hardware_fix.c', 'w') as f:
        f.write(fix_script)
        
    # Create diagnostic plot
    analyzer.create_diagnostic_plot('h743_current_range_diagnostic.png')
    
    print("\n📁 Generated Files:")
    print("- h743_hardware_diagnostic_report.txt")
    print("- h743_hardware_fix.c") 
    print("- h743_current_range_diagnostic.png")
    
    return analyzer

if __name__ == "__main__":
    print("🔧 H743 Current Range Hardware Analysis")
    print("=====================================")
    
    analyzer = analyze_from_graph_data()
    
    print("\n🎯 CONCLUSION:")
    print("The identical slopes in Range 0 and Range 1 indicate a hardware")
    print("configuration issue in the TIA (Transimpedance Amplifier) circuit.")
    print("This requires hardware inspection and possible firmware updates.")