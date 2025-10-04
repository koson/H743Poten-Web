namespace CVPeakValidation.Api.Models;

/// <summary>
/// DTO for CV file upload
/// </summary>
public class CVFileUploadDto
{
    public IFormFile File { get; set; } = null!;
    public string? CompoundName { get; set; }
    public string? Electrolyte { get; set; }
    public double? ScanRate { get; set; }
}

/// <summary>
/// DTO for CV analysis response
/// </summary>
public class CVAnalysisResponseDto
{
    public int FileId { get; set; }
    public string FileName { get; set; } = string.Empty;
    public int SessionId { get; set; }
    public CVDataDto CVData { get; set; } = new();
    public List<PeakDto> Peaks { get; set; } = new();
    public string PlotUrl { get; set; } = string.Empty;
    public AnalysisParametersDto Parameters { get; set; } = new();
}

/// <summary>
/// DTO for CV data points
/// </summary>
public class CVDataDto
{
    public List<double> Voltage { get; set; } = new();
    public List<double> Current { get; set; } = new();
    public int DataPoints { get; set; }
    public double StartPotential { get; set; }
    public double EndPotential { get; set; }
    public double ScanRate { get; set; }
}

/// <summary>
/// DTO for peak information
/// </summary>
public class PeakDto
{
    public int Id { get; set; }
    public double Voltage { get; set; }
    public double Current { get; set; }
    public string PeakType { get; set; } = "unknown";
    public double Confidence { get; set; }
    public double? Height { get; set; }
    public double? Width { get; set; }
    public double? Area { get; set; }
    public string DetectionMethod { get; set; } = string.Empty;
    public ValidationStatus ValidationStatus { get; set; }
}

/// <summary>
/// DTO for analysis parameters
/// </summary>
public class AnalysisParametersDto
{
    // Optimized default parameters for ferrocyanide peak detection
    public double Height { get; set; } = 0.5;       // Increased to avoid noise detection
    public double Distance { get; set; } = 20.0;    // Increased minimum distance between peaks
    public double Prominence { get; set; } = 0.3;    // Increased to select significant peaks only
    public double Width { get; set; } = 3.0;        // Reduced for sharper peak detection
    public int WindowSize { get; set; } = 10;
    public string DetectionMethod { get; set; } = "enhanced_v6";
}

/// <summary>
/// DTO for peak validation request
/// </summary>
public class PeakValidationRequestDto
{
    public int SessionId { get; set; }
    public List<PeakValidationDto> PeakValidations { get; set; } = new();
}

/// <summary>
/// DTO for individual peak validation
/// </summary>
public class PeakValidationDto
{
    public int PeakId { get; set; }
    public ValidationStatus Status { get; set; }
    public string? Comments { get; set; }
    public string? CorrectedPeakType { get; set; }
    public double ValidationConfidence { get; set; } = 1.0;
}

/// <summary>
/// DTO for validation session
/// </summary>
public class ValidationSessionDto
{
    public int Id { get; set; }
    public int CVFileId { get; set; }
    public string SessionName { get; set; } = string.Empty;
    public string? ValidatorName { get; set; }
    public DateTime StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public SessionStatus Status { get; set; }
    public int PeaksDetected { get; set; }
    public int PeaksValidated { get; set; }
    public int PeaksRejected { get; set; }
    public string? Notes { get; set; }
}

/// <summary>
/// DTO for training data export
/// </summary>
public class TrainingDataExportDto
{
    public DateTime ExportedAt { get; set; }
    public int TotalPeaks { get; set; }
    public int ValidatedPeaks { get; set; }
    public int Sessions { get; set; }
    public List<TrainingPeakDto> Peaks { get; set; } = new();
}

/// <summary>
/// DTO for training peak data
/// </summary>
public class TrainingPeakDto
{
    public double Voltage { get; set; }
    public double Current { get; set; }
    public string PeakType { get; set; } = string.Empty;
    public double Height { get; set; }
    public double Width { get; set; }
    public double Area { get; set; }
    public ValidationStatus ValidationStatus { get; set; }
    public string CompoundName { get; set; } = string.Empty;
    public string DetectionMethod { get; set; } = string.Empty;
    public double ScanRate { get; set; }
}

/// <summary>
/// DTO for Python service response
/// </summary>
public class PythonServiceResponseDto
{
    public bool Success { get; set; }
    public string? Error { get; set; }
    public object? Data { get; set; }
}

/// <summary>
/// DTO for Python peak detection request
/// </summary>
public class PythonPeakDetectionRequestDto
{
    public List<double> Voltage { get; set; } = new();
    public List<double> Current { get; set; } = new();
    public Dictionary<string, object> Parameters { get; set; } = new();
    public string Method { get; set; } = "enhanced_v6";
}

/// <summary>
/// DTO for Python peak detection response
/// </summary>
public class PythonPeakDetectionResponseDto
{
    public List<PythonPeakDto> Peaks { get; set; } = new();
    public string PlotData { get; set; } = string.Empty;
    public Dictionary<string, object> Metadata { get; set; } = new();
}

/// <summary>
/// DTO for Python peak data
/// </summary>
public class PythonPeakDto
{
    public double Voltage { get; set; }
    public double Current { get; set; }
    public string Type { get; set; } = "unknown";
    public double Confidence { get; set; }
    public double? Height { get; set; }
    public double? Width { get; set; }
    public double? Area { get; set; }
}