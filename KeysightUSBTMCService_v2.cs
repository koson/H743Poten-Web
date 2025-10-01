using System.Text;

namespace Keysight34461A.TestApp.Services;

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
                    _usbtmcStream = new FileStream(device, FileMode.Open, FileAccess.ReadWrite, FileShare.ReadWrite);
                    _devicePath = device;

                    // Test with *IDN? command
                    await Task.Delay(100); // Small delay
                    var response = await SendCommandAsync("*IDN?");
                    
                    _logger.LogInformation($"IDN Response from {device}: '{response}'");
                    
                    if (!string.IsNullOrEmpty(response) && 
                        (response.Contains("34461A") || response.Contains("Keysight")))
                    {
                        _isConnected = true;
                        _logger.LogInformation($"✅ Keysight 34461A connected successfully on {device}");
                        _logger.LogInformation($"Device Info: {response.Trim()}");
                        return true;
                    }

                    // If no valid response, close and try next device
                    _usbtmcStream.Close();
                    _usbtmcStream.Dispose();
                    _usbtmcStream = null;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, $"❌ Failed to connect to {device}: {ex.Message}");
                    _usbtmcStream?.Close();
                    _usbtmcStream?.Dispose();
                    _usbtmcStream = null;
                }
            }

            _logger.LogWarning("❌ Keysight 34461A not found on any USBTMC device");
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Connection failed with exception");
            return false;
        }
    }

    public async Task<string> SendCommandAsync(string command)
    {
        if (!_isConnected || _usbtmcStream == null)
        {
            _logger.LogWarning($"⚠️ Not connected - cannot send command: {command}");
            throw new InvalidOperationException("Not connected to device");
        }

        try
        {
            _logger.LogDebug($"📤 Sending command: {command}");

            // Send command to USBTMC device
            var commandBytes = Encoding.ASCII.GetBytes(command + "\n");
            await _usbtmcStream.WriteAsync(commandBytes);
            await _usbtmcStream.FlushAsync();

            // For query commands, read response
            if (command.EndsWith("?"))
            {
                // Wait for response
                await Task.Delay(200);

                // Read response with timeout
                var buffer = new byte[4096];
                var bytesRead = 0;
                
                // Try to read with multiple attempts
                for (int attempt = 0; attempt < 5; attempt++)
                {
                    try
                    {
                        bytesRead = await _usbtmcStream.ReadAsync(buffer);
                        if (bytesRead > 0) break;
                        await Task.Delay(50);
                    }
                    catch
                    {
                        if (attempt == 4) throw;
                        await Task.Delay(100);
                    }
                }
                
                if (bytesRead > 0)
                {
                    var response = Encoding.ASCII.GetString(buffer, 0, bytesRead);
                    var cleanResponse = response.Trim('\n', '\r', '\0', ' ');
                    _logger.LogDebug($"📥 Received response: '{cleanResponse}' ({bytesRead} bytes)");
                    return cleanResponse;
                }
                else
                {
                    _logger.LogWarning($"⚠️ No response received for command: {command}");
                    return "";
                }
            }

            _logger.LogDebug($"✅ Command sent successfully: {command}");
            return "OK";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, $"❌ Failed to send command '{command}': {ex.Message}");
            throw;
        }
    }

    public async Task<double> MeasureVoltageAsync()
    {
        try
        {
            _logger.LogInformation("📊 Measuring voltage...");
            var response = await SendCommandAsync("MEAS:VOLT:DC?");
            
            if (double.TryParse(response, out double voltage))
            {
                _logger.LogInformation($"✅ Voltage measurement: {voltage:F6} V");
                return voltage;
            }
            
            _logger.LogError($"❌ Invalid voltage reading: '{response}'");
            throw new InvalidDataException($"Invalid voltage reading: {response}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Voltage measurement failed");
            throw;
        }
    }

    public async Task DisconnectAsync()
    {
        try
        {
            if (_usbtmcStream != null)
            {
                _logger.LogInformation($"🔌 Disconnecting from {_devicePath}");
                _usbtmcStream.Close();
                _usbtmcStream.Dispose();
                _usbtmcStream = null;
            }
            _isConnected = false;
            _devicePath = null;
            _logger.LogInformation("✅ Disconnected successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Error during disconnect");
        }
        await Task.CompletedTask;
    }

    public void Dispose()
    {
        try
        {
            _usbtmcStream?.Close();
            _usbtmcStream?.Dispose();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error disposing USBTMC stream");
        }
    }
}