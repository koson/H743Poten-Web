# CV Peak Validation API 🧪⚡

A modern .NET Core Web API for **Cyclic Voltammetry (CV) peak detection and validation** using hybrid architecture with Python ML services.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/REST     ┌──────────────────┐
│   .NET Web API  │ ◄──────────────► │  Python Services │
│   (Main App)    │                  │  (ML/Analysis)   │
├─────────────────┤                  ├──────────────────┤
│ • Web UI        │                  │ • Enhanced V6    │
│ • Database      │                  │ • DeepCV V2      │
│ • File Mgmt     │                  │ • Peak Detection │
│ • Validation    │                  │ • Plot Gen       │
└─────────────────┘                  └──────────────────┘
```

## 🚀 Features

- **CV File Upload & Processing** - Support for CSV/TXT format CV data
- **Peak Detection** - Integration with Python Enhanced Detector V6/V7
- **Interactive Validation** - Web-based peak validation interface
- **Training Data Collection** - Export validated data for AI model training
- **Real-time Analysis** - Async processing with Python microservices
- **Database Storage** - SQLite with Entity Framework Core
- **REST API** - Full CRUD operations with Swagger documentation
- **Health Monitoring** - System and service health checks

## 🛠️ Technology Stack

### .NET Core Backend
- **.NET 8.0** - Latest LTS version
- **ASP.NET Core Web API** - RESTful API framework
- **Entity Framework Core** - ORM with SQLite database
- **Swagger/OpenAPI** - API documentation and testing
- **Dependency Injection** - Built-in IoC container

### Python Integration
- **HTTP Client** - Async communication with Python services
- **Enhanced Detector V6/V7** - Advanced peak detection algorithms
- **DeepCV V2** - Deep learning models for CV analysis
- **Matplotlib Integration** - Plot generation and visualization

## 📦 Project Structure

```
CVPeakValidation.Api/
├── Controllers/           # API endpoints
│   ├── CVAnalysisController.cs    # Main CV operations
│   └── HealthController.cs        # Health checks
├── Models/               # Data models and DTOs
│   ├── CVModels.cs      # Core domain models
│   └── DTOs.cs          # Data transfer objects
├── Services/            # Business logic layer
│   ├── CVAnalysisService.cs      # CV processing service
│   └── PythonCVService.cs        # Python integration
├── Data/                # Database context
│   └── CVValidationContext.cs    # EF Core context
├── Program.cs           # Application startup
├── appsettings.json     # Configuration
└── CVPeakValidation.Api.http     # API test file
```

## 🏃‍♂️ Quick Start

### Prerequisites
- **.NET 8.0 SDK** - [Download here](https://dotnet.microsoft.com/download)
- **Python 3.8+** - For ML services
- **VS Code** - Recommended IDE

### 1. Clone and Setup
```bash
git clone <repository-url>
cd dotnet-python-web/CVPeakValidation.Api
dotnet restore
```

### 2. Configure Python Service
Update `appsettings.json`:
```json
{
  "PythonService": {
    "BaseUrl": "http://localhost:5003",
    "Timeout": "00:05:00"
  }
}
```

### 3. Run the Application
```bash
dotnet run
```

The API will be available at:
- **Swagger UI**: http://localhost:5017
- **API Base**: http://localhost:5017/api
- **Health Check**: http://localhost:5017/api/health

### 4. Start Python Services
```bash
# In separate terminal
cd ../validation_data
python cv_validation_app.py
```

## 📋 API Endpoints

### Core CV Operations
- `POST /api/cvanalysis/upload` - Upload CV data file
- `POST /api/cvanalysis/analyze/{fileId}` - Analyze CV for peaks
- `POST /api/cvanalysis/sessions` - Create validation session
- `POST /api/cvanalysis/validate` - Validate detected peaks
- `GET /api/cvanalysis/export-training-data` - Export training data

### Health & Monitoring
- `GET /api/health` - System health status
- `GET /api/health/python-service` - Python service status

### Documentation
- `GET /` - API information and status
- `GET /swagger` - Interactive API documentation

## 🧪 Testing the API

Use the included `CVPeakValidation.Api.http` file with the REST Client extension:

1. **Upload CV File**:
```http
POST http://localhost:5017/api/cvanalysis/upload
Content-Type: multipart/form-data
# Upload your CV CSV file
```

2. **Analyze for Peaks**:
```http
POST http://localhost:5017/api/cvanalysis/analyze/1
{
  "height": 0.02,
  "distance": 10.0,
  "prominence": 0.01,
  "detectionMethod": "enhanced_v6"
}
```

3. **Validate Results**:
```http
POST http://localhost:5017/api/cvanalysis/validate
{
  "sessionId": 1,
  "peakValidations": [
    {
      "peakId": 1,
      "status": "Accepted",
      "comments": "Good peak detection"
    }
  ]
}
```

## 🗄️ Database Schema

The application uses SQLite with the following main entities:

- **CVFiles** - Uploaded CV data files
- **Peaks** - Detected peaks with analysis results  
- **ValidationSessions** - Human validation sessions
- **PeakValidations** - Individual peak validation records

## 🔧 Configuration

### Application Settings
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Data Source=cvvalidation.db"
  },
  "PythonService": {
    "BaseUrl": "http://localhost:5003",
    "Timeout": "00:05:00"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

### Development Environment
- Database is created automatically on first run
- CORS is enabled for all origins in development
- Detailed logging for debugging

## 🐍 Python Service Integration

The .NET API communicates with Python services for:

1. **Peak Detection** - Using Enhanced Detector V6/V7
2. **Plot Generation** - Matplotlib-based visualization
3. **AI Analysis** - DeepCV V2 integration

### Communication Flow
```
.NET API Request → HTTP Client → Python Service → ML Processing → JSON Response
```

## 🚀 Deployment

### Docker Support (Optional)
```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 80

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["CVPeakValidation.Api.csproj", "."]
RUN dotnet restore
COPY . .
RUN dotnet build -c Release -o /app/build

FROM build AS publish
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "CVPeakValidation.Api.dll"]
```

### Production Configuration
- Use SQL Server or PostgreSQL for production database
- Configure proper CORS policies
- Enable HTTPS and security headers
- Set up logging and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is part of the H743Poten Research initiative for electrochemical analysis tools.

## 🆘 Support

For support and questions:
- Check the [API documentation](http://localhost:5017/swagger)
- Review the test examples in `CVPeakValidation.Api.http`
- Contact the H743Poten Research Team

---

**Built with ❤️ for the electrochemical research community**