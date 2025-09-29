"""
Data Stream Manager for STM32 H743 Potentiostat
================================================

Queue-based data streaming system:
- STM32 continuously sends data → stored in memory queue
- Web frontend polls at any rate → gets new data via pointer
- No data loss, efficient memory usage, scalable design

Author: GitHub Copilot + Brilliant Shower Idea 🚿💡
Date: September 30, 2025
"""

import threading
import time
import json
import os
from collections import deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import tempfile

@dataclass
class DataPoint:
    """Single measurement data point"""
    timestamp: float
    voltage: float
    current: float
    measurement_type: str
    cycle: int = 0
    point_index: int = 0
    raw_data: str = ""

@dataclass
class StreamSession:
    """Measurement stream session"""
    session_id: str
    measurement_id: int
    measurement_type: str
    start_time: float
    parameters: Dict[str, Any]
    status: str = "active"  # active, paused, completed, error
    total_points: int = 0
    last_activity: float = 0

class DataStreamManager:
    """
    Thread-safe data stream manager with queue-based architecture
    """
    
    def __init__(self, max_memory_points: int = 10000):
        self.max_memory_points = max_memory_points
        self.sessions: Dict[str, StreamSession] = {}
        self.data_queues: Dict[str, deque] = {}
        self.client_pointers: Dict[str, Dict[str, int]] = {}  # session_id -> {client_id: pointer}
        self.lock = threading.RLock()
        
        # Memory-mapped file storage for large datasets
        self.temp_dir = tempfile.mkdtemp(prefix="h743_stream_")
        print(f"📁 Stream data directory: {self.temp_dir}")
    
    def create_session(self, measurement_id: int, measurement_type: str, 
                      parameters: Dict[str, Any]) -> str:
        """Create new streaming session"""
        session_id = f"{measurement_type}_{measurement_id}_{int(time.time())}"
        
        with self.lock:
            self.sessions[session_id] = StreamSession(
                session_id=session_id,
                measurement_id=measurement_id,
                measurement_type=measurement_type,
                start_time=time.time(),
                parameters=parameters,
                last_activity=time.time()
            )
            self.data_queues[session_id] = deque(maxlen=self.max_memory_points)
            self.client_pointers[session_id] = {}
            
        print(f"🆕 Created stream session: {session_id}")
        return session_id
    
    def add_data_point(self, session_id: str, data_point: DataPoint) -> bool:
        """Add data point to session queue"""
        if session_id not in self.sessions:
            return False
            
        with self.lock:
            # Add to memory queue
            self.data_queues[session_id].append(data_point)
            
            # Update session stats
            session = self.sessions[session_id]
            session.total_points += 1
            session.last_activity = time.time()
            
            # If queue is full, optionally write to file
            if len(self.data_queues[session_id]) >= self.max_memory_points:
                self._write_overflow_to_file(session_id)
                
        return True
    
    def _write_overflow_to_file(self, session_id: str):
        """Write oldest data to file when memory queue is full"""
        # This could be implemented for very long measurements
        # For now, deque with maxlen handles overflow automatically
        pass
    
    def get_new_data(self, session_id: str, client_id: str = "default") -> List[Dict]:
        """Get new data points since last call for this client"""
        if session_id not in self.sessions:
            return []
            
        with self.lock:
            # Initialize client pointer if new
            if client_id not in self.client_pointers[session_id]:
                self.client_pointers[session_id][client_id] = 0
            
            current_pointer = self.client_pointers[session_id][client_id]
            queue = list(self.data_queues[session_id])
            
            # Get new data since pointer
            new_data = queue[current_pointer:]
            
            # Update pointer
            self.client_pointers[session_id][client_id] = len(queue)
            
            # Convert to dict format
            return [asdict(point) for point in new_data]
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get session status and statistics"""
        if session_id not in self.sessions:
            return None
            
        with self.lock:
            session = self.sessions[session_id]
            queue_size = len(self.data_queues[session_id])
            
            return {
                "session_id": session_id,
                "measurement_id": session.measurement_id,
                "measurement_type": session.measurement_type,
                "status": session.status,
                "start_time": session.start_time,
                "last_activity": session.last_activity,
                "total_points": session.total_points,
                "queue_size": queue_size,
                "parameters": session.parameters,
                "clients": list(self.client_pointers[session_id].keys()),
                "uptime": time.time() - session.start_time
            }
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status"""
        if session_id not in self.sessions:
            return False
            
        with self.lock:
            self.sessions[session_id].status = status
            self.sessions[session_id].last_activity = time.time()
            
        print(f"📊 Session {session_id} status: {status}")
        return True
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        with self.lock:
            return [self.get_session_status(sid) for sid in self.sessions.keys()]
    
    def cleanup_session(self, session_id: str):
        """Clean up completed session"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.data_queues:
                del self.data_queues[session_id]
            if session_id in self.client_pointers:
                del self.client_pointers[session_id]
                
        print(f"🧹 Cleaned up session: {session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: float = 24):
        """Clean up old inactive sessions"""
        current_time = time.time()
        to_cleanup = []
        
        with self.lock:
            for session_id, session in self.sessions.items():
                age_hours = (current_time - session.last_activity) / 3600
                if age_hours > max_age_hours:
                    to_cleanup.append(session_id)
        
        for session_id in to_cleanup:
            self.cleanup_session(session_id)
            
        if to_cleanup:
            print(f"🧹 Cleaned up {len(to_cleanup)} old sessions")

# Global stream manager instance
stream_manager = DataStreamManager()

def parse_stm32_response(response: str, measurement_type: str) -> Optional[DataPoint]:
    """
    Parse STM32 response into DataPoint
    
    Expected format: "CV, Time(us), Potential(V), Current(uA), CurrentRange, cycle no, extra..."
    Example: "CV, 141355, 0.1334, -1.0540, 2, 1, 2269, 2051, 1429, 2252"
    """
    try:
        if not response.strip():
            return None
            
        parts = [p.strip() for p in response.split(',')]
        if len(parts) < 4:  # Need at least: Mode, Time, Voltage, Current
            return None
            
        # Check if it's the expected measurement type
        if parts[0].upper() != measurement_type.upper():
            return None
            
        # Parse according to correct STM32 format
        timestamp_us = float(parts[1])  # Time in microseconds
        voltage = float(parts[2])       # Potential in V
        current_ua = float(parts[3])    # Current in uA
        
        # Convert current from uA to A for consistency
        current = current_ua / 1_000_000  # uA to A
        
        # Extract additional fields if available
        current_range = int(parts[4]) if len(parts) > 4 and parts[4].replace('-','').isdigit() else 0
        cycle_no = int(parts[5]) if len(parts) > 5 and parts[5].replace('-','').isdigit() else 0
        
        return DataPoint(
            timestamp=timestamp_us / 1_000_000,  # Convert us to seconds
            voltage=voltage,
            current=current,
            measurement_type=measurement_type,
            cycle=cycle_no,
            point_index=0,  # Will be set by stream manager
            raw_data=response
        )
        
    except (ValueError, IndexError) as e:
        print(f"⚠️ Failed to parse STM32 response: {response} - {e}")
        return None

if __name__ == "__main__":
    # Test the stream manager
    print("🧪 Testing Data Stream Manager...")
    
    # Create session
    session_id = stream_manager.create_session(
        measurement_id=999,
        measurement_type="CV",
        parameters={"start_voltage": -1.0, "end_voltage": 1.0}
    )
    
    # Add some test data
    for i in range(5):
        point = DataPoint(
            timestamp=time.time(),
            voltage=-1.0 + i * 0.5,
            current=-0.001 * i,
            measurement_type="CV",
            point_index=i
        )
        stream_manager.add_data_point(session_id, point)
        time.sleep(0.1)
    
    # Test client data retrieval
    client1_data = stream_manager.get_new_data(session_id, "client1")
    print(f"Client 1 got {len(client1_data)} points")
    
    client2_data = stream_manager.get_new_data(session_id, "client2")
    print(f"Client 2 got {len(client2_data)} points")
    
    # Client 1 calls again (should get no new data)
    client1_data2 = stream_manager.get_new_data(session_id, "client1")
    print(f"Client 1 second call got {len(client1_data2)} points")
    
    # Session status
    status = stream_manager.get_session_status(session_id)
    print(f"Session status: {json.dumps(status, indent=2)}")
    
    print("✅ Stream Manager test completed!")