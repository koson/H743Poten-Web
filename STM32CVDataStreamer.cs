using System.Collections.Concurrent;
using System.IO.Ports;
using System.Text;
using System.Text.Json;

namespace PureDotNetScpiServer;

/// <summary>
/// CV Data Point structure matching Python implementation
/// </summary>
public class STM32CVDataPoint
{
    public string Type { get; set; } = "CV";
    public int TimeUs { get; set; }
    public double Voltage { get; set; }
    public double CurrentUA { get; set; }
    public int TiaGainIndex { get; set; }
    public int CycleNumber { get; set; }
    public int Dac1Counts { get; set; }
    public int Dac2Counts { get; set; }
    public int SequenceNumber { get; set; }
    public int AdcData { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// CV Scan Configuration
/// </summary>
public class STM32CVScanConfig
{
    public double BeginVoltage { get; set; } = -1.0;
    public double UpperVoltage { get; set; } = 1.0;
    public double LowerVoltage { get; set; } = -1.0;
    public double ScanRate { get; set; } = 0.05; // V/s
    public int Cycles { get; set; } = 3;
    public bool EnableAutoRangeDebug { get; set; } = true;
}

/// <summary>
/// STM32 CV Data Streamer - ports CV test functionality from Python
/// </summary>
public class STM32CVDataStreamer : IDisposable
{
    private readonly string _portName;
    private SerialPort? _serialPort;
    private readonly ConcurrentQueue<STM32CVDataPoint> _dataBuffer = new();
    private readonly List<STM32CVDataPoint> _allData = new();
    private CancellationTokenSource? _cts;
    private bool _isRunning;
    private STM32CVScanConfig _config = new();
    private bool _isConnected;
    
    // TIA Gain values from firmware
    private readonly Dictionary<int, double> _tiaGains = new()
    {
        { 0, 1e3 },   // 1kΩ
        { 1, 10e3 },  // 10kΩ
        { 2, 100e3 }, // 100kΩ
        { 3, 1e6 }    // 1MΩ
    };
    
    private readonly Dictionary<int, string> _currentRanges = new()
    {
        { 0, "±1mA" },
        { 1, "±100µA" },
        { 2, "±10µA" },
        { 3, "±1µA" }
    };

    public bool IsRunning => _isRunning;
    public bool IsConnected => _isConnected;
    public int DataPointCount => _allData.Count;
    public STM32CVScanConfig CurrentConfig => _config;

    public STM32CVDataStreamer(string portName = "/dev/ttyACM0")
    {
        _portName = portName;
    }

    /// <summary>
    /// Connect to STM32 device
    /// </summary>
    public async Task<bool> ConnectAsync()
    {
        try
        {
            _serialPort = new SerialPort(_portName, 115200, Parity.None, 8, StopBits.One)
            {
                ReadTimeout = 5000,
                WriteTimeout = 5000,
                NewLine = "\n"
            };

            _serialPort.Open();
            Console.WriteLine($"✅ Connected to STM32 via {_portName}");

            // Clear STM32 state (ported from Python)
            await ClearSTM32StateAsync();
            
            // Verify device connection
            var response = await SendCommandAsync("*IDN?");
            if (response.Contains("MANUFACTURE,INSTR2013"))
            {
                _isConnected = true;
                Console.WriteLine("✅ Device connection verified!");
                return true;
            }
            else
            {
                Console.WriteLine($"❌ Unexpected device response: {response}");
                return false;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Connection failed: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Clear STM32 state (ported from Python clear_stm32_state function)
    /// </summary>
    private async Task ClearSTM32StateAsync()
    {
        Console.WriteLine("Clearing STM32 state...");
        
        for (int i = 1; i <= 3; i++)
        {
            await SendCommandAsync("ABORT");
            Console.WriteLine($"  Sent ABORT command #{i}");
            await Task.Delay(100);
        }

        // Discard old data
        int discardedLines = 0;
        while (_serialPort?.BytesToRead > 0)
        {
            try
            {
                _serialPort.ReadLine();
                discardedLines++;
            }
            catch
            {
                break;
            }
        }
        Console.WriteLine($"  Discarded {discardedLines} lines of old data");

        // Status check
        var statusResponse = await SendCommandAsync("*IDN?");
        Console.WriteLine($"  Status check response: {statusResponse}");
        Console.WriteLine("  STM32 state cleared successfully!");
    }

    /// <summary>
    /// Send command to STM32 and get response
    /// </summary>
    private async Task<string> SendCommandAsync(string command)
    {
        if (_serialPort == null || !_serialPort.IsOpen)
            throw new InvalidOperationException("Serial port not open");

        _serialPort.WriteLine(command);
        await Task.Delay(50); // Give device time to respond
        
        try
        {
            return _serialPort.ReadLine().Trim();
        }
        catch (TimeoutException)
        {
            return "TIMEOUT";
        }
    }

    /// <summary>
    /// Start CV scan with STM32 (ported from Python)
    /// </summary>
    public async Task<bool> StartScanAsync(STM32CVScanConfig config)
    {
        if (_isRunning) return false;
        if (!_isConnected) 
        {
            Console.WriteLine("❌ STM32 not connected");
            return false;
        }

        _config = config;
        _dataBuffer.Clear();
        _allData.Clear();
        _cts = new CancellationTokenSource();
        _isRunning = true;

        Console.WriteLine($"🚀 Starting CV Scan: {config.BeginVoltage}V to {config.UpperVoltage}V, rate: {config.ScanRate}V/s, cycles: {config.Cycles}");

        // Calculate scan time
        var totalVoltageSwing = Math.Abs(config.UpperVoltage - config.LowerVoltage) * 2; // Up and down
        var estimatedScanTime = (totalVoltageSwing / config.ScanRate) * config.Cycles;
        var timeout = estimatedScanTime + 30; // Add 30s buffer
        
        Console.WriteLine($"  Estimated scan time: {estimatedScanTime:F1}s (timeout: {timeout:F1}s)");

        _ = Task.Run(() => RunCVScanAsync(_cts.Token, timeout));
        return true;
    }

    /// <summary>
    /// Main CV scan loop (ported from Python test_cv_scan function)
    /// </summary>
    private async Task RunCVScanAsync(CancellationToken ct, double timeoutSeconds)
    {
        try
        {
            // Send CV start command (ported from Python)
            var command = $"POTEn:CV:Start:ALL {_config.BeginVoltage},{_config.UpperVoltage},{_config.LowerVoltage},{_config.ScanRate},{_config.Cycles}";
            Console.WriteLine($"Sending: {command}");
            _serialPort?.WriteLine(command);

            Console.WriteLine("Collecting CV data...");
            var startTime = DateTime.UtcNow;
            var timeout = TimeSpan.FromSeconds(timeoutSeconds);

            while (!ct.IsCancellationRequested && (DateTime.UtcNow - startTime) < timeout)
            {
                try
                {
                    if (_serialPort?.BytesToRead > 0)
                    {
                        var line = _serialPort.ReadLine().Trim();
                        if (!string.IsNullOrEmpty(line))
                        {
                            var dataPoint = ParseCVDataLine(line);
                            if (dataPoint != null)
                            {
                                _allData.Add(dataPoint);
                                _dataBuffer.Enqueue(dataPoint);

                                // Debug output (ported from Python)
                                if (_config.EnableAutoRangeDebug)
                                {
                                    DebugAutoRange(dataPoint);
                                }

                                // Progress indicator
                                var elapsed = (DateTime.UtcNow - startTime).TotalSeconds;
                                if (_allData.Count % 50 == 0)
                                {
                                    Console.WriteLine($"  [{elapsed:F1}s] Points collected: {_allData.Count}");
                                }
                            }
                        }
                    }
                    else
                    {
                        await Task.Delay(10, ct); // Small delay to prevent busy waiting
                    }
                }
                catch (TimeoutException)
                {
                    // Continue trying to read
                    continue;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ Data collection error: {ex.Message}");
                    break;
                }
            }

            Console.WriteLine($"✅ CV scan complete: {_allData.Count} data points collected");
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("⚠️ CV scan cancelled");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ CV scan error: {ex.Message}");
        }
        finally
        {
            _isRunning = false;
        }
    }

    /// <summary>
    /// Parse CV data line (ported from Python parse_cv_data_line function)
    /// </summary>
    private STM32CVDataPoint? ParseCVDataLine(string line)
    {
        try
        {
            var parts = line.Split(',');
            if (parts.Length < 10 || parts[0] != "CV")
                return null;

            return new STM32CVDataPoint
            {
                Type = parts[0],
                TimeUs = int.Parse(parts[1]),
                Voltage = double.Parse(parts[2]),
                CurrentUA = double.Parse(parts[3]) * 1e6, // Convert to µA
                TiaGainIndex = int.Parse(parts[4]),
                CycleNumber = int.Parse(parts[5]),
                Dac1Counts = int.Parse(parts[6]),
                Dac2Counts = int.Parse(parts[7]),
                SequenceNumber = int.Parse(parts[8]),
                AdcData = int.Parse(parts[9])
            };
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Parse error: {ex.Message} for line: {line}");
            return null;
        }
    }

    /// <summary>
    /// Debug auto-range info (ported from Python debug_auto_range function)
    /// </summary>
    private void DebugAutoRange(STM32CVDataPoint dataPoint)
    {
        if (_tiaGains.TryGetValue(dataPoint.TiaGainIndex, out var rgain) &&
            _currentRanges.TryGetValue(dataPoint.TiaGainIndex, out var rangeStr))
        {
            var debugMsg = $"AUTO-RANGE DEBUG: V={dataPoint.Voltage:F4}, Range={dataPoint.TiaGainIndex}, RGain={rgain:F0}, I={dataPoint.CurrentUA:F2} µA";
            debugMsg = debugMsg + $", DAC1={dataPoint.Dac1Counts}";
            debugMsg = debugMsg + $" ({rangeStr})";
            
            Console.WriteLine(debugMsg);
        }
        else
        {
            Console.WriteLine($"AUTO-RANGE DEBUG: V={dataPoint.Voltage:F4}, Range={dataPoint.TiaGainIndex} (UNKNOWN), I={dataPoint.CurrentUA:F2} µA");
        }
    }

    /// <summary>
    /// Stop CV scan
    /// </summary>
    public void StopScan()
    {
        _cts?.Cancel();
        _isRunning = false;
        Console.WriteLine($"🛑 CV scan stopped. Total: {_allData.Count} points");
    }

    /// <summary>
    /// Get new data points since last call
    /// </summary>
    public List<STM32CVDataPoint> GetNewDataPoints()
    {
        var newPoints = new List<STM32CVDataPoint>();
        while (_dataBuffer.TryDequeue(out var point))
        {
            newPoints.Add(point);
        }
        return newPoints;
    }

    /// <summary>
    /// Get all collected data
    /// </summary>
    public List<STM32CVDataPoint> GetAllData()
    {
        return new List<STM32CVDataPoint>(_allData);
    }

    /// <summary>
    /// Clear all data
    /// </summary>
    public void ClearData()
    {
        _allData.Clear();
        while (_dataBuffer.TryDequeue(out _)) { }
        Console.WriteLine("🧹 Data cleared");
    }

    public void Dispose()
    {
        _cts?.Cancel();
        _serialPort?.Close();
        _serialPort?.Dispose();
    }
}