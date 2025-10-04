#!/usr/bin/env python3
"""
🧠 DeepCV V2.1 - AI Training from V6 Database
=============================================

Major improvements:
1. Load training data from V6 validation database
2. Advanced feature extraction from validated peaks
3. Ensemble learning with confidence estimation
4. Real-time training pipeline
5. Performance evaluation and model export

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from datetime import datetime
import json

sys.path.append('.')
sys.path.append('validation_data')

try:
    from enhanced_detector_v6_improved import ValidationDatabase
except ImportError:
    print("⚠️  V6 Improved not found")
    ValidationDatabase = None

class DeepCVV21:
    """DeepCV V2.1 - Train on human-validated data"""
    
    def __init__(self, db_path="validation_data/peak_validation.db"):
        self.db_path = db_path
        self.database = ValidationDatabase(db_path) if ValidationDatabase else None
        
        # Models
        self.peak_classifier = None
        self.confidence_regressor = None
        self.scaler = StandardScaler()
        
        # Training history
        self.training_history = []
        self.feature_names = []
        
        print("🧠 DeepCV V2.1 initialized")
        print("📊 Features: Database training, Ensemble learning, Confidence estimation")
    
    def load_training_data(self, min_confidence=0.8, dataset_name=None):
        """Load training data from validation database"""
        if not self.database:
            print("❌ Database not available")
            return None
        
        print(f"📚 Loading training data (min_confidence={min_confidence})...")
        
        # Get validated peaks
        training_data = self.database.get_training_data(dataset_name, min_confidence)
        
        if training_data.empty:
            print("⚠️  No training data available")
            return None
        
        print(f"📊 Loaded {len(training_data)} validated peaks from database")
        print(f"📈 Sessions: {training_data['session_id'].nunique()}")
        print(f"🧪 Compounds: {training_data['compound_name'].nunique()}")
        
        return training_data
    
    def extract_features(self, training_data):
        """Extract advanced features from validated peaks"""
        print("🔍 Extracting features from validated peaks...")
        
        features = []
        labels = []
        confidences = []
        
        for _, row in training_data.iterrows():
            # Basic peak properties
            voltage = row['voltage']
            current = row['current']
            peak_type = row['peak_type']
            is_valid = row['is_valid']
            confidence = row['confidence']
            
            # Feature vector
            feature_vector = [
                voltage,                           # Peak voltage
                current,                          # Peak current
                abs(current),                     # Peak magnitude
                voltage**2,                       # Voltage squared
                current**2,                       # Current squared
                voltage * current,                # Voltage-current interaction
                1 if peak_type == 'oxidation' else 0,  # Is oxidation
                1 if peak_type == 'reduction' else 0,  # Is reduction
            ]
            
            # Contextual features (if available)
            if 'concentration' in row and pd.notna(row['concentration']):
                try:
                    conc = float(row['concentration'].replace('mM', '').replace('M', '').strip())
                    feature_vector.extend([
                        conc,                     # Concentration
                        np.log10(conc + 1e-6),   # Log concentration
                        current / conc,          # Current density
                    ])
                except:
                    feature_vector.extend([1.0, 0.0, current])  # Default values
            else:
                feature_vector.extend([1.0, 0.0, current])
            
            # Statistical features
            feature_vector.extend([
                confidence,                       # Original V5 confidence
                1 if confidence > 0.8 else 0,   # High confidence flag
                np.exp(-abs(voltage)),           # Voltage decay
                np.tanh(current),                # Current saturation
            ])
            
            features.append(feature_vector)
            labels.append(1 if is_valid else 0)
            confidences.append(confidence)
        
        # Feature names for interpretability
        self.feature_names = [
            'voltage', 'current', 'magnitude', 'voltage_sq', 'current_sq', 'v_i_interaction',
            'is_oxidation', 'is_reduction', 'concentration', 'log_concentration', 'current_density',
            'v5_confidence', 'high_confidence', 'voltage_decay', 'current_saturation'
        ]
        
        X = np.array(features)
        y = np.array(labels)
        conf = np.array(confidences)
        
        print(f"✅ Extracted {X.shape[1]} features from {X.shape[0]} peaks")
        print(f"📊 Valid peaks: {np.sum(y)} / {len(y)} ({np.mean(y):.1%})")
        
        return X, y, conf
    
    def train_models(self, X, y, conf, test_size=0.2):
        """Train ensemble models"""
        print("🎓 Training DeepCV V2.1 models...")
        
        # Split data
        X_train, X_test, y_train, y_test, conf_train, conf_test = train_test_split(
            X, y, conf, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train peak validity classifier
        print("🔍 Training peak validity classifier...")
        self.peak_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.peak_classifier.fit(X_train_scaled, y_train)
        
        # Train confidence regressor
        print("📊 Training confidence regressor...")
        self.confidence_regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        # Use only valid peaks for confidence training
        valid_mask = y_train == 1
        if np.sum(valid_mask) > 0:
            self.confidence_regressor.fit(X_train_scaled[valid_mask], conf_train[valid_mask])
        
        # Evaluate models
        self._evaluate_models(X_test_scaled, y_test, conf_test)
        
        # Store training history
        training_record = {
            'timestamp': datetime.now().isoformat(),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': X.shape[1],
            'valid_ratio': np.mean(y),
            'test_accuracy': self.peak_classifier.score(X_test_scaled, y_test)
        }
        
        self.training_history.append(training_record)
        
        print("✅ DeepCV V2.1 training completed!")
        return training_record
    
    def _evaluate_models(self, X_test, y_test, conf_test):
        """Evaluate trained models"""
        print("\n📊 MODEL EVALUATION")
        print("-" * 50)
        
        # Classification performance
        y_pred = self.peak_classifier.predict(X_test)
        
        # Handle case where all samples are from one class
        unique_classes = self.peak_classifier.classes_
        if len(unique_classes) > 1:
            y_pred_proba = self.peak_classifier.predict_proba(X_test)[:, 1]
        else:
            y_pred_proba = np.ones(len(X_test)) * 0.5  # Default probability
        
        accuracy = np.mean(y_pred == y_test)
        print(f"🎯 Peak Classification Accuracy: {accuracy:.3f}")
        print(f"📊 Classes in model: {unique_classes}")
        
        # Cross-validation (if we have enough diverse data)
        if len(np.unique(y_test)) > 1 and len(X_test) >= 3:
            try:
                cv_scores = cross_val_score(self.peak_classifier, X_test, y_test, cv=min(3, len(X_test)))
                print(f"📊 Cross-validation Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            except Exception as e:
                print(f"⚠️  Cross-validation skipped: {e}")
        else:
            print("⚠️  Cross-validation skipped: insufficient data diversity")
        
        # Feature importance
        feature_importance = self.peak_classifier.feature_importances_
        important_features = sorted(zip(self.feature_names, feature_importance), 
                                  key=lambda x: x[1], reverse=True)[:5]
        
        print("\n🔍 Top 5 Important Features:")
        for name, importance in important_features:
            print(f"   {name}: {importance:.3f}")
        
        # Confidence regression (if applicable)
        if self.confidence_regressor and np.sum(y_test == 1) > 0:
            valid_test_mask = y_test == 1
            if np.sum(valid_test_mask) > 0:
                conf_pred = self.confidence_regressor.predict(X_test[valid_test_mask])
                conf_mae = np.mean(np.abs(conf_pred - conf_test[valid_test_mask]))
                print(f"📈 Confidence Prediction MAE: {conf_mae:.3f}")
    
    def predict_peaks(self, voltage, current, peak_candidates=None):
        """Predict peak validity and confidence"""
        if not self.peak_classifier:
            print("❌ Model not trained yet")
            return None
        
        if peak_candidates is None:
            # Simple peak detection fallback
            peak_candidates = self._simple_peak_detection(voltage, current)
        
        print(f"🔍 Analyzing {len(peak_candidates)} peak candidates...")
        
        predictions = []
        
        for i, candidate in enumerate(peak_candidates):
            # Extract features for this candidate
            features = self._extract_single_peak_features(candidate)
            features_scaled = self.scaler.transform([features])
            
            # Predict validity
            if len(self.peak_classifier.classes_) > 1:
                validity_prob = self.peak_classifier.predict_proba(features_scaled)[0, 1]
            else:
                # Only one class in training data
                validity_prob = 0.9 if self.peak_classifier.classes_[0] == 1 else 0.1
            is_valid = validity_prob > 0.5
            
            # Predict confidence (if valid)
            confidence = 0.0
            if is_valid and self.confidence_regressor:
                confidence = self.confidence_regressor.predict(features_scaled)[0]
                confidence = np.clip(confidence, 0.0, 1.0)
            
            predictions.append({
                'index': i,
                'voltage': candidate.get('voltage', 0.0),
                'current': candidate.get('current', 0.0),
                'type': candidate.get('type', 'unknown'),
                'is_valid': is_valid,
                'validity_probability': validity_prob,
                'confidence': confidence,
                'ai_method': 'DeepCV_V2.1'
            })
        
        # Filter to only valid predictions
        valid_predictions = [p for p in predictions if p['is_valid']]
        
        print(f"✅ DeepCV V2.1 Results:")
        print(f"   📊 Candidates analyzed: {len(predictions)}")
        print(f"   ✅ Valid peaks predicted: {len(valid_predictions)}")
        print(f"   📈 Average confidence: {np.mean([p['confidence'] for p in valid_predictions]):.3f}")
        
        return {
            'all_predictions': predictions,
            'valid_peaks': valid_predictions,
            'method': 'DeepCV_V2.1',
            'model_version': '2.1',
            'training_samples': len(self.training_history[-1]) if self.training_history else 0
        }
    
    def _simple_peak_detection(self, voltage, current):
        """Simple peak detection for candidates"""
        try:
            from scipy.signal import find_peaks
            
            # Find peaks in both directions
            pos_peaks, _ = find_peaks(current, height=np.std(current)*0.5, distance=5)
            neg_peaks, _ = find_peaks(-current, height=np.std(current)*0.5, distance=5)
            
            candidates = []
            
            # Add positive peaks
            for idx in pos_peaks:
                candidates.append({
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'oxidation'
                })
            
            # Add negative peaks
            for idx in neg_peaks:
                candidates.append({
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'reduction'
                })
            
            return candidates
            
        except ImportError:
            # Fallback: sample points
            return [
                {'voltage': voltage[i], 'current': current[i], 'type': 'unknown'}
                for i in range(0, len(voltage), len(voltage)//10)
            ][:20]
    
    def _extract_single_peak_features(self, candidate):
        """Extract features for single peak candidate"""
        voltage = candidate.get('voltage', 0.0)
        current = candidate.get('current', 0.0)
        peak_type = candidate.get('type', 'unknown')
        
        features = [
            voltage,                           # Peak voltage
            current,                          # Peak current
            abs(current),                     # Peak magnitude
            voltage**2,                       # Voltage squared
            current**2,                       # Current squared
            voltage * current,                # Voltage-current interaction
            1 if peak_type == 'oxidation' else 0,  # Is oxidation
            1 if peak_type == 'reduction' else 0,  # Is reduction
            1.0,                              # Default concentration
            0.0,                              # Default log concentration
            current,                          # Default current density
            0.7,                              # Default V5 confidence
            0,                                # Default high confidence flag
            np.exp(-abs(voltage)),           # Voltage decay
            np.tanh(current),                # Current saturation
        ]
        
        return features
    
    def save_model(self, filepath="models/deepcv_v21.joblib"):
        """Save trained model"""
        if not self.peak_classifier:
            print("❌ No model to save")
            return False
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'peak_classifier': self.peak_classifier,
            'confidence_regressor': self.confidence_regressor,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'training_history': self.training_history,
            'version': '2.1',
            'saved_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 Model saved to: {filepath}")
        return True
    
    def load_model(self, filepath="models/deepcv_v21.joblib"):
        """Load trained model"""
        try:
            model_data = joblib.load(filepath)
            
            self.peak_classifier = model_data['peak_classifier']
            self.confidence_regressor = model_data['confidence_regressor']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.training_history = model_data['training_history']
            
            print(f"📁 Model loaded from: {filepath}")
            print(f"🕒 Model version: {model_data.get('version', 'unknown')}")
            print(f"📊 Training history: {len(self.training_history)} sessions")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def create_training_report(self):
        """Create comprehensive training report"""
        if not self.training_history:
            print("❌ No training history available")
            return None
        
        latest = self.training_history[-1]
        
        report = {
            'model_info': {
                'version': '2.1',
                'type': 'Human-AI Collaborative',
                'algorithm': 'Random Forest + Gradient Boosting'
            },
            'training_data': {
                'total_samples': latest['train_samples'] + latest['test_samples'],
                'train_samples': latest['train_samples'],
                'test_samples': latest['test_samples'],
                'feature_count': latest['feature_count'],
                'valid_peak_ratio': latest['valid_ratio']
            },
            'performance': {
                'test_accuracy': latest['test_accuracy'],
                'training_date': latest['timestamp']
            },
            'features': self.feature_names,
            'training_sessions': len(self.training_history)
        }
        
        # Save report
        report_file = f"reports/deepcv_v21_training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Training report saved: {report_file}")
        return report

def main():
    """Test DeepCV V2.1 training pipeline"""
    
    # Initialize
    deepcv = DeepCVV21()
    
    # Load training data
    training_data = deepcv.load_training_data(min_confidence=0.7)
    
    if training_data is not None and not training_data.empty:
        # Extract features and train
        X, y, conf = deepcv.extract_features(training_data)
        training_result = deepcv.train_models(X, y, conf)
        
        # Save model
        deepcv.save_model()
        
        # Create report
        report = deepcv.create_training_report()
        
        print("\n🎉 DeepCV V2.1 Training Pipeline Complete!")
        print(f"📊 Final accuracy: {training_result['test_accuracy']:.3f}")
        
        # Test prediction (if sample data available)
        if os.path.exists("sample_data/cv_sample.csv"):
            print("\n🧪 Testing prediction on sample data...")
            try:
                df = pd.read_csv("sample_data/cv_sample.csv")
                if len(df.columns) >= 2:
                    voltage = df.iloc[:, 0].values
                    current = df.iloc[:, 1].values
                    
                    prediction_result = deepcv.predict_peaks(voltage, current)
                    if prediction_result:
                        print(f"✅ Predicted {len(prediction_result['valid_peaks'])} valid peaks")
            except Exception as e:
                print(f"⚠️  Test prediction failed: {e}")
    else:
        print("❌ No training data available. Please run V6 validation first.")
        print("💡 Tip: Use enhanced_detector_v6_improved.py to create validation data")
    
    return deepcv

if __name__ == "__main__":
    main()