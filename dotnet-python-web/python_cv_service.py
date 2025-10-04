#!/usr/bin/env python3
"""
🐍 Python CV Analysis Service for .NET Integration
================================================

Simple Flask service that provides CV peak detection APIs
compatible with the .NET CVPeakValidation.Api

Author: H743Poten Research Team
Date: October 4, 2025
"""

from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from scipy.signal import find_peaks
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class SimpleCVPeakDetector:
    """Enhanced CV peak detection optimized for ferrocyanide"""
    
    def detect_peaks(self, voltage, current, parameters):
        """Detect peaks in CV data with optimized parameters for ferrocyanide"""
        try:
            # Enhanced parameters optimized for ferrocyanide CV
            # Default values work better for typical ferrocyanide concentrations
            height = parameters.get('height', 0.5)  # Increased to avoid noise
            distance = parameters.get('distance', 20)  # Increased minimum distance between peaks
            prominence = parameters.get('prominence', 0.3)  # Increased to select significant peaks only
            width = parameters.get('width', 3)  # Reduced for sharper peak detection
            
            # Convert to numpy arrays
            voltage = np.array(voltage)
            current = np.array(current)
            
            # Find oxidation peaks (positive current)
            ox_peaks, ox_props = find_peaks(
                current, 
                height=height, 
                distance=distance, 
                prominence=prominence,
                width=width
            )
            
            # Find reduction peaks (negative current, so invert)
            red_peaks, red_props = find_peaks(
                -current, 
                height=height, 
                distance=distance, 
                prominence=prominence,
                width=width
            )
            
            peaks = []
            
            # More flexible peak filtering based on distance from scan limits
            # Instead of fixed voltage ranges, filter out peaks too close to Vmin/Vmax
            v_min = min(voltage)
            v_max = max(voltage)
            v_range = v_max - v_min
            
            # Default margin: 100mV from scan limits (adjustable via parameters)
            edge_margin = parameters.get('edge_margin_v', 0.10)  # 100mV margin from edges
            min_peak_voltage = v_min + edge_margin
            max_peak_voltage = v_max - edge_margin
            
            logger.info(f"Voltage scan range: {v_min:.3f}V to {v_max:.3f}V (total: {v_range:.3f}V)")
            logger.info(f"Peak detection zone: {min_peak_voltage:.3f}V to {max_peak_voltage:.3f}V (margin: {edge_margin:.3f}V)")
            
            # Process oxidation peaks with flexible edge-based filtering
            for i, peak_idx in enumerate(ox_peaks):
                peak_voltage = float(voltage[peak_idx])
                peak_current = float(current[peak_idx])
                
                # Filter peaks that are too close to scan limits (more flexible)
                if min_peak_voltage <= peak_voltage <= max_peak_voltage and peak_current > 0:
                    peak = {
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'oxidation',
                        'confidence': float(min(ox_props['prominences'][i] / max(current) * 10, 1.0)),
                        'height': float(ox_props['prominences'][i]) if 'prominences' in ox_props else None,
                        'width': float(ox_props['widths'][i]) if 'widths' in ox_props else None,
                        'area': None
                    }
                    peaks.append(peak)
            
            # Process reduction peaks with flexible edge-based filtering
            for i, peak_idx in enumerate(red_peaks):
                peak_voltage = float(voltage[peak_idx])
                peak_current = float(current[peak_idx])
                
                # Filter peaks that are too close to scan limits (more flexible)
                if min_peak_voltage <= peak_voltage <= max_peak_voltage and peak_current < 0:
                    peak = {
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'reduction',
                        'confidence': float(min(red_props['prominences'][i] / abs(min(current)) * 10, 1.0)),
                        'height': float(red_props['prominences'][i]) if 'prominences' in red_props else None,
                        'width': float(red_props['widths'][i]) if 'widths' in red_props else None,
                        'area': None
                    }
                    peaks.append(peak)
            
            # Log peak detection results for debugging
            total_ox_found = len(ox_peaks)
            total_red_found = len(red_peaks)
            filtered_peaks = len(peaks)
            
            logger.info(f"Peak detection summary:")
            logger.info(f"  Raw oxidation peaks found: {total_ox_found}")
            logger.info(f"  Raw reduction peaks found: {total_red_found}")
            logger.info(f"  Filtered peaks (ferrocyanide range): {filtered_peaks}")
            logger.info(f"  Detection parameters: height={height}, distance={distance}, prominence={prominence}")
            logger.info(f"  Flexible filtering: Peak zone=[{min_peak_voltage:.3f}-{max_peak_voltage:.3f}V], Edge margin={edge_margin:.3f}V")
            
            # Sort peaks by voltage for consistent output
            peaks.sort(key=lambda x: x['voltage'])
            
            return peaks
            
        except Exception as e:
            logger.error(f"Error in peak detection: {e}")
            return []
    
    def generate_plot(self, voltage, current, peaks):
        """Generate CV plot with detected peaks"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Plot CV curve
            plt.plot(voltage, current, 'b-', linewidth=2, label='CV Data')
            
            # Plot peaks
            for peak in peaks:
                color = 'red' if peak['type'] == 'oxidation' else 'green'
                marker = 'o' if peak['type'] == 'oxidation' else '^'
                plt.scatter(peak['voltage'], peak['current'], 
                          c=color, s=100, marker=marker, 
                          edgecolors='black', linewidth=1,
                          label=f"{peak['type'].title()} Peak" if peaks.index(peak) == 0 or 
                               not any(p['type'] == peak['type'] and peaks.index(p) < peaks.index(peak) for p in peaks) else "")
            
            plt.xlabel('Voltage (V)')
            plt.ylabel('Current (A)')
            plt.title('Cyclic Voltammetry with Detected Peaks')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{plot_data}"
            
        except Exception as e:
            logger.error(f"Error generating plot: {e}")
            return ""

# Initialize detector
detector = SimpleCVPeakDetector()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Python CV Analysis Service',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_cv():
    """Analyze CV data for peaks - Compatible with .NET API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Log incoming data for debugging
        logger.info(f"Received data keys: {list(data.keys())}")
        logger.info(f"Data content preview: {str(data)[:200]}...")
        
        # Extract data from .NET request format
        voltage = data.get('voltage', [])
        current = data.get('current', [])
        parameters = data.get('parameters', {})
        
        if not voltage or not current:
            logger.error(f"Missing data - voltage: {len(voltage) if voltage else 0}, current: {len(current) if current else 0}")
            return jsonify({'success': False, 'error': 'Voltage and current data required', 'received_keys': list(data.keys())}), 400
        
        if len(voltage) != len(current):
            logger.error(f"Length mismatch - voltage: {len(voltage)}, current: {len(current)}")
            return jsonify({'success': False, 'error': 'Voltage and current arrays must have same length'}), 400
        
        logger.info(f"Analyzing CV data: {len(voltage)} points")
        
        # Detect peaks
        peaks = detector.detect_peaks(voltage, current, parameters)
        
        # No longer generate plot since we use Plotly.js in frontend
        
        response_data = {
            'peaks': peaks,
            'metadata': {
                'data_points': len(voltage),
                'peaks_detected': len(peaks),
                'analysis_method': 'scipy_find_peaks',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"Analysis complete: {len(peaks)} peaks detected")
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_cv: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate_plot', methods=['POST'])
def generate_plot():
    """Generate plot for CV data with peaks"""
    try:
        data = request.get_json()
        
        cv_data = data.get('cv_data', {})
        peaks_data = data.get('peaks', [])
        
        voltage = cv_data.get('voltage', [])
        current = cv_data.get('current', [])
        
        if not voltage or not current:
            return jsonify({'success': False, 'error': 'CV data required'}), 400
        
        # Convert peaks data to internal format
        peaks = []
        for peak in peaks_data:
            peaks.append({
                'voltage': peak.get('voltage', 0),
                'current': peak.get('current', 0),
                'type': peak.get('type', 'unknown'),
                'confidence': peak.get('confidence', 0)
            })
        
        plot_url = detector.generate_plot(voltage, current, peaks)
        
        return jsonify({
            'success': True,
            'data': {'plot_url': plot_url}
        })
        
    except Exception as e:
        logger.error(f"Error generating plot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'Python CV Analysis Service',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            '/health - Health check',
            '/api/analyze - Analyze CV data for peaks',
            '/api/generate_plot - Generate CV plot'
        ],
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🐍 Starting Python CV Analysis Service")
    print("📊 Compatible with .NET CVPeakValidation.Api")
    print("🚀 Access at: http://localhost:5003")
    print("🔗 Also available at: http://127.0.0.1:5003")
    
    # Bind to all interfaces for WSL compatibility
    app.run(host='0.0.0.0', port=5003, debug=True, use_reloader=False)