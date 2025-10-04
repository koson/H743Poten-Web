#!/usr/bin/env python3
"""
🚀 Train DeepCV V2 with Enhanced Detector V5 as Teacher
======================================================

Training DeepCV V2 using Enhanced Detector V5 as teacher to generate
high-quality ground truth labels for peak detection.

Following the workflow diagram:
TraditionalCV Enhanced V5 → DeepCV V2 (train by V5) → HybridCV Enhanced

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
sys.path.append('.')

import numpy as np
import pandas as pd
import glob
import time
import pickle
from pathlib import Path

def load_cv_data(csv_file: str):
    """Load CV data from CSV file"""
    try:
        df = pd.read_csv(csv_file, skiprows=1)
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        return voltage, current
    except Exception as e:
        print(f"❌ Error loading {csv_file}: {e}")
        return None, None

class SimpleDeepCVV2:
    """Simple DeepCV V2 implementation using scikit-learn trained by V5"""
    
    def __init__(self):
        # Import sklearn components
        try:
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.neural_network import MLPRegressor
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_squared_error, r2_score
            
            # Store imports for later use
            self.train_test_split = train_test_split
            self.mean_squared_error = mean_squared_error
            self.r2_score = r2_score
            self.sklearn_available = True
        except ImportError:
            self.sklearn_available = False
            print("❌ scikit-learn not available!")
            return
        
        self.scaler = StandardScaler()
        self.peak_count_model = RandomForestRegressor(n_estimators=200, random_state=42)
        self.peak_position_model = GradientBoostingRegressor(n_estimators=200, random_state=42)
        self.confidence_model = MLPRegressor(
            hidden_layer_sizes=(100, 50, 25), 
            max_iter=1000, 
            random_state=42
        )
        
        self.is_trained = False
        self.training_history = []
        self.v5_teacher = None
        
    def set_teacher(self, v5_teacher):
        """Set Enhanced V5 as teacher"""
        self.v5_teacher = v5_teacher
        print("✅ Enhanced Detector V5 set as teacher")
        
    def extract_advanced_features(self, voltage, current):
        """Extract advanced features for DeepCV V2"""
        try:
            features = []
            
            # Basic statistical features
            features.extend([
                np.mean(current), np.std(current), 
                np.min(current), np.max(current),
                np.mean(voltage), np.std(voltage),
                len(current), np.ptp(current)  # peak-to-peak
            ])
            
            # Advanced electrochemical features
            # Current density and range analysis
            current_range = np.ptp(current)
            current_positive = current[current > 0]
            current_negative = current[current < 0]
            
            features.extend([
                len(current_positive) / len(current) if len(current) > 0 else 0,  # positive ratio
                len(current_negative) / len(current) if len(current) > 0 else 0,  # negative ratio
                np.mean(current_positive) if len(current_positive) > 0 else 0,
                np.mean(current_negative) if len(current_negative) > 0 else 0,
                current_range
            ])
            
            # Derivative features
            dcurrent_dv = np.gradient(current, voltage)
            features.extend([
                np.mean(dcurrent_dv), np.std(dcurrent_dv),
                np.max(dcurrent_dv), np.min(dcurrent_dv),
                np.sum(dcurrent_dv > 0), np.sum(dcurrent_dv < 0)
            ])
            
            # Second derivative (curvature)
            d2current_dv2 = np.gradient(dcurrent_dv, voltage)
            features.extend([
                np.mean(d2current_dv2), np.std(d2current_dv2),
                np.max(d2current_dv2), np.min(d2current_dv2)
            ])
            
            # Frequency domain features
            fft_current = np.fft.fft(current)
            fft_power = np.abs(fft_current[:len(fft_current)//2])
            features.extend([
                np.mean(fft_power), np.std(fft_power),
                np.argmax(fft_power),  # Dominant frequency
                np.sum(fft_power[:5]),  # Low frequency power
                np.sum(fft_power[-5:]) if len(fft_power) > 5 else 0  # High frequency power
            ])
            
            # Peak-related features (simple detection)
            from scipy.signal import find_peaks
            try:
                peaks_pos, _ = find_peaks(current, height=np.std(current))
                peaks_neg, _ = find_peaks(-current, height=np.std(current))
                
                features.extend([
                    len(peaks_pos), len(peaks_neg),
                    np.mean(current[peaks_pos]) if len(peaks_pos) > 0 else 0,
                    np.mean(current[peaks_neg]) if len(peaks_neg) > 0 else 0
                ])
            except:
                features.extend([0, 0, 0, 0])
            
            # Voltage window analysis
            v_min, v_max = np.min(voltage), np.max(voltage)
            v_windows = 5
            window_size = (v_max - v_min) / v_windows
            
            for i in range(v_windows):
                v_start = v_min + i * window_size
                v_end = v_min + (i + 1) * window_size
                window_mask = (voltage >= v_start) & (voltage < v_end)
                window_current = current[window_mask]
                
                if len(window_current) > 0:
                    features.extend([
                        np.mean(window_current),
                        np.std(window_current),
                        np.max(window_current) - np.min(window_current)
                    ])
                else:
                    features.extend([0, 0, 0])
            
            # Clean features (remove NaN and inf)
            features = np.array(features)
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
            
            return features
            
        except Exception as e:
            print(f"⚠️  Feature extraction error: {e}")
            return np.zeros(50)  # Return default size
    
    def generate_labels_with_v5(self, voltage, current, filename):
        """Generate ground truth labels using V5 teacher"""
        if self.v5_teacher is None:
            print("❌ V5 teacher not set!")
            return 0, 0.0, []
        
        try:
            # Get V5 analysis
            result = self.v5_teacher.detect_peaks_enhanced_v5(voltage, current)
            
            # Extract information
            peaks_list = result.get('peaks', [])
            peak_count = len(peaks_list)
            
            # Calculate confidence
            if peaks_list:
                confidences = [p.get('confidence', 0.0) for p in peaks_list if 'confidence' in p]
                avg_confidence = np.mean(confidences) if confidences else 0.0
            else:
                avg_confidence = 0.0
            
            # Extract peak positions for position learning
            peak_positions = []
            for peak in peaks_list:
                peak_positions.append({
                    'voltage': peak.get('voltage', 0.0),
                    'current': peak.get('current', 0.0),
                    'type': peak.get('type', 'unknown'),
                    'confidence': peak.get('confidence', 0.0)
                })
            
            return peak_count, avg_confidence, peak_positions
            
        except Exception as e:
            print(f"⚠️  V5 labeling error for {filename}: {e}")
            return 0, 0.0, []
    
    def train_with_v5_teacher(self, training_files, max_files=50):
        """Train DeepCV V2 using V5 as teacher"""
        if not self.sklearn_available:
            print("❌ scikit-learn not available - cannot train!")
            return False
        
        if self.v5_teacher is None:
            print("❌ V5 teacher not set!")
            return False
        
        print(f"🏫 Training DeepCV V2 with Enhanced V5 as teacher...")
        print(f"🎯 Processing up to {max_files} files")
        
        # Collect training data
        X_features = []
        y_peak_counts = []
        y_confidences = []
        successful_samples = 0
        
        training_files = training_files[:max_files]
        
        for i, csv_file in enumerate(training_files):
            filename = os.path.basename(csv_file)
            print(f"   📄 {i+1:2d}/{len(training_files)}: {filename[:40]:40s}", end=" ")
            
            # Load data
            voltage, current = load_cv_data(csv_file)
            if voltage is None:
                print("❌ Load failed")
                continue
            
            # Generate labels with V5 teacher
            peak_count, confidence, peak_positions = self.generate_labels_with_v5(
                voltage, current, filename
            )
            
            if peak_count > 0 and confidence > 30.0:  # Only use high-confidence samples
                # Extract advanced features
                features = self.extract_advanced_features(voltage, current)
                
                X_features.append(features)
                y_peak_counts.append(peak_count)
                y_confidences.append(confidence)
                successful_samples += 1
                
                print(f"✅ {peak_count} peaks ({confidence:.1f}% conf)")
            else:
                print(f"⚠️  Low confidence ({confidence:.1f}%)")
        
        if successful_samples < 10:
            print("❌ Insufficient high-quality training data!")
            return False
        
        print(f"\n📊 Training data collected:")
        print(f"   🎯 Successful samples: {successful_samples}/{len(training_files)}")
        print(f"   📈 Peak count distribution: {np.bincount(y_peak_counts)}")
        print(f"   📊 Average confidence: {np.mean(y_confidences):.1f}%")
        
        # Convert to arrays and clean
        X_features = np.array(X_features)
        y_peak_counts = np.array(y_peak_counts)
        y_confidences = np.array(y_confidences)
        
        # Clean any remaining NaN/inf values
        X_features = np.nan_to_num(X_features, nan=0.0, posinf=0.0, neginf=0.0)
        y_peak_counts = np.nan_to_num(y_peak_counts, nan=0.0, posinf=0.0, neginf=0.0)
        y_confidences = np.nan_to_num(y_confidences, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Scale features
        print("\n🔧 Training models...")
        X_scaled = self.scaler.fit_transform(X_features)
        
        # Split data
        X_train, X_test, y_count_train, y_count_test, y_conf_train, y_conf_test = self.train_test_split(
            X_scaled, y_peak_counts, y_confidences, test_size=0.2, random_state=42
        )
        
        # Train peak count model
        print("   🎯 Training peak count predictor...")
        self.peak_count_model.fit(X_train, y_count_train)
        
        # Train confidence model
        print("   📊 Training confidence predictor...")
        self.confidence_model.fit(X_train, y_conf_train)
        
        # Evaluate models
        y_count_pred = self.peak_count_model.predict(X_test)
        y_conf_pred = self.confidence_model.predict(X_test)
        
        count_mse = self.mean_squared_error(y_count_test, y_count_pred)
        count_r2 = self.r2_score(y_count_test, y_count_pred)
        
        conf_mse = self.mean_squared_error(y_conf_test, y_conf_pred)
        conf_r2 = self.r2_score(y_conf_test, y_conf_pred)
        
        print(f"   📊 Peak count model - MSE: {count_mse:.3f}, R²: {count_r2:.3f}")
        print(f"   📊 Confidence model - MSE: {conf_mse:.3f}, R²: {conf_r2:.3f}")
        
        self.is_trained = True
        self.training_history.append({
            'count_mse': count_mse, 'count_r2': count_r2,
            'conf_mse': conf_mse, 'conf_r2': conf_r2,
            'samples': successful_samples,
            'teacher': 'Enhanced_V5'
        })
        
        return True
    
    def predict_peaks(self, voltage, current):
        """Predict peaks using trained DeepCV V2"""
        if not self.is_trained:
            return {'peaks_detected': 0, 'confidence': 0.0, 'method': 'DeepCV_V2_Untrained'}
        
        try:
            features = self.extract_advanced_features(voltage, current).reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            peak_count = self.peak_count_model.predict(features_scaled)[0]
            confidence = self.confidence_model.predict(features_scaled)[0]
            
            peak_count = max(0, round(peak_count))
            confidence = max(0.0, min(100.0, confidence))
            
            return {
                'peaks_detected': int(peak_count),
                'confidence': float(confidence),
                'method': 'DeepCV_V2_Enhanced',
                'teacher': 'Enhanced_V5'
            }
            
        except Exception as e:
            print(f"⚠️  DeepCV V2 prediction error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0, 'method': 'DeepCV_V2_Error'}
    
    def save_model(self, path):
        """Save trained DeepCV V2 model"""
        try:
            model_data = {
                'scaler': self.scaler,
                'peak_count_model': self.peak_count_model,
                'confidence_model': self.confidence_model,
                'is_trained': self.is_trained,
                'training_history': self.training_history,
                'version': 'DeepCV_V2_Enhanced_by_V5',
                'teacher': 'Enhanced_Detector_V5'
            }
            
            with open(path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"💾 DeepCV V2 model saved to: {path}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False

def main():
    """Main training function"""
    print("🚀 DEEPCV V2 TRAINING WITH ENHANCED V5 TEACHER")
    print("=" * 70)
    
    # Initialize Enhanced V5 teacher
    print("🏫 Initializing Enhanced Detector V5 as teacher...")
    try:
        from enhanced_detector_v5 import EnhancedDetectorV5
        v5_teacher = EnhancedDetectorV5()
        print("✅ Enhanced Detector V5 teacher ready")
    except ImportError as e:
        print(f"❌ Failed to import V5 teacher: {e}")
        return False
    
    # Initialize DeepCV V2 student
    print("🧠 Initializing DeepCV V2 student...")
    deepcv_v2 = SimpleDeepCVV2()
    if not deepcv_v2.sklearn_available:
        print("❌ DeepCV V2 initialization failed!")
        return False
    
    deepcv_v2.set_teacher(v5_teacher)
    
    # Find training data
    data_dirs = [
        '../Test_Data_CV/palmsense/palmsense-cv-0.5mM',
        '../Test_Data_CV/palmsense/palmsense-cv-1.0mM', 
        '../Test_Data_CV/palmsense/palmsense-cv-5.0mM'
    ]
    
    print(f"🔍 Collecting training data...")
    all_files = []
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
            all_files.extend(csv_files)
            print(f"   📁 {data_dir}: {len(csv_files)} files")
    
    if not all_files:
        print("❌ No training data found!")
        return False
    
    print(f"📊 Total files available: {len(all_files)}")
    
    # Train DeepCV V2
    print("\n🚀 Starting DeepCV V2 training...")
    print("-" * 70)
    
    start_time = time.time()
    success = deepcv_v2.train_with_v5_teacher(all_files, max_files=40)
    training_time = time.time() - start_time
    
    if success:
        print(f"\n✅ DeepCV V2 training completed in {training_time:.1f} seconds")
        
        # Save model
        model_path = "deepcv_v2_trained_by_v5.pkl"
        deepcv_v2.save_model(model_path)
        
        # Quick validation test
        print("\n🧪 Validation testing...")
        test_files = all_files[-10:]  # Use last 10 files for validation
        
        correct_predictions = 0
        total_tests = 0
        
        for csv_file in test_files:
            filename = os.path.basename(csv_file)
            voltage, current = load_cv_data(csv_file)
            
            if voltage is not None:
                # Get ground truth from V5 teacher
                gt_count, gt_confidence, _ = deepcv_v2.generate_labels_with_v5(
                    voltage, current, filename
                )
                
                # Get prediction from DeepCV V2
                pred_result = deepcv_v2.predict_peaks(voltage, current)
                pred_count = pred_result['peaks_detected']
                pred_confidence = pred_result['confidence']
                
                print(f"   📄 {filename[:35]:35s} GT:{gt_count} Pred:{pred_count} ({pred_confidence:.1f}%)", end="")
                
                if pred_count == gt_count:
                    correct_predictions += 1
                    print(" ✅")
                else:
                    print(" ❌")
                
                total_tests += 1
        
        if total_tests > 0:
            accuracy = correct_predictions / total_tests * 100
            print(f"   🎯 Validation accuracy: {accuracy:.1f}% ({correct_predictions}/{total_tests})")
        
        print("\n🎊 DEEPCV V2 TRAINING SUCCESS!")
        print(f"📁 Model saved: {model_path}")
        print("🚀 Ready for integration with HybridCV Enhanced!")
        
        # Next step recommendation
        print(f"\n📋 NEXT STEPS:")
        print("1. ✅ Enhanced Detector V5 - READY")
        print("2. ✅ DeepCV V2 trained by V5 - READY") 
        print("3. 🎯 Create HybridCV Enhanced (V5 + DeepCV V2)")
        
        return True
        
    else:
        print("❌ DeepCV V2 training failed!")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 TRAINING COMPLETE!' if success else '❌ TRAINING FAILED!'}")