using CVPeakValidation.Api.Models;
using System.Text.Json;

namespace CVPeakValidation.Api.Services;

/// <summary>
/// Service for communicating with Python CV analysis services
/// </summary>
public interface IPythonCVService
{
    Task<PythonPeakDetectionResponseDto> DetectPeaksAsync(CVDataDto cvData, AnalysisParametersDto parameters);
    Task<string> GeneratePlotAsync(CVDataDto cvData, List<PeakDto> peaks);
    Task<bool> IsServiceAvailableAsync();
}

/// <summary>
/// Implementation of Python CV service using HTTP client
/// </summary>
public class PythonCVService : IPythonCVService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<PythonCVService> _logger;
    private readonly IConfiguration _configuration;
    private readonly string _pythonServiceUrl;

    public PythonCVService(HttpClient httpClient, ILogger<PythonCVService> logger, IConfiguration configuration)
    {
        _httpClient = httpClient;
        _logger = logger;
        _configuration = configuration;
        _pythonServiceUrl = _configuration["PythonService:BaseUrl"] ?? "http://localhost:5003";
    }

    public async Task<PythonPeakDetectionResponseDto> DetectPeaksAsync(CVDataDto cvData, AnalysisParametersDto parameters)
    {
        try
        {
            // Create request in the format expected by Python service
            var requestData = new
            {
                voltage = cvData.Voltage,
                current = cvData.Current,
                method = parameters.DetectionMethod,
                parameters = new Dictionary<string, object>
                {
                    { "height", parameters.Height },
                    { "distance", parameters.Distance },
                    { "prominence", parameters.Prominence },
                    { "width", parameters.Width },
                    { "window_size", parameters.WindowSize }
                }
            };

            var requestJson = JsonSerializer.Serialize(requestData);
            var content = new StringContent(requestJson, System.Text.Encoding.UTF8, "application/json");

            _logger.LogInformation("Sending peak detection request to Python service at {Url}", $"{_pythonServiceUrl}/api/analyze");
            
            var response = await _httpClient.PostAsync($"{_pythonServiceUrl}/api/analyze", content);
            
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                _logger.LogError("Python service returned error: {StatusCode} - {Content}", response.StatusCode, errorContent);
                throw new HttpRequestException($"Python service error: {response.StatusCode}");
            }

            var responseJson = await response.Content.ReadAsStringAsync();
            _logger.LogInformation("Python service response: {Response}", responseJson);
            
            try 
            {
                // Parse the JSON response - handle both flat and nested structures
                using var jsonDoc = JsonDocument.Parse(responseJson);
                var root = jsonDoc.RootElement;

                // Check if the response indicates success
                _logger.LogInformation("Response has success field: {HasSuccess}", root.TryGetProperty("success", out var successElement));
                _logger.LogInformation("Response has data field: {HasData}", root.TryGetProperty("data", out var _));
                
                bool isSuccessful = true; // Assume success unless explicitly told otherwise
                
                if (root.TryGetProperty("success", out var successEl))
                {
                    isSuccessful = successEl.GetBoolean();
                    _logger.LogInformation("Success field value: {Success}", isSuccessful);
                }

                if (!isSuccessful)
                {
                    string errorMessage = "Unknown error";
                    if (root.TryGetProperty("error", out var errorElement))
                    {
                        errorMessage = errorElement.GetString() ?? "Unknown error";
                    }
                    else if (root.TryGetProperty("message", out var messageElement))
                    {
                        errorMessage = messageElement.GetString() ?? "Unknown error";
                    }

                    _logger.LogError("Python service returned error: {Error}", errorMessage);
                    throw new InvalidOperationException($"Python service error: {errorMessage}");
                }

                // Parse the successful response
                var responseData = new PythonPeakDetectionResponseDto();

                // Determine if response is nested (has 'data' property) or flat
                JsonElement dataRoot;
                if (root.TryGetProperty("data", out var dataElement))
                {
                    dataRoot = dataElement;
                    _logger.LogInformation("Parsing nested response structure");
                }
                else
                {
                    dataRoot = root;
                    _logger.LogInformation("Parsing flat response structure");
                }

                // Extract peaks array
                if (dataRoot.TryGetProperty("peaks", out var peaksElement) && peaksElement.ValueKind == JsonValueKind.Array)
                {
                    foreach (var peakElement in peaksElement.EnumerateArray())
                    {
                        var peak = new PythonPeakDto
                        {
                            Voltage = peakElement.TryGetProperty("voltage", out var v) ? v.GetDouble() : 0,
                            Current = peakElement.TryGetProperty("current", out var c) ? c.GetDouble() : 0,
                            Type = peakElement.TryGetProperty("type", out var t) ? t.GetString() ?? "unknown" : "unknown",
                            Confidence = peakElement.TryGetProperty("confidence", out var conf) ? conf.GetDouble() : 0,
                            Height = peakElement.TryGetProperty("height", out var h) ? h.GetDouble() : null,
                            Width = peakElement.TryGetProperty("width", out var w) ? w.GetDouble() : null,
                            Area = peakElement.TryGetProperty("area", out var a) && a.ValueKind != JsonValueKind.Null ? a.GetDouble() : null
                        };
                        responseData.Peaks.Add(peak);
                    }
                }

                // Plot data is no longer provided by Python service since we use Plotly.js
                // Set empty plot data to maintain compatibility
                responseData.PlotData = string.Empty;

                // Extract metadata (optional)
                if (dataRoot.TryGetProperty("metadata", out var metadataElement))
                {
                    responseData.Metadata["raw"] = metadataElement.ToString();
                }

                _logger.LogInformation("Successfully parsed Python service response with {PeakCount} peaks", responseData.Peaks.Count);
                return responseData;
            }
            catch (JsonException jsonEx)
            {
                _logger.LogError(jsonEx, "JSON parsing error. Response: {Response}", responseJson);
                throw new InvalidOperationException($"Failed to parse Python service response: {jsonEx.Message}");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling Python peak detection service");
            throw;
        }
    }

    public async Task<string> GeneratePlotAsync(CVDataDto cvData, List<PeakDto> peaks)
    {
        try
        {
            var requestData = new
            {
                cv_data = new
                {
                    voltage = cvData.Voltage,
                    current = cvData.Current
                },
                peaks = peaks.Select(p => new
                {
                    voltage = p.Voltage,
                    current = p.Current,
                    type = p.PeakType,
                    confidence = p.Confidence
                })
            };

            var requestJson = JsonSerializer.Serialize(requestData);
            var content = new StringContent(requestJson, System.Text.Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync($"{_pythonServiceUrl}/api/generate_plot", content);
            
            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("Plot generation failed: {StatusCode}", response.StatusCode);
                return string.Empty;
            }

            var responseJson = await response.Content.ReadAsStringAsync();
            var pythonResponse = JsonSerializer.Deserialize<PythonServiceResponseDto>(responseJson);

            if (pythonResponse?.Success == true && pythonResponse.Data != null)
            {
                var plotData = JsonSerializer.Deserialize<Dictionary<string, object>>(
                    JsonSerializer.Serialize(pythonResponse.Data));
                
                return plotData?.GetValueOrDefault("plot_url")?.ToString() ?? string.Empty;
            }

            return string.Empty;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating plot from Python service");
            return string.Empty;
        }
    }

    public async Task<bool> IsServiceAvailableAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{_pythonServiceUrl}/health");
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Python service health check failed");
            return false;
        }
    }
}