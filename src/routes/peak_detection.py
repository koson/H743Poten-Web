import time
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, session
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import linregress
import logging
import uuid
import glob
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

peak_detection_bp = Blueprint('peak_detection', __name__)

def detect_linear_segments(voltage, current, min_length=5, r2_threshold=0.95):
    """Find all linear segments that could be baseline candidates"""
    segments = []
    n = len(voltage)
    
    for start in range(n - min_length + 1):
        for length in range(min_length, min(50, n - start + 1)):
            end = start + length - 1
            if end >= n:
                break
                
            v_seg = voltage[start:end+1]
            i_seg = current[start:end+1]
            
            if not (np.all(np.isfinite(v_seg)) and np.all(np.isfinite(i_seg))):
                continue
                
            voltage_span = v_seg[-1] - v_seg[0]
            if abs(voltage_span) < 0.02:
                continue
            
            try:
                slope, intercept, r_value, p_value, std_err = linregress(v_seg, i_seg)
                r2 = r_value ** 2
                
                if r2 >= r2_threshold:
                    segments.append({
                        'start_idx': start,
                        'end_idx': end,
                        'length': length,
                        'slope': slope,
                        'intercept': intercept,
                        'r2': r2,
                        'voltage_range': (v_seg[0], v_seg[-1]),
                        'voltage_span': voltage_span,
                        'mean_current': np.mean(i_seg),
                        'std_current': np.std(i_seg)
                    })
            except:
                continue
    
    # Remove overlapping segments
    segments = sorted(segments, key=lambda x: x['r2'], reverse=True)
    filtered = []
    for segment in segments:
        is_overlapping = False
        for selected in filtered:
            overlap_start = max(segment['start_idx'], selected['start_idx'])
            overlap_end = min(segment['end_idx'], selected['end_idx'])
            overlap_length = max(0, overlap_end - overlap_start + 1)
            segment_length = segment['end_idx'] - segment['start_idx'] + 1
            overlap_ratio = overlap_length / segment_length
            
            if overlap_ratio > 0.6:
                is_overlapping = True
                break
        
        if not is_overlapping:
            filtered.append(segment)
    
    return filtered

def detect_improved_baseline_2step(voltage, current):
    """2-step baseline detection: find segments, then select best ones"""
    try:
        # Step 1: Find linear segments
        segments = detect_linear_segments(voltage, current)
        
        if not segments:
            logger.warning("No linear segments found, using simple baseline")
            n = len(voltage)
            mid = n // 2
            
            def simple_fit(v, i):
                if len(v) < 2:
                    return np.full_like(v, np.nan)
                coeffs = np.polyfit(v, i, 1)
                return np.polyval(coeffs, v)
            
            return simple_fit(voltage[:mid], current[:mid]), simple_fit(voltage[mid:], current[mid:])
        
        # Step 2: Find peaks first to guide baseline selection
        # Use simple prominence-based peak detection to identify peak regions
        current_norm = current / np.abs(current).max()
        pos_peaks, _ = find_peaks(current_norm, prominence=0.1, width=3)
        neg_peaks, _ = find_peaks(-current_norm, prominence=0.1, width=3)
        all_peak_indices = sorted(list(pos_peaks) + list(neg_peaks))
        
        logger.info(f"Found {len(all_peak_indices)} peaks for baseline guidance: {all_peak_indices}")
        
        # Find the turning point (minimum voltage typically)
        min_voltage_idx = np.argmin(voltage)
        
        # Step 3: Select baseline segments intelligently
        forward_segments = [s for s in segments if s['end_idx'] <= min_voltage_idx + 10]
        reverse_segments = [s for s in segments if s['start_idx'] >= min_voltage_idx - 10]
        
        logger.info(f"Forward segments: {len(forward_segments)}, Reverse segments: {len(reverse_segments)}")
        
        def score_baseline_segment(segment, scan_direction='forward'):
            """Score a segment for baseline suitability with peak awareness"""
            logger.info(f"[BASELINE] Scoring segment {segment['start_idx']}-{segment['end_idx']} for {scan_direction} baseline")
            score = 0.0
            
            # Linearity (R²) - higher is better (stricter requirement)
            if segment['r2'] < 0.8:  # Poor linearity penalty
                score -= 30
                logger.debug(f"[BASELINE] Poor linearity penalty: -30")
            
            r2_score = segment['r2'] * 50
            score += r2_score
            logger.debug(f"[BASELINE] R² score: {r2_score:.2f}")
            
            # Length - longer is better (minimum 8 points for good baseline)
            if segment['length'] < 8:
                score -= 50  # Heavy penalty for too short segments
                logger.debug(f"[BASELINE] Short segment penalty: -50")
            
            length_score = min(segment['length'] / 20, 1) * 30
            score += length_score
            logger.debug(f"[BASELINE] Length score: {length_score:.2f}")
            
            # Low slope - more horizontal is better for baseline (stricter penalty)
            slope_abs = abs(segment['slope'])
            if slope_abs > 50:  # Very steep slopes are bad for baseline
                slope_penalty = 100  # Maximum penalty
            else:
                slope_penalty = slope_abs * 2  # Increased penalty factor
            score -= slope_penalty
            logger.debug(f"[BASELINE] Slope penalty: {slope_penalty:.2f} (slope: {segment['slope']:.2e})")
            
            # Voltage span - reasonable span is better
            voltage_span = abs(segment['voltage_span'])
            if 0.05 <= voltage_span <= 0.3:
                score += 10
            
            # Low current standard deviation - more stable is better
            if segment['std_current'] > 0:
                score += max(0, 10 - (segment['std_current'] * 1e6))
            
            # NEW: Peak awareness - prefer segments that are NOT in peak regions
            segment_mid = (segment['start_idx'] + segment['end_idx']) // 2
            min_distance_to_peak = float('inf')
            
            for peak_idx in all_peak_indices:
                distance = abs(segment_mid - peak_idx)
                min_distance_to_peak = min(min_distance_to_peak, distance)
            
            # Bonus for being far from peaks (baseline should be in non-peak regions)
            if min_distance_to_peak > 20:
                score += 20
            elif min_distance_to_peak > 10:
                score += 10
            else:
                score -= 5  # Penalty for being too close to peaks
            
            # NEW: Position preference for forward scan
            if scan_direction == 'forward':
                # For forward scan, prefer segments that are BEFORE major peaks
                # Find the first significant peak in forward scan
                forward_peaks = [p for p in all_peak_indices if p < min_voltage_idx]
                if forward_peaks:
                    first_peak = min(forward_peaks)
                    logger.debug(f"[BASELINE] Forward scan first peak at index {first_peak}")
                    if segment['end_idx'] < first_peak - 5:  # Must be well before first peak
                        score += 25  # Strong bonus for pre-peak segments
                        logger.debug(f"[BASELINE] Pre-peak bonus applied: +25")
                    elif segment['start_idx'] > first_peak:  # Penalty for post-peak segments
                        score -= 15
                        logger.debug(f"[BASELINE] Post-peak penalty applied: -15")
                        
                # Additional preference for earlier segments in forward scan
                segment_position = segment['start_idx'] / len(voltage)
                if segment_position < 0.3:  # First 30% of scan
                    score += 15
                    logger.debug(f"[BASELINE] Early position bonus: +15")
                elif segment_position > 0.7:  # Last 30% of forward scan
                    score -= 10
                    logger.debug(f"[BASELINE] Late position penalty: -10")
            
            logger.info(f"[BASELINE] Final segment score: {score:.2f}")
            return score
        
        def select_best_segment(segment_list, scan_direction='forward'):
            if not segment_list:
                logger.warning(f"[BASELINE] No segments available for {scan_direction} baseline")
                return None
            
            logger.info(f"[BASELINE] Selecting best segment from {len(segment_list)} {scan_direction} segments")
            scored_segments = [(score_baseline_segment(s, scan_direction), s) for s in segment_list]
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            
            logger.info(f"[BASELINE] {scan_direction.capitalize()} segment scores: {[f'{s[0]:.1f}' for s in scored_segments[:3]]}")
            
            best_score, best_segment = scored_segments[0]
            logger.info(f"[BASELINE] Selected {scan_direction} segment [{best_segment['start_idx']}:{best_segment['end_idx']}] with score {best_score:.2f}")
            return best_segment
        
        forward_segment = select_best_segment(forward_segments, 'forward')
        reverse_segment = select_best_segment(reverse_segments, 'reverse')
        
        # Step 4: Generate baseline arrays
        n = len(voltage)
        baseline_forward = np.full(n//2, np.nan)
        baseline_reverse = np.full(n - n//2, np.nan)
        
        if forward_segment:
            v_forward = voltage[:n//2]
            baseline_forward = forward_segment['slope'] * v_forward + forward_segment['intercept']
            logger.info(f"Forward baseline: slope={forward_segment['slope']:.2e}, R²={forward_segment['r2']:.3f}, segment=[{forward_segment['start_idx']}:{forward_segment['end_idx']}]")
        
        if reverse_segment:
            v_reverse = voltage[n//2:]
            baseline_reverse = reverse_segment['slope'] * v_reverse + reverse_segment['intercept']
            logger.info(f"Reverse baseline: slope={reverse_segment['slope']:.2e}, R²={reverse_segment['r2']:.3f}, segment=[{reverse_segment['start_idx']}:{reverse_segment['end_idx']}]")
        
        return baseline_forward, baseline_reverse
        
    except Exception as e:
        logger.error(f"Error in improved baseline detection: {e}")
        # Fallback
        n = len(voltage)
        mid = n // 2
        def simple_fit(v, i):
            if len(v) < 2:
                return np.full_like(v, np.nan)
            coeffs = np.polyfit(v, i, 1)
            return np.polyval(coeffs, v)
        return simple_fit(voltage[:mid], current[:mid]), simple_fit(voltage[mid:], current[mid:])

# In-memory storage for analysis sessions
# Global variable for tracking peak detection progress
peak_detection_progress = {
    'active': False,
    'current_file': 0,
    'total_files': 0,
    'percent': 0,
    'message': '',
    'start_time': None
}

analysis_sessions = {}

@peak_detection_bp.route('/api/get_saved_files')
def get_saved_files():
    """Get list of saved CSV files"""
    try:
        data_dir = os.path.join(current_app.root_path, '..', 'data_logs', 'csv')
        data_dir = os.path.abspath(data_dir)  # Resolve to absolute path
        
        if not os.path.exists(data_dir):
            return jsonify([])
        
        files = []
        for file_path in glob.glob(os.path.join(data_dir, '*.csv')):
            try:
                stat = os.stat(file_path)
                filename = os.path.basename(file_path)
                files.append({
                    'name': filename,
                    'filename': filename,  # Use filename instead of full path
                    'path': os.path.abspath(file_path),  # Keep full path for debugging
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'size': stat.st_size
                })
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['date'], reverse=True)
        return jsonify(files)
        
    except Exception as e:
        logger.error(f"Error getting saved files: {str(e)}")
        return jsonify([])

@peak_detection_bp.route('/api/load_saved_file_by_name/<filename>')
def load_saved_file_by_name(filename):
    """Load data from a saved CSV file by filename"""
    try:
        # Construct the file path
        data_dir = os.path.join(current_app.root_path, '..', 'data_logs', 'csv')
        data_dir = os.path.abspath(data_dir)
        file_path = os.path.join(data_dir, filename)
        
        # Security check - ensure the file is within the data directory
        if not os.path.abspath(file_path).startswith(data_dir):
            return jsonify({'success': False, 'error': 'Invalid file path'})
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': f'File not found: {filename}'})
        
        return load_csv_file(file_path)
        
    except Exception as e:
        logger.error(f"Error loading saved file by name: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def load_csv_file(file_path):
    """Helper function to load and parse CSV file"""
    try:
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File too short'})
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return jsonify({'success': False, 'error': f'Could not find voltage or current columns in headers: {headers}'})
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        if current_unit == 'ua':
            current_scale = 1e-6  # microAmps to Amps
        elif current_unit == 'ma':
            current_scale = 1e-3  # milliAmps to Amps
        elif current_unit == 'na':
            current_scale = 1e-9  # nanoAmps to Amps
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({'success': False, 'error': 'No valid data points found'})
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        logger.info(f"Current range: {min(current):.6e} to {max(current):.6e} A")
        
        return jsonify({
            'success': True,
            'data': {
                'voltage': voltage,
                'current': current
            },
            'metadata': {
                'points': len(voltage),
                'voltage_range': [min(voltage), max(voltage)],
                'current_range': [min(current), max(current)],
                'current_unit': current_unit,
                'current_scale': current_scale
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@peak_detection_bp.route('/api/load_saved_file/<path:file_path>')
def load_saved_file(file_path):
    """Load data from a saved CSV file"""
    try:
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File too short'})
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return jsonify({'success': False, 'error': f'Could not find voltage or current columns in headers: {headers}'})
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        if current_unit == 'ua':
            current_scale = 1e-6  # microAmps to Amps
        elif current_unit == 'ma':
            current_scale = 1e-3  # milliAmps to Amps
        elif current_unit == 'na':
            current_scale = 1e-9  # nanoAmps to Amps
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({'success': False, 'error': 'No valid data points found'})
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        logger.info(f"Current range: {min(current):.6e} to {max(current):.6e} A")
        
        return jsonify({
            'success': True,
            'data': {
                'voltage': voltage,
                'current': current
            },
            'metadata': {
                'points': len(voltage),
                'voltage_range': [min(voltage), max(voltage)],
                'current_range': [min(current), max(current)],
                'current_unit': current_unit,
                'current_scale': current_scale
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading saved file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@peak_detection_bp.route('/create_analysis_session', methods=['POST'])
def create_analysis_session():
    """Create a new analysis session and store data"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided to create_analysis_session")
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Creating analysis session with data keys: {list(data.keys())}")
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store data in in-memory storage
        # Ensure peaks is a list of dicts, not an int
        peaks = data.get('peaks', [])
        if isinstance(peaks, int):
            # Try to get from previewData if available
            peaks = data.get('previewData', {}).get('peaks', [])
        if not isinstance(peaks, list):
            peaks = []

        # Handle multi-trace: data['data'] is list of traces, each should have 'filename'
        traces = data.get('data', {})
        if isinstance(traces, list):
            # Add filename if missing
            for i, trace in enumerate(traces):
                if 'filename' not in trace:
                    # Try to get from filenames array if present
                    filenames = data.get('filenames') or data.get('file_labels')
                    if filenames and i < len(filenames):
                        trace['filename'] = filenames[i]
                    else:
                        trace['filename'] = f'Trace {i+1}'
        elif isinstance(traces, dict):
            # Single trace: add filename if present
            if 'filename' not in traces:
                filename = data.get('filename') or (data.get('filenames')[0] if data.get('filenames') else None)
                if filename:
                    traces['filename'] = filename
        analysis_sessions[session_id] = {
            'peaks': peaks,
            'data': traces,
            'method': data.get('method', ''),
            'methodName': data.get('methodName', ''),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Created analysis session {session_id} for method {data.get('method')}")
        return jsonify({'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error creating analysis session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@peak_detection_bp.route('/peak_analysis/<session_id>')
def peak_analysis(session_id):
    """Render peak analysis details page"""
    try:
        # Get data from in-memory storage
        session_data = analysis_sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found in analysis_sessions")
            logger.info(f"Available sessions: {list(analysis_sessions.keys())}")
            return "Session not found", 404
        
        logger.info(f"Loading analysis session {session_id} for method {session_data.get('method')}")
        
        return render_template('peak_analysis.html',
                             peaks=session_data['peaks'],
                             data=session_data['data'],
                             method=session_data['method'],
                             methodName=session_data['methodName'])
                             
    except Exception as e:
        logger.error(f"Error rendering peak analysis: {str(e)}")
        return str(e), 500

@peak_detection_bp.route('/get-progress', methods=['GET'])
def get_progress():
    """Get current peak detection progress"""
    global peak_detection_progress
    
    # Calculate elapsed time if active
    elapsed_time = None
    if peak_detection_progress['active'] and peak_detection_progress['start_time']:
        elapsed_time = int(time.time() - peak_detection_progress['start_time'])
    
    return jsonify({
        'success': True,
        'progress': {
            **peak_detection_progress,
            'elapsed_time': elapsed_time
        }
    })

@peak_detection_bp.route('/get-peaks/<method>', methods=['POST'])
def get_peaks(method):
    """
    Analyze CV data and detect peaks using specified method
    Returns peaks with their positions and characteristics
    """
    global peak_detection_progress
    
    try:
        logger.info(f"Starting peak detection with method: {method}")
        
        # Initialize progress tracking
        peak_detection_progress.update({
            'active': True,
            'current_file': 0,
            'total_files': 0,
            'percent': 0,
            'message': 'Initializing...',
            'start_time': time.time()
        })
        
        # Get data from POST request
        data = request.get_json()
        if not data:
            peak_detection_progress['active'] = False
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Multi-trace: voltage/current เป็น list of list หรือ dataFiles
        if 'dataFiles' in data and isinstance(data['dataFiles'], list):
            nFiles = len(data['dataFiles'])
            logger.info(f"Processing {nFiles} files with method: {method}")
            
            # Update progress with total files
            peak_detection_progress.update({
                'total_files': nFiles,
                'message': f'Processing {nFiles} files...'
            })
            
            peaks_per_file = [ [] for _ in range(nFiles) ]
            for i, file in enumerate(data['dataFiles']):
                    # Update progress
                    progress_percent = int((i / nFiles) * 100)
                    peak_detection_progress.update({
                        'current_file': i + 1,
                        'percent': progress_percent,
                        'message': f'Processing file {i+1}/{nFiles}...'
                    })
                    
                    logger.info(f"[PROGRESS] Processing file {i+1}/{nFiles} ({progress_percent}%)")
                    
                    voltage = np.array(file.get('voltage', []))
                    current = np.array(file.get('current', []))
                    logger.info(f"[DEBUG] File {i}: voltage len={len(voltage)}, current len={len(current)}")
                    logger.info(f"[DEBUG] File {i}: voltage min={np.min(voltage) if len(voltage)>0 else 'NA'}, max={np.max(voltage) if len(voltage)>0 else 'NA'}, mean={np.mean(voltage) if len(voltage)>0 else 'NA'}")
                    logger.info(f"[DEBUG] File {i}: current min={np.min(current) if len(current)>0 else 'NA'}, max={np.max(current) if len(current)>0 else 'NA'}, mean={np.mean(current) if len(current)>0 else 'NA'}")
                    if np.any(np.isnan(voltage)) or np.any(np.isnan(current)):
                        logger.warning(f"[DEBUG] File {i}: NaN detected in voltage or current!")
                    if np.any(np.isinf(voltage)) or np.any(np.isinf(current)):
                        logger.warning(f"[DEBUG] File {i}: Inf detected in voltage or current!")
                    try:
                        result = detect_cv_peaks(voltage, current, method=method)
                        file_peaks = result['peaks']
                        logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                        
                        # Add baseline data to each peak if available
                        if 'baseline' in result:
                            for p in file_peaks:
                                p['baseline'] = result['baseline']
                        
                    except Exception as e:
                        logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                        file_peaks = []
                    for p in file_peaks:
                        p['fileIdx'] = i
                    peaks_per_file[i] = file_peaks
            
            # Mark completion
            peak_detection_progress.update({
                'current_file': nFiles,
                'percent': 100,
                'message': f'Completed processing {nFiles} files',
                'active': False
            })
            
            logger.info(f"[PROGRESS] Processing complete: {nFiles}/{nFiles} files (100%)")
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify({'success': True, 'peaks': peaks_per_file})
        elif isinstance(data.get('voltage'), list) and len(data['voltage']) > 0 and isinstance(data['voltage'][0], list):
            # voltage/current เป็น list of list
            nFiles = len(data['voltage'])
            peaks_per_file = [ [] for _ in range(nFiles) ]
            for i, (v, c) in enumerate(zip(data['voltage'], data['current'])):
                voltage = np.array(v)
                current = np.array(c)
                logger.info(f"[DEBUG] File {i}: voltage len={len(voltage)}, current len={len(current)}")
                logger.info(f"[DEBUG] File {i}: voltage min={np.min(voltage) if len(voltage)>0 else 'NA'}, max={np.max(voltage) if len(voltage)>0 else 'NA'}, mean={np.mean(voltage) if len(voltage)>0 else 'NA'}")
                logger.info(f"[DEBUG] File {i}: current min={np.min(current) if len(current)>0 else 'NA'}, max={np.max(current) if len(current)>0 else 'NA'}, mean={np.mean(current) if len(current)>0 else 'NA'}")
                if np.any(np.isnan(voltage)) or np.any(np.isnan(current)):
                    logger.warning(f"[DEBUG] File {i}: NaN detected in voltage or current!")
                if np.any(np.isinf(voltage)) or np.any(np.isinf(current)):
                    logger.warning(f"[DEBUG] File {i}: Inf detected in voltage or current!")
                try:
                    file_peaks = detect_cv_peaks(voltage, current, method=method)['peaks']
                    logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                except Exception as e:
                    logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                    file_peaks = []
                for p in file_peaks:
                    p['fileIdx'] = i
                peaks_per_file[i] = file_peaks
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify({'success': True, 'peaks': peaks_per_file})
        else:
            # Single trace (default)
            if 'voltage' not in data or 'current' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing voltage or current data in request'
                }), 400
            voltage = np.array(data['voltage'])
            current = np.array(data['current'])
            results = detect_cv_peaks(voltage, current, method=method)
            return jsonify({'success': True, **results})
    except Exception as e:
        logger.error(f"Error in peak detection: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@peak_detection_bp.route('/get-settings', methods=['GET'])
def get_settings():
    """Get current peak detection settings"""
    return jsonify({
        'success': True,
        'settings': {
            'prominence': current_app.config.get('PEAK_PROMINENCE', 0.1),
            'width': current_app.config.get('PEAK_WIDTH', 5),
            'description': {
                'prominence': 'Minimum peak prominence (normalized)',
                'width': 'Minimum peak width in data points'
            }
        }
    })

@peak_detection_bp.route('/update-settings', methods=['POST'])
def update_settings():
    """Update peak detection settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No settings provided'
            })

        # Update settings
        if 'prominence' in data:
            current_app.config['PEAK_PROMINENCE'] = float(data['prominence'])
        if 'width' in data:
            current_app.config['PEAK_WIDTH'] = int(data['width'])

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': {
                'prominence': current_app.config.get('PEAK_PROMINENCE', 0.1),
                'width': current_app.config.get('PEAK_WIDTH', 5)
            }
        })

    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def detect_cv_peaks(voltage, current, method='prominence'):
    """
    Detect peaks in CV data using specified method
    Returns list of peaks with their characteristics
    """
    try:
        if method == 'prominence':
            return detect_peaks_prominence(voltage, current)
        elif method == 'derivative':
            return detect_peaks_derivative(voltage, current)
        elif method == 'ml':
            return detect_peaks_ml(voltage, current)
        else:
            raise ValueError(f"Unknown method: {method}")
    except Exception as e:
        logger.error(f"Error in CV peak detection: {str(e)}")
        raise

def detect_peaks_prominence(voltage, current):
    """Detect peaks using prominence method"""
    try:
        # Get settings from config or use defaults
        prominence = current_app.config.get('PEAK_PROMINENCE', 0.1)
        width = current_app.config.get('PEAK_WIDTH', 5)

        # Normalize current for peak detection
        current_norm = current / np.abs(current).max()

        # Find positive peaks (oxidation)
        pos_peaks, pos_properties = find_peaks(
            current_norm,
            prominence=prominence,
            width=width
        )

        # Find negative peaks (reduction)
        neg_peaks, neg_properties = find_peaks(
            -current_norm,
            prominence=prominence,
            width=width
        )

        # Format peak data
        peaks = []

        # Add oxidation peaks
        for i, peak_idx in enumerate(pos_peaks):
            peaks.append({
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'type': 'oxidation',
                'confidence': float(pos_properties['prominences'][i] * 100)
            })

        # Add reduction peaks
        for i, peak_idx in enumerate(neg_peaks):
            peaks.append({
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'type': 'reduction',
                'confidence': float(neg_properties['prominences'][i] * 100)
            })

        # --- Improved Baseline fitting แยกฝั่ง (2-step process) ---
        baseline_forward, baseline_reverse = detect_improved_baseline_2step(voltage, current)
        
        # Combine for full baseline
        baseline_full = np.concatenate([baseline_forward, baseline_reverse])

        return {
            'peaks': peaks,
            'method': 'prominence',
            'params': {
                'prominence': prominence,
                'width': width
            },
            'baseline': {
                'forward': baseline_forward.tolist(),
                'reverse': baseline_reverse.tolist(),
                'full': baseline_full.tolist()
            }
        }

    except Exception as e:
        logger.error(f"Error in prominence peak detection: {str(e)}")
        raise

def detect_peaks_derivative(voltage, current):
    """Detect peaks using derivative method with improved filtering"""
    try:
        from scipy import signal
        
        # Smooth data first to reduce noise
        window_length = min(11, len(current) // 10)  # Adaptive window
        if window_length % 2 == 0:
            window_length += 1  # Must be odd
        if window_length >= 3:
            current_smooth = signal.savgol_filter(current, window_length, 3)
        else:
            current_smooth = current
        
        # Calculate first derivative
        dv = np.gradient(voltage)
        di = np.gradient(current_smooth)
        slope = di/dv
        
        # Find zero crossings in second derivative
        d2i = np.gradient(slope)
        zero_crossings = np.where(np.diff(np.signbit(d2i)))[0]
        
        peaks = []
        
        # Filter peaks by significance
        current_std = np.std(current)
        current_range = np.max(current) - np.min(current)
        
        # Adaptive thresholds based on data characteristics
        min_peak_height = max(current_std * 0.2, current_range * 0.01)  # More lenient
        min_prominence = max(current_std * 0.1, current_range * 0.005)   # More lenient
        
        logger.info(f"Derivative filtering: std={current_std:.2e}, range={current_range:.2e}, min_height={min_peak_height:.2e}, min_prominence={min_prominence:.2e}")
        
        for idx in zero_crossings:
            if idx < 5 or idx >= len(current) - 5:  # Skip edge points
                continue
                
            # Check if this is a significant peak
            peak_current = current[idx]
            local_baseline = np.mean(current[max(0, idx-10):min(len(current), idx+10)])
            peak_height = abs(peak_current - local_baseline)
            
            # More lenient filtering
            if peak_height < min_peak_height:
                continue
                
            # Check prominence (peak stands out from surroundings)
            left_vals = current[max(0, idx-5):idx] if idx > 0 else [peak_current]
            right_vals = current[idx+1:min(len(current), idx+6)] if idx < len(current)-1 else [peak_current]
            
            left_min = np.min(left_vals) if len(left_vals) > 0 else peak_current
            right_min = np.min(right_vals) if len(right_vals) > 0 else peak_current
            prominence = abs(peak_current) - max(abs(left_min), abs(right_min))
            
            # More lenient prominence check
            if prominence < min_prominence:
                continue
            
            peak_type = 'oxidation' if current[idx] > local_baseline else 'reduction'
            confidence = min(100.0, (peak_height / max(abs(current_range), 1e-10)) * 100)
            
            peaks.append({
                'voltage': float(voltage[idx]),
                'current': float(current[idx]),
                'type': peak_type,
                'confidence': float(confidence)
            })
        
        # Less restrictive peak limit
        if len(peaks) > 50:  # Increased from 20
            peaks = sorted(peaks, key=lambda x: x['confidence'], reverse=True)[:50]
        
        # Fallback: if no peaks found, use simpler method
        if len(peaks) == 0:
            logger.warning("No peaks found with derivative method, trying fallback")
            # Use scipy find_peaks as fallback
            from scipy.signal import find_peaks
            current_norm = current / np.abs(current).max()
            
            # Find positive peaks
            pos_peaks, _ = find_peaks(current_norm, prominence=0.1, width=3)
            # Find negative peaks  
            neg_peaks, _ = find_peaks(-current_norm, prominence=0.1, width=3)
            
            for peak_idx in pos_peaks:
                peaks.append({
                    'voltage': float(voltage[peak_idx]),
                    'current': float(current[peak_idx]),
                    'type': 'oxidation',
                    'confidence': 75.0
                })
            
            for peak_idx in neg_peaks:
                peaks.append({
                    'voltage': float(voltage[peak_idx]),
                    'current': float(current[peak_idx]),
                    'type': 'reduction', 
                    'confidence': 75.0
                })
            
            logger.info(f"Fallback method found {len(peaks)} peaks")
            
        logger.info(f"Derivative method found {len(peaks)} significant peaks (filtered from {len(zero_crossings)} zero crossings)")
            
        return {
            'peaks': peaks,
            'method': 'derivative',
            'params': {
                'smoothing': 'savgol_filter',
                'window': window_length,
                'min_height': min_peak_height,
                'min_prominence': min_prominence,
                'zero_crossings_found': len(zero_crossings),
                'peaks_after_filtering': len(peaks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in derivative peak detection: {str(e)}")
        raise

def detect_peaks_ml(voltage, current):
    """Detect peaks using ML-enhanced method"""
    try:
        # Start with prominence method as baseline
        base_results = detect_peaks_prominence(voltage, current)
        base_peaks = base_results['peaks']
        
        # Add ML enhancements (feature extraction)
        enhanced_peaks = []
        for peak in base_peaks:
            # Find peak width at half height
            peak_idx = np.where((voltage == peak['voltage']) & (current == peak['current']))[0][0]
            half_height = peak['current'] / 2
            left_idx = right_idx = peak_idx
            
            while left_idx > 0 and abs(current[left_idx]) > abs(half_height):
                left_idx -= 1
            while right_idx < len(current)-1 and abs(current[right_idx]) > abs(half_height):
                right_idx += 1
                
            width = voltage[right_idx] - voltage[left_idx]
            area = np.trapz(current[left_idx:right_idx], voltage[left_idx:right_idx])
            
            enhanced_peaks.append({
                'voltage': peak['voltage'],
                'current': peak['current'],
                'type': peak['type'],
                'confidence': min(100.0, peak['confidence'] * 1.1),  # ML confidence boost
                'width': float(width),
                'area': float(area)
            })
            
        return {
            'peaks': enhanced_peaks,
            'method': 'ml',
            'params': {
                'feature_extraction': ['width', 'area'],
                'confidence_boost': 1.1
            },
            'baseline': base_results.get('baseline', {})  # Pass through baseline from prominence method
        }
        
    except Exception as e:
        logger.error(f"Error in ML peak detection: {str(e)}")
        raise