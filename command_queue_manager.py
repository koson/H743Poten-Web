"""
Advanced Command Queue Management System
=======================================

🌅 Morning Setup Vision:
- Researchers prepare samples + queue measurements for the day
- STM32 devices execute commands automatically
- Full queue management: view, modify, delete commands
- Multi-device support: 10+ STM32 running simultaneously

Author: GitHub Copilot + User's Brilliant Vision
Date: September 30, 2025
"""

import threading
import time
import json
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import queue
import logging

logger = logging.getLogger(__name__)

class CommandStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class QueuedCommand:
    """Single command in the execution queue"""
    command_id: str
    device_id: str  # Which STM32 device
    command_type: str  # CV, DPV, SWV, CA, etc.
    parameters: Dict[str, Any]
    priority: Priority
    researcher_id: str
    sample_info: Dict[str, Any]
    notes: str
    created_at: float
    scheduled_start: Optional[float] = None
    estimated_duration: Optional[float] = None
    status: CommandStatus = CommandStatus.QUEUED
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class DeviceInfo:
    """STM32 device information"""
    device_id: str
    port: str
    serial_number: str
    status: str  # connected, busy, error, offline
    current_command_id: Optional[str] = None
    last_activity: float = 0
    capabilities: List[str] = None
    queue_size: int = 0

class CommandQueueManager:
    """Advanced Command Queue Management System"""
    
    def __init__(self):
        self.command_queue = queue.PriorityQueue()
        self.commands: Dict[str, QueuedCommand] = {}
        self.devices: Dict[str, DeviceInfo] = {}
        self.running_commands: Dict[str, QueuedCommand] = {}
        self.completed_commands: List[QueuedCommand] = []
        self.lock = threading.RLock()
        
        # Auto-execution control
        self.auto_execution_enabled = True
        self.max_concurrent_commands = 10
        self.execution_threads: Dict[str, threading.Thread] = {}
        
        # Statistics
        self.total_queued = 0
        self.total_completed = 0
        self.total_failed = 0
    
    def register_device(self, device_id: str, port: str, serial_number: str, 
                       capabilities: List[str] = None) -> bool:
        """Register a new STM32 device"""
        with self.lock:
            if capabilities is None:
                capabilities = ["CV", "DPV", "SWV", "CA"]
                
            self.devices[device_id] = DeviceInfo(
                device_id=device_id,
                port=port,
                serial_number=serial_number,
                status="connected",
                capabilities=capabilities,
                last_activity=time.time()
            )
            
        logger.info(f"📱 Registered device: {device_id} on {port}")
        return True
    
    def queue_command(self, command_type: str, parameters: Dict[str, Any],
                     researcher_id: str, sample_info: Dict[str, Any],
                     device_id: str = None, priority: Priority = Priority.NORMAL,
                     notes: str = "", scheduled_start: float = None,
                     estimated_duration: float = None) -> str:
        """Queue a new measurement command"""
        
        command_id = str(uuid.uuid4())
        
        # Auto-assign device if not specified
        if device_id is None:
            device_id = self._find_available_device(command_type)
            if not device_id:
                raise ValueError(f"No available device for {command_type}")
        
        # Validate device can handle this command
        if not self._can_device_handle_command(device_id, command_type):
            raise ValueError(f"Device {device_id} cannot handle {command_type}")
        
        command = QueuedCommand(
            command_id=command_id,
            device_id=device_id,
            command_type=command_type,
            parameters=parameters,
            priority=priority,
            researcher_id=researcher_id,
            sample_info=sample_info,
            notes=notes,
            created_at=time.time(),
            scheduled_start=scheduled_start,
            estimated_duration=estimated_duration
        )
        
        with self.lock:
            self.commands[command_id] = command
            self.command_queue.put((priority.value, time.time(), command_id))
            self.total_queued += 1
            
            # Update device queue size
            if device_id in self.devices:
                self.devices[device_id].queue_size += 1
        
        logger.info(f"📝 Queued command: {command_id} ({command_type}) for {researcher_id}")
        return command_id
    
    def _find_available_device(self, command_type: str) -> Optional[str]:
        """Find an available device that can handle the command"""
        with self.lock:
            # Prefer devices that are not busy
            idle_devices = []
            busy_devices = []
            
            for device_id, device in self.devices.items():
                if (command_type in device.capabilities and 
                    device.status in ["connected", "busy"]):
                    if device.status == "connected":
                        idle_devices.append((device_id, device.queue_size))
                    else:
                        busy_devices.append((device_id, device.queue_size))
            
            # Sort by queue size (prefer less busy devices)
            if idle_devices:
                idle_devices.sort(key=lambda x: x[1])
                return idle_devices[0][0]
            
            if busy_devices:
                busy_devices.sort(key=lambda x: x[1])
                return busy_devices[0][0]
            
            return None
    
    def _can_device_handle_command(self, device_id: str, command_type: str) -> bool:
        """Check if device can handle the command type"""
        with self.lock:
            device = self.devices.get(device_id)
            return (device and 
                   device.status in ["connected", "busy"] and
                   command_type in device.capabilities)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get comprehensive queue status"""
        with self.lock:
            # Get all queued commands
            queued_commands = [cmd for cmd in self.commands.values() 
                             if cmd.status == CommandStatus.QUEUED]
            queued_commands.sort(key=lambda x: (x.priority.value, x.created_at))
            
            # Get running commands
            running_commands = [cmd for cmd in self.commands.values() 
                              if cmd.status == CommandStatus.RUNNING]
            
            # Calculate estimated completion times
            total_estimated_time = sum(
                cmd.estimated_duration or 300  # Default 5 minutes
                for cmd in queued_commands
            )
            
            return {
                "queue_summary": {
                    "total_queued": len(queued_commands),
                    "total_running": len(running_commands),
                    "total_completed": len(self.completed_commands),
                    "estimated_completion_time": total_estimated_time,
                    "auto_execution_enabled": self.auto_execution_enabled
                },
                "devices": {
                    device_id: {
                        "status": device.status,
                        "current_command": device.current_command_id,
                        "queue_size": device.queue_size,
                        "capabilities": device.capabilities,
                        "last_activity": device.last_activity
                    }
                    for device_id, device in self.devices.items()
                },
                "queued_commands": [
                    {
                        "command_id": cmd.command_id,
                        "command_type": cmd.command_type,
                        "device_id": cmd.device_id,
                        "researcher_id": cmd.researcher_id,
                        "priority": cmd.priority.name,
                        "created_at": cmd.created_at,
                        "estimated_duration": cmd.estimated_duration,
                        "sample_info": cmd.sample_info,
                        "notes": cmd.notes
                    }
                    for cmd in queued_commands[:20]  # Show first 20
                ],
                "running_commands": [
                    {
                        "command_id": cmd.command_id,
                        "command_type": cmd.command_type,
                        "device_id": cmd.device_id,
                        "researcher_id": cmd.researcher_id,
                        "started_at": cmd.started_at,
                        "session_id": cmd.session_id,
                        "elapsed_time": time.time() - (cmd.started_at or 0)
                    }
                    for cmd in running_commands
                ],
                "statistics": {
                    "total_queued": self.total_queued,
                    "total_completed": self.total_completed,
                    "total_failed": self.total_failed,
                    "success_rate": (
                        self.total_completed / max(self.total_queued, 1) * 100
                        if self.total_queued > 0 else 0
                    )
                }
            }
    
    def modify_command(self, command_id: str, **updates) -> bool:
        """Modify a queued command"""
        with self.lock:
            command = self.commands.get(command_id)
            if not command:
                return False
                
            if command.status != CommandStatus.QUEUED:
                logger.warning(f"Cannot modify command {command_id}: status is {command.status}")
                return False
            
            # Update allowed fields
            allowed_updates = ['priority', 'parameters', 'notes', 'scheduled_start', 
                             'estimated_duration', 'device_id']
            
            for key, value in updates.items():
                if key in allowed_updates:
                    if key == 'priority' and isinstance(value, str):
                        value = Priority[value.upper()]
                    setattr(command, key, value)
            
            logger.info(f"📝 Modified command: {command_id}")
            return True
    
    def cancel_command(self, command_id: str, reason: str = "") -> bool:
        """Cancel a queued or running command"""
        with self.lock:
            command = self.commands.get(command_id)
            if not command:
                return False
            
            if command.status == CommandStatus.COMPLETED:
                return False
            
            # Update command status
            command.status = CommandStatus.CANCELLED
            command.error_message = f"Cancelled: {reason}"
            command.completed_at = time.time()
            
            # Remove from running if applicable
            if command_id in self.running_commands:
                del self.running_commands[command_id]
            
            # Update device status
            device = self.devices.get(command.device_id)
            if device and device.current_command_id == command_id:
                device.current_command_id = None
                device.status = "connected"
                device.queue_size = max(0, device.queue_size - 1)
            
            logger.info(f"❌ Cancelled command: {command_id} - {reason}")
            return True
    
    def get_command_details(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific command"""
        with self.lock:
            command = self.commands.get(command_id)
            if not command:
                return None
            
            return {
                "command": asdict(command),
                "device_info": asdict(self.devices.get(command.device_id)) if command.device_id in self.devices else None,
                "estimated_completion": self._estimate_completion_time(command_id),
                "position_in_queue": self._get_queue_position(command_id)
            }
    
    def _estimate_completion_time(self, command_id: str) -> Optional[float]:
        """Estimate when a command will complete"""
        with self.lock:
            command = self.commands.get(command_id)
            if not command or command.status != CommandStatus.QUEUED:
                return None
            
            # Find all commands ahead in queue for same device
            ahead_commands = [
                cmd for cmd in self.commands.values()
                if (cmd.device_id == command.device_id and
                    cmd.status in [CommandStatus.QUEUED, CommandStatus.RUNNING] and
                    (cmd.priority.value > command.priority.value or
                     (cmd.priority.value == command.priority.value and 
                      cmd.created_at < command.created_at)))
            ]
            
            total_time = sum(cmd.estimated_duration or 300 for cmd in ahead_commands)
            return time.time() + total_time
    
    def _get_queue_position(self, command_id: str) -> Optional[int]:
        """Get position of command in queue"""
        with self.lock:
            command = self.commands.get(command_id)
            if not command or command.status != CommandStatus.QUEUED:
                return None
            
            # Count commands ahead in queue
            ahead_count = 0
            for cmd in self.commands.values():
                if (cmd.device_id == command.device_id and
                    cmd.status == CommandStatus.QUEUED and
                    (cmd.priority.value > command.priority.value or
                     (cmd.priority.value == command.priority.value and 
                      cmd.created_at < command.created_at))):
                    ahead_count += 1
            
            return ahead_count + 1
    
    def start_auto_execution(self):
        """Start automatic command execution"""
        self.auto_execution_enabled = True
        logger.info("🚀 Auto-execution enabled")
    
    def stop_auto_execution(self):
        """Stop automatic command execution"""
        self.auto_execution_enabled = False
        logger.info("⏸️ Auto-execution disabled")
    
    def get_researcher_commands(self, researcher_id: str) -> List[Dict[str, Any]]:
        """Get all commands for a specific researcher"""
        with self.lock:
            researcher_commands = []
            for command in self.commands.values():
                if command.researcher_id == researcher_id:
                    researcher_commands.append({
                        "command_id": command.command_id,
                        "command_type": command.command_type,
                        "status": command.status.value,
                        "created_at": command.created_at,
                        "sample_info": command.sample_info,
                        "notes": command.notes,
                        "device_id": command.device_id
                    })
            
            # Sort by creation time
            researcher_commands.sort(key=lambda x: x["created_at"], reverse=True)
            return researcher_commands

# Global queue manager instance
queue_manager = CommandQueueManager()

if __name__ == "__main__":
    # Test the queue system
    print("🧪 Testing Command Queue Manager...")
    
    # Register some devices
    queue_manager.register_device("STM32_001", "/dev/ttyACM0", "SN001", ["CV", "DPV"])
    queue_manager.register_device("STM32_002", "/dev/ttyACM1", "SN002", ["SWV", "CA"])
    queue_manager.register_device("STM32_003", "/dev/ttyACM2", "SN003", ["CV", "DPV", "SWV"])
    
    # Queue some commands
    cmd1 = queue_manager.queue_command(
        command_type="CV",
        parameters={"start_voltage": -1.0, "end_voltage": 1.0},
        researcher_id="Dr.Smith",
        sample_info={"sample_id": "SAMPLE_001", "concentration": "1mM"},
        priority=Priority.HIGH,
        notes="Morning batch - high priority sample",
        estimated_duration=600
    )
    
    cmd2 = queue_manager.queue_command(
        command_type="DPV",
        parameters={"start_voltage": -0.5, "end_voltage": 0.5},
        researcher_id="Dr.Johnson",
        sample_info={"sample_id": "SAMPLE_002", "pH": 7.4},
        notes="Standard protocol",
        estimated_duration=450
    )
    
    # Get queue status
    status = queue_manager.get_queue_status()
    print(f"📊 Queue Status: {json.dumps(status, indent=2, default=str)}")
    
    print("✅ Command Queue Manager test completed!")