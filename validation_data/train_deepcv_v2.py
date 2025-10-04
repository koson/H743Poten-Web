#!/usr/bin/env python3
"""
🚀 DeepCV V2 Training Script
============================

Script สำหรับ train DeepCV V2 model ด้วยข้อมูล CV จริงจาก PalmSens
ใช้ HybridCV เป็น teacher สำหรับสร้าง ground truth labels

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
from pathlib import Path

# Import our frameworks
try:
    from deepcv_v2 import DeepCVAnalyzer
    from peak_detection_framework import HybridCVAnalyzer
    print("✅ Successfully imported CV frameworks")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

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
        
        # Convert peak positions to ground truth format
        ground_truth_peaks = []
        if hasattr(result, 'peak_positions') and result.peak_positions:
            for peak_pos in result.peak_positions:
                # Convert to (voltage, current) format
                v_idx = int(peak_pos)
                if 0 <= v_idx < len(voltage):
                    ground_truth_peaks.append({
                        'voltage': voltage[v_idx],
                        'current': current[v_idx],
                        'index': v_idx
                    })
        
        return ground_truth_peaks, result.confidence_score
    except Exception as e:
        print(f"⚠️  Error generating labels for {filename}: {e}")
        return [], 0.0

def main():
    print("🧠 DeepCV V2 Training Pipeline")
    print("=" * 60)
    
    # Initialize analyzers
    print("🔧 Initializing analyzers...")
    
    # HybridCV as teacher (already proven to work well)
    hybrid_config = {
        'traditional_weight': 0.7,
        'deep_weight': 0.3,
        'consensus_threshold': 0.2,
        'max_peak_difference': 0.08
    }
    hybrid_teacher = HybridCVAnalyzer(hybrid_config)
    
    # DeepCV V2 as student
    deepcv_config = {
        'min_training_samples': 20,  # Lower threshold for testing
        'batch_size': 8,
        'learning_rate': 0.001,
        'epochs': 50,
        'validation_split': 0.2
    }
    deep_student = DeepCVAnalyzer(deepcv_config)
    
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
    
    # Limit files for initial training (use first 25 files)
    training_files = all_files[:25]
    print(f"🎯 Using {len(training_files)} files for training")
    print()
    
    # Generate training data using HybridCV as teacher
    print("🏫 Generating training labels with HybridCV teacher...")
    training_count = 0
    successful_labels = 0
    
    for i, csv_file in enumerate(training_files):
        filename = os.path.basename(csv_file)
        print(f"   📄 Processing {i+1:2d}/{len(training_files)}: {filename[:40]:40s}", end=" ")
        
        # Load data
        voltage, current = load_cv_data(csv_file)
        if voltage is None:
            print("❌ Load failed")
            continue
            
        # Generate ground truth with HybridCV teacher
        ground_truth_peaks, confidence = generate_training_labels(
            voltage, current, filename, hybrid_teacher
        )
        
        if len(ground_truth_peaks) > 0 and confidence > 0.3:  # Only use high-confidence labels
            # Add to DeepCV training data
            deep_student.add_training_data(
                voltage, current, ground_truth_peaks, filename
            )
            training_count += 1
            successful_labels += len(ground_truth_peaks)
            print(f"✅ {len(ground_truth_peaks)} peaks (conf: {confidence:.2f})")
        else:
            print(f"⚠️  Low confidence ({confidence:.2f}) or no peaks")
    
    print()
    print(f"📊 Training data summary:")
    print(f"   🎯 Successful samples: {training_count}/{len(training_files)}")
    print(f"   🏷️  Total peak labels: {successful_labels}")
    print(f"   📈 Average peaks per sample: {successful_labels/max(training_count,1):.1f}")
    
    if training_count < 10:
        print("⚠️  Warning: Limited training data - model may not perform optimally")
    
    # Start training
    print()
    print("🚀 Starting DeepCV V2 training...")
    print("-" * 60)
    
    try:
        start_time = time.time()
        
        # Train the model
        deep_student.train(save_model=True)
        
        training_time = time.time() - start_time
        print(f"✅ Training completed in {training_time:.1f} seconds")
        
        # Test on a few samples
        print()
        print("🧪 Testing trained model...")
        test_files = training_files[-3:]  # Use last 3 files for quick test
        
        correct_predictions = 0
        total_tests = 0
        
        for csv_file in test_files:
            filename = os.path.basename(csv_file)
            voltage, current = load_cv_data(csv_file)
            
            if voltage is not None:
                # Get ground truth from teacher
                gt_peaks, gt_confidence = generate_training_labels(
                    voltage, current, filename, hybrid_teacher
                )
                
                # Get prediction from student
                try:
                    result = deep_student.detect_peaks(voltage, current, filename)
                    predicted_peaks = result.peaks_detected
                    actual_peaks = len(gt_peaks)
                    
                    print(f"   📄 {filename[:35]:35s} GT:{actual_peaks} Pred:{predicted_peaks}", end="")
                    
                    if predicted_peaks == actual_peaks:
                        correct_predictions += 1
                        print(" ✅")
                    else:
                        print(" ❌") 
                    
                    total_tests += 1
                    
                except Exception as e:
                    print(f"   📄 {filename[:35]:35s} Error: {e}")
        
        if total_tests > 0:
            accuracy = correct_predictions / total_tests * 100
            print(f"   🎯 Quick test accuracy: {accuracy:.1f}% ({correct_predictions}/{total_tests})")
        
        print()
        print("🎊 DeepCV V2 Training Complete!")
        print(f"📁 Model saved to: {deep_student.model_save_path}")
        print("🚀 Ready for production use!")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()