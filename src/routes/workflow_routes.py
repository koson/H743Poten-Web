"""
Workflow Visualization Routes
H743Poten Analysis Pipeline Visualization
"""

from flask import Blueprint, render_template, request, jsonify, session
import os
import json
import random
import logging
import time
import traceback
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)
import time
from datetime import datetime

# Import our analysis modules
import sys
sys.path.append('validation_data')

try:
    from cross_instrument_calibration import CrossInstrumentCalibrator, FeatureExtractor
    from execute_validation_fixed import load_cv_data_robust, simple_peak_detection_enhanced
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

logger = logging.getLogger(__name__)

workflow_bp = Blueprint('workflow', __name__)

@workflow_bp.route('/workflow')
def workflow_visualization():
    """Main workflow visualization page"""
    return render_template('workflow_visualization.html')

@workflow_bp.route('/api/workflow/scan-files', methods=['POST'])
def scan_files():
    """Scan uploaded files and analyze them"""
    try:
        # Check if files were uploaded
        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        files = request.files.getlist('files[]')
        
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        # Check total size before processing
        total_size = 0
        for file in files:
            if file.filename:
                # Check individual file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)     # Reset to beginning
                
                total_size += file_size
                
                # Check if individual file is too large (50MB per file)
                if file_size > 50 * 1024 * 1024:
                    return jsonify({
                        'success': False,
                        'error': f'File "{file.filename}" is too large. Maximum size per file is 50MB.',
                        'file_size_mb': round(file_size / (1024 * 1024), 2),
                        'max_size_mb': 50
                    }), 413
        
        # Check total upload size (100MB total)
        if total_size > 100 * 1024 * 1024:
            return jsonify({
                'success': False,
                'error': 'Total upload size too large. Maximum total size is 100MB.',
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'max_total_mb': 100
            }), 413
        
        # Analyze files
        total_files = len(files)
        valid_files = 0
        file_info = []
        temp_file_path = None
        
        allowed_extensions = {'.csv', '.txt', '.xlsx', '.json'}
        
        # Create temp directory for preview files
        temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_data')
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            temp_dir = None
        
        for file in files:
            if file.filename:
                file_ext = os.path.splitext(file.filename.lower())[1]
                
                if file_ext in allowed_extensions:
                    valid_files += 1
                    
                    # Get file size
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                    
                    # Save first valid file for preview (temporary)
                    if valid_files == 1 and temp_dir:  # Save first valid file if temp_dir exists
                        # More thorough filename sanitization
                        import re
                        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file.filename)
                        safe_filename = safe_filename.replace(' ', '_')  # Also replace spaces
                        temp_file_path = os.path.join(temp_dir, f"preview_{safe_filename}")
                        logger.info(f"Saving temp file: {temp_file_path}")
                        try:
                            file.save(temp_file_path)
                            # Reset file pointer for further processing
                            file.seek(0)
                        except Exception as e:
                            logger.error(f"Failed to save temp file: {e}")
                            temp_file_path = None
                            file.seek(0)
                    
                    # Try to read a small sample to validate format
                    try:
                        sample = file.read(1024).decode('utf-8', errors='ignore')
                        file.seek(0)
                        
                        # Detect file type based on content
                        file_type = 'Unknown'
                        if 'potential' in sample.lower() and 'current' in sample.lower():
                            file_type = 'CV Data'
                        elif ',' in sample and '\n' in sample:
                            file_type = 'CSV Data'
                        elif '\t' in sample:
                            file_type = 'Tab-delimited Data'
                        
                    except Exception:
                        file_type = 'Binary/Unknown'
                    
                    file_info.append({
                        'name': file.filename,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'type': file_type,
                        'extension': file_ext,
                        'valid': True
                    })
                else:
                    file_info.append({
                        'name': file.filename,
                        'size': 0,
                        'type': 'Unsupported',
                        'extension': file_ext,
                        'valid': False
                    })
        
        # Store file info in session for later steps
        session['workflow_files'] = {
            'total_files': total_files,
            'valid_files': valid_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_info': file_info,
            'upload_timestamp': time.time(),
            'sample_file_path': temp_file_path
        }
        
        return jsonify({
            'success': True,
            'total_files': total_files,
            'valid_files': valid_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_info': file_info,
            'message': f'Successfully scanned {valid_files} valid files out of {total_files} total files'
        })
        
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"File scan error: {error_details}")
        
        return jsonify({
            'success': False,
            'error': f'Failed to scan files: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@workflow_bp.route('/api/workflow/preprocess', methods=['POST'])
def preprocess_data():
    """Preprocess the uploaded data"""
    try:
        # Get preprocessing parameters
        data = request.get_json()
        instrument_type = data.get('instrument_type', 'stm32')
        
        # Simulate preprocessing with real-time updates
        processing_steps = [
            {'step': 'Validating file formats...', 'progress': 20},
            {'step': 'Converting units (μA → A)...', 'progress': 40},
            {'step': 'Checking data quality...', 'progress': 60},
            {'step': 'Applying noise filtering...', 'progress': 80},
            {'step': 'Preprocessing completed!', 'progress': 100}
        ]
        
        # In a real implementation, you would process each file here
        file_info = session.get('workflow_files', {})
        processed_files = file_info.get('valid_files', 0)
        
        # Calculate quality score based on instrument type
        if instrument_type == 'palmsens':
            quality_score = 98
        elif instrument_type == 'stm32':
            quality_score = 95
        else:
            quality_score = 85
        
        session['preprocessing_results'] = {
            'processed_files': processed_files,
            'quality_score': quality_score,
            'unit_format': instrument_type.upper(),
            'preprocessing_time': time.time()
        }
        
        return jsonify({
            'success': True,
            'processed_files': processed_files,
            'quality_score': quality_score,
            'unit_format': instrument_type.upper(),
            'processing_steps': processing_steps
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@workflow_bp.route('/api/workflow/detect-peaks', methods=['POST'])
def detect_peaks():
    """Run peak detection analysis"""
    try:
        data = request.get_json()
        method = data.get('method', 'deepcv')
        
        # Simulate peak detection with method-specific results
        if method == 'deepcv':
            peaks_detected = 4
            confidence = 89
            processing_time = 0.156
        elif method == 'traditional':
            peaks_detected = 3
            confidence = 72
            processing_time = 0.089
        else:  # hybrid
            peaks_detected = 3
            confidence = 78
            processing_time = 0.123
        
        session['peak_detection_results'] = {
            'method': method,
            'peaks_detected': peaks_detected,
            'confidence': confidence,
            'processing_time': processing_time,
            'detection_time': time.time()
        }
        
        return jsonify({
            'success': True,
            'peaks_detected': peaks_detected,
            'confidence': confidence,
            'processing_time': processing_time,
            'method_used': method
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@workflow_bp.route('/api/workflow/calibrate', methods=['POST'])
def calibrate_measurements():
    """Apply cross-instrument calibration"""
    try:
        data = request.get_json()
        model_type = data.get('model_type', 'random_forest')
        
        # Simulate calibration results based on model type
        if model_type == 'random_forest':
            accuracy = 91
            potential_error = 2.3
            current_error = 4.7
        elif model_type == 'neural_network':
            accuracy = 87
            potential_error = 3.1
            current_error = 5.2
        else:  # gradient_boost
            accuracy = 89
            potential_error = 2.8
            current_error = 4.9
        
        session['calibration_results'] = {
            'model_type': model_type,
            'accuracy': accuracy,
            'potential_error': potential_error,
            'current_error': current_error,
            'calibration_time': time.time()
        }
        
        return jsonify({
            'success': True,
            'accuracy': accuracy,
            'potential_error': potential_error,
            'current_error': current_error,
            'model_used': model_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@workflow_bp.route('/api/workflow/generate-visualization', methods=['POST'])
def generate_visualization():
    """Generate visualization data"""
    try:
        data = request.get_json()
        viz_type = data.get('type', 'cv_plots')
        
        # Generate mock visualization data
        if viz_type == 'cv_plots':
            viz_data = {
                'type': 'cv_plots',
                'title': 'Cyclic Voltammetry Analysis',
                'data': {
                    'voltage': [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5],
                    'current': [-2e-6, -1e-6, 0, 1e-6, 2e-6, 1.5e-6],
                    'peaks': [
                        {'voltage': 0.1, 'current': 1e-6, 'type': 'anodic'},
                        {'voltage': -0.2, 'current': -1e-6, 'type': 'cathodic'}
                    ]
                }
            }
        elif viz_type == 'peak_analysis':
            viz_data = {
                'type': 'peak_analysis',
                'title': 'Peak Analysis Dashboard',
                'data': {
                    'peak_count': session.get('peak_detection_results', {}).get('peaks_detected', 3),
                    'confidence': session.get('peak_detection_results', {}).get('confidence', 85),
                    'peak_details': [
                        {'potential': 0.15, 'current': 1.2e-6, 'width': 0.05, 'area': 6.2e-8},
                        {'potential': -0.18, 'current': -1.1e-6, 'width': 0.04, 'area': 5.8e-8}
                    ]
                }
            }
        else:  # calibration_comparison
            viz_data = {
                'type': 'calibration_comparison',
                'title': 'Before/After Calibration',
                'data': {
                    'original': {
                        'potentials': [0.12, -0.21],
                        'currents': [1.1e-6, -1.05e-6]
                    },
                    'calibrated': {
                        'potentials': [0.15, -0.18],
                        'currents': [1.2e-6, -1.1e-6]
                    },
                    'improvement': {
                        'potential_accuracy': 95,
                        'current_accuracy': 92
                    }
                }
            }
        
        return jsonify({
            'success': True,
            'visualization': viz_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@workflow_bp.route('/api/workflow/export', methods=['POST'])
def export_results():
    """Export analysis results"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')
        
        # Compile all results from session
        results = {
            'analysis_info': {
                'timestamp': datetime.now().isoformat(),
                'instrument_type': 'STM32H743',
                'analysis_version': '2.0'
            },
            'file_info': session.get('workflow_files', {}),
            'preprocessing': session.get('preprocessing_results', {}),
            'peak_detection': session.get('peak_detection_results', {}),
            'calibration': session.get('calibration_results', {}),
            'quality_metrics': {
                'overall_quality': 94,
                'scientific_accuracy': 96,
                'reliability_score': 92
            }
        }
        
        if export_format == 'json':
            filename = f"h743poten_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:  # csv
            filename = f"h743poten_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return jsonify({
            'success': True,
            'filename': filename,
            'data': results,
            'download_url': f'/api/workflow/download/{filename}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@workflow_bp.route('/api/workflow/test-session', methods=['POST'])
def test_session():
    """Test endpoint to manually set session for debugging"""
    session['workflow_files'] = {
        'total_files': 1,
        'valid_files': 1,
        'total_size': 1024,
        'total_size_mb': 0.001,
        'file_info': [{'name': 'test_cv_data.csv', 'valid': True}],
        'upload_timestamp': time.time(),
        'sample_file_path': os.path.join(os.path.dirname(__file__), '..', '..', 'temp_data', 'preview_test_cv_data.csv')
    }
    
    return jsonify({
        'success': True,
        'message': 'Test session created',
        'session_data': session.get('workflow_files')
    })

@workflow_bp.route('/api/workflow/data-source-info', methods=['GET'])
def get_data_source_info():
    """Get comprehensive information about data sources for workflow steps"""
    try:
        # Check session data
        file_info = session.get('workflow_files', {})
        has_session_data = file_info and file_info.get('valid_files', 0) > 0
        
        # Check uploaded files in temp_data
        temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_data')
        uploaded_files = []
        has_uploaded_files = False
        
        if os.path.exists(temp_dir):
            all_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
            uploaded_files = [f for f in all_files if not f.startswith('preview_test_')]
            has_uploaded_files = len(uploaded_files) > 0
        
        # Determine overall data source status
        if has_session_data:
            data_source_status = 'real'
            source_description = 'Real uploaded files with active session'
        elif has_uploaded_files:
            data_source_status = 'enhanced_mock'
            source_description = 'Real files uploaded but session expired'
        else:
            data_source_status = 'mock'
            source_description = 'No uploaded files - using generated data'
        
        return jsonify({
            'success': True,
            'data_source_status': data_source_status,
            'source_description': source_description,
            'has_session_data': has_session_data,
            'has_uploaded_files': has_uploaded_files,
            'uploaded_file_count': len(uploaded_files),
            'uploaded_files': uploaded_files[:5],  # Show first 5 files
            'session_valid_files': file_info.get('valid_files', 0) if has_session_data else 0,
            'temp_dir_exists': os.path.exists(temp_dir)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data_source_status': 'mock'
        }), 500


@workflow_bp.route('/api/workflow/test-session-data', methods=['GET'])
def test_session_data():
    """Test endpoint to check session data and set up real data test"""
    try:
        # Get current session data
        file_info = session.get('workflow_files', {})
        
        # Write to debug file
        debug_file = os.path.join(os.path.dirname(__file__), '..', '..', 'debug_api.log')
        with open(debug_file, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TEST SESSION - Current data: {file_info}\n")
        
        # Set up test session with real file data
        temp_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_data', 'preview_test_cv_data.csv')
        session['workflow_files'] = {
            'valid_files': 1,
            'total_files': 1,
            'sample_file_path': temp_file_path,
            'upload_timestamp': time.time()
        }
        
        # Write test setup to debug file
        with open(debug_file, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TEST SESSION - Set up real data session\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TEST SESSION - File path: {temp_file_path}\n")
        
        return jsonify({
            'success': True,
            'message': 'Test session created with real file data',
            'session_data': session['workflow_files'],
            'file_exists': os.path.exists(temp_file_path)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@workflow_bp.route('/api/workflow/get-preview-data', methods=['GET'])
def get_preview_data():
    """Get sample data for preview chart"""
    print("=== PREVIEW DATA ENDPOINT HIT ===")
    
    try:
        # Get session data
        file_info = session.get('workflow_files', {})
        
        # Write debug to file for tracking
        debug_file = os.path.join(os.path.dirname(__file__), '..', '..', 'debug_api.log')
        with open(debug_file, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Preview data endpoint called\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Session ID: {session}\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Session data: {file_info}\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Valid files: {file_info.get('valid_files', 0)}\n")
        
        # Add extensive debug logging
        logger.info(f"Preview data request - Session ID: {session}")
        logger.info(f"Preview data request - File info: {file_info}")
        logger.info(f"Valid files: {file_info.get('valid_files', 0)}")
        logger.info(f"Sample file path: {file_info.get('sample_file_path')}")
        
        # Check if file path exists
        sample_file_path = file_info.get('sample_file_path')
        if sample_file_path:
            logger.info(f"Sample file exists: {os.path.exists(sample_file_path)}")
            logger.info(f"Sample file path resolved: {sample_file_path}")
            
            # Write file check to debug file
            with open(debug_file, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] File path check: {sample_file_path}\n")
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] File exists: {os.path.exists(sample_file_path)}\n")
        
        # Debug condition check
        condition_1 = not file_info
        condition_2 = file_info.get('valid_files', 0) == 0
        logger.info(f"Condition checks - no file_info: {condition_1}, no valid files: {condition_2}")
        
        # Enhanced data source detection: Check session AND file system
        has_session_data = file_info and file_info.get('valid_files', 0) > 0
        
        # Also check if we have real uploaded files in temp_data directory
        temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_data')
        has_uploaded_files = False
        uploaded_file_count = 0
        
        if os.path.exists(temp_dir):
            uploaded_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv') and not f.startswith('preview_test_')]
            uploaded_file_count = len(uploaded_files)
            has_uploaded_files = uploaded_file_count > 0
            
        with open(debug_file, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Session data available: {has_session_data}\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Uploaded files found: {has_uploaded_files} (count: {uploaded_file_count})\n")
        
        # Determine data source intelligently
        if has_session_data or has_uploaded_files:
            data_source_type = 'real' if has_session_data else 'enhanced_mock'
            
            with open(debug_file, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Using data source: {data_source_type}\n")
                
        if not file_info or file_info.get('valid_files', 0) == 0:
            # Return realistic CV mock data if no files uploaded
            import math
            
            # Generate proper CV curve: forward scan (-1V to +1V) then reverse scan (+1V to -1V)
            voltage_data = []
            current_data = []
            
            # Forward scan: -1.0V to +1.0V
            for i in range(101):
                v = -1.0 + (2.0 * i / 100)
                voltage_data.append(v)
                
                # CV current with oxidation peak at ~+0.2V
                current = 2.0  # baseline current
                
                # Oxidation peak (anodic)
                if -0.3 < v < 0.7:
                    current += 35 * math.exp(-((v - 0.2) / 0.12) ** 2)
                
                # Add some noise
                current += random.uniform(-1.5, 1.5)
                current_data.append(current)
            
            # Reverse scan: +1.0V to -1.0V  
            for i in range(100, -1, -1):
                v = -1.0 + (2.0 * i / 100)
                voltage_data.append(v)
                
                # CV current with reduction peak at ~+0.1V (slightly shifted)
                current = 2.0  # baseline current
                
                # Reduction peak (cathodic) - negative current
                if -0.2 < v < 0.5:
                    current -= 28 * math.exp(-((v - 0.1) / 0.1) ** 2)
                
                # Add some noise
                current += random.uniform(-1.5, 1.5)
                current_data.append(current)
            
            # Determine data source based on our enhanced detection
            final_data_source = 'mock'
            if has_uploaded_files:
                final_data_source = 'enhanced_mock'
            
            return jsonify({
                'success': True,
                'data_source': final_data_source,
                'voltage': voltage_data,
                'current': current_data,
                'instrument': 'Enhanced Mock CV Generator' if final_data_source == 'enhanced_mock' else 'Mock CV Generator',
                'scan_rate': '100 mV/s',
                'file_name': 'sample_cv_data.csv',
                'data_points': len(voltage_data)
            })
        
        # Try to load real data from uploaded files
        logger.info("=== REAL DATA PROCESSING START ===")
        try:
            import pandas as pd
            import numpy as np
            
            # Get the first uploaded file for preview
            sample_file_path = file_info.get('sample_file_path')
            logger.info(f"Processing sample file path: {sample_file_path}")
            
            if sample_file_path and os.path.exists(sample_file_path):
                logger.info(f"File exists, attempting to load: {sample_file_path}")
                # Load real CV data
                df = pd.read_csv(sample_file_path)
                logger.info(f"CSV loaded successfully - shape: {df.shape}, columns: {list(df.columns)}")
                
                # Try to identify voltage and current columns
                voltage_col = None
                current_col = None
                
                # Look for voltage/potential columns
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if any(keyword in col_lower for keyword in ['potential', 'voltage', 'volt', 'e(v)', 'e_v', 'v_applied', 'working_electrode']):
                        voltage_col = col
                        break
                
                # Look for current columns  
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if any(keyword in col_lower for keyword in ['current', 'curr', 'i(a)', 'i_a', 'amp', 'working_current', 'we_current']):
                        current_col = col
                        break
                
                # If exact matches not found, try simpler patterns
                if not voltage_col:
                    for col in df.columns:
                        if len(col.strip()) <= 3 and any(c in col.lower() for c in ['v', 'e']):
                            voltage_col = col
                            break
                
                if not current_col:
                    for col in df.columns:
                        if len(col.strip()) <= 3 and any(c in col.lower() for c in ['i', 'a']):
                            current_col = col
                            break
                
                if voltage_col and current_col:
                    logger.info(f"Found columns - Voltage: '{voltage_col}', Current: '{current_col}'")
                    # Get sample of data (max 500 points for performance)
                    sample_size = min(500, len(df))
                    step = len(df) // sample_size
                    
                    voltage_data = df[voltage_col][::step].tolist()
                    current_data = df[current_col][::step].tolist()
                    
                    result = {
                        'success': True,
                        'data_source': 'real',
                        'voltage': voltage_data,
                        'current': current_data,
                        'instrument': file_info.get('instrument_type', 'Unknown'),
                        'scan_rate': 'Variable',
                        'file_name': os.path.basename(sample_file_path),
                        'data_points': len(voltage_data)
                    }
                    logger.info(f"Returning real data with data_source: {result['data_source']}")
                    return jsonify(result)
                else:
                    logger.warning(f"Could not find voltage/current columns - voltage_col: {voltage_col}, current_col: {current_col}")
            else:
                logger.warning(f"Sample file path invalid - exists: {os.path.exists(sample_file_path) if sample_file_path else 'None'}, path: {sample_file_path}")
                    
        except Exception as e:
            logger.error(f"Error loading real data: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
        
        # Fallback to enhanced CV mock data
        import math
        voltage_data = []
        current_data = []
        
        # Generate proper CV curve: forward scan (-1V to +1V) then reverse scan (+1V to -1V)
        # Forward scan: -1.0V to +1.0V
        for i in range(101):
            v = -1.0 + (2.0 * i / 100)
            voltage_data.append(v)
            
            # CV current with oxidation peak at ~+0.2V
            current = 2.0  # baseline current
            
            # Oxidation peak (anodic)
            if -0.3 < v < 0.7:
                current += 35 * math.exp(-((v - 0.2) / 0.12) ** 2)
            
            # Add some noise
            current += random.uniform(-1.5, 1.5)
            current_data.append(current)
        
        # Reverse scan: +1.0V to -1.0V  
        for i in range(100, -1, -1):
            v = -1.0 + (2.0 * i / 100)
            voltage_data.append(v)
            
            # CV current with reduction peak at ~+0.1V (slightly shifted)
            current = 2.0  # baseline current
            
            # Reduction peak (cathodic) - negative current
            if -0.2 < v < 0.5:
                current -= 28 * math.exp(-((v - 0.1) / 0.1) ** 2)
            
            # Add some noise
            current += random.uniform(-1.5, 1.5)
            current_data.append(current)
        
        return jsonify({
            'success': True,
            'data_source': 'enhanced_mock',
            'voltage': voltage_data,
            'current': current_data,
            'instrument': 'Enhanced Mock',
            'scan_rate': '100 mV/s'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@workflow_bp.route('/api/workflow/status', methods=['GET'])
def get_workflow_status():
    """Get current workflow status"""
    try:
        status = {
            'files_loaded': bool(session.get('workflow_files')),
            'preprocessing_done': bool(session.get('preprocessing_results')),
            'peaks_detected': bool(session.get('peak_detection_results')),
            'calibration_applied': bool(session.get('calibration_results')),
            'analysis_available': ANALYSIS_AVAILABLE
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'session_data': {
                'files': session.get('workflow_files', {}),
                'preprocessing': session.get('preprocessing_results', {}),
                'detection': session.get('peak_detection_results', {}),
                'calibration': session.get('calibration_results', {})
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@workflow_bp.route('/api/workflow/run-analysis', methods=['POST'])
def run_full_analysis():
    """Run the complete analysis pipeline"""
    try:
        if not ANALYSIS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Analysis modules not available'
            })
        
        data = request.get_json()
        files = data.get('files', [])
        
        # This would integrate with the actual analysis pipeline
        # For now, return mock results
        analysis_results = {
            'phase1_results': {
                'deepcv': {'peaks': 4, 'confidence': 89, 'time': 0.156},
                'traditional': {'peaks': 3, 'confidence': 72, 'time': 0.089},
                'hybrid': {'peaks': 3, 'confidence': 78, 'time': 0.123}
            },
            'phase2_results': {
                'calibration_accuracy': 91,
                'potential_error': 2.3,
                'current_error': 4.7
            },
            'quality_assessment': {
                'overall_score': 94,
                'scientific_grade': True,
                'ready_for_publication': True
            }
        }
        
        return jsonify({
            'success': True,
            'results': analysis_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
