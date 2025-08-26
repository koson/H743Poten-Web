#!/usr/bin/env python3
"""
Extended Baseline Detector with Enhanced Segment Extension
Improves upon v4 algorithm by extending baseline segments for better R²
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
import logging
from typing import List, Dict, Tuple, Optional
import os
import glob

# Import existing detectors
from baseline_detector_v4 import cv_baseline_detector_v4
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ExtendedBaselineDetector:
    """Enhanced baseline detector with segment extension capabilities"""
    
    def __init__(self):
        # Extended parameters for better segment coverage
        self.extended_params = {
            'window_span': 0.05,     # Smaller windows (50mV vs 100mV)
            'step_fraction': 0.2,     # Smaller steps (20% vs 30%)
            'max_total_length': 400,  # Allow longer segments (400 vs 200)
            'slope_tolerance': 3.0,   # More lenient slope grouping
            'merge_threshold': 0.02,  # Merge segments within 20mV
            'min_segment_length': 20, # Minimum points per segment
            'extend_factor': 2.0,     # More aggressive extension (2.0 vs 1.5)
            'r2_threshold_factor': 0.8, # Allow more R² degradation (80% of original)
            'slope_change_threshold': 0.8  # Allow larger slope changes (80% vs 50%)
        }
        
    def detect_extended_baseline(self, voltage: np.ndarray, current: np.ndarray) -> Dict:
        """
        Detect baseline using v4 algorithm then extend segments for better coverage
        """
        logger.info("🚀 Starting extended baseline detection...")
        
        # Step 1: Get initial detection from v4
        try:
            v4_result = cv_baseline_detector_v4(voltage, current)
            forward_baseline, reverse_baseline, metadata = v4_result
            logger.info("✅ v4 detection completed")
        except Exception as e:
            logger.error(f"❌ v4 detection failed: {e}")
            return {'error': str(e)}
        
        # Step 2: Extract segment information and indices from metadata
        forward_meta = metadata.get('forward_segment', {})
        reverse_meta = metadata.get('reverse_segment', {})
        
        # Get indices from metadata
        forward_start = forward_meta.get('start_idx', 0)
        forward_end = forward_meta.get('end_idx', 0)
        reverse_start = reverse_meta.get('start_idx', 0)
        reverse_end = reverse_meta.get('end_idx', 0)
        
        forward_indices = np.arange(forward_start, forward_end + 1) if forward_start < forward_end else np.array([])
        reverse_indices = np.arange(reverse_start, reverse_end + 1) if reverse_start < reverse_end else np.array([])
        
        # Get original R² values
        original_forward_r2 = forward_meta.get('r2', 0.0)
        original_reverse_r2 = reverse_meta.get('r2', 0.0)
        
        logger.info(f"📊 Original results:")
        logger.info(f"   Forward: {len(forward_indices)} points, R²={original_forward_r2:.4f}")
        logger.info(f"   Reverse: {len(reverse_indices)} points, R²={original_reverse_r2:.4f}")
        
        if len(forward_indices) == 0 and len(reverse_indices) == 0:
            logger.warning("⚠️ No baseline segments found by v4")
            return {
                'forward_indices': forward_indices,
                'reverse_indices': reverse_indices,
                'forward_r2': 0.0,
                'reverse_r2': 0.0,
                'overall_r2': 0.0,
                'original_forward_r2': original_forward_r2,
                'original_reverse_r2': original_reverse_r2,
                'extension_applied': False,
                'algorithm': 'extended_v4'
            }
        
        # Step 3: Apply extension algorithm
        extended_forward = self._extend_segment_indices(voltage, current, forward_indices)
        extended_reverse = self._extend_segment_indices(voltage, current, reverse_indices)
        
        # Step 4: Calculate new R² values
        forward_r2 = self._calculate_r2(voltage[extended_forward], current[extended_forward]) if len(extended_forward) > 1 else 0.0
        reverse_r2 = self._calculate_r2(voltage[extended_reverse], current[extended_reverse]) if len(extended_reverse) > 1 else 0.0
        
        # Step 5: Compare with original
        logger.info(f"📊 Forward R²: {original_forward_r2:.4f} → {forward_r2:.4f} (Δ={forward_r2-original_forward_r2:+.4f})")
        logger.info(f"📊 Reverse R²: {original_reverse_r2:.4f} → {reverse_r2:.4f} (Δ={reverse_r2-original_reverse_r2:+.4f})")
        logger.info(f"📊 Forward length: {len(forward_indices)} → {len(extended_forward)} (+{len(extended_forward)-len(forward_indices)})")
        logger.info(f"📊 Reverse length: {len(reverse_indices)} → {len(extended_reverse)} (+{len(extended_reverse)-len(reverse_indices)})")
        
        # Return extended results
        return {
            'forward_indices': extended_forward,
            'reverse_indices': extended_reverse,
            'forward_r2': forward_r2,
            'reverse_r2': reverse_r2,
            'overall_r2': max(forward_r2, reverse_r2),
            'original_forward_r2': original_forward_r2,
            'original_reverse_r2': original_reverse_r2,
            'original_forward_indices': forward_indices,
            'original_reverse_indices': reverse_indices,
            'extension_applied': True,
            'algorithm': 'extended_v4'
        }
    
    def _extend_segment_indices(self, voltage: np.ndarray, current: np.ndarray, 
                              original_indices: np.ndarray) -> np.ndarray:
        """
        Extend segment indices by finding adjacent points with similar slope
        """
        if len(original_indices) < 2:
            return original_indices
        
        # Calculate original segment properties
        orig_v = voltage[original_indices]
        orig_i = current[original_indices]
        orig_slope, _, orig_r2, _, _ = linregress(orig_v, orig_i)
        
        logger.debug(f"🔍 Extending segment: {len(original_indices)} points, slope={orig_slope:.2e}, R²={orig_r2:.4f}")
        
        # Find voltage range of original segment
        v_min, v_max = orig_v.min(), orig_v.max()
        
        # Define extension range (more aggressive than v4)
        extension_range = (v_max - v_min) * self.extended_params['extend_factor']
        search_v_min = max(voltage.min(), v_min - extension_range)
        search_v_max = min(voltage.max(), v_max + extension_range)
        
        # Find all points in extended range
        extended_mask = (voltage >= search_v_min) & (voltage <= search_v_max)
        candidate_indices = np.where(extended_mask)[0]
        
        if len(candidate_indices) <= len(original_indices):
            return original_indices
        
        # Test extended segment
        extended_v = voltage[candidate_indices]
        extended_i = current[candidate_indices]
        
        try:
            ext_slope, _, ext_r2, _, _ = linregress(extended_v, extended_i)
            
            # Accept extension if R² doesn't decrease significantly
            r2_threshold = max(0.6, orig_r2 * self.extended_params['r2_threshold_factor'])  # More lenient
            slope_change = abs(ext_slope - orig_slope) / max(abs(orig_slope), 1e-10)
            
            if ext_r2 >= r2_threshold and slope_change < self.extended_params['slope_change_threshold']:
                logger.debug(f"✅ Extension accepted: R²={ext_r2:.4f}, slope_change={slope_change:.2%}")
                return candidate_indices
            else:
                logger.debug(f"❌ Extension rejected: R²={ext_r2:.4f} < {r2_threshold:.4f} or slope_change={slope_change:.2%} > {self.extended_params['slope_change_threshold']*100:.0f}%")
                
        except Exception as e:
            logger.debug(f"❌ Extension failed: {e}")
        
        return original_indices
    
    def _calculate_r2(self, voltage: np.ndarray, current: np.ndarray) -> float:
        """Calculate R² for voltage-current relationship"""
        if len(voltage) < 2:
            return 0.0
        try:
            _, _, r_value, _, _ = linregress(voltage, current)
            return r_value ** 2
        except:
            return 0.0
    
    def visualize_comparison(self, voltage: np.ndarray, current: np.ndarray, 
                           extended_results: Dict, title: str = "Extended Baseline Comparison") -> plt.Figure:
        """
        Create visualization comparing original vs extended baseline detection
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Original baseline (v4)
        ax1.plot(voltage * 1000, current * 1e6, 'b-', alpha=0.7, linewidth=1, label='CV Data')
        
        orig_forward = extended_results.get('original_forward_indices', np.array([]))
        orig_reverse = extended_results.get('original_reverse_indices', np.array([]))
        orig_forward_r2 = extended_results.get('original_forward_r2', 0.0)
        orig_reverse_r2 = extended_results.get('original_reverse_r2', 0.0)
        
        if len(orig_forward) > 0:
            ax1.plot(voltage[orig_forward] * 1000, current[orig_forward] * 1e6, 
                    'ro', markersize=4, label=f'Original Forward (R²={orig_forward_r2:.3f})')
        if len(orig_reverse) > 0:
            ax1.plot(voltage[orig_reverse] * 1000, current[orig_reverse] * 1e6, 
                    'go', markersize=4, label=f'Original Reverse (R²={orig_reverse_r2:.3f})')
        
        ax1.set_xlabel('Voltage (mV)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title(f'{title} - Original v4 Detection')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Extended baseline
        ax2.plot(voltage * 1000, current * 1e6, 'b-', alpha=0.7, linewidth=1, label='CV Data')
        
        ext_forward = extended_results.get('forward_indices', np.array([]))
        ext_reverse = extended_results.get('reverse_indices', np.array([]))
        ext_forward_r2 = extended_results.get('forward_r2', 0.0)
        ext_reverse_r2 = extended_results.get('reverse_r2', 0.0)
        
        if len(ext_forward) > 0:
            ax2.plot(voltage[ext_forward] * 1000, current[ext_forward] * 1e6, 
                    'ro', markersize=4, label=f'Extended Forward (R²={ext_forward_r2:.3f})')
        if len(ext_reverse) > 0:
            ax2.plot(voltage[ext_reverse] * 1000, current[ext_reverse] * 1e6, 
                    'go', markersize=4, label=f'Extended Reverse (R²={ext_reverse_r2:.3f})')
        
        ax2.set_xlabel('Voltage (mV)')
        ax2.set_ylabel('Current (µA)')
        ax2.set_title(f'{title} - Extended Detection')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig


def test_extended_detector(csv_file: str):
    """Test extended baseline detector on a single CSV file"""
    logger.info(f"🧪 Testing extended detector on: {csv_file}")
    
    # Load data
    try:
        # Try loading with different options to handle various formats
        df = None
        try:
            df = pd.read_csv(csv_file)
            # Check if we got valid columns
            if len(df.columns) == 1 or df.columns[0].startswith('FileName:'):
                # This suggests we need to skip a header row
                df = pd.read_csv(csv_file, skiprows=1)
        except:
            # If that fails, try skipping first row (common with Stm32/Palmsens files)
            df = pd.read_csv(csv_file, skiprows=1)
        
        # Try different column combinations
        if 'WE(1).Potential (V)' in df.columns and 'WE(1).Current (A)' in df.columns:
            voltage = df['WE(1).Potential (V)'].values
            current = df['WE(1).Current (A)'].values
        elif 'Voltage (V)' in df.columns and 'Current (A)' in df.columns:
            voltage = df['Voltage (V)'].values
            current = df['Current (A)'].values
        elif 'V' in df.columns and 'uA' in df.columns:
            voltage = df['V'].values
            current = df['uA'].values * 1e-6  # Convert µA to A
            logger.info("🔄 Loaded Palmsens/Stm32 format (V, µA)")
        else:
            logger.error(f"❌ Unknown column format in {csv_file}")
            logger.error(f"Available columns: {list(df.columns)}")
            return
            
        # Convert to µA if needed
        if np.mean(np.abs(current)) < 1e-6:
            current = current * 1e6  # Convert A to µA
            logger.info("🔄 Converted current from A to µA")
            
    except Exception as e:
        logger.error(f"❌ Failed to load {csv_file}: {e}")
        return
    
    # Run extended detection
    detector = ExtendedBaselineDetector()
    results = detector.detect_extended_baseline(voltage, current)
    
    if 'error' in results:
        logger.error(f"❌ Detection failed: {results['error']}")
        return
    
    # Create visualization
    fig = detector.visualize_comparison(voltage, current, results, 
                                      title=f"Extended Baseline - {os.path.basename(csv_file)}")
    
    # Save plot
    output_name = f"extended_baseline_{os.path.basename(csv_file).replace('.csv', '')}.png"
    fig.savefig(output_name, dpi=300, bbox_inches='tight')
    logger.info(f"💾 Saved plot: {output_name}")
    
    plt.show()
    
    # Print summary
    print(f"\n📊 Results Summary for {os.path.basename(csv_file)}:")
    print(f"   Original Forward R²: {results.get('original_forward_r2', 0.0):.4f}")
    print(f"   Extended Forward R²: {results.get('forward_r2', 0.0):.4f}")
    print(f"   Original Reverse R²: {results.get('original_reverse_r2', 0.0):.4f}")
    print(f"   Extended Reverse R²: {results.get('reverse_r2', 0.0):.4f}")
    print(f"   Overall Improvement: {results.get('overall_r2', 0.0) - max(results.get('original_forward_r2', 0.0), results.get('original_reverse_r2', 0.0)):+.4f}")


def batch_test_extended_detector():
    """Test extended detector on all CSV files"""
    test_files = glob.glob("Test_data/**/*.csv", recursive=True)
    
    if not test_files:
        logger.warning("⚠️ No CSV files found in Test_data/")
        return
    
    logger.info(f"🎯 Found {len(test_files)} CSV files for testing")
    
    results_summary = []
    
    for i, csv_file in enumerate(test_files[:3], 1):  # Test first 3 files
        logger.info(f"\n{'='*60}")
        logger.info(f"📁 Testing file {i}/{min(3, len(test_files))}: {csv_file}")
        logger.info(f"{'='*60}")
        
        try:
            test_extended_detector(csv_file)
            results_summary.append(f"✅ {os.path.basename(csv_file)}")
        except Exception as e:
            logger.error(f"❌ Failed on {csv_file}: {e}")
            results_summary.append(f"❌ {os.path.basename(csv_file)}: {e}")
    
    # Print final summary
    print(f"\n{'='*60}")
    print("📊 BATCH TEST SUMMARY")
    print(f"{'='*60}")
    for result in results_summary:
        print(f"   {result}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Test with a single file first
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    if os.path.exists(test_file):
        test_extended_detector(test_file)
    else:
        logger.info("🔍 Running batch test instead...")
        batch_test_extended_detector()