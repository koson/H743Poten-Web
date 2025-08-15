"""
Data Logging Service for H743Poten Web Interface
Handles automatic saving of CV measurements as CSV and PNG files
"""

import os
import json
import logging
import pandas as pd

# Configure matplotlib to use Agg backend (non-interactive)
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import io
import base64

logger = logging.getLogger(__name__)

class DataLoggingService:
    """Service for logging CV measurement data and plots"""
    
    def __init__(self, base_data_dir: str = "data_logs"):
        self.base_data_dir = Path(base_data_dir)
        self.ensure_data_directory()
        
        # Metadata tracking
        self.session_metadata = {}
        
    def ensure_data_directory(self):
        """Create data directory structure"""
        try:
            # Create main data directory
            self.base_data_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            (self.base_data_dir / "csv").mkdir(exist_ok=True)
            (self.base_data_dir / "png").mkdir(exist_ok=True)
            (self.base_data_dir / "metadata").mkdir(exist_ok=True)
            (self.base_data_dir / "sessions").mkdir(exist_ok=True)
            
            logger.info(f"Data logging directory initialized: {self.base_data_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create data directories: {e}")
            raise
    
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"CV_{timestamp}"
    
    def save_cv_measurement(self, 
                          data_points: List[Dict], 
                          parameters: Dict,
                          session_id: Optional[str] = None) -> Dict:
        """
        Save CV measurement data and generate plot
        
        Returns:
            Dict with file paths and session info
        """
        try:
            if not data_points:
                raise ValueError("No data points to save")
            
            # Generate session ID if not provided
            if not session_id:
                session_id = self.generate_session_id()
            
            # Create session directory
            session_dir = self.base_data_dir / "sessions" / session_id
            session_dir.mkdir(exist_ok=True)
            
            # Prepare data for saving
            df = pd.DataFrame(data_points)
            
            # Generate file paths
            csv_path = session_dir / f"{session_id}.csv"
            png_path = session_dir / f"{session_id}.png"
            metadata_path = session_dir / f"{session_id}_metadata.json"
            
            # Save CSV data
            csv_result = self._save_csv_data(df, csv_path, parameters)
            
            # Generate and save PNG plot
            png_result = self._save_png_plot(df, png_path, parameters, session_id)
            
            # Save metadata
            metadata = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'parameters': parameters,
                'data_points_count': len(data_points),
                'csv_file': str(csv_path.relative_to(self.base_data_dir)),
                'png_file': str(png_path.relative_to(self.base_data_dir)),
                'voltage_range': {
                    'min': float(df['potential'].min()),
                    'max': float(df['potential'].max())
                },
                'current_range': {
                    'min': float(df['current'].min()),
                    'max': float(df['current'].max())
                },
                'cycles': int(df['cycle'].max()) if 'cycle' in df.columns else 1
            }
            
            metadata_result = self._save_metadata(metadata, metadata_path)
            
            # Store session info
            self.session_metadata[session_id] = metadata
            
            logger.info(f"CV measurement saved successfully: {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'csv_file': str(csv_path),
                'png_file': str(png_path),
                'metadata_file': str(metadata_path),
                'data_points_count': len(data_points),
                'message': f"Data saved to session {session_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to save CV measurement: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to save measurement: {e}"
            }
    
    def _save_csv_data(self, df: pd.DataFrame, csv_path: Path, parameters: Dict) -> bool:
        """Save CV data as CSV file"""
        try:
            # Add header with measurement parameters
            header_lines = [
                f"# CV Measurement Data",
                f"# Generated: {datetime.now().isoformat()}",
                f"# Parameters: {json.dumps(parameters, indent=None)}",
                f"# Columns: timestamp,potential,current,cycle,direction",
                ""
            ]
            
            # Write header and data
            with open(csv_path, 'w') as f:
                f.write('\n'.join(header_lines))
                
            # Append DataFrame
            df.to_csv(csv_path, mode='a', index=False)
            
            logger.info(f"CSV data saved: {csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save CSV data: {e}")
            return False
    
    def _save_png_plot(self, df: pd.DataFrame, png_path: Path, parameters: Dict, session_id: str) -> bool:
        """Generate and save CV plot as PNG"""
        try:
            # Create matplotlib figure
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Check if we have cycle information
            if 'cycle' in df.columns and df['cycle'].nunique() > 1:
                # Plot multiple cycles with different colors
                cycles = sorted(df['cycle'].unique())
                # Use different colors for each cycle
                color_list = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
                colors = [color_list[i % len(color_list)] for i in range(len(cycles))]
                
                for i, cycle in enumerate(cycles):
                    cycle_data = df[df['cycle'] == cycle]
                    ax.plot(cycle_data['potential'], cycle_data['current'], 
                           color=colors[i], label=f'Cycle {cycle}', linewidth=2)
            else:
                # Single cycle or no cycle info
                ax.plot(df['potential'], df['current'], 'b-', linewidth=2, label='CV Scan')
            
            # Customize plot
            ax.set_xlabel('Potential (V)', fontsize=12)
            ax.set_ylabel('Current (A)', fontsize=12)
            ax.set_title(f'Cyclic Voltammogram - {session_id}\\n'
                        f'Scan Rate: {parameters.get("rate", "N/A")} V/s, '
                        f'Range: {parameters.get("lower", "N/A")} to {parameters.get("upper", "N/A")} V', 
                        fontsize=14)
            
            # Add grid and legend
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Format axes
            ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
            
            # Add timestamp
            timestamp_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            fig.text(0.02, 0.02, timestamp_text, fontsize=10, alpha=0.7)
            
            # Save with high DPI
            plt.tight_layout()
            plt.savefig(png_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"PNG plot saved: {png_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save PNG plot: {e}")
            # Make sure to close the figure even on error
            plt.close('all')
            return False
    
    def _save_metadata(self, metadata: Dict, metadata_path: Path) -> bool:
        """Save session metadata as JSON"""
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata saved: {metadata_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False
    
    def list_sessions(self, limit: Optional[int] = None) -> List[Dict]:
        """List all saved measurement sessions"""
        try:
            sessions = []
            sessions_dir = self.base_data_dir / "sessions"
            
            if not sessions_dir.exists():
                return sessions
            
            # Get all session directories
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    metadata_file = session_dir / f"{session_dir.name}_metadata.json"
                    
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            
                            # Add file existence checks
                            csv_file = session_dir / f"{session_dir.name}.csv"
                            png_file = session_dir / f"{session_dir.name}.png"
                            
                            metadata['files_exist'] = {
                                'csv': csv_file.exists(),
                                'png': png_file.exists()
                            }
                            
                            sessions.append(metadata)
                            
                        except Exception as e:
                            logger.warning(f"Failed to load metadata for {session_dir.name}: {e}")
            
            # Sort by timestamp (newest first)
            sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Apply limit if specified
            if limit:
                sessions = sessions[:limit]
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get complete session data including CSV content"""
        try:
            session_dir = self.base_data_dir / "sessions" / session_id
            
            if not session_dir.exists():
                return None
            
            # Load metadata
            metadata_file = session_dir / f"{session_id}_metadata.json"
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Load CSV data
            csv_file = session_dir / f"{session_id}.csv"
            csv_data = None
            if csv_file.exists():
                # Skip header lines starting with #
                csv_data = pd.read_csv(csv_file, comment='#').to_dict('records')
            
            # Check PNG file
            png_file = session_dir / f"{session_id}.png"
            png_exists = png_file.exists()
            
            return {
                'metadata': metadata,
                'csv_data': csv_data,
                'csv_file': str(csv_file),
                'png_file': str(png_file),
                'png_exists': png_exists
            }
            
        except Exception as e:
            logger.error(f"Failed to get session data for {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> Tuple[bool, str]:
        """Delete a measurement session"""
        try:
            session_dir = self.base_data_dir / "sessions" / session_id
            
            if not session_dir.exists():
                return False, f"Session {session_id} not found"
            
            # Remove all files in session directory
            import shutil
            shutil.rmtree(session_dir)
            
            # Remove from memory cache
            if session_id in self.session_metadata:
                del self.session_metadata[session_id]
            
            logger.info(f"Session deleted: {session_id}")
            return True, f"Session {session_id} deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False, f"Failed to delete session: {e}"
    
    def get_data_directory_info(self) -> Dict:
        """Get information about data directory"""
        try:
            sessions_dir = self.base_data_dir / "sessions"
            
            if not sessions_dir.exists():
                return {
                    'total_sessions': 0,
                    'total_size_mb': 0,
                    'data_directory': str(self.base_data_dir)
                }
            
            # Count sessions and calculate total size
            total_sessions = len([d for d in sessions_dir.iterdir() if d.is_dir()])
            
            total_size = 0
            for item in self.base_data_dir.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            
            total_size_mb = total_size / (1024 * 1024)  # Convert to MB
            
            return {
                'total_sessions': total_sessions,
                'total_size_mb': round(total_size_mb, 2),
                'data_directory': str(self.base_data_dir),
                'directory_exists': self.base_data_dir.exists()
            }
            
        except Exception as e:
            logger.error(f"Failed to get data directory info: {e}")
            return {
                'total_sessions': 0,
                'total_size_mb': 0,
                'data_directory': str(self.base_data_dir),
                'error': str(e)
            }
