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