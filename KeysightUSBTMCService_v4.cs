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
            _logger.LogInformation($"📡 Available USBTMC devices: {string.Join(", ", usbtmcDevices)}");

            foreach (var device in usbtmcDevices)
            {
                try
                {
                    _logger.LogInformation($"🔌 Attempting to connect to {device}");
                    
                    // Open USBTMC device for read/write
                    _usbtmcStream = new FileStream(device, FileMode.Open, FileAccess.ReadWrite, FileShare.ReadWrite);
                    _devicePath = device;

                    // Test with *IDN? command using the working method
                    _logger.LogInformation($"📤 Sending test command: *IDN?");
                    var command = "*IDN?\n";
                    var commandBytes = Encoding.ASCII.GetBytes(command);
                    
                    await _usbtmcStream.WriteAsync(commandBytes);
                    await _usbtmcStream.FlushAsync();
                    
                    // Wait for response
                    await Task.Delay(500);
                    
                    // Read response
                    var buffer = new byte[1024];
                    var bytesRead = await _usbtmcStream.ReadAsync(buffer);
                    
                    string response = "";
                    if (bytesRead > 0)
                    {
                        response = Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();
                        _logger.LogInformation($"📥 Received response: '{response}' ({bytesRead} bytes)");
                    }
                    else
                    {
                        _logger.LogWarning($"⚠️ No async response, trying sync read...");
                        // Try synchronous read as backup
                        _usbtmcStream.Position = 0;
                        var syncBytes = _usbtmcStream.Read(buffer, 0, buffer.Length);
                        if (syncBytes > 0)
                        {
                            response = Encoding.ASCII.GetString(buffer, 0, syncBytes).Trim();
                            _logger.LogInformation($"📥 Sync response: '{response}' ({syncBytes} bytes)");
                        }
                    }
                    
                    if (!string.IsNullOrEmpty(response) && 
                        (response.Contains("34461A") || response.Contains("Keysight")))
                    {
                        _isConnected = true;
                        _logger.LogInformation($"✅ Keysight 34461A connected successfully!");
                        _logger.LogInformation($"🔧 Device: {response}");
                        return true;
                    }
                    else
                    {
                        _logger.LogWarning($"❌ Invalid response: '{response}'");
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
            _logger.LogInformation($"📤 Sending command: {command}");

            // Send command using the working method
            var commandWithNewline = command + "\n";
            var commandBytes = Encoding.ASCII.GetBytes(commandWithNewline);
            await _usbtmcStream.WriteAsync(commandBytes);
            await _usbtmcStream.FlushAsync();

            // For query commands, read response
            if (command.EndsWith("?"))
            {
                // Wait for response (same as working test)
                await Task.Delay(500);

                // Read response
                var buffer = new byte[1024];
                var bytesRead = await _usbtmcStream.ReadAsync(buffer);
                
                if (bytesRead > 0)
                {
                    var response = Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();
                    _logger.LogInformation($"📥 Response: '{response}' ({bytesRead} bytes)");
                    return response;
                }
                else
                {
                    // Try sync read as backup
                    _logger.LogInformation($"🔄 Trying synchronous read...");
                    _usbtmcStream.Position = 0;
                    var syncBytes = _usbtmcStream.Read(buffer, 0, buffer.Length);
                    if (syncBytes > 0)
                    {
                        var syncResponse = Encoding.ASCII.GetString(buffer, 0, syncBytes).Trim();
                        _logger.LogInformation($"📥 Sync response: '{syncResponse}' ({syncBytes} bytes)");
                        return syncResponse;
                    }
                    
                    _logger.LogWarning($"⚠️ No response received for command: {command}");
                    return "";
                }
            }

            _logger.LogInformation($"✅ Command sent successfully: {command}");
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
            if (_usbtmcStream != null && _isConnected)
            {
                _logger.LogInformation($"🔧 Initiating proper USBTMC disconnect from {_devicePath}");
                
                try
                {
                    // Method 1: Send USBTMC Go-To-Local (GTL) control message
                    _logger.LogInformation("🏠 Sending Go-To-Local control message...");
                    
                    // USBTMC GTL control message: Write 0x01 to control endpoint
                    // This is the proper way to exit remote mode in USBTMC
                    var gtlMessage = new byte[] { 0x01 }; // GTL (Go To Local) control message
                    
                    // Try to send control message (this might not work with FileStream)
                    // but we'll try other methods
                    
                    // Method 2: Send standard SCPI local commands
                    _logger.LogInformation("📤 Sending SCPI local commands...");
                    await SendCommandAsync("*CLS");
                    await Task.Delay(100);
                    
                    // Try different local commands
                    await SendCommandAsync("SYST:LOC");
                    await Task.Delay(100);
                    
                    // Method 3: USBTMC specific local command
                    await SendCommandAsync("SYST:REM:STAT OFF");
                    await Task.Delay(100);
                    
                    _logger.LogInformation("✅ Local commands sent");
                }
                catch (Exception cmdEx)
                {
                    _logger.LogWarning(cmdEx, "⚠️ Warning: Could not send all cleanup commands");
                }
                
                // Method 4: Close and reopen to force local mode
                _logger.LogInformation($"🔄 Closing and reopening connection to force local mode...");
                _usbtmcStream.Close();
                _usbtmcStream.Dispose();
                
                // Brief delay
                await Task.Delay(500);
                
                // Reopen and immediately close to trigger local mode
                try
                {
                    var tempStream = new FileStream(_devicePath, FileMode.Open, FileAccess.ReadWrite);
                    await Task.Delay(100);
                    tempStream.Close();
                    tempStream.Dispose();
                    _logger.LogInformation("✅ Force local mode sequence completed");
                }
                catch (Exception ex)
                {
                    _logger.LogWarning($"⚠️ Could not execute force local sequence: {ex.Message}");
                }
                
                _usbtmcStream = null;
            }
            
            _isConnected = false;
            _devicePath = null;
            _logger.LogInformation("✅ Disconnect complete - DMM should return to local mode");
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