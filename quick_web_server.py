#!/usr/bin/env python3
"""
Quick Flask Web Server for SCPI STM32 Testing
Minimal dependencies - only Flask required
"""

from flask import Flask, render_template_string, request, jsonify
import serial
import time
import json
import os
import traceback

app = Flask(__name__)

# HTML template for web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>STM32 SCPI Web Interface</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .panel { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .success { background-color: #d4edda; border-color: #c3e6cb; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; }
        .command-panel { background-color: #e7f3ff; }
        .data-panel { background-color: #f8f9fa; }
        button { background: #007bff; color: white; border: none; padding: 8px 15px; cursor: pointer; border-radius: 3px; }
        button:hover { background: #0056b3; }
        .status { font-weight: bold; }
        textarea { width: 100%; height: 200px; font-family: monospace; }
        input[type="text"] { width: 200px; padding: 5px; }
        .log { max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 10px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 STM32 SCPI Web Interface</h1>
        
        <div class="panel command-panel">
            <h3>📤 SCPI Commands</h3>
            <button onclick="sendCommand('*IDN?')">Device ID</button>
            <button onclick="sendCommand('POTEn:CV:STATUS?')">CV Status</button>
            <button onclick="startCV()">Start CV</button>
            <button onclick="sendCommand('POTEn:CV:DATA?')">Get Data</button>
            <button onclick="reconnectSTM32()" style="background: #28a745;">🔄 Reconnect</button>
            <button onclick="clearLog()">Clear Log</button>
            <br><br>
            
            <div>
                <label>Custom Command:</label>
                <input type="text" id="customCmd" placeholder="Enter SCPI command">
                <button onclick="sendCustomCommand()">Send</button>
            </div>
            
            <div style="margin-top: 10px;">
                <label>CV Parameters:</label>
                Start: <input type="text" id="startV" value="-0.5" style="width: 60px;">
                End: <input type="text" id="endV" value="0.5" style="width: 60px;">
                Step: <input type="text" id="stepV" value="0.1" style="width: 60px;">
                Cycles: <input type="text" id="cycles" value="1" style="width: 60px;">
            </div>
        </div>
        
        <div class="panel data-panel">
            <h3>📊 Response Log</h3>
            <div id="responseLog" class="log"></div>
        </div>
        
        <div class="panel">
            <h3>📈 Data Visualization</h3>
            <textarea id="dataDisplay" placeholder="CSV data will appear here..."></textarea>
        </div>
    </div>

    <script>
        function log(message, type = 'info') {
            const logDiv = document.getElementById('responseLog');
            const timestamp = new Date().toLocaleTimeString();
            const className = type === 'error' ? 'error' : type === 'success' ? 'success' : '';
            logDiv.innerHTML += `<div class="${className}">[${timestamp}] ${message}</div>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function sendCommand(command) {
            log(`📤 Sending: ${command}`, 'info');
            fetch('/scpi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    log(`📥 Response: ${data.response}`, 'success');
                    if (data.response.includes('CSV:')) {
                        document.getElementById('dataDisplay').value = data.response;
                    }
                } else {
                    log(`❌ Error: ${data.error}`, 'error');
                }
            })
            .catch(error => {
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
        
        function clearLog() {
            document.getElementById('responseLog').innerHTML = '';
            document.getElementById('dataDisplay').value = '';
        }
        
        function reconnectSTM32() {
            log('🔄 Forcing STM32 reconnection...', 'info');
            fetch('/reconnect', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    log('✅ STM32 Reconnected Successfully', 'success');
                    setTimeout(() => sendCommand('*IDN?'), 1000);
                } else {
                    log(`❌ Reconnection failed: ${data.error}`, 'error');
                }
            })
            .catch(error => log(`❌ Reconnection Error: ${error}`, 'error'));
        }
        
        // Auto-refresh status every 3 seconds when measurement is running
        let statusInterval;
        function startStatusMonitoring() {
            if (statusInterval) clearInterval(statusInterval);
            statusInterval = setInterval(() => {
                sendCommand('POTEn:CV:STATUS?');
            }, 3000);
        }
        
        // Initialize
        window.onload = function() {
            log('🚀 STM32 SCPI Web Interface Started', 'success');
            setTimeout(() => sendCommand('*IDN?'), 2000);  // Delay initial command
        };
    </script>
</body>
</html>
'''

class SCPIController:
    def __init__(self, port='/dev/ttyACM1', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.last_error_time = 0
    
    def connect(self, retry_count=3):
        """Connect to STM32 with retry logic"""
        for attempt in range(retry_count):
            try:
                # Force close any existing connection
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                
                # Wait a bit between attempts
                if attempt > 0:
                    time.sleep(1)
                
                print(f"🔗 Connection attempt {attempt + 1}/{retry_count} to {self.port}")
                self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=3)
                
                # Test the connection with a simple command
                time.sleep(2)  # Wait for STM32 to be ready after reset
                self.serial_conn.write(b"*IDN?\r\n")
                time.sleep(0.5)
                test_response = self.serial_conn.read_all()
                
                print(f"✅ STM32 Connected (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
        
        return False
    
    def send_command(self, command, max_retries=2):
        """Send SCPI command with automatic reconnection on failure"""
        for retry in range(max_retries + 1):
            try:
                # Check if we need to connect/reconnect
                if not self.serial_conn or not self.serial_conn.is_open:
                    if not self.connect():
                        return {"success": False, "error": "Cannot connect to STM32 after multiple attempts"}
                
                # Clear input buffer before sending
                self.serial_conn.reset_input_buffer()
                
                # Send command
                cmd_bytes = (command + "\r\n").encode('utf-8')
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()  # Ensure data is sent
                
                # Wait for response
                time.sleep(0.8)  # Increased wait time for STM32 processing
                
                # Read response with timeout handling
                response_bytes = self.serial_conn.read_all()
                response = response_bytes.decode('utf-8', errors='ignore').strip()
                
                # If we get here without exception, command succeeded
                print(f"📤 Command: {command}")
                print(f"📥 Response: {repr(response[:100])}")
                
                return {"success": True, "response": response}
                
            except (serial.SerialException, OSError) as e:
                print(f"⚠️  Serial error on retry {retry + 1}: {e}")
                
                # Force close and set to None to trigger reconnection
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                    self.serial_conn = None
                
                # If this is not the last retry, wait before trying again
                if retry < max_retries:
                    print(f"🔄 Retrying command in 2 seconds...")
                    time.sleep(2)
                else:
                    return {"success": False, "error": f"Serial communication failed: {str(e)}"}
                    
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}
        
        return {"success": False, "error": "Command failed after all retries"}
    
    def disconnect(self):
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None

# Global SCPI controller
scpi = SCPIController()

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
    """Force reconnection to STM32"""
    try:
        # Disconnect first
        scpi.disconnect()
        print("🔌 Disconnected from STM32")
        
        # Wait a moment
        time.sleep(1)
        
        # Try to reconnect
        if scpi.connect(retry_count=5):
            return jsonify({"success": True, "message": "STM32 reconnected successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to reconnect to STM32"})
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Reconnection error: {str(e)}"})

@app.route('/status')
def status():
    """Health check endpoint"""
    try:
        # Test connection
        result = scpi.send_command("*IDN?")
        return jsonify({
            "server": "running",
            "stm32_connected": result["success"],
            "port": scpi.port
        })
    except Exception as e:
        return jsonify({
            "server": "running", 
            "stm32_connected": False,
            "error": str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting STM32 SCPI Web Server...")
    print(f"📡 Connecting to STM32 on {scpi.port}")
    
    # Test initial connection
    if scpi.connect():
        print("✅ STM32 Connected Successfully")
    else:
        print("⚠️  STM32 Not Connected - Will retry on first command")
    
    print("🌐 Web server starting on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)