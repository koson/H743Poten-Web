using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.IO.Ports;


namespace Poten2501.Services
{
    public interface ISerialPortService
    {
        List<string> GetAvailablePorts();
        bool OpenPort(string portName, int baudRate, int dataBits, StopBits stopBits, Parity parity);
        void ClosePort();
        void WriteData(byte[] data);
        bool IsOpen { get; set; }
        event EventHandler<byte[]> DataReceived;
    }
}
