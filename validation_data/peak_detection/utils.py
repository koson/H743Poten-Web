"""
Peak Detection Framework - Common Utilities
==========================================

This module provides common utilities for all peak detection methods.
Includes data loading, preprocessing, and evaluation helpers.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union
import json
import warnings

class CVDataLoader:
    """Utility class for loading CV data files with proper error handling."""
    
    @staticmethod
    def load_cv_file(filepath: Union[str, Path]) -> Optional[pd.DataFrame]:
        """
        Load a single CV file with robust error handling.
        
        Args:
            filepath: Path to CV file
            
        Returns:
            DataFrame with V and current columns, or None if failed
        """
        try:
            # Try different loading strategies
            for skiprows in [0, 1, 2]:
                try:
                    df = pd.read_csv(filepath, skiprows=skiprows)
                    
                    # Check for voltage column
                    voltage_cols = [col for col in df.columns if any(v in col.lower() for v in ['volt', 'v', 'potential'])]
                    if not voltage_cols:
                        continue
                        
                    # Check for current column  
                    current_cols = [col for col in df.columns if any(c in col.lower() for c in ['current', 'i', 'ua', 'ma', 'amp'])]
                    if not current_cols:
                        continue
                    
                    # Success - rename columns to standard format
                    df_clean = pd.DataFrame()
                    df_clean['V'] = df[voltage_cols[0]]
                    df_clean['I'] = df[current_cols[0]]
                    
                    # Remove any NaN values
                    df_clean = df_clean.dropna()
                    
                    if len(df_clean) < 10:  # Too few points
                        continue
                        
                    return df_clean
                    
                except Exception:
                    continue
                    
            return None
            
        except Exception as e:
            warnings.warn(f"Failed to load {filepath}: {e}")
            return None
    
    @staticmethod
    def load_file_list(file_list_path: Union[str, Path]) -> List[str]:
        """Load list of files from text file."""
        with open(file_list_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    @staticmethod
    def load_multiple_cv_files(file_paths: List[str], base_path: str = "") -> Dict[str, pd.DataFrame]:
        """
        Load multiple CV files and return as dictionary.
        
        Args:
            file_paths: List of file paths (relative or absolute)
            base_path: Base path to prepend if paths are relative
            
        Returns:
            Dictionary mapping file paths to DataFrames
        """
        results = {}
        failed_files = []
        
        for filepath in file_paths:
            full_path = Path(base_path) / filepath if base_path else Path(filepath)
            
            df = CVDataLoader.load_cv_file(full_path)
            if df is not None:
                results[str(filepath)] = df
            else:
                failed_files.append(str(filepath))
        
        if failed_files:
            print(f"⚠️  Failed to load {len(failed_files)} files:")
            for f in failed_files[:5]:  # Show first 5
                print(f"   - {f}")
            if len(failed_files) > 5:
                print(f"   ... and {len(failed_files) - 5} more")
        
        print(f"✅ Successfully loaded {len(results)} CV files")
        return results

class CVPreprocessor:
    """Preprocessing utilities for CV data."""
    
    @staticmethod
    def smooth_data(data: np.ndarray, window_size: int = 5, method: str = 'savgol') -> np.ndarray:
        """
        Smooth CV data using various methods.
        
        Args:
            data: Input data array
            window_size: Size of smoothing window
            method: 'savgol', 'moving_average', or 'gaussian'
            
        Returns:
            Smoothed data array
        """
        if method == 'savgol':
            from scipy.signal import savgol_filter
            # Ensure window_size is odd and not larger than data
            window_size = min(window_size, len(data))
            if window_size % 2 == 0:
                window_size -= 1
            if window_size < 3:
                return data
            return savgol_filter(data, window_size, 2)
            
        elif method == 'moving_average':
            return pd.Series(data).rolling(window=window_size, center=True).mean().fillna(method='bfill').fillna(method='ffill').values
            
        elif method == 'gaussian':
            from scipy.ndimage import gaussian_filter1d
            sigma = window_size / 4.0
            return gaussian_filter1d(data, sigma)
            
        else:
            raise ValueError(f"Unknown smoothing method: {method}")
    
    @staticmethod
    def normalize_voltage_range(df: pd.DataFrame, v_min: float = -1.0, v_max: float = 1.0) -> pd.DataFrame:
        """
        Normalize voltage range to standard window.
        
        Args:
            df: CV DataFrame with V and I columns
            v_min, v_max: Target voltage range
            
        Returns:
            DataFrame with normalized voltage range
        """
        df_norm = df.copy()
        
        # Find actual voltage range
        actual_min, actual_max = df['V'].min(), df['V'].max()
        
        # Only keep data within target range
        mask = (df['V'] >= v_min) & (df['V'] <= v_max)
        df_norm = df_norm[mask].reset_index(drop=True)
        
        return df_norm
    
    @staticmethod
    def interpolate_to_common_grid(df: pd.DataFrame, num_points: int = 1000) -> pd.DataFrame:
        """
        Interpolate CV data to common voltage grid.
        
        Args:
            df: CV DataFrame
            num_points: Number of points in interpolated grid
            
        Returns:
            DataFrame with interpolated data
        """
        v_min, v_max = df['V'].min(), df['V'].max()
        v_grid = np.linspace(v_min, v_max, num_points)
        
        # Interpolate current values
        i_interp = np.interp(v_grid, df['V'], df['I'])
        
        return pd.DataFrame({'V': v_grid, 'I': i_interp})

class PeakAnalyzer:
    """Utilities for analyzing detected peaks."""
    
    @staticmethod
    def calculate_peak_properties(voltage: np.ndarray, current: np.ndarray, 
                                 peak_indices: np.ndarray) -> Dict:
        """
        Calculate properties of detected peaks.
        
        Args:
            voltage: Voltage array
            current: Current array  
            peak_indices: Indices of detected peaks
            
        Returns:
            Dictionary with peak properties
        """
        properties = {
            'positions_v': voltage[peak_indices],
            'positions_idx': peak_indices,
            'heights': current[peak_indices],
            'count': len(peak_indices)
        }
        
        # Calculate peak widths (simple estimation)
        widths = []
        areas = []
        
        for idx in peak_indices:
            # Find width at half maximum
            peak_height = current[idx]
            half_height = peak_height / 2
            
            # Search left and right for half-height points
            left_idx = idx
            while left_idx > 0 and current[left_idx] > half_height:
                left_idx -= 1
                
            right_idx = idx  
            while right_idx < len(current) - 1 and current[right_idx] > half_height:
                right_idx += 1
            
            width = voltage[right_idx] - voltage[left_idx] if right_idx > left_idx else 0
            widths.append(width)
            
            # Estimate area (simple trapezoidal rule in width region)
            if right_idx > left_idx:
                area = np.trapz(current[left_idx:right_idx+1], voltage[left_idx:right_idx+1])
                areas.append(abs(area))
            else:
                areas.append(0)
        
        properties['widths'] = np.array(widths)
        properties['areas'] = np.array(areas)
        
        return properties

class DataSplitManager:
    """Manager for working with data splits."""
    
    def __init__(self, splits_dir: str = "validation_data/splits"):
        self.splits_dir = Path(splits_dir)
    
    def load_primary_splits(self) -> Tuple[List[str], List[str], List[str]]:
        """Load primary 70/15/15 data splits."""
        train_files = self.load_file_list(self.splits_dir / "train_files.txt")
        val_files = self.load_file_list(self.splits_dir / "validation_files.txt") 
        test_files = self.load_file_list(self.splits_dir / "test_files.txt")
        
        return train_files, val_files, test_files
    
    def load_cross_instrument_splits(self) -> Dict[str, Tuple[List[str], List[str]]]:
        """Load cross-instrument validation splits."""
        cross_dir = self.splits_dir / "cross_instrument"
        
        splits = {}
        
        # PalmSens → STM32
        palmsens_train = self.load_file_list(cross_dir / "palmsens_train_stm32_test_train.txt")
        stm32_test = self.load_file_list(cross_dir / "palmsens_train_stm32_test_test.txt")
        splits['palmsens_to_stm32'] = (palmsens_train, stm32_test)
        
        # STM32 → PalmSens  
        stm32_train = self.load_file_list(cross_dir / "stm32_train_palmsens_test_train.txt")
        palmsens_test = self.load_file_list(cross_dir / "stm32_train_palmsens_test_test.txt")
        splits['stm32_to_palmsens'] = (stm32_train, palmsens_test)
        
        return splits
    
    def load_loco_splits(self, condition_type: str) -> List[Tuple[List[str], List[str]]]:
        """
        Load LOCO (Leave-One-Condition-Out) splits.
        
        Args:
            condition_type: 'concentration', 'scan_rate', or 'electrode'
            
        Returns:
            List of (train_files, test_files) tuples
        """
        loco_dir = self.splits_dir / "loco_splits" / f"leave_{condition_type}_out"
        
        splits = []
        for train_file in loco_dir.glob("*_train.txt"):
            test_file = train_file.parent / train_file.name.replace("_train.txt", "_test.txt")
            
            if test_file.exists():
                train_files = self.load_file_list(train_file)
                test_files = self.load_file_list(test_file)
                splits.append((train_files, test_files))
        
        return splits
    
    @staticmethod
    def load_file_list(filepath: Path) -> List[str]:
        """Load file list from text file."""
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip()]

def plot_cv_with_peaks(voltage: np.ndarray, current: np.ndarray, 
                      peak_properties: Dict, title: str = "CV with Detected Peaks",
                      figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
    """
    Plot CV curve with detected peaks highlighted.
    
    Args:
        voltage: Voltage array
        current: Current array
        peak_properties: Peak properties from PeakAnalyzer
        title: Plot title
        figsize: Figure size
        
    Returns:
        Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot CV curve
    ax.plot(voltage, current, 'b-', linewidth=1.5, label='CV Curve')
    
    # Plot detected peaks
    if peak_properties['count'] > 0:
        ax.plot(peak_properties['positions_v'], peak_properties['heights'], 
                'ro', markersize=8, label=f'Detected Peaks (n={peak_properties["count"]})')
        
        # Add peak annotations
        for i, (v, i_val) in enumerate(zip(peak_properties['positions_v'], peak_properties['heights'])):
            ax.annotate(f'P{i+1}', (v, i_val), xytext=(5, 5), 
                       textcoords='offset points', fontsize=8)
    
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (µA)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig

# Export main classes and functions
__all__ = [
    'CVDataLoader', 'CVPreprocessor', 'PeakAnalyzer', 
    'DataSplitManager', 'plot_cv_with_peaks'
]
