using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CVPeakValidation.Api.Models;
using CVPeakValidation.Api.Services;
using CVPeakValidation.Api.Data;

namespace CVPeakValidation.Api.Controllers;

/// <summary>
/// Controller for CV file upload and analysis operations
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class CVAnalysisController : ControllerBase
{
    private readonly ICVAnalysisService _analysisService;
    private readonly ILogger<CVAnalysisController> _logger;
    private readonly CVValidationContext _context;

    public CVAnalysisController(ICVAnalysisService analysisService, ILogger<CVAnalysisController> logger, CVValidationContext context)
    {
        _analysisService = analysisService;
        _logger = logger;
        _context = context;
    }

    /// <summary>
    /// Upload a CV file for analysis
    /// </summary>
    [HttpPost("upload")]
    [Consumes("multipart/form-data")]
    [ApiExplorerSettings(IgnoreApi = true)] // Exclude from Swagger
    public async Task<ActionResult> UploadFile([FromForm] CVFileUploadDto uploadDto)
    {
        try
        {
            if (uploadDto.File == null || uploadDto.File.Length == 0)
            {
                return BadRequest(new { error = "No file provided" });
            }

            var allowedExtensions = new[] { ".csv", ".txt" };
            var fileExtension = Path.GetExtension(uploadDto.File.FileName).ToLowerInvariant();
            
            if (!allowedExtensions.Contains(fileExtension))
            {
                return BadRequest(new { error = "Only CSV and TXT files are supported" });
            }

            var cvFile = await _analysisService.SaveFileAsync(uploadDto);
            
            _logger.LogInformation("CV file uploaded successfully: {FileName} ({Id})", cvFile.FileName, cvFile.Id);
            
            // Return simplified response
            return Ok(new {
                id = cvFile.Id,
                fileName = cvFile.FileName,
                fileSize = cvFile.FileSize,
                dataPoints = cvFile.DataPoints,
                compoundName = cvFile.CompoundName,
                electrolyte = cvFile.Electrolyte,
                scanRate = cvFile.ScanRate,
                uploadedAt = cvFile.UploadedAt,
                message = "File uploaded successfully"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading CV file");
            return StatusCode(500, new { error = "Internal server error during file upload", details = ex.Message });
        }
    }

    /// <summary>
    /// Get all available CV files
    /// </summary>
    [HttpGet("cv-files")]
    public async Task<ActionResult<IEnumerable<object>>> GetCVFiles()
    {
        try
        {
            var files = await _context.CVFiles
                .OrderByDescending(f => f.UploadedAt)
                .Select(f => new { f.Id, f.FileName, f.UploadedAt, f.FileSize })
                .ToListAsync();
            
            return Ok(files);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving CV files");
            return StatusCode(500, new { error = "Failed to retrieve CV files" });
        }
    }

    /// <summary>
    /// Browse files in uploads folder
    /// </summary>
    [HttpGet("browse-uploads")]
    public ActionResult<IEnumerable<object>> BrowseUploadsFolder()
    {
        try
        {
            var uploadsPath = Path.Combine(Directory.GetCurrentDirectory(), "uploads");
            
            if (!Directory.Exists(uploadsPath))
            {
                return Ok(new List<object>());
            }

            var allowedExtensions = new[] { ".csv", ".txt" };
            var files = Directory.GetFiles(uploadsPath)
                .Where(file => allowedExtensions.Contains(Path.GetExtension(file).ToLowerInvariant()))
                .Select(file => new
                {
                    fileName = Path.GetFileName(file),
                    filePath = file,
                    fileSize = new FileInfo(file).Length,
                    lastModified = new FileInfo(file).LastWriteTime
                })
                .OrderByDescending(f => f.lastModified)
                .ToList();

            return Ok(files);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error browsing uploads folder");
            return StatusCode(500, new { error = "Failed to browse uploads folder" });
        }
    }

    /// <summary>
    /// Analyze a file directly from uploads folder
    /// </summary>
    [HttpPost("analyze-uploads/{fileName}")]
    public async Task<ActionResult<CVAnalysisResponseDto>> AnalyzeUploadsFile(
        string fileName, 
        [FromBody] AnalysisParametersDto parameters)
    {
        try
        {
            var uploadsPath = Path.Combine(Directory.GetCurrentDirectory(), "uploads");
            var filePath = Path.Combine(uploadsPath, fileName);
            
            if (!System.IO.File.Exists(filePath))
            {
                return NotFound(new { error = "File not found in uploads folder", fileName });
            }

            var allowedExtensions = new[] { ".csv", ".txt" };
            var fileExtension = Path.GetExtension(fileName).ToLowerInvariant();
            
            if (!allowedExtensions.Contains(fileExtension))
            {
                return BadRequest(new { error = "Only CSV and TXT files are supported" });
            }

            // Create a temporary CVFile object for analysis
            var fileInfo = new FileInfo(filePath);
            var tempCVFile = new CVFile
            {
                Id = 0, // Temporary ID
                FileName = fileName,
                FilePath = filePath,
                FileSize = fileInfo.Length,
                UploadedAt = fileInfo.LastWriteTime
            };

            var result = await _analysisService.AnalyzeFileDirectAsync(tempCVFile, parameters);
            
            _logger.LogInformation("Direct CV analysis completed for file {FileName}: {PeakCount} peaks detected", 
                fileName, result.Peaks.Count);
            
            return Ok(result);
        }
        catch (FileNotFoundException ex)
        {
            _logger.LogWarning(ex, "File not found for direct analysis: {FileName}", fileName);
            return NotFound(new { error = ex.Message, fileName });
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Python service error during direct analysis");
            return StatusCode(502, new { error = "Python analysis service unavailable", details = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error analyzing uploads file {FileName}", fileName);
            return StatusCode(500, new { error = "Internal server error during analysis", details = ex.Message });
        }
    }

    /// <summary>
    /// Get CV file details
    /// </summary>
    [HttpGet("cv-files/{fileId}")]
    public async Task<ActionResult<object>> GetCVFile(int fileId)
    {
        try
        {
            var file = await _context.CVFiles.FindAsync(fileId);
            if (file == null)
            {
                return NotFound(new { error = "CV file not found" });
            }

            return Ok(new
            {
                file.Id,
                file.FileName,
                file.FileSize,
                file.UploadedAt,
                file.DataPoints,
                file.ScanRate
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving CV file {FileId}", fileId);
            return StatusCode(500, new { error = "Failed to retrieve CV file" });
        }
    }

    /// <summary>
    /// Analyze a CV file for peak detection
    /// </summary>
    [HttpPost("analyze/{fileId}")]
    public async Task<ActionResult<CVAnalysisResponseDto>> AnalyzeFile(
        int fileId, 
        [FromBody] AnalysisParametersDto parameters)
    {
        try
        {
            if (fileId <= 0)
            {
                return BadRequest(new { error = "Invalid file ID. File ID must be greater than 0." });
            }

            var result = await _analysisService.AnalyzeFileAsync(fileId, parameters);
            
            _logger.LogInformation("CV analysis completed for file {FileId}: {PeakCount} peaks detected", 
                fileId, result.Peaks.Count);
            
            return Ok(result);
        }
        catch (ArgumentException ex)
        {
            _logger.LogWarning(ex, "File not found for analysis: {FileId}", fileId);
            return NotFound(new { error = ex.Message, fileId = fileId });
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Python service error during analysis");
            return StatusCode(502, new { error = "Python analysis service unavailable", details = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error analyzing CV file {FileId}", fileId);
            return StatusCode(500, new { error = "Internal server error during analysis", details = ex.Message });
        }
    }

    /// <summary>
    /// Create a new validation session
    /// </summary>
    [HttpPost("sessions")]
    public async Task<ActionResult<ValidationSessionDto>> CreateSession([FromBody] CreateSessionRequest request)
    {
        try
        {
            var session = await _analysisService.CreateValidationSessionAsync(
                request.FileId, 
                request.SessionName, 
                request.ValidatorName);
            
            return Ok(session);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating validation session");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Validate detected peaks
    /// </summary>
    [HttpPost("validate")]
    public async Task<ActionResult> ValidatePeaks([FromBody] PeakValidationRequestDto request)
    {
        try
        {
            var success = await _analysisService.ValidatePeaksAsync(request);
            
            if (!success)
            {
                return BadRequest("Validation session not found or invalid");
            }

            _logger.LogInformation("Peak validation completed for session {SessionId}: {ValidationCount} peaks validated", 
                request.SessionId, request.PeakValidations.Count);
            
            return Ok(new { message = "Peak validation completed successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error validating peaks for session {SessionId}", request.SessionId);
            return StatusCode(500, "Internal server error during validation");
        }
    }

    /// <summary>
    /// Test endpoint for API verification
    /// </summary>
    [HttpGet("test")]
    public ActionResult<object> Test()
    {
        return Ok(new {
            message = "CV Analysis API is working",
            timestamp = DateTime.UtcNow,
            version = "1.0.0"
        });
    }

    /// <summary>
    /// Export training data from validated peaks
    /// </summary>
    [HttpGet("export-training-data")]
    public async Task<ActionResult<TrainingDataExportDto>> ExportTrainingData()
    {
        try
        {
            var trainingData = await _analysisService.ExportTrainingDataAsync();
            
            _logger.LogInformation("Training data exported: {TotalPeaks} peaks from {Sessions} sessions", 
                trainingData.TotalPeaks, trainingData.Sessions);
            
            return Ok(trainingData);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error exporting training data");
            return StatusCode(500, "Internal server error during export");
        }
    }

    /// <summary>
    /// Save validated peak results
    /// </summary>
    [HttpPost("validate-peaks")]
    public async Task<ActionResult> SaveValidatedPeaks([FromBody] PeakValidationRequestDto request)
    {
        try
        {
            var success = await _analysisService.ValidatePeaksAsync(request);
            if (!success)
            {
                return BadRequest(new { error = "Validation failed" });
            }
            return Ok(new { message = "Peak validation saved successfully", sessionId = request.SessionId });
        }
        catch (ArgumentException ex)
        {
            _logger.LogWarning(ex, "Invalid validation request");
            return BadRequest(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving peak validation");
            return StatusCode(500, new { error = "Internal server error during validation save" });
        }
    }
}

/// <summary>
/// Request model for creating validation sessions
/// </summary>
public class CreateSessionRequest
{
    public int FileId { get; set; }
    public string SessionName { get; set; } = string.Empty;
    public string? ValidatorName { get; set; }
}