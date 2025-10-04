#!/usr/bin/env python3
"""
🚀 DeepCV V2 Simple Training Script (No PyTorch Required)
========================================================

ใช้ scikit-learn แทน PyTorch สำหรับ training DeepCV V2
Compatible กับ environment ปัจจุบัน

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
sys.path.append('.')
sys.path.append('..')

import numpy as np
import pandas as pd
import glob
import time
import pickle
from pathlib import Path

# Scientific computing
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Import our frameworks
try:
    from peak_detection_framework import HybridCVAnalyzer
    print("✅ Successfully imported CV frameworks")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class SimpleDeepCV:
    """Simple DeepCV implementation using scikit-learn"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.peak_count_model = None
        self.peak_position_model = None
        self.is_trained = False
        self.training_history = []
        
        # Models
        if SKLEARN_AVAILABLE:
            self.peak_count_model = RandomForestRegressor(
                n_estimators=100, random_state=42
            )
            self.peak_position_model = GradientBoostingRegressor(
                n_estimators=100, random_state=42
            )
        
    def extract_features(self, voltage, current):
        """Extract features from CV data"""
        try:
            features = []
            
            # Basic statistics
            features.extend([
                np.mean(current), np.std(current), 
                np.min(current), np.max(current),
                np.mean(voltage), np.std(voltage),
                len(current)
            ])
            
            # Peak-related features
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(np.abs(current), height=np.std(current))
            features.extend([
                len(peaks),
                np.mean(np.abs(current[peaks])) if len(peaks) > 0 else 0,
                np.std(np.abs(current[peaks])) if len(peaks) > 0 else 0
            ])
            
            # Derivative features
            dcurrent_dv = np.gradient(current, voltage)
            features.extend([
                np.mean(dcurrent_dv), np.std(dcurrent_dv),
                np.max(dcurrent_dv), np.min(dcurrent_dv)
            ])
            
            # Frequency domain features (simple)
            fft_current = np.fft.fft(current)
            fft_power = np.abs(fft_current[:len(fft_current)//2])
            features.extend([
                np.mean(fft_power), np.std(fft_power),
                np.argmax(fft_power)  # Dominant frequency
            ])
            
            return np.array(features)
            
        except Exception as e:
            print(f"⚠️  Feature extraction error: {e}")
            return np.zeros(16)  # Return zero vector if failed
    
    def train(self, X_features, y_peak_counts, y_peak_positions=None):
        """Train the models"""
        if not SKLEARN_AVAILABLE:
            print("❌ scikit-learn not available")
            return False
            
        try:
            print("🔧 Training peak count model...")
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X_features)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_peak_counts, test_size=0.2, random_state=42
            )
            
            # Train peak count model
            self.peak_count_model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.peak_count_model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"   📊 Peak count model - MSE: {mse:.3f}, R²: {r2:.3f}")
            
            self.is_trained = True
            self.training_history.append({
                'mse': mse, 'r2': r2, 'samples': len(X_features)
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Training error: {e}")
            return False
    
    def predict(self, voltage, current):
        """Predict peaks for CV data"""
        if not self.is_trained:
            return {'peaks_detected': 0, 'confidence': 0.0}
            
        try:
            features = self.extract_features(voltage, current).reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            peak_count = self.peak_count_model.predict(features_scaled)[0]
            peak_count = max(0, round(peak_count))  # Ensure non-negative integer
            
            # Simple confidence based on model certainty
            # For now, use a heuristic based on feature quality
            confidence = min(1.0, np.std(current) / (np.mean(np.abs(current)) + 1e-8))
            
            return {
                'peaks_detected': int(peak_count),
                'confidence': float(confidence),
                'peak_positions': []  # TODO: Implement position prediction
            }
            
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0}
    
    def save_model(self, path):
        """Save trained model"""
        try:
            model_data = {
                'scaler': self.scaler,
                'peak_count_model': self.peak_count_model,
                'peak_position_model': self.peak_position_model,
                'is_trained': self.is_trained,
                'training_history': self.training_history
            }
            
            with open(path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"💾 Model saved to: {path}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False
    
    def load_model(self, path):
        """Load trained model"""
        try:
            if not os.path.exists(path):
                return False
                
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.scaler = model_data['scaler']
            self.peak_count_model = model_data['peak_count_model']
            self.peak_position_model = model_data['peak_position_model']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data['training_history']
            
            print(f"📁 Model loaded from: {path}")
            return True
            
        except Exception as e:
            print(f"❌ Load error: {e}")
            return False

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

def generate_training_labels(voltage, current, filename, hybrid_analyzer):
    """Use HybridCV as teacher to generate ground truth labels"""
    try:
        result = hybrid_analyzer.detect_peaks(voltage, current, filename)
        peak_count = result.peaks_detected
        confidence = result.confidence_score
        
        return peak_count, confidence
    except Exception as e:
        print(f"⚠️  Error generating labels for {filename}: {e}")
        return 0, 0.0

def main():
    print("🧠 Simple DeepCV Training Pipeline")
    print("=" * 60)
    
    if not SKLEARN_AVAILABLE:
        print("❌ scikit-learn not available - cannot train model")
        return
    
    # Initialize analyzers
    print("🔧 Initializing analyzers...")
    
    # HybridCV as teacher
    hybrid_config = {
        'traditional_weight': 0.7,
        'deep_weight': 0.3,
        'consensus_threshold': 0.2,
        'max_peak_difference': 0.08
    }
    hybrid_teacher = HybridCVAnalyzer(hybrid_config)
    
    # Simple DeepCV as student
    simple_deepcv = SimpleDeepCV()
    
    # Find training data
    data_dirs = [
        '../Test_Data_CV/palmsense/palmsense-cv-0.5mM',
        '../Test_Data_CV/palmsense/palmsense-cv-1.0mM', 
        '../Test_Data_CV/palmsense/palmsense-cv-5.0mM'
    ]
    
    print(f"🔍 Searching for training data...")
    all_files = []
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
            all_files.extend(csv_files)
            print(f"   📁 {data_dir}: {len(csv_files)} files")
    
    if not all_files:
        print("❌ No training data found!")
        return
    
    print(f"📊 Total files found: {len(all_files)}")
    
    # Use all available files for training  
    training_files = all_files[:30]  # Limit to first 30 for speed
    print(f"🎯 Using {len(training_files)} files for training")
    print()
    
    # Collect training data
    print("🏫 Collecting training data with HybridCV teacher...")
    X_features = []
    y_peak_counts = []
    successful_samples = 0
    
    for i, csv_file in enumerate(training_files):
        filename = os.path.basename(csv_file)
        print(f"   📄 Processing {i+1:2d}/{len(training_files)}: {filename[:40]:40s}", end=" ")
        
        # Load data
        voltage, current = load_cv_data(csv_file)
        if voltage is None:
            print("❌ Load failed")
            continue
            
        # Generate labels with teacher
        peak_count, confidence = generate_training_labels(
            voltage, current, filename, hybrid_teacher
        )
        
        if confidence > 0.3:  # Only use high-confidence samples
            # Extract features
            features = simple_deepcv.extract_features(voltage, current)
            
            X_features.append(features)
            y_peak_counts.append(peak_count)
            successful_samples += 1
            
            print(f"✅ {peak_count} peaks (conf: {confidence:.2f})")
        else:
            print(f"⚠️  Low confidence ({confidence:.2f})")
    
    if successful_samples < 5:
        print("❌ Insufficient training data!")
        return
    
    print()
    print(f"📊 Training data summary:")
    print(f"   🎯 Successful samples: {successful_samples}/{len(training_files)}")
    print(f"   📈 Peak count distribution: {np.bincount(y_peak_counts)}")
    
    # Convert to arrays
    X_features = np.array(X_features)
    y_peak_counts = np.array(y_peak_counts)
    
    # Train model
    print()
    print("🚀 Training Simple DeepCV model...")
    print("-" * 60)
    
    start_time = time.time()
    success = simple_deepcv.train(X_features, y_peak_counts)
    training_time = time.time() - start_time
    
    if success:
        print(f"✅ Training completed in {training_time:.1f} seconds")
        
        # Save model
        model_path = "simple_deepcv_model.pkl"
        simple_deepcv.save_model(model_path)
        
        # Quick test
        print()
        print("🧪 Testing trained model...")
        test_files = training_files[-5:]  # Use last 5 files for test
        
        correct_predictions = 0
        total_tests = 0
        
        for csv_file in test_files:
            filename = os.path.basename(csv_file)
            voltage, current = load_cv_data(csv_file)
            
            if voltage is not None:
                # Get ground truth from teacher
                gt_count, gt_confidence = generate_training_labels(
                    voltage, current, filename, hybrid_teacher
                )
                
                # Get prediction from student
                pred_result = simple_deepcv.predict(voltage, current)
                pred_count = pred_result['peaks_detected']
                
                print(f"   📄 {filename[:35]:35s} GT:{gt_count} Pred:{pred_count}", end="")
                
                if pred_count == gt_count:
                    correct_predictions += 1
                    print(" ✅")
                else:
                    print(" ❌") 
                
                total_tests += 1
        
        if total_tests > 0:
            accuracy = correct_predictions / total_tests * 100
            print(f"   🎯 Test accuracy: {accuracy:.1f}% ({correct_predictions}/{total_tests})")
        
        print()
        print("🎊 Simple DeepCV Training Complete!")
        print(f"📁 Model saved to: {model_path}")
        print("🚀 Ready to use!")
        
    else:
        print("❌ Training failed!")

if __name__ == "__main__":
    main()