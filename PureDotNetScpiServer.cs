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
            var idn = await SendCommandAsync("*IDN?");
            Console.WriteLine($"📡 Device: {idn}");
            
            return !string.IsNullOrEmpty(idn);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Open failed: {ex.Message}");
            return false;
        }
    }

    public async Task<string> SendCommandAsync(string command)
    {
        await _semaphore.WaitAsync();
        try
        {
            if (_deviceStream == null)
                throw new InvalidOperationException("Device not opened");

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

    public void Dispose()
    {
        _deviceStream?.Dispose();
        _semaphore.Dispose();
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

            // Send welcome message
            var welcome = "SCPI Server Ready\n";
            var welcomeBytes = Encoding.ASCII.GetBytes(welcome);
            await stream.WriteAsync(welcomeBytes, 0, welcomeBytes.Length, ct);

            while (!ct.IsCancellationRequested && client.Connected)
            {
                var bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length, ct);
                if (bytesRead == 0) break;

                var command = Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();
                
                if (string.IsNullOrWhiteSpace(command))
                    continue;

                Console.WriteLine($"📨 [{endpoint}] Command: {command}");

                // Handle special commands
                if (command.Equals("QUIT", StringComparison.OrdinalIgnoreCase))
                {
                    var byeBytes = Encoding.ASCII.GetBytes("Goodbye!\n");
                    await stream.WriteAsync(byeBytes, 0, byeBytes.Length, ct);
                    break;
                }

                // Forward to USBTMC device
                var response = await _device.SendCommandAsync(command);
                Console.WriteLine($"📤 [{endpoint}] Response: {response}");

                // Send response back to client
                var responseBytes = Encoding.ASCII.GetBytes(response + "\n");
                await stream.WriteAsync(responseBytes, 0, responseBytes.Length, ct);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Client error [{endpoint}]: {ex.Message}");
        }
        finally
        {
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
    static async Task Main(string[] args)
    {
        Console.WriteLine("╔══════════════════════════════════════════════╗");
        Console.WriteLine("║   Pure .NET SCPI Server for DMM 34461A      ║");
        Console.WriteLine("║   No Python Required! 🚀                     ║");
        Console.WriteLine("╚══════════════════════════════════════════════╝");
        Console.WriteLine();

        var devicePath = args.Length > 0 ? args[0] : "/dev/usbtmc0";
        var port = args.Length > 1 ? int.Parse(args[1]) : 5025;

        using var device = new USBTMCDevice(devicePath);
        
        Console.WriteLine("🔌 Opening USBTMC device...");
        if (!await device.OpenAsync())
        {
            Console.WriteLine("❌ Failed to open device. Please check:");
            Console.WriteLine("   1. USB cable connected");
            Console.WriteLine("   2. Device permissions: sudo chmod 666 /dev/usbtmc0");
            Console.WriteLine("   3. DMM powered on");
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