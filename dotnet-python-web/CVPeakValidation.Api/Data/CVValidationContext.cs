using Microsoft.EntityFrameworkCore;
using CVPeakValidation.Api.Models;

namespace CVPeakValidation.Api.Data;

/// <summary>
/// Entity Framework context for CV Peak Validation database
/// </summary>
public class CVValidationContext : DbContext
{
    public CVValidationContext(DbContextOptions<CVValidationContext> options) : base(options)
    {
    }

    public DbSet<CVFile> CVFiles { get; set; }
    public DbSet<Peak> Peaks { get; set; }
    public DbSet<ValidationSession> ValidationSessions { get; set; }
    public DbSet<PeakValidation> PeakValidations { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // CVFile configuration
        modelBuilder.Entity<CVFile>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.FileName);
            entity.Property(e => e.FileName).IsRequired().HasMaxLength(255);
            entity.Property(e => e.FilePath).HasMaxLength(500);
            entity.Property(e => e.CompoundName).HasMaxLength(100);
            entity.Property(e => e.Electrolyte).HasMaxLength(100);
            entity.Property(e => e.UploadedAt).HasDefaultValueSql("datetime('now')");
        });

        // Peak configuration
        modelBuilder.Entity<Peak>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.CVFileId, e.Voltage });
            entity.Property(e => e.PeakType).HasMaxLength(20).HasDefaultValue("unknown");
            entity.Property(e => e.DetectionMethod).HasMaxLength(50).HasDefaultValue("Enhanced_V6");
            entity.Property(e => e.DetectedAt).HasDefaultValueSql("datetime('now')");
            entity.Property(e => e.ValidationStatus).HasDefaultValue(ValidationStatus.Pending);

            // Foreign key relationship
            entity.HasOne(e => e.CVFile)
                  .WithMany(e => e.Peaks)
                  .HasForeignKey(e => e.CVFileId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        // ValidationSession configuration
        modelBuilder.Entity<ValidationSession>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.CVFileId);
            entity.Property(e => e.SessionName).IsRequired().HasMaxLength(100);
            entity.Property(e => e.ValidatorName).HasMaxLength(50);
            entity.Property(e => e.StartedAt).HasDefaultValueSql("datetime('now')");
            entity.Property(e => e.Status).HasDefaultValue(SessionStatus.InProgress);
            entity.Property(e => e.Notes).HasMaxLength(500);

            // Foreign key relationship
            entity.HasOne(e => e.CVFile)
                  .WithMany(e => e.ValidationSessions)
                  .HasForeignKey(e => e.CVFileId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        // PeakValidation configuration
        modelBuilder.Entity<PeakValidation>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.PeakId, e.ValidationSessionId }).IsUnique();
            entity.Property(e => e.ValidatorName).HasMaxLength(50);
            entity.Property(e => e.ValidatedAt).HasDefaultValueSql("datetime('now')");
            entity.Property(e => e.Comments).HasMaxLength(500);
            entity.Property(e => e.CorrectedPeakType).HasMaxLength(20);
            entity.Property(e => e.ValidationConfidence).HasDefaultValue(1.0);

            // Foreign key relationships
            entity.HasOne(e => e.Peak)
                  .WithMany(e => e.Validations)
                  .HasForeignKey(e => e.PeakId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.ValidationSession)
                  .WithMany(e => e.PeakValidations)
                  .HasForeignKey(e => e.ValidationSessionId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        // Enum conversions
        modelBuilder.Entity<Peak>()
            .Property(e => e.ValidationStatus)
            .HasConversion<string>();

        modelBuilder.Entity<ValidationSession>()
            .Property(e => e.Status)
            .HasConversion<string>();

        modelBuilder.Entity<PeakValidation>()
            .Property(e => e.Status)
            .HasConversion<string>();
    }
}