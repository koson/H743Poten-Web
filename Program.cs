using Microsoft.AspNetCore.Mvc;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddSwaggerGen();
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Configure pipeline
app.UseSwagger();
app.UseSwaggerUI();
app.UseCors();
app.MapControllers();

// Keysight API Controller
app.MapPost("/api/keysight/connect", async () =>
{
    try
    {
        if (!File.Exists("/dev/usbtmc0"))
        {
            return Results.BadRequest(new { success = false, message = "USBTMC device not found" });
        }

        // Test connection
        using (var device = new FileStream("/dev/usbtmc0", FileMode.Open, FileAccess.ReadWrite))
        {
            var command = "*IDN?\n";
            var commandBytes = System.Text.Encoding.ASCII.GetBytes(command);
            await device.WriteAsync(commandBytes, 0, commandBytes.Length);
            await device.FlushAsync();
            
            await Task.Delay(200); // Wait for response
            
            var buffer = new byte[1024];
            int bytesRead = await device.ReadAsync(buffer, 0, buffer.Length);
            var response = System.Text.Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();

            if (response.Contains("Keysight"))
            {
                return Results.Ok(new { success = true, message = $"Connected: {response}" });
            }
            else
            {
                return Results.BadRequest(new { success = false, message = "Invalid device response" });
            }
        }
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new { success = false, message = $"Connection failed: {ex.Message}" });
    }
});

app.MapPost("/api/keysight/command", async (HttpRequest request) =>
{
    try
    {
        var body = await new StreamReader(request.Body).ReadToEndAsync();
        var json = JsonSerializer.Deserialize<Dictionary<string, object>>(body);
        var command = json?["command"]?.ToString();

        if (string.IsNullOrEmpty(command))
        {
            return Results.BadRequest(new { success = false, message = "No command specified" });
        }

        await File.WriteAllTextAsync("/dev/usbtmc0", $"{command}\n");

        if (command.Contains('?'))
        {
            await Task.Delay(100); // Wait for response
            var response = await File.ReadAllTextAsync("/dev/usbtmc0");
            return Results.Ok(new { success = true, response = response.Trim() });
        }
        else
        {
            return Results.Ok(new { success = true, message = "Command sent" });
        }
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new { success = false, message = ex.Message });
    }
});

app.MapGet("/api/keysight/voltage", async () =>
{
    try
    {
        await File.WriteAllTextAsync("/dev/usbtmc0", "READ?\n");
        await Task.Delay(100);
        var response = await File.ReadAllTextAsync("/dev/usbtmc0");
        
        if (double.TryParse(response.Trim(), out double voltage))
        {
            return Results.Ok(new { success = true, voltage = voltage });
        }
        else
        {
            return Results.BadRequest(new { success = false, message = "Invalid voltage response" });
        }
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new { success = false, message = ex.Message });
    }
});

Console.WriteLine("Keysight USBTMC API starting on http://0.0.0.0:5001");
Console.WriteLine("Swagger UI available at http://localhost:5001/swagger");

app.Run("http://0.0.0.0:5001");