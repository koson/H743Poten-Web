using Poten2501.Services;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO.Ports;
using Poten2501.Platforms.Windows.Services;


namespace Poten2501.Platforms.Windows.Services
{
    public class WindowsSerialPortService : ISerialPortService
    {
        private SerialPort _serialPort;

        public List<string> GetAvailablePorts()
        {
            return SerialPort.GetPortNames().ToList();
        }

        public bool OpenPort(string portName, int baudRate, int dataBits, StopBits stopBits, Parity parity)
        {
            try
            {
                _serialPort = new SerialPort(portName, baudRate, parity, dataBits, stopBits);
                _serialPort.DataReceived += SerialPort_DataReceived;
                _serialPort.Open();
                IsOpen = _serialPort.IsOpen;
                return IsOpen;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error opening serial port: {ex.Message}");
                return false;
            }
        }

        public void ClosePort()
        {
            if (_serialPort != null && _serialPort.IsOpen)
            {
                _serialPort.DataReceived -= SerialPort_DataReceived;
                _serialPort.Close();
                IsOpen= false;
            }
        }

        public void WriteData(byte[] data)
        {
            if (_serialPort != null && _serialPort.IsOpen)
            {
                _serialPort.Write(data, 0, data.Length);
            }
        }

        public bool IsOpen { get; set; }




        public event EventHandler<byte[]> DataReceived;

        private void SerialPort_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            if (_serialPort != null)
            {
                int bytesToRead = _serialPort.BytesToRead;
                byte[] data = new byte[bytesToRead];
                _serialPort.Read(data, 0, bytesToRead);
                DataReceived?.Invoke(this, data);
            }
        }
    }
}
