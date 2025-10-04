<!-- CV Peak Validation .NET Web API Project Instructions -->

# CV Peak Validation .NET Web API

This is a hybrid architecture project combining .NET Core Web API with Python microservices for CV (Cyclic Voltammetry) peak detection and validation.

## Architecture Overview
- **Frontend**: .NET Core Web API with Swagger UI
- **Backend Services**: Python Enhanced Detector V6/V7 + DeepCV V2
- **Database**: Entity Framework Core with SQLite/SQL Server
- **Communication**: HTTP REST API between .NET and Python services

## Key Features
- CV file upload and validation
- Peak detection via Python services
- Interactive peak validation UI
- Training data collection for AI models
- Real-time analysis results

## Development Guidelines
- Use dependency injection for service registration
- Implement proper error handling and logging
- Follow REST API conventions
- Maintain separation between .NET UI and Python ML services
- Use async/await patterns for HTTP communication

## Project Structure
- Controllers: API endpoints
- Models: Data transfer objects
- Services: Business logic and Python service integration
- Data: Entity Framework context and models