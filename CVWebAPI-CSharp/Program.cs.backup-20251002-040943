using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(options => options.AddDefaultPolicy(p => p.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));
builder.Services.AddSingleton<DMMDevice>();
builder.Services.AddSingleton<CVDataStreamer>();
builder.Services.AddSingleton<SystemMonitor>();
var app = builder.Build();
app.UseCors();
app.UseStaticFiles();

// CV API endpoints
app.MapGet("/", () => Results.Redirect("/index.html"));
app.MapGet("/api/cv/status", (CVDataStreamer s) => Results.Json(new { running = s.IsRunning, dataPoints = s.DataPointCount, config = s.CurrentConfig }));
app.MapPost("/api/cv/start", async (CVDataStreamer s, CVScanConfig? c) => { c ??= new CVScanConfig(); var ok = await s.StartScanAsync(c); return Results.Json(new { success = ok, message = ok ? "Scan started" : "Already running" }); });
app.MapPost("/api/cv/stop", (CVDataStreamer s) => { s.StopScan(); return Results.Json(new { success = true }); });
app.MapGet("/api/cv/data", (CVDataStreamer s) => Results.Json(s.GetNewDataPoints()));
app.MapGet("/api/cv/data/all", (CVDataStreamer s) => Results.Json(s.GetAllData()));
app.MapPost("/api/cv/clear", (CVDataStreamer s) => { s.ClearData(); return Results.Json(new { success = true }); });

// System monitoring API
app.MapGet("/api/system/metrics", async (SystemMonitor m) => Results.Json(await m.GetMetricsAsync()));

Console.WriteLine("🚀 CV Web API on http://0.0.0.0:5000");
Console.WriteLine("📊 Performance Monitor: http://0.0.0.0:5000/performance.html");
app.Run("http://0.0.0.0:5000");

// ==================== Class Definitions ====================

public class CVDataPoint
{
    public double Voltage { get; set; }
    public double Current { get; set; }
    public double Time { get; set; }
    public int Index { get; set; }
}

public class CVScanConfig
{
    public double StartVoltage { get; set; } = -0.5;
    public double EndVoltage { get; set; } = 0.5;
    public double ScanRate { get; set; } = 0.1;
    public int DataPoints { get; set; } = 400;
    public int Cycles { get; set; } = 1;
    public bool UseRealDMM { get; set; } = true;
}

// DMM Device Handler
public class DMMDevice : IDisposable
{
    private FileStream? _deviceStream;
    private readonly string _devicePath;
    private readonly SemaphoreSlim _semaphore = new(1, 1);
    private bool _isOpen;

    public DMMDevice()
    {
        var devices = new[] { "/dev/usbtmc0", "/dev/usbtmc1", "/dev/usbtmc2" };
        _devicePath = devices.FirstOrDefault(File.Exists) ?? "/dev/usbtmc0";
        Console.WriteLine($"🔍 Using DMM device: {_devicePath}");
    }

    public async Task<bool> OpenAsync()
    {
        if (_isOpen) return true;
        
        try
        {
            if (!File.Exists(_devicePath))
            {
                Console.WriteLine($"⚠️  DMM not found: {_devicePath}, will use simulation");
                return false;
            }

            _deviceStream = new FileStream(_devicePath, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
            
            await SendCommandAsync("*CLS");
            await Task.Delay(100);
            
            var idn = await SendCommandAsync("*IDN?");
            if (!string.IsNullOrEmpty(idn) && !idn.StartsWith("ERROR"))
            {
                Console.WriteLine($"✅ DMM Connected: {idn}");
                
                await SendCommandAsync("*RST");
                await Task.Delay(500);
                await SendCommandAsync("*CLS");
                await Task.Delay(100);
                
                await SendCommandAsync("CONF:VOLT:DC");
                await Task.Delay(100);
                
                await SendCommandAsync("VOLT:DC:NPLC 0.2");
                await Task.Delay(100);
                
                await SendCommandAsync("*CLS");
                await Task.Delay(100);
                
                _isOpen = true;
                Console.WriteLine("✅ DMM configured for fast DC voltage measurement");
                return true;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"⚠️  DMM open failed: {ex.Message}, will use simulation");
        }
        
        return false;
    }

    public async Task<double> MeasureVoltageAsync()
    {
        if (!_isOpen || _deviceStream == null)
            return 0.0;

        await _semaphore.WaitAsync();
        try
        {
            var response = await SendCommandAsync("READ?");
            await SendCommandAsync("*CLS");
            
            if (double.TryParse(response.Trim(), out var voltage))
            {
                return voltage;
            }
            else
            {
                Console.WriteLine($"⚠️  Failed to parse voltage: '{response}'");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"⚠️  Measurement error: {ex.Message}");
        }
        finally
        {
            _semaphore.Release();
        }
        
        return 0.0;
    }

    private async Task<string> SendCommandAsync(string command)
    {
        if (_deviceStream == null) return "ERROR: Device not open";

        try
        {
            var commandBytes = Encoding.ASCII.GetBytes(command.TrimEnd('\n') + "\n");
            await _deviceStream.WriteAsync(commandBytes, 0, commandBytes.Length);
            await _deviceStream.FlushAsync();

            if (command.Contains('?'))
            {
                await Task.Delay(200);
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
            return $"ERROR: {ex.Message}";
        }
    }

    public void Dispose()
    {
        try
        {
            if (_deviceStream != null && _isOpen)
            {
                var clsCmd = Encoding.ASCII.GetBytes("*CLS\n");
                _deviceStream.Write(clsCmd, 0, clsCmd.Length);
                _deviceStream.Flush();
                Thread.Sleep(100);
                
                var localCmd = Encoding.ASCII.GetBytes("SYST:LOC\n");
                _deviceStream.Write(localCmd, 0, localCmd.Length);
                _deviceStream.Flush();
                Thread.Sleep(100);
            }
        }
        catch { }
        finally
        {
            _deviceStream?.Dispose();
            _semaphore.Dispose();
        }
    }
}

public class CVDataStreamer
{
    private readonly DMMDevice _dmm;
    private readonly ConcurrentQueue<CVDataPoint> _dataBuffer = new();
    private readonly List<CVDataPoint> _allData = new();
    private CancellationTokenSource? _cts;
    private bool _isRunning;
    private CVScanConfig _config = new();
    private bool _dmmAvailable;
    
    public bool IsRunning => _isRunning;
    public int DataPointCount => _allData.Count;
    public CVScanConfig CurrentConfig => _config;

    public CVDataStreamer(DMMDevice dmm)
    {
        _dmm = dmm;
        _dmmAvailable = _dmm.OpenAsync().Result;
        Console.WriteLine(_dmmAvailable 
            ? "✅ CV Streamer: Using REAL DMM measurements" 
            : "⚠️  CV Streamer: Using SIMULATED data");
    }

    public async Task<bool> StartScanAsync(CVScanConfig config)
    {
        if (_isRunning) return false;
        _config = config;
        _dataBuffer.Clear();
        _allData.Clear();
        _cts = new CancellationTokenSource();
        _isRunning = true;
        
        var mode = _dmmAvailable && config.UseRealDMM ? "REAL DMM" : "SIMULATED";
        Console.WriteLine($"🚀 Starting CV Scan ({mode}): {config.DataPoints} points, {config.StartVoltage}V to {config.EndVoltage}V");
        
        _ = Task.Run(() => StreamDataAsync(_cts.Token));
        return true;
    }

    public void StopScan()
    {
        _cts?.Cancel();
        _isRunning = false;
        Console.WriteLine($"🛑 Scan stopped. Total: {_allData.Count} points");
    }

    private async Task StreamDataAsync(CancellationToken ct)
    {
        try
        {
            var voltageRange = _config.EndVoltage - _config.StartVoltage;
            var voltageStep = (2 * voltageRange) / _config.DataPoints;
            var startTime = DateTime.UtcNow;
            
            for (int cycle = 0; cycle < _config.Cycles && !ct.IsCancellationRequested; cycle++)
            {
                Console.WriteLine($"📊 Cycle {cycle + 1}/{_config.Cycles}");
                await SweepAsync(_config.StartVoltage, _config.EndVoltage, voltageStep, startTime, ct);
                await SweepAsync(_config.EndVoltage, _config.StartVoltage, -voltageStep, startTime, ct);
            }
            _isRunning = false;
            Console.WriteLine($"✅ Scan complete: {_allData.Count} points");
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("⚠️  Scan cancelled");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Scan error: {ex.Message}");
        }
        finally
        {
            _isRunning = false;
        }
    }

    private async Task SweepAsync(double startV, double endV, double step, DateTime startTime, CancellationToken ct)
    {
        double voltage = startV;
        int pointsInSweep = (int)Math.Abs((endV - startV) / step);
        
        for (int i = 0; i < pointsInSweep && !ct.IsCancellationRequested; i++)
        {
            var pointStart = DateTime.UtcNow;
            
            double current;
            if (_dmmAvailable && _config.UseRealDMM)
            {
                var measuredVoltage = await _dmm.MeasureVoltageAsync();
                current = ConvertVoltageToCurrent(measuredVoltage);
                
                if (i % 20 == 0)
                {
                    Console.WriteLine($"📈 Point {_allData.Count}: SweepV={voltage:F3}V, DMM={measuredVoltage:F4}V, I={current:E2}A");
                }
            }
            else
            {
                current = SimulateCurrentResponse(voltage);
            }
            
            var dataPoint = new CVDataPoint
            {
                Voltage = voltage,
                Current = current,
                Time = (DateTime.UtcNow - startTime).TotalSeconds,
                Index = _allData.Count
            };
            
            _dataBuffer.Enqueue(dataPoint);
            _allData.Add(dataPoint);
            voltage += step;
            
            var elapsed = DateTime.UtcNow - pointStart;
            var delay = TimeSpan.FromMilliseconds(100) - elapsed;
            if (delay > TimeSpan.Zero)
            {
                await Task.Delay(delay, ct);
            }
        }
    }

    private double ConvertVoltageToCurrent(double voltage)
    {
        return (voltage - 2.5) * 20e-6;
    }

    private double SimulateCurrentResponse(double voltage)
    {
        var peak1 = 2e-5 * Math.Exp(-Math.Pow((voltage - 0.2) / 0.1, 2));
        var peak2 = -1.8e-5 * Math.Exp(-Math.Pow((voltage + 0.2) / 0.1, 2));
        var background = voltage * 1e-6;
        var noise = (Random.Shared.NextDouble() - 0.5) * 1e-7;
        return peak1 + peak2 + background + noise;
    }

    public List<CVDataPoint> GetNewDataPoints()
    {
        var newPoints = new List<CVDataPoint>();
        while (_dataBuffer.TryDequeue(out var point)) newPoints.Add(point);
        return newPoints;
    }

    public List<CVDataPoint> GetAllData() => new List<CVDataPoint>(_allData);
    
    public void ClearData() 
    { 
        _dataBuffer.Clear(); 
        _allData.Clear();
        Console.WriteLine("🗑️  Data cleared");
    }
}

// System Monitor for Raspberry Pi
public class SystemMonitor
{
    private DateTime _startTime = DateTime.UtcNow;

    public async Task<object> GetMetricsAsync()
    {
        try
        {
            var metrics = new
            {
                cpu = await GetCpuUsageAsync(),
                memoryPercent = GetMemoryUsagePercent(),
                memoryUsed = GetMemoryUsed(),
                memoryTotal = GetMemoryTotal(),
                diskPercent = GetDiskUsagePercent(),
                diskUsed = GetDiskUsed(),
                diskTotal = GetDiskTotal(),
                temperature = await GetCpuTemperatureAsync(),
                uptime = GetUptime(),
                hostname = GetHostname(),
                os = GetOS(),
                kernel = GetKernel(),
                architecture = GetArchitecture(),
                cpuCores = Environment.ProcessorCount
            };

            return metrics;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error getting metrics: {ex.Message}");
            return new { error = ex.Message };
        }
    }

    private async Task<double> GetCpuUsageAsync()
    {
        try
        {
            // Read /proc/stat for CPU usage
            var lines = await File.ReadAllLinesAsync("/proc/stat");
            var cpuLine = lines.FirstOrDefault(l => l.StartsWith("cpu "));
            if (cpuLine != null)
            {
                var values = cpuLine.Split(' ', StringSplitOptions.RemoveEmptyEntries).Skip(1).Select(long.Parse).ToArray();
                var idle = values[3];
                var total = values.Sum();
                
                // Simple approximation (single sample)
                var usage = total > 0 ? 100.0 * (total - idle) / total : 0;
                return Math.Max(0, Math.Min(100, usage));
            }
        }
        catch { }
        return 0;
    }

    private double GetMemoryUsagePercent()
    {
        try
        {
            var lines = File.ReadAllLines("/proc/meminfo");
            var total = ParseMemInfoLine(lines, "MemTotal:");
            var available = ParseMemInfoLine(lines, "MemAvailable:");
            
            if (total > 0)
            {
                var used = total - available;
                return 100.0 * used / total;
            }
        }
        catch { }
        return 0;
    }

    private long GetMemoryUsed()
    {
        try
        {
            var lines = File.ReadAllLines("/proc/meminfo");
            var total = ParseMemInfoLine(lines, "MemTotal:");
            var available = ParseMemInfoLine(lines, "MemAvailable:");
            return (total - available) * 1024; // Convert to bytes
        }
        catch { }
        return 0;
    }

    private long GetMemoryTotal()
    {
        try
        {
            var lines = File.ReadAllLines("/proc/meminfo");
            return ParseMemInfoLine(lines, "MemTotal:") * 1024; // Convert to bytes
        }
        catch { }
        return 0;
    }

    private long ParseMemInfoLine(string[] lines, string key)
    {
        var line = lines.FirstOrDefault(l => l.StartsWith(key));
        if (line != null)
        {
            var parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length >= 2 && long.TryParse(parts[1], out var value))
            {
                return value;
            }
        }
        return 0;
    }

    private double GetDiskUsagePercent()
    {
        try
        {
            var info = new DriveInfo("/");
            return 100.0 * (info.TotalSize - info.AvailableFreeSpace) / info.TotalSize;
        }
        catch { }
        return 0;
    }

    private long GetDiskUsed()
    {
        try
        {
            var info = new DriveInfo("/");
            return info.TotalSize - info.AvailableFreeSpace;
        }
        catch { }
        return 0;
    }

    private long GetDiskTotal()
    {
        try
        {
            var info = new DriveInfo("/");
            return info.TotalSize;
        }
        catch { }
        return 0;
    }

    private async Task<double> GetCpuTemperatureAsync()
    {
        try
        {
            // Raspberry Pi temperature
            if (File.Exists("/sys/class/thermal/thermal_zone0/temp"))
            {
                var tempStr = await File.ReadAllTextAsync("/sys/class/thermal/thermal_zone0/temp");
                if (int.TryParse(tempStr.Trim(), out var temp))
                {
                    return temp / 1000.0; // Convert to Celsius
                }
            }
        }
        catch { }
        return 0;
    }

    private long GetUptime()
    {
        try
        {
            var uptimeStr = File.ReadAllText("/proc/uptime").Split(' ')[0];
            if (double.TryParse(uptimeStr, out var uptime))
            {
                return (long)uptime;
            }
        }
        catch { }
        return 0;
    }

    private string GetHostname()
    {
        try
        {
            return File.ReadAllText("/etc/hostname").Trim();
        }
        catch { }
        return "Unknown";
    }

    private string GetOS()
    {
        try
        {
            if (File.Exists("/etc/os-release"))
            {
                var lines = File.ReadAllLines("/etc/os-release");
                var prettyName = lines.FirstOrDefault(l => l.StartsWith("PRETTY_NAME="));
                if (prettyName != null)
                {
                    return prettyName.Split('=')[1].Trim('"');
                }
            }
        }
        catch { }
        return "Linux";
    }

    private string GetKernel()
    {
        try
        {
            var process = Process.Start(new ProcessStartInfo
            {
                FileName = "uname",
                Arguments = "-r",
                RedirectStandardOutput = true,
                UseShellExecute = false
            });
            
            if (process != null)
            {
                var output = process.StandardOutput.ReadToEnd().Trim();
                process.WaitForExit();
                return output;
            }
        }
        catch { }
        return "Unknown";
    }

    private string GetArchitecture()
    {
        try
        {
            var process = Process.Start(new ProcessStartInfo
            {
                FileName = "uname",
                Arguments = "-m",
                RedirectStandardOutput = true,
                UseShellExecute = false
            });
            
            if (process != null)
            {
                var output = process.StandardOutput.ReadToEnd().Trim();
                process.WaitForExit();
                return output;
            }
        }
        catch { }
        return RuntimeInformation.ProcessArchitecture.ToString();
    }
}
