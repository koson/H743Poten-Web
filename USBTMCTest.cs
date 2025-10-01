using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        try
        {
            Console.WriteLine("Testing USBTMC Communication...");
            
            // Open USBTMC device
            using var device = new FileStream("/dev/usbtmc0", FileMode.Open, FileAccess.ReadWrite);
            Console.WriteLine("✅ Device opened successfully");
            
            // Send *IDN? command
            var command = "*IDN?\n";
            var commandBytes = Encoding.ASCII.GetBytes(command);
            
            Console.WriteLine($"📤 Sending: {command.Trim()}");
            await device.WriteAsync(commandBytes);
            await device.FlushAsync();
            
            // Wait for response
            await Task.Delay(500);
            
            // Read response
            var buffer = new byte[1024];
            var bytesRead = await device.ReadAsync(buffer);
            
            if (bytesRead > 0)
            {
                var response = Encoding.ASCII.GetString(buffer, 0, bytesRead);
                Console.WriteLine($"📥 Response: {response.Trim()}");
                Console.WriteLine($"✅ Communication successful! Bytes read: {bytesRead}");
            }
            else
            {
                Console.WriteLine("❌ No response received");
                
                // Try alternative approach - synchronous read
                Console.WriteLine("Trying synchronous read...");
                device.Position = 0;
                var syncBuffer = new byte[1024];
                var syncBytes = device.Read(syncBuffer, 0, syncBuffer.Length);
                
                if (syncBytes > 0)
                {
                    var syncResponse = Encoding.ASCII.GetString(syncBuffer, 0, syncBytes);
                    Console.WriteLine($"📥 Sync Response: {syncResponse.Trim()}");
                }
            }
            
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Error: {ex.Message}");
            Console.WriteLine($"Stack trace: {ex.StackTrace}");
        }
    }
}