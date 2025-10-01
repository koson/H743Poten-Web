using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.FileProviders;
using System.Text.Json;
using PureDotNetScpiServer;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});

builder.Services.AddSingleton(sp =>
{
    var devicePath = "/dev/usbtmc0";
    if (File.Exists("/dev/usbtmc1")) devicePath = "/dev/usbtmc1";
    var device = new USBTMCDevice(devicePath);
    device.OpenAsync().Wait();
    return device;
});

builder.Services.AddSingleton<CVDataStreamer>(sp =>
{
    var device = sp.GetRequiredService<USBTMCDevice>();
    return new CVDataStreamer(device);
});

var app = builder.Build();

app.UseCors();
app.UseStaticFiles();

app.MapGet("/", () => Results.Redirect("/index.html"));

app.MapGet("/api/cv/status", (CVDataStreamer streamer) =>
{
    return Results.Json(new
    {
        running = streamer.IsRunning,
        dataPoints = streamer.DataPointCount,
        config = streamer.CurrentConfig
    });
});

app.MapPost("/api/cv/start", async (CVDataStreamer streamer, CVScanConfig? config) =>
{
    config ??= new CVScanConfig();
    var success = await streamer.StartScanAsync(config);
    return Results.Json(new { success, message = success ? "Scan started" : "Scan already running" });
});

app.MapPost("/api/cv/stop", (CVDataStreamer streamer) =>
{
    streamer.StopScan();
    return Results.Json(new { success = true, message = "Scan stopped" });
});

app.MapGet("/api/cv/data", (CVDataStreamer streamer) =>
{
    var newData = streamer.GetNewDataPoints();
    return Results.Json(newData);
});

app.MapGet("/api/cv/data/all", (CVDataStreamer streamer) =>
{
    var allData = streamer.GetAllData();
    return Results.Json(allData);
});

app.MapPost("/api/cv/clear", (CVDataStreamer streamer) =>
{
    streamer.ClearData();
    return Results.Json(new { success = true, message = "Data cleared" });
});

Console.WriteLine("🚀 CV Web API starting on http://0.0.0.0:5000");
app.Run("http://0.0.0.0:5000");
