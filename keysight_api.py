#!/usr/bin/env python3

from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/api/keysight/connect', methods=['POST'])
def connect():
    try:
        # Check if USBTMC device exists
        if not os.path.exists('/dev/usbtmc0'):
            return jsonify({"success": False, "message": "USBTMC device not found"}), 400
        
        # Test connection by sending *IDN?
        with open('/dev/usbtmc0', 'wb') as device:
            device.write(b'*IDN?\n')
            device.flush()
        
        with open('/dev/usbtmc0', 'rb') as device:
            response = device.read(1024).decode('ascii').strip()
        
        if 'Keysight' in response:
            return jsonify({"success": True, "message": f"Connected: {response}"})
        else:
            return jsonify({"success": False, "message": "Invalid device response"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Connection failed: {str(e)}"}), 500

@app.route('/api/keysight/command', methods=['POST'])
def send_command():
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({"success": False, "message": "No command specified"}), 400
        
        # Send command
        with open('/dev/usbtmc0', 'wb') as device:
            device.write(f'{command}\n'.encode())
            device.flush()
        
        # Read response if it's a query
        if '?' in command:
            with open('/dev/usbtmc0', 'rb') as device:
                response = device.read(1024).decode('ascii').strip()
            return jsonify({"success": True, "response": response})
        else:
            return jsonify({"success": True, "message": "Command sent"})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/keysight/voltage', methods=['GET'])
def get_voltage():
    try:
        # Send READ? command
        with open('/dev/usbtmc0', 'wb') as device:
            device.write(b'READ?\n')
            device.flush()
        
        with open('/dev/usbtmc0', 'rb') as device:
            response = device.read(1024).decode('ascii').strip()
        
        voltage = float(response)
        return jsonify({"success": True, "voltage": voltage})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)