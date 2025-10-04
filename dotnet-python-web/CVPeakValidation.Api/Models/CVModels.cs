using System.ComponentModel.DataAnnotations;

namespace CVPeakValidation.Api.Models;

/// <summary>
/// Represents a CV (Cyclic Voltammetry) data file
/// </summary>
public class CVFile
{
    public int Id { get; set; }
    
    [Required]
    [StringLength(255)]
    public string FileName { get; set; } = string.Empty;
    
    [StringLength(500)]
    public string? FilePath { get; set; }
    
    public long FileSize { get; set; }
    
    public DateTime UploadedAt { get; set; } = DateTime.UtcNow;
    
    [StringLength(100)]
    public string? CompoundName { get; set; }
    
    [StringLength(100)]
    public string? Electrolyte { get; set; }
    
    public double? ScanRate { get; set; }
    
    public int DataPoints { get; set; }
    
    public double? StartPotential { get; set; }
    
    public double? EndPotential { get; set; }
    
    // Navigation properties
    public virtual ICollection<Peak> Peaks { get; set; } = new List<Peak>();
    public virtual ICollection<ValidationSession> ValidationSessions { get; set; } = new List<ValidationSession>();
}

/// <summary>
/// Represents a detected peak in CV data
/// </summary>
public class Peak
{
    public int Id { get; set; }
    
    public int CVFileId { get; set; }
    
    /// <summary>
    /// Peak voltage (V)
    /// </summary>
    public double Voltage { get; set; }
    
    /// <summary>
    /// Peak current (A or µA)
    /// </summary>
    public double Current { get; set; }
    
    /// <summary>
    /// Peak type: oxidation, reduction, unknown
    /// </summary>
    [StringLength(20)]
    public string PeakType { get; set; } = "unknown";
    
    /// <summary>
    /// Detection confidence (0.0 - 1.0)
    /// </summary>
    public double Confidence { get; set; }
    
    /// <summary>
    /// Peak height above baseline
    /// </summary>
    public double? Height { get; set; }
    
    /// <summary>
    /// Peak width at half maximum
    /// </summary>
    public double? Width { get; set; }
    
    /// <summary>
    /// Peak area
    /// </summary>
    public double? Area { get; set; }
    
    /// <summary>
    /// Detection method used
    /// </summary>
    [StringLength(50)]
    public string DetectionMethod { get; set; } = "Enhanced_V6";
    
    public DateTime DetectedAt { get; set; } = DateTime.UtcNow;
    
    /// <summary>
    /// Human validation status
    /// </summary>
    public ValidationStatus ValidationStatus { get; set; } = ValidationStatus.Pending;
    
    // Navigation properties
    public virtual CVFile CVFile { get; set; } = null!;
    public virtual ICollection<PeakValidation> Validations { get; set; } = new List<PeakValidation>();
}

/// <summary>
/// Represents a validation session for CV peak analysis
/// </summary>
public class ValidationSession
{
    public int Id { get; set; }
    
    public int CVFileId { get; set; }
    
    [StringLength(100)]
    public string SessionName { get; set; } = string.Empty;
    
    [StringLength(50)]
    public string? ValidatorName { get; set; }
    
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;
    
    public DateTime? CompletedAt { get; set; }
    
    public SessionStatus Status { get; set; } = SessionStatus.InProgress;
    
    /// <summary>
    /// Detection parameters used
    /// </summary>
    public string? DetectionParameters { get; set; }
    
    /// <summary>
    /// Number of peaks detected
    /// </summary>
    public int PeaksDetected { get; set; }
    
    /// <summary>
    /// Number of peaks validated
    /// </summary>
    public int PeaksValidated { get; set; }
    
    /// <summary>
    /// Number of peaks rejected
    /// </summary>
    public int PeaksRejected { get; set; }
    
    [StringLength(500)]
    public string? Notes { get; set; }
    
    // Navigation properties
    public virtual CVFile CVFile { get; set; } = null!;
    public virtual ICollection<PeakValidation> PeakValidations { get; set; } = new List<PeakValidation>();
}

/// <summary>
/// Represents human validation of a detected peak
/// </summary>
public class PeakValidation
{
    public int Id { get; set; }
    
    public int PeakId { get; set; }
    
    public int ValidationSessionId { get; set; }
    
    public ValidationStatus Status { get; set; }
    
    [StringLength(50)]
    public string? ValidatorName { get; set; }
    
    public DateTime ValidatedAt { get; set; } = DateTime.UtcNow;
    
    [StringLength(500)]
    public string? Comments { get; set; }
    
    /// <summary>
    /// Corrected peak type if different from detected
    /// </summary>
    [StringLength(20)]
    public string? CorrectedPeakType { get; set; }
    
    /// <summary>
    /// Confidence in validation (0.0 - 1.0)
    /// </summary>
    public double ValidationConfidence { get; set; } = 1.0;
    
    // Navigation properties
    public virtual Peak Peak { get; set; } = null!;
    public virtual ValidationSession ValidationSession { get; set; } = null!;
}

/// <summary>
/// Validation status enumeration
/// </summary>
public enum ValidationStatus
{
    Pending = 0,
    Accepted = 1,
    Rejected = 2,
    NeedsReview = 3
}

/// <summary>
/// Session status enumeration
/// </summary>
public enum SessionStatus
{
    InProgress = 0,
    Completed = 1,
    Cancelled = 2,
    Error = 3
}