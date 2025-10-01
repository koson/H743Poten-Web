using System.Text;
using System.Net;
using System.Net.Sockets;

namespace PureDotNetScpiServer;

/// <summary>
/// USBTMC Device Communication Handler
/// </summary>
public class USBTMCDevice : IDisposable
{
    private FileStream? _deviceStream;
    private readonly string _devicePath;
    private readonly SemaphoreSlim _semaphore = new(1, 1);

    public USBTMCDevice(string devicePath = "/dev/usbtmc0")
    {
        _devicePath = devicePath;
    }

    public async Task<bool> OpenAsync()
    {
        try
        {
            if (!File.Exists(_devicePath))
            {
                Console.WriteLine($"❌ Device not found: {_devicePath}");
                return false;
            }

            _deviceStream = new FileStream(_devicePath, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
            
            Console.WriteLine($"✅ Opened USBTMC device: {_devicePath}");
            
            // Test connection
            var idn = await SendCommandAsync("*IDN?", retryCount: 2);
            Console.WriteLine($"📡 Device: {idn}");
            
            return !string.IsNullOrEmpty(idn) && !idn.StartsWith("ERROR");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Open failed: {ex.Message}");
            return false;
        }
    }

    public async Task<string> SendCommandAsync(string command, int retryCount = 1)
    {
        await _semaphore.WaitAsync();
        try
        {
            if (_deviceStream == null)
                throw new InvalidOperationException("Device not opened");

            // Handle special reset command with proper sequence
            if (command.Trim().Equals("*RST", StringComparison.OrdinalIgnoreCase))
            {
                // Clear errors before reset
                await SendRawCommandAsync("*CLS");
                await Task.Delay(100);
                
                // Send reset
                await SendRawCommandAsync("*RST");
                await Task.Delay(2000); // Wait for reset to complete
                
                // Clear any errors after reset
                await SendRawCommandAsync("*CLS");
                await Task.Delay(100);
                
                // Reopen device after reset
                await ReopenDeviceAsync();
                
                return "OK - Device Reset";
            }

            for (int i = 0; i <= retryCount; i++)
            {
                try
                {
                    // Send command
                    var commandBytes = Encoding.ASCII.GetBytes(command.TrimEnd('\n') + "\n");
                    await _deviceStream.WriteAsync(commandBytes, 0, commandBytes.Length);
                    await _deviceStream.FlushAsync();

                    // Wait for response if query
                    if (command.Contains('?'))
                    {
                        await Task.Delay(150); // Give device time to respond
                        
                        var buffer = new byte[4096];
                        var bytesRead = await _deviceStream.ReadAsync(buffer, 0, buffer.Length);
                        
                        if (bytesRead > 0)
                        {
                            return Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();
                        }
                    }

                    return "OK";
                }
                catch (TimeoutException) when (i < retryCount)
                {
                    Console.WriteLine($"⚠️  Timeout, attempting recovery... (attempt {i + 1}/{retryCount + 1})");
                    await ReopenDeviceAsync();
                }
                catch (IOException) when (i < retryCount)
                {
                    Console.WriteLine($"⚠️  IO error, attempting recovery... (attempt {i + 1}/{retryCount + 1})");
                    await ReopenDeviceAsync();
                }
            }

            throw new IOException("Command failed after retries");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Command failed: {ex.Message}");
            return $"ERROR: {ex.Message}";
        }
        finally
        {
            _semaphore.Release();
        }
    }

    private async Task ReopenDeviceAsync()
    {
        try
        {
            Console.WriteLine("🔄 Reopening device...");
            _deviceStream?.Dispose();
            await Task.Delay(500);
            _deviceStream = new FileStream(_devicePath, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
            Console.WriteLine("✅ Device reopened");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Failed to reopen device: {ex.Message}");
            throw;
        }
    }

    private async Task SendRawCommandAsync(string command)
    {
        var commandBytes = Encoding.ASCII.GetBytes(command.TrimEnd('\n') + "\n");
        await _deviceStream!.WriteAsync(commandBytes, 0, commandBytes.Length);
        await _deviceStream.FlushAsync();
    }

    public void Dispose()
    {
        try
        {
            // Return device to local mode before closing
            if (_deviceStream != null)
            {
                var localCmd = Encoding.ASCII.GetBytes("SYST:LOC\n");
                _deviceStream.Write(localCmd, 0, localCmd.Length);
                _deviceStream.Flush();
                Thread.Sleep(200);
                Console.WriteLine("🔓 Device returned to local mode on dispose");
            }
        }
        catch
        {
            // Ignore errors during cleanup
        }
        finally
        {
            _deviceStream?.Dispose();
            _semaphore.Dispose();
        }
    }
}

/// <summary>
/// Pure .NET SCPI Server - TCP Socket Server
/// </summary>
public class ScpiTcpServer
{
    private readonly USBTMCDevice _device;
    private readonly int _port;
    private TcpListener? _listener;
    private CancellationTokenSource? _cts;

    public ScpiTcpServer(USBTMCDevice device, int port = 5025)
    {
        _device = device;
        _port = port;
    }

    public async Task StartAsync()
    {
        _cts = new CancellationTokenSource();
        _listener = new TcpListener(IPAddress.Any, _port);
        _listener.Start();

        Console.WriteLine($"🚀 SCPI Server listening on port {_port}");
        Console.WriteLine($"📝 Connect with: telnet 192.168.9.75 {_port}");
        Console.WriteLine($"📝 Or use SCPI commands via TCP socket");
        Console.WriteLine();

        while (!_cts.Token.IsCancellationRequested)
        {
            try
            {
                var client = await _listener.AcceptTcpClientAsync(_cts.Token);
                _ = Task.Run(() => HandleClientAsync(client, _cts.Token), _cts.Token);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Accept error: {ex.Message}");
            }
        }
    }

    private async Task HandleClientAsync(TcpClient client, CancellationToken ct)
    {
        var endpoint = client.Client.RemoteEndPoint?.ToString() ?? "unknown";
        Console.WriteLine($"✅ Client connected: {endpoint}");

        try
        {
            using var stream = client.GetStream();
            var buffer = new byte[4096];
            var receivedData = new StringBuilder();

            // Send welcome message
            var welcome = "SCPI Server Ready\n";
            var welcomeBytes = Encoding.ASCII.GetBytes(welcome);
            await stream.WriteAsync(welcomeBytes, 0, welcomeBytes.Length, ct);

            while (!ct.IsCancellationRequested && client.Connected)
            {
                // Read available data
                var readTask = stream.ReadAsync(buffer, 0, buffer.Length, ct);
                var timeoutTask = Task.Delay(100, ct);
                var completedTask = await Task.WhenAny(readTask, timeoutTask);
                
                int bytesRead;
                if (completedTask == readTask)
                {
                    bytesRead = await readTask;
                    if (bytesRead == 0) break; // Client closed connection (EOF)
                    
                    // Append to buffer
                    receivedData.Append(Encoding.ASCII.GetString(buffer, 0, bytesRead));
                }
                else
                {
                    // Check if client is still connected
                    if (!client.Connected || !stream.CanRead)
                        break;
                    
                    // If no data and buffer is empty, continue waiting
                    if (receivedData.Length == 0)
                        continue;
                    
                    // If we have data but no new data arrived, process what we have
                }

                // Process all complete commands (separated by newlines)
                var data = receivedData.ToString();
                var commands = data.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
                
                // If data doesn't end with newline, keep the last partial command in buffer
                if (!data.EndsWith("\n") && !data.EndsWith("\r") && commands.Length > 0)
                {
                    // Keep last partial command
                    receivedData.Clear();
                    receivedData.Append(commands[^1]);
                    commands = commands[..^1]; // Process all but last
                }
                else
                {
                    receivedData.Clear(); // All commands complete
                }

                // Process each complete command
                foreach (var command in commands)
                {
                    var cmd = command.Trim();
                    if (string.IsNullOrWhiteSpace(cmd))
                        continue;

                    Console.WriteLine($"📨 [{endpoint}] Command: {cmd}");

                    Console.WriteLine($"📨 [{endpoint}] Command: {cmd}");

                    // Handle special commands
                    if (cmd.Equals("QUIT", StringComparison.OrdinalIgnoreCase) ||
                        cmd.Equals("EXIT", StringComparison.OrdinalIgnoreCase))
                    {
                        Console.WriteLine($"👋 [{endpoint}] Client requested disconnect, returning to local mode...");
                        
                        // Return DMM to local mode before disconnect
                        try
                        {
                            await _device.SendCommandAsync("SYST:LOC");
                            await Task.Delay(200);
                            Console.WriteLine($"✅ [{endpoint}] Device returned to local mode");
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"⚠️  [{endpoint}] Failed to return to local mode: {ex.Message}");
                        }
                        
                        var byeBytes = Encoding.ASCII.GetBytes("Device returned to local mode. Goodbye!\n");
                        await stream.WriteAsync(byeBytes, 0, byeBytes.Length, ct);
                        await stream.FlushAsync(ct);
                        return; // Exit handler
                    }

                    if (cmd.Equals("HELP", StringComparison.OrdinalIgnoreCase) ||
                        cmd.Equals("?", StringComparison.OrdinalIgnoreCase))
                    {
                        var help = @"Available Commands:
  *IDN?           - Get device identity
  *RST            - Reset device (safe reset with error clearing)
  *CLS            - Clear status registers
  MEAS:VOLT:DC?   - Measure DC voltage
  MEAS:VOLT:AC?   - Measure AC voltage
  MEAS:CURR:DC?   - Measure DC current
  MEAS:RES?       - Measure resistance
  READ?           - Take a reading
  SYST:ERR?       - Query error queue
  SYST:LOC        - Return device to local mode (unlock front panel)
  LOCAL           - Same as SYST:LOC
  HELP/?          - Show this help
  QUIT/EXIT       - Disconnect and return to local mode
";
                        var helpBytes = Encoding.ASCII.GetBytes(help);
                        await stream.WriteAsync(helpBytes, 0, helpBytes.Length, ct);
                        await stream.FlushAsync(ct);
                        continue;
                    }

                    // Handle LOCAL command alias
                    if (cmd.Equals("LOCAL", StringComparison.OrdinalIgnoreCase))
                    {
                        Console.WriteLine($"🔓 [{endpoint}] Returning device to local mode...");
                        await _device.SendCommandAsync("SYST:LOC");
                        var localBytes = Encoding.ASCII.GetBytes("Device returned to local mode (front panel unlocked)\n");
                        await stream.WriteAsync(localBytes, 0, localBytes.Length, ct);
                        await stream.FlushAsync(ct);
                        continue;
                    }

                    // Check for error query after command
                    bool checkError = !cmd.Contains('?') && 
                                    !cmd.Equals("*CLS", StringComparison.OrdinalIgnoreCase);

                    // Forward to USBTMC device
                    var response = await _device.SendCommandAsync(cmd);
                    Console.WriteLine($"📤 [{endpoint}] Response: {response}");

                    // Send response back to client
                    var responseBytes = Encoding.ASCII.GetBytes(response + "\n");
                    await stream.WriteAsync(responseBytes, 0, responseBytes.Length, ct);
                    await stream.FlushAsync(ct); // Ensure data sent immediately

                    // Check for errors after non-query commands
                    if (checkError && !response.StartsWith("ERROR"))
                    {
                        await Task.Delay(100);
                        var errorCheck = await _device.SendCommandAsync("SYST:ERR?");
                        if (!errorCheck.Contains("No error") && !errorCheck.StartsWith("ERROR"))
                        {
                            Console.WriteLine($"⚠️  [{endpoint}] Device Error: {errorCheck}");
                            var errorBytes = Encoding.ASCII.GetBytes($"Warning: {errorCheck}\n");
                            await stream.WriteAsync(errorBytes, 0, errorBytes.Length, ct);
                            await stream.FlushAsync(ct);
                        }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Client error [{endpoint}]: {ex.Message}");
        }
        finally
        {
            // Always return device to local mode when client disconnects
            try
            {
                await _device.SendCommandAsync("SYST:LOC");
                Console.WriteLine($"🔓 [{endpoint}] Device returned to local mode");
            }
            catch
            {
                // Ignore errors during cleanup
            }
            
            client.Close();
            Console.WriteLine($"👋 Client disconnected: {endpoint}");
        }
    }

    public void Stop()
    {
        _cts?.Cancel();
        _listener?.Stop();
    }
}

/// <summary>
/// Main Program Entry Point
/// </summary>
class Program
{
    static string FindUSBTMCDevice()
    {
        // Try to find available USBTMC devices
        var devices = new[] { "/dev/usbtmc0", "/dev/usbtmc1", "/dev/usbtmc2" };
        
        foreach (var device in devices)
        {
            if (File.Exists(device))
            {
                Console.WriteLine($"🔍 Found USBTMC device: {device}");
                return device;
            }
        }
        
        Console.WriteLine("⚠️  No USBTMC device found, using default: /dev/usbtmc0");
        return "/dev/usbtmc0";
    }

    static async Task Main(string[] args)
    {
        Console.WriteLine("╔══════════════════════════════════════════════╗");
        Console.WriteLine("║   Pure .NET SCPI Server for DMM 34461A      ║");
        Console.WriteLine("║   No Python Required! 🚀                     ║");
        Console.WriteLine("╚══════════════════════════════════════════════╝");
        Console.WriteLine();

        // Try to auto-detect USBTMC device
        var devicePath = FindUSBTMCDevice();
        if (args.Length > 0) devicePath = args[0]; // Override with command line
        
        var port = args.Length > 1 ? int.Parse(args[1]) : 5025;

        Console.WriteLine($"📍 Using device: {devicePath}");
        
        using var device = new USBTMCDevice(devicePath);
        
        Console.WriteLine("🔌 Opening USBTMC device...");
        if (!await device.OpenAsync())
        {
            Console.WriteLine("❌ Failed to open device. Please check:");
            Console.WriteLine("   1. USB cable connected and detected");
            Console.WriteLine($"   2. Device permissions: sudo chmod 666 {devicePath}");
            Console.WriteLine("   3. DMM powered on");
            Console.WriteLine("   4. Try unplugging and replugging USB cable");
            Console.WriteLine();
            Console.WriteLine("💡 Tip: Run 'ls -la /dev/usbtmc*' to see available devices");
            return;
        }

        var server = new ScpiTcpServer(device, port);

        Console.WriteLine();
        Console.WriteLine("Press Ctrl+C to stop server...");
        Console.WriteLine();

        // Handle Ctrl+C gracefully
        Console.CancelKeyPress += (sender, e) =>
        {
            e.Cancel = true;
            Console.WriteLine("\n🛑 Stopping server...");
            server.Stop();
        };

        await server.StartAsync();

        Console.WriteLine("👋 Server stopped. Goodbye!");
    }
}