#!/usr/bin/env python3
"""
SSH-based SCPI Web Server
Local Flask server that connects to remote STM32 via SSH
"""

from flask import Flask, render_template_string, request, jsonify
import subprocess
import time
import json
import threading
import re

app = Flask(__name__)

# Configuration
REMOTE_HOST = "koson@192.168.9.76"
REMOTE_PATH = "/home/koson/H743Poten/H743Poten-Web"

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>SSH STM32 SCPI Web Interface</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; margin: 0 auto; 
            background: white; padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { 
            color: #333; text-align: center; 
            margin-bottom: 30px; 
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .panel { 
            border: 2px solid #e1e5e9; 
            margin: 20px 0; padding: 20px; 
            border-radius: 10px; 
            background: #f8f9fa;
        }
        .success { 
            background: linear-gradient(45deg, #d4edda, #c3e6cb); 
            border-color: #28a745; 
            color: #155724; 
        }
        .error { 
            background: linear-gradient(45deg, #f8d7da, #f5c6cb); 
            border-color: #dc3545; 
            color: #721c24; 
        }
        .info { 
            background: linear-gradient(45deg, #d1ecf1, #bee5eb); 
            border-color: #17a2b8; 
            color: #0c5460; 
        }
        .warning { 
            background: linear-gradient(45deg, #fff3cd, #ffeaa7); 
            border-color: #ffc107; 
            color: #856404; 
        }
        button { 
            background: linear-gradient(45deg, #007bff, #0056b3); 
            color: white; border: none; 
            padding: 12px 24px; cursor: pointer; 
            border-radius: 8px; margin: 8px; 
            font-size: 14px; font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,123,255,0.3);
        }
        button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 12px rgba(0,123,255,0.4);
        }
        .reconnect-btn { 
            background: linear-gradient(45deg, #28a745, #1e7e34); 
            box-shadow: 0 4px 8px rgba(40,167,69,0.3);
        }
        .clear-btn { 
            background: linear-gradient(45deg, #6c757d, #545b62); 
            box-shadow: 0 4px 8px rgba(108,117,125,0.3);
        }
        .start-btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            box-shadow: 0 4px 8px rgba(255,107,107,0.3);
        }
        textarea { 
            width: 100%; height: 250px; 
            font-family: 'Courier New', monospace; 
            border: 2px solid #dee2e6; 
            border-radius: 8px; padding: 15px; 
            background: #f8f9fa;
            font-size: 13px;
            resize: vertical;
        }
        .log { 
            max-height: 500px; overflow-y: auto; 
            background: #2d3748; color: #e2e8f0; 
            padding: 20px; border: 2px solid #4a5568; 
            border-radius: 10px; 
            font-family: 'Courier New', monospace; 
            font-size: 13px; line-height: 1.4;
        }
        input[type="text"] { 
            padding: 10px; border: 2px solid #dee2e6; 
            border-radius: 6px; margin: 5px; 
            font-size: 14px;
        }
        .status-indicator { 
            display: inline-block; width: 16px; height: 16px; 
            border-radius: 50%; margin-right: 10px; 
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .status-connected { 
            background: linear-gradient(45deg, #28a745, #20c997); 
        }
        .status-disconnected { 
            background: linear-gradient(45deg, #dc3545, #e74c3c); 
        }
        .status-connecting { 
            background: linear-gradient(45deg, #ffc107, #fd7e14); 
            animation: pulse 1.5s infinite; 
        }
        @keyframes pulse { 
            0%, 100% { opacity: 1; } 
            50% { opacity: 0.4; } 
        }
        .connection-info { 
            background: #e9ecef; padding: 15px; 
            border-radius: 8px; margin: 15px 0; 
            font-family: 'Courier New', monospace; 
            border-left: 4px solid #007bff;
        }
        .cmd-group {
            display: flex; flex-wrap: wrap; gap: 10px;
            margin: 15px 0;
        }
        .param-group {
            background: #f1f3f4; 
            padding: 15px; border-radius: 8px; 
            margin: 10px 0;
        }
        .log-entry {
            margin: 5px 0; padding: 8px;
            border-radius: 4px;
        }
        .log-info { background: rgba(23, 162, 184, 0.1); }
        .log-success { background: rgba(40, 167, 69, 0.1); }
        .log-error { background: rgba(220, 53, 69, 0.1); }
        .log-warning { background: rgba(255, 193, 7, 0.1); }
    </style>
</head>
<body>
<div class="container">
    <h1>🔬 SSH STM32 SCPI Web Interface</h1>
    
    <div class="panel info">
        <h3>📡 Connection Status</h3>
        <div>
            <span class="status-indicator status-disconnected" id="statusIndicator"></span>
            <strong id="statusText">Initializing SSH connection...</strong>
        </div>
        <div class="connection-info">
            <div>🖥️ Remote Host: <strong>koson@192.168.9.76</strong></div>
            <div>📂 Remote Path: <strong>/home/koson/H743Poten/H743Poten-Web</strong></div>
            <div>🔌 STM32 Port: <strong id="stm32Port">Auto-detecting...</strong></div>
        </div>
    </div>

    <div class="panel">
        <h3>📤 SCPI Commands</h3>
        <div class="cmd-group">
            <button onclick="sendCommand('*IDN?')">🆔 Device ID</button>
            <button onclick="sendCommand('POTEn:CV:STATUS?')">📊 CV Status</button>
            <button onclick="startCV()" class="start-btn">▶️ Start CV</button>
            <button onclick="sendCommand('POTEn:CV:DATA?')">📈 Get Data</button>
            <button onclick="reconnectSSH()" class="reconnect-btn">🔄 Reconnect SSH</button>
            <button onclick="clearLog()" class="clear-btn">🗑️ Clear Log</button>
        </div>

        <div class="param-group">
            <h4>⚙️ CV Parameters</h4>
            <div>
                <label>Start V:</label> <input type="text" id="startV" value="-0.5" style="width: 80px;">
                <label>End V:</label> <input type="text" id="endV" value="0.5" style="width: 80px;">
                <label>Step V:</label> <input type="text" id="stepV" value="0.1" style="width: 80px;">
                <label>Cycles:</label> <input type="text" id="cycles" value="1" style="width: 60px;">
            </div>
        </div>

        <div class="param-group">
            <h4>💻 Custom Command</h4>
            <input type="text" id="customCmd" placeholder="Enter SCPI command" style="width: 400px;">
            <button onclick="sendCustomCommand()">📤 Send Command</button>
        </div>
    </div>

    <div class="panel">
        <h3>📊 Command Log</h3>
        <div id="responseLog" class="log"></div>
    </div>

    <div class="panel">
        <h3>📈 CSV Data Output</h3>
        <textarea id="dataDisplay" placeholder="CSV measurement data will appear here..."></textarea>
    </div>
</div>

<script>
let connectionStatus = 'disconnected';

function updateStatus(status, port = null) {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const portDisplay = document.getElementById('stm32Port');
    
    indicator.className = 'status-indicator status-' + status;
    connectionStatus = status;
    
    const statusMessages = {
        'connected': '✅ SSH Connected - STM32 Ready',
        'connecting': '🔄 Connecting via SSH...',
        'disconnected': '❌ SSH Disconnected'
    };
    
    statusText.textContent = statusMessages[status] || 'Unknown Status';
    
    if (port) {
        portDisplay.textContent = port;
    }
}

function log(message, type = 'info') {
    const logDiv = document.getElementById('responseLog');
    const timestamp = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry log-' + type;
    logEntry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
    
    logDiv.appendChild(logEntry);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function sendCommand(command) {
    log(`📤 Sending SSH command: ${command}`, 'info');
    updateStatus('connecting');
    
    fetch('/ssh-scpi', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: command})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateStatus('connected', data.port);
            log(`📥 Response: ${data.response}`, 'success');
            
            // Handle CSV data
            if (data.response.includes('CSV:') || data.response.includes(',')) {
                document.getElementById('dataDisplay').value = data.response;
                log('📊 CSV data loaded into display area', 'info');
            }
        } else {
            updateStatus('disconnected');
            log(`❌ SSH Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        updateStatus('disconnected');
        log(`❌ Network Error: ${error}`, 'error');
    });
}

function sendCustomCommand() {
    const cmd = document.getElementById('customCmd').value.trim();
    if (cmd) {
        sendCommand(cmd);
        document.getElementById('customCmd').value = '';
    } else {
        log('⚠️ Please enter a command first', 'warning');
    }
}

function startCV() {
    const startV = document.getElementById('startV').value;
    const endV = document.getElementById('endV').value;
    const stepV = document.getElementById('stepV').value;
    const cycles = document.getElementById('cycles').value;
    
    const command = `POTEn:CV:Start:ALL ${startV},${endV},${stepV},${cycles}`;
    log(`🚀 Starting CV measurement: ${startV}V to ${endV}V, step ${stepV}V, ${cycles} cycles`, 'info');
    sendCommand(command);
}

function reconnectSSH() {
    log('🔄 Forcing SSH reconnection...', 'warning');
    updateStatus('connecting');
    
    fetch('/reconnect', {method: 'POST'})
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateStatus('connected');
            log('✅ SSH reconnection successful', 'success');
            setTimeout(() => sendCommand('*IDN?'), 1000);
        } else {
            updateStatus('disconnected');
            log(`❌ SSH reconnection failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        updateStatus('disconnected');
        log(`❌ Reconnection error: ${error}`, 'error');
    });
}

function clearLog() {
    document.getElementById('responseLog').innerHTML = '';
    document.getElementById('dataDisplay').value = '';
    log('🗑️ Log and data display cleared', 'info');
}

// Initialize
window.onload = function() {
    log('🚀 SSH STM32 SCPI Web Interface Started', 'info');
    log('🔧 Connecting to remote STM32 via SSH...', 'info');
    updateStatus('connecting');
    
    // Test connection after 2 seconds
    setTimeout(() => {
        sendCommand('*IDN?');
    }, 2000);
};

// Status monitoring
setInterval(() => {
    if (connectionStatus === 'connected') {
        fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (!data.ssh_connected) {
                updateStatus('disconnected');
                log('⚠️ SSH connection lost', 'warning');
            }
        })
        .catch(() => {
            // Don't log network errors during status checks
        });
    }
}, 15000); // Check every 15 seconds
</script>
</body>
</html>'''

class SSHSCPIController:
    def __init__(self, remote_host=REMOTE_HOST, remote_path=REMOTE_PATH):
        self.remote_host = remote_host
        self.remote_path = remote_path
        self.last_port = None
        
    def execute_ssh_command(self, command, timeout=30):
        """Execute command on remote server via SSH"""
        try:
            ssh_cmd = [
                'ssh', 
                '-o', 'ConnectTimeout=10',
                '-o', 'ServerAliveInterval=5',
                '-o', 'ServerAliveCountMax=3',
                self.remote_host,
                f'cd {self.remote_path} && source poten-env/bin/activate && {command}'
            ]
            
            print(f"🔧 SSH Command: {' '.join(ssh_cmd)}")
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"✅ SSH Success: {repr(output[:100])}")
                return {"success": True, "output": output}
            else:
                error = result.stderr.strip() or result.stdout.strip()
                print(f"❌ SSH Error (code {result.returncode}): {error}")
                return {"success": False, "error": f"SSH error: {error}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "SSH command timeout"}
        except Exception as e:
            print(f"❌ SSH Exception: {e}")
            return {"success": False, "error": f"SSH exception: {str(e)}"}
    
    def find_stm32_port(self):
        """Find STM32 port on remote server"""
        result = self.execute_ssh_command("ls -la /dev/tty* | grep -E '(USB|ACM)'", timeout=10)
        if result["success"]:
            # Parse output to find port
            lines = result["output"].split('\n')
            for line in lines:
                if '/dev/ttyACM' in line or '/dev/ttyUSB' in line:
                    # Extract port name
                    port_match = re.search(r'/dev/(tty(?:ACM|USB)\d+)', line)
                    if port_match:
                        port = f"/dev/{port_match.group(1)}"
                        self.last_port = port
                        return port
        return None
    
    def send_scpi_command(self, scpi_command):
        """Send SCPI command to remote STM32"""
        try:
            # First, find the STM32 port
            port = self.find_stm32_port()
            if not port:
                return {"success": False, "error": "STM32 port not found", "port": None}
            
            # Create temporary Python script on remote server
            script_content = f'''import serial
import time
try:
    ser = serial.Serial("{port}", 115200, timeout=3)
    time.sleep(1.5)
    
    ser.write(b"{scpi_command}\\r\\n")
    ser.flush()
    time.sleep(1.2)
    
    response = ser.read_all().decode("utf-8", errors="ignore").strip()
    ser.close()
    
    print("SCPI_RESPONSE:", response)
except Exception as e:
    print("SCPI_ERROR:", str(e))
'''
            
            # Create and execute script via SSH
            import uuid
            script_name = f"temp_scpi_{uuid.uuid4().hex[:8]}.py"
            
            # Step 1: Create the script file using heredoc
            create_cmd = f"cat > {script_name} << 'EOF'\n{script_content}\nEOF"
            create_result = self.execute_ssh_command(create_cmd, timeout=10)
            
            if not create_result["success"]:
                return {"success": False, "error": f"Failed to create script: {create_result['error']}", "port": port}
            
            # Step 2: Execute the script
            result = self.execute_ssh_command(f'python3 {script_name}', timeout=15)
            
            # Step 3: Clean up the script file
            self.execute_ssh_command(f'rm -f {script_name}', timeout=5)
            
            if result["success"]:
                output = result["output"]
                
                # Parse response
                if "SCPI_RESPONSE:" in output:
                    response = output.split("SCPI_RESPONSE:", 1)[1].strip()
                    
                    # Clean up debug output to extract actual SCPI response
                    lines = response.split('\n')
                    cleaned_response = []
                    
                    for line in lines:
                        # Skip debug lines that start with 🔤, CDC:, 🔍
                        if not any(line.strip().startswith(prefix) for prefix in ['🔤', 'CDC:', '🔍', 'SCPI_Parse:']):
                            if line.strip():  # Only non-empty lines
                                cleaned_response.append(line.strip())
                    
                    # Join meaningful response lines
                    final_response = '\n'.join(cleaned_response) if cleaned_response else response
                    
                    return {
                        "success": True, 
                        "response": final_response,
                        "port": port
                    }
                elif "SCPI_ERROR:" in output:
                    error = output.split("SCPI_ERROR:", 1)[1].strip()
                    return {
                        "success": False, 
                        "error": f"SCPI error: {error}",
                        "port": port
                    }
                else:
                    return {
                        "success": False, 
                        "error": f"Unexpected output: {output}",
                        "port": port
                    }
            else:
                return {
                    "success": False, 
                    "error": result["error"],
                    "port": port
                }
                
        except Exception as e:
            return {
                "success": False, 
                "error": f"SSH SCPI error: {str(e)}",
                "port": self.last_port
            }
    
    def test_connection(self):
        """Test SSH connection to remote server"""
        result = self.execute_ssh_command("echo 'SSH_TEST_OK'", timeout=10)
        return result["success"] and "SSH_TEST_OK" in result.get("output", "")

# Global controller
ssh_scpi = SSHSCPIController()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ssh-scpi', methods=['POST'])
def handle_ssh_scpi():
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({"success": False, "error": "No command provided"})
        
        print(f"🔧 Processing SCPI command: {command}")
        result = ssh_scpi.send_scpi_command(command)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({"success": False, "error": f"Server error: {str(e)}"})

@app.route('/reconnect', methods=['POST'])
def force_reconnect():
    try:
        print("🔄 Testing SSH reconnection...")
        if ssh_scpi.test_connection():
            return jsonify({
                "success": True, 
                "message": "SSH connection verified"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "SSH connection test failed"
            })
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": f"Reconnection error: {str(e)}"
        })

@app.route('/status')
def status():
    try:
        ssh_connected = ssh_scpi.test_connection()
        return jsonify({
            "server": "running",
            "ssh_connected": ssh_connected,
            "remote_host": ssh_scpi.remote_host,
            "stm32_port": ssh_scpi.last_port
        })
    except Exception as e:
        return jsonify({
            "server": "running", 
            "ssh_connected": False,
            "error": str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting SSH STM32 SCPI Web Server...")
    print(f"🔗 Remote Host: {REMOTE_HOST}")
    print(f"📂 Remote Path: {REMOTE_PATH}")
    
    # Test initial SSH connection
    print("🧪 Testing SSH connection...")
    if ssh_scpi.test_connection():
        print("✅ SSH Connection OK")
    else:
        print("⚠️ SSH Connection Failed - Will retry on first command")
    
    print("🌐 Local web server starting on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)