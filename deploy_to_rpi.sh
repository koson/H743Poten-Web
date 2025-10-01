#!/bin/bash

# Deploy Keysight 34461A Test Application to RPi
# Usage: ./deploy_to_rpi.sh

RPI_HOST="ben@192.168.9.75"
RPI_PATH="/home/ben/H743Poten/Keysight34461A.TestApp"

echo "🚀 Deploying Keysight 34461A Test Application to RPi..."

# Create basic SCPI service
cat > KeysightService.cs << 'EOF'
using System.IO.Ports;

namespace Keysight34461A.TestApp.Services;

public interface IKeysightService
{
    Task<bool> ConnectAsync();
    Task<string> SendCommandAsync(string command);
    Task<double> MeasureVoltageAsync();
    Task DisconnectAsync();
    bool IsConnected { get; }
}

public class KeysightService : IKeysightService, IDisposable
{
    private SerialPort? _serialPort;
    private readonly ILogger<KeysightService> _logger;
    private bool _isConnected = false;

    public bool IsConnected => _isConnected;

    public KeysightService(ILogger<KeysightService> logger)
    {
        _logger = logger;
    }

    public async Task<bool> ConnectAsync()
    {
        try
        {
            // Try to find Keysight 34461A via USB
            var ports = SerialPort.GetPortNames();
            _logger.LogInformation($"Available ports: {string.Join(", ", ports)}");

            foreach (var port in ports)
            {
                try
                {
                    _serialPort = new SerialPort(port, 9600, Parity.None, 8, StopBits.One)
                    {
                        ReadTimeout = 2000,
                        WriteTimeout = 2000,
                        NewLine = "\n"
                    };

                    _serialPort.Open();
                    await Task.Delay(100); // Small delay for connection

                    var response = await SendCommandAsync("*IDN?");
                    if (!string.IsNullOrEmpty(response) && 
                        (response.Contains("34461A") || response.Contains("Keysight")))
                    {
                        _isConnected = true;
                        _logger.LogInformation($"Keysight 34461A found on {port}: {response.Trim()}");
                        return true;
                    }

                    _serialPort.Close();
                    _serialPort.Dispose();
                }
                catch (Exception ex)
                {
                    _logger.LogWarning($"Failed to connect to {port}: {ex.Message}");
                    _serialPort?.Close();
                    _serialPort?.Dispose();
                }
            }

            _logger.LogWarning("Keysight 34461A not found on any port");
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
        if (!_isConnected || _serialPort == null)
            throw new InvalidOperationException("Not connected to device");

        try
        {
            _serialPort.WriteLine(command);
            await Task.Delay(50); // Small delay for response

            // For query commands, read response
            if (command.EndsWith("?"))
            {
                var response = _serialPort.ReadLine();
                return response?.Trim() ?? "";
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
        if (_serialPort?.IsOpen == true)
        {
            _serialPort.Close();
        }
        _isConnected = false;
        await Task.CompletedTask;
    }

    public void Dispose()
    {
        _serialPort?.Close();
        _serialPort?.Dispose();
    }
}
EOF

# Create API controller
cat > KeysightController.cs << 'EOF'
using Microsoft.AspNetCore.Mvc;
using Keysight34461A.TestApp.Services;

namespace Keysight34461A.TestApp.Controllers;

[ApiController]
[Route("api/[controller]")]
public class KeysightController : ControllerBase
{
    private readonly IKeysightService _keysightService;
    private readonly ILogger<KeysightController> _logger;

    public KeysightController(IKeysightService keysightService, ILogger<KeysightController> logger)
    {
        _keysightService = keysightService;
        _logger = logger;
    }

    [HttpPost("connect")]
    public async Task<ActionResult<object>> Connect()
    {
        try
        {
            var connected = await _keysightService.ConnectAsync();
            return Ok(new { success = connected, message = connected ? "Connected" : "Connection failed" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Connection error");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("disconnect")]
    public async Task<ActionResult<object>> Disconnect()
    {
        try
        {
            await _keysightService.DisconnectAsync();
            return Ok(new { success = true, message = "Disconnected" });
        }
        catch (Exception ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("status")]
    public ActionResult<object> GetStatus()
    {
        return Ok(new { connected = _keysightService.IsConnected });
    }

    [HttpPost("command")]
    public async Task<ActionResult<object>> SendCommand([FromBody] CommandRequest request)
    {
        try
        {
            var response = await _keysightService.SendCommandAsync(request.Command);
            return Ok(new { command = request.Command, response = response });
        }
        catch (Exception ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("voltage")]
    public async Task<ActionResult<object>> MeasureVoltage()
    {
        try
        {
            var voltage = await _keysightService.MeasureVoltageAsync();
            return Ok(new { voltage = voltage, timestamp = DateTime.UtcNow });
        }
        catch (Exception ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }
}

public class CommandRequest
{
    public string Command { get; set; } = "";
}
EOF

# Create updated Program.cs
cat > Program.cs << 'EOF'
using Keysight34461A.TestApp.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add our custom services
builder.Services.AddSingleton<IKeysightService, KeysightService>();

// Configure CORS for web interface
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

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors();
app.UseAuthorization();
app.MapControllers();

// Add a simple HTML interface
app.MapGet("/", () => Results.Content("""
<!DOCTYPE html>
<html>
<head>
    <title>Keysight 34461A Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .response { background: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0; }
        input[type="text"] { padding: 8px; width: 300px; margin: 5px; }
        #status { font-weight: bold; padding: 10px; border-radius: 3px; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 Keysight 34461A Test Interface</h1>
        
        <div class="card">
            <h3>Connection Status</h3>
            <div id="status" class="disconnected">Disconnected</div>
            <button class="btn btn-success" onclick="connect()">Connect</button>
            <button class="btn btn-danger" onclick="disconnect()">Disconnect</button>
            <button class="btn btn-primary" onclick="checkStatus()">Check Status</button>
        </div>

        <div class="card">
            <h3>SCPI Commands</h3>
            <input type="text" id="command" placeholder="Enter SCPI command (e.g., *IDN?)" value="*IDN?">
            <button class="btn btn-primary" onclick="sendCommand()">Send Command</button>
            <div class="response" id="commandResponse"></div>
        </div>

        <div class="card">
            <h3>Voltage Measurement</h3>
            <button class="btn btn-success" onclick="measureVoltage()">Measure Voltage</button>
            <div class="response" id="voltageResponse"></div>
        </div>

        <div class="card">
            <h3>Quick SCPI Tests</h3>
            <button class="btn btn-primary" onclick="sendQuickCommand('*IDN?')">*IDN?</button>
            <button class="btn btn-primary" onclick="sendQuickCommand('*RST')">*RST</button>
            <button class="btn btn-primary" onclick="sendQuickCommand('SYST:ERR?')">SYST:ERR?</button>
            <button class="btn btn-primary" onclick="sendQuickCommand('CONF:VOLT:DC')">CONF:VOLT:DC</button>
        </div>
    </div>

    <script>
        async function connect() {
            try {
                const response = await fetch('/api/keysight/connect', { method: 'POST' });
                const data = await response.json();
                document.getElementById('commandResponse').innerHTML = 
                    `<strong>Connect:</strong> ${JSON.stringify(data, null, 2)}`;
                checkStatus();
            } catch (error) {
                document.getElementById('commandResponse').innerHTML = 
                    `<strong>Error:</strong> ${error.message}`;
            }
        }

        async function disconnect() {
            try {
                const response = await fetch('/api/keysight/disconnect', { method: 'POST' });
                const data = await response.json();
                document.getElementById('commandResponse').innerHTML = 
                    `<strong>Disconnect:</strong> ${JSON.stringify(data, null, 2)}`;
                checkStatus();
            } catch (error) {
                document.getElementById('commandResponse').innerHTML = 
                    `<strong>Error:</strong> ${error.message}`;
            }
        }

        async function checkStatus() {
            try {
                const response = await fetch('/api/keysight/status');
                const data = await response.json();
                const statusDiv = document.getElementById('status');
                if (data.connected) {
                    statusDiv.textContent = 'Connected ✅';
                    statusDiv.className = 'connected';
                } else {
                    statusDiv.textContent = 'Disconnected ❌';
                    statusDiv.className = 'disconnected';
                }
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }

        async function sendCommand() {
            const command = document.getElementById('command').value;
            await sendQuickCommand(command);
        }

        async function sendQuickCommand(command) {
            try {
                const response = await fetch('/api/keysight/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });
                const data = await response.json();
                document.getElementById('commandResponse').innerHTML = 
                    `<strong>${command}:</strong><br>${JSON.stringify(data, null, 2)}`;
            } catch (error) {
                document.getElementById('commandResponse').innerHTML = 
                    `<strong>Error:</strong> ${error.message}`;
            }
        }

        async function measureVoltage() {
            try {
                const response = await fetch('/api/keysight/voltage');
                const data = await response.json();
                document.getElementById('voltageResponse').innerHTML = 
                    `<strong>Voltage:</strong> ${data.voltage} V<br><strong>Time:</strong> ${data.timestamp}`;
            } catch (error) {
                document.getElementById('voltageResponse').innerHTML = 
                    `<strong>Error:</strong> ${error.message}`;
            }
        }

        // Check status on page load
        checkStatus();
        
        // Auto-refresh status every 5 seconds
        setInterval(checkStatus, 5000);
    </script>
</body>
</html>
""", "text/html"));

Console.WriteLine("🚀 Keysight 34461A Test Application started!");
Console.WriteLine($"🌐 Web Interface: http://localhost:5000");
Console.WriteLine($"📊 Swagger UI: http://localhost:5000/swagger");

app.Run();
EOF

# Deploy files to RPi
echo "📁 Uploading files to RPi..."
scp KeysightService.cs ${RPI_HOST}:${RPI_PATH}/Services/ 2>/dev/null || \
    ssh ${RPI_HOST} "mkdir -p ${RPI_PATH}/Services" && scp KeysightService.cs ${RPI_HOST}:${RPI_PATH}/Services/

scp KeysightController.cs ${RPI_HOST}:${RPI_PATH}/Controllers/
scp Program.cs ${RPI_HOST}:${RPI_PATH}/

echo "🔨 Building application on RPi..."
ssh ${RPI_HOST} "cd ${RPI_PATH} && ~/.dotnet/dotnet build"

echo "✅ Deployment complete!"
echo ""
echo "🚀 To run the application:"
echo "   ssh ${RPI_HOST}"
echo "   cd ${RPI_PATH}"
echo "   ~/.dotnet/dotnet run"
echo ""
echo "🌐 Then open: http://192.168.9.75:5000"

# Clean up local files
rm -f KeysightService.cs KeysightController.cs Program.cs

echo "🎯 Ready to test C# performance vs Python!"