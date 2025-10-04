using CVPeakValidation.Api.Data;
using CVPeakValidation.Api.Models;
using Microsoft.EntityFrameworkCore;
using System.Globalization;

namespace CVPeakValidation.Api.Services;

/// <summary>
/// Service for CV file processing and analysis
/// </summary>
public interface ICVAnalysisService
{
    Task<CVAnalysisResponseDto> AnalyzeFileAsync(int fileId, AnalysisParametersDto parameters);
    Task<CVAnalysisResponseDto> AnalyzeFileDirectAsync(CVFile cvFile, AnalysisParametersDto parameters);
    Task<CVFile> SaveFileAsync(CVFileUploadDto uploadDto);
    Task<ValidationSessionDto> CreateValidationSessionAsync(int fileId, string sessionName, string? validatorName = null);
    Task<bool> ValidatePeaksAsync(PeakValidationRequestDto request);
    Task<TrainingDataExportDto> ExportTrainingDataAsync();
    Task<CVDataDto> LoadCVDataAsync(string filePath);
}

/// <summary>
/// Implementation of CV analysis service
/// </summary>
public class CVAnalysisService : ICVAnalysisService
{
    private readonly CVValidationContext _context;
    private readonly IPythonCVService _pythonService;
    private readonly ILogger<CVAnalysisService> _logger;
    private readonly IWebHostEnvironment _environment;

    public CVAnalysisService(
        CVValidationContext context,
        IPythonCVService pythonService,
        ILogger<CVAnalysisService> logger,
        IWebHostEnvironment environment)
    {
        _context = context;
        _pythonService = pythonService;
        _logger = logger;
        _environment = environment;
    }

    public async Task<CVFile> SaveFileAsync(CVFileUploadDto uploadDto)
    {
        var uploadsPath = Path.Combine(_environment.ContentRootPath, "uploads");
        Directory.CreateDirectory(uploadsPath);

        var fileName = $"{DateTime.UtcNow:yyyyMMdd_HHmmss}_{uploadDto.File.FileName}";
        var filePath = Path.Combine(uploadsPath, fileName);

        using (var stream = new FileStream(filePath, FileMode.Create))
        {
            await uploadDto.File.CopyToAsync(stream);
        }

        var cvFile = new CVFile
        {
            FileName = uploadDto.File.FileName,
            FilePath = filePath,
            FileSize = uploadDto.File.Length,
            CompoundName = uploadDto.CompoundName,
            Electrolyte = uploadDto.Electrolyte,
            ScanRate = uploadDto.ScanRate,
            UploadedAt = DateTime.UtcNow
        };

        // Load and parse CV data to get metadata
        try
        {
            var cvData = await LoadCVDataAsync(filePath);
            cvFile.DataPoints = cvData.DataPoints;
            cvFile.StartPotential = cvData.StartPotential;
            cvFile.EndPotential = cvData.EndPotential;
            if (cvFile.ScanRate == null && cvData.ScanRate > 0)
            {
                cvFile.ScanRate = cvData.ScanRate;
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Could not parse CV data metadata for file {FileName}", fileName);
        }

        _context.CVFiles.Add(cvFile);
        await _context.SaveChangesAsync();

        return cvFile;
    }

    public async Task<CVAnalysisResponseDto> AnalyzeFileAsync(int fileId, AnalysisParametersDto parameters)
    {
        var cvFile = await _context.CVFiles.FindAsync(fileId);
        if (cvFile == null)
        {
            throw new ArgumentException($"CV file with ID {fileId} not found");
        }

        // Load CV data
        var cvData = await LoadCVDataAsync(cvFile.FilePath!);

        // Call Python service for peak detection
        var pythonResponse = await _pythonService.DetectPeaksAsync(cvData, parameters);

        // Create validation session
        var session = new ValidationSession
        {
            CVFileId = fileId,
            SessionName = $"Analysis_{DateTime.UtcNow:yyyyMMdd_HHmmss}",
            DetectionParameters = System.Text.Json.JsonSerializer.Serialize(parameters),
            PeaksDetected = pythonResponse.Peaks.Count,
            Status = SessionStatus.InProgress
        };

        _context.ValidationSessions.Add(session);

        // Convert Python peaks to database peaks
        var peaks = new List<Peak>();
        foreach (var pythonPeak in pythonResponse.Peaks)
        {
            var peak = new Peak
            {
                CVFileId = fileId,
                Voltage = pythonPeak.Voltage,
                Current = pythonPeak.Current,
                PeakType = pythonPeak.Type,
                Confidence = pythonPeak.Confidence,
                Height = pythonPeak.Height,
                Width = pythonPeak.Width,
                Area = pythonPeak.Area,
                DetectionMethod = parameters.DetectionMethod,
                ValidationStatus = ValidationStatus.Pending
            };
            
            peaks.Add(peak);
            _context.Peaks.Add(peak);
        }

        await _context.SaveChangesAsync();

        // Generate plot
        var peakDtos = peaks.Select(p => new PeakDto
        {
            Id = p.Id,
            Voltage = p.Voltage,
            Current = p.Current,
            PeakType = p.PeakType,
            Confidence = p.Confidence,
            Height = p.Height,
            Width = p.Width,
            Area = p.Area,
            DetectionMethod = p.DetectionMethod,
            ValidationStatus = p.ValidationStatus
        }).ToList();

        // No longer use Python-generated plot since we use Plotly.js in frontend
        // Just provide empty plot URL since frontend generates its own interactive plot
        var plotUrl = string.Empty;

        _logger.LogInformation("Using Plotly.js for frontend plotting instead of Python-generated plots");
        
        return new CVAnalysisResponseDto
        {
            FileId = fileId,
            FileName = cvFile.FileName,
            SessionId = session.Id,
            CVData = cvData,
            Peaks = peakDtos,
            PlotUrl = plotUrl,
            Parameters = parameters
        };
    }

    public async Task<CVAnalysisResponseDto> AnalyzeFileDirectAsync(CVFile cvFile, AnalysisParametersDto parameters)
    {
        // Load CV data
        var cvData = await LoadCVDataAsync(cvFile.FilePath!);

        // Call Python service for peak detection
        var pythonResponse = await _pythonService.DetectPeaksAsync(cvData, parameters);

        // Convert Python peaks (without saving to database)
        var peakDtos = pythonResponse.Peaks.Select(pythonPeak => new PeakDto
        {
            Id = 0, // Temporary ID for direct analysis
            Voltage = pythonPeak.Voltage,
            Current = pythonPeak.Current,
            PeakType = pythonPeak.Type,
            Confidence = pythonPeak.Confidence,
            Height = pythonPeak.Height,
            Width = pythonPeak.Width,
            Area = pythonPeak.Area,
            DetectionMethod = parameters.DetectionMethod,
            ValidationStatus = ValidationStatus.Pending
        }).ToList();

        // No longer use Python-generated plot since we use Plotly.js in frontend
        // Just provide empty plot URL since frontend generates its own interactive plot
        var plotUrl = string.Empty;

        _logger.LogInformation("Using Plotly.js for frontend plotting instead of Python-generated plots");
        
        return new CVAnalysisResponseDto
        {
            FileId = 0, // Indicate this is direct analysis
            FileName = cvFile.FileName,
            SessionId = 0, // No session for direct analysis
            CVData = cvData,
            Peaks = peakDtos,
            PlotUrl = plotUrl,
            Parameters = parameters
        };
    }

    public async Task<ValidationSessionDto> CreateValidationSessionAsync(int fileId, string sessionName, string? validatorName = null)
    {
        var session = new ValidationSession
        {
            CVFileId = fileId,
            SessionName = sessionName,
            ValidatorName = validatorName,
            Status = SessionStatus.InProgress
        };

        _context.ValidationSessions.Add(session);
        await _context.SaveChangesAsync();

        return new ValidationSessionDto
        {
            Id = session.Id,
            CVFileId = session.CVFileId,
            SessionName = session.SessionName,
            ValidatorName = session.ValidatorName,
            StartedAt = session.StartedAt,
            Status = session.Status
        };
    }

    public async Task<bool> ValidatePeaksAsync(PeakValidationRequestDto request)
    {
        var session = await _context.ValidationSessions.FindAsync(request.SessionId);
        if (session == null)
        {
            return false;
        }

        var validatedCount = 0;
        var rejectedCount = 0;

        foreach (var validation in request.PeakValidations)
        {
            var peak = await _context.Peaks.FindAsync(validation.PeakId);
            if (peak == null) continue;

            // Update peak status
            peak.ValidationStatus = validation.Status;

            // Check if validation record already exists (using tracked query)
            var existingValidation = await _context.PeakValidations
                .FirstOrDefaultAsync(pv => pv.PeakId == validation.PeakId && pv.ValidationSessionId == request.SessionId);

            if (existingValidation != null)
            {
                // Update existing validation record
                existingValidation.Status = validation.Status;
                existingValidation.Comments = validation.Comments;
                existingValidation.CorrectedPeakType = validation.CorrectedPeakType;
                existingValidation.ValidationConfidence = validation.ValidationConfidence;
                existingValidation.ValidatedAt = DateTime.UtcNow;
                existingValidation.ValidatorName = session.ValidatorName; // Update validator name too
            }
            else
            {
                // Create new validation record
                var peakValidation = new PeakValidation
                {
                    PeakId = validation.PeakId,
                    ValidationSessionId = request.SessionId,
                    Status = validation.Status,
                    Comments = validation.Comments,
                    CorrectedPeakType = validation.CorrectedPeakType,
                    ValidationConfidence = validation.ValidationConfidence,
                    ValidatorName = session.ValidatorName,
                    ValidatedAt = DateTime.UtcNow
                };

                _context.PeakValidations.Add(peakValidation);
            }

            if (validation.Status == ValidationStatus.Accepted)
                validatedCount++;
            else if (validation.Status == ValidationStatus.Rejected)
                rejectedCount++;
        }

        // Update session statistics
        session.PeaksValidated = validatedCount;
        session.PeaksRejected = rejectedCount;
        session.CompletedAt = DateTime.UtcNow;
        session.Status = SessionStatus.Completed;

        await _context.SaveChangesAsync();
        return true;
    }

    public async Task<TrainingDataExportDto> ExportTrainingDataAsync()
    {
        var validatedPeaks = await _context.PeakValidations
            .Include(pv => pv.Peak)
            .ThenInclude(p => p.CVFile)
            .Where(pv => pv.Status == ValidationStatus.Accepted)
            .ToListAsync();

        var trainingPeaks = validatedPeaks.Select(pv => new TrainingPeakDto
        {
            Voltage = pv.Peak.Voltage,
            Current = pv.Peak.Current,
            PeakType = pv.CorrectedPeakType ?? pv.Peak.PeakType,
            Height = pv.Peak.Height ?? 0,
            Width = pv.Peak.Width ?? 0,
            Area = pv.Peak.Area ?? 0,
            ValidationStatus = pv.Status,
            CompoundName = pv.Peak.CVFile.CompoundName ?? "Unknown",
            DetectionMethod = pv.Peak.DetectionMethod,
            ScanRate = pv.Peak.CVFile.ScanRate ?? 0
        }).ToList();

        var sessionCount = await _context.ValidationSessions
            .Where(vs => vs.Status == SessionStatus.Completed)
            .CountAsync();

        return new TrainingDataExportDto
        {
            ExportedAt = DateTime.UtcNow,
            TotalPeaks = validatedPeaks.Count,
            ValidatedPeaks = validatedPeaks.Count,
            Sessions = sessionCount,
            Peaks = trainingPeaks
        };
    }

    public async Task<CVDataDto> LoadCVDataAsync(string filePath)
    {
        var lines = await File.ReadAllLinesAsync(filePath);
        var voltages = new List<double>();
        var currents = new List<double>();

        // Parse CSV data (assumes voltage,current format)
        foreach (var line in lines.Skip(1)) // Skip header
        {
            var parts = line.Split(',');
            if (parts.Length >= 2 && 
                double.TryParse(parts[0], NumberStyles.Float, CultureInfo.InvariantCulture, out var voltage) &&
                double.TryParse(parts[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var current))
            {
                voltages.Add(voltage);
                currents.Add(current);
            }
        }

        return new CVDataDto
        {
            Voltage = voltages,
            Current = currents,
            DataPoints = voltages.Count,
            StartPotential = voltages.Count > 0 ? voltages.Min() : 0,
            EndPotential = voltages.Count > 0 ? voltages.Max() : 0,
            ScanRate = 0.1 // Default, should be extracted from metadata or file
        };
    }
}