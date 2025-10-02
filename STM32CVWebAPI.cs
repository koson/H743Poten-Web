using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using System.Text.Json;
using PureDotNetScpiServer;

var builder = WebApplication.CreateBuilder(args);

// Add services
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
    options.SerializerOptions.WriteIndented = true;
});

// Register STM32 CV Data Streamer as singleton
builder.Services.AddSingleton<STM32CVDataStreamer>(sp =>
{
    // Auto-detect STM32 port
    string portName = "/dev/ttyACM0";
    if (OperatingSystem.IsWindows())
    {
        // Try common Windows COM ports
        var windowsPorts = new[] { "COM10", "COM6", "COM3", "COM4", "COM5" };
        foreach (var port in windowsPorts)
        {
            if (System.IO.Ports.SerialPort.GetPortNames().Contains(port))
            {
                portName = port;
                break;
            }
        }
    }
    else
    {
        // Try common Linux ports
        var linuxPorts = new[] { "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1" };
        foreach (var port in linuxPorts)
        {
            if (File.Exists(port))
            {
                portName = port;
                break;
            }
        }
    }
    
    Console.WriteLine($"🔌 Using STM32 port: {portName}");
    var streamer = new STM32CVDataStreamer(portName);
    
    // Auto-connect on startup
    _ = Task.Run(async () =>
    {
        var connected = await streamer.ConnectAsync();
        Console.WriteLine(connected ? "✅ STM32 ready for CV testing" : "❌ STM32 connection failed");
    });
    
    return streamer;
});

var app = builder.Build();

// Configure middleware
app.UseCors();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}

// Serve static files (for web interface)
app.UseFileServer();

// Default route
app.MapGet("/", () => Results.Text(@"
🔬 STM32 CV Web API Server

Available endpoints:
  GET  /api/cv/status     - Get CV scan status
  POST /api/cv/start      - Start CV scan  
  POST /api/cv/stop       - Stop CV scan
  GET  /api/cv/data       - Get new data points
  GET  /api/cv/data/all   - Get all data points
  POST /api/cv/clear      - Clear all data
  GET  /api/stm32/status  - Get STM32 connection status

Example CV start request:
{
  ""beginVoltage"": -1.0,
  ""upperVoltage"": 1.0,
  ""lowerVoltage"": -1.0,
  ""scanRate"": 0.05,
  ""cycles"": 3,
  ""enableAutoRangeDebug"": true
}
", "text/plain"));

// CV API endpoints
app.MapGet("/api/cv/status", (STM32CVDataStreamer streamer) =>
{
    return Results.Json(new
    {
        running = streamer.IsRunning,
        connected = streamer.IsConnected,
        dataPoints = streamer.DataPointCount,
        config = streamer.CurrentConfig
    });
});

app.MapPost("/api/cv/start", async (STM32CVDataStreamer streamer, STM32CVScanConfig? config) =>
{
    config ??= new STM32CVScanConfig();
    
    if (!streamer.IsConnected)
    {
        return Results.Json(new { success = false, message = "STM32 not connected" });
    }
    
    if (streamer.IsRunning)
    {
        return Results.Json(new { success = false, message = "CV scan already running" });
    }
    
    var success = await streamer.StartScanAsync(config);
    return Results.Json(new { 
        success, 
        message = success ? "CV scan started" : "Failed to start CV scan",
        config
    });
});

app.MapPost("/api/cv/stop", (STM32CVDataStreamer streamer) =>
{
    streamer.StopScan();
    return Results.Json(new { success = true, message = "CV scan stopped" });
});

app.MapGet("/api/cv/data", (STM32CVDataStreamer streamer) =>
{
    var newData = streamer.GetNewDataPoints();
    return Results.Json(new { 
        dataPoints = newData,
        count = newData.Count,
        totalPoints = streamer.DataPointCount
    });
});

app.MapGet("/api/cv/data/all", (STM32CVDataStreamer streamer) =>
{
    var allData = streamer.GetAllData();
    return Results.Json(new { 
        dataPoints = allData,
        count = allData.Count
    });
});

app.MapPost("/api/cv/clear", (STM32CVDataStreamer streamer) =>
{
    streamer.ClearData();
    return Results.Json(new { success = true, message = "All CV data cleared" });
});

// STM32 connection status
app.MapGet("/api/stm32/status", async (STM32CVDataStreamer streamer) =>
{
    if (!streamer.IsConnected)
    {
        // Try to reconnect
        var reconnected = await streamer.ConnectAsync();
        return Results.Json(new { 
            connected = reconnected,
            message = reconnected ? "STM32 reconnected" : "STM32 disconnected"
        });
    }
    
    return Results.Json(new { 
        connected = true,
        message = "STM32 connected and ready"
    });
});

// Health check
app.MapGet("/health", () => Results.Json(new { 
    status = "healthy",
    timestamp = DateTime.UtcNow,
    service = "STM32 CV Web API"
}));

// Start server
var port = args.Length > 0 && int.TryParse(args[0], out var p) ? p : 5000;
Console.WriteLine($"🚀 STM32 CV Web API starting on http://0.0.0.0:{port}");
Console.WriteLine($"📊 CV functionality ported from Python test_cv_final.py");
Console.WriteLine($"🔗 API docs available at http://localhost:{port}");

app.Run($"http://0.0.0.0:{port}");