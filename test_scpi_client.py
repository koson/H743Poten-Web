#!/usr/bin/env python3
"""
Test client for Pure .NET SCPI Server
Demonstrates how to use the server from Python
"""

import socket
import time

def test_scpi_server():
    HOST = '192.168.9.75'
    PORT = 5025
    
    print("🔌 Connecting to SCPI Server...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    
    # Read welcome message
    welcome = sock.recv(1024).decode()
    print(f"📨 {welcome.strip()}")
    
    commands = [
        "HELP",
        "*IDN?",
        "MEAS:VOLT:DC?",
        "*RST",
        "SYST:ERR?",
        "QUIT"
    ]
    
    for cmd in commands:
        print(f"\n📤 Sending: {cmd}")
        sock.send(f"{cmd}\n".encode())
        time.sleep(0.5)
        
        response = sock.recv(4096).decode()
        print(f"📥 Response: {response.strip()}")
        
        if cmd == "*RST":
            print("⏱️  Waiting for reset to complete...")
            time.sleep(2)
    
    sock.close()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_scpi_server()