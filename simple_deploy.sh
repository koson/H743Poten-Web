#!/bin/bash

# Simple deployment using existing C# files
PI_HOST="ben@192.168.9.75"
PROJECT_DIR="/home/ben/dotnet-keysight"

echo "Creating project directory on Pi..."
ssh $PI_HOST "mkdir -p $PROJECT_DIR"

echo "Copying C# source files to Pi..."
scp KeysightController.cs KeysightUSBTMCService_v4.cs USBTMCTest.cs $PI_HOST:$PROJECT_DIR/

echo "Creating simple C# test program on Pi..."
ssh $PI_HOST "cat > $PROJECT_DIR/SimpleTest.cs << 'EOF'
using System;
using System.IO;

class Program
{
    static void Main()
    {
        try
        {
            Console.WriteLine(\"Testing USBTMC connection...\");
            
            using (var device = new FileStream(\"/dev/usbtmc0\", FileMode.Open, FileAccess.ReadWrite))
            {
                // Send *IDN? command
                var command = \"*IDN?\\n\";
                var commandBytes = System.Text.Encoding.ASCII.GetBytes(command);
                device.Write(commandBytes, 0, commandBytes.Length);
                device.Flush();
                
                // Read response
                byte[] buffer = new byte[1024];
                int bytesRead = device.Read(buffer, 0, buffer.Length);
                string response = System.Text.Encoding.ASCII.GetString(buffer, 0, bytesRead);
                
                Console.WriteLine($\"Response: {response.Trim()}\");
                Console.WriteLine(\"Connection successful!\");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($\"Error: {ex.Message}\");
        }
    }
}
EOF"

echo "Compiling simple test program..."
ssh $PI_HOST "cd $PROJECT_DIR && mcs SimpleTest.cs -out:SimpleTest.exe 2>/dev/null || echo 'Mono not available, trying direct execution'"

echo "Running simple test..."
ssh $PI_HOST "cd $PROJECT_DIR && (mono SimpleTest.exe 2>/dev/null || echo 'Testing with direct file access:' && echo '*IDN?' > /dev/usbtmc0 && timeout 3 cat /dev/usbtmc0)"