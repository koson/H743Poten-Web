#!/usr/bin/env python3
"""
Stratified Data Splitting for Peak Detection Framework
แบ่งข้อมูลแบบ stratified เพื่อการ validation ที่มีคุณภาพ

Author: H743Poten Research Team
Date: 2025-08-16
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import random
import re
from collections import defaultdict, Counter
import shutil
from datetime import datetime

class StratifiedDataSplitter:
    """แบ่งข้อมูล CV แบบ stratified สำหรับ peak detection validation"""
    
    def __init__(self, base_path=None, random_seed=42):
        if base_path is None:
            # Use current script directory as base
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
            if not self.base_path.is_absolute():
                self.base_path = Path(__file__).parent / base_path
        
        self.palmsens_path = self.base_path / "reference_cv_data" / "palmsens"
        self.stm32_path = self.base_path / "reference_cv_data" / "stm32h743"
        self.splits_path = self.base_path / "splits"
        self.metadata_path = self.base_path / "metadata"
        
        # สร้างโฟลเดอร์
        self.splits_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        (self.splits_path / "cross_instrument").mkdir(exist_ok=True)
        (self.splits_path / "loco_splits").mkdir(exist_ok=True)
        
        # Set random seed สำหรับ reproducibility
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        print(f"🎲 Stratified Data Splitter initialized with seed={random_seed}")
    
    def analyze_and_split_data(self):
        """วิเคราะห์และแบ่งข้อมูลทั้งหมด"""
        
        print("\n🔍 Analyzing data structure...")
        
        # รวบรวมข้อมูลไฟล์
        file_metadata = self._collect_file_metadata()
        
        print(f"📊 Found {len(file_metadata)} total files")
        
        # สร้าง primary splits (70/15/15)
        print("\n📚 Creating primary train/validation/test splits...")
        primary_splits = self._create_primary_splits(file_metadata)
        
        # สร้าง cross-instrument splits
        print("\n🔄 Creating cross-instrument validation splits...")
        cross_splits = self._create_cross_instrument_splits(file_metadata)
        
        # สร้าง LOCO splits
        print("\n🌟 Creating Leave-One-Condition-Out splits...")
        loco_splits = self._create_loco_splits(file_metadata)
        
        # บันทึกผลลัพธ์
        print("\n💾 Saving split results...")
        self._save_splits(primary_splits, cross_splits, loco_splits)
        
        # สร้างรายงาน
        print("\n📋 Generating split analysis report...")
        self._generate_split_report(file_metadata, primary_splits, cross_splits, loco_splits)
        
        print("\n✅ Data splitting completed successfully!")
        
        return primary_splits, cross_splits, loco_splits
    
    def _collect_file_metadata(self):
        """รวบรวม metadata ของทุกไฟล์"""
        
        file_metadata = []
        
        # PalmSens files
        palmsens_files = list(self.palmsens_path.glob("*.csv")) if self.palmsens_path.exists() else []
        for file_path in palmsens_files:
            metadata = self._extract_file_metadata(file_path, "palmsens")
            if metadata:
                file_metadata.append(metadata)
        
        # STM32H743 files  
        stm32_files = list(self.stm32_path.glob("*.csv")) if self.stm32_path.exists() else []
        for file_path in stm32_files:
            metadata = self._extract_file_metadata(file_path, "stm32h743")
            if metadata:
                file_metadata.append(metadata)
        
        return file_metadata
    
    def _extract_file_metadata(self, file_path, instrument):
        """สกัด metadata จากชื่อไฟล์ด้วย regex patterns"""
        
        try:
            name = file_path.name.replace('.csv', '')
            
            if instrument == "palmsens":
                # PalmSens: Palmsens_[conc]mM_CV_[rate]mVpS_E[electrode]_scan_[num]
                # Example: Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv
                pattern = r'Palmsens_(\d+\.?\d*)mM_CV_(\d+)mVpS_E(\d+)_scan_(\d+)'
                match = re.match(pattern, name)
                
                if match:
                    concentration = float(match.group(1))
                    scan_rate = int(match.group(2))
                    electrode = int(match.group(3))
                    scan_number = int(match.group(4))
                    
                    return {
                        'file_path': str(file_path),
                        'filename': file_path.name,
                        'instrument': 'PalmSens',
                        'concentration': concentration,
                        'scan_rate': scan_rate,
                        'electrode': electrode,
                        'scan_number': scan_number,
                        'condition_key': f"{concentration}mM_{scan_rate}mVpS_E{electrode}"
                    }
            
            elif instrument == "stm32h743":
                # STM32H743: Pipot_Ferro[_/-][conc]mM_[rate]mVpS_E[electrode]_scan_[num]
                # Examples: 
                # - Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv (decimal with underscore)
                # - Pipot_Ferro-1_0mM_200mVpS_E2_scan_05.csv (decimal with underscore after dash)
                # - Pipot_Ferro_10mM_50mVpS_E3_scan_11.csv (integer)
                # - Pipot_Ferro-10mM_50mVpS_E3_scan_11.csv (integer with dash)
                
                # Try pattern with underscore separator for decimal concentrations
                pattern1 = r'Pipot_Ferro_(\d+)_(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'
                match = re.match(pattern1, name)
                
                if match:
                    # Handle decimal concentrations like 0_5mM -> 0.5
                    concentration = float(f"{match.group(1)}.{match.group(2)}")
                    scan_rate = int(match.group(3))
                    electrode = int(match.group(4))
                    scan_number = int(match.group(5))
                else:
                    # Try pattern with dash separator for decimal concentrations
                    pattern2 = r'Pipot_Ferro-(\d+)_(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'
                    match = re.match(pattern2, name)
                    
                    if match:
                        # Handle decimal concentrations like 1_0mM -> 1.0
                        concentration = float(f"{match.group(1)}.{match.group(2)}")
                        scan_rate = int(match.group(3))
                        electrode = int(match.group(4))
                        scan_number = int(match.group(5))
                    else:
                        # Try pattern with underscore separator for integer concentrations
                        pattern3 = r'Pipot_Ferro_(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'
                        match = re.match(pattern3, name)
                        
                        if match:
                            concentration = float(match.group(1))
                            scan_rate = int(match.group(2))
                            electrode = int(match.group(3))
                            scan_number = int(match.group(4))
                        else:
                            # Try pattern with dash separator for integer concentrations
                            pattern4 = r'Pipot_Ferro-(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'
                            match = re.match(pattern4, name)
                            
                            if match:
                                concentration = float(match.group(1))
                                scan_rate = int(match.group(2))
                                electrode = int(match.group(3))
                                scan_number = int(match.group(4))
                            else:
                                print(f"⚠️  STM32H743 filename pattern not recognized: {name}")
                                return None
                
                return {
                    'file_path': str(file_path),
                    'filename': file_path.name,
                    'instrument': 'STM32H743',
                    'concentration': concentration,
                    'scan_rate': scan_rate,
                    'electrode': electrode,
                    'scan_number': scan_number,
                    'condition_key': f"{concentration}mM_{scan_rate}mVpS_E{electrode}"
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️  Failed to extract metadata from {file_path.name}: {e}")
            return None
    
    def _create_primary_splits(self, file_metadata):
        """สร้าง primary splits แบบ stratified 70/15/15"""
        
        # จัดกลุ่มตาม condition และ instrument
        condition_groups = defaultdict(lambda: defaultdict(list))
        
        for file_meta in file_metadata:
            condition = file_meta['condition_key']
            instrument = file_meta['instrument']
            condition_groups[condition][instrument].append(file_meta)
        
        train_files = []
        val_files = []
        test_files = []
        
        # แบ่งแต่ละ condition แยกกัน
        for condition, instruments in condition_groups.items():
            for instrument, files in instruments.items():
                if len(files) == 0:
                    continue
                
                # Shuffle files
                files_shuffled = files.copy()
                random.shuffle(files_shuffled)
                
                # คำนวณ split points
                n_files = len(files_shuffled)
                n_train = int(n_files * 0.7)
                n_val = int(n_files * 0.15)
                
                # แบ่งไฟล์
                train_files.extend(files_shuffled[:n_train])
                val_files.extend(files_shuffled[n_train:n_train + n_val])
                test_files.extend(files_shuffled[n_train + n_val:])
        
        return {
            'train': train_files,
            'validation': val_files,
            'test': test_files
        }
    
    def _create_cross_instrument_splits(self, file_metadata):
        """สร้าง cross-instrument validation splits"""
        
        palmsens_files = [f for f in file_metadata if f['instrument'] == 'palmsens']
        stm32_files = [f for f in file_metadata if f['instrument'] == 'stm32h743']
        
        return {
            'palmsens_train_stm32_test': {
                'train': palmsens_files,
                'test': stm32_files
            },
            'stm32_train_palmsens_test': {
                'train': stm32_files,
                'test': palmsens_files
            }
        }
    
    def _create_loco_splits(self, file_metadata):
        """สร้าง Leave-One-Condition-Out splits"""
        
        loco_splits = {
            'leave_concentration_out': [],
            'leave_scan_rate_out': [],
            'leave_electrode_out': []
        }
        
        # Leave-One-Concentration-Out
        concentrations = set(f['concentration'] for f in file_metadata)
        for conc in concentrations:
            test_files = [f for f in file_metadata if f['concentration'] == conc]
            train_files = [f for f in file_metadata if f['concentration'] != conc]
            
            if len(test_files) > 0 and len(train_files) > 0:
                loco_splits['leave_concentration_out'].append({
                    'name': f'leave_{conc}_out',
                    'train': train_files,
                    'test': test_files,
                    'left_out_condition': conc
                })
        
        # Leave-One-ScanRate-Out
        scan_rates = set(f['scan_rate'] for f in file_metadata)
        for rate in scan_rates:
            test_files = [f for f in file_metadata if f['scan_rate'] == rate]
            train_files = [f for f in file_metadata if f['scan_rate'] != rate]
            
            if len(test_files) > 0 and len(train_files) > 0:
                loco_splits['leave_scan_rate_out'].append({
                    'name': f'leave_{rate}_out',
                    'train': train_files,
                    'test': test_files,
                    'left_out_condition': rate
                })
        
        # Leave-One-Electrode-Out
        electrodes = set(f['electrode'] for f in file_metadata)
        for electrode in electrodes:
            test_files = [f for f in file_metadata if f['electrode'] == electrode]
            train_files = [f for f in file_metadata if f['electrode'] != electrode]
            
            if len(test_files) > 0 and len(train_files) > 0:
                loco_splits['leave_electrode_out'].append({
                    'name': f'leave_{electrode}_out',
                    'train': train_files,
                    'test': test_files,
                    'left_out_condition': electrode
                })
        
        return loco_splits
    
    def _save_splits(self, primary_splits, cross_splits, loco_splits):
        """บันทึก splits ลงไฟล์"""
        
        # Primary splits
        for split_name, files in primary_splits.items():
            file_paths = [f['file_path'] for f in files]
            output_file = self.splits_path / f"{split_name}_files.txt"
            with open(output_file, 'w') as f:
                f.write('\n'.join(file_paths))
            print(f"   💾 Saved {len(file_paths)} files to {output_file}")
        
        # Cross-instrument splits
        cross_dir = self.splits_path / "cross_instrument"
        for split_name, split_data in cross_splits.items():
            for subset_name, files in split_data.items():
                file_paths = [f['file_path'] for f in files]
                output_file = cross_dir / f"{split_name}_{subset_name}.txt"
                with open(output_file, 'w') as f:
                    f.write('\n'.join(file_paths))
        
        # LOCO splits
        loco_dir = self.splits_path / "loco_splits"
        for category, splits_list in loco_splits.items():
            category_dir = loco_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for split_info in splits_list:
                split_name = split_info['name']
                
                # Train files
                train_paths = [f['file_path'] for f in split_info['train']]
                train_file = category_dir / f"{split_name}_train.txt"
                with open(train_file, 'w') as f:
                    f.write('\n'.join(train_paths))
                
                # Test files
                test_paths = [f['file_path'] for f in split_info['test']]
                test_file = category_dir / f"{split_name}_test.txt"
                with open(test_file, 'w') as f:
                    f.write('\n'.join(test_paths))
    
    def _generate_split_report(self, file_metadata, primary_splits, cross_splits, loco_splits):
        """สร้างรายงานการแบ่งข้อมูล"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'random_seed': self.random_seed,
            'total_files': len(file_metadata),
            'instruments': {
                'palmsens': len([f for f in file_metadata if f['instrument'] == 'palmsens']),
                'stm32h743': len([f for f in file_metadata if f['instrument'] == 'stm32h743'])
            },
            'primary_splits': {
                'train': len(primary_splits['train']),
                'validation': len(primary_splits['validation']),
                'test': len(primary_splits['test'])
            },
            'cross_instrument_splits': {
                name: {subset: len(files) for subset, files in split_data.items()}
                for name, split_data in cross_splits.items()
            },
            'loco_splits': {
                category: len(splits_list) 
                for category, splits_list in loco_splits.items()
            }
        }
        
        # Detailed condition analysis
        report['condition_analysis'] = self._analyze_condition_distribution(file_metadata, primary_splits)
        
        # บันทึกรายงาน
        report_file = self.metadata_path / "split_statistics.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"   📊 Split report saved to {report_file}")
        
        # พิมพ์สรุป
        self._print_split_summary(report)
    
    def _analyze_condition_distribution(self, file_metadata, primary_splits):
        """วิเคราะห์การกระจายของเงื่อนไขในแต่ละ split"""
        
        def count_conditions(files):
            conditions = defaultdict(int)
            for f in files:
                conditions[f['condition_key']] += 1
            return dict(conditions)
        
        return {
            'train': count_conditions(primary_splits['train']),
            'validation': count_conditions(primary_splits['validation']),
            'test': count_conditions(primary_splits['test'])
        }
    
    def _print_split_summary(self, report):
        """พิมพ์สรุปการแบ่งข้อมูล"""
        
        print(f"\n📋 Split Summary:")
        print(f"   📊 Total Files: {report['total_files']:,}")
        print(f"   🔬 PalmSens: {report['instruments']['palmsens']:,}")
        print(f"   💻 STM32H743: {report['instruments']['stm32h743']:,}")
        
        print(f"\n📚 Primary Splits (70/15/15):")
        train_pct = report['primary_splits']['train'] / report['total_files'] * 100
        val_pct = report['primary_splits']['validation'] / report['total_files'] * 100
        test_pct = report['primary_splits']['test'] / report['total_files'] * 100
        
        print(f"   📚 Training: {report['primary_splits']['train']:,} files ({train_pct:.1f}%)")
        print(f"   🔍 Validation: {report['primary_splits']['validation']:,} files ({val_pct:.1f}%)")
        print(f"   🧪 Test: {report['primary_splits']['test']:,} files ({test_pct:.1f}%)")
        
        print(f"\n🔄 Cross-Instrument Splits:")
        for name, counts in report['cross_instrument_splits'].items():
            print(f"   {name}: Train={counts['train']:,}, Test={counts['test']:,}")
        
        print(f"\n🌟 LOCO Splits:")
        for category, count in report['loco_splits'].items():
            print(f"   {category}: {count} splits")

def main():
    """Main function"""
    
    print("🎲 H743Poten Stratified Data Splitting")
    print("=" * 60)
    
    # สร้าง splitter
    splitter = StratifiedDataSplitter(random_seed=42)
    
    # ทำการแบ่งข้อมูล
    primary_splits, cross_splits, loco_splits = splitter.analyze_and_split_data()
    
    print(f"\n🎉 Data splitting completed successfully!")
    print(f"📁 Check validation_data/splits/ for split files")
    print(f"📊 Check validation_data/metadata/ for detailed reports")

if __name__ == "__main__":
    main()
