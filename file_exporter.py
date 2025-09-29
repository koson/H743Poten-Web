"""
File export system for H743 Potentiostat measurements
Exports data as CSV files and generates PNG plots
"""

import os
import csv
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileExporter:
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        self.ensure_export_directory()
    
    def ensure_export_directory(self):
        """Create export directory if it doesn't exist"""
        try:
            os.makedirs(self.export_dir, exist_ok=True)
            # Create subdirectories
            for subdir in ['csv', 'png', 'json']:
                os.makedirs(os.path.join(self.export_dir, subdir), exist_ok=True)
            logger.info(f"✅ Export directories ready: {self.export_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to create export directories: {e}")
            raise
    
    def export_csv(self, measurement_id: int, measurement_data: Dict[str, Any], data_points: List[Dict[str, float]]) -> str:
        """Export measurement data as CSV file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            measurement_type = measurement_data.get('measurement_type', 'UNKNOWN')
            filename = f"{measurement_type}_M{measurement_id}_{timestamp}.csv"
            filepath = os.path.join(self.export_dir, 'csv', filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header with metadata
                writer.writerow(['# H743 Potentiostat Measurement Data'])
                writer.writerow(['# Measurement ID:', measurement_id])
                writer.writerow(['# Type:', measurement_type])
                writer.writerow(['# Timestamp:', measurement_data.get('timestamp', 'Unknown')])
                writer.writerow(['# Status:', measurement_data.get('status', 'Unknown')])
                writer.writerow(['# Data Points:', len(data_points)])
                writer.writerow(['# Duration (s):', measurement_data.get('duration_seconds', 0)])
                
                # Write parameters
                parameters = measurement_data.get('parameters', {})
                if parameters:
                    writer.writerow(['# Parameters:'])
                    for key, value in parameters.items():
                        writer.writerow([f'# {key}:', value])
                
                writer.writerow(['#'])  # Separator
                
                # Write data header
                if data_points:
                    # Determine columns based on available data
                    sample_point = data_points[0]
                    columns = ['Point Index', 'Voltage (V)', 'Current (A)']
                    if 'timestamp_offset' in sample_point:
                        columns.append('Time (s)')
                    
                    writer.writerow(columns)
                    
                    # Write data points
                    for i, point in enumerate(data_points):
                        row = [
                            i + 1,
                            point.get('voltage', 0),
                            point.get('current', 0)
                        ]
                        if 'timestamp_offset' in point:
                            row.append(point['timestamp_offset'])
                        writer.writerow(row)
                else:
                    writer.writerow(['# No data points available'])
            
            logger.info(f"✅ Exported CSV: {filename} ({len(data_points)} points)")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Failed to export CSV for measurement {measurement_id}: {e}")
            raise
    
    def export_png(self, measurement_id: int, measurement_data: Dict[str, Any], data_points: List[Dict[str, float]]) -> str:
        """Export measurement data as PNG plot"""
        try:
            if not data_points:
                raise ValueError("No data points to plot")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            measurement_type = measurement_data.get('measurement_type', 'UNKNOWN')
            filename = f"{measurement_type}_M{measurement_id}_{timestamp}.png"
            filepath = os.path.join(self.export_dir, 'png', filename)
            
            # Extract data for plotting
            voltages = [point.get('voltage', 0) for point in data_points]
            currents = [point.get('current', 0) for point in data_points]
            
            # Create plot
            plt.figure(figsize=(12, 8))
            
            if measurement_type.upper() == 'CV':
                # Cyclic Voltammetry plot
                plt.plot(voltages, currents, 'b-', linewidth=2, alpha=0.8)
                plt.xlabel('Potential (V)', fontsize=12)
                plt.ylabel('Current (A)', fontsize=12)
                plt.title(f'Cyclic Voltammetry - Measurement {measurement_id}', fontsize=14, fontweight='bold')
                plt.grid(True, alpha=0.3)
                
                # Add parameters to plot
                parameters = measurement_data.get('parameters', {})
                param_text = []
                if 'start_voltage' in parameters:
                    param_text.append(f"Start: {parameters['start_voltage']:.3f} V")
                if 'end_voltage' in parameters:
                    param_text.append(f"End: {parameters['end_voltage']:.3f} V")
                if 'scan_rate' in parameters:
                    param_text.append(f"Scan Rate: {parameters['scan_rate']:.3f} V/s")
                
                if param_text:
                    plt.text(0.02, 0.98, '\n'.join(param_text), transform=plt.gca().transAxes, 
                            fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
            elif measurement_type.upper() in ['SWV', 'DPV']:
                # Square Wave / Differential Pulse Voltammetry
                plt.plot(voltages, currents, 'r-', linewidth=2, alpha=0.8)
                plt.xlabel('Potential (V)', fontsize=12)
                plt.ylabel('Current (A)', fontsize=12)
                plt.title(f'{measurement_type.upper()} - Measurement {measurement_id}', fontsize=14, fontweight='bold')
                plt.grid(True, alpha=0.3)
                
            else:
                # Generic plot
                plt.plot(voltages, currents, 'g-', linewidth=2, alpha=0.8)
                plt.xlabel('Potential (V)', fontsize=12)
                plt.ylabel('Current (A)', fontsize=12)
                plt.title(f'{measurement_type} - Measurement {measurement_id}', fontsize=14, fontweight='bold')
                plt.grid(True, alpha=0.3)
            
            # Add metadata
            metadata_text = f"Points: {len(data_points)} | Status: {measurement_data.get('status', 'Unknown')}"
            if measurement_data.get('duration_seconds'):
                metadata_text += f" | Duration: {measurement_data['duration_seconds']:.1f}s"
            
            plt.figtext(0.02, 0.02, metadata_text, fontsize=9, style='italic')
            plt.figtext(0.98, 0.02, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                       fontsize=9, style='italic', ha='right')
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✅ Exported PNG: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Failed to export PNG for measurement {measurement_id}: {e}")
            raise
    
    def export_json(self, measurement_id: int, measurement_data: Dict[str, Any], data_points: List[Dict[str, float]]) -> str:
        """Export measurement data as JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            measurement_type = measurement_data.get('measurement_type', 'UNKNOWN')
            filename = f"{measurement_type}_M{measurement_id}_{timestamp}.json"
            filepath = os.path.join(self.export_dir, 'json', filename)
            
            export_data = {
                "measurement_id": measurement_id,
                "export_timestamp": datetime.now().isoformat(),
                "measurement": measurement_data,
                "data_points": data_points,
                "statistics": {
                    "total_points": len(data_points),
                    "voltage_range": {
                        "min": min(p.get('voltage', 0) for p in data_points) if data_points else 0,
                        "max": max(p.get('voltage', 0) for p in data_points) if data_points else 0
                    },
                    "current_range": {
                        "min": min(p.get('current', 0) for p in data_points) if data_points else 0,
                        "max": max(p.get('current', 0) for p in data_points) if data_points else 0
                    }
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Exported JSON: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Failed to export JSON for measurement {measurement_id}: {e}")
            raise
    
    def export_all_formats(self, measurement_id: int, measurement_data: Dict[str, Any], data_points: List[Dict[str, float]]) -> Dict[str, str]:
        """Export measurement in all formats"""
        try:
            exported_files = {}
            
            # Export CSV
            try:
                exported_files['csv'] = self.export_csv(measurement_id, measurement_data, data_points)
            except Exception as e:
                logger.error(f"CSV export failed: {e}")
            
            # Export PNG (only if we have data points)
            if data_points:
                try:
                    exported_files['png'] = self.export_png(measurement_id, measurement_data, data_points)
                except Exception as e:
                    logger.error(f"PNG export failed: {e}")
            
            # Export JSON
            try:
                exported_files['json'] = self.export_json(measurement_id, measurement_data, data_points)
            except Exception as e:
                logger.error(f"JSON export failed: {e}")
            
            logger.info(f"✅ Exported measurement {measurement_id} in {len(exported_files)} formats")
            return exported_files
            
        except Exception as e:
            logger.error(f"❌ Failed to export measurement {measurement_id}: {e}")
            return {}
    
    def list_exported_files(self, file_type: str = None) -> List[Dict[str, Any]]:
        """List exported files"""
        try:
            files = []
            search_dirs = [file_type] if file_type else ['csv', 'png', 'json']
            
            for subdir in search_dirs:
                dir_path = os.path.join(self.export_dir, subdir)
                if not os.path.exists(dir_path):
                    continue
                
                for filename in os.listdir(dir_path):
                    filepath = os.path.join(dir_path, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        files.append({
                            'filename': filename,
                            'filepath': filepath,
                            'type': subdir,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            
            # Sort by creation time, newest first
            files.sort(key=lambda x: x['created'], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to list exported files: {e}")
            return []
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get export directory statistics"""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'files_by_type': {}
            }
            
            for subdir in ['csv', 'png', 'json']:
                dir_path = os.path.join(self.export_dir, subdir)
                if not os.path.exists(dir_path):
                    stats['files_by_type'][subdir] = {'count': 0, 'size': 0}
                    continue
                
                count = 0
                size = 0
                for filename in os.listdir(dir_path):
                    filepath = os.path.join(dir_path, filename)
                    if os.path.isfile(filepath):
                        count += 1
                        size += os.path.getsize(filepath)
                
                stats['files_by_type'][subdir] = {'count': count, 'size': size}
                stats['total_files'] += count
                stats['total_size'] += size
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get export stats: {e}")
            return {}

# Global exporter instance
exporter = FileExporter()