using Microsoft.AspNetCore.Mvc;
using CVPeakValidation.Api.Services;

namespace CVPeakValidation.Api.Controllers;

/// <summary>
/// Controller for system health and Python service status
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    private readonly IPythonCVService _pythonService;
    private readonly ILogger<HealthController> _logger;

    public HealthController(IPythonCVService pythonService, ILogger<HealthController> logger)
    {
        _pythonService = pythonService;
        _logger = logger;
    }

    /// <summary>
    /// Check overall system health
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<HealthStatus>> GetHealth()
    {
        var pythonServiceAvailable = await _pythonService.IsServiceAvailableAsync();
        
        var status = new HealthStatus
        {
            IsHealthy = pythonServiceAvailable,
            Timestamp = DateTime.UtcNow,
            Services = new Dictionary<string, ServiceStatus>
            {
                { "dotnet-api", new ServiceStatus { IsHealthy = true, Message = "OK" } },
                { "python-cv-service", new ServiceStatus { IsHealthy = pythonServiceAvailable, Message = pythonServiceAvailable ? "OK" : "Unavailable" } }
            }
        };

        if (!status.IsHealthy)
        {
            _logger.LogWarning("System health check failed: Python service unavailable");
            return StatusCode(503, status);
        }

        return Ok(status);
    }

    /// <summary>
    /// Check Python service status specifically
    /// </summary>
    [HttpGet("python-service")]
    public async Task<ActionResult<ServiceStatus>> GetPythonServiceStatus()
    {
        var isAvailable = await _pythonService.IsServiceAvailableAsync();
        
        var status = new ServiceStatus
        {
            IsHealthy = isAvailable,
            Message = isAvailable ? "Python CV service is available" : "Python CV service is unavailable",
            LastChecked = DateTime.UtcNow
        };

        if (!isAvailable)
        {
            return StatusCode(503, status);
        }

        return Ok(status);
    }
}

/// <summary>
/// Simple endpoint for python health check (compatible with web UI)
/// </summary>
[ApiController]
[Route("api")]
public class PythonHealthController : ControllerBase
{
    private readonly IPythonCVService _pythonService;

    public PythonHealthController(IPythonCVService pythonService)
    {
        _pythonService = pythonService;
    }

    [HttpGet("python-health")]
    public async Task<IActionResult> GetPythonHealth()
    {
        var isAvailable = await _pythonService.IsServiceAvailableAsync();
        return Ok(new { status = isAvailable ? "OK" : "Error" });
    }
}

/// <summary>
/// Health status response model
/// </summary>
public class HealthStatus
{
    public bool IsHealthy { get; set; }
    public DateTime Timestamp { get; set; }
    public Dictionary<string, ServiceStatus> Services { get; set; } = new();
}

/// <summary>
/// Individual service status model
/// </summary>
public class ServiceStatus
{
    public bool IsHealthy { get; set; }
    public string Message { get; set; } = string.Empty;
    public DateTime LastChecked { get; set; } = DateTime.UtcNow;
}