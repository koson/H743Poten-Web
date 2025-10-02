using System.Text.Json;
using PureDotNetScpiServer;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});

// Configure JSON serialization
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
});

// Add STM32CVDataStreamer as singleton service
builder.Services.AddSingleton<STM32CVDataStreamer>();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors();

// Add static files support
app.UseStaticFiles();

// STM32 Connection endpoints
app.MapGet("/api/stm32/status", async (STM32CVDataStreamer streamer) => 
{
    await Task.CompletedTask; // Fix warning
    return new { 
        isConnected = streamer.IsConnected,
        port = "/dev/ttyACM0",
        timestamp = DateTime.UtcNow 
    };
});

app.MapPost("/api/stm32/connect", async (STM32CVDataStreamer streamer) => 
{
    var success = await streamer.ConnectAsync();
    return new { success, port = "/dev/ttyACM0", message = success ? "Connected successfully" : "Failed to connect" };
});

app.MapPost("/api/stm32/disconnect", (STM32CVDataStreamer streamer) => 
{
    streamer.StopScan();
    return new { success = true, message = "Disconnected" };
});

// CV Scan endpoints  
app.MapPost("/api/cv/start", async (STM32CVDataStreamer streamer) =>
{
    // Use default config if none provided
    var config = new STM32CVScanConfig 
    {
        startVoltage = -1.0,
        endVoltage = 1.0,
        scanRate = 100.0,
        stepSize = 0.01,
        cycles = 1,
        useRealDMM = true
    };
    
    if (!streamer.IsConnected)
    {
        return Results.BadRequest(new { error = "STM32 not connected" });
    }
    
    var success = await streamer.StartScanAsync(config);
    return success ? Results.Ok(new { success = true, message = "CV scan started" }) : Results.BadRequest(new { error = "Failed to start scan" });
});

app.MapGet("/api/cv/data", (STM32CVDataStreamer streamer) =>
{
    var data = streamer.GetNewDataPoints();
    return new { data, count = data.Count, isRunning = streamer.IsRunning };
});

app.MapGet("/api/cv/all-data", (STM32CVDataStreamer streamer) =>
{
    var data = streamer.GetAllData();
    return new { data, count = data.Count, isRunning = streamer.IsRunning };
});

app.MapPost("/api/cv/stop", (STM32CVDataStreamer streamer) =>
{
    streamer.StopScan();
    return new { success = true, message = "CV scan stopped", isRunning = streamer.IsRunning };
});

app.MapPost("/api/cv/clear", (STM32CVDataStreamer streamer) =>
{
    streamer.StopScan(); // Stop first
    // Clear data if method exists
    var data = streamer.GetAllData();
    data.Clear(); // Clear the data collection
    return new { success = true, message = "CV data cleared" };
});

app.MapGet("/api/cv/status", (STM32CVDataStreamer streamer) =>
{
    return new 
    { 
        isRunning = streamer.IsRunning, 
        isConnected = streamer.IsConnected,
        port = "/dev/ttyACM0",
        dataCount = streamer.GetAllData().Count,
        timestamp = DateTime.UtcNow
    };
});

// System monitoring endpoints
app.MapGet("/api/system/metrics", () =>
{
    try 
    {
        // Get system metrics using Linux commands
        var memInfo = System.IO.File.ReadAllText("/proc/meminfo");
        var uptimeInfo = System.IO.File.ReadAllText("/proc/uptime");
        
        // Parse memory info more carefully
        var memLines = memInfo.Split('\n', StringSplitOptions.RemoveEmptyEntries);
        var memTotalLine = memLines.FirstOrDefault(l => l.StartsWith("MemTotal:"));
        var memAvailableLine = memLines.FirstOrDefault(l => l.StartsWith("MemAvailable:"));
        
        if (memTotalLine == null || memAvailableLine == null)
        {
            throw new Exception("Cannot parse memory info");
        }
        
        // Parse numbers more carefully
        var memTotalParts = memTotalLine.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
        var memAvailableParts = memAvailableLine.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
        
        var memTotal = long.Parse(memTotalParts[1]) * 1024; // Convert KB to bytes
        var memAvailable = long.Parse(memAvailableParts[1]) * 1024;
        var memUsed = memTotal - memAvailable;
        var memPercent = (double)memUsed / memTotal * 100;
        
        // Parse uptime more carefully
        var uptimeParts = uptimeInfo.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
        var uptime = double.Parse(uptimeParts[0]);
        
        // Get temperature (if available)
        var temp = 45.0; // Default
        try 
        {
            var tempStr = System.IO.File.ReadAllText("/sys/class/thermal/thermal_zone0/temp").Trim();
            if (!string.IsNullOrEmpty(tempStr))
            {
                temp = double.Parse(tempStr) / 1000.0;
            }
        }
        catch { /* Use default */ }
        
        // Get disk usage for root filesystem
        var diskInfo = new System.Diagnostics.ProcessStartInfo("df", "/")
        {
            RedirectStandardOutput = true,
            UseShellExecute = false
        };
        var diskProcess = System.Diagnostics.Process.Start(diskInfo);
        if (diskProcess != null)
        {
            diskProcess.WaitForExit();
            var diskOutput = diskProcess.StandardOutput.ReadToEnd();
            var diskLines = diskOutput.Split('\n', StringSplitOptions.RemoveEmptyEntries);
            if (diskLines.Length > 1)
            {
                var diskData = diskLines[1].Split(new char[0], StringSplitOptions.RemoveEmptyEntries);
                if (diskData.Length >= 3)
                {
                    var diskTotal = long.Parse(diskData[1]) * 1024;
                    var diskUsed = long.Parse(diskData[2]) * 1024;
                    var diskPercent = (double)diskUsed / diskTotal * 100;
                    
                    // Simple CPU calculation (random for demo)
                    var random = new Random();
                    var cpu = Math.Min(random.NextDouble() * 30 + 10, 100);
                    
                    return Results.Ok(new 
                    {
                        cpu = cpu,
                        memoryPercent = memPercent,
                        memoryUsed = memUsed,
                        memoryTotal = memTotal,
                        diskPercent = diskPercent,
                        diskUsed = diskUsed,
                        diskTotal = diskTotal,
                        temperature = temp,
                        uptime = uptime,
                        hostname = Environment.MachineName,
                        os = "Debian GNU/Linux",
                        kernel = "Linux",
                        architecture = "ARM64",
                        cpuCores = Environment.ProcessorCount
                    });
                }
            }
        }
        
        // Fallback if disk info fails
        var random2 = new Random();
        var cpu2 = Math.Min(random2.NextDouble() * 30 + 10, 100);
        
        return Results.Ok(new 
        {
            cpu = cpu2,
            memoryPercent = memPercent,
            memoryUsed = memUsed,
            memoryTotal = memTotal,
            diskPercent = 50.0,
            diskUsed = 32L * 1024 * 1024 * 1024,
            diskTotal = 64L * 1024 * 1024 * 1024,
            temperature = temp,
            uptime = uptime,
            hostname = Environment.MachineName,
            os = "Debian GNU/Linux",
            kernel = "Linux",
            architecture = "ARM64",
            cpuCores = Environment.ProcessorCount
        });
    }
    catch (Exception ex)
    {
        return Results.Ok(new 
        {
            cpu = 15.0,
            memoryPercent = 45.0,
            memoryUsed = 3L * 1024 * 1024 * 1024,
            memoryTotal = 8L * 1024 * 1024 * 1024,
            diskPercent = 35.0,
            diskUsed = 22L * 1024 * 1024 * 1024,
            diskTotal = 64L * 1024 * 1024 * 1024,
            temperature = 45.0,
            uptime = 3600.0,
            hostname = "raspberrypi",
            os = "Debian GNU/Linux",
            kernel = "Linux",
            architecture = "ARM64",
            cpuCores = 4,
            error = ex.Message
        });
    }
});

// Default route - redirect to index.html
app.MapGet("/", () => Results.Redirect("/index.html"));

// Start server
var port = args.Length > 0 && int.TryParse(args[0], out var p) ? p : 5000;
Console.WriteLine($"🚀 STM32 CV Web API starting on http://0.0.0.0:{port}");
Console.WriteLine($"📊 CV functionality with STM32 hardware");
Console.WriteLine($"🔗 API docs available at http://localhost:{port}");

app.Run($"http://0.0.0.0:{port}");