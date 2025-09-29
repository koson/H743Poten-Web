#!/usr/bin/env python3
"""
Smart SCPI Controller with Auto Port Detection
"""

from flask import Flask, render_template_string, request, jsonify
import serial
import serial.tools.list_ports
import time
import json
import glob
import os

app = Flask(__name__)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html><head><title>STM32 SCPI Web Interface</title><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
.container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.panel { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px; }
.success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
.error { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
.info { background-color: #e7f3ff; border-color: #bee5eb; color: #0c5460; }
.warning { background-color: #fff3cd; border-color: #ffeaa7; color: #856404; }
button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; margin: 5px; transition: all 0.3s; }
button:hover { background: #0056b3; transform: translateY(-1px); }
.reconnect-btn { background: #28a745; }
.reconnect-btn:hover { background: #1e7e34; }
.clear-btn { background: #6c757d; }
.clear-btn:hover { background: #545b62; }
textarea { width: 100%; height: 200px; font-family: 'Courier New', monospace; border: 1px solid #ddd; border-radius: 5px; padding: 10px; }
.log { max-height: 400px; overflow-y: auto; background: #f8f9fa; padding: 15px; border: 1px solid #ddd; border-radius: 5px; font-family: 'Courier New', monospace; }
input[type="text"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin: 2px; }
.status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
.status-connected { background: #28a745; }
.status-disconnected { background: #dc3545; }
.status-connecting { background: #ffc107; animation: pulse 1s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
.port-info { background: #e9ecef; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace; }
</style></head><body>
<div class="container">
<h1>🔬 STM32 SCPI Web Interface</h1>

<div class="panel info">
<h3>📡 Connection Status</h3>
<div id="connectionStatus">
<span class="status-indicator status-disconnected"></span>
<span id="statusText">Initializing...</span>
</div>
<div id="portInfo" class="port-info">Port: Detecting...</div>
</div>

<div class="panel">
<h3>📤 SCPI Commands</h3>
<button onclick="sendCommand('*IDN?')">🆔 Device ID</button>
<button onclick="sendCommand('POTEn:CV:STATUS?')">📊 CV Status</button>
<button onclick="startCV()">▶️ Start CV</button>
<button onclick="sendCommand('POTEn:CV:DATA?')">📈 Get Data</button>
<button onclick="reconnectSTM32()" class="reconnect-btn">🔄 Reconnect</button>
<button onclick="clearLog()" class="clear-btn">🗑️ Clear Log</button>
<br><br>

<div>
<label><strong>Custom Command:</strong></label><br>
<input type="text" id="customCmd" placeholder="Enter SCPI command" style="width: 300px;">
<button onclick="sendCustomCommand()">📤 Send</button>
</div>

<div style="margin-top: 15px;">
<label><strong>CV Parameters:</strong></label><br>
Start V: <input type="text" id="startV" value="-0.5" style="width: 80px;">
End V: <input type="text" id="endV" value="0.5" style="width: 80px;">
Step V: <input type="text" id="stepV" value="0.1" style="width: 80px;">
Cycles: <input type="text" id="cycles" value="1" style="width: 60px;">
</div>
</div>

<div class="panel">
<h3>📊 Response Log</h3>
<div id="responseLog" class="log"></div>
</div>

<div class="panel">
<h3>📈 Data Visualization</h3>
<textarea id="dataDisplay" placeholder="CSV data will appear here..."></textarea>
</div>
</div>

<script>
let connectionStatus = 'disconnected';

function updateConnectionStatus(status, port = null) {
    const indicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('statusText');
    const portInfo = document.getElementById('portInfo');
    
    indicator.className = 'status-indicator status-' + status;
    connectionStatus = status;
    
    switch(status) {
        case 'connected':
            statusText.textContent = 'Connected to STM32';
            statusText.style.color = '#28a745';
            break;
        case 'connecting':
            statusText.textContent = 'Connecting...';
            statusText.style.color = '#ffc107';
            break;
        case 'disconnected':
            statusText.textContent = 'Disconnected';
            statusText.style.color = '#dc3545';
            break;
    }
    
    if (port) {
        portInfo.textContent = `Port: ${port}`;
    }
}

function log(message, type = 'info') {
    const logDiv = document.getElementById('responseLog');
    const timestamp = new Date().toLocaleTimeString();
    const typeClass = {
        'info': '',
        'success': 'success',
        'error': 'error',
        'warning': 'warning'
    }[type] || '';
    
    const logEntry = document.createElement('div');
    logEntry.className = typeClass;
    logEntry.innerHTML = `[${timestamp}] ${message}`;
    logDiv.appendChild(logEntry);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function sendCommand(command) {
    log(`📤 Sending: ${command}`, 'info');
    
    if (connectionStatus === 'disconnected') {
        updateConnectionStatus('connecting');
    }
    
    fetch('/scpi', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: command})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateConnectionStatus('connected', data.port || 'Unknown');
            log(`📥 Response: ${data.response}`, 'success');
            if (data.response.includes('CSV:')) {
                document.getElementById('dataDisplay').value = data.response;
            }
        } else {
            updateConnectionStatus('disconnected');
            log(`❌ Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        updateConnectionStatus('disconnected');
        log(`❌ Network Error: ${error}`, 'error');
    });
}

function sendCustomCommand() {
    const cmd = document.getElementById('customCmd').value.trim();
    if (cmd) {
        sendCommand(cmd);
        document.getElementById('customCmd').value = '';
    }
}

function startCV() {
    const startV = document.getElementById('startV').value;
    const endV = document.getElementById('endV').value;
    const stepV = document.getElementById('stepV').value;
    const cycles = document.getElementById('cycles').value;
    const command = `POTEn:CV:Start:ALL ${startV},${endV},${stepV},${cycles}`;
    sendCommand(command);
}

function reconnectSTM32() {
    log('🔄 Forcing STM32 reconnection...', 'warning');
    updateConnectionStatus('connecting');
    
    fetch('/reconnect', {method: 'POST'})
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateConnectionStatus('connected', data.port);
            log(`✅ STM32 Reconnected Successfully on ${data.port}`, 'success');
            setTimeout(() => sendCommand('*IDN?'), 1000);
        } else {
            updateConnectionStatus('disconnected');
            log(`❌ Reconnection failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        updateConnectionStatus('disconnected');
        log(`❌ Reconnection Error: ${error}`, 'error');
    });
}

function clearLog() {
    document.getElementById('responseLog').innerHTML = '';
    document.getElementById('dataDisplay').value = '';
    log('🗑️ Log cleared', 'info');
}

// Initialize
window.onload = function() {
    log('🚀 STM32 SCPI Web Interface Started', 'info');
    updateConnectionStatus('connecting');
    setTimeout(() => sendCommand('*IDN?'), 2000);
};

// Auto-detect connection status
setInterval(() => {
    if (connectionStatus === 'connected') {
        fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (!data.stm32_connected) {
                updateConnectionStatus('disconnected');
                log('⚠️ STM32 connection lost', 'warning');
            }
        })
        .catch(() => {
            updateConnectionStatus('disconnected');
        });
    }
}, 10000); // Check every 10 seconds
</script></body></html>'''

class SmartSCPIController:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.serial_conn = None
        self.current_port = None
        self.last_working_port = None
    
    def find_stm32_ports(self):
        """Find all potential STM32 ports"""
        ports = []
        
        # Method 1: Use pyserial port detection
        try:
            available_ports = serial.tools.list_ports.comports()
            for port in available_ports:
                if any(keyword in port.description.lower() for keyword in ['stm', 'usb', 'serial']):
                    ports.append(port.device)
        except:
            pass
        
        # Method 2: Check Linux USB ACM devices
        for device_pattern in ['/dev/ttyACM*', '/dev/ttyUSB*']:
            ports.extend(glob.glob(device_pattern))
        
        # Method 3: Check common Windows COM ports (if running on Windows)
        if os.name == 'nt':
            for i in range(1, 21):
                ports.append(f'COM{i}')
        
        # Remove duplicates and sort
        ports = sorted(list(set(ports)))
        print(f"🔍 Found potential ports: {ports}")
        return ports
    
    def test_port(self, port):
        """Test if a port responds to STM32 SCPI commands"""
        try:
            print(f"🧪 Testing port: {port}")
            test_conn = serial.Serial(port, self.baudrate, timeout=2)
            time.sleep(1.5)  # Wait for STM32 to be ready
            
            # Send test command
            test_conn.write(b"*IDN?\r\n")
            time.sleep(0.8)
            response = test_conn.read_all().decode('utf-8', errors='ignore').strip()
            test_conn.close()
            
            # Check if response looks like STM32
            if response and any(keyword in response.upper() for keyword in ['STM', 'POTEN', 'H743']):
                print(f"✅ STM32 found on {port}: {repr(response[:50])}")
                return True
            else:
                print(f"❌ No STM32 response on {port}: {repr(response[:50])}")
                return False
                
        except Exception as e:
            print(f"❌ Port {port} test failed: {e}")
            return False
    
    def auto_connect(self, retry_count=2):
        """Automatically find and connect to STM32"""
        print("🔍 Auto-detecting STM32...")
        
        # First try the last working port
        if self.last_working_port:
            print(f"🔄 Trying last working port: {self.last_working_port}")
            if self.test_port(self.last_working_port):
                if self.connect_to_port(self.last_working_port):
                    return True
        
        # Scan all available ports
        ports = self.find_stm32_ports()
        if not ports:
            print("❌ No serial ports found")
            return False
        
        for port in ports:
            if port == self.last_working_port:
                continue  # Already tried above
                
            if self.test_port(port):
                if self.connect_to_port(port, retry_count):
                    self.last_working_port = port
                    return True
        
        print("❌ STM32 not found on any port")
        return False
    
    def connect_to_port(self, port, retry_count=2):
        """Connect to specific port"""
        for attempt in range(retry_count):
            try:
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                
                if attempt > 0:
                    time.sleep(1.5)
                
                print(f"🔗 Connecting to {port} (attempt {attempt + 1}/{retry_count})")
                self.serial_conn = serial.Serial(port, self.baudrate, timeout=3)
                self.current_port = port
                
                # Test connection
                time.sleep(2)
                self.serial_conn.write(b"*IDN?\r\n")
                time.sleep(0.8)
                test_response = self.serial_conn.read_all()
                
                print(f"✅ Connected to STM32 on {port}")
                return True
                
            except Exception as e:
                print(f"❌ Connection to {port} failed (attempt {attempt + 1}): {e}")
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
        
        return False
    
    def send_command(self, command, max_retries=2):
        """Send SCPI command with auto-reconnection"""
        for retry in range(max_retries + 1):
            try:
                # Check connection
                if not self.serial_conn or not self.serial_conn.is_open:
                    if not self.auto_connect():
                        return {"success": False, "error": "Cannot connect to STM32", "port": None}
                
                # Clear buffers
                self.serial_conn.reset_input_buffer()
                
                # Send command
                cmd_bytes = (command + "\r\n").encode('utf-8')
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()
                
                # Wait and read response
                time.sleep(0.8)
                response_bytes = self.serial_conn.read_all()
                response = response_bytes.decode('utf-8', errors='ignore').strip()
                
                print(f"📤 {command} → 📥 {repr(response[:100])}")
                
                return {
                    "success": True, 
                    "response": response,
                    "port": self.current_port
                }
                
            except (serial.SerialException, OSError) as e:
                print(f"⚠️ Serial error (retry {retry + 1}): {e}")
                
                # Force reconnection
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                
                if retry < max_retries:
                    print("🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    return {"success": False, "error": f"Serial error: {str(e)}", "port": self.current_port}
                    
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return {"success": False, "error": f"Unexpected error: {str(e)}", "port": self.current_port}
        
        return {"success": False, "error": "All retries failed", "port": self.current_port}
    
    def disconnect(self):
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None
        self.current_port = None

# Global controller
scpi = SmartSCPIController()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/scpi', methods=['POST'])
def handle_scpi():
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({"success": False, "error": "No command provided"})
        
        result = scpi.send_command(command)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"})

@app.route('/reconnect', methods=['POST'])
def force_reconnect():
    try:
        scpi.disconnect()
        print("🔌 Disconnected from STM32")
        time.sleep(1)
        
        if scpi.auto_connect(retry_count=3):
            return jsonify({
                "success": True, 
                "message": "STM32 reconnected successfully",
                "port": scpi.current_port
            })
        else:
            return jsonify({"success": False, "error": "Failed to reconnect to STM32"})
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Reconnection error: {str(e)}"})

@app.route('/status')
def status():
    try:
        # Quick connection test
        if scpi.serial_conn and scpi.serial_conn.is_open:
            return jsonify({
                "server": "running",
                "stm32_connected": True,
                "port": scpi.current_port
            })
        else:
            return jsonify({
                "server": "running",
                "stm32_connected": False,
                "port": scpi.current_port
            })
    except Exception as e:
        return jsonify({
            "server": "running", 
            "stm32_connected": False,
            "error": str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting Smart STM32 SCPI Web Server...")
    print("🔍 Auto-detecting STM32 connection...")
    
    # Try initial connection
    if scpi.auto_connect():
        print(f"✅ STM32 Auto-Connected on {scpi.current_port}")
    else:
        print("⚠️ STM32 Not Found - Will auto-detect on first command")
    
    print("🌐 Web server starting on http://192.168.9.76:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)