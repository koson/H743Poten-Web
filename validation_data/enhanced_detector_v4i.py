"""
Enhanced Peak Detection V4 - Improved Version
Optimized for better reduction peak detection and edge effect elimination
"""

import numpy as np
import logging
from scipy.signal import find_peaks, savgol_filter
from scipy.stats import zscore

# Set up logging
logger = logging.getLogger(__name__)

class EnhancedDetectorV4Improved:
    def __init__(self, confidence_threshold=25.0):  # ลด threshold จาก 40% เป็น 25%
        """
        Initialize Enhanced Detector V4 - Improved Version
        
        Args:
            confidence_threshold: Minimum confidence percentage for peak acceptance (default: 25%)
        """
        self.confidence_threshold = confidence_threshold
        
        # ขยาย voltage ranges ให้กว้างขึ้น เพื่อ detect reduction peaks ได้ดีขึ้น
        self.ferrocyanide_ox_range = (0.1, 0.7)    # เดิม (0.2, 0.6)
        self.ferrocyanide_red_range = (-0.1, 0.4)  # เดิม (0.0, 0.3) ขยายลงไปติดลบ
        
        # Edge detection parameters
        self.edge_voltage_margin = 0.05  # 50mV margin from scan edges
        
        logger.info(f"🚀 Enhanced Detector V4 Improved initialized:")
        logger.info(f"   Confidence threshold: {self.confidence_threshold}%")
        logger.info(f"   Oxidation range: {self.ferrocyanide_ox_range}")
        logger.info(f"   Reduction range: {self.ferrocyanide_red_range}")
        logger.info(f"   Edge margin: {self.edge_voltage_margin}V")
    
    def detect_scan_direction_v4(self, voltage):
        """Detect CV scan direction and characteristics"""
        scan_info = {
            'direction': 'unknown',
            'start_voltage': voltage[0],
            'end_voltage': voltage[-1],
            'voltage_range': (voltage.min(), voltage.max()),
            'scan_rate_estimate': 'unknown',
            'total_points': len(voltage)
        }
        
        # Determine scan direction from first few points
        if len(voltage) > 10:
            initial_trend = voltage[10] - voltage[0]
            if initial_trend > 0:
                scan_info['direction'] = 'anodic_first'
            else:
                scan_info['direction'] = 'cathodic_first'
        
        return scan_info
    
    def calculate_dynamic_thresholds_v4(self, current, scan_analysis):
        """Calculate dynamic thresholds with improved sensitivity"""
        current_stats = {
            'mean': np.mean(current),
            'std': np.std(current),
            'range': np.ptp(current),
            'min': np.min(current),
            'max': np.max(current)
        }
        
        # ใช้ baseline ที่ conservative มากขึ้น
        baseline = np.median(current)  # ใช้ median แทน mean
        
        # ลด height threshold ให้ sensitive มากขึ้น
        height_threshold = current_stats['std'] * 1.5  # เดิม 2.0
        
        thresholds = {
            'baseline': baseline,
            'height': height_threshold,
            'min_peak_separation': max(3, len(current) // 50),  # ลด separation
            'width': max(2, len(current) // 100),  # ลด width requirement
            'prominence': height_threshold * 0.3,  # ลด prominence
            'current_stats': current_stats
        }
        
        logger.info(f"📊 Dynamic thresholds (improved):")
        logger.info(f"   Baseline: {baseline:.3f}µA")
        logger.info(f"   Height: {height_threshold:.3f}µA")
        logger.info(f"   Width: {thresholds['width']} points")
        logger.info(f"   Prominence: {thresholds['prominence']:.3f}µA")
        
        return thresholds
    
    def detect_edge_effects(self, voltage, current):
        """Detect and filter out edge effects at scan boundaries"""
        v_min, v_max = voltage.min(), voltage.max()
        v_range = v_max - v_min
        
        # Define edge regions (5% of total voltage range from each edge)
        edge_margin = max(self.edge_voltage_margin, v_range * 0.05)
        
        edge_mask = (
            (voltage <= v_min + edge_margin) |  # Lower edge
            (voltage >= v_max - edge_margin)    # Upper edge
        )
        
        edge_indices = np.where(edge_mask)[0]
        
        logger.info(f"🔍 Edge detection: margin={edge_margin:.3f}V, {len(edge_indices)} edge points")
        
        return edge_indices, edge_mask
    
    def improved_baseline_detection_v4(self, voltage, current, peak_positions=None):
        """Improved baseline detection with better stability"""
        window_size = max(5, len(current) // 20)  # ลด window size
        
        # Smooth current for variation calculation
        current_smooth = savgol_filter(current, window_length=min(window_size*2+1, len(current)//2*2+1), polyorder=2)
        variation = np.abs(current - current_smooth)
        
        # Use more sensitive percentile for stable regions
        variation_threshold = np.percentile(variation, 30)  # ลดจาก 40%
        stable_mask = variation <= variation_threshold
        
        # Remove edge effects
        edge_indices, edge_mask = self.detect_edge_effects(voltage, current)
        stable_mask = stable_mask & ~edge_mask
        
        # Remove points near existing peaks
        if peak_positions:
            voltage_tolerance = 0.03  # ลด tolerance
            for peak in peak_positions:
                peak_mask = np.abs(voltage - peak['voltage']) < voltage_tolerance
                stable_mask = stable_mask & ~peak_mask
        
        baseline_indices = np.where(stable_mask)[0]
        
        # Fallback if too few baseline points
        if len(baseline_indices) < 10:
            logger.info("Using fallback baseline detection")
            # Use central region only (avoid edges)
            central_mask = (voltage > voltage.min() + (voltage.max() - voltage.min()) * 0.2) & \
                          (voltage < voltage.max() - (voltage.max() - voltage.min()) * 0.2)
            central_indices = np.where(central_mask)[0]
            
            if len(central_indices) > 0:
                central_current = current[central_indices]
                median_current = np.median(central_current)
                stable_current_mask = np.abs(central_current - median_current) < np.std(central_current)
                baseline_indices = central_indices[stable_current_mask]
        
        baseline_info = []
        if len(baseline_indices) > 0:
            baseline_current = current[baseline_indices]
            baseline_info.append({
                'region': 'stable',
                'mean': np.mean(baseline_current),
                'std': np.std(baseline_current),
                'count': len(baseline_indices),
                'voltage_range': (voltage[baseline_indices].min(), voltage[baseline_indices].max())
            })
            
            logger.info(f"📈 Baseline found: {len(baseline_indices)} stable points, "
                       f"mean={np.mean(baseline_current):.3f}±{np.std(baseline_current):.3f}µA")
        
        return baseline_indices, baseline_info
    
    def improved_peak_detection_v4(self, current, thresholds):
        """Improved peak detection with better reduction peak sensitivity"""
        
        # Smooth current for peak detection
        smoothed_current = savgol_filter(current, window_length=min(11, len(current)//2*2+1), polyorder=2)
        
        # Oxidation peaks (positive peaks)
        ox_peaks, ox_properties = find_peaks(
            smoothed_current,
            height=thresholds['baseline'] + thresholds['height'] * 0.2,  # ลด threshold
            distance=thresholds['min_peak_separation'],
            width=max(1, thresholds['width'] // 2),  # ลด width requirement
            prominence=thresholds['prominence'] * 0.5  # ลด prominence
        )
        
        # Reduction peaks (negative peaks) - หา peaks ใน inverted signal
        red_peaks, red_properties = find_peaks(
            -smoothed_current,  # Invert signal for negative peaks
            height=-(thresholds['baseline'] - thresholds['height'] * 0.2),  # Adjusted for inverted signal
            distance=thresholds['min_peak_separation'],
            width=max(1, thresholds['width'] // 2),  # ลด width requirement
            prominence=thresholds['prominence'] * 0.5  # ลด prominence
        )
        
        logger.info(f"🔍 Peak detection results:")
        logger.info(f"   Oxidation peaks: {len(ox_peaks)}")
        logger.info(f"   Reduction peaks: {len(red_peaks)}")
        
        return ox_peaks, red_peaks
    
    def voltage_range_filtering_v4(self, peaks, voltage, peak_type):
        """Filter peaks by voltage range with improved ranges"""
        if peak_type == 'oxidation':
            v_min, v_max = self.ferrocyanide_ox_range
        else:  # reduction
            v_min, v_max = self.ferrocyanide_red_range
        
        filtered_peaks = []
        rejected_peaks = []
        
        for peak_idx in peaks:
            if 0 <= peak_idx < len(voltage):
                peak_voltage = voltage[peak_idx]
                
                if v_min <= peak_voltage <= v_max:
                    filtered_peaks.append(peak_idx)
                else:
                    rejected_peaks.append({
                        'index': peak_idx,
                        'voltage': peak_voltage,
                        'reason': f'voltage_range_{peak_type}',
                        'expected_range': (v_min, v_max)
                    })
        
        logger.info(f"📋 {peak_type.capitalize()} voltage filtering:")
        logger.info(f"   Range: {v_min:.3f} to {v_max:.3f}V")
        logger.info(f"   Accepted: {len(filtered_peaks)}/{len(peaks)} peaks")
        
        return np.array(filtered_peaks), rejected_peaks
    
    def calculate_peak_confidence_v4(self, peak_idx, voltage, current, baseline_info, peak_type):
        """Calculate peak confidence with improved scoring"""
        if not baseline_info:
            return 30.0  # Default confidence
        
        baseline_mean = baseline_info[0]['mean']
        baseline_std = baseline_info[0]['std']
        
        peak_voltage = voltage[peak_idx]
        peak_current = current[peak_idx]
        
        # Signal-to-noise ratio (improved calculation)
        if baseline_std > 0:
            snr = abs(peak_current - baseline_mean) / baseline_std
        else:
            snr = 5.0  # Default if std is 0
        
        # Voltage range score (improved ranges)
        if peak_type == 'oxidation':
            v_center = np.mean(self.ferrocyanide_ox_range)
            v_range = self.ferrocyanide_ox_range[1] - self.ferrocyanide_ox_range[0]
        else:
            v_center = np.mean(self.ferrocyanide_red_range)
            v_range = self.ferrocyanide_red_range[1] - self.ferrocyanide_red_range[0]
        
        voltage_distance = abs(peak_voltage - v_center)
        voltage_score = max(0, 1 - (voltage_distance / (v_range / 2))) * 100
        
        # Combined confidence (weighted)
        confidence = (
            snr * 15 +        # SNR contribution (increased weight)
            voltage_score * 0.5 +  # Voltage position contribution
            30             # Base confidence
        )
        
        confidence = min(100, max(0, confidence))
        
        return confidence
    
    def detect_peaks_enhanced_v4(self, voltage, current):
        """Main enhanced peak detection with improvements"""
        logger.info(f"🚀 Starting Enhanced V4 Improved detection...")
        
        # 1. Scan analysis
        scan_analysis = self.detect_scan_direction_v4(voltage)
        
        # 2. Calculate thresholds
        thresholds = self.calculate_dynamic_thresholds_v4(current, scan_analysis)
        
        # 3. Initial baseline detection
        baseline_indices, baseline_info = self.improved_baseline_detection_v4(voltage, current)
        
        # 4. Peak detection
        ox_peaks, red_peaks = self.improved_peak_detection_v4(current, thresholds)
        
        # 5. Voltage range filtering
        ox_peaks_filtered, ox_rejected = self.voltage_range_filtering_v4(ox_peaks, voltage, 'oxidation')
        red_peaks_filtered, red_rejected = self.voltage_range_filtering_v4(red_peaks, voltage, 'reduction')
        
        # 6. Edge effect filtering
        edge_indices, edge_mask = self.detect_edge_effects(voltage, current)
        
        # Filter out edge peaks
        ox_peaks_no_edge = [p for p in ox_peaks_filtered if p not in edge_indices]
        red_peaks_no_edge = [p for p in red_peaks_filtered if p not in edge_indices]
        
        edge_rejected_ox = [p for p in ox_peaks_filtered if p in edge_indices]
        edge_rejected_red = [p for p in red_peaks_filtered if p in edge_indices]
        
        logger.info(f"🚫 Edge filtering removed {len(edge_rejected_ox)} ox + {len(edge_rejected_red)} red peaks")
        
        # 7. Calculate confidence and filter
        final_peaks = []
        rejected_peaks = ox_rejected + red_rejected
        
        # Process oxidation peaks
        for peak_idx in ox_peaks_no_edge:
            confidence = self.calculate_peak_confidence_v4(peak_idx, voltage, current, baseline_info, 'oxidation')
            
            peak_data = {
                'voltage': voltage[peak_idx],
                'current': current[peak_idx],
                'type': 'oxidation',
                'index': int(peak_idx),
                'confidence': confidence
            }
            
            if confidence >= self.confidence_threshold:
                final_peaks.append(peak_data)
            else:
                rejected_peaks.append({
                    **peak_data,
                    'reason': 'low_confidence',
                    'threshold': self.confidence_threshold
                })
        
        # Process reduction peaks
        for peak_idx in red_peaks_no_edge:
            confidence = self.calculate_peak_confidence_v4(peak_idx, voltage, current, baseline_info, 'reduction')
            
            # Use the correct current value for reduction peaks
            # In STM32 data, the actual current at reduction peaks should be used directly
            peak_current = current[peak_idx]
            
            peak_data = {
                'voltage': voltage[peak_idx],
                'current': peak_current,
                'type': 'reduction',
                'index': int(peak_idx),
                'confidence': confidence
            }
            
            if confidence >= self.confidence_threshold:
                final_peaks.append(peak_data)
            else:
                rejected_peaks.append({
                    **peak_data,
                    'reason': 'low_confidence',
                    'threshold': self.confidence_threshold
                })
        
        # Add edge rejected peaks to rejected list
        for peak_idx in edge_rejected_ox:
            rejected_peaks.append({
                'voltage': voltage[peak_idx],
                'current': current[peak_idx],
                'type': 'oxidation',
                'index': int(peak_idx),
                'reason': 'edge_effect',
                'confidence': 0
            })
        
        for peak_idx in edge_rejected_red:
            rejected_peaks.append({
                'voltage': voltage[peak_idx],
                'current': current[peak_idx],
                'type': 'reduction',
                'index': int(peak_idx),
                'reason': 'edge_effect',
                'confidence': 0
            })
        
        # Sort peaks by voltage
        final_peaks.sort(key=lambda x: x['voltage'])
        
        results = {
            'peaks': final_peaks,
            'rejected_peaks': rejected_peaks,
            'scan_analysis': scan_analysis,
            'thresholds': thresholds,
            'baseline_info': baseline_info,
            'edge_indices': edge_indices.tolist(),
            'total_detected': len(ox_peaks) + len(red_peaks),
            'total_accepted': len(final_peaks)
        }
        
        # Summary
        ox_count = len([p for p in final_peaks if p['type'] == 'oxidation'])
        red_count = len([p for p in final_peaks if p['type'] == 'reduction'])
        
        logger.info(f"✅ Enhanced V4 Improved Results:")
        logger.info(f"   Oxidation peaks: {ox_count}")
        logger.info(f"   Reduction peaks: {red_count}")
        logger.info(f"   Total accepted: {len(final_peaks)}")
        logger.info(f"   Total rejected: {len(rejected_peaks)}")
        
        return results
    
    def analyze_cv_data(self, data):
        """
        Web API compatible method for Enhanced V4 Improved analysis
        """
        try:
            voltage = np.array(data['voltage'])
            current = np.array(data['current'])
            
            logger.info(f"🔍 Enhanced V4 Improved analyze_cv_data: {len(voltage)} points")
            logger.info(f"📊 V-range: {voltage.min():.3f}-{voltage.max():.3f}V, I-range: {current.min():.3f}-{current.max():.3f}µA")
            
            # Run enhanced detection
            detection_results = self.detect_peaks_enhanced_v4(voltage, current)
            
            # Format results for web API
            result = {
                'peaks': detection_results['peaks'],
                'scan_analysis': detection_results['scan_analysis'],
                'thresholds': detection_results['thresholds'],
                'all_peaks': detection_results['peaks'] + detection_results.get('rejected_peaks', []),
                'processing_time': 0.1,
                'method': 'enhanced_v4_improved',
                'ferrocyanide_optimized': True,
                'confidence_threshold': self.confidence_threshold,
                'voltage_ranges': {
                    'oxidation': self.ferrocyanide_ox_range,
                    'reduction': self.ferrocyanide_red_range
                },
                'improvements': [
                    'Expanded voltage ranges for better reduction detection',
                    'Lowered confidence threshold from 40% to 25%',
                    'Added edge effect detection and filtering',
                    'Improved baseline detection with Savitzky-Golay smoothing',
                    'Enhanced peak detection sensitivity'
                ]
            }
            
            ox_count = len([p for p in detection_results['peaks'] if p['type'] == 'oxidation'])
            red_count = len([p for p in detection_results['peaks'] if p['type'] == 'reduction'])
            
            logger.info(f"✅ Enhanced V4 Improved completed: {ox_count} ox + {red_count} red = {len(detection_results['peaks'])} total peaks")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Enhanced V4 Improved analyze_cv_data: {e}")
            raise
