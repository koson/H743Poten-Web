using System.Text;

namespace Keysight34461A.TestApp.Services;

public interface IKeysightService
{
    Task<bool> ConnectAsync();
    Task<string> SendCommandAsync(string command);
    Task<double> MeasureVoltageAsync();
    Task DisconnectAsync();
    bool IsConnected { get; }
}

public class KeysightUSBTMCService : IKeysightService, IDisposable
{
    private FileStream? _usbtmcStream;
    private readonly ILogger<KeysightUSBTMCService> _logger;
    private bool _isConnected = false;
    private string? _devicePath;

    public bool IsConnected => _isConnected;

    public KeysightUSBTMCService(ILogger<KeysightUSBTMCService> logger)
    {
        _logger = logger;
    }

    public async Task<bool> ConnectAsync()
    {
        try
        {
            // Try to find USBTMC devices
            var usbtmcDevices = Directory.GetFiles("/dev", "usbtmc*");
            _logger.LogInformation($"Available USBTMC devices: {string.Join(", ", usbtmcDevices)}");

            foreach (var device in usbtmcDevices)
            {
                try
                {
                    _logger.LogInformation($"Trying to connect to {device}");
                    
                    // Open USBTMC device for read/write
                    _usbtmcStream = new FileStream(device, FileMode.Open, FileAccess.ReadWrite);
                    _devicePath = device;

                    // Test with *IDN? command
                    var response = await SendCommandAsync("*IDN?");
                    if (!string.IsNullOrEmpty(response) && 
                        (response.Contains("34461A") || response.Contains("Keysight")))
                    {
                        _isConnected = true;
                        _logger.LogInformation($"Keysight 34461A found on {device}: {response.Trim()}");
                        return true;
                    }

                    // If no valid response, close and try next device
                    _usbtmcStream.Close();
                    _usbtmcStream.Dispose();
                    _usbtmcStream = null;
                }
                catch (Exception ex)
                {
                    _logger.LogWarning($"Failed to connect to {device}: {ex.Message}");
                    _usbtmcStream?.Close();
                    _usbtmcStream?.Dispose();
                    _usbtmcStream = null;
                }
            }

            _logger.LogWarning("Keysight 34461A not found on any USBTMC device");
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Connection failed");
            return false;
        }
    }

    public async Task<string> SendCommandAsync(string command)
    {
        if (!_isConnected || _usbtmcStream == null)
            throw new InvalidOperationException("Not connected to device");

        try
        {
            // Send command to USBTMC device
            var commandBytes = Encoding.ASCII.GetBytes(command + "\n");
            await _usbtmcStream.WriteAsync(commandBytes);
            await _usbtmcStream.FlushAsync();

            // For query commands, read response
            if (command.EndsWith("?"))
            {
                // Wait a bit for response
                await Task.Delay(100);

                // Read response
                var buffer = new byte[1024];
                var bytesRead = await _usbtmcStream.ReadAsync(buffer);
                
                if (bytesRead > 0)
                {
                    var response = Encoding.ASCII.GetString(buffer, 0, bytesRead);
                    return response.Trim('\n', '\r', '\0');
                }
            }

            return "OK";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"Failed to send command: {command}");
            throw;
        }
    }

    public async Task<double> MeasureVoltageAsync()
    {
        var response = await SendCommandAsync("MEAS:VOLT:DC?");
        if (double.TryParse(response, out double voltage))
        {
            return voltage;
        }
        throw new InvalidDataException($"Invalid voltage reading: {response}");
    }

    public async Task DisconnectAsync()
    {
        if (_usbtmcStream != null)
        {
            _usbtmcStream.Close();
            _usbtmcStream.Dispose();
            _usbtmcStream = null;
        }
        _isConnected = false;
        _devicePath = null;
        await Task.CompletedTask;
    }

    public void Dispose()
    {
        _usbtmcStream?.Close();
        _usbtmcStream?.Dispose();
    }
}