using Microsoft.EntityFrameworkCore;
using CVPeakValidation.Api.Data;
using CVPeakValidation.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();

// Configure Entity Framework
builder.Services.AddDbContext<CVValidationContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection") 
        ?? "Data Source=cvvalidation.db"));

// Configure HTTP clients for Python service
builder.Services.AddHttpClient<IPythonCVService, PythonCVService>(client =>
{
    client.Timeout = TimeSpan.FromMinutes(5); // Long timeout for ML operations
});

// Register services
builder.Services.AddScoped<ICVAnalysisService, CVAnalysisService>();

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy
            .AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

// Temporarily disable Swagger due to file upload conflicts
// Configure Swagger/OpenAPI
// builder.Services.AddEndpointsApiExplorer();
// builder.Services.AddSwaggerGen(options =>
// {
//     options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
//     {
//         Title = "CV Peak Validation API",
//         Version = "v1",
//         Description = "A .NET Web API for CV (Cyclic Voltammetry) peak detection and validation using Python services",
//         Contact = new Microsoft.OpenApi.Models.OpenApiContact
//         {
//             Name = "H743Poten Research Team",
//             Email = "research@h743poten.com"
//         }
//     });
//     
//     // Skip problematic operations
//     options.DocInclusionPredicate((name, api) => true);
// });

// Configure logging
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();

var app = builder.Build();

// Ensure database is created
using (var scope = app.Services.CreateScope())
{
    var context = scope.ServiceProvider.GetRequiredService<CVValidationContext>();
    context.Database.EnsureCreated();
}

// Configure the HTTP request pipeline  
if (app.Environment.IsDevelopment())
{
    // Swagger temporarily disabled due to file upload endpoint conflicts
    // app.UseSwagger();
    // app.UseSwaggerUI(c =>
    // {
    //     c.SwaggerEndpoint("/swagger/v1/swagger.json", "CV Peak Validation API v1");
    //     c.RoutePrefix = string.Empty;
    // });
}

// Remove custom middleware that might interfere with static files

app.UseHttpsRedirection();
app.UseCors("AllowAll");

// Serve static files (for UI)
app.UseDefaultFiles(); // Enable default files like index.html
app.UseStaticFiles();

app.UseRouting();
app.UseAuthorization();

// Web UI endpoint - serve HTML directly (MUST be before MapControllers)
app.MapGet("/", async (HttpContext context) => 
{
    try 
    {
        context.Response.ContentType = "text/html; charset=utf-8";
        
        // Get the full path to wwwroot/index.html
        var webRoot = app.Environment.WebRootPath ?? Path.Combine(app.Environment.ContentRootPath, "wwwroot");
        var indexPath = Path.Combine(webRoot, "index.html");
        
        if (File.Exists(indexPath))
        {
            var html = await File.ReadAllTextAsync(indexPath);
            await context.Response.WriteAsync(html);
        }
        else
        {
            // Fallback - serve simple HTML if file not found
            await context.Response.WriteAsync(@"
                <!DOCTYPE html>
                <html><head><title>CV Peak Validation</title></head>
                <body>
                    <h1>🧪 CV Peak Validation System</h1>
                    <p>Static files not found. File path checked: " + indexPath + @"</p>
                    <p><a href='/api/info'>API Info</a></p>
                </body></html>");
        }
    }
    catch (Exception ex)
    {
        context.Response.ContentType = "text/html";
        await context.Response.WriteAsync($"<h1>Error</h1><p>{ex.Message}</p>");
    }
});

// Map API controllers AFTER custom routes
app.MapControllers();

// API info endpoint 
app.MapGet("/api/info", (HttpContext context) => 
{
    return new
    {
        service = "CV Peak Validation API",
        version = "v1.0",
        status = "Running",
        timestamp = DateTime.UtcNow,
        endpoints = new
        {
            health = "/api/health",
            pythonHealth = "/api/python-health",
            upload = "POST /api/CVAnalysis/upload",
            analyze = "POST /api/CVAnalysis/analyze/{id}",
            validate = "POST /api/CVAnalysis/validate",
            exportTraining = "GET /api/CVAnalysis/export-training-data",
            test = "GET /api/CVAnalysis/test"
        }
    };
});

// Remove these since we want static files to work properly
// app.MapGet("/index.html", (HttpContext context) => 
// {
//     context.Response.Redirect("/", permanent: true);
//     return Task.CompletedTask;
// });

// Removed swagger redirect endpoints to fix UI loading

app.Run();
