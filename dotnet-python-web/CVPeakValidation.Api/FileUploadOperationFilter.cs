using Microsoft.OpenApi.Models;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace CVPeakValidation.Api;

/// <summary>
/// Swagger operation filter to handle file uploads properly
/// </summary>
public class FileUploadOperationFilter : IOperationFilter
{
    public void Apply(OpenApiOperation operation, OperationFilterContext context)
    {
        var fileParameters = context.MethodInfo.GetParameters()
            .Where(p => p.ParameterType == typeof(IFormFile) || 
                       p.ParameterType.GetProperties().Any(prop => prop.PropertyType == typeof(IFormFile)))
            .ToArray();

        if (fileParameters.Any())
        {
            operation.RequestBody = new OpenApiRequestBody
            {
                Content = new Dictionary<string, OpenApiMediaType>
                {
                    ["multipart/form-data"] = new OpenApiMediaType
                    {
                        Schema = new OpenApiSchema
                        {
                            Type = "object",
                            Properties = new Dictionary<string, OpenApiSchema>
                            {
                                ["file"] = new OpenApiSchema
                                {
                                    Type = "string",
                                    Format = "binary"
                                },
                                ["compoundName"] = new OpenApiSchema
                                {
                                    Type = "string"
                                },
                                ["electrolyte"] = new OpenApiSchema
                                {
                                    Type = "string"
                                },
                                ["scanRate"] = new OpenApiSchema
                                {
                                    Type = "number",
                                    Format = "double"
                                }
                            },
                            Required = new HashSet<string> { "file" }
                        }
                    }
                }
            };
        }
    }
}